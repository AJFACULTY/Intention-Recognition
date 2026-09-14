#!/usr/bin/env python3
"""
web_map_visualizer.py — RViz-Equivalent Web Visualizer for Autonomous Mobile Robot Cognition
Platform: ROS 2 (Raspberry Pi 5 / Workstation)
Author: Eleana Osei Owusu & Joel Nii Adjetey Ahulu (GCTU)

Serves a live real-time web dashboard at http://<HOST_IP>:8080/ providing an RViz-equivalent
visual experience in the browser:
  1. High-resolution occupancy grid room map (/map).
  2. Live 10 Hz Dynamic Local Rolling Costmap (/local_costmap/costmap) with obstacle/inflation shading.
  3. Live AMCL Localization Particle Cloud (/particlecloud) with orientation needles.
  4. TF-synchronized 2D LiDAR scans (/scan_downsampled) projected accurately into map coordinates.
  5. Standard REP-103 RGB Coordinate Frame Axes (Red = +X Forward, Green = +Y Left) at robot pose.
  6. Autonomous Nav2 Global Planned Path (/plan) and Local Controller Trajectory (/local_plan).
  7. Interactive Web 2D Pose Estimation (/initialpose) and 2D Nav Goal (/goal_pose) click-and-drag.
  8. Real-time telemetry, layer toggles, and mission waypoint annotations.

Performance & Stability:
  - Runs headless in <40MB RAM without X11 or OpenGL overhead.
  - Zero-latency multi-threaded rendering engine decoupled from HTTP client request loops.
  - Pre-rendered JPEG memory caching serves frames in <1ms.
"""

import os
import io
import math
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, Path
from sensor_msgs.msg import LaserScan, CompressedImage
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped, PoseArray, Twist
from std_msgs.msg import UInt16, String
from tf2_ros import Buffer, TransformListener, TransformException


