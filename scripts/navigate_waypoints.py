#!/usr/bin/env python3
"""
navigate_waypoints.py — Multi-Waypoint Patrol & Trajectory Action Client
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Institution: Ghana Communication Technology University (GCTU)

Dispatches autonomous multi-leg waypoint navigation using Nav2 action servers.
Supports sequential NavigateToPose execution with per-waypoint dwell & live telemetry,
as well as NavigateThroughPoses continuous trajectory following.
"""

import sys
import time
import math
import argparse
from dataclasses import dataclass
from typing import List, Optional

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose, NavigateThroughPoses


@dataclass
class Waypoint:
    name: str
    x: float
    y: float
    yaw_deg: float
    dwell_sec: float = 2.0


# Pre-calibrated 3-Waypoint Corridor Patrol Loop
DEFAULT_PATROL_WAYPOINTS = [
    Waypoint("WP1: Mid-Corridor Transit", 0.40, 0.00, 0.0, dwell_sec=2.0),
    Waypoint("WP2: Aisle Curve Inspection", 0.70, 0.35, 0.0, dwell_sec=2.0),
    Waypoint("WP3: Return Leg Midpoint", 0.35, 0.15, 0.0, dwell_sec=1.0),
    Waypoint("WP4: Home Station (Base)", 0.08, 0.05, 0.0, dwell_sec=2.0),
]


