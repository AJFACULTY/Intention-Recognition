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
import os
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
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
        self.declare_parameter('gesture_buffer_size', 5)
        self.declare_parameter('lock_timeout', 3.0)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_gesture')
        self.declare_parameter('gesture_topic', '/cognition/gesture')
        self.declare_parameter('require_face_auth', False)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.angular_speed = float(self.get_parameter('angular_speed').value)
        self.follow_speed = float(self.get_parameter('follow_speed').value)
        self.buffer_size = int(self.get_parameter('gesture_buffer_size').value)
        self.lock_timeout = float(self.get_parameter('lock_timeout').value)
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.gesture_topic = self.get_parameter('gesture_topic').value
        self.require_face_auth = bool(self.get_parameter('require_face_auth').value)

        # ── Publishers ──────────────────────────────────────────
        # Publishes to /cmd_vel_gesture (Priority 40 in twist_mux)
        self.cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)

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

        # 10 Hz Real-Time Control Loop Timer
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info(
            f'BrainNode started — cmd_vel_topic={self.cmd_vel_topic}, '
            f'gesture_topic={self.gesture_topic}, '
            f'require_face_auth={self.require_face_auth}, '
            f'linear={self.linear_speed:.2f}, follow={self.follow_speed:.2f}'
        )

    # ── CALLBACKS ─────────────────────────────────────────────────

    def mode_callback(self, msg: String):
        """Receive system mode updates (GESTURE vs AUTO/NAV2 mode)."""
        new_mode = msg.data.strip().upper()
        if new_mode in ("GESTURE", "AUTO", "MANUAL", "PAUSE"):
            if new_mode != self.system_mode:
                self.system_mode = new_mode
                self.get_logger().info(f"System mode switched to: {self.system_mode}")

    def face_identity_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
            self.operator_authorized = bool(payload.get("authorized", False))
            self.operator_name = payload.get("name", "Unknown")
            self.last_face_time = time.monotonic()
        except Exception as e:
            self.get_logger().error(f"Error parsing face identity JSON: {e}")

    def detection_callback(self, msg: Detection):
        if msg.label == 'person' and msg.confidence > 0.45:
            self.person_detected = True
            self.person_center_x = msg.center_x
            self.person_width = msg.width
            self.last_seen_time = time.monotonic()
            if self.locked_on:
                self.lock_time = time.monotonic()
        else:
            # Clear person flag only after 1.0s grace period to tolerate frame skips
            if self.last_seen_time is None or (time.monotonic() - self.last_seen_time) > 1.0:
                self.person_detected = False

    def gesture_callback(self, msg: Gesture):
        if not self.person_detected:
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

        # Handle subject lock timeout
        if self.locked_on and self.lock_time is not None:
            elapsed = now - self.lock_time
            if elapsed > self.lock_timeout:
                self.locked_on = False
                self.lock_time = None
                self.gesture_triggered = False
                self.current_gesture = GESTURE_NONE
                self.gesture_buffer.clear()
                self.get_logger().info(f'Subject UNLOCKED — operator absent for {elapsed:.1f}s')

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
            cmd_linear = -self.linear_speed * 0.6
            self.get_logger().info(f'CMD: BACK — reversing at {cmd_linear:.2f} m/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_LEFT:
            cmd_angular = self.angular_speed
            self.get_logger().info(f'CMD: LEFT — pivoting at {self.angular_speed:.2f} rad/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_RIGHT:
            cmd_angular = -self.angular_speed
            self.get_logger().info(f'CMD: RIGHT — pivoting at {-self.angular_speed:.2f} rad/s', throttle_duration_sec=1.5)

        elif self.current_gesture == GESTURE_FOLLOW:
            if self.person_detected:
                # Lateral visual centering error: error > 0 => person right => steer right (negative angular z)
                error = self.person_center_x - 0.5
                cmd_angular = -error * 1.5

                # Maintain social distance: if person is close (width > 0.45 of frame), hold
                if self.person_width > 0.45:
                    cmd_linear = 0.0
                    self.get_logger().info(f'CMD: FOLLOW — holding social distance (w={self.person_width:.2f})', throttle_duration_sec=1.5)
                else:
                    cmd_linear = self.follow_speed
                    self.get_logger().info(f'CMD: FOLLOW — following person (v={self.follow_speed:.2f}, w={cmd_angular:.2f})', throttle_duration_sec=1.5)
            else:
                # Person briefly lost during follow — slowly sweep to re-acquire
                cmd_angular = 0.25
                self.get_logger().info('CMD: FOLLOW — scanning to re-acquire subject', throttle_duration_sec=1.5)

        else:
            self.get_logger().info(
                'Subject detected — awaiting confirmed gesture (GO, FOLLOW, STOP, etc.)',
                throttle_duration_sec=3.0
            )

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
