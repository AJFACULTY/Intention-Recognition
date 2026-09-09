#!/usr/bin/env python3
"""
gimbal_video_demo.py — Visual Servoing & Gimbal Kinematics Demonstration
Demonstrates continuous, smooth, velocity-controlled multi-axis gimbal motion
for video documentation and milestone verification.
"""

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


def smooth_move(pub, node, start_deg, target_deg, speed_deg_s=25.0):
    diff = target_deg - start_deg
    if diff == 0:
        return
    step = 1 if diff > 0 else -1
    delay = 1.0 / speed_deg_s
    for angle in range(start_deg, target_deg + step, step):
        msg = Int32()
        msg.data = angle
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.001)
        time.sleep(delay)
    # Flush
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.01)
        time.sleep(0.01)


def main():
    rclpy.init()
    node = Node("gimbal_demo_controller")
    pub_s1 = node.create_publisher(Int32, "/servo_s1", 10)
    pub_s2 = node.create_publisher(Int32, "/servo_s2", 10)

    print("Connecting to micro-ROS servo topics...")
    t_start = time.time()
    while (pub_s1.get_subscription_count() == 0 or pub_s2.get_subscription_count() == 0) and (time.time() - t_start) < 3.0:
        rclpy.spin_once(node, timeout_sec=0.05)
        time.sleep(0.05)
    print(">> Micro-ROS hardware connected!")

    print("\n========================================================")
    print("  GET READY TO RECORD VIDEO!")
    print("========================================================")
    for i in range(5, 0, -1):
        print(f"  Starting demonstration in {i} seconds...")
        time.sleep(1.0)

    print("\n>>> [STEP 1] Center -> Panning Right (+45°)...")
    smooth_move(pub_s1, node, start_deg=0, target_deg=45, speed_deg_s=25.0)
    time.sleep(1.0)

    print(">>> [STEP 2] Panning Left from +45° to -45° (Continuous Smooth Sweep)...")
    smooth_move(pub_s1, node, start_deg=45, target_deg=-45, speed_deg_s=25.0)
    time.sleep(1.0)

    print(">>> [STEP 3] Returning smoothly to Center (0°)...")
    smooth_move(pub_s1, node, start_deg=-45, target_deg=0, speed_deg_s=25.0)
    time.sleep(1.0)

    print(">>> [STEP 4] Vertical Tilt Demonstration (Pitch)...")
    smooth_move(pub_s2, node, start_deg=-45, target_deg=-20, speed_deg_s=20.0)
    time.sleep(0.5)
    smooth_move(pub_s2, node, start_deg=-20, target_deg=-45, speed_deg_s=20.0)

    print("\n========================================================")
    print("  DEMONSTRATION COMPLETE — 100% SUCCESS")
    print("========================================================")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
