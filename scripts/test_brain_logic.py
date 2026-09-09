#!/usr/bin/env python3
"""
test_brain_logic.py — Automated Verification Suite for BrainNode
Tests:
1. Initial configuration & parameter overrides (cmd_vel_topic=/cmd_vel_gesture)
2. Unauthenticated gesture control (GO, STOP, BACK, LEFT, RIGHT)
3. Follow mode centering error & social distance holding
4. Biometric Face ID authentication gating (authorized vs unknown vs stale)
5. Subject locking FSM, timeout expiration, and reset_lock service
"""

import json
import os
import sys
import time
import unittest

WORKSPACE_PATH = "/home/j/ros2_cognition_ws"
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from std_srvs.srv import SetBool
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


class TestBrainLogic(unittest.TestCase):
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

        # Intercept publisher to capture output commands
        self.original_pub = self.node.cmd_vel_pub.publish
        self.node.cmd_vel_pub.publish = self._capture_publish

    def tearDown(self):
        self.node.destroy_node()

    def _capture_publish(self, msg):
        self.published_twists.append(msg)
        return self.original_pub(msg)

    def _send_detection(self, center_x=0.5, width=0.25, confidence=0.85, label='person'):
        msg = Detection()
        msg.label = label
        msg.confidence = float(confidence)
        msg.center_x = float(center_x)
        msg.width = float(width)
        self.node.detection_callback(msg)

    def _send_gesture(self, gesture_id, gesture_label="TEST", count=3):
        for _ in range(count):
            msg = Gesture()
            msg.gesture_id = int(gesture_id)
            msg.gesture_label = gesture_label
            msg.confidence = 0.95
            self.node.gesture_callback(msg)

    def _send_face_id(self, name="AJ", authorized=True):
        msg = String()
        msg.data = json.dumps({"name": name, "authorized": authorized})
        self.node.face_identity_callback(msg)

    # ── TESTS ──────────────────────────────────────────────────────

    def test_01_default_configuration(self):
        """Verify default parameters and topics match twist_mux specification."""
        self.assertEqual(self.node.cmd_vel_topic, '/cmd_vel_gesture')
        self.assertEqual(self.node.gesture_topic, '/cognition/gesture')
        self.assertFalse(self.node.require_face_auth)
        self.assertAlmostEqual(self.node.linear_speed, 0.25)
        self.assertAlmostEqual(self.node.angular_speed, 0.40)
        self.assertAlmostEqual(self.node.follow_speed, 0.20)
        print("\n✓ Test 01: Default configuration & twist_mux topics verified")

    def test_02_unlocked_idle_parks(self):
        """Verify that with no subject detected, the node publishes zero velocity."""
        self.published_twists.clear()
        self.node.control_loop()
        self.assertTrue(len(self.published_twists) >= 1)
        last_cmd = self.published_twists[-1]
        self.assertEqual(last_cmd.linear.x, 0.0)
        self.assertEqual(last_cmd.angular.z, 0.0)
        print("✓ Test 02: Unlocked idle state holds robot parked (0.0 m/s)")

    def test_03_confirmed_gestures_and_motion(self):
        """Verify gesture debouncing, subject locking, and velocity mapping."""
        # 1. Detect person
        self._send_detection(center_x=0.5, width=0.25)

        # 2. Send GO gesture (ID: 2)
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_GO)
        self.assertTrue(self.node.locked_on)

        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.25)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)

        # 3. Send STOP gesture (ID: 5)
        self._send_gesture(GESTURE_STOP, "STOP", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_STOP)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)

        # 4. Send BACK gesture (ID: 0)
        self._send_gesture(GESTURE_BACK, "BACK", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_BACK)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, -0.25 * 0.6)

        # 5. Send LEFT gesture (ID: 3)
        self._send_gesture(GESTURE_LEFT, "LEFT", count=3)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.40)

        # 6. Send RIGHT gesture (ID: 4)
        self._send_gesture(GESTURE_RIGHT, "RIGHT", count=3)
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].angular.z, -0.40)

        print("✓ Test 03: Confirmed gestures (GO, STOP, BACK, LEFT, RIGHT) verified")

    def test_04_follow_mode_centering_and_distance(self):
        """Verify follow steering calculation and social distance holding."""
        self._send_detection(center_x=0.7, width=0.20)
        self._send_gesture(GESTURE_FOLLOW, "FOLLOW", count=3)

        # Person off-center to right (0.7 - 0.5 = 0.2)
        # Expected angular z = -0.2 * 1.5 = -0.30 rad/s
        self.published_twists.clear()
        self.node.control_loop()
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.20)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, -0.30)

        # Person gets close (width > 0.45)
        self._send_detection(center_x=0.5, width=0.55)
        self.published_twists.clear()
        self.node.control_loop()
        # Linear velocity halted for safety margin, angular centered
        self.assertAlmostEqual(self.published_twists[-1].linear.x, 0.0)
        self.assertAlmostEqual(self.published_twists[-1].angular.z, 0.0)

        print("✓ Test 04: Follow mode lateral centering & social distance verified")

    def test_05_biometric_face_id_gate(self):
        """Verify require_face_auth blocks unauthorized gestures and passes authorized ones."""
        self.node.require_face_auth = True
        self._send_detection(center_x=0.5, width=0.25)

        # 1. Attempt gesture with no face ID published yet -> should be ignored
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_NONE)

        # 2. Publish unauthorized face (bystander)
        self._send_face_id(name="Stranger", authorized=False)
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_NONE)

        # 3. Publish authorized face (AJ)
        self._send_face_id(name="AJ", authorized=True)
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertEqual(self.node.current_gesture, GESTURE_GO)

        # 4. Simulate stale face (> 5.0 seconds old)
        self.node.last_face_time = time.monotonic() - 6.0
        self._send_gesture(GESTURE_STOP, "STOP", count=3)
        # STOP ignored because face is stale; current_gesture remains GO
        self.assertEqual(self.node.current_gesture, GESTURE_GO)

        print("✓ Test 05: Biometric Face ID gating (unauthorized, authorized, stale) verified")

    def test_06_subject_lock_timeout_and_reset(self):
        """Verify subject lock expiration and manual service reset."""
        self._send_detection(center_x=0.5, width=0.25)
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertTrue(self.node.locked_on)

        # 1. Reset lock via SetBool service
        req = SetBool.Request()
        req.data = True
        res = SetBool.Response()
        res = self.node.reset_lock_callback(req, res)
        self.assertTrue(res.success)
        self.assertFalse(self.node.locked_on)
        self.assertEqual(self.node.current_gesture, GESTURE_NONE)

        # 2. Re-acquire lock, then simulate timeout
        self._send_gesture(GESTURE_GO, "GO", count=3)
        self.assertTrue(self.node.locked_on)
        self.node.lock_time = time.monotonic() - (self.node.lock_timeout + 1.0)
        self.node.control_loop()
        self.assertFalse(self.node.locked_on)
        self.assertEqual(self.node.current_gesture, GESTURE_NONE)

        print("✓ Test 06: Subject lock reset service & timeout expiration verified")


if __name__ == '__main__':
    unittest.main()
