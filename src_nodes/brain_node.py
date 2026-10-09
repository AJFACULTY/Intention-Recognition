#!/usr/bin/env python3
"""
brain_node.py — Production Multi-Modal Cognition & Decision Node
Cognition Robot Project — Milestone 5 Autonomy

Features:
- Subscribes to /cognition/gesture (Gesture) and /cognition/detection (Detection)
- Subscribes to /cognition/face_identity (String JSON) for biometric authorization
- Parameterized velocity publisher topic (default: /cmd_vel_gesture) for seamless
  priority arbitration via twist_mux
- Optional biometric gate (require_face_auth parameter):
  - When True: ignores gestures from unknown/unauthorized bystanders
  - When False: accepts gestures from any zone-eligible person (lab testing mode)
- Subject locking FSM with configurable lock_timeout
- Smooth speed arbitration for STOP, GO, BACK, LEFT, RIGHT, FOLLOW
"""

import json
import math
import os
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String, Int32, UInt16
from std_srvs.srv import SetBool
from cognition_interfaces.msg import Gesture, Detection

# Gesture ID Constants (must match gesture classifier label encoder)
GESTURE_NONE = -1
GESTURE_BACK = 0
GESTURE_FOLLOW = 1
GESTURE_GO = 2
GESTURE_LEFT = 3
GESTURE_RIGHT = 4
GESTURE_STOP = 5


