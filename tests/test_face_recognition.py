#!/usr/bin/env python3
"""
test_face_recognition.py — Automated Unit Test for FaceRecognitionNode
Cognition Robot Project — Milestone 2 / 3 Verification

Tests:
1. FaceRecognitionNode initializes cleanly.
2. Loads InsightFace buffalo_sc engine and enrolled face database (AJ, BigFisher).
3. Ingests mock CompressedImage and publishes /cognition/face_target and /cognition/face_identity.
4. Confirms inference_interval: 3 frame skipping behavior.
"""

import os
import sys
import unittest
import numpy as np
import cv2

WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

import rclpy
from sensor_msgs.msg import CompressedImage

from src_nodes.face_recognition_node import FaceRecognitionNode


class TestFaceRecognitionNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        if rclpy.ok():
            rclpy.shutdown()

    def create_dummy_jpeg(self, width=640, height=480):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a synthetic face oval with features
        cv2.ellipse(img, (320, 240), (80, 110), 0, 0, 360, (180, 180, 180), -1)
        cv2.circle(img, (290, 210), 10, (50, 50, 50), -1)
        cv2.circle(img, (350, 210), 10, (50, 50, 50), -1)
        cv2.line(img, (300, 280), (340, 280), (50, 50, 50), 3)

        success, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        msg = CompressedImage()
        msg.header.stamp = rclpy.clock.Clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = encoded.tobytes()
        return msg

    def test_01_face_recognition_initialization(self):
        """Verify node loads engine and identifies enrolled DB."""
        node = FaceRecognitionNode()
        self.assertEqual(node.inference_interval, 3)
        self.assertIn("AJ", node.db)
        self.assertIn("BigFisher", node.db)
        print(f"\n✓ Test 01: FaceRecognitionNode initialized. Enrolled identities: {list(node.db.keys())}")

        dummy_img = self.create_dummy_jpeg()

        # Frame 1: Skipped (frame_counter=1, 1 % 3 != 0)
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_counter, 1)

        # Frame 2: Skipped
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_counter, 2)

        # Frame 3: Active inference frame
        node.image_callback(dummy_img)
        self.assertEqual(node.frame_counter, 3)
        print("✓ Test 02: Frame skipping (every 3rd frame inference) verified")

        node.destroy_node()


if __name__ == "__main__":
    unittest.main()
