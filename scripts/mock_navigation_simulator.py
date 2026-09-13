#!/usr/bin/env python3
"""
mock_navigation_simulator.py — Real-Time Offline Navigation & Telemetry Simulator
Platform: ROS 2 (Runs 100% offline on Workstation without physical robot)
Author: Eleana Osei Owusu & Joel Nii Adjetey Ahulu (GCTU)

Simulates the complete physical robot navigation stack using the real room map:
  1. Publishes /map from maps/room_map_20260812_0826.png.
  2. Publishes dynamic 10 Hz rolling local costmap (/local_costmap/costmap) with obstacle & inflation.
  3. Publishes live AMCL particle cloud (/particlecloud) with Gaussian convergence spread.
  4. Publishes simulated 2D LiDAR scans (/scan_downsampled) with obstacle reflections.
  5. Publishes Nav2 planned global paths (/plan) and local trajectory (/local_plan).
  6. Broadcasts full TF tree: map -> odom_frame -> base_footprint -> laser_frame.
  7. Responds interactively to /goal_pose (navigates toward target) and /initialpose (teleports AMR).
"""

import os
import math
import time
import heapq
import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid, Path
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import (
    PoseStamped,
    PoseWithCovarianceStamped,
    PoseArray,
    Pose,
    Twist,
    TransformStamped
)
from std_msgs.msg import UInt16
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster


