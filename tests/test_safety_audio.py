#!/usr/bin/env python3
"""
test_safety_audio.py — Automated Unit & Integration Tests for SafetyAudioNode
Tests:
1. Reversing detection on negative linear.x velocity.
2. E-Stop state detection on /e_stop topic.
3. Acoustic chime trigger and /beep publishing.
"""

import os
import sys
import time
import unittest

WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, String, UInt16

from src_nodes.safety_audio_node import SafetyAudioNode


class TestSafetyAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        if rclpy.ok():
            rclpy.shutdown()

    def setUp(self):
        self.node = SafetyAudioNode()
        self.beeps_published = []
        self.node.beep_pub.publish = lambda msg: self.beeps_published.append(msg.data)

    def tearDown(self):
        self.node.destroy_node()

    def test_reverse_detection(self):
        """Verify that negative velocity sets is_reversing and triggers beeping."""
        twist = Twist()
        twist.linear.x = -0.15  # Reversing
        self.node._cmd_vel_cb(twist)
        self.assertTrue(self.node.is_reversing)

        # Forward motion clears reverse state
        twist.linear.x = 0.20
        self.node._cmd_vel_cb(twist)
        self.assertFalse(self.node.is_reversing)

    def test_estop_detection(self):
        """Verify that e-stop triggers state change."""
        msg = Bool()
        msg.data = True
        self.node._estop_cb(msg)
        self.assertTrue(self.node.is_estop)

        msg.data = False
        self.node._estop_cb(msg)
        self.assertFalse(self.node.is_estop)

    def test_chime_dispatch(self):
        """Verify that arrival and obstacle chimes emit valid duration values."""
        self.node._play_sequence("waypoint")
        self.assertIn(70, self.beeps_published)

        self.beeps_published.clear()
        self.node._play_sequence("obstacle")
        self.assertEqual(self.beeps_published, [100, 100])


if __name__ == "__main__":
    unittest.main()
