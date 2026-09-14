#!/usr/bin/env python3
"""
test_safety_reactive_reverse.py — Automated Verification Suite for LiDAR Safety & Active Reverse
Cognition Robot Project — Milestone 10 (Domino 5 Safety Gate)

Tests:
1. Clear environment (distance >= 0.36m) permits autonomous motion
2. Frontal obstacle breach (< 0.36m) immediately triggers safety halt & active reverse
3. Active reverse executes controlled 20 cm retract maneuver (-0.12 m/s for 1.67s)
4. Persistent obstacle clamps forward commands while allowing rotational turns
5. Hysteresis clearance (>= 0.45m) restores normal gesture execution
6. Peripheral obstacles outside frontal cone (+/- 45 deg) do not cause false halts
"""

import math
import os
import sys
import time
import unittest

WORKSPACE_PATH = "/home/j/ros2_cognition_ws"
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from cognition_interfaces.msg import Gesture, Detection

from src_nodes.brain_node import (
    BrainNode,
    GESTURE_NONE,
    GESTURE_BACK,
    GESTURE_FOLLOW,
    GESTURE_GO,
    GESTURE_LEFT,
    GESTURE_RIGHT,
    GESTURE_STOP,
)


class TestSafetyReactiveReverse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        if rclpy.ok():
            rclpy.shutdown()

    def setUp(self):
        self.node = BrainNode()
        self.published_twists = []

        # Intercept publisher to capture output velocity commands
        self.original_pub = self.node.cmd_vel_pub.publish
        self.node.cmd_vel_pub.publish = self._capture_publish

    def tearDown(self):
        self.node.destroy_node()

    def _capture_publish(self, msg):
        self.published_twists.append(msg)
        return self.original_pub(msg)

    def _send_detection(self, center_x=0.5, width=0.25, confidence=0.85):
        msg = Detection()
        msg.label = 'person'
        msg.confidence = float(confidence)
        msg.center_x = float(center_x)
        msg.width = float(width)
        self.node.detection_callback(msg)

    def _send_gesture(self, gesture_id, gesture_label="GO"):
        for _ in range(3):
            msg = Gesture()
            msg.gesture_id = int(gesture_id)
            msg.gesture_label = gesture_label
            msg.confidence = 0.95
            self.node.gesture_callback(msg)

    def _make_scan(self, default_range=2.0, num_points=360):
        scan = LaserScan()
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = (2.0 * math.pi) / num_points
        scan.range_min = 0.05
        scan.range_max = 12.0
        scan.ranges = [float(default_range)] * num_points
        return scan

    def _inject_obstacle(self, distance_m, angle_deg=0.0):
        scan = self._make_scan(default_range=2.5, num_points=360)
        # Calculate index for given angle
        angle_rad = math.radians(angle_deg)
        idx = int((angle_rad - scan.angle_min) / scan.angle_increment)
        idx = max(0, min(len(scan.ranges) - 1, idx))
        scan.ranges[idx] = float(distance_m)
        self.node.scan_callback(scan)

    # ── TESTS ──────────────────────────────────────────────────────

    def test_01_clear_environment_allows_motion(self):
        """Verify that when frontal ranges >= 0.36m, GO gesture translates at full speed."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")
        self._inject_obstacle(distance_m=1.20, angle_deg=0.0)

        self.assertFalse(self.node.safety_halt_active)
        self.assertFalse(self.node.safety_reverse_active)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.25)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)
        print("\n✓ Test 01: Clear path (1.20m >= 0.36m) permits full GO translation (0.25 m/s)")

    def test_02_frontal_obstacle_breach_triggers_emergency_clamp(self):
        """Verify that obstacle within 0.36m immediately trips safety and initiates reverse."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")

        # Inject obstacle at 0.28m (< 0.36m) directly ahead (0 deg)
        self._inject_obstacle(distance_m=0.28, angle_deg=0.0)

        self.assertTrue(self.node.safety_halt_active)
        self.assertTrue(self.node.safety_reverse_active)
        self.assertAlmostEqual(self.node.min_frontal_distance, 0.28)

        # Control loop should execute active reverse (-0.12 m/s)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, -0.12)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)
        print("✓ Test 02: Frontal obstacle breach at 0.28m triggers emergency active reverse (-0.12 m/s)")

    def test_03_active_reverse_displacement_duration(self):
        """Verify active reverse maintains retraction until timeout, achieving 20 cm displacement."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")
        self._inject_obstacle(distance_m=0.25, angle_deg=0.0)

        # Simulate 1.0s elapsed (still reversing)
        self.node.safety_reverse_start_time = time.monotonic() - 1.0
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, -0.12)

        # Simulate 2.0s elapsed (> reverse_duration 1.67s)
        self.node.safety_reverse_start_time = time.monotonic() - 2.0
        self.published_twists.clear()
        self.node.control_loop()
        self.assertFalse(self.node.safety_reverse_active)
        # Forward motion must still be clamped because obstacle is still at 0.25m
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        print("✓ Test 03: Active reverse duration (1.67s @ 0.12 m/s = 20.0 cm) verified and safely completes")

    def test_04_persistent_obstacle_clamps_forward_drive_but_allows_turn(self):
        """Verify forward commands are clamped, but angular turns away are permitted."""
        self._send_detection()
        self._inject_obstacle(distance_m=0.30, angle_deg=0.0)
        self.node.safety_reverse_active = False  # Reverse completed

        # 1. GO command must be clamped to 0.0
        self._send_gesture(GESTURE_GO, "GO")
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)

        # 2. LEFT turn command must be allowed
        self._send_gesture(GESTURE_LEFT, "LEFT")
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.40)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)

        # 3. RIGHT turn command must be allowed
        self._send_gesture(GESTURE_RIGHT, "RIGHT")
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].angular.z, -0.40)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)

        print("✓ Test 04: Forward motion clamped (0.0 m/s); pivot maneuvers (LEFT/RIGHT) permitted to escape")

    def test_05_hysteresis_clearance_restores_motion(self):
        """Verify that when obstacle moves beyond clearance threshold (>= 0.45m), safety releases."""
        self._send_detection()
        self._inject_obstacle(distance_m=0.25, angle_deg=0.0)
        self.assertTrue(self.node.safety_halt_active)

        # Clear obstacle to 0.50m (>= 0.45m clearance threshold)
        self._inject_obstacle(distance_m=0.50, angle_deg=0.0)
        self.assertFalse(self.node.safety_halt_active)

        self._send_gesture(GESTURE_GO, "GO")
        self.node.safety_reverse_active = False
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.25)
        print("✓ Test 05: Hysteresis clearance (0.50m >= 0.45m) restores full forward GO capability")

    def test_06_peripheral_obstacles_outside_cone_ignored(self):
        """Verify that obstacles outside frontal collision cone (+/- 45 deg) do not trigger false halts."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")

        # Inject obstacle close (0.25m) but at 75 degrees (flank/side wall)
        self._inject_obstacle(distance_m=0.25, angle_deg=75.0)

        self.assertFalse(self.node.safety_halt_active)
        self.assertFalse(self.node.safety_reverse_active)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.25)
        print("✓ Test 06: Lateral obstacle at 75 deg (outside +/-45 deg cone) ignored — zero false halts")

    def test_07_lateral_obstacle_outside_corridor_ignored(self):
        """Verify that an obstacle at 40 deg with y=0.25m (outside 0.18m corridor) does not halt."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")

        # Obstacle at angle=40 deg, distance=0.38m -> x = 0.38*cos(40) = 0.29m, y = 0.38*sin(40) = 0.24m
        # y=0.24m is outside half_corridor=0.18m, so it must NOT trip emergency halt
        self._inject_obstacle(distance_m=0.38, angle_deg=40.0)

        self.assertFalse(self.node.safety_halt_active)
        self.assertFalse(self.node.safety_reverse_active)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.25)
        print("✓ Test 07: Lateral obstacle at y=0.24m (outside 0.18m corridor) ignored — zero false halts")

    def test_08_coupled_gimbal_yaw_steering(self):
        """Verify that when the gimbal is panned to -30 deg, FOLLOW mode commands positive yaw to align chassis."""
        from std_msgs.msg import Int32
        # Human centered in camera image (optical error = 0)
        self._send_detection(center_x=0.50, width=0.25)
        self._send_gesture(GESTURE_FOLLOW, "FOLLOW")

        # Gimbal panned left (-30 deg)
        servo_msg = Int32()
        servo_msg.data = -30
        self.node.servo_s1_callback(servo_msg)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        # Target bearing = -30 deg (-0.523 rad). Law: cmd_angular = -bearing * Kp = -(-0.523)*1.5 = +0.78 -> clamped to +0.40
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.40)
        print("✓ Test 08: Coupled gimbal yaw (-30 deg pan) drives chassis rotation (+0.40 rad/s) toward operator")

    def test_09_battery_cutoff_clamps_velocity(self):
        """Verify that battery voltage below 6.8V triggers safety cutoff and clamps cmd_vel to zero."""
        from std_msgs.msg import UInt16
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")

        # Inject low battery 6.6V (encoded as 66)
        bat_msg = UInt16()
        bat_msg.data = 66
        self.node.battery_callback(bat_msg)

        self.assertTrue(self.node.battery_cutoff_active)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)
        print("✓ Test 09: Battery cutoff at 6.6V (< 6.8V) safely locks out motors (cmd_vel = 0.0)")

    def _inject_dual_obstacle(self, front_dist_m=0.20, rear_dist_m=0.15):
        scan = self._make_scan(default_range=2.5, num_points=360)
        # Frontal at 0 deg
        idx_front = int((0.0 - scan.angle_min) / scan.angle_increment)
        idx_front = max(0, min(len(scan.ranges) - 1, idx_front))
        scan.ranges[idx_front] = float(front_dist_m)
        # Rear at 180 deg (pi rad)
        idx_rear = int((math.pi - scan.angle_min) / scan.angle_increment)
        idx_rear = max(0, min(len(scan.ranges) - 1, idx_rear))
        scan.ranges[idx_rear] = float(rear_dist_m)
        self.node.scan_callback(scan)

    def test_10_rear_clear_allows_reactive_reverse(self):
        """Verify that frontal breach with clear rear triggers standard 20 cm reactive reverse."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")
        # Frontal obstacle at 0.20m (< 0.36m), rear is clear at default 2.5m
        self._inject_obstacle(distance_m=0.20, angle_deg=0.0)

        self.assertTrue(self.node.safety_halt_active)
        self.assertTrue(self.node.safety_reverse_active)
        self.assertFalse(self.node.rear_safety_blocked)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, -0.12)
        print("✓ Test 10: Clear rear allows standard reactive reverse (-0.12 m/s)")

    def test_11_rear_blocked_prevents_reactive_reverse(self):
        """Verify that frontal breach when rear is blocked (< 0.25m) halts chassis without reversing."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")
        # Frontal obstacle at 0.20m (< 0.36m), Rear obstacle at 0.15m (< 0.25m)
        self._inject_dual_obstacle(front_dist_m=0.20, rear_dist_m=0.15)

        self.assertTrue(self.node.safety_halt_active)
        self.assertTrue(self.node.rear_safety_blocked)
        self.assertFalse(self.node.safety_reverse_active)  # Reverse must NOT activate!

        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)
        print("✓ Test 11: Blocked rear (0.15m < 0.25m) prevents reverse — chassis safely halts at 0.0 m/s")

    def test_12_rear_obstacle_during_reverse_aborts_immediately(self):
        """Verify that an obstacle appearing behind the robot mid-reverse aborts maneuver instantly."""
        self._send_detection()
        self._send_gesture(GESTURE_GO, "GO")
        # Start reactive reverse (rear was clear)
        self._inject_obstacle(distance_m=0.20, angle_deg=0.0)
        self.assertTrue(self.node.safety_reverse_active)

        # Dynamic rear obstacle suddenly appears at 0.12m
        self._inject_obstacle(distance_m=0.12, angle_deg=180.0)
        self.assertTrue(self.node.rear_safety_blocked)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertFalse(self.node.safety_reverse_active)  # Reverse must be aborted immediately!
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        print("✓ Test 12: Dynamic obstacle behind robot aborts active reverse in-flight instantly")

    def test_13_gesture_back_inhibited_by_rear_obstacle(self):
        """Verify that GESTURE_BACK commands zero linear velocity when rear corridor is obstructed."""
        self._send_detection()
        self._send_gesture(GESTURE_BACK, "BACK")

        # Rear obstructed at 0.18m (< 0.25m)
        self._inject_obstacle(distance_m=0.18, angle_deg=180.0)
        self.assertTrue(self.node.rear_safety_blocked)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        print("✓ Test 13: GESTURE_BACK is safely inhibited (0.0 m/s) when rear obstacle is detected")


if __name__ == '__main__':
    unittest.main()


