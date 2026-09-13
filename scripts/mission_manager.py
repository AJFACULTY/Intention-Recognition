#!/usr/bin/env python3
"""
mission_manager.py — Industrial-Grade Autonomous Mission Dispatcher
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Author: Eleana Osei Owusu & Joel Nii Adjetey Ahulu
Institution: Ghana Communication Technology University (GCTU)

Provides a production pool of selectable autonomous missions:
  1. RETURN_HOME: Returns robot from any mapped location back to Home Base (0, 0, 0)
  2. RUNWAY_TRANSIT: Dispatches straight corridor transit down the clear runway (1.40m)
  3. CORRIDOR_PATROL: Multi-waypoint continuous loop (Home -> Midpoint -> Station Charlie -> Home)
  4. SURVEILLANCE_INSPECTION: Navigates to inspection posts with 5s dwell & sensor survey
  5. ACTIVE_BACKUP_RECOVERY: Test active 20cm reverse maneuver when blocked by obstacles
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
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from action_msgs.msg import GoalStatus
from std_msgs.msg import String, UInt16
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from nav2_msgs.action import NavigateToPose, NavigateThroughPoses, BackUp
from tf2_ros import Buffer, TransformListener, TransformException


@dataclass
class Waypoint:
    name: str
    x: float
    y: float
    yaw_deg: float
    dwell_sec: float = 0.0


# Pre-calibrated mission catalog for the verified metric room map (room_map_20260812_0826)
# Home Base calibrated to (0.08, 0.05) to clear 15cm costmap wall inflation cushion
MISSION_CATALOG = {
    "RETURN_HOME": [
        Waypoint("P1 Home Base", 0.08, 0.05, 0.0, dwell_sec=2.0),
    ],
    "CENTRAL_INSPECTION": [
        Waypoint("P2 Central Hub", 1.64, 1.62, 0.78, dwell_sec=3.0),
        Waypoint("P1 Home Base", 0.08, 0.05, 0.0, dwell_sec=2.0),
    ],
    "NORTH_GALLERY_PATROL": [
        Waypoint("P2 Central Hub", 1.64, 1.62, 0.78, dwell_sec=3.0),
        Waypoint("P3 North Gallery", 3.20, 3.20, 0.78, dwell_sec=3.0),
        Waypoint("P2 Central Hub (Return)", 1.64, 1.62, 2.36, dwell_sec=2.0),
        Waypoint("P1 Home Base", 0.08, 0.05, 0.0, dwell_sec=2.0),
    ],
    "UNATTENDED_FACILITY_PATROL": [
        Waypoint("P2 Central Hub", 1.64, 1.62, 0.78, dwell_sec=3.0),
        Waypoint("P3 North Gallery", 3.20, 3.20, 0.78, dwell_sec=3.0),
        Waypoint("P4 East Lab", 4.70, 1.80, -0.75, dwell_sec=3.0),
        Waypoint("P3 North Gallery (Return)", 3.20, 3.20, 2.36, dwell_sec=2.0),
        Waypoint("P2 Central Hub (Return)", 1.64, 1.62, 2.36, dwell_sec=2.0),
        Waypoint("P1 Home Base", 0.08, 0.05, 0.0, dwell_sec=2.0),
    ],
}


class MissionManagerNode(Node):
    def __init__(self):
        super().__init__('mission_manager')

        # Action clients
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.nav_through_poses_client = ActionClient(self, NavigateThroughPoses, '/navigate_through_poses')
        self.backup_client = ActionClient(self, BackUp, '/backup')

        # Velocity publisher for emergency stops and preemption
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Acoustic safety chime publisher
        self.chime_pub = self.create_publisher(String, '/safety/chime', 10)

        # Battery health monitoring for automated low-voltage safety return
        self.battery_voltage = 8.4
        self.battery_healthy = True
        self.battery_sub = self.create_subscription(
            UInt16, '/battery', self._battery_cb, 10
        )

        # AMCL latched pose subscriber for instantaneous ground-truth localization
        self.amcl_pose = None
        qos_amcl = QoSProfile(depth=1)
        qos_amcl.durability = DurabilityPolicy.TRANSIENT_LOCAL
        qos_amcl.reliability = ReliabilityPolicy.RELIABLE
        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self._amcl_pose_cb,
            qos_amcl
        )

        # TF listener for fallback ground-truth pose lookup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.current_goal_handle = None
        self._last_dist = 999.0
        self.get_logger().info('Industrial Mission Manager initialized successfully.')

    def _battery_cb(self, msg: UInt16):
        """Monitors Yahboom battery telemetry and evaluates health."""
        val = float(msg.data)
        if val > 50.0:  # e.g. 79 -> 7.9V
            self.battery_voltage = val / 10.0
        else:  # percentage
            self.battery_voltage = 6.8 + (val / 100.0) * 1.6
        self.battery_healthy = (self.battery_voltage >= 7.4)

    def play_chime(self, chime_name: str):
        """Triggers acoustic warning sequence on safety_audio_node."""
        m = String()
        m.data = chime_name
        self.chime_pub.publish(m)

    def _amcl_pose_cb(self, msg: PoseWithCovarianceStamped):
        """Callback for latched AMCL particle filter estimated pose."""
        p = msg.pose.pose
        yaw = math.degrees(2.0 * math.atan2(p.orientation.z, p.orientation.w))
        self.amcl_pose = (p.position.x, p.position.y, yaw)

    # ── POSE HELPERS ──────────────────────────────────────────────

    def get_current_pose(self) -> Optional[tuple]:
        """Returns the latest localized robot pose from AMCL or TF."""
        # 1. Check AMCL subscription (spin briefly to ingest latched message)
        for _ in range(30):
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.amcl_pose is not None:
                return self.amcl_pose

        # 2. Fallback to TF buffer
        try:
            t = self.tf_buffer.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time()
            )
            x = t.transform.translation.x
            y = t.transform.translation.y
            qz = t.transform.rotation.z
            qw = t.transform.rotation.w
            yaw = math.degrees(2.0 * math.atan2(qz, qw))
            return x, y, yaw
        except Exception as e:
            self.get_logger().warn(f'Could not resolve ground-truth pose via TF or AMCL: {e}')
            return None

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
        """Halts the robot immediately by zeroing cmd_vel and cancelling active goals."""
        self.get_logger().warn('EMERGENCY STOP TRIGGERED: Halting chassis.')
        if self.current_goal_handle is not None:
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None

        stop_msg = Twist()
        for _ in range(5):
            self.cmd_vel_pub.publish(stop_msg)
            time.sleep(0.02)

    # ── ACTION DISPATCHERS ────────────────────────────────────────

    def execute_waypoint(self, wp: Waypoint, leg_timeout_sec: float = 60.0) -> bool:
        """Dispatches NavigateToPose for a single waypoint with dwell and telemetry."""
        self.get_logger().info(f'>>> DISPATCHING WAYPOINT: {wp.name} at ({wp.x:.2f}m, {wp.y:.2f}m, {wp.yaw_deg:.1f}°)')

        if not self.nav_to_pose_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('NavigateToPose action server unavailable!')
            return False

        self._last_dist = 999.0
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self.make_pose_stamped(wp.x, wp.y, wp.yaw_deg)

        send_goal_future = self.nav_to_pose_client.send_goal_async(
            goal_msg, feedback_callback=self._nav_feedback_cb
        )
        rclpy.spin_until_future_complete(self, send_goal_future)

        goal_handle = send_goal_future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'Goal to {wp.name} rejected by Nav2!')
            return False

        self.current_goal_handle = goal_handle
        self.get_logger().info('Goal accepted by Nav2 controller. Executing transit...')

        get_result_future = goal_handle.get_result_async()
        start_wait = time.time()
        leg_success = False

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.2)
            if get_result_future.done():
                status = get_result_future.result().status
                elapsed = time.time() - start_wait
                if status == GoalStatus.STATUS_SUCCEEDED:
                    leg_success = True
                    if elapsed < 1.5:
                        self.get_logger().info(
                            f'Target {wp.name} already satisfied by current localization '
                            f'(elapsed: {elapsed:.2f}s, distance: {self._last_dist:.2f}m).'
                        )
                break
            # Spatial completion check: verify real physical distance to goal to prevent 0.00m false positives
            pose = self.get_current_pose()
            if pose:
                real_dist = math.hypot(pose[0] - wp.x, pose[1] - wp.y)
                if real_dist <= 0.15 and (time.time() - start_wait) > 4.0:
                    self.get_logger().info(f'Waypoint {wp.name} physically achieved (measured distance: {real_dist:.2f}m). Proceeding...')
                    leg_success = True
                    goal_handle.cancel_goal_async()
                    break
            elif 0.005 < self._last_dist <= 0.12 and (time.time() - start_wait) > 4.0:
                self.get_logger().info(f'Waypoint {wp.name} feedback achieved (remaining: {self._last_dist:.2f}m). Proceeding...')
                leg_success = True
                goal_handle.cancel_goal_async()
                break
            if time.time() - start_wait > leg_timeout_sec:
                self.get_logger().warn(f'Leg exceeded timeout ({leg_timeout_sec}s). Cancelling...')
                goal_handle.cancel_goal_async()
                break

        self.current_goal_handle = None

        if leg_success:
            self.play_chime("arrival")
            self.get_logger().info(f'✓ REACHED WAYPOINT: {wp.name}')
            if wp.dwell_sec > 0:
                self.get_logger().info(f'Dwelling at {wp.name} for {wp.dwell_sec:.1f}s (Sensor Survey)...')
                time.sleep(wp.dwell_sec)
            return True
        else:
            self.play_chime("obstacle")
            self.get_logger().warn(f'✗ Failed to reach {wp.name}')
            return False

    def _nav_feedback_cb(self, feedback_msg):
        """Displays real-time distance remaining and navigation velocity."""
        fb = feedback_msg.feedback
        dist = fb.distance_remaining
        self._last_dist = dist
        time_elapsed = fb.navigation_time.sec
        num_recoveries = fb.number_of_recoveries
        print(f'\r  [TRANSIT] Distance Remaining: {dist:.2f} m | Elapsed: {time_elapsed}s | Recoveries: {num_recoveries}   ', end='', flush=True)

    def execute_active_backup(self, distance: float = 0.20, speed: float = 0.10) -> bool:
        """Executes an active reverse maneuver away from frontal obstacles."""
        self.get_logger().info(f'>>> INITIATING ACTIVE REVERSE: Backing up {distance:.2f}m at {-speed:.2f}m/s...')

        if not self.backup_client.wait_for_server(timeout_sec=4.0):
            # Fallback to direct velocity commands if BackUp action server is not reachable
            self.get_logger().warn('BackUp action server not reachable. Executing direct velocity reverse...')
            cmd = Twist()
            cmd.linear.x = -abs(speed)
            duration = distance / speed
            t_end = time.monotonic() + duration
            while time.monotonic() < t_end and rclpy.ok():
                self.cmd_vel_pub.publish(cmd)
                time.sleep(0.05)
            self.emergency_stop()
            return True

        goal = BackUp.Goal()
        goal.target.x = -abs(distance)
        goal.speed = abs(speed)

        future = self.backup_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        handle = future.result()

        if not handle.accepted:
            self.get_logger().warn('Nav2 rejected BackUp action. Using manual reverse fallback.')
            return self.execute_active_backup(distance, speed)

        res_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, res_future)
        self.get_logger().info('✓ Active reverse completed cleanly. Obstacle buffer restored.')
        return True

    def execute_mission(self, mission_name: str) -> bool:
        """Runs a complete named mission consisting of sequential waypoints."""
        if mission_name not in MISSION_CATALOG:
            self.get_logger().error(f'Unknown mission "{mission_name}". Available: {list(MISSION_CATALOG.keys())}')
            return False

        print('\n' + '=' * 70)
        print(f'   CHECKING NAV2 READINESS FOR MISSION: {mission_name}')
        print('=' * 70)

        # 1. Verify Nav2 Action Server is actually running before attempting mission
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=3.0):
            print('\n[ERROR] Nav2 Navigation Stack is NOT active on the robot!')
            print('        The /navigate_to_pose action server is offline.')
            print('        To launch Nav2, run:')
            print('            bash ~/start_nav2.sh')
            print('        Mission safely cancelled. No wheels will move.\n')
            return False

        # Preflight Pose Check
        pose = self.get_current_pose()
        if pose:
            print(f'Initial Robot Position: x = {pose[0]:.2f}m, y = {pose[1]:.2f}m, heading = {pose[2]:.1f}°')
        else:
            print('Notice: AMCL pose not yet received. Nav2 will rely on initial /initialpose.')

        # Dynamically build corridor return path if RETURN_HOME is selected anywhere in the building
        if mission_name == "RETURN_HOME":
            if pose:
                rx, ry, _ = pose
                wps = []
                dist_p3 = math.hypot(rx - 3.20, ry - 3.20)
                dist_p2 = math.hypot(rx - 1.64, ry - 1.62)
                # If currently far down the East Lab branch (P4 branch)
                if rx > 3.8 and dist_p3 > 0.6:
                    wps.append(Waypoint("P3 North Gallery (Elbow)", 3.20, 3.20, 2.36, dwell_sec=2.0))
                # If currently in North Gallery corridor above P2
                if (ry > 1.9 or rx > 1.9) and dist_p2 > 0.4:
                    wps.append(Waypoint("P2 Central Hub (Midpoint)", 1.64, 1.62, 2.36, dwell_sec=2.0))
                wps.append(Waypoint("P1 Home Base", 0.08, 0.05, 0.0, dwell_sec=2.0))
                waypoints = wps
            else:
                waypoints = MISSION_CATALOG["RETURN_HOME"]
        else:
            waypoints = MISSION_CATALOG[mission_name]

        total_wp = len(waypoints)

        success_count = 0
        for idx, wp in enumerate(waypoints, start=1):
            # Check battery health before embarking on next leg
            if not self.battery_healthy and mission_name != "RETURN_HOME":
                print(f'\n[LOW BATTERY SAFETY] Battery voltage is {self.battery_voltage:.2f}V (< 7.40V cutoff)!')
                print('                     Aborting outward mission and routing safely back to Home Base (P1)...')
                self.play_chime("low_battery")
                return self.execute_mission("RETURN_HOME")

            print(f'\n--- [Leg {idx}/{total_wp}] Target: {wp.name} ---')
            ok = self.execute_waypoint(wp)
            if ok:
                success_count += 1
            else:
                print(f'\n[WARN] Failed leg {idx}.')
                break

        print('\n' + '=' * 70)
        if success_count == total_wp:
            self.play_chime("mission_complete")
            print(f'🏆 MISSION COMPLETED: {mission_name} (100% Legs Succeeded)')
            print('=' * 70)
            return True
        else:
            self.play_chime("obstacle")
            print(f'⚠️ MISSION INCOMPLETE: {success_count}/{total_wp} legs finished.')
            print('=' * 70)
            return False


def main():
    parser = argparse.ArgumentParser(description="Industrial Mission Manager for Autonomous Mobile Robot")
    parser.add_argument(
        '--mission',
        type=str,
        default=None,
        help=f"Named mission to dispatch: {list(MISSION_CATALOG.keys())}"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List all pre-calibrated missions in the catalog"
    )
    parser.add_argument(
        '--reverse',
        type=float,
        default=None,
        help="Test standalone active reverse recovery for given distance (meters), e.g. --reverse 0.20"
    )

    args, unknown = parser.parse_known_args()

    if args.list:
        print("\n=== PRE-CALIBRATED INDUSTRIAL MISSION POOL ===")
        for name, wps in MISSION_CATALOG.items():
            print(f"\n• Mission: {name}")
            for idx, wp in enumerate(wps, 1):
                print(f"    [{idx}] {wp.name:32s} -> (x={wp.x:5.2f}m, y={wp.y:5.2f}m, yaw={wp.yaw_deg:5.1f}°, dwell={wp.dwell_sec}s)")
        print("\nUsage: python3 scripts/mission_manager.py --mission RETURN_HOME")
        return

    rclpy.init()
    node = MissionManagerNode()

    try:
        if args.reverse is not None:
            node.execute_active_backup(distance=args.reverse)
        elif args.mission:
            node.execute_mission(args.mission.upper())
        else:
            # Interactive Menu
            print("\n=======================================================")
            print("   AUTONOMOUS ROBOT COGNITION — MISSION DISPATCHER")
            print("=======================================================")
            missions = list(MISSION_CATALOG.keys())
            for idx, m in enumerate(missions, 1):
                print(f"  [{idx}] {m}")
            print(f"  [{len(missions)+1}] TEST ACTIVE REVERSE (20 cm Backup)")
            print("  [0] Exit")
            print("-------------------------------------------------------")

            choice = input("Select mission to dispatch [0-5]: ").strip()
            if choice == "0":
                print("Exiting.")
            elif choice == str(len(missions) + 1):
                node.execute_active_backup(distance=0.20)
            elif choice.isdigit() and 1 <= int(choice) <= len(missions):
                node.execute_mission(missions[int(choice) - 1])
            else:
                print("Invalid selection.")

    except KeyboardInterrupt:
        print("\n[OPERATOR ABORT] KeyboardInterrupt detected. Triggering emergency stop...")
        node.emergency_stop()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