class MockNavigationSimulator(Node):
    def __init__(self):
        super().__init__('mock_navigation_simulator')

        # ── Map Configuration ────────────────────────────────────────────────
        map_path = os.path.join(os.path.dirname(__file__), '..', 'maps', 'room_map_20260812_0826.png')
        map_img = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
        if map_img is None:
            self.get_logger().warn(f'Could not find {map_path}, generating synthetic room layout.')
            map_img = np.full((195, 185), 205, dtype=np.uint8)
            map_img[30:170, 30:160] = 254  # Free space
            map_img[30, 30:160] = 0        # North wall
            map_img[170, 30:160] = 0       # South wall
            map_img[30:170, 30] = 0        # West wall
            map_img[30:170, 160] = 0       # East wall

        self.map_h, self.map_w = map_img.shape
        self.map_res = 0.05
        self.map_origin_x = -2.40
        self.map_origin_y = -3.84

        # Convert image to ROS OccupancyGrid format (-1 unknown, 0 free, 100 occupied)
        # In PNG row 0 is top (Y_max), flip vertically so row 0 is bottom (Y_min = map origin)
        cartesian_img = cv2.flip(map_img, 0)
        self.cartesian_img = cartesian_img
        grid_data = np.full((self.map_h, self.map_w), -1, dtype=np.int8)
        grid_data[cartesian_img == 254] = 0    # Free
        grid_data[cartesian_img == 0] = 100    # Occupied
        self.occupancy_data = grid_data.flatten().tolist()

        # ── Collision Inflation & A* Grid Path Planner ──────────────────────
        is_obstacle = (cartesian_img != 254).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.inflated_grid = cv2.dilate(is_obstacle, kernel)
        self.active_path = []  # List of (x, y) waypoints around walls

        # ── Global Costmap Precomputation (Encompassing full building map) ──
        is_wall = (cartesian_img == 0).astype(np.uint8)
        dist_transform = cv2.distanceTransform(1 - is_wall, cv2.DIST_L2, 5) * self.map_res
        global_grid = np.full((self.map_h, self.map_w), -1, dtype=np.int8)
        global_grid[cartesian_img == 254] = 0
        global_grid[is_wall == 1] = 100
        inf_zone = (dist_transform > 0) & (dist_transform <= 0.35) & (is_wall == 0)
        global_grid[inf_zone] = (99 * np.exp(-6.0 * (dist_transform[inf_zone] - 0.05))).clip(1, 99).astype(np.int8)
        self.global_costmap_data = global_grid.flatten().tolist()

        # ── Simulated Robot State ────────────────────────────────────────────
        self.robot_x = 0.08
        self.robot_y = 0.05
        self.last_safe_x = 0.08
        self.last_safe_y = 0.05
        self.robot_yaw = 0.0
        self.target_x = 0.40
        self.target_y = 0.00
        self.target_yaw = 0.0
        self.final_goal_x = 0.40
        self.final_goal_y = 0.00

        # Mission corridor patrol circuit
        self.patrol_circuit = [
            (0.08, 0.05),  # Home Base
            (0.40, 0.00),  # WP1 Runway
            (0.70, 0.35),  # WP2 Curve
            (0.35, 0.15),  # WP3 Return
        ]
        self.circuit_idx = 1
        self.auto_patrol = True

        # ── QoS Profiles ─────────────────────────────────────────────────────
        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        sensor_qos = QoSProfile(
            depth=5,
            reliability=ReliabilityPolicy.BEST_EFFORT
        )

        # ── Publishers ───────────────────────────────────────────────────────
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', map_qos)
        self.global_costmap_pub = self.create_publisher(OccupancyGrid, '/global_costmap/costmap', map_qos)
        self.amcl_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/amcl_pose', 10)
        self.particles_pub = self.create_publisher(PoseArray, '/particlecloud', 10)
        self.local_costmap_pub = self.create_publisher(OccupancyGrid, '/local_costmap/costmap', 10)
        self.scan_pub = self.create_publisher(LaserScan, '/scan_downsampled', sensor_qos)
        self.raw_scan_pub = self.create_publisher(LaserScan, '/scan', sensor_qos)
        self.plan_pub = self.create_publisher(Path, '/plan', 10)
        self.local_plan_pub = self.create_publisher(Path, '/local_plan', 10)
        self.battery_pub = self.create_publisher(UInt16, '/battery', 10)

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(PoseStamped, '/goal_pose', self._on_goal, 10)
        self.create_subscription(PoseWithCovarianceStamped, '/initialpose', self._on_initialpose, 10)
        self.create_subscription(Twist, '/cmd_vel', self._on_cmd_vel, 10)

        # ── TF Broadcasters ──────────────────────────────────────────────────
        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)

        # Broadcast static laser transform: base_footprint -> laser_frame (Z=0.079m)
        stf = TransformStamped()
        stf.header.stamp = self.get_clock().now().to_msg()
        stf.header.frame_id = 'base_footprint'
        stf.child_frame_id = 'laser_frame'
        stf.transform.translation.x = 0.0
        stf.transform.translation.y = 0.0
        stf.transform.translation.z = 0.079
        stf.transform.rotation.w = 1.0
        self.static_tf_broadcaster.sendTransform(stf)

        # ── Timers ───────────────────────────────────────────────────────────
        # Publish static map once every 2s
        self.create_timer(2.0, self._publish_map)
        # Main simulation update loop at 10 Hz
        self.create_timer(0.1, self._sim_tick)

        self._publish_map()
        self.get_logger().info('Mock Navigation Simulator ready. Ingesting room map and generating dynamic navigation telemetry.')

    def _publish_map(self):
        stamp = self.get_clock().now().to_msg()
        msg = OccupancyGrid()
        msg.header.stamp = stamp
        msg.header.frame_id = 'map'
        msg.info.resolution = self.map_res
        msg.info.width = self.map_w
        msg.info.height = self.map_h
        msg.info.origin.position.x = self.map_origin_x
        msg.info.origin.position.y = self.map_origin_y
        msg.info.origin.orientation.w = 1.0
        msg.data = self.occupancy_data
        self.map_pub.publish(msg)

        gc_msg = OccupancyGrid()
        gc_msg.header.stamp = stamp
        gc_msg.header.frame_id = 'map'
        gc_msg.info.resolution = self.map_res
        gc_msg.info.width = self.map_w
        gc_msg.info.height = self.map_h
        gc_msg.info.origin.position.x = self.map_origin_x
        gc_msg.info.origin.position.y = self.map_origin_y
        gc_msg.info.origin.orientation.w = 1.0
        gc_msg.data = self.global_costmap_data
        self.global_costmap_pub.publish(gc_msg)

    def _find_nearest_free(self, r: int, c: int):
        """Finds nearest free cell if coordinates are inside an obstacle."""
        if 0 <= r < self.map_h and 0 <= c < self.map_w and self.inflated_grid[r, c] == 0:
            return r, c
        for rad in range(1, 15):
            for dr in range(-rad, rad + 1):
                for dc in range(-rad, rad + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.map_h and 0 <= nc < self.map_w and self.inflated_grid[nr, nc] == 0:
                        return nr, nc
        return r, c

    def _plan_astar(self, sx: float, sy: float, gx: float, gy: float):
        """Calculates collision-free A* path around room partition walls and obstacles."""
        sr = int((sy - self.map_origin_y) / self.map_res)
        sc = int((sx - self.map_origin_x) / self.map_res)
        gr = int((gy - self.map_origin_y) / self.map_res)
        gc = int((gx - self.map_origin_x) / self.map_res)

        start = self._find_nearest_free(sr, sc)
        goal = self._find_nearest_free(gr, gc)

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        def h(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        found = False
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                found = True
                break
            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.map_h and 0 <= nc < self.map_w and self.inflated_grid[nr, nc] == 0:
                    cost = 1.414 if (dr != 0 and dc != 0) else 1.0
                    tg = g_score[current] + cost
                    nb = (nr, nc)
                    if tg < g_score.get(nb, float('inf')):
                        came_from[nb] = current
                        g_score[nb] = tg
                        f = tg + h(nb, goal)
                        heapq.heappush(open_set, (f, nb))

        if not found:
            return []

        curr = goal
        cells = []
        while curr in came_from:
            cells.append(curr)
            curr = came_from[curr]
        cells.reverse()

        # Downsample waypoints (every 3 cells ~ 15 cm) + final target
        pts = []
        for i in range(0, len(cells), 3):
            wx = self.map_origin_x + (cells[i][1] + 0.5) * self.map_res
            wy = self.map_origin_y + (cells[i][0] + 0.5) * self.map_res
            pts.append((wx, wy))
        pts.append((gx, gy))
        return pts

    def _on_goal(self, msg: PoseStamped):
        gx = msg.pose.position.x
        gy = msg.pose.position.y
        qz = msg.pose.orientation.z
        qw = msg.pose.orientation.w
        self.target_yaw = 2.0 * math.atan2(qz, qw)
        self.final_goal_x = gx
        self.final_goal_y = gy
        self.auto_patrol = False

        self.get_logger().info(f'Interactive Goal received: ({gx:.2f}m, {gy:.2f}m). Planning A* obstacle-free route...')
        path = self._plan_astar(self.robot_x, self.robot_y, gx, gy)
        if path:
            self.active_path = path
            self.target_x, self.target_y = self.active_path.pop(0)
            self.get_logger().info(f'A* route planned: {len(path)} waypoints safely circumventing partition walls.')
        else:
            self.get_logger().warn(f'No obstacle-free path to ({gx:.2f}m, {gy:.2f}m)! Goal is unreachable or inside a wall.')
            # Halt safely in place, maintaining collision protection without blindly roaming
            self.active_path = []
            self.target_x = self.robot_x
            self.target_y = self.robot_y

    def _on_cmd_vel(self, msg: Twist):
        if abs(msg.linear.x) < 1e-4 and abs(msg.angular.z) < 1e-4:
            self.auto_patrol = False
            self.active_path = []
            self.target_x = self.robot_x
            self.target_y = self.robot_y
            self.get_logger().info('Mock Robot halted via /cmd_vel zero clamp (E-Stop).')

    def _on_initialpose(self, msg: PoseWithCovarianceStamped):
        px = msg.pose.pose.position.x
        py = msg.pose.pose.position.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        yaw = 2.0 * math.atan2(qz, qw)

        c_col = int((px - self.map_origin_x) / self.map_res)
        c_row = int((py - self.map_origin_y) / self.map_res)

        # Guard: if operator placed initial pose on a wall, reject and reset to Home Base
        if 0 <= c_col < self.map_w and 0 <= c_row < self.map_h and self.cartesian_img[c_row, c_col] == 0:
            self.get_logger().warn(f'Initial pose ({px:.2f}m, {py:.2f}m) is inside a wall! Resetting to Home Base (0.08, 0.05).')
            self.robot_x = 0.08
            self.robot_y = 0.05
            self.robot_yaw = 0.0
            self.last_safe_x = 0.08
            self.last_safe_y = 0.05
        else:
            self.robot_x = px
            self.robot_y = py
            self.robot_yaw = yaw
            self.last_safe_x = px
            self.last_safe_y = py
            self.get_logger().info(f'AMCL Initial Pose set to: ({self.robot_x:.2f}m, {self.robot_y:.2f}m, {math.degrees(self.robot_yaw):.1f}°)')

        self.auto_patrol = False
        self.active_path = []
        self.target_x = self.robot_x
        self.target_y = self.robot_y

    def _sim_tick(self):
        now = self.get_clock().now()
        stamp = now.to_msg()

        # 0. Self-healing check: if robot finds itself stuck on a wall, bounce to last safe point
        curr_col = int((self.robot_x - self.map_origin_x) / self.map_res)
        curr_row = int((self.robot_y - self.map_origin_y) / self.map_res)
        if 0 <= curr_col < self.map_w and 0 <= curr_row < self.map_h and self.cartesian_img[curr_row, curr_col] == 0:
            self.get_logger().warn(f'Robot was inside wall at ({self.robot_x:.2f}, {self.robot_y:.2f})! Restoring safe pose ({self.last_safe_x:.2f}, {self.last_safe_y:.2f}).')
            self.robot_x = self.last_safe_x
            self.robot_y = self.last_safe_y
            self.active_path = []
            self.target_x = self.last_safe_x
            self.target_y = self.last_safe_y

        # 1. Update Robot Kinematics toward Target
        dx = self.target_x - self.robot_x
        dy = self.target_y - self.robot_y
        dist = math.hypot(dx, dy)

        if dist > 0.05:
            desired_yaw = math.atan2(dy, dx)
            yaw_diff = (desired_yaw - self.robot_yaw + math.pi) % (2 * math.pi) - math.pi

            # Differential Drive Rotate-to-Heading:
            # If yaw error > ~20 degrees, rotate in place first before moving forward
            if abs(yaw_diff) > 0.35:
                self.robot_yaw += math.copysign(min(abs(yaw_diff), 0.22), yaw_diff)
                step = 0.0  # Stop linear advance until heading is aligned
            else:
                self.robot_yaw += math.copysign(min(abs(yaw_diff), 0.15), yaw_diff)
                step = min(dist, 0.025) * max(0.2, math.cos(yaw_diff))

            next_x = self.robot_x + step * math.cos(self.robot_yaw)
            next_y = self.robot_y + step * math.sin(self.robot_yaw)
            c_col = int((next_x - self.map_origin_x) / self.map_res)
            c_row = int((next_y - self.map_origin_y) / self.map_res)

            # Check if proposed step collides with solid wall (0 in PNG)
            if 0 <= c_col < self.map_w and 0 <= c_row < self.map_h and self.cartesian_img[c_row, c_col] == 0:
                # Solid wall collision: maintain safe pose and re-plan route
                self.robot_x = self.last_safe_x
                self.robot_y = self.last_safe_y
                if self.final_goal_x is not None and not self.auto_patrol:
                    self.get_logger().warn(f'Obstacle guard held safe pose at ({self.last_safe_x:.2f}, {self.last_safe_y:.2f}). Re-planning path to ({self.final_goal_x:.2f}, {self.final_goal_y:.2f})...')
                    new_path = self._plan_astar(self.robot_x, self.robot_y, self.final_goal_x, self.final_goal_y)
                    if new_path:
                        self.active_path = new_path
                        self.target_x, self.target_y = self.active_path.pop(0)
                    else:
                        self.active_path = []
                        self.target_x = self.robot_x
                        self.target_y = self.robot_y
                else:
                    self.active_path = []
                    self.target_x = self.robot_x
                    self.target_y = self.robot_y
            else:
                self.robot_x = next_x
                self.robot_y = next_y
                self.last_safe_x = next_x
                self.last_safe_y = next_y
        else:
            # Current waypoint reached!
            if self.active_path:
                self.target_x, self.target_y = self.active_path.pop(0)
            elif self.auto_patrol:
                self.circuit_idx = (self.circuit_idx + 1) % len(self.patrol_circuit)
                gx, gy = self.patrol_circuit[self.circuit_idx]
                p_path = self._plan_astar(self.robot_x, self.robot_y, gx, gy)
                if p_path:
                    self.active_path = p_path
                    self.target_x, self.target_y = self.active_path.pop(0)
                else:
                    self.target_x, self.target_y = gx, gy
            else:
                # Final destination reached
                pass

        rx, ry, ryaw = self.robot_x, self.robot_y, self.robot_yaw

        # 2. Broadcast Dynamic TF (map -> odom_frame -> base_footprint)
        # map -> odom_frame (identity for clean simulation)
        t_mo = TransformStamped()
        t_mo.header.stamp = stamp
        t_mo.header.frame_id = 'map'
        t_mo.child_frame_id = 'odom_frame'
        t_mo.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t_mo)

        # odom_frame -> base_footprint (robot pose)
        t_ob = TransformStamped()
        t_ob.header.stamp = stamp
        t_ob.header.frame_id = 'odom_frame'
        t_ob.child_frame_id = 'base_footprint'
        t_ob.transform.translation.x = rx
        t_ob.transform.translation.y = ry
        t_ob.transform.translation.z = 0.0
        t_ob.transform.rotation.z = math.sin(ryaw / 2.0)
        t_ob.transform.rotation.w = math.cos(ryaw / 2.0)
        self.tf_broadcaster.sendTransform(t_ob)

        # 3. Publish /amcl_pose
        pose_msg = PoseWithCovarianceStamped()
        pose_msg.header.stamp = stamp
        pose_msg.header.frame_id = 'map'
        pose_msg.pose.pose.position.x = rx
        pose_msg.pose.pose.position.y = ry
        pose_msg.pose.pose.orientation.z = math.sin(ryaw / 2.0)
        pose_msg.pose.pose.orientation.w = math.cos(ryaw / 2.0)
        pose_msg.pose.covariance[0] = 0.04
        pose_msg.pose.covariance[7] = 0.04
        pose_msg.pose.covariance[35] = 0.02
        self.amcl_pose_pub.publish(pose_msg)

        # 4. Publish /particlecloud (Swarm of ~80 particles with ±0.06m variance)
        par_msg = PoseArray()
        par_msg.header.stamp = stamp
        par_msg.header.frame_id = 'map'
        for _ in range(80):
            p = Pose()
            p.position.x = rx + np.random.normal(0, 0.05)
            p.position.y = ry + np.random.normal(0, 0.05)
            p_yaw = ryaw + np.random.normal(0, 0.08)
            p.orientation.z = math.sin(p_yaw / 2.0)
            p.orientation.w = math.cos(p_yaw / 2.0)
            par_msg.poses.append(p)
        self.particles_pub.publish(par_msg)

        # 5. Publish /local_costmap/costmap (5m x 5m rolling window = 100x100 cells @ 0.05m)
        lc_size = 100
        lc_res = self.map_res
        lc_ox = rx - (lc_size * lc_res) / 2.0
        lc_oy = ry - (lc_size * lc_res) / 2.0

        r_start = int((lc_oy - self.map_origin_y) / self.map_res)
        c_start = int((lc_ox - self.map_origin_x) / self.map_res)
        r_end = r_start + lc_size
        c_end = c_start + lc_size

        lc_grid = np.zeros((lc_size, lc_size), dtype=np.int8)
        mr_min = max(0, r_start)
        mr_max = min(self.map_h, r_end)
        mc_min = max(0, c_start)
        mc_max = min(self.map_w, c_end)

        if mr_max > mr_min and mc_max > mc_min:
            lr_min = mr_min - r_start
            lr_max = lr_min + (mr_max - mr_min)
            lc_min = mc_min - c_start
            lc_max = lc_min + (mc_max - mc_min)
            sub = self.cartesian_img[mr_min:mr_max, mc_min:mc_max]
            lc_grid[lr_min:lr_max, lc_min:lc_max][sub == 0] = 100

        # Place simulated dynamic obstacle 0.6m ahead of the robot
        obs_x = rx + 0.6 * math.cos(ryaw)
        obs_y = ry + 0.6 * math.sin(ryaw)
        obs_col = int((obs_x - lc_ox) / lc_res)
        obs_row = int((obs_y - lc_oy) / lc_res)
        if 0 <= obs_row < lc_size and 0 <= obs_col < lc_size:
            cv2.circle(lc_grid, (obs_col, obs_row), 2, 100, -1)

        # Radial inflation cushion across local window
        obs_mask = (lc_grid == 100).astype(np.uint8)
        if np.any(obs_mask):
            dt = cv2.distanceTransform(1 - obs_mask, cv2.DIST_L2, 3) * lc_res
            inf_zone = (dt > 0) & (dt <= 0.35) & (obs_mask == 0)
            lc_grid[inf_zone] = (99 * np.exp(-6.0 * (dt[inf_zone] - 0.05))).clip(1, 99).astype(np.int8)

        cost_msg = OccupancyGrid()
        cost_msg.header.stamp = stamp
        cost_msg.header.frame_id = 'odom_frame'
        cost_msg.info.resolution = lc_res
        cost_msg.info.width = lc_size
        cost_msg.info.height = lc_size
        cost_msg.info.origin.position.x = lc_ox
        cost_msg.info.origin.position.y = lc_oy
        cost_msg.info.origin.orientation.w = 1.0
        cost_msg.data = lc_grid.flatten().tolist()
        self.local_costmap_pub.publish(cost_msg)

        # 6. Publish /scan_downsampled (120 beams) & /scan via Real Raycasting against Map Walls
        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = 'laser_frame'
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = (2 * math.pi) / 120
        scan.range_min = 0.12
        scan.range_max = 8.0

        ranges = []
        angles = np.linspace(-math.pi, math.pi, 120, endpoint=False)
        for ang in angles:
            world_ang = ryaw + ang
            cos_a = math.cos(world_ang)
            sin_a = math.sin(world_ang)
            hit_dist = scan.range_max
            # Step in 0.04m increments along ray
            for d in np.arange(scan.range_min, scan.range_max, 0.04):
                wx = rx + d * cos_a
                wy = ry + d * sin_a
                r = int((wy - self.map_origin_y) / self.map_res)
                c = int((wx - self.map_origin_x) / self.map_res)
                if 0 <= r < self.map_h and 0 <= c < self.map_w:
                    if self.cartesian_img[r, c] == 0:
                        hit_dist = d
                        break
                else:
                    hit_dist = d
                    break
            ranges.append(float(hit_dist))
        scan.ranges = ranges
        self.scan_pub.publish(scan)
        self.raw_scan_pub.publish(scan)

        # 7. Publish /plan (Global Path) and /local_plan (Local Controller Carrot)
        plan_msg = Path()
        plan_msg.header.stamp = stamp
        plan_msg.header.frame_id = 'map'
        if self.active_path:
            pts_to_draw = [(rx, ry), (self.target_x, self.target_y)] + self.active_path
            for px, py in pts_to_draw:
                ps = PoseStamped()
                ps.header.stamp = stamp
                ps.header.frame_id = 'map'
                ps.pose.position.x = float(px)
                ps.pose.position.y = float(py)
                plan_msg.poses.append(ps)
        else:
            steps = 15
            for s in range(steps + 1):
                t = s / float(steps)
                ps = PoseStamped()
                ps.header.stamp = stamp
                ps.header.frame_id = 'map'
                ps.pose.position.x = rx + t * (self.target_x - rx)
                ps.pose.position.y = ry + t * (self.target_y - ry)
                plan_msg.poses.append(ps)
        self.plan_pub.publish(plan_msg)

        local_plan = Path()
        local_plan.header.stamp = stamp
        local_plan.header.frame_id = 'map'
        for s in range(6):
            t = s / 5.0
            ps = PoseStamped()
            ps.header.stamp = stamp
            ps.header.frame_id = 'map'
            ps.pose.position.x = rx + t * 0.35 * math.cos(ryaw)
            ps.pose.position.y = ry + t * 0.35 * math.sin(ryaw)
            local_plan.poses.append(ps)
        self.local_plan_pub.publish(local_plan)

        # 8. Publish /battery (Yahboom Micro-ROS 2S Li-ion 7.8V telemetry)
        bat_msg = UInt16()
        bat_msg.data = 78  # 7.8V (Healthy)
        self.battery_pub.publish(bat_msg)


def main():
    rclpy.init()
    node = MockNavigationSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