class MapVisualizerNode(Node):
    def __init__(self):
        super().__init__('web_map_visualizer')

        self.lock = threading.Lock()

        # ── Map & Coordinate State ───────────────────────────────────────────
        self.map_img = None
        self.map_res = 0.05
        self.map_origin_x = 0.0
        self.map_origin_y = 0.0
        self.map_width = 0
        self.map_height = 0

        # ── Robot State ──────────────────────────────────────────────────────
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.robot_localized = False
        self.last_pose_time = 0.0
        self.trajectory_history = []  # List of (x, y) visited positions

        # ── Battery & Hardware Safety State (Yahboom Micro-ROS) ──────────────
        self.battery_voltage = 7.8
        self.battery_pct = 75
        self.battery_healthy = True
        self.battery_last_time = 0.0

        # ── Waypoints & Patrol Landmarks (L-Form Alignment) ──────────────────
        self.corridor_landmarks = [
            (0.08, 0.05, "P1 Home Base"),
            (1.64, 1.62, "P2 Central Hub"),
            (3.20, 3.20, "P3 North Gallery"),
            (4.70, 1.80, "P4 East Lab"),
        ]

        # ── Nav2 Paths, Scans & Goals ────────────────────────────────────────
        self.global_plan_points = []
        self.local_plan_points = []
        self.lidar_points_map = []
        self.goal_x = None
        self.goal_y = None

        # ── RViz Equivalent Layers: Costmaps & Particles ─────────────────────
        self.local_costmap_cells = []       # List of (map_x, map_y, cost)
        self.local_costmap_active = False
        self.local_costmap_last_time = 0.0
        self.global_costmap_raw = None

        self.particles = []                 # List of (px, py, pyaw)
        self.particle_spread = 0.0          # Standard deviation of particle cloud (meters)
        self.particle_count = 0

        # ── Layer Visibility Toggles ─────────────────────────────────────────
        self.show_local_costmap = True
        self.show_particles = True
        self.show_lidar = True
        self.show_axes = True
        self.show_paths = True
        self.show_trail = True

        # ── TF Buffer & Transform Listener ───────────────────────────────────
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

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
        # Compatible QoS for local costmap (handles both VOLATILE and TRANSIENT_LOCAL publishers)
        costmap_sub_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE
        )

        # ── Publishers for Navigation & Physical E-Stop ──────────────────────
        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, '/initialpose', 10)
        self.goal_pub = self.create_publisher(
            PoseStamped, '/goal_pose', 10)
        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10)
        self.patrol_cmd_pub = self.create_publisher(
            String, '/patrol_cmd', 10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(OccupancyGrid, '/map', self._map_cb, map_qos)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap', self._global_costmap_cb, map_qos)
        self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self._local_costmap_cb, costmap_sub_qos)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self._amcl_cb, 10)
        self.create_subscription(PoseArray, '/particlecloud', self._particle_cb, 10)
        self.create_subscription(Path, '/plan', self._plan_cb, 10)
        self.create_subscription(Path, '/local_plan', self._local_plan_cb, 10)
        self.create_subscription(LaserScan, '/scan_downsampled', self._scan_cb, sensor_qos)
        self.create_subscription(LaserScan, '/scan', self._scan_cb, sensor_qos)
        self.create_subscription(PoseStamped, '/goal_pose', self._goal_cb, 10)
        self.create_subscription(UInt16, '/battery', self._battery_cb, 10)

        # ── Live Camera Feed Subscription ────────────────────────────────────
        self.latest_camera_jpeg = None
        self.create_subscription(CompressedImage, '/camera/image_raw/compressed', self._camera_cb, 10)

        # Periodic TF polling timer (10 Hz)
        self.create_timer(0.1, self._poll_tf_pose)

        # ── Pre-rendered Frame Cache & Render Thread ─────────────────────────
        self._cached_jpeg = None
        self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._render_thread.start()

        self.get_logger().info('RViz-Equivalent Web Map Visualizer initialized.')

    # ── ROS Callbacks ────────────────────────────────────────────────────────

    def _camera_cb(self, msg: CompressedImage):
        with self.lock:
            self.latest_camera_jpeg = bytes(msg.data)

    def _map_cb(self, msg: OccupancyGrid):
        with self.lock:
            self.map_width = msg.info.width
            self.map_height = msg.info.height
            self.map_res = msg.info.resolution
            self.map_origin_x = msg.info.origin.position.x
            self.map_origin_y = msg.info.origin.position.y

            data = np.array(msg.data, dtype=np.int8).reshape((self.map_height, self.map_width))
            img = np.full((self.map_height, self.map_width, 3), 210, dtype=np.uint8)  # Unknown grey
            img[data == 0] = [252, 252, 252]                                           # Free white
            img[data > 50] = [35, 35, 35]                                              # Occupied dark charcoal

            # ROS maps have (0,0) at bottom-left; flip vertically for pixel image convention
            self.map_img = cv2.flip(img, 0)
            self.get_logger().info(f'Loaded base map: {self.map_width}x{self.map_height} @ {self.map_res}m/px')

    def _global_costmap_cb(self, msg: OccupancyGrid):
        with self.lock:
            raw = np.array(msg.data, dtype=np.int8).reshape((msg.info.height, msg.info.width))
            self.global_costmap_raw = cv2.flip(raw, 0)

    def _local_costmap_cb(self, msg: OccupancyGrid):
        """Ingests 10 Hz dynamic local rolling costmap and transforms active obstacle/inflation cells."""
        w = msg.info.width
        h = msg.info.height
        res = msg.info.resolution
        ox = msg.info.origin.position.x
        oy = msg.info.origin.position.y
        frame_id = msg.header.frame_id

        # Determine transform from local costmap frame (e.g. odom_frame) to map frame
        tx, ty, tf_yaw = 0.0, 0.0, 0.0
        if frame_id != 'map':
            try:
                t = self.tf_buffer.lookup_transform('map', frame_id, rclpy.time.Time())
                tx = t.transform.translation.x
                ty = t.transform.translation.y
                qz = t.transform.rotation.z
                qw = t.transform.rotation.w
                tf_yaw = 2.0 * math.atan2(qz, qw)
            except TransformException:
                with self.lock:
                    tx, ty, tf_yaw = self.robot_x, self.robot_y, self.robot_yaw

        cos_t = math.cos(tf_yaw)
        sin_t = math.sin(tf_yaw)

        data = np.array(msg.data, dtype=np.int8)
        active_indices = np.where(data > 0)[0]

        cells = []
        step = max(1, len(active_indices) // 1000)
        for idx in active_indices[::step]:
            cost = int(data[idx])
            col = idx % w
            row = idx // w
            # Local coordinates in local costmap frame
            lx = ox + (col + 0.5) * res
            ly = oy + (row + 0.5) * res
            # Transform to map world coordinates
            mx = tx + (lx * cos_t - ly * sin_t)
            my = ty + (lx * sin_t + ly * cos_t)
            cells.append((mx, my, cost))

        with self.lock:
            self.local_costmap_cells = cells
            self.local_costmap_active = True
            self.local_costmap_last_time = time.monotonic()

    def _particle_cb(self, msg: PoseArray):
        """Ingests AMCL localization particle swarm to render convergence state."""
        pts = []
        xs, ys = [], []
        # Downsample to at most 180 particles for crisp real-time rendering
        step = max(1, len(msg.poses) // 180)
        for p in msg.poses[::step]:
            px = p.position.x
            py = p.position.y
            qz = p.orientation.z
            qw = p.orientation.w
            yaw = 2.0 * math.atan2(qz, qw)
            pts.append((px, py, yaw))
            xs.append(px)
            ys.append(py)

        with self.lock:
            self.particles = pts
            self.particle_count = len(msg.poses)
            if len(xs) > 1:
                self.particle_spread = float(math.sqrt(np.var(xs) + np.var(ys)))
            else:
                self.particle_spread = 0.0

    def _update_pose(self, x: float, y: float, yaw: float):
        self.robot_x = x
        self.robot_y = y
        self.robot_yaw = yaw
        self.robot_localized = True
        self.last_pose_time = time.monotonic()

        # Append to trajectory trail if moved > 2 cm
        if not self.trajectory_history:
            self.trajectory_history.append((x, y))
        else:
            lx, ly = self.trajectory_history[-1]
            if math.hypot(x - lx, y - ly) >= 0.02:
                self.trajectory_history.append((x, y))
                if len(self.trajectory_history) > 3000:
                    self.trajectory_history.pop(0)

    def _poll_tf_pose(self):
        """Polls latest map -> base_footprint transform."""
        try:
            now = rclpy.time.Time()
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', now)
            with self.lock:
                qz = t.transform.rotation.z
                qw = t.transform.rotation.w
                yaw = 2.0 * math.atan2(qz, qw)
                self._update_pose(t.transform.translation.x, t.transform.translation.y, yaw)
        except TransformException:
            pass

    def _amcl_cb(self, msg: PoseWithCovarianceStamped):
        with self.lock:
            qz = msg.pose.pose.orientation.z
            qw = msg.pose.pose.orientation.w
            yaw = 2.0 * math.atan2(qz, qw)
            self._update_pose(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def _plan_cb(self, msg: Path):
        pts = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        with self.lock:
            self.global_plan_points = pts

    def _local_plan_cb(self, msg: Path):
        pts = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        with self.lock:
            self.local_plan_points = pts

    def _goal_cb(self, msg: PoseStamped):
        with self.lock:
            self.goal_x = msg.pose.position.x
            self.goal_y = msg.pose.position.y

    def _battery_cb(self, msg: UInt16):
        with self.lock:
            val = float(msg.data)
            if val > 50.0:  # Yahboom reports voltage * 10 (e.g. 79 = 7.9V)
                self.battery_voltage = val / 10.0
                pct = int(max(0, min(100, (self.battery_voltage - 6.8) / (8.4 - 6.8) * 100)))
                self.battery_pct = pct
            else:  # Direct percentage
                self.battery_pct = int(val)
                self.battery_voltage = 6.8 + (val / 100.0) * 1.6
            self.battery_healthy = (self.battery_voltage >= 7.0)
            self.battery_last_time = time.monotonic()

    def dispatch_patrol_cmd(self, cmd: str):
        """Dispatches patrol mode command to navigation stack."""
        msg = String()
        msg.data = str(cmd)
        self.patrol_cmd_pub.publish(msg)
        self.get_logger().info(f'Patrol command sent: {cmd}')

    def emergency_stop(self):
        """Immediately halts robot kinematics via zero velocity clamp."""
        self.dispatch_patrol_cmd('stop')
        with self.lock:
            self.goal_x = None
            self.goal_y = None
            self.global_plan_points = []
            self.local_plan_points = []
        zero_twist = Twist()
        for _ in range(5):
            self.cmd_vel_pub.publish(zero_twist)
            time.sleep(0.01)
        self.get_logger().warn('EMERGENCY STOP: Zero velocity published to /cmd_vel.')

    def dispatch_waypoint(self, x: float, y: float, yaw: float = 0.0):
        """Dispatches a 2D navigation goal to Nav2 on /goal_pose."""
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.position.z = 0.0
        msg.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.orientation.w = math.cos(yaw / 2.0)
        self.goal_pub.publish(msg)
        with self.lock:
            self.goal_x = float(x)
            self.goal_y = float(y)
        self.get_logger().info(f'Dispatched Nav2 Goal: ({x:.2f}m, {y:.2f}m, yaw={math.degrees(yaw):.1f}°)')

    def _scan_cb(self, msg: LaserScan):
        """Projects 2D LiDAR ranges into world map coordinates with TF sensor calibration."""
        laser_x, laser_y, laser_yaw = None, None, None

        # Look up laser_frame in map frame to automatically account for mounting position & yaw
        try:
            t = self.tf_buffer.lookup_transform('map', msg.header.frame_id, rclpy.time.Time())
            laser_x = t.transform.translation.x
            laser_y = t.transform.translation.y
            qz = t.transform.rotation.z
            qw = t.transform.rotation.w
            laser_yaw = 2.0 * math.atan2(qz, qw)
        except TransformException:
            # Fallback to robot base pose if transform is not yet available
            if self.robot_localized:
                with self.lock:
                    laser_x, laser_y, laser_yaw = self.robot_x, self.robot_y, self.robot_yaw

        if laser_x is None:
            return

        pts = []
        angle = msg.angle_min
        r_min, r_max = msg.range_min, msg.range_max
        for r in msg.ranges:
            if r_min < r < r_max and not math.isinf(r) and not math.isnan(r):
                total_angle = laser_yaw + angle
                ox = laser_x + r * math.cos(total_angle)
                oy = laser_y + r * math.sin(total_angle)
                pts.append((ox, oy))
            angle += msg.angle_increment

        with self.lock:
            self.lidar_points_map = pts

    # ── Rendering Pipeline (RViz Equivalents) ────────────────────────────────

    def render_map_jpeg(self) -> bytes:
        buf = self._cached_jpeg
        if buf is not None:
            return buf
        return self._render_canvas_jpeg()

    def _render_loop(self):
        while rclpy.ok():
            try:
                buf = self._render_canvas_jpeg()
                if buf:
                    with self.lock:
                        self._cached_jpeg = buf
            except Exception as e:
                pass
            time.sleep(0.08)  # ~12.5 Hz rendering loop

    def _render_canvas_jpeg(self) -> bytes:
        """Renders the composite top-down visualizer image and returns JPEG bytes."""
        with self.lock:
            if self.map_img is None:
                blank = np.full((400, 600, 3), 25, dtype=np.uint8)
                cv2.putText(blank, "Waiting for /map topic from Nav2...", (70, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2)
                _, buf = cv2.imencode('.jpg', blank)
                return buf.tobytes()

            canvas = self.map_img.copy()
            costmap_copy = self.global_costmap_raw.copy() if self.global_costmap_raw is not None else None
            rx, ry, ryaw = self.robot_x, self.robot_y, self.robot_yaw
            loc = self.robot_localized
            plan_pts = list(self.global_plan_points)
            local_pts = list(self.local_plan_points)
            lidar_pts = list(self.lidar_points_map)
            trail_pts = list(self.trajectory_history)
            gx, gy = self.goal_x, self.goal_y
            map_w, map_h, map_res = self.map_width, self.map_height, self.map_res

            local_cost_cells = list(self.local_costmap_cells)
            particles_list = list(self.particles)
            p_spread = self.particle_spread
            p_count = self.particle_count

            show_lc = self.show_local_costmap
            show_part = self.show_particles
            show_lid = self.show_lidar
            show_ax = self.show_axes
            show_p = self.show_paths
            show_tr = self.show_trail

        # ── 1. Global Costmap Background Tint ────────────────────────────────
        if costmap_copy is not None and costmap_copy.shape == canvas.shape[:2]:
            inf_mask = (costmap_copy > 0) & (costmap_copy < 100)
            if np.any(inf_mask):
                canvas[inf_mask] = (canvas[inf_mask].astype(np.float32) * 0.75 +
                                    np.array([210, 160, 240], dtype=np.float32) * 0.25).astype(np.uint8)

        # Scale up canvas for high-resolution visualizer display
        scale = 3.5
        resized = cv2.resize(canvas, (int(map_w * scale), int(map_h * scale)),
                             interpolation=cv2.INTER_NEAREST)

        def w2p_s(wx: float, wy: float):
            px = (wx - self.map_origin_x) / self.map_res
            py = (self.map_height - 1) - (wy - self.map_origin_y) / self.map_res
            return int(round(px * scale)), int(round(py * scale))

        # ── 2. Local Dynamic Rolling Costmap (RViz Shading) ──────────────────
        if show_lc and local_cost_cells:
            cell_px = max(2, int(round((0.05 / map_res) * scale)))
            half_c = cell_px // 2

            # Create an overlay canvas for alpha blending the costmap
            cost_overlay = resized.copy()
            for (cx, cy, cost) in local_cost_cells:
                u, v = w2p_s(cx, cy)
                if 0 <= u < resized.shape[1] and 0 <= v < resized.shape[0]:
                    if cost >= 99:
                        # Lethal obstacle: Vivid magenta / crimson
                        col = (220, 20, 230)
                    else:
                        # Inflation gradient: Cyan to purple
                        ratio = cost / 100.0
                        col = (
                            int(240 * (1.0 - ratio) + 180 * ratio),
                            int(180 * (1.0 - ratio) + 50 * ratio),
                            int(50 * (1.0 - ratio) + 220 * ratio)
                        )
                    cv2.rectangle(cost_overlay, (u - half_c, v - half_c), (u + half_c, v + half_c), col, -1)

            cv2.addWeighted(cost_overlay, 0.45, resized, 0.55, 0, resized)

        # ── 3. Subtle Strategic Waypoint Pins ─────────────────────────────────
        def draw_wp_ring(img_out, wx, wy, label, col):
            rpx, rpy = w2p_s(wx, wy)
            if 0 <= rpx < img_out.shape[1] and 0 <= rpy < img_out.shape[0]:
                cv2.circle(img_out, (rpx, rpy), 8, col, 2, cv2.LINE_AA)
                cv2.circle(img_out, (rpx, rpy), 2, col, -1)
                # Dual-pass outline: black border then bright core for crisp readability on any background
                cv2.putText(img_out, label, (rpx + 10, rpy + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(img_out, label, (rpx + 10, rpy + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw subtle L-form mission corridor guideline (P1 -> P2 -> P3 -> P4)
        if show_p and len(self.corridor_landmarks) >= 4:
            l_coords = [w2p_s(item[0], item[1]) for item in self.corridor_landmarks]
            for p_idx in range(len(l_coords) - 1):
                pt_a = l_coords[p_idx]
                pt_b = l_coords[p_idx + 1]
                cv2.line(resized, pt_a, pt_b, (210, 180, 240), 1, cv2.LINE_AA)

        pin_colors = [
            (0, 220, 100),   # P1 Home Base (Vibrant Green)
            (255, 190, 40),  # P2 Central Hub (Cyan/Sky)
            (220, 100, 240), # P3 North Gallery (Magenta)
            (40, 180, 255),  # P4 East Lab (Warm Amber)
        ]
        for i, item in enumerate(self.corridor_landmarks):
            wx, wy, name = item
            lbl = name.split()[0]  # P1, P2, P3, P4
            col = pin_colors[i % len(pin_colors)]
            draw_wp_ring(resized, wx, wy, lbl, col)

        # ── 4. Traveled Odometry Trail (Warm Amber/Gold Breadcrumbs) ─────────
        if show_tr and len(trail_pts) > 1:
            scaled_trail = [w2p_s(tx, ty) for (tx, ty) in trail_pts]
            pts_arr = np.array([scaled_trail], dtype=np.int32)
            cv2.polylines(resized, pts_arr, False, (45, 195, 255), 2, cv2.LINE_AA)

        # ── 5. Nav2 Global Planned Path (Luminous Green Ribbon) ───────────────
        if show_p and len(plan_pts) > 1:
            scaled_plan = [w2p_s(x, y) for (x, y) in plan_pts]
            pts_arr = np.array([scaled_plan], dtype=np.int32)
            cv2.polylines(resized, pts_arr, False, (10, 160, 30), 6, cv2.LINE_AA)   # Soft outer glow
            cv2.polylines(resized, pts_arr, False, (50, 255, 80), 2, cv2.LINE_AA)   # High-contrast core

        # ── 6. Local Controller Trajectory (Vivid Cyan Arc) ───────────────────
        if show_p and len(local_pts) > 1:
            scaled_local = [w2p_s(x, y) for (x, y) in local_pts]
            pts_arr = np.array([scaled_local], dtype=np.int32)
            cv2.polylines(resized, pts_arr, False, (255, 235, 0), 2, cv2.LINE_AA)

        # ── 7. AMCL Particle Cloud Swarm (RViz Green Needles) ────────────────
        if show_part and particles_list:
            head_len = 7
            for (px, py, pyaw) in particles_list:
                pu, pv = w2p_s(px, py)
                if 0 <= pu < resized.shape[1] and 0 <= pv < resized.shape[0]:
                    tip_x = pu + int(round(head_len * math.cos(pyaw)))
                    tip_y = pv - int(round(head_len * math.sin(pyaw)))
                    cv2.line(resized, (pu, pv), (tip_x, tip_y), (45, 245, 110), 1, cv2.LINE_AA)
                    cv2.circle(resized, (pu, pv), 1, (100, 255, 150), -1)

        # ── 8. Calibrated 2D LiDAR Points (Vivid Neon Coral Reflections) ─────
        if show_lid and lidar_pts:
            for (ox, oy) in lidar_pts:
                u, v = w2p_s(ox, oy)
                if 0 <= u < resized.shape[1] and 0 <= v < resized.shape[0]:
                    cv2.circle(resized, (u, v), 2, (30, 45, 255), -1)

        # ── 9. Active Target Waypoint Reticle (Bright Gold Bullseye) ─────────
        if gx is not None and gy is not None:
            gu, gv = w2p_s(gx, gy)
            cv2.circle(resized, (gu, gv), 12, (0, 215, 255), 2, cv2.LINE_AA)
            cv2.circle(resized, (gu, gv), 4, (0, 215, 255), -1)
            cv2.drawMarker(resized, (gu, gv), (0, 215, 255), cv2.MARKER_CROSS, 18, 1)

        # ── 10. Realistic AMR Chassis Footprint & REP-103 TF Coordinate Axes ──
        if loc:
            ru_s, rv_s = w2p_s(rx, ry)
            hl = (0.24 / map_res) * scale / 2.0  # half length ~ 8.4 px
            hw = (0.18 / map_res) * scale / 2.0  # half width ~ 6.3 px
            cos_a = math.cos(ryaw)
            sin_a = math.sin(ryaw)

            # Chassis polygon rotated by robot yaw
            corners = [
                (hl, -hw),
                (hl, hw),
                (-hl, hw),
                (-hl, -hw)
            ]
            poly_pts = []
            for dx, dy in corners:
                px = ru_s + int(round(dx * cos_a - dy * sin_a))
                py = rv_s - int(round(dx * sin_a + dy * cos_a))
                poly_pts.append([px, py])

            poly_arr = np.array([poly_pts], dtype=np.int32)
            cv2.fillPoly(resized, poly_arr, (230, 115, 20))                          # Electric blue body
            cv2.polylines(resized, poly_arr, True, (255, 255, 255), 2, cv2.LINE_AA)  # Crisp white border

            # Drive Wheels (Black pads)
            for dx, dy in [(hl * 0.7, -hw - 1), (hl * 0.7, hw + 1), (-hl * 0.7, -hw - 1), (-hl * 0.7, hw + 1)]:
                wx = ru_s + int(round(dx * cos_a - dy * sin_a))
                wy = rv_s - int(round(dx * sin_a + dy * cos_a))
                cv2.circle(resized, (wx, wy), 2, (20, 20, 20), -1)

            # Central LiDAR Turret cylinder
            cv2.circle(resized, (ru_s, rv_s), 4, (45, 45, 45), -1)
            cv2.circle(resized, (ru_s, rv_s), 2, (0, 0, 255), -1)

            # Standard ROS REP-103 Coordinate Frame Axes (Red = +X, Green = +Y)
            if show_ax:
                ax_len_x = (0.35 / map_res) * scale
                ax_len_y = (0.25 / map_res) * scale
                # Red arrow (+X Forward)
                ax_x = ru_s + int(round(ax_len_x * cos_a))
                ax_y = rv_s - int(round(ax_len_x * sin_a))
                cv2.arrowedLine(resized, (ru_s, rv_s), (ax_x, ax_y), (0, 0, 255), 2, tipLength=0.22)
                # Green arrow (+Y Left)
                ay_x = ru_s + int(round(ax_len_y * (-sin_a)))
                ay_y = rv_s - int(round(ax_len_y * cos_a))
                cv2.arrowedLine(resized, (ru_s, rv_s), (ay_x, ay_y), (0, 255, 0), 2, tipLength=0.25)
            else:
                # Forward heading laser projection beam
                head_len = (0.45 / map_res) * scale
                hpx = ru_s + int(round(head_len * cos_a))
                hpy = rv_s - int(round(head_len * sin_a))
                cv2.arrowedLine(resized, (ru_s, rv_s), (hpx, hpy), (0, 240, 255), 2, tipLength=0.25)

        # ── 11. Pure Canvas Output (No burned-in HUD clutter) ─────────────────
        _, buf = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return buf.tobytes()

    def get_telemetry_dict(self):
        with self.lock:
            bat_fresh = (time.monotonic() - self.battery_last_time < 5.0) if self.battery_last_time > 0 else False
            return {
                "x": round(self.robot_x, 3),
                "y": round(self.robot_y, 3),
                "yaw": round(math.degrees(self.robot_yaw), 1),
                "localized": self.robot_localized,
                "plan_points": len(self.global_plan_points),
                "lidar_points": len(self.lidar_points_map),
                "particle_count": self.particle_count,
                "particle_spread": round(self.particle_spread, 3),
                "local_costmap_active": (time.monotonic() - self.local_costmap_last_time < 3.0),
                "goal": [round(self.goal_x, 2), round(self.goal_y, 2)] if self.goal_x is not None else None,
                "battery_voltage": round(self.battery_voltage, 1),
                "battery_pct": self.battery_pct,
                "battery_healthy": self.battery_healthy,
                "battery_fresh": bat_fresh,
                "toggles": {
                    "costmap": self.show_local_costmap,
                    "particles": self.show_particles,
                    "lidar": self.show_lidar,
                    "axes": self.show_axes,
                    "paths": self.show_paths,
                    "trail": self.show_trail
                },
                "map_info": {
                    "width": self.map_width,
                    "height": self.map_height,
                    "res": self.map_res,
                    "origin_x": self.map_origin_x,
                    "origin_y": self.map_origin_y
                }
            }


# ── HTTP SERVER & INTERACTIVE FRONTEND ───────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AMR Cognition — Autonomous Navigation Console</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #090d13;
      --card-bg: #121822;
      --card-bg-hover: #16202c;
      --border: #222c3c;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --accent: #58a6ff;
      --green: #2ea043;
      --green-glow: rgba(46, 160, 67, 0.25);
      --red: #f85149;
      --red-glow: rgba(248, 81, 73, 0.35);
      --gold: #d29922;
      --gold-glow: rgba(210, 153, 34, 0.25);
      --purple: #a371f7;
      --cyan: #39c5bb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 16px 24px;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 14px;
      gap: 16px;
      flex-wrap: wrap;
    }
    .brand h1 {
      margin: 0;
      font-size: 1.3rem;
      color: var(--text-bright);
      font-weight: 600;
      letter-spacing: -0.2px;
    }
    .sub-title {
      font-size: 0.85rem;
      color: var(--accent);
      font-weight: 500;
    }
    .sys-sub {
      color: #8b949e;
      font-size: 0.75rem;
      margin-top: 3px;
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .battery-widget {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #161f2b;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 6px 12px;
      font-size: 0.82rem;
    }
    .bat-bar-wrap {
      width: 44px;
      height: 10px;
      background: #090d13;
      border: 1px solid #303e52;
      border-radius: 3px;
      position: relative;
      overflow: hidden;
    }
    .bat-bar-fill {
      height: 100%;
      background: var(--green);
      transition: width 0.3s, background 0.3s;
    }
    .badge {
      padding: 5px 10px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: bold;
      letter-spacing: 0.5px;
    }
    .badge-live {
      background: rgba(46, 160, 67, 0.2);
      border: 1px solid var(--green);
      color: #3fb950;
    }
    .badge-healthy {
      background: rgba(46, 160, 67, 0.2);
      color: #3fb950;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: bold;
      font-size: 0.72rem;
    }
    .badge-warning {
      background: rgba(248, 81, 73, 0.2);
      color: #f85149;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: bold;
      font-size: 0.72rem;
      animation: pulse 1s infinite;
    }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.5; }
      100% { opacity: 1; }
    }
    .btn-estop {
      background: #da3633;
      border: 1px solid #f85149;
      color: #fff;
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.4px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 0 12px var(--red-glow);
      transition: all 0.2s;
    }
    .btn-estop:hover {
      background: #b62324;
      box-shadow: 0 0 18px rgba(248, 81, 73, 0.6);
      transform: scale(1.02);
    }
    .btn-estop:active {
      transform: scale(0.98);
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 14px;
    }
    .tool-btn {
      background: #182230;
      border: 1px solid var(--border);
      color: var(--text-bright);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.78rem;
      cursor: pointer;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .tool-btn:hover { background: #223044; border-color: var(--accent); }
    .tool-btn.active {
      background: #1f4277;
      border-color: var(--accent);
      color: #fff;
      box-shadow: 0 0 8px rgba(88,166,255,0.4);
    }
    .tool-separator {
      width: 1px;
      height: 20px;
      background: var(--border);
      margin: 0 4px;
    }
    .container {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 16px;
    }
    @media (max-width: 960px) {
      .container { grid-template-columns: 1fr; }
    }
    .map-container {
      position: relative;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.5);
      text-align: center;
      user-select: none;
    }
    .canvas-wrapper {
      position: relative;
      display: inline-block;
      max-width: 100%;
      border-radius: 6px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: #000;
    }
    #map-img {
      display: block;
      max-width: 100%;
      height: auto;
    }
    #overlay-canvas {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      cursor: crosshair;
    }
    .panel {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
    }
    .card h2 {
      margin-top: 0;
      font-size: 0.9rem;
      color: var(--accent);
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .btn-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .action-btn {
      background: #182230;
      border: 1px solid var(--border);
      color: var(--text-bright);
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 0.78rem;
      cursor: pointer;
      font-weight: 500;
      text-align: left;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .action-btn:hover {
      background: #233144;
      border-color: var(--accent);
      color: #fff;
    }
    .action-btn.full-width {
      grid-column: 1 / -1;
      justify-content: center;
      font-weight: 600;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      margin: 8px 0;
      font-size: 0.82rem;
    }
    .metric-label { color: #8b949e; }
    .metric-value { font-family: monospace; font-weight: bold; color: var(--text-bright); }
    .legend-details summary {
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--accent);
      outline: none;
      user-select: none;
    }
    .legend-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 10px;
      font-size: 0.78rem;
    }
    .legend-item { display: flex; align-items: center; gap: 8px; }
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 18px;
      background: #1c2430;
      color: #fff;
      border: 1px solid var(--accent);
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.6);
      font-size: 0.85rem;
      display: none;
      z-index: 1000;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="brand">
      <h1>AMR COGNITION <span class="sub-title">• Yahboom Micro-ROS Console</span></h1>
      <div class="sys-sub">Raspberry Pi 5 + ESP32-S3 Platform | Layered Costmaps & TF Telemetry</div>
    </div>
    <div class="header-right">
      <div class="battery-widget">
        <span>🔋</span>
        <span class="metric-value" id="bat-val">7.8V</span>
        <div class="bat-bar-wrap">
          <div class="bat-bar-fill" id="bat-fill" style="width: 75%;"></div>
        </div>
        <span id="bat-status" class="badge-healthy">HEALTHY</span>
      </div>
      <span class="badge badge-live" id="conn-badge">LIVE DDS</span>
      <button class="btn-estop" onclick="triggerEStop()" title="Emergency Stop (Spacebar / Esc)">🛑 E-STOP</button>
    </div>
  </div>

  <div class="toolbar">
    <button class="tool-btn active" id="btn-mode-view" onclick="setMode('view')">👁 View</button>
    <button class="tool-btn" id="btn-mode-pose" onclick="setMode('pose')">📍 2D Pose</button>
    <button class="tool-btn" id="btn-mode-goal" onclick="setMode('goal')">🎯 2D Goal</button>
    <div class="tool-separator"></div>
    <button class="tool-btn active" id="tgl-costmap" onclick="toggleLayer('costmap')">Local Costmap</button>
    <button class="tool-btn active" id="tgl-particles" onclick="toggleLayer('particles')">AMCL Particles</button>
    <button class="tool-btn active" id="tgl-lidar" onclick="toggleLayer('lidar')">LiDAR Scans</button>
    <button class="tool-btn active" id="tgl-axes" onclick="toggleLayer('axes')">TF Axes</button>
    <button class="tool-btn active" id="tgl-paths" onclick="toggleLayer('paths')">Nav2 Paths</button>
    <button class="tool-btn active" id="tgl-trail" onclick="toggleLayer('trail')">Trail</button>
    <div class="tool-separator"></div>
    <button class="tool-btn" style="color:var(--gold)" onclick="clearTrail()">🧹 Clear Trail</button>
    <button class="tool-btn" style="color:var(--green)" onclick="dispatchWaypoint('P1 Home Base', 0.08, 0.05, 0.0)">🏠 Dock Home</button>
    <button class="tool-btn" style="color:var(--accent)" onclick="resetHome()">📍 Reset Pose</button>
  </div>

  <div class="container">
    <div class="map-container">
      <div class="canvas-wrapper" id="canvas-wrap">
        <img id="map-img" src="/map.jpg" alt="Nav2 Live Occupancy Grid Map" />
        <canvas id="overlay-canvas"></canvas>
      </div>
      <div id="instruction-hint" style="margin-top: 8px; font-size: 0.78rem; color: #8b949e;">
        Mode: <b>View</b>. Switch to <i>2D Goal</i> or <i>2D Pose</i> to click & drag heading directly on map.
      </div>
    </div>

    <div class="panel">
      <div class="card">
        <h2>Strategic Waypoint Dispatch (4-Point Facility Coverage)</h2>
        <div class="btn-grid">
          <button class="action-btn" onclick="dispatchWaypoint('P1 Home Base', 0.08, 0.05, 0.0)">
            <span style="color:var(--green)">🏠</span> P1 Home (0.08, 0.05)
          </button>
          <button class="action-btn" onclick="dispatchWaypoint('P2 Central Hub', 1.64, 1.62, 0.78)">
            <span style="color:var(--cyan)">2️⃣</span> P2 Center (1.64, 1.62)
          </button>
          <button class="action-btn" onclick="dispatchWaypoint('P3 North Gallery', 3.20, 3.20, 0.78)">
            <span style="color:var(--purple)">3️⃣</span> P3 North (3.20, 3.20)
          </button>
          <button class="action-btn" onclick="dispatchWaypoint('P4 East Lab', 4.70, 1.80, -0.75)">
            <span style="color:var(--gold)">4️⃣</span> P4 East (4.70, 1.80)
          </button>
          <button class="action-btn full-width" style="color:var(--accent)" onclick="startSmartPatrol('unattended')">
            🔄 Run 4-Point Unattended Mission (Starts at Nearest Post)
          </button>
          <button class="action-btn full-width" style="color:var(--gold)" onclick="resetHome()">
            📍 Reset Pose to Home Base (Unwedge)
          </button>
          <button class="action-btn full-width" style="color:var(--red)" onclick="cancelGoal()">
            ⏹ Cancel Active Nav2 Goal
          </button>
        </div>
      <div class="card">
        <h2>Live Onboard Camera Stream</h2>
        <div style="position:relative; width:100%; height:180px; background:#0b0f15; border-radius:6px; overflow:hidden; border:1px solid var(--border);">
          <img id="cam-img" src="/camera.jpg" style="width:100%; height:100%; object-fit:contain;" onerror="document.getElementById('cam-status').style.display='flex';" onload="document.getElementById('cam-status').style.display='none';" />
          <div id="cam-status" style="display:none; position:absolute; inset:0; align-items:center; justify-content:center; color:#8b949e; font-size:0.75rem; text-align:center;">
            Camera Stream Standby...<br><span style="color:var(--accent); font-size:0.70rem;">/camera/image_raw/compressed</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Robot Telemetry & Diagnostics</h2>
        <div class="metric-row">
          <span class="metric-label">Position X / Y:</span>
          <span class="metric-value"><span id="val-x">0.00</span>m, <span id="val-y">0.00</span>m</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Heading Yaw:</span>
          <span class="metric-value" id="val-yaw">0.0°</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">AMCL Alignment:</span>
          <span class="metric-value" id="val-loc" style="color: var(--green);">LOCALIZED</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Particle Spread (StdDev):</span>
          <span class="metric-value" id="val-spread">±0.00 m</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Particles Count:</span>
          <span class="metric-value" id="val-particles">0</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Local Costmap:</span>
          <span class="metric-value" id="val-costmap" style="color: var(--green);">ACTIVE (10 Hz)</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">LiDAR Scan Hits:</span>
          <span class="metric-value" id="val-lidar">0 pts</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Motor Cutoff Threshold:</span>
          <span class="metric-value" style="color: #8b949e;">6.8V Protection</span>
        </div>
      </div>

      <div class="card">
        <details class="legend-details" open>
          <summary>Layer Visual Legend</summary>
          <div class="legend-list">
            <div class="legend-item"><span class="dot" style="background: #a371f7;"></span> <b>Local Costmap:</b> 3m dynamic obstacle window</div>
            <div class="legend-item"><span class="dot" style="background: #2ea043;"></span> <b>AMCL Cloud:</b> Convergence orientation arrows</div>
            <div class="legend-item"><span class="dot" style="background: #f85149;"></span> <b>LiDAR Scans:</b> Calibrated obstacle hits</div>
            <div class="legend-item"><span class="dot" style="background: #32d74b;"></span> <b>Global Plan:</b> Nav2 route (Green ribbon)</div>
            <div class="legend-item"><span class="dot" style="background: #00d4ff;"></span> <b>Local Trajectory:</b> Controller carrot (Cyan)</div>
            <div class="legend-item"><span class="dot" style="background: #e3b341;"></span> <b>Traveled Trail:</b> Odom history (Gold)</div>
            <div class="legend-item"><span class="dot" style="background: #1f6feb;"></span> <b>AMR Body:</b> Blue chassis footprint</div>
            <div class="legend-item"><span class="dot" style="background: #d29922;"></span> <b>TF Axes:</b> Red +X Forward, Green +Y Left</div>
          </div>
        </details>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    let currentMode = 'view';
    let mapInfo = null;
    let dragStart = null;
    let dragEnd = null;
    let isDragging = false;

    const imgElem = document.getElementById('map-img');
    const overlay = document.getElementById('overlay-canvas');
    const ctx = overlay.getContext('2d');
    const hintElem = document.getElementById('instruction-hint');

    // Chained image preloading to prevent frame dropping
    function streamMap() {
      const nextImg = new Image();
      nextImg.onload = function() {
        imgElem.src = nextImg.src;
        syncCanvasDimensions();
        setTimeout(streamMap, 100); // 10 FPS stream
      };
      nextImg.onerror = function() {
        setTimeout(streamMap, 500);
      };
      nextImg.src = '/map.jpg?t=' + Date.now();
    }
    streamMap();

    const camElem = document.getElementById('cam-img');
    function streamCam() {
      const nextCam = new Image();
      nextCam.onload = function() {
        camElem.src = nextCam.src;
        document.getElementById('cam-status').style.display = 'none';
        setTimeout(streamCam, 100); // 10 FPS live camera feed
      };
      nextCam.onerror = function() {
        document.getElementById('cam-status').style.display = 'flex';
        setTimeout(streamCam, 1000);
      };
      nextCam.src = '/camera.jpg?t=' + Date.now();
    }
    streamCam();

    function syncCanvasDimensions() {
      if (overlay.width !== imgElem.clientWidth || overlay.height !== imgElem.clientHeight) {
        overlay.width = imgElem.clientWidth;
        overlay.height = imgElem.clientHeight;
      }
    }
    window.addEventListener('resize', syncCanvasDimensions);

    function showToast(msg, isAlert = false) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.borderColor = isAlert ? 'var(--red)' : 'var(--accent)';
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 3500);
    }

    function triggerEStop() {
      fetch('/api/estop', { method: 'POST' })
        .then(() => showToast('🛑 EMERGENCY STOP: Zero velocity sent to /cmd_vel!', true));
    }

    function cancelGoal() {
      fetch('/api/cancel', { method: 'POST' })
        .then(() => showToast('⏹ Active Nav2 Goal Cancelled.'));
    }

    function dispatchWaypoint(name, x, y, yaw) {
      fetch('/api/waypoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: x, y: y, yaw: yaw })
      })
      .then(() => showToast(`🎯 Nav2 Goal sent to ${name} (${x.toFixed(2)}m, ${y.toFixed(2)}m)`));
    }

    function runPatrolCircuit() {
      startSmartPatrol('unattended');
    }

    function startSmartPatrol(circuitType) {
      fetch('/api/patrol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: circuitType || 'unattended' })
      })
      .then(r => r.json())
      .then(data => {
        showToast(`🔄 Dynamic 4-Point Unattended mission active (Starting at ${data.start_wp})`);
      });
    }

    function resetHome() {
      fetch('/api/initialpose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: 0.08, y: 0.05, yaw: 0.0 })
      })
      .then(() => showToast('📍 AMR pose reset to Home Base (0.08m, 0.05m).'));
    }

    function setMode(mode) {
      currentMode = mode;
      document.getElementById('btn-mode-view').classList.toggle('active', mode === 'view');
      document.getElementById('btn-mode-pose').classList.toggle('active', mode === 'pose');
      document.getElementById('btn-mode-goal').classList.toggle('active', mode === 'goal');

      if (mode === 'view') {
        hintElem.innerHTML = 'Mode: <b>View</b>. Panning / monitoring mode active.';
        overlay.style.cursor = 'default';
      } else if (mode === 'pose') {
        hintElem.innerHTML = 'Mode: <b style="color:var(--gold)">2D Pose Estimate</b>. Click on map position & drag forward to set AMCL heading.';
        overlay.style.cursor = 'crosshair';
      } else if (mode === 'goal') {
        hintElem.innerHTML = 'Mode: <b style="color:var(--accent)">2D Nav Goal</b>. Click on target position & drag forward to dispatch Nav2 goal.';
        overlay.style.cursor = 'crosshair';
      }
    }

    function toggleLayer(layer) {
      const btn = document.getElementById('tgl-' + layer);
      const active = !btn.classList.contains('active');
      btn.classList.toggle('active', active);

      fetch('/api/toggles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layer: layer, value: active })
      });
    }

    function clearTrail() {
      fetch('/api/cleartrail', { method: 'POST' })
        .then(() => showToast('🧹 Traveled trajectory trail cleared.'));
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space' || e.key === 'Escape') {
        triggerEStop();
      } else if (e.key === 'h' || e.key === 'H') {
        dispatchWaypoint('P1 Home Base', 0.08, 0.05, 0.0);
      } else if (e.key === 'c' || e.key === 'C') {
        clearTrail();
      }
    });

    // Mouse Drag Handling for Initial Pose & Goal
    overlay.addEventListener('mousedown', (e) => {
      if (currentMode === 'view') return;
      const rect = overlay.getBoundingClientRect();
      dragStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      dragEnd = { ...dragStart };
      isDragging = true;
    });

    overlay.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const rect = overlay.getBoundingClientRect();
      dragEnd = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      drawDragArrow();
    });

    overlay.addEventListener('mouseup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      const rect = overlay.getBoundingClientRect();
      dragEnd = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      ctx.clearRect(0, 0, overlay.width, overlay.height);

      if (!mapInfo || mapInfo.width === 0) {
        showToast('Map information not yet received from robot.');
        return;
      }

      const imgW = imgElem.naturalWidth;
      const imgH = imgElem.naturalHeight;
      const scaleX = imgW / overlay.width;
      const scaleY = imgH / overlay.height;

      const px = dragStart.x * scaleX;
      const py = dragStart.y * scaleY;

      const renderScale = 3.5;
      const mapPx = px / renderScale;
      const mapPy = py / renderScale;

      const wx = mapInfo.origin_x + mapPx * mapInfo.res;
      const wy = mapInfo.origin_y + (mapInfo.height - 1 - mapPy) * mapInfo.res;

      const dx = (dragEnd.x - dragStart.x);
      const dy = -(dragEnd.y - dragStart.y);
      const yaw = Math.hypot(dx, dy) > 8 ? Math.atan2(dy, dx) : 0.0;

      if (currentMode === 'pose') {
        fetch('/api/initialpose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ x: wx, y: wy, yaw: yaw })
        })
        .then(r => r.json())
        .then(res => {
          showToast(`📍 2D Pose Estimate sent to AMCL: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m, ${(yaw * 180 / Math.PI).toFixed(0)}°)`);
          setMode('view');
        });
      } else if (currentMode === 'goal') {
        fetch('/api/goal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ x: wx, y: wy, yaw: yaw })
        })
        .then(r => r.json())
        .then(res => {
          showToast(`🎯 Nav2 Goal Dispatched: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m, ${(yaw * 180 / Math.PI).toFixed(0)}°)`);
          setMode('view');
        });
      }
    });

    function drawDragArrow() {
      ctx.clearRect(0, 0, overlay.width, overlay.height);
      ctx.beginPath();
      ctx.arc(dragStart.x, dragStart.y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = currentMode === 'pose' ? '#d29922' : '#58a6ff';
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(dragStart.x, dragStart.y);
      ctx.lineTo(dragEnd.x, dragEnd.y);
      ctx.strokeStyle = currentMode === 'pose' ? '#d29922' : '#58a6ff';
      ctx.lineWidth = 3;
      ctx.stroke();
    }

    // Real-Time Telemetry Polling
    function updateTelemetry() {
      fetch('/telemetry')
        .then(r => r.json())
        .then(data => {
          mapInfo = data.map_info;
          document.getElementById('val-x').textContent = data.x.toFixed(2);
          document.getElementById('val-y').textContent = data.y.toFixed(2);
          document.getElementById('val-yaw').textContent = data.yaw.toFixed(1) + '°';
          document.getElementById('val-lidar').textContent = data.lidar_points + ' pts';
          document.getElementById('val-particles').textContent = data.particle_count;

          const spreadElem = document.getElementById('val-spread');
          spreadElem.textContent = '±' + data.particle_spread.toFixed(2) + ' m';
          spreadElem.style.color = data.particle_spread < 0.15 ? 'var(--green)' : 'var(--gold)';

          const locElem = document.getElementById('val-loc');
          locElem.textContent = data.localized ? 'LOCALIZED' : 'UNALIGNED';
          locElem.style.color = data.localized ? 'var(--green)' : 'var(--gold)';

          const costElem = document.getElementById('val-costmap');
          costElem.textContent = data.local_costmap_active ? 'ACTIVE (10 Hz)' : 'OFFLINE';
          costElem.style.color = data.local_costmap_active ? 'var(--green)' : 'var(--red)';

          // Battery Telemetry
          const batVal = document.getElementById('bat-val');
          const batFill = document.getElementById('bat-fill');
          const batStatus = document.getElementById('bat-status');
          if (data.battery_voltage !== undefined) {
            batVal.textContent = data.battery_voltage.toFixed(1) + 'V';
            batFill.style.width = data.battery_pct + '%';
            if (data.battery_voltage < 7.0) {
              batStatus.className = 'badge-warning';
              batStatus.textContent = 'LOW (<7.0V)';
              batFill.style.background = 'var(--red)';
            } else if (data.battery_voltage < 7.4) {
              batStatus.className = 'badge-healthy';
              batStatus.style.color = 'var(--gold)';
              batStatus.textContent = 'MODERATE';
              batFill.style.background = 'var(--gold)';
            } else {
              batStatus.className = 'badge-healthy';
              batStatus.style.color = 'var(--green)';
              batStatus.textContent = 'HEALTHY';
              batFill.style.background = 'var(--green)';
            }
          }
        })
        .catch(() => {});
    }
    setInterval(updateTelemetry, 250);
  </script>
</body>
</html>
"""


class WebHandler(BaseHTTPRequestHandler):
    node_ref: MapVisualizerNode = None

    def do_HEAD(self):
        if self.path.startswith('/map.jpg'):
            jpeg_bytes = self.node_ref.render_map_jpeg()
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(jpeg_bytes)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
        elif self.path.startswith('/camera.jpg'):
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
        elif self.path == '/telemetry':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

    def do_GET(self):
        if self.path.startswith('/map.jpg'):
            jpeg_bytes = self.node_ref.render_map_jpeg()
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(jpeg_bytes)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(jpeg_bytes)

        elif self.path.startswith('/camera.jpg'):
            with self.node_ref.lock:
                jpeg_bytes = self.node_ref.latest_camera_jpeg
            if jpeg_bytes is not None:
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(jpeg_bytes)))
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self.end_headers()
                self.wfile.write(jpeg_bytes)
            else:
                self.send_response(404)
                self.end_headers()

        elif self.path == '/telemetry':
            data = self.node_ref.get_telemetry_dict()
            payload = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(payload)

        else:
            payload = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length)

        try:
            req_data = json.loads(post_body.decode('utf-8'))
        except Exception:
            req_data = {}

        if self.path == '/api/initialpose':
            # Reseed AMCL Monte Carlo Localization
            msg = PoseWithCovarianceStamped()
            msg.header.stamp = self.node_ref.get_clock().now().to_msg()
            msg.header.frame_id = 'map'
            msg.pose.pose.position.x = float(req_data.get('x', 0.0))
            msg.pose.pose.position.y = float(req_data.get('y', 0.0))
            msg.pose.pose.position.z = 0.0

            yaw = float(req_data.get('yaw', 0.0))
            msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
            msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

            # Standard covariance: 0.25 m^2 for x/y, 0.068 rad^2 for yaw
            msg.pose.covariance[0] = 0.25
            msg.pose.covariance[7] = 0.25
            msg.pose.covariance[35] = 0.068

            self.node_ref.initial_pose_pub.publish(msg)
            self.node_ref.get_logger().info(
                f'Published 2D Pose Estimate to AMCL: ({msg.pose.pose.position.x:.2f}, '
                f'{msg.pose.pose.position.y:.2f}, yaw={yaw:.2f})')

            resp = json.dumps({"status": "ok", "action": "initialpose"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/goal':
            # Dispatch Nav2 Goal
            msg = PoseStamped()
            msg.header.stamp = self.node_ref.get_clock().now().to_msg()
            msg.header.frame_id = 'map'
            msg.pose.position.x = float(req_data.get('x', 0.0))
            msg.pose.position.y = float(req_data.get('y', 0.0))
            msg.pose.position.z = 0.0

            yaw = float(req_data.get('yaw', 0.0))
            msg.pose.orientation.z = math.sin(yaw / 2.0)
            msg.pose.orientation.w = math.cos(yaw / 2.0)

            self.node_ref.goal_pub.publish(msg)
            self.node_ref.get_logger().info(
                f'Dispatched Nav2 Goal Pose: ({msg.pose.position.x:.2f}, '
                f'{msg.pose.position.y:.2f}, yaw={yaw:.2f})')

            resp = json.dumps({"status": "ok", "action": "goal"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/estop':
            self.node_ref.emergency_stop()
            resp = json.dumps({"status": "ok", "action": "estop"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/cancel':
            with self.node_ref.lock:
                self.node_ref.goal_x = None
                self.node_ref.goal_y = None
                self.node_ref.global_plan_points = []
                self.node_ref.local_plan_points = []
            self.node_ref.emergency_stop()
            resp = json.dumps({"status": "ok", "action": "cancel"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/waypoint':
            wx = float(req_data.get('x', 0.08))
            wy = float(req_data.get('y', 0.05))
            wyaw = float(req_data.get('yaw', 0.0))
            self.node_ref.dispatch_patrol_cmd('stop')
            self.node_ref.dispatch_waypoint(wx, wy, wyaw)
            resp = json.dumps({"status": "ok", "action": "waypoint", "x": wx, "y": wy, "yaw": wyaw}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/patrol':
            circuit = [
                (0.08, 0.05, "P1 Home Base"),
                (1.64, 1.62, "P2 Central Hub"),
                (3.20, 3.20, "P3 North Gallery"),
                (4.70, 1.80, "P4 East Lab"),
            ]

            with self.node_ref.lock:
                rx, ry = self.node_ref.robot_x, self.node_ref.robot_y

            # Dynamic entry point: select nearest waypoint to robot's CURRENT position
            dists = [math.hypot(wp[0] - rx, wp[1] - ry) for wp in circuit]
            best_idx = int(np.argmin(dists))
            target_wp = circuit[best_idx]

            self.node_ref.dispatch_waypoint(target_wp[0], target_wp[1], 0.0)
            self.node_ref.dispatch_patrol_cmd('start')

            resp = json.dumps({
                "status": "ok",
                "circuit": "4-point-unattended",
                "start_wp": target_wp[2],
                "x": target_wp[0],
                "y": target_wp[1]
            }).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/cleartrail':
            with self.node_ref.lock:
                self.node_ref.trajectory_history.clear()
            resp = json.dumps({"status": "ok", "action": "cleartrail"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/toggles':
            layer = req_data.get('layer', '')
            val = bool(req_data.get('value', True))

            with self.node_ref.lock:
                if layer == 'costmap':
                    self.node_ref.show_local_costmap = val
                elif layer == 'particles':
                    self.node_ref.show_particles = val
                elif layer == 'lidar':
                    self.node_ref.show_lidar = val
                elif layer == 'axes':
                    self.node_ref.show_axes = val
                elif layer == 'paths':
                    self.node_ref.show_paths = val
                elif layer == 'trail':
                    self.node_ref.show_trail = val

            resp = json.dumps({"status": "ok", "layer": layer, "value": val}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress verbose HTTP access logs in terminal
        pass


def run_ros(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = MapVisualizerNode()
    WebHandler.node_ref = node

    # Start ROS 2 executor thread
    ros_thread = threading.Thread(target=run_ros, args=(node,), daemon=True)
    ros_thread.start()

    # Start HTTP server on port 8080
    port = 8080
    server = HTTPServer(('0.0.0.0', port), WebHandler)
    node.get_logger().info(f'===========================================================')
    node.get_logger().info(f'   RVIZ-EQUIVALENT WEB VISUALIZER RUNNING AT: http://0.0.0.0:{port}')
    node.get_logger().info(f'===========================================================')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
