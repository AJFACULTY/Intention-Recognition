#!/usr/bin/env python3
import rclpy
from sensor_msgs.msg import LaserScan
import math

rclpy.init()
node = rclpy.create_node("scan_live_check")

def cb(msg):
    angle = msg.angle_min
    inc = msg.angle_increment
    corridor_half = 0.18
    front_all = []
    front_filtered = []
    rear_all = []
    rear_filtered = []
    for r in msg.ranges:
        if msg.range_min <= r <= msg.range_max and not math.isnan(r) and not math.isinf(r):
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            if abs(y) <= corridor_half:
                if x > 0:
                    front_all.append(x)
                    if 0.14 <= x <= 0.65:
                        front_filtered.append(x)
                elif x < 0:
                    rear_all.append(abs(x))
                    if -0.65 <= x <= -0.15:
                        rear_filtered.append(abs(x))
        angle += inc

    f_all_min = f"{min(front_all):.2f}m" if front_all else "NONE"
    f_filt_min = f"{min(front_filtered):.2f}m" if front_filtered else "CLEAR (>0.65m)"
    r_all_min = f"{min(rear_all):.2f}m" if rear_all else "NONE"
    r_filt_min = f"{min(rear_filtered):.2f}m" if rear_filtered else "CLEAR (>0.65m)"

    print(f"RAW FRONT (including chassis): {f_all_min} | FILTERED (External): {f_filt_min}")
    print(f"RAW REAR  (including chassis): {r_all_min} | FILTERED (External): {r_filt_min}")
    rclpy.shutdown()

sub = node.create_subscription(LaserScan, "/scan", cb, 10)
rclpy.spin(node)
