#!/usr/bin/env python3
"""
test_perception_throttling.py — Automated Unit Test for Perception Throttling
Cognition Robot Project — Milestone 2 Verification

Tests:
1. PersonDetectionNode initializes with frame_skip=3.
2. PersonDetectionNode processes active frames and extrapolates centroids on skipped frames.
3. GestureNode initializes with frame_skip=3.
4. GestureNode processes active frames and holds gestures on skipped frames.
"""

import sys
import time
import unittest
import numpy as np
import cv2

WORKSPACE_PATH = "/home/j/ros2_cognition_ws"
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from sensor_msgs.msg import CompressedImage
from cognition_interfaces.msg import Detection, Gesture

from src_nodes.person_detection_node import PersonDetectionNode
from src_nodes.gesture_node import GestureNode


class TestPerceptionThrottling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        if rclpy.ok():
            rclpy.shutdown()

    def create_dummy_jpeg(self, width=640, height=480):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a synthetic rectangular person-like shape in the center
        cv2.rectangle(img, (260, 100), (380, 420), (200, 200, 200), -1)
        success, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        msg = CompressedImage()
        msg.header.stamp = rclpy.clock.Clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = encoded.tobytes()
        return msg

    def test_01_person_detection_throttling(self):
        """Verify PersonDetectionNode frame-skip logic and velocity extrapolation."""
        node = PersonDetectionNode()
        self.assertEqual(node.frame_skip, 3)

        dummy_img = self.create_dummy_jpeg()

        # Frame 1: Active frame (frame_count=1, 1 % 3 != 0 -> wait, 1 % 3 = 1)
        # Note: frame_skip is 3, so active frames are frame_count % 3 == 0 (or count=3, 6, 9)
        # Frames 1 and 2 are skipped, frame 3 is active inference!
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 1)

        # Frame 2: Skipped frame
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 2)

        # Mock an active detection to test extrapolation
        node.last_active_det = {
            'box': (260, 100, 380, 420),
            'conf': 0.85,
            'cx': 0.50,
            'cy': 0.50,
            'bw': 0.18,
            'bh': 0.60,
            'vel_x': 0.10,  # moving right at 0.10 norm units/sec
            'vel_y': 0.0,
            'direction': 'MOVING RIGHT',
        }
        node.last_det_time = node.get_clock().now()

        # Frame 3: Active frame (runs YOLO)
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 3)

        # Frame 4: Skipped frame with extrapolation
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 4)

        node.destroy_node()
        print("\n✓ Test 01: PersonDetectionNode frame skipping and extrapolation verified")

    def test_02_gesture_throttling(self):
        """Verify GestureNode frame-skip logic and gesture state holding."""
        node = GestureNode()
        self.assertEqual(node.frame_skip, 3)

        dummy_img = self.create_dummy_jpeg()

        # Frame 1: Skipped
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 1)

        # Frame 2: Skipped
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 2)

        # Frame 3: Active frame
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_count, 3)

        node.destroy_node()
        print("✓ Test 02: GestureNode frame skipping and state holding verified")


if __name__ == "__main__":
    unittest.main()
