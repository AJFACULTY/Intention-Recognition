#!/usr/bin/env python3
"""
camera_pub.py — Robust Auto-Probing Camera Publisher Node
Cognition Robot Project — Embedded Vision Stack

Features:
- Dynamically probes and auto-detects active USB camera (/dev/video0, /dev/video1, etc.)
- Configures V4L2 MJPG capture format to prevent USB 3.0 XHCI buffer timeouts
- Automatically resizes frames to 320x240 for low CPU consumption
- Reconnection resilience if camera USB cable is momentarily glitched or re-enumerated
- Publishes standard sensor_msgs/CompressedImage to /camera/image_raw/compressed
"""

import os
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.declare_parameter('device_index', -1)  # -1 for auto-probe
        self.declare_parameter('publish_fps', 20.0)
        self.declare_parameter('capture_width', 640)
        self.declare_parameter('capture_height', 480)
        self.declare_parameter('output_width', 320)
        self.declare_parameter('output_height', 240)
        self.declare_parameter('jpeg_quality', 80)

        self.target_idx = int(self.get_parameter('device_index').value)
        self.fps = float(self.get_parameter('publish_fps').value)
        self.cap_w = int(self.get_parameter('capture_width').value)
        self.cap_h = int(self.get_parameter('capture_height').value)
        self.out_w = int(self.get_parameter('output_width').value)
        self.out_h = int(self.get_parameter('output_height').value)
        self.jpeg_quality = int(self.get_parameter('jpeg_quality').value)

        self.pub = self.create_publisher(CompressedImage, '/camera/image_raw/compressed', 10)

        self.cap = None
        self.active_idx = -1
        self.consecutive_failures = 0

        self._init_camera()

        timer_period = 1.0 / max(1.0, self.fps)
        self.timer = self.create_timer(timer_period, self.publish_frame)
        self.get_logger().info(f"Camera Publisher initialized @ {self.fps:.1f} Hz ({self.out_w}x{self.out_h})")

    def _open_device(self, idx):
        """Attempts to open a camera device index with V4L2 and MJPG codec."""
        dev_path = f"/dev/video{idx}"
        if not os.path.exists(dev_path):
            return None
        # Open standard capture backend matching the verified 1-second test
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cap_w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cap_h)

            # Test read
            for _ in range(3):
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    return cap
            cap.release()
        return None

    def _init_camera(self):
        """Probes and initializes the camera."""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        if self.target_idx >= 0:
            self.get_logger().info(f"Attempting to open configured camera index {self.target_idx}...")
            cap = self._open_device(self.target_idx)
            if cap is not None:
                self.cap = cap
                self.active_idx = self.target_idx
                self.get_logger().info(f"Successfully opened configured camera at index {self.active_idx}")
                self.consecutive_failures = 0
                return
            else:
                self.get_logger().warn(f"Configured camera index {self.target_idx} failed, falling back to auto-probe.")

        # Auto-probe candidates: probe 0 first (standard primary UVC video capture stream), then 1, 2, 3
        candidates = [0, 1, 2, 3]
        for idx in candidates:
            dev_path = f"/dev/video{idx}"
            if not os.path.exists(dev_path):
                continue
            cap = self._open_device(idx)
            if cap is not None:
                self.cap = cap
                self.active_idx = idx
                self.get_logger().info(f"Auto-detected active camera at index {self.active_idx} ({dev_path})")
                self.consecutive_failures = 0
                return

        self.get_logger().error(f"No working camera device found on indices {candidates}!")

    def publish_frame(self):
        if self.cap is None or not self.cap.isOpened():
            self.consecutive_failures += 1
            if self.consecutive_failures % 20 == 0:
                self.get_logger().warn("Camera disconnected or unavailable. Attempting auto-reconnection...")
                self._init_camera()
            return

        ret, frame = self.cap.read()
        if not ret or frame is None or frame.size == 0:
            self.consecutive_failures += 1
            if self.consecutive_failures % 20 == 0:
                self.get_logger().warn(f"Failed to capture frame ({self.consecutive_failures} dropped). Reconnecting...")
                self._init_camera()
            return

        self.consecutive_failures = 0

        # Resize for lightweight transmission
        if frame.shape[1] != self.out_w or frame.shape[0] != self.out_h:
            frame = cv2.resize(frame, (self.out_w, self.out_h), interpolation=cv2.INTER_AREA)

        # Encode to JPEG
        ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if not ret:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_frame'
        msg.format = 'jpeg'
        msg.data = buf.tobytes()
        self.pub.publish(msg)

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
