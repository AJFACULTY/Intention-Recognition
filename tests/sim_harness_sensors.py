#!/usr/bin/env python3
"""
sim_harness_sensors.py — High-Fidelity Realistic Sensor Replay Node
===================================================================
Replays authentic robot sensor data for realistic headless testing:
1. Real camera video from `test_vids/bot_camera_session.mp4` as CompressedImage (JPEG)
2. Authentic MS200 LiDAR LaserScan stream from `bags/nav_run_20260910_192920`
3. Authentic Odometry stream (/odom_raw)
4. Dynamic obstacle injection for ISO 15066 safety preemption verification
"""

import os
import sys
import time
import sqlite3
import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import CompressedImage, LaserScan
from nav_msgs.msg import Odometry

WS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_VIDEO = os.path.join(WS_DIR, "test_vids", "bot_camera_session.mp4")
DEFAULT_BAG_DB = os.path.join(WS_DIR, "bags", "nav_run_20260910_192920", "nav_run_20260910_192920_0.db3")


class SensorReplayHarness(Node):
    def __init__(self, video_path=DEFAULT_VIDEO, bag_path=DEFAULT_BAG_DB, enable_obstacle_injection=False):
        super().__init__('sim_harness_sensors')

        self.video_path = video_path
        self.bag_path = bag_path
        self.enable_obstacle_injection = enable_obstacle_injection
        self.obstacle_active = False
        self.obstacle_distance = 0.28

        # Publishers
        self.image_pub = self.create_publisher(CompressedImage, '/camera/image_raw/compressed', 10)
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom_raw', 10)

        # 1. Load Video
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.get_logger().error(f"Failed to open video: {self.video_path}")
            self.fps = 20.0
            self.total_frames = 0
        else:
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 20.0
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.get_logger().info(f"Loaded video: {self.video_path} ({self.total_frames} frames @ {self.fps:.1f} FPS)")

        # 2. Load Rosbag Telemetry
        self.scans = []
        self.odoms = []
        self._load_bag_messages()

        self.scan_idx = 0
        self.odom_idx = 0
        self.frame_idx = 0

        # Timers: Camera at ~20 Hz (0.05s), LiDAR at ~12 Hz (0.083s), Odom at ~10 Hz (0.10s)
        self.cam_timer = self.create_timer(1.0 / self.fps, self._cam_callback)
        self.scan_timer = self.create_timer(0.083, self._scan_callback)
        self.odom_timer = self.create_timer(0.100, self._odom_callback)

        self.get_logger().info("SensorReplayHarness initialized and streaming authentic telemetry.")

    def _load_bag_messages(self):
        if not os.path.exists(self.bag_path):
            self.get_logger().warn(f"Bag file not found at {self.bag_path}. Synthesizing planar scans.")
            return

        try:
            conn = sqlite3.connect(self.bag_path)
            c = conn.cursor()

            # Topic 6 = /scan
            c.execute("SELECT data FROM messages WHERE topic_id=6 ORDER BY timestamp")
            for row in c.fetchall():
                scan_msg = deserialize_message(row[0], LaserScan)
                self.scans.append(scan_msg)

            # Topic 5 = /odom_raw
            c.execute("SELECT data FROM messages WHERE topic_id=5 ORDER BY timestamp")
            for row in c.fetchall():
                odom_msg = deserialize_message(row[0], Odometry)
                self.odoms.append(odom_msg)

            conn.close()
            self.get_logger().info(f"Loaded {len(self.scans)} LaserScans and {len(self.odoms)} Odometry messages from bag.")
        except Exception as e:
            self.get_logger().error(f"Error loading bag: {e}")

    def trigger_obstacle_breach(self, distance_m=0.28):
        """Injects a frontal obstacle breach inside the critical <0.36m ISO 15066 safety zone."""
        self.obstacle_active = True
        self.obstacle_distance = distance_m
        self.get_logger().warn(f"[INJECTION] Frontal obstacle breach injected: {distance_m:.2f}m")

    def clear_obstacle_breach(self):
        """Clears injected frontal obstacle."""
        self.obstacle_active = False
        self.get_logger().info("[INJECTION] Frontal obstacle breach cleared.")

    def _cam_callback(self):
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            # Loop video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return

        self.frame_idx += 1
        success, enc = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera_optical_frame"
        msg.format = "jpeg"
        msg.data = enc.tobytes()
        self.image_pub.publish(msg)

    def _scan_callback(self):
        now = self.get_clock().now().to_msg()

        if self.scans:
            msg = self.scans[self.scan_idx]
            self.scan_idx = (self.scan_idx + 1) % len(self.scans)
            # Make a copy to avoid mutating cache
            scan_out = LaserScan()
            scan_out.header.stamp = now
            scan_out.header.frame_id = "laser_frame"
            scan_out.angle_min = msg.angle_min
            scan_out.angle_max = msg.angle_max
            scan_out.angle_increment = msg.angle_increment
            scan_out.time_increment = msg.time_increment
            scan_out.scan_time = msg.scan_time
            scan_out.range_min = msg.range_min
            scan_out.range_max = msg.range_max

            ranges = list(msg.ranges)

            # Apply dynamic obstacle injection if active
            if self.obstacle_active:
                n = len(ranges)
                mid = n // 2
                cone_width = int(n * (45.0 / 360.0))  # +/- 45 deg cone
                for i in range(max(0, mid - cone_width), min(n, mid + cone_width)):
                    ranges[i] = self.obstacle_distance

            scan_out.ranges = ranges
            self.scan_pub.publish(scan_out)
        else:
            # Synthetic backup planar scan
            scan_out = LaserScan()
            scan_out.header.stamp = now
            scan_out.header.frame_id = "laser_frame"
            scan_out.angle_min = -3.14159
            scan_out.angle_max = 3.14159
            scan_out.angle_increment = 6.28318 / 360.0
            scan_out.range_min = 0.12
            scan_out.range_max = 8.0
            d = self.obstacle_distance if self.obstacle_active else 1.50
            scan_out.ranges = [d if 135 <= i <= 225 else 2.5 for i in range(360)]
            self.scan_pub.publish(scan_out)

    def _odom_callback(self):
        if not self.odoms:
            return
        msg = self.odoms[self.odom_idx]
        self.odom_idx = (self.odom_idx + 1) % len(self.odoms)
        msg.header.stamp = self.get_clock().now().to_msg()
        self.odom_pub.publish(msg)

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SensorReplayHarness()
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
