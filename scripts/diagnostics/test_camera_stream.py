#!/usr/bin/env python3
"""
test_camera_stream.py — Diagnostic Tool for Camera Devices and ROS 2 Image Feed
=============================================================================
Probes V4L2 video devices, tests frame capture rates, saves a test snapshot,
and optionally checks the ROS 2 /camera/image_raw/compressed topic.
"""

import os
import sys
import time
import glob
import cv2
import numpy as np

# ANSI styling
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_CYAN = "\033[36m"


def probe_v4l2_devices():
    print(f"\n{C_BOLD}{C_CYAN}── 1. Probing V4L2 Video Devices ─────────────────────────────{C_RESET}")
    devices = sorted(glob.glob('/dev/video*'))
    if not devices:
        print(f"  {C_RED}✗ No /dev/video* devices found! Check USB camera cable.{C_RESET}")
        return []
    
    print(f"  Found {len(devices)} device entries: {', '.join(devices)}")
    working = []
    
    for dev in devices:
        try:
            idx = int(dev.replace('/dev/video', ''))
        except ValueError:
            continue
        
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                h, w = frame.shape[:2]
                print(f"  {C_GREEN}✓ {dev} is ACTIVE! Capture resolution: {w}x{h}{C_RESET}")
                working.append((idx, dev, w, h))
            else:
                print(f"  {C_YELLOW}○ {dev} opened but returned empty frame (metadata/buffer node){C_RESET}")
            cap.release()
        else:
            print(f"  {C_YELLOW}○ {dev} cannot be opened by OpenCV{C_RESET}")
            
    return working


def benchmark_capture(device_idx: int, num_frames: int = 15, save_snapshot: str = "camera_test.jpg"):
    print(f"\n{C_BOLD}{C_CYAN}── 2. Benchmarking Frame Capture on /dev/video{device_idx} ──────────────{C_RESET}")
    cap = cv2.VideoCapture(device_idx)
    if not cap.isOpened():
        cap = cv2.VideoCapture(device_idx, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"  {C_RED}✗ Failed to open /dev/video{device_idx} for benchmark!{C_RESET}")
        return False
    
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frames_read = 0
    t0 = time.time()
    last_frame = None
    
    for i in range(num_frames):
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            frames_read += 1
            last_frame = frame
        time.sleep(0.01)
    
    elapsed = time.time() - t0
    cap.release()
    
    fps = frames_read / elapsed if elapsed > 0 else 0
    print(f"  Captured {frames_read}/{num_frames} frames in {elapsed:.2f}s ({fps:.1f} FPS)")
    
    if last_frame is not None:
        cv2.imwrite(save_snapshot, last_frame)
        print(f"  {C_GREEN}✓ Snapshot saved to: {os.path.abspath(save_snapshot)}{C_RESET}")
        return True
    return False


def test_ros2_topic(topic: str = "/camera/image_raw/compressed", timeout_sec: float = 3.0):
    print(f"\n{C_BOLD}{C_CYAN}── 3. Checking ROS 2 Topic {topic} ──────────────{C_RESET}")
    try:
        import rclpy
        from sensor_msgs.msg import CompressedImage
    except ImportError:
        print(f"  {C_YELLOW}○ ROS 2 Python libraries not available in current shell — skipping topic check.{C_RESET}")
        return

    try:
        rclpy.init()
    except Exception:
        pass

    node = rclpy.create_node('camera_diagnostic_listener')
    received = []

    def cb(msg):
        received.append(len(msg.data))

    sub = node.create_subscription(CompressedImage, topic, cb, 10)
    t_end = time.time() + timeout_sec
    while time.time() < t_end and len(received) < 5:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()

    if received:
        print(f"  {C_GREEN}✓ Successfully received {len(received)} compressed frames from {topic}! (Avg size: {sum(received)//len(received)} bytes){C_RESET}")
    else:
        print(f"  {C_YELLOW}○ No frames received on {topic} within {timeout_sec}s (camera publisher node may be stopped).{C_RESET}")


def main():
    print(f"{C_BOLD}{C_GREEN}══════════════════════════════════════════════════════════════════════════{C_RESET}")
    print(f"{C_BOLD}{C_GREEN}       EMBEDDED CAMERA & VISION FEED DIAGNOSTIC UTILITY                   {C_RESET}")
    print(f"{C_BOLD}{C_GREEN}══════════════════════════════════════════════════════════════════════════{C_RESET}")
    
    devices = probe_v4l2_devices()
    if devices:
        primary_idx = devices[0][0]
        benchmark_capture(primary_idx)
    
    test_ros2_topic()
    print(f"\n{C_BOLD}Diagnostic complete.{C_RESET}\n")


if __name__ == '__main__':
    main()
