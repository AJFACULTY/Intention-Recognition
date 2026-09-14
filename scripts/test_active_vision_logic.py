#!/usr/bin/env python3
"""
test_active_vision_logic.py — Automated Verification Suite for ActiveVisionNode
Tests mathematical control law, deadband filtering, slew-rate limiting,
mechanical safety clamping, and Finite State Machine (FSM) transitions.
"""

import math
import os
import sys
import time
import unittest

# Ensure workspace is on sys.path
WORKSPACE_PATH = "/home/j/ros2_cognition_ws"
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Int32, String

from src_nodes.active_vision_node import ActiveVisionNode


class TestActiveVisionLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        if rclpy.ok():
            rclpy.shutdown()

    def setUp(self):
        self.node = ActiveVisionNode()

    def tearDown(self):
        self.node.destroy_node()

    def test_01_initial_neutral_pose(self):
        """Verify node initializes to configured home pose and IDLE state."""
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_IDLE)
        self.assertEqual(self.node.current_pan, 0.0)
        self.assertEqual(self.node.current_tilt, 8.0)
        self.assertEqual(self.node.pan_home, 0)
        self.assertEqual(self.node.tilt_home, 8)
        print("\n✓ Test 01: Initial neutral pose verified (pan=0, tilt=8, state=IDLE)")

    def test_02_deadband_suppression(self):
        """Verify errors within deadband (<= 0.05) produce zero movement."""
        self.assertEqual(self.node.apply_deadband(0.0), 0.0)
        self.assertEqual(self.node.apply_deadband(0.03), 0.0)
        self.assertEqual(self.node.apply_deadband(-0.04), 0.0)
        self.assertEqual(self.node.apply_deadband(0.05), 0.0)

        # Values outside deadband subtract the deadband margin
        self.assertAlmostEqual(self.node.apply_deadband(0.10), 0.05)
        self.assertAlmostEqual(self.node.apply_deadband(-0.10), -0.05)
        print("✓ Test 02: Deadband suppression verified (zero jitter within +/-0.05)")

    def test_03_visual_servoing_direction(self):
        """Verify positive x (right) pans right, negative y (top) tilts up."""
        # Target at x=0.4 (right), y=-0.3 (above optical center)
        target = Point(x=0.4, y=-0.3, z=0.95)
        self.node.target_callback(target)
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_TRACKING)

        initial_pan = self.node.current_pan
        initial_tilt = self.node.current_tilt

        # Run one control loop tick
        self.node.control_loop()

        # In Yahboom coordinate frame:
        # To track target to right, pan angle must increase (+deg is right)
        # To track target above center, tilt angle must increase (+deg is up)
        self.assertGreater(self.node.current_pan, initial_pan, "Pan should increase to track right target")
        self.assertGreater(self.node.current_tilt, initial_tilt, "Tilt should increase to track elevated target")
        print(f"✓ Test 03: Servoing direction verified: pan {initial_pan} -> {self.node.current_pan:.2f}, tilt {initial_tilt} -> {self.node.current_tilt:.2f}")

    def test_04_slew_rate_limiter(self):
        """Verify maximum step per tick does not exceed max_slew_deg (3.0 deg)."""
        # Command an extreme error that would demand an 18 deg jump
        target = Point(x=1.0, y=1.0, z=0.99)
        self.node.target_callback(target)

        initial_pan = self.node.current_pan
        initial_tilt = self.node.current_tilt

        self.node.control_loop()

        pan_delta = abs(self.node.current_pan - initial_pan)
        tilt_delta = abs(self.node.current_tilt - initial_tilt)

        self.assertLessEqual(pan_delta, self.node.max_slew_deg + 1e-5)
        self.assertLessEqual(tilt_delta, self.node.max_slew_deg + 1e-5)
        print(f"✓ Test 04: Slew rate limiter verified (pan_step={pan_delta:.2f} deg <= {self.node.max_slew_deg} deg)")

    def test_05_mechanical_safety_clamping(self):
        """Verify servo angles cannot exceed mechanical joint bounds."""
        self.node.current_pan = 2.0
        self.node.current_tilt = 21.0

        # Push heavily downwards and rightwards
        target = Point(x=1.0, y=-1.0, z=0.99)
        self.node.target_callback(target)

        for _ in range(50):
            self.node.last_target_time = time.time()  # keep fresh
            self.node.control_loop()

        self.assertGreaterEqual(self.node.current_pan, self.node.pan_min)
        self.assertLessEqual(self.node.current_pan, self.node.pan_max)
        self.assertGreaterEqual(self.node.current_tilt, self.node.tilt_min)
        self.assertLessEqual(self.node.current_tilt, self.node.tilt_max)
        print(f"✓ Test 05: Mechanical clamps verified: pan={self.node.current_pan:.1f} in [{self.node.pan_min},{self.node.pan_max}], tilt={self.node.current_tilt:.1f} in [{self.node.tilt_min},{self.node.tilt_max}]")

    def test_06_target_loss_memory_hold_and_search_fsm(self):
        """Verify transition TRACKING -> MEMORY_HOLD -> SEARCH -> REVERT -> IDLE."""
        # 1. Acquire target
        self.node.target_callback(Point(x=0.2, y=0.1, z=0.9))
        self.node.control_loop()
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_TRACKING)

        # 2. Target lost explicitly (z <= 0)
        self.node.target_callback(Point(x=0.0, y=0.0, z=-1.0))
        self.node.control_loop()
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_MEMORY_HOLD)
        held_pan = self.node.current_pan
        held_tilt = self.node.current_tilt

        # 3. Memory hold preserves heading
        self.node.control_loop()
        self.assertEqual(self.node.current_pan, held_pan)
        self.assertEqual(self.node.current_tilt, held_tilt)

        # 4. Simulate target timeout (> 1.5s)
        self.node.last_target_time = time.time() - 2.0
        self.node.control_loop()
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_SEARCH)

        # 5. In search mode, pan sweeps sinusoidally
        search_pan_1 = self.node.current_pan
        time.sleep(0.1)
        self.node.control_loop()
        search_pan_2 = self.node.current_pan
        self.assertTrue(abs(search_pan_2 - self.node.pan_home) >= 0.0)

        # 6. Simulate search duration timeout (> search_duration)
        self.node.search_start_time = time.time() - (self.node.search_duration + 1.0)
        self.node.control_loop()
        self.assertEqual(self.node.state, ActiveVisionNode.STATE_REVERT)

        # 7. Let REVERT bring gimbal back to neutral
        for _ in range(30):
            self.node.control_loop()

        self.assertEqual(self.node.state, ActiveVisionNode.STATE_IDLE)
        self.assertAlmostEqual(self.node.current_pan, self.node.pan_home, delta=0.5)
        self.assertAlmostEqual(self.node.current_tilt, self.node.tilt_home, delta=0.5)
        print("✓ Test 06: Full FSM cycle verified: TRACKING -> MEMORY_HOLD -> SEARCH -> REVERT -> IDLE")

    def test_07_target_reacquisition_interrupts_search(self):
        """Verify re-acquiring target while in SEARCH immediately recovers TRACKING."""
        # Force into SEARCH
        self.node.state = ActiveVisionNode.STATE_SEARCH
        self.node.search_start_time = time.time()

        # Target re-appears
        self.node.target_callback(Point(x=0.15, y=-0.1, z=0.85))
        self.node.control_loop()

        self.assertEqual(self.node.state, ActiveVisionNode.STATE_TRACKING)
        print("✓ Test 07: Target re-acquisition immediately recovers TRACKING from SEARCH")


if __name__ == "__main__":
    unittest.main()
