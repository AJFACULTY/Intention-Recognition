#!/usr/bin/env python3
"""
smooth_servo_move.py — Smooth Gimbal Trajectory Controller
Interpolates servo angle gradually to prevent violent motor snaps and mechanical wear.

Usage:
  python3 smooth_servo_move.py --servo s1 --target 10 --start 90 --speed 30
"""

import argparse
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


def main():
    parser = argparse.ArgumentParser(description="Smooth servo motion utility")
    parser.add_argument("--servo", choices=["s1", "s2"], default="s1", help="Servo channel: s1 (pan) or s2 (tilt)")
    parser.add_argument("--target", type=int, required=True, help="Target angle (-90 to 90)")
    parser.add_argument("--start", type=int, default=None, help="Assumed starting angle (if unknown, uses 0)")
    parser.add_argument("--speed", type=float, default=30.0, help="Rotation speed in degrees per second (default: 30 deg/s)")
    args = parser.parse_args()

    rclpy.init()
    node = Node("smooth_servo_mover")
    topic = f"/servo_{args.servo}"
    pub = node.create_publisher(Int32, topic, 10)

    # If start angle not provided, default to 0 for true center
    start = args.start
    if start is None:
        start = 0

    target = max(-90, min(90, args.target))
    diff = target - start

    if diff == 0:
        print(f"/servo_{args.servo} is already at {target}°")
        node.destroy_node()
        rclpy.shutdown()
        return

    step = 1 if diff > 0 else -1
    delay = 1.0 / args.speed if args.speed > 0 else 0.03

    # Wait for micro-ROS DDS subscriber matching
    print(f"Connecting to /servo_{args.servo}...")
    t_wait = time.time()
    while pub.get_subscription_count() == 0 and (time.time() - t_wait) < 3.0:
        rclpy.spin_once(node, timeout_sec=0.05)
        time.sleep(0.05)

    print(f"Matched {pub.get_subscription_count()} subscriber(s). Moving from {start}° to {target}° at {args.speed}°/s...")

    for angle in range(start, target + step, step):
        msg = Int32()
        msg.data = angle
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.001)
        time.sleep(delay)

    # Flush final packet
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.02)
        time.sleep(0.02)

    print(f"✓ /servo_{args.servo} reached target: {target}°")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