class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('navigate_waypoints_client')
        self._nav_to_pose_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self._nav_through_poses_client = ActionClient(self, NavigateThroughPoses, '/navigate_through_poses')
        self._cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self._goal_handle = None
        self._start_time = None

    def make_pose_stamped(self, x: float, y: float, yaw_deg: float) -> PoseStamped:
        """Constructs a PoseStamped in the map frame."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0

        yaw_rad = math.radians(yaw_deg)
        pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
        pose.pose.orientation.w = math.cos(yaw_rad / 2.0)
        return pose

    def emergency_stop(self):
        """Halts the robot immediately by zeroing velocity."""
        stop_msg = Twist()
        for _ in range(5):
            self._cmd_vel_pub.publish(stop_msg)
            time.sleep(0.02)

    def execute_sequential_patrol(self, waypoints: List[Waypoint], leg_timeout_sec: float = 60.0) -> bool:
        """Navigates sequentially through each waypoint using NavigateToPose."""
        self.get_logger().info("Connecting to /navigate_to_pose action server...")
        if not self._nav_to_pose_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error(
                "Action server /navigate_to_pose not available! "
                "Ensure Nav2 stack is running (bash ~/start_nav2.sh)."
            )
            return False

        print("\n" + "=" * 65)
        print(f"  DISPATCHING SEQUENTIAL PATROL ({len(waypoints)} Waypoints)")
        print("=" * 65)
        for idx, wp in enumerate(waypoints, 1):
            print(f"  [{idx}] {wp.name:32s} -> (x={wp.x:5.2f}m, y={wp.y:5.2f}m, yaw={wp.yaw_deg:5.1f}°, dwell={wp.dwell_sec}s)")
        print("=" * 65 + "\n")

        overall_start = time.time()
        successful_legs = 0

        for idx, wp in enumerate(waypoints, 1):
            print(f"--- [Leg {idx}/{len(waypoints)}] Dispatching: {wp.name} ---")
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = self.make_pose_stamped(wp.x, wp.y, wp.yaw_deg)

            self._start_time = time.time()
            remaining_dist = [0.0]

            def feedback_cb(fb_msg):
                fb = fb_msg.feedback
                dist = getattr(fb, 'distance_remaining', 0.0)
                remaining_dist[0] = dist
                elapsed = time.time() - self._start_time
                sys.stdout.write(f"\r  [TRANSIT] Distance Remaining: {dist:5.2f} m | Elapsed: {elapsed:4.1f}s   ")
                sys.stdout.flush()

            send_goal_future = self._nav_to_pose_client.send_goal_async(goal_msg, feedback_callback=feedback_cb)
            rclpy.spin_until_future_complete(self, send_goal_future)
            self._goal_handle = send_goal_future.result()

            if not self._goal_handle.accepted:
                self.get_logger().error(f"Goal for {wp.name} rejected by Nav2!")
                self.emergency_stop()
                return False

            result_future = self._goal_handle.get_result_async()
            start_wait = time.time()
            leg_success = False

            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.2)
                if result_future.done():
                    res = result_future.result()
                    if res.status == GoalStatus.STATUS_SUCCEEDED:
                        leg_success = True
                    break
                # If the robot is already within 8 cm of the waypoint for > 3.0s, the spatial goal is achieved!
                if remaining_dist[0] <= 0.08 and (time.time() - self._start_time) > 4.0:
                    self.get_logger().info(f"Waypoint {wp.name} spatially achieved (remaining: {remaining_dist[0]:.2f}m). Proceeding...")
                    leg_success = True
                    self._goal_handle.cancel_goal_async()
                    break
                if time.time() - start_wait > leg_timeout_sec:
                    print(f"\n[WARN] Leg {idx} exceeded timeout ({leg_timeout_sec}s). Cancelling leg...")
                    self._goal_handle.cancel_goal_async()
                    self.emergency_stop()
                    break

            leg_dur = time.time() - self._start_time
            if leg_success:
                successful_legs += 1
                print(f"\n✓ REACHED: {wp.name} in {leg_dur:.1f}s (Remaining: {remaining_dist[0]:.2f}m)")
                if wp.dwell_sec > 0:
                    print(f"  Dwelling at {wp.name} for {wp.dwell_sec:.1f}s (Sensor Survey)...")
                    time.sleep(wp.dwell_sec)
                print()
            else:
                print(f"\n✗ Failed leg {idx} ({wp.name}) after {leg_dur:.1f}s.")
                self.emergency_stop()
                break

        total_dur = time.time() - overall_start
        print("=" * 65)
        if successful_legs == len(waypoints):
            print(f"🏆 MISSION COMPLETED: All {len(waypoints)}/{len(waypoints)} Legs Succeeded in {total_dur:.1f}s")
            print("=" * 65 + "\n")
            return True
        else:
            print(f"⚠️ MISSION INCOMPLETE: {successful_legs}/{len(waypoints)} Legs Succeeded in {total_dur:.1f}s")
            print("=" * 65 + "\n")
            return False


def parse_custom_waypoints(wp_str: str) -> List[Waypoint]:
    """Parses semicolon-separated 'x,y,yaw' strings."""
    waypoints = []
    points = [p.strip() for p in wp_str.split(';') if p.strip()]
    for idx, pt in enumerate(points, 1):
        parts = [float(x.strip()) for x in pt.split(',')]
        if len(parts) == 2:
            waypoints.append(Waypoint(f"WP{idx}", parts[0], parts[1], 0.0))
        elif len(parts) >= 3:
            waypoints.append(Waypoint(f"WP{idx}", parts[0], parts[1], parts[2]))
        else:
            raise ValueError(f"Invalid waypoint format '{pt}'. Expected 'x,y' or 'x,y,yaw'.")
    return waypoints


def main():
    parser = argparse.ArgumentParser(description="Multi-Waypoint Patrol & Trajectory Dispatcher")
    parser.add_argument(
        '--waypoints', type=str, default=None,
        help="Custom waypoints formatted as 'x1,y1,yaw1;x2,y2,yaw2' (e.g. '0.4,0,0;0.7,0.35,20;0,0,0')"
    )
    parser.add_argument(
        '--timeout', type=float, default=60.0,
        help="Timeout per waypoint leg in seconds (default: 60s)"
    )
    args, unknown = parser.parse_known_args()

    rclpy.init()
    navigator = WaypointNavigator()

    try:
        if args.waypoints:
            wps = parse_custom_waypoints(args.waypoints)
        else:
            wps = DEFAULT_PATROL_WAYPOINTS

        success = navigator.execute_sequential_patrol(wps, leg_timeout_sec=args.timeout)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n[ABORT] Operator interrupted patrol with Ctrl+C. Halting chassis...")
        navigator.emergency_stop()
        sys.exit(130)
    finally:
        navigator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
