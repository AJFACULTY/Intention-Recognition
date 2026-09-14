#!/usr/bin/env python3
"""
active_vision_node.py — Production 2-DOF Pan/Tilt Active Gimbal Tracking Node
Cognition Robot Project

Mathematical Formulation:
- Decoupled Image-Based Visual Servoing (IBVS) Controller
- Proportional-Integral (PI) control law with anti-windup
- Nonlinear deadband filtering to eliminate servo gear buzzing/jitter
- Slew-rate limiting to prevent image motion blur
- Finite State Machine (FSM): IDLE, TRACKING, SEARCH_SWEEP, RETURN_HOME
- Target: Centering human face (and hand gestures) dynamically in camera FOV
- Hardware Topics: /servo_s1 (Pan: 0-180 deg) and /servo_s2 (Tilt: 0-180 deg)
"""

import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Int32, String


class ActiveVisionNode(Node):
    # FSM State Constants
    STATE_IDLE = "IDLE"
    STATE_TRACKING = "TRACKING"
    STATE_MEMORY_HOLD = "MEMORY_HOLD"
    STATE_SEARCH = "SEARCH"
    STATE_REVERT = "REVERT"

    def __init__(self):
        super().__init__("active_vision_node")

        # Configurable Parameters (Yahboom 0-Centric Hardware Protocol: 0 deg = Center Forward)
        self.declare_parameter("pan_home", 0)          # Hardware neutral center forward (0 deg)
        self.declare_parameter("tilt_home", 8)         # Forward level horizon (+8 deg, clear of motor)
        self.declare_parameter("pan_min", -60)         # Max left pan (-60 deg)
        self.declare_parameter("pan_max", 60)          # Max right pan (+60 deg)
        self.declare_parameter("tilt_min", -15)        # Lower tilt limit (-15 deg)
        self.declare_parameter("tilt_max", 18)         # Upper tilt limit (+18 deg, prevents hitting motor)

        # Control Gains
        self.declare_parameter("kp_pan", 18.0)         # Deg per normalized unit error
        self.declare_parameter("ki_pan", 1.2)          # Integral gain
        self.declare_parameter("kd_pan", 2.5)          # Derivative damping (prevents hunting/overshoot)
        self.declare_parameter("kp_tilt", 14.0)        # Deg per normalized unit error
        self.declare_parameter("ki_tilt", 1.0)         # Integral gain
        self.declare_parameter("kd_tilt", 2.0)         # Derivative damping

        # Smoothing & PTZ Slew Rate
        self.declare_parameter("alpha_ema", 0.35)      # Centroid Exponential Moving Average smoothing
        self.declare_parameter("deadband", 0.05)       # 5% deadband window (anti-jitter)
        self.declare_parameter("max_slew_deg", 0.8)    # 0.8 deg/tick @ 20Hz = 16 deg/sec smooth glide (eliminates snapping)
        self.declare_parameter("control_rate_hz", 20.0)# 20 Hz control loop

        # Target Topic, Timeout & Search
        self.declare_parameter("target_topic", "/cognition/face_target")
        self.declare_parameter("target_timeout", 1.5)  # Seconds of target loss before search
        self.declare_parameter("search_duration", 30.0)# Seconds to search before reverting (30s)
        self.declare_parameter("search_amplitude", 28.0) # Safe cable-friendly sweep (+/- 28 deg arc)
        self.declare_parameter("search_freq", 0.10)    # Sweep frequency (0.10 Hz = 10s smooth wide cycle)
        self.declare_parameter("enable_patrol_sweep", True) # Dynamic sinusoidal sweep during patrol

        # Read parameters
        self.target_topic = str(self.get_parameter("target_topic").value)
        self.pan_home = int(self.get_parameter("pan_home").value)
        self.tilt_home = int(self.get_parameter("tilt_home").value)
        self.pan_min = int(self.get_parameter("pan_min").value)
        self.pan_max = int(self.get_parameter("pan_max").value)
        self.tilt_min = int(self.get_parameter("tilt_min").value)
        self.tilt_max = int(self.get_parameter("tilt_max").value)

        self.kp_pan = float(self.get_parameter("kp_pan").value)
        self.ki_pan = float(self.get_parameter("ki_pan").value)
        self.kd_pan = float(self.get_parameter("kd_pan").value)
        self.kp_tilt = float(self.get_parameter("kp_tilt").value)
        self.ki_tilt = float(self.get_parameter("ki_tilt").value)
        self.kd_tilt = float(self.get_parameter("kd_tilt").value)

        self.alpha_ema = float(self.get_parameter("alpha_ema").value)
        self.deadband = float(self.get_parameter("deadband").value)
        self.max_slew_deg = float(self.get_parameter("max_slew_deg").value)
        self.control_rate = float(self.get_parameter("control_rate_hz").value)

        self.target_timeout = float(self.get_parameter("target_timeout").value)
        self.search_duration = float(self.get_parameter("search_duration").value)
        self.search_amp = float(self.get_parameter("search_amplitude").value)
        self.search_freq = float(self.get_parameter("search_freq").value)
        self.enable_patrol_sweep = bool(self.get_parameter("enable_patrol_sweep").value)

        # Internal Control State
        self.current_pan = float(self.pan_home)
        self.current_tilt = float(self.tilt_home)
        self.integral_pan = 0.0
        self.integral_tilt = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0
        self.filtered_target_x = 0.0
        self.filtered_target_y = 0.0
        self.has_filtered_target = False

        self.state = self.STATE_IDLE
        self.last_target_time = 0.0
        self.search_start_time = 0.0
        self.latest_target = None
        self.last_go_time = 0.0
        self.node_start_time = time.time()

        # Publishers
        self.pan_pub = self.create_publisher(Int32, "/servo_s1", 10)
        self.tilt_pub = self.create_publisher(Int32, "/servo_s2", 10)
        self.state_pub = self.create_publisher(String, "/cognition/gimbal_state", 10)

        # Face target time for dedicated priority tracking
        self.last_face_time = 0.0

        # Subscribers
        self.sub_target = self.create_subscription(
            Point,
            self.target_topic,
            self.face_target_callback,
            10,
        )

        # Hand Target subscriber (Point msg from MediaPipe Gesture Node)
        self.last_hand_time = 0.0
        self.sub_hand = self.create_subscription(
            Point,
            "/cognition/hand_target",
            self.hand_callback,
            10,
        )

        # Fallback/Primary Person Detection subscriber (Detection msg from YOLOv8)
        try:
            from cognition_interfaces.msg import Detection
            self.sub_detection = self.create_subscription(
                Detection,
                "/cognition/detection",
                self.detection_callback,
                10,
            )
        except ImportError:
            self.sub_detection = None

        # Gesture subscriber (allows returning to forward task pose on GO command)
        self.current_gesture = -1
        try:
            from cognition_interfaces.msg import Gesture
            self.sub_gesture = self.create_subscription(
                Gesture,
                "/cognition/gesture",
                self.gesture_callback,
                10,
            )
        except ImportError:
            self.sub_gesture = None

        # Main Real-Time Control Loop Timer (20 Hz)
        timer_period = 1.0 / self.control_rate
        self.timer = self.create_timer(timer_period, self.control_loop)

        self.get_logger().info(
            f"ActiveVisionNode initialized. Home: ({self.pan_home}, {self.tilt_home}) | "
            f"Deadband: {self.deadband} | Control Rate: {self.control_rate} Hz (Smooth Glide Enabled)"
        )

    def face_target_callback(self, msg: Point):
        """Dedicated callback for /cognition/face_target to track face priority."""
        if msg.z > 0.0:
            self.last_face_time = time.time()
        self.target_callback(msg)

    def target_callback(self, msg: Point):
        """
        Receives normalized target coordinates:
        msg.x: normalized horizontal offset u in [-1.0, 1.0] (0 = center, -1 = left, +1 = right)
        msg.y: normalized vertical offset v in [-1.0, 1.0] (0 = center, -1 = top, +1 = bottom)
        msg.z: detection confidence (z > 0 = valid target, z <= 0 = lost/none)
        """
        if msg.z > 0.0:
            # Exponential Moving Average (EMA) filtering to eliminate bounding box detection jitter
            if not self.has_filtered_target:
                self.filtered_target_x = float(msg.x)
                self.filtered_target_y = float(msg.y)
                self.has_filtered_target = True
            else:
                self.filtered_target_x = float(self.alpha_ema * msg.x + (1.0 - self.alpha_ema) * self.filtered_target_x)
                self.filtered_target_y = float(self.alpha_ema * msg.y + (1.0 - self.alpha_ema) * self.filtered_target_y)

            self.latest_target = msg
            self.last_target_time = time.time()
            if self.state not in (self.STATE_TRACKING, self.STATE_MEMORY_HOLD):
                self.get_logger().info(f"Target acquired (confidence: {msg.z:.2f}). Transition to TRACKING.")
            self.state = self.STATE_TRACKING
        else:
            # Explicit target loss signaled (z <= 0) -> immediately drop latest_target for FSM MEMORY_HOLD
            self.latest_target = None

    def hand_callback(self, msg: Point):
        """
        Ingests Hand Target message from MediaPipe Gesture Node:
        Gently blends vertical tilt to accommodate raised hands without yanking pan off the torso.
        """
        if msg.z > 0.45:
            self.last_hand_time = time.time()
            # If face is actively tracking (<0.5s), do not disrupt lock
            if (time.time() - getattr(self, 'last_face_time', 0.0)) < 0.5:
                return

            if self.latest_target is not None:
                # Soft vertical bias: preserve pan horizontal centering, gently adjust tilt
                blended = Point()
                blended.x = self.latest_target.x
                blended.y = float(0.35 * msg.y + 0.65 * self.latest_target.y)
                blended.z = float(msg.z)
                self.target_callback(blended)
            else:
                self.target_callback(msg)

    def detection_callback(self, msg):
        """
        Ingests Detection message from YOLOv8 person detector:
        msg.center_x in [0.0, 1.0] -> mapped to horizontal offset in [-1.0, 1.0]
        msg.center_y in [0.0, 1.0] -> mapped to vertical offset in [-1.0, 1.0]
        """
        # Prioritize dedicated hand target if actively gesturing (<0.6s)
        if (time.time() - getattr(self, 'last_hand_time', 0.0)) < 0.6:
            return

        # Prioritize dedicated face target if recently active (<0.5s)
        if (time.time() - getattr(self, 'last_face_time', 0.0)) < 0.5:
            return

        if getattr(msg, 'label', '') == 'person' and getattr(msg, 'confidence', 0.0) >= 0.35:
            point = Point()
            point.x = float((msg.center_x - 0.5) * 2.0)
            point.y = float((msg.center_y - 0.5) * 2.0)
            point.z = float(msg.confidence)
            self.target_callback(point)
        else:
            if (time.time() - self.last_target_time) > 1.5:
                self.latest_target = None

    def gesture_callback(self, msg):
        """Monitors active operator gesture to adapt gimbal pose (e.g. GO -> look forward)."""
        self.current_gesture = getattr(msg, 'gesture_id', -1)
        if self.current_gesture == 2:
            self.last_go_time = time.time()

    def apply_deadband(self, error: float) -> float:
        """Applies nonlinear deadband function to eliminate micro-jitter."""
        if abs(error) <= self.deadband:
            return 0.0
        return error - math.copysign(self.deadband, error)

    def clamp(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(value, max_val))

    def control_loop(self):
        dt = 1.0 / self.control_rate
        now = time.time()

        # Check target freshness (250ms freshness threshold)
        is_target_fresh = (
            self.latest_target is not None and
            (now - self.last_target_time) <= 0.25
        )

        # -------------------------------------------------------------
        # STATE MACHINE TRANSITIONS
        # -------------------------------------------------------------
        # When operator commands GO (ID: 2), gimbal maintains forward navigation pose for 3.0s
        is_go_active = (self.current_gesture == 2) or ((now - getattr(self, 'last_go_time', 0.0)) < 3.0)
        if is_go_active:
            self.state = "TASK_FORWARD"
        elif self.state in (self.STATE_TRACKING, self.STATE_MEMORY_HOLD, "TASK_FORWARD"):
            if is_target_fresh:
                self.state = self.STATE_TRACKING
            else:
                # Fresh target unavailable -> evaluate memory hold / search timeout
                if (now - self.last_target_time) > self.target_timeout:
                    self.get_logger().warn(f"Target lost for > {self.target_timeout:.1f}s. Transitioning to SEARCH mode.")
                    self.state = self.STATE_SEARCH
                    self.search_start_time = now
                    self.integral_pan = 0.0
                    self.integral_tilt = 0.0
                elif self.state != self.STATE_MEMORY_HOLD:
                    self.get_logger().info("Target temporarily lost. Entering MEMORY_HOLD.")
                    self.state = self.STATE_MEMORY_HOLD

        elif self.state == self.STATE_SEARCH:
            if is_target_fresh:
                self.get_logger().info("Target re-acquired during SEARCH. Transition to TRACKING.")
                self.state = self.STATE_TRACKING
                self.integral_pan = 0.0
                self.integral_tilt = 0.0
            elif (now - self.search_start_time) > self.search_duration:
                self.get_logger().info("Search timed out without finding target. Returning to HOME.")
                self.state = self.STATE_REVERT

        elif self.state == self.STATE_REVERT:
            if is_target_fresh:
                self.get_logger().info("Target re-acquired during REVERT. Transition to TRACKING.")
                self.state = self.STATE_TRACKING
                self.integral_pan = 0.0
                self.integral_tilt = 0.0
            else:
                # Smoothly transition back to home position
                pan_diff = self.pan_home - self.current_pan
                tilt_diff = self.tilt_home - self.current_tilt
                if abs(pan_diff) < 2.0 and abs(tilt_diff) < 2.0:
                    self.current_pan = float(self.pan_home)
                    self.current_tilt = float(self.tilt_home)
                    self.state = self.STATE_IDLE
                    self.get_logger().info("Gimbal restored to neutral HOME pose. State: IDLE.")

        elif self.state == self.STATE_IDLE:
            if is_target_fresh:
                self.get_logger().info("Target acquired from IDLE. Transition to TRACKING.")
                self.state = self.STATE_TRACKING
                self.integral_pan = 0.0
                self.integral_tilt = 0.0
            elif self.enable_patrol_sweep and (now - getattr(self, 'node_start_time', now)) > 5.0 and (now - self.last_target_time) > 5.0:
                self.get_logger().info("No subject in forward view. Initiating autonomous room search sweep.")
                self.state = self.STATE_SEARCH
                self.search_start_time = now
                self.integral_pan = 0.0
                self.integral_tilt = 0.0

        # -------------------------------------------------------------
        # CONTROLLER EXECUTION PER STATE
        # -------------------------------------------------------------
        target_pan = self.current_pan
        target_tilt = self.current_tilt

        if self.state == "TASK_FORWARD":
            # Smoothly glide to neutral forward-facing task pose (looking ahead along path)
            target_pan = float(self.pan_home)
            target_tilt = float(self.tilt_home)
            self.integral_pan = 0.0
            self.integral_tilt = 0.0

        elif self.state == self.STATE_TRACKING and is_target_fresh:
            # Normalized errors using EMA smoothed target coordinates
            raw_x = self.filtered_target_x if self.has_filtered_target else self.latest_target.x
            raw_y = self.filtered_target_y if self.has_filtered_target else self.latest_target.y
            e_x = self.apply_deadband(raw_x)
            e_y = self.apply_deadband(raw_y)

            # Derivative error calculation for smooth damping (anti-hunting)
            deriv_x = (e_x - self.prev_error_x) / dt if dt > 0 else 0.0
            deriv_y = (e_y - self.prev_error_y) / dt if dt > 0 else 0.0
            self.prev_error_x = e_x
            self.prev_error_y = e_y

            # Integrator bleed-off when inside deadband to prevent kick on exit
            if e_x == 0.0:
                self.integral_pan *= 0.90
            else:
                self.integral_pan = self.clamp(self.integral_pan + e_x * dt, -0.5, 0.5)

            if e_y == 0.0:
                self.integral_tilt *= 0.90
            else:
                self.integral_tilt = self.clamp(self.integral_tilt + e_y * dt, -0.5, 0.5)

            # Decoupled PID control law with derivative damping
            # 0-Centric kinematics: positive pan turns right; increasing tilt tilts up
            delta_pan = +(self.kp_pan * e_x + self.ki_pan * self.integral_pan + self.kd_pan * deriv_x)
            delta_tilt = -(self.kp_tilt * e_y + self.ki_tilt * self.integral_tilt + self.kd_tilt * deriv_y)

            target_pan = self.current_pan + delta_pan
            target_tilt = self.current_tilt + delta_tilt

        elif self.state == self.STATE_MEMORY_HOLD:
            # Maintain last commanded heading, bleed off integrator terms
            self.integral_pan *= 0.90
            self.integral_tilt *= 0.90
            target_pan = self.current_pan
            target_tilt = self.current_tilt

        elif self.state == self.STATE_SEARCH:
            # Symmetrical sinusoidal search sweep centered around 0 deg (neutral forward)
            elapsed = now - self.search_start_time
            sweep_offset = self.search_amp * math.sin(2.0 * math.pi * self.search_freq * elapsed)
            target_pan = self.pan_home + sweep_offset
            target_tilt = float(self.tilt_home)

        elif self.state == self.STATE_REVERT:
            target_pan = float(self.pan_home)
            target_tilt = float(self.tilt_home)

        # -------------------------------------------------------------
        # SLEW-RATE LIMITING (Anti-Blur) & MECHANICAL CLAMPING
        # -------------------------------------------------------------
        slew_limit = 2.0 if self.state == self.STATE_SEARCH else self.max_slew_deg
        pan_step = self.clamp(target_pan - self.current_pan, -slew_limit, slew_limit)
        tilt_step = self.clamp(target_tilt - self.current_tilt, -slew_limit, slew_limit)

        self.current_pan = self.clamp(self.current_pan + pan_step, self.pan_min, self.pan_max)
        self.current_tilt = self.clamp(self.current_tilt + tilt_step, self.tilt_min, self.tilt_max)

        # Publish discrete integer angle commands to hardware servos
        pan_cmd = int(round(self.current_pan))
        tilt_cmd = int(round(self.current_tilt))
        self.publish_servos(pan_cmd, tilt_cmd)

        # Publish state string
        state_msg = String()
        state_msg.data = f"{self.state}|pan:{pan_cmd}|tilt:{tilt_cmd}"
        self.state_pub.publish(state_msg)

    def publish_servos(self, pan: int, tilt: int):
        p_msg = Int32()
        p_msg.data = pan
        self.pan_pub.publish(p_msg)

        t_msg = Int32()
        t_msg.data = tilt
        self.tilt_pub.publish(t_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ActiveVisionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