class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # ── Parameters ─────────────────────────────────────────
        self.declare_parameter('linear_speed', 0.25)
        self.declare_parameter('angular_speed', 0.40)
        self.declare_parameter('follow_speed', 0.20)
        self.declare_parameter('follow_kp_angular', 1.5)
        self.declare_parameter('gesture_buffer_size', 5)
        self.declare_parameter('lock_timeout', 3.0)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_gesture')
        self.declare_parameter('gesture_topic', '/cognition/gesture')
        self.declare_parameter('require_face_auth', False)
        self.declare_parameter('enable_lidar_safety', True)
        self.declare_parameter('lidar_safety_distance', 0.36)
        self.declare_parameter('lidar_clearance_distance', 0.45)
        self.declare_parameter('lidar_cone_deg', 45.0)
        self.declare_parameter('corridor_safety_width', 0.36)
        self.declare_parameter('reverse_speed', 0.12)
        self.declare_parameter('reverse_duration', 1.67)
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('enable_coupled_gimbal_yaw', True)
        self.declare_parameter('reacquisition_timeout_sec', 5.0)
        self.declare_parameter('low_battery_warn_v', 7.0)
        self.declare_parameter('low_battery_cutoff_v', 6.8)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.angular_speed = float(self.get_parameter('angular_speed').value)
        self.follow_speed = float(self.get_parameter('follow_speed').value)
        self.follow_kp_angular = float(self.get_parameter('follow_kp_angular').value)
        self.buffer_size = int(self.get_parameter('gesture_buffer_size').value)
        self.lock_timeout = float(self.get_parameter('lock_timeout').value)
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.gesture_topic = self.get_parameter('gesture_topic').value
        self.require_face_auth = bool(self.get_parameter('require_face_auth').value)
        self.enable_lidar_safety = bool(self.get_parameter('enable_lidar_safety').value)
        self.lidar_safety_distance = float(self.get_parameter('lidar_safety_distance').value)
        self.lidar_clearance_distance = float(self.get_parameter('lidar_clearance_distance').value)
        self.lidar_cone_deg = float(self.get_parameter('lidar_cone_deg').value)
        self.corridor_safety_width = float(self.get_parameter('corridor_safety_width').value)
        self.reverse_speed = float(self.get_parameter('reverse_speed').value)
        self.reverse_duration = float(self.get_parameter('reverse_duration').value)
        self.declare_parameter('lidar_rear_safety_distance', 0.25)
        self.lidar_rear_safety_distance = float(self.get_parameter('lidar_rear_safety_distance').value)
        self.scan_topic = str(self.get_parameter('scan_topic').value)
        self.enable_coupled_gimbal_yaw = bool(self.get_parameter('enable_coupled_gimbal_yaw').value)
        self.reacquisition_timeout_sec = float(self.get_parameter('reacquisition_timeout_sec').value)
        self.low_battery_warn_v = float(self.get_parameter('low_battery_warn_v').value)
        self.low_battery_cutoff_v = float(self.get_parameter('low_battery_cutoff_v').value)

        # ── Publishers ──────────────────────────────────────────
        # Publishes to /cmd_vel_gesture (Priority 40 in twist_mux)
        self.cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.beep_pub = self.create_publisher(UInt16, '/beep', 10)

        # ── Subscribers ─────────────────────────────────────────
        self.detection_sub = self.create_subscription(
            Detection, '/cognition/detection', self.detection_callback, 10)

        self.gesture_sub = self.create_subscription(
            Gesture, self.gesture_topic, self.gesture_callback, 10)

        self.face_id_sub = self.create_subscription(
            String, '/cognition/face_identity', self.face_identity_callback, 10)

        # Mode subscriber (supports GESTURE vs AUTO/NAV2 mode switching)
        self.mode_sub = self.create_subscription(
            String, '/system/mode', self.mode_callback, 10)

        # Gimbal feedback subscriber (Coupled eye-to-base visual servoing)
        self.servo_s1_sub = self.create_subscription(
            Int32, '/servo_s1', self.servo_s1_callback, 10)

        # Battery monitor subscriber (Two-tiered low voltage protection)
        self.battery_sub = self.create_subscription(
            UInt16, '/battery', self.battery_callback, 10)

        # LiDAR Planar LaserScan subscriber (Continuous frontal safety monitor)
        if self.enable_lidar_safety:
            self.scan_sub = self.create_subscription(
                LaserScan, self.scan_topic, self.scan_callback, 10)

        # ── Services ────────────────────────────────────────────
        self.srv_reset = self.create_service(SetBool, 'reset_lock', self.reset_lock_callback)

        # ── Internal State ──────────────────────────────────────
        self.system_mode = "GESTURE"  # Default to active gesture mode
        self.person_detected = False
        self.person_center_x = 0.5
        self.person_width = 0.0
        self.last_seen_time = None

        self.operator_authorized = False
        self.operator_name = "Unknown"
        self.last_face_time = 0.0

        self.locked_on = False
        self.lock_time = None
        self.gesture_triggered = False
        self.current_gesture = GESTURE_NONE
        self.gesture_buffer = []

        # LiDAR Safety State
        self.min_frontal_distance = float('inf')
        self.min_rear_distance = float('inf')
        self.rear_safety_blocked = False
        self.safety_halt_active = False
        self.safety_reverse_active = False
        self.safety_reverse_start_time = None
        self.last_reverse_beep_time = 0.0
        self.last_scan_time = None

        # Gimbal Pan Feedback State
        self.gimbal_pan_deg = 0.0
        self.last_pan_time = 0.0

        # Battery Telemetry State
        self.battery_voltage = 8.4
        self.battery_last_warn_time = 0.0
        self.battery_cutoff_active = False

        # Visual Servoing Re-acquisition State
        self.last_target_bearing = 0.0

        # 10 Hz Real-Time Control Loop Timer
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info(
            f'BrainNode started — cmd_vel_topic={self.cmd_vel_topic}, '
            f'gesture_topic={self.gesture_topic}, '
            f'require_face_auth={self.require_face_auth}, '
            f'linear={self.linear_speed:.2f}, follow={self.follow_speed:.2f}, '
            f'lidar_safety={self.enable_lidar_safety} (< {self.lidar_safety_distance:.2f}m)'
        )

    # ── CALLBACKS ─────────────────────────────────────────────────

    def mode_callback(self, msg: String):
        """Receive system mode updates (GESTURE vs AUTO/NAV2 mode)."""
        new_mode = msg.data.strip().upper()
        if new_mode in ("GESTURE", "AUTO", "MANUAL", "PAUSE"):
            if new_mode != self.system_mode:
                self.system_mode = new_mode
                self.get_logger().info(f"System mode switched to: {self.system_mode}")

    def servo_s1_callback(self, msg: Int32):
        # Physical clamp within +/-60 deg Yahboom gimbal limits
        angle = max(-60.0, min(60.0, float(msg.data)))
        self.gimbal_pan_deg = angle
        self.last_pan_time = time.monotonic()

    def battery_callback(self, msg: UInt16):
        val = float(msg.data)
        self.battery_voltage = (val / 10.0) if val > 50.0 else val

        if self.battery_voltage < self.low_battery_cutoff_v:
            if not self.battery_cutoff_active:
                self.get_logger().error(
                    f"BATTERY CUTOFF REACHED: {self.battery_voltage:.1f}V (< {self.low_battery_cutoff_v:.1f}V)! "
                    f"Engaging automatic safety park to prevent cell degradation."
                )
                self.battery_cutoff_active = True
        elif self.battery_voltage >= (self.low_battery_cutoff_v + 0.3):
            self.battery_cutoff_active = False

    def face_identity_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
            self.operator_authorized = bool(payload.get("authorized", False))
            self.operator_name = payload.get("name", "Unknown")
            self.last_face_time = time.monotonic()
        except Exception as e:
            self.get_logger().error(f"Error parsing face identity JSON: {e}")

    def detection_callback(self, msg: Detection):
        if msg.label == 'person' and msg.confidence >= 0.35:
            self.person_detected = True
            self.person_center_x = msg.center_x
            self.person_width = msg.width
            self.last_seen_time = time.monotonic()
            if self.locked_on:
                self.lock_time = time.monotonic()
        else:
            # Clear person flag only after 2.0s grace period to tolerate frame skips and head turns
            if self.last_seen_time is None or (time.monotonic() - self.last_seen_time) > 2.0:
                self.person_detected = False

    def scan_callback(self, msg: LaserScan):
        """Processes 2D LiDAR ranges and evaluates bidirectional collision safety within Cartesian corridor."""
        if not self.enable_lidar_safety:
            return

        half_corridor = self.corridor_safety_width / 2.0  # e.g. 0.18m for 0.36m corridor
        min_frontal_dist = float('inf')
        min_rear_dist = float('inf')

        angle = msg.angle_min
        inc = msg.angle_increment if msg.angle_increment > 0 else 0.0087
        for r in msg.ranges:
            if msg.range_min <= r <= msg.range_max and not math.isnan(r) and not math.isinf(r):
                # Convert polar (r, angle) to robot Cartesian coordinates
                # x = forward/backward distance (+x forward, -x rear), y = lateral distance (+y left, -y right)
                x = r * math.cos(angle)
                y = r * math.sin(angle)

                # Filter strictly within the vehicle's driving corridor width
                if abs(y) <= half_corridor:
                    # Frontal corridor: obstacle must be in front of physical chassis bumper (x >= 0.14m)
                    if 0.14 <= x <= (self.lidar_clearance_distance + 0.20):
                        if x < min_frontal_dist:
                            min_frontal_dist = x
                    # Rear corridor: obstacle must be behind physical rear chassis plate (x <= -0.15m)
                    elif -(self.lidar_clearance_distance + 0.20) <= x <= -0.15:
                        rear_d = abs(x)
                        if rear_d < min_rear_dist:
                            min_rear_dist = rear_d
            angle += inc

        self.min_frontal_distance = min_frontal_dist
        self.min_rear_distance = min_rear_dist
        self.rear_safety_blocked = (min_rear_dist < self.lidar_rear_safety_distance)
        self.last_scan_time = time.monotonic()

        # Emergency Breach Detection (< 0.36m within driving corridor)
        if min_frontal_dist < self.lidar_safety_distance:
            if not self.safety_halt_active and not self.safety_reverse_active:
                self.safety_halt_active = True
                if self.rear_safety_blocked:
                    self.safety_reverse_active = False
                    self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
                    self.get_logger().warn(
                        f"LiDAR SAFETY BREACH: Frontal obstacle in corridor at {min_frontal_dist:.2f}m "
                        f"(< {self.lidar_safety_distance:.2f}m), but REAR BLOCKED at {min_rear_dist:.2f}m "
                        f"(< {self.lidar_rear_safety_distance:.2f}m)! Halting chassis without reverse."
                    )
                else:
                    self.get_logger().warn(
                        f"LiDAR SAFETY BREACH: Frontal obstacle in corridor at {min_frontal_dist:.2f}m "
                        f"(< {self.lidar_safety_distance:.2f}m)! Initiating reactive reverse."
                    )
                    self.safety_reverse_active = True
                    self.safety_reverse_start_time = time.monotonic()

                # Pulse acoustic alarm
                beep_msg = UInt16()
                beep_msg.data = 150
                self.beep_pub.publish(beep_msg)
        elif min_frontal_dist >= self.lidar_clearance_distance:
            if self.safety_halt_active:
                self.get_logger().info(
                    f"LiDAR SAFETY RESTORED: Frontal corridor clearance {min_frontal_dist:.2f}m "
                    f"(>= {self.lidar_clearance_distance:.2f}m). Resuming normal FSM."
                )
                self.safety_halt_active = False

    def gesture_callback(self, msg: Gesture):
        is_stop_gesture = (msg.gesture_id == GESTURE_STOP or msg.gesture_label == "STOP")
        # Allow gesture if person detected, OR if emergency STOP, OR if high-confidence gesture (>= 0.80)
        if not self.person_detected and not is_stop_gesture and msg.confidence < 0.80:
            return

        # Check Biometric Authorization Gate
        if self.require_face_auth:
            face_fresh = (time.monotonic() - self.last_face_time) < 5.0
            if not (self.operator_authorized and face_fresh):
                self.get_logger().warn(
                    f'Ignoring gesture {msg.gesture_label}: Operator unauthorized ({self.operator_name})',
                    throttle_duration_sec=2.0
                )
                return

        # Dual ID/Label resolution for 100% interoperability across nodes and dashboard
        LABEL_TO_ID = {
            "BACK": GESTURE_BACK,
            "FOLLOW": GESTURE_FOLLOW,
            "GO": GESTURE_GO,
            "LEFT": GESTURE_LEFT,
            "RIGHT": GESTURE_RIGHT,
            "STOP": GESTURE_STOP,
        }
        gid = msg.gesture_id
        if gid < 0 and msg.gesture_label in LABEL_TO_ID:
            gid = LABEL_TO_ID[msg.gesture_label]

        # ONLY buffer valid, actionable gestures (>= 0); ignore NONE (-1) so dropped frames do not flush votes
        if gid >= 0:
            self.gesture_buffer.append(gid)
            if len(self.gesture_buffer) > self.buffer_size:
                self.gesture_buffer.pop(0)

            # Confirm gesture if at least 2 votes in buffer for responsive actuation
            if self.gesture_buffer.count(gid) >= 2:
                if gid != self.current_gesture:
                    self.gesture_buffer.clear()
                    self.get_logger().info(f'Gesture confirmed: {msg.gesture_label} (ID: {gid})')

                self.current_gesture = gid
                self.gesture_triggered = True

                if not self.locked_on:
                    self.locked_on = True
                    self.lock_time = time.monotonic()
                    self.get_logger().info(f'Subject LOCKED — active operator confirmed: {msg.gesture_label}')

    def reset_lock_callback(self, request, response):
        if request.data:
            self.locked_on = False
            self.lock_time = None
            self.gesture_triggered = False
            self.current_gesture = GESTURE_NONE
            self.gesture_buffer.clear()
            response.success = True
            response.message = 'Subject lock reset successfully'
            self.get_logger().info('Lock reset via service call')
        else:
            response.success = False
            response.message = 'No action taken'
        return response

    # ── HELPERS ───────────────────────────────────────────────────

    def make_cmd(self, linear=0.0, angular=0.0):
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        return twist

    # ── CONTROL LOOP (10 Hz) ──────────────────────────────────────

    def control_loop(self):
        # In non-GESTURE modes (e.g. AUTO, MANUAL, PAUSE), yield control to Nav2 / Teleop
        if self.system_mode != "GESTURE":
            return

        now = time.monotonic()

        # Handle subject lock timeout with mode-aware tolerance
        if self.locked_on and self.lock_time is not None:
            timeout_limit = self.reacquisition_timeout_sec if self.current_gesture == GESTURE_FOLLOW else self.lock_timeout
            elapsed = now - self.lock_time
            if elapsed > timeout_limit:
                self.locked_on = False
                self.lock_time = None
                self.gesture_triggered = False
                self.current_gesture = GESTURE_NONE
                self.gesture_buffer.clear()
                self.get_logger().info(f'Subject UNLOCKED — operator absent for {elapsed:.1f}s')

        # Check battery cutoff state (Priority 0 Emergency Lockout)
        if self.battery_cutoff_active:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
            self.get_logger().warn(
                f"BATTERY CUTOFF ACTIVE ({self.battery_voltage:.1f}V): Autonomy locked out to protect cells.",
                throttle_duration_sec=3.0
            )
            return

        # Periodic Low Battery Warning Chime
        if self.battery_voltage < self.low_battery_warn_v:
            if now - self.battery_last_warn_time > 10.0:
                self.battery_last_warn_time = now
                beep_msg = UInt16()
                beep_msg.data = 100
                self.beep_pub.publish(beep_msg)
                self.get_logger().warn(
                    f"BATTERY LOW: {self.battery_voltage:.1f}V (< {self.low_battery_warn_v:.1f}V). Please charge.",
                    throttle_duration_sec=5.0
                )

        # Check active reactive reverse safety maneuver (Priority 1)
        if self.safety_reverse_active and self.safety_reverse_start_time is not None:
            # Emergency Rear Obstacle Guard: Abort reverse immediately if rear corridor is blocked
            if self.rear_safety_blocked:
                self.safety_reverse_active = False
                self.safety_reverse_start_time = None
                self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
                beep_msg = UInt16()
                beep_msg.data = 250
                self.beep_pub.publish(beep_msg)
                self.get_logger().warn(
                    f"SAFETY REVERSE ABORTED: Rear obstacle at {self.min_rear_distance:.2f}m "
                    f"(< {self.lidar_rear_safety_distance:.2f}m)! Chassis halted.",
                    throttle_duration_sec=1.0
                )
                return

            elapsed_reverse = now - self.safety_reverse_start_time
            if elapsed_reverse < self.reverse_duration:
                # Command negative linear velocity to reverse 20 cm
                cmd_linear = -self.reverse_speed
                cmd_angular = 0.0
                self.cmd_vel_pub.publish(self.make_cmd(cmd_linear, cmd_angular))

                # Audible Industrial Backup Alarm Pulse (100ms tone every 400ms while reversing)
                if now - self.last_reverse_beep_time > 0.40:
                    self.last_reverse_beep_time = now
                    beep_msg = UInt16()
                    beep_msg.data = 100
                    self.beep_pub.publish(beep_msg)

                self.get_logger().warn(
                    f"SAFETY REVERSE ACTIVE: Retracting chassis (t={elapsed_reverse:.1f}/{self.reverse_duration:.1f}s)",
                    throttle_duration_sec=0.5
                )
                return
            else:
                self.safety_reverse_active = False
                self.safety_reverse_start_time = None
                self.get_logger().info("SAFETY REVERSE COMPLETED: 20 cm recovery displacement achieved.")

        # If no subject present and not locked, stay parked
        if not self.locked_on and not self.person_detected:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
            self.get_logger().info(
                'Waiting — no interaction subject detected',
                throttle_duration_sec=3.0
            )
            return

        cmd_linear = 0.0
        cmd_angular = 0.0

        # Execute gesture state machine
        if self.current_gesture == GESTURE_STOP:
            self.get_logger().info('CMD: STOP — wheels halted', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_GO:
            cmd_linear = self.linear_speed
            self.get_logger().info(f'CMD: GO — translating forward at {self.linear_speed:.2f} m/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_BACK:
            if self.rear_safety_blocked:
                cmd_linear = 0.0
                self.get_logger().warn(
                    f"CMD: BACK INHIBITED — rear obstacle at {self.min_rear_distance:.2f}m "
                    f"(< {self.lidar_rear_safety_distance:.2f}m)",
                    throttle_duration_sec=1.5
                )
            else:
                cmd_linear = -self.linear_speed * 0.6
                self.get_logger().info(f'CMD: BACK — reversing at {cmd_linear:.2f} m/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_LEFT:
            cmd_angular = self.angular_speed
            self.get_logger().info(f'CMD: LEFT — pivoting at {self.angular_speed:.2f} rad/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_RIGHT:
            cmd_angular = -self.angular_speed
            self.get_logger().info(f'CMD: RIGHT — pivoting at {-self.angular_speed:.2f} rad/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_FOLLOW:
            time_since_seen = (now - self.last_seen_time) if self.last_seen_time else 999.0

            if self.person_detected and time_since_seen < 1.0:
                # ── STAGE 1: ACTIVE VISUAL SERVOING ──
                # Normalized optical error: center is 0.50. Error > 0 => person right => steer right (negative angular z)
                optical_error = self.person_center_x - 0.5

                # Coupled eye-to-base turning: add physical gimbal pan angle in normalized FOV space
                pan_fresh = (now - self.last_pan_time) < 0.5 if self.last_pan_time > 0 else False
                if self.enable_coupled_gimbal_yaw and pan_fresh:
                    # Camera HFOV is 65.0 deg. Normalize gimbal pan to match optical error scale
                    gimbal_pan_norm = self.gimbal_pan_deg / 65.0
                    total_error = gimbal_pan_norm + optical_error
                else:
                    total_error = optical_error

                self.last_target_bearing = total_error

                # Visual centering deadband (±4% of frame) to eliminate chassis jitter when aligned
                if abs(total_error) < 0.04:
                    cmd_angular = 0.0
                else:
                    cmd_angular = -total_error * self.follow_kp_angular
                    cmd_angular = max(-self.angular_speed, min(self.angular_speed, cmd_angular))

                # Progressive social distance holding:
                # - Close proximity (> 0.42 frame width): Stop completely
                # - Mid proximity (0.32 - 0.42 frame width): Smooth 50% deceleration
                # - Far proximity (<= 0.32 frame width): Full follow cruise speed
                if self.person_width > 0.42:
                    cmd_linear = 0.0
                    self.get_logger().info(f'CMD: FOLLOW — holding social distance (w={self.person_width:.2f})', throttle_duration_sec=1.5)
                elif self.person_width > 0.32:
                    cmd_linear = self.follow_speed * 0.5
                    self.get_logger().info(f'CMD: FOLLOW — smooth approach damping (v={cmd_linear:.2f}, w={cmd_angular:.2f})', throttle_duration_sec=1.5)
                else:
                    cmd_linear = self.follow_speed
                    self.get_logger().info(f'CMD: FOLLOW — following person (v={self.follow_speed:.2f}, w={cmd_angular:.2f})', throttle_duration_sec=1.5)

            elif time_since_seen <= 2.0:
                # ── STAGE 2: MOMENTARY COAST & INTENTION HOLD ──
                cmd_linear = 0.0
                # Continue orienting smoothly toward last known bearing
                cmd_angular = max(-0.25, min(0.25, -self.last_target_bearing * 0.5))
                self.get_logger().info(
                    f'CMD: FOLLOW — momentary sight loss (t={time_since_seen:.1f}s <= 2.0s), holding orientation',
                    throttle_duration_sec=1.0
                )

            elif time_since_seen <= self.reacquisition_timeout_sec:
                # ── STAGE 3: SEARCH SWEEP / RE-ACQUISITION WINDOW ──
                cmd_linear = 0.0
                cmd_angular = 0.0
                self.get_logger().info(
                    f'CMD: FOLLOW — awaiting visual re-acquisition (t={time_since_seen:.1f}s <= {self.reacquisition_timeout_sec:.1f}s)',
                    throttle_duration_sec=1.5
                )

            else:
                cmd_linear = 0.0
                cmd_angular = 0.0

        else:
            self.get_logger().info(
                'Subject detected — awaiting confirmed gesture (GO, FOLLOW, STOP, etc.)',
                throttle_duration_sec=3.0
            )

        # If safety halt is active (obstacle still within breach threshold), clamp any forward motion
        if self.safety_halt_active:
            if cmd_linear > 0.0:
                self.get_logger().warn(
                    f"MOTION CLAMPED: Forward drive blocked by obstacle in corridor at {self.min_frontal_distance:.2f}m (< {self.lidar_safety_distance:.2f}m)!",
                    throttle_duration_sec=1.5
                )
                cmd_linear = 0.0

        self.cmd_vel_pub.publish(self.make_cmd(cmd_linear, cmd_angular))


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
