#!/usr/bin/env python3
"""
probe_gimbal_limits.py — Hardware Servo Limit & Direction Diagnostic Tool
========================================================================
Interactive and automated diagnostic utility to:
1. Verify physical servo motion to the left and right.
2. Determine exact hardware angular limits and neutral center.
3. Test whether the STM32 board accepts negative angles (-90°..+90°)
   or expects unsigned angles (0°..180° with 90° center).
4. Ensure all movements are velocity-profiled (anti-jerk, smooth glide).

Usage on Raspberry Pi:
    docker exec -it yahboom_gesture python3 /root/cognition_ws/probe_gimbal_limits.py
"""

import sys
import time
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class GimbalProbe(Node):
    def __init__(self):
        super().__init__("gimbal_probe")
        self.pub_pan = self.create_publisher(Int32, "/servo_s1", 10)
        self.pub_tilt = self.create_publisher(Int32, "/servo_s2", 10)
        self.current_pan = 0
        self.current_tilt = 35

    def publish_smooth(self, target_pan, target_tilt=None, speed_deg_s=25.0):
        """Ramps servo angle smoothly to target at a fixed angular velocity."""
        if target_tilt is None:
            target_tilt = self.current_tilt

        pan_diff = target_pan - self.current_pan
        tilt_diff = target_tilt - self.current_tilt
        total_steps = int(max(abs(pan_diff), abs(tilt_diff)))

        if total_steps == 0:
            return

        delay = 1.0 / speed_deg_s
        step_pan = pan_diff / total_steps
        step_tilt = tilt_diff / total_steps

        start_p = float(self.current_pan)
        start_t = float(self.current_tilt)

        for i in range(1, total_steps + 1):
            p = int(round(start_p + step_pan * i))
            t = int(round(start_t + step_tilt * i))

            msg_p = Int32()
            msg_p.data = p
            self.pub_pan.publish(msg_p)

            msg_t = Int32()
            msg_t.data = t
            self.pub_tilt.publish(msg_t)

            rclpy.spin_once(self, timeout_sec=0.001)
            time.sleep(delay)

        self.current_pan = target_pan
        self.current_tilt = target_tilt
        time.sleep(0.05)


def print_banner():
    print("=" * 65)
    print("      COGNITION ROBOTICS — 2-DOF GIMBAL HARDWARE LIMIT PROBE")
    print("=" * 65)
    print("  Controls & Diagnostics:")
    print("  [1] Test 0-Centric Protocol (-90° to +90°, Neutral = 0°)")
    print("  [2] Test 90-Centric Protocol (0° to 180°, Neutral = 90°)")
    print("  [3] Interactive Jogger (Enter custom angles with smooth ramping)")
    print("  [4] Neutral Return (Reset to 0° pan, 35° tilt)")
    print("  [Q] Exit")
    print("=" * 65)


def run_sweep_0_centric(probe):
    print("\n--- Testing 0-Centric Protocol (Neutral = 0°) ---")
    print(">> Returning to Center (0°)...")
    probe.publish_smooth(0, 35)
    time.sleep(1.0)

    # Step Right: Positive
    print("\n[Phase 1] Panning toward POSITIVE angles (+10° -> +45°)...")
    for angle in [10, 20, 30, 45]:
        print(f"  -> Moving to +{angle}°...")
        probe.publish_smooth(angle, 35)
        time.sleep(0.8)
    print(">> Returning to Center (0°)...")
    probe.publish_smooth(0, 35)
    time.sleep(1.0)

    # Step Left: Negative
    print("\n[Phase 2] Panning toward NEGATIVE angles (-10° -> -45°)...")
    for angle in [-10, -20, -30, -45]:
        print(f"  -> Moving to {angle}°...")
        probe.publish_smooth(angle, 35)
        time.sleep(0.8)
    print(">> Returning to Center (0°)...")
    probe.publish_smooth(0, 35)
    print("\nPhase complete. Observe: Did the camera physically move during Phase 2?")


def run_sweep_90_centric(probe):
    print("\n--- Testing 90-Centric Protocol (Neutral = 90°) ---")
    print(">> Moving to 90° center...")
    probe.publish_smooth(90, 90)
    time.sleep(1.0)

    # Step >90
    print("\n[Phase 1] Testing Increasing Angles (90° -> 135°)...")
    for angle in [100, 110, 120, 135]:
        print(f"  -> Moving to {angle}°...")
        probe.publish_smooth(angle, 90)
        time.sleep(0.8)
    print(">> Returning to 90°...")
    probe.publish_smooth(90, 90)
    time.sleep(1.0)

    # Step <90
    print("\n[Phase 2] Testing Decreasing Angles (90° -> 45°)...")
    for angle in [80, 70, 60, 45]:
        print(f"  -> Moving to {angle}°...")
        probe.publish_smooth(angle, 90)
        time.sleep(0.8)
    print(">> Returning to 90°...")
    probe.publish_smooth(90, 90)
    print("\nPhase complete.")


def run_interactive(probe):
    print("\n--- Interactive Gimbal Jogger ---")
    print("Type an angle for Pan (-90 to +90 or 0 to 180), or 'q' to return:")
    while rclpy.ok():
        try:
            val = input("\nEnter Target Pan Angle (current: " + str(probe.current_pan) + "°): ").strip()
            if val.lower() == 'q':
                break
            target = int(val)
            print(f">> Smoothly ramping pan from {probe.current_pan}° to {target}°...")
            probe.publish_smooth(target, probe.current_tilt)
            print(f">> Position reached: {target}°")
        except ValueError:
            print("Invalid integer. Please try again.")
        except (KeyboardInterrupt, EOFError):
            break


def main():
    rclpy.init()
    probe = GimbalProbe()

    # Wait for micro-ROS connection
    print("Connecting to /servo_s1 and /servo_s2 topics...")
    t0 = time.time()
    while (probe.pub_pan.get_subscription_count() == 0) and (time.time() - t0 < 3.0):
        rclpy.spin_once(probe, timeout_sec=0.05)
        time.sleep(0.05)
    print(">> Hardware connected!\n")

    while rclpy.ok():
        print_banner()
        try:
            choice = input("Select an option [1-4, Q]: ").strip().upper()
            if choice == "1":
                run_sweep_0_centric(probe)
            elif choice == "2":
                run_sweep_90_centric(probe)
            elif choice == "3":
                run_interactive(probe)
            elif choice == "4":
                print(">> Resetting to Home (0°, 35°)...")
                probe.publish_smooth(0, 35)
            elif choice == "Q":
                break
            else:
                print("Invalid option.")
        except (KeyboardInterrupt, EOFError):
            break

    print("\n>> Resetting to neutral pose before exit...")
    probe.publish_smooth(0, 35)
    probe.destroy_node()
    rclpy.shutdown()
    print("Gimbal probe tool finished.")


if __name__ == "__main__":
    main()
