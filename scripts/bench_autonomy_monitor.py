#!/usr/bin/env python3
"""
bench_autonomy_monitor.py — Live Interactive Terminal Dashboard
Monitors live vision detections, active gimbal tracking, gesture classifications,
and chassis drive commands during bench qualification.
"""

import os
import sys
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, String, UInt16
from cognition_interfaces.msg import Detection, Gesture


class BenchAutonomyMonitor(Node):
    def __init__(self):
        super().__init__("bench_autonomy_monitor")

        self.last_detection = None
        self.last_detection_time = 0.0
        self.last_gesture = None
        self.last_gesture_time = 0.0
        self.current_pan = 0
        self.current_tilt = 25
        self.gimbal_state = "IDLE"
        self.cmd_linear = 0.0
        self.cmd_angular = 0.0
        self.final_linear = 0.0
        self.final_angular = 0.0
        self.battery_pct = None

        # Subscriptions
        self.create_subscription(Detection, "/cognition/detection", self.cb_detection, 10)
        self.create_subscription(Gesture, "/cognition/gesture", self.cb_gesture, 10)
        self.create_subscription(Int32, "/servo_s1", self.cb_pan, 10)
        self.create_subscription(Int32, "/servo_s2", self.cb_tilt, 10)
        self.create_subscription(String, "/cognition/gimbal_state", self.cb_state, 10)
        self.create_subscription(Twist, "/cmd_vel_gesture", self.cb_cmd_gesture, 10)
        self.create_subscription(Twist, "/cmd_vel", self.cb_cmd_vel, 10)
        self.create_subscription(UInt16, "/battery", self.cb_battery, 10)

        self.timer = self.create_timer(0.3, self.display_hud)
        print("\033[2J\033[H", end="")  # Clear screen

    def cb_detection(self, msg: Detection):
        if msg.label == "person":
            self.last_detection = msg
            self.last_detection_time = time.time()

    def cb_gesture(self, msg: Gesture):
        self.last_gesture = msg
        self.last_gesture_time = time.time()

    def cb_pan(self, msg: Int32):
        self.current_pan = msg.data

    def cb_tilt(self, msg: Int32):
        self.current_tilt = msg.data

    def cb_state(self, msg: String):
        self.gimbal_state = msg.data

    def cb_cmd_gesture(self, msg: Twist):
        self.cmd_linear = msg.linear.x
        self.cmd_angular = msg.angular.z

    def cb_cmd_vel(self, msg: Twist):
        self.final_linear = msg.linear.x
        self.final_angular = msg.angular.z

    def cb_battery(self, msg: UInt16):
        self.battery_pct = msg.data

    def display_hud(self):
        now = time.time()
        # Check freshness
        person_present = (self.last_detection is not None) and (now - self.last_detection_time < 2.5)
        gesture_active = (self.last_gesture is not None) and (now - self.last_gesture_time < 3.5)

        # Format Battery
        if self.battery_pct is not None:
            b_color = "\033[92m" if self.battery_pct >= 40 else "\033[93m" if self.battery_pct >= 20 else "\033[91m"
            bat_str = f"{b_color}{self.battery_pct}% (Healthy)\033[0m"
        else:
            bat_str = "\033[90mREADING...\033[0m"

        # Format Person Detection
        if person_present:
            det = self.last_detection
            person_str = f"\033[92mYES (LOCKED)\033[0m (Conf: {det.confidence:.2f} | Centroid: [{det.center_x:.2f}, {det.center_y:.2f}])"
        elif self.last_detection is not None:
            time_ago = now - self.last_detection_time
            person_str = f"\033[93mLOST ({time_ago:.1f}s ago)\033[0m — Gimbal Searching FOV"
        else:
            person_str = "\033[93mSEARCHING...\033[0m (No person in frame)"

        # Format Gesture
        if gesture_active and self.last_gesture.gesture_id >= 0:
            g = self.last_gesture
            label = g.gesture_label.upper()
            color = "\033[92m" if label in ("GO", "FOLLOW") else "\033[91m" if label == "STOP" else "\033[94m"
            gesture_str = f"{color}▶ {label}\033[0m (Conf: {g.confidence:.2f}) [CONFIRMED]"
        elif self.last_gesture is not None and self.last_gesture.gesture_id >= 0:
            g = self.last_gesture
            label = g.gesture_label.upper()
            time_ago = now - self.last_gesture_time
            gesture_str = f"\033[90mLAST: {label} ({time_ago:.1f}s ago) — AWAITING NEXT GESTURE\033[0m"
        elif gesture_active and self.last_gesture.gesture_label == "TOO_FAR":
            gesture_str = "\033[93mHAND DETECTED (MOVE CLOSER)\033[0m"
        else:
            gesture_str = "\033[90mWAITING FOR HAND GESTURE\033[0m"

        # Format Chassis Motion (support either /cmd_vel or /cmd_vel_gesture)
        active_linear = self.final_linear if abs(self.final_linear) > 0.005 else self.cmd_linear
        active_angular = self.final_angular if abs(self.final_angular) > 0.005 else self.cmd_angular

        if abs(active_linear) > 0.01:
            wheel_str = f"\033[92mSPINNING FORWARD ({active_linear:+.2f} m/s)\033[0m"
        elif abs(active_angular) > 0.01:
            turn = "LEFT" if active_angular > 0 else "RIGHT"
            wheel_str = f"\033[94mTURNING {turn} ({active_angular:+.2f} rad/s)\033[0m"
        else:
            wheel_str = "\033[90mPARKED / HALTED (0.00 m/s)\033[0m"

        # Gimbal State Color
        state_color = "\033[92m" if self.gimbal_state in ("TRACKING", "TASK_FORWARD") else "\033[93m" if self.gimbal_state == "SEARCH" else "\033[96m"

        # Render Terminal UI with \033[K (clear line to prevent ghost characters)
        output = [
            "\033[H",  # Move cursor to home
            "================================================================================\033[K",
            "           COGNITION ROBOTICS — BENCH AUTONOMY LIVE DEMO MONITOR\033[K",
            f"           Robot Battery: {bat_str} | FastDDS Domain: 20\033[K",
            "================================================================================\033[K",
            f"  [1] PERSON DETECTION   : {person_str}\033[K",
            f"  [2] ACTIVE GIMBAL      : Pan = {self.current_pan:3d}° | Tilt = {self.current_tilt:3d}° | State: {state_color}{self.gimbal_state}\033[0m\033[K",
            f"  [3] HAND GESTURE       : {gesture_str}\033[K",
            f"  [4] BRAIN /cmd_vel     : Linear = {active_linear:+.2f} m/s | Angular = {active_angular:+.2f} rad/s\033[K",
            f"  [5] CHASSIS ACTUATION  : {wheel_str}\033[K",
            "--------------------------------------------------------------------------------\033[K",
            "  GESTURE CONTROLS FOR OPERATOR:\033[K",
            "  * OPEN PALM           -> STOP   (Wheels halt instantly)\033[K",
            "  * INDEX POINT / THUMB -> GO     (Wheels spin forward at 0.25 m/s)\033[K",
            "  * V-SIGN / PEACE      -> FOLLOW (Wheels steer and follow operator distance)\033[K",
            "  * STEP LEFT / RIGHT   -> Active gimbal smoothly tracks and centers your torso\033[K",
            "================================================================================\033[K",
            "  [Press Ctrl+C in launch terminal to safely conclude test]\033[K",
        ]
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()


def main():
    rclpy.init()
    node = BenchAutonomyMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
