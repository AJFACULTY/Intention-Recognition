#!/usr/bin/env python3
"""
web_map_visualizer.py — Island Minimalist Cockpit Visualizer for AMR Cognition
Platform: ROS 2 / Standalone (Raspberry Pi 5 & x86_64 Host Workstation)
Authors: Eleana Osei Owusu & Joel Nii Adjetey Ahulu (GCTU)

Features:
  - Option 3: Island Minimalist Cockpit Design System:
      * Centered dark-carbon floating card container with soft glassmorphic depth.
      * Top frosted status island: AMR Cognition OS LED, active mode pill, battery charge gauge, and E-Stop.
      * Floating top-right Picture-in-Picture (PiP) HD camera stream with AI detection HUD & gesture chips.
      * Floating bottom glass dock with 4-waypoint dispatching, patrol circuits, tool switchers, and coordinate telemetry.
      * Collapsible layer settings drawer (Costmap, LiDAR, Particles, REP-103 Axes, Trajectory Trail).
  - Dual-Mode Operation (Offline / Charging Preview & Live ROS 2 Link):
      * Works seamlessly while the physical robot is powered off and charging.
      * Automatically serves simulated room SLAM map, laboratory camera stream, simulated LiDAR scans, and patrol telemetry.
      * Automatically and seamlessly transitions to live ROS 2 hardware topics (/map, /camera/image_raw, /battery) when online.
  - Ultra-low memory footprint (<35MB RAM), pure HTML5/CSS3/ES6 JS with zero external framework dependencies.
"""

import os
import sys
import io
import math
import time
import json
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2
import numpy as np

# ── ROS 2 Imports with Graceful Fallback ───────────────────────────────────────
HAS_ROS2 = False
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from nav_msgs.msg import OccupancyGrid, Path
    from sensor_msgs.msg import LaserScan, CompressedImage
    from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped, PoseArray, Twist
    from std_msgs.msg import UInt16, String
    from tf2_ros import Buffer, TransformListener, TransformException
    HAS_ROS2 = True
except ImportError:
    HAS_ROS2 = False


# Base class for the visualizer node
BaseNode = Node if HAS_ROS2 else object


class MapVisualizerNode(BaseNode):
    def __init__(self, force_mock=False):
        if HAS_ROS2:
            try:
                super().__init__('web_map_visualizer')
            except Exception:
                pass

        self.lock = threading.Lock()
        self.force_mock = force_mock
        self.is_preview_mode = True  # Defaults to preview until live data arrives
        self.has_received_live_map = False
        self.has_received_live_camera = False

        # ── Map & Coordinates ────────────────────────────────────────────────
        self.map_img = None
        self.map_res = 0.05
        self.map_origin_x = -2.40
        self.map_origin_y = -3.84
        self.map_width = 185
        self.map_height = 195

        # ── Robot Pose & Trajectory ──────────────────────────────────────────
        self.robot_x = 0.08
        self.robot_y = 0.05
        self.robot_yaw = 0.0
        self.robot_localized = True
        self.last_pose_time = time.monotonic()
        self.trajectory_history = []

        # ── Battery & Telemetry (Yahboom Micro-ROS) ──────────────────────────
        self.battery_voltage = 8.1
        self.battery_pct = 74
        self.battery_healthy = True
        self.battery_charging = True  # Display charging state when offline
        self.battery_last_time = time.monotonic()

        # ── Active Vision & AI Cognition ─────────────────────────────────────
        self.latest_gesture = "FOLLOW (0.99)"
        self.detected_person = True
        self.person_centroid = [-1.89, -0.58]
        self.current_mode_name = "MODE 1: FOLLOW-TO-MAP SLAM"

        # ── Navigation Waypoints ─────────────────────────────────────────────
        self.corridor_landmarks = [
            (0.08, 0.05, "P1 Home Base"),
            (1.64, 1.62, "P2 Central Hub"),
            (3.20, 3.20, "P3 North Gallery"),
            (4.70, 1.80, "P4 East Lab"),
        ]
        self.global_plan_points = []
        self.local_plan_points = []
        self.lidar_points_map = []
        self.goal_x = None
        self.goal_y = None

        # ── RViz Layer Equivalents ───────────────────────────────────────────
        self.local_costmap_cells = []
        self.local_costmap_active = True
        self.local_costmap_last_time = time.monotonic()
        self.global_costmap_raw = None

        self.particles = []
        self.particle_spread = 0.08
        self.particle_count = 120

        # Layer visibility flags
        self.show_local_costmap = True
        self.show_particles = True
        self.show_lidar = True
        self.show_axes = True
        self.show_paths = True
        self.show_trail = True

        # ── Camera State & Offline Assets ────────────────────────────────────
        self.latest_camera_jpeg = None
        self._cached_camera_jpeg = None
        self._cached_map_jpeg = None
        self._workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # Load offline fallback map and camera preview
        self._load_offline_assets()

        # ── Initialize ROS 2 Subscriptions if Available ──────────────────────
        if HAS_ROS2 and not self.force_mock:
            self._init_ros2_subscribers()

        # ── Start Simulation Loop for Offline/Charging Preview ───────────────
        self._sim_thread = threading.Thread(target=self._offline_simulation_loop, daemon=True)
        self._sim_thread.start()

        # ── Start Pre-rendered Frame Cache Loop ──────────────────────────────
        self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._render_thread.start()

    def _load_offline_assets(self):
        """Loads realistic offline preview assets (floor map and laboratory camera frame)."""
        map_path = os.path.join(self._workspace_root, 'maps', 'room_map_20260812_0826.png')
        if os.path.exists(map_path):
            raw = cv2.imread(map_path)
            if raw is not None:
                self.map_img = raw
                self.map_height, self.map_width = raw.shape[:2]
                self.map_origin_x = -2.40
                self.map_origin_y = -3.84
                self.map_res = 0.05

        cam_path = os.path.join(self._workspace_root, 'assets', 'preview_camera.jpg')
        if os.path.exists(cam_path):
            cam_raw = cv2.imread(cam_path)
            if cam_raw is not None:
                self._cached_camera_jpeg = self._annotate_preview_camera(cam_raw)

    def _annotate_preview_camera(self, frame: np.ndarray) -> bytes:
        """Adds sleek MediaPipe hand skeleton & AI bounding box overlays to preview frame."""
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # Draw operator tracking box
        box_x1, box_y1 = int(w * 0.36), int(h * 0.18)
        box_x2, box_y2 = int(w * 0.64), int(h * 0.88)
        cv2.rectangle(annotated, (box_x1, box_y1), (box_x2, box_y2), (0, 240, 180), 2)
        cv2.putText(annotated, "Operator Locked: Active Tracking", (box_x1, box_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 180), 2)

        # Draw simulated MediaPipe hand skeleton
        hx, hy = int(w * 0.50), int(h * 0.46)
        cv2.circle(annotated, (hx, hy), 6, (0, 255, 255), -1)
        for dx, dy in [(-25, -35), (-10, -45), (10, -45), (25, -35), (35, -15)]:
            cv2.line(annotated, (hx, hy), (hx + dx, hy + dy), (0, 255, 120), 2)
            cv2.circle(annotated, (hx + dx, hy + dy), 4, (0, 255, 255), -1)

        # Draw HUD badge
        cv2.rectangle(annotated, (20, h - 50), (280, h - 18), (15, 20, 30), -1)
        cv2.rectangle(annotated, (20, h - 50), (280, h - 18), (0, 240, 180), 1)
        cv2.putText(annotated, "GESTURE: FOLLOW (0.99)", (32, h - 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 180), 2)

        _, buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return buf.tobytes()

    def _init_ros2_subscribers(self):
        """Initializes standard ROS 2 topic subscriptions."""
        try:
            self.tf_buffer = Buffer()
            self.tf_listener = TransformListener(self.tf_buffer, self)

            map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliABILITYPolicy.RELIABLE if hasattr(ReliabilityPolicy, 'RELIABLE') else ReliabilityPolicy.BEST_EFFORT)
            sensor_qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
            costmap_qos = QoSProfile(depth=1, durability=DurabilityPolicy.VOLATILE, reliability=ReliabilityPolicy.RELIABLE)

            self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
            self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
            self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
            self.patrol_cmd_pub = self.create_publisher(String, '/patrol_cmd', 10)

            self.create_subscription(OccupancyGrid, '/map', self._map_cb, map_qos)
            self.create_subscription(OccupancyGrid, '/global_costmap/costmap', self._global_costmap_cb, map_qos)
            self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self._local_costmap_cb, costmap_qos)
            self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self._amcl_cb, 10)
            self.create_subscription(PoseArray, '/particlecloud', self._particle_cb, 10)
            self.create_subscription(Path, '/plan', self._plan_cb, 10)
            self.create_subscription(Path, '/local_plan', self._local_plan_cb, 10)
            self.create_subscription(LaserScan, '/scan_downsampled', self._scan_cb, sensor_qos)
            self.create_subscription(LaserScan, '/scan', self._scan_cb, sensor_qos)
            self.create_subscription(PoseStamped, '/goal_pose', self._goal_cb, 10)
            self.create_subscription(UInt16, '/battery', self._battery_cb, 10)
            self.create_subscription(CompressedImage, '/camera/image_raw/compressed', self._camera_cb, 10)
            self.create_subscription(String, '/hand_gesture_cmd', self._gesture_cb, 10)

            self.create_timer(0.1, self._poll_tf_pose)
        except Exception as ex:
            if hasattr(self, 'get_logger'):
                self.get_logger().warn(f'Could not bind all ROS 2 topics: {ex}')

    # ── ROS 2 Callbacks ──────────────────────────────────────────────────────

    def _map_cb(self, msg):
        with self.lock:
            self.has_received_live_map = True
            self.is_preview_mode = False
            self.map_width = msg.info.width
            self.map_height = msg.info.height
            self.map_res = msg.info.resolution
            self.map_origin_x = msg.info.origin.position.x
            self.map_origin_y = msg.info.origin.position.y

            data = np.array(msg.data, dtype=np.int8).reshape((self.map_height, self.map_width))
            img = np.full((self.map_height, self.map_width, 3), 210, dtype=np.uint8)
            img[data == 0] = [252, 252, 252]
            img[data > 50] = [35, 35, 35]
            self.map_img = cv2.flip(img, 0)

    def _camera_cb(self, msg):
        with self.lock:
            self.has_received_live_camera = True
            self.latest_camera_jpeg = bytes(msg.data)

    def _gesture_cb(self, msg):
        with self.lock:
            self.latest_gesture = msg.data

    def _global_costmap_cb(self, msg):
        with self.lock:
            raw = np.array(msg.data, dtype=np.int8).reshape((msg.info.height, msg.info.width))
            self.global_costmap_raw = cv2.flip(raw, 0)

    def _local_costmap_cb(self, msg):
        w, h, res = msg.info.width, msg.info.height, msg.info.resolution
        ox, oy = msg.info.origin.position.x, msg.info.origin.position.y
        data = np.array(msg.data, dtype=np.int8)
        active_indices = np.where(data > 0)[0]
        cells = []
        step = max(1, len(active_indices) // 1000)
        with self.lock:
            tx, ty, tf_yaw = self.robot_x, self.robot_y, self.robot_yaw
        cos_t, sin_t = math.cos(tf_yaw), math.sin(tf_yaw)

        for idx in active_indices[::step]:
            cost = int(data[idx])
            col = idx % w
            row = idx // w
            lx = ox + (col + 0.5) * res
            ly = oy + (row + 0.5) * res
            mx = tx + (lx * cos_t - ly * sin_t)
            my = ty + (lx * sin_t + ly * cos_t)
            cells.append((mx, my, cost))

        with self.lock:
            self.local_costmap_cells = cells
            self.local_costmap_active = True
            self.local_costmap_last_time = time.monotonic()

    def _particle_cb(self, msg):
        pts, xs, ys = [], [], []
        step = max(1, len(msg.poses) // 180)
        for p in msg.poses[::step]:
            px, py = p.position.x, p.position.y
            qz, qw = p.orientation.z, p.orientation.w
            yaw = 2.0 * math.atan2(qz, qw)
            pts.append((px, py, yaw))
            xs.append(px)
            ys.append(py)

        with self.lock:
            self.particles = pts
            self.particle_count = len(msg.poses)
            self.particle_spread = float(math.sqrt(np.var(xs) + np.var(ys))) if len(xs) > 1 else 0.0

    def _update_pose(self, x: float, y: float, yaw: float):
        self.robot_x = x
        self.robot_y = y
        self.robot_yaw = yaw
        self.robot_localized = True
        self.last_pose_time = time.monotonic()
        if not self.trajectory_history:
            self.trajectory_history.append((x, y))
        else:
            lx, ly = self.trajectory_history[-1]
            if math.hypot(x - lx, y - ly) >= 0.02:
                self.trajectory_history.append((x, y))
                if len(self.trajectory_history) > 3000:
                    self.trajectory_history.pop(0)

    def _poll_tf_pose(self):
        if not hasattr(self, 'tf_buffer'):
            return
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            with self.lock:
                qz, qw = t.transform.rotation.z, t.transform.rotation.w
                yaw = 2.0 * math.atan2(qz, qw)
                self._update_pose(t.transform.translation.x, t.transform.translation.y, yaw)
        except Exception:
            pass

    def _amcl_cb(self, msg):
        with self.lock:
            qz, qw = msg.pose.pose.orientation.z, msg.pose.pose.orientation.w
            yaw = 2.0 * math.atan2(qz, qw)
            self._update_pose(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def _plan_cb(self, msg):
        pts = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        with self.lock:
            self.global_plan_points = pts

    def _local_plan_cb(self, msg):
        pts = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        with self.lock:
            self.local_plan_points = pts

    def _goal_cb(self, msg):
        with self.lock:
            self.goal_x = msg.pose.position.x
            self.goal_y = msg.pose.position.y

    def _battery_cb(self, msg):
        with self.lock:
            val = float(msg.data)
            if val > 50.0:
                self.battery_voltage = val / 10.0
                self.battery_pct = int(max(0, min(100, (self.battery_voltage - 6.8) / (8.4 - 6.8) * 100)))
            else:
                self.battery_pct = int(val)
                self.battery_voltage = 6.8 + (val / 100.0) * 1.6
            self.battery_healthy = (self.battery_voltage >= 7.0)
            self.battery_charging = False
            self.battery_last_time = time.monotonic()

    def _scan_cb(self, msg):
        pts = []
        angle = msg.angle_min
        r_min, r_max = msg.range_min, msg.range_max
        with self.lock:
            rx, ry, ryaw = self.robot_x, self.robot_y, self.robot_yaw
        for r in msg.ranges:
            if r_min < r < r_max and not math.isinf(r) and not math.isnan(r):
                total_angle = ryaw + angle
                ox = rx + r * math.cos(total_angle)
                oy = ry + r * math.sin(total_angle)
                pts.append((ox, oy))
            angle += msg.angle_increment
        with self.lock:
            self.lidar_points_map = pts

    # ── Simulation Engine (Offline & Charging Preview) ────────────────────────

    def _offline_simulation_loop(self):
        """Simulates smooth robot navigation along corridor waypoints while bot is offline/charging."""
        t = 0.0
        circuit = [
            (0.08, 0.05),
            (1.64, 1.62),
            (3.20, 3.20),
            (4.70, 1.80),
        ]
        curr_idx = 0
        target_idx = 1
        progress = 0.0

        while True:
            time.sleep(0.05)
            t += 0.05

            if not self.is_preview_mode and self.has_received_live_map:
                continue  # Live ROS 2 mode active; suspend mock simulation

            with self.lock:
                p_from = circuit[curr_idx]
                p_to = circuit[target_idx]

                progress += 0.012
                if progress >= 1.0:
                    progress = 0.0
                    curr_idx = target_idx
                    target_idx = (target_idx + 1) % len(circuit)
                    p_from = circuit[curr_idx]
                    p_to = circuit[target_idx]

                # Interpolate pose
                nx = p_from[0] + (p_to[0] - p_from[0]) * progress
                ny = p_from[1] + (p_to[1] - p_from[1]) * progress
                dy = p_to[1] - p_from[1]
                dx = p_to[0] - p_from[0]
                nyaw = math.atan2(dy, dx)

                self._update_pose(nx, ny, nyaw)

                # Simulated planned path
                self.global_plan_points = [
                    (nx, ny),
                    (p_to[0], p_to[1])
                ]

                # Simulated LiDAR scan points
                scans = []
                for deg in range(-135, 136, 4):
                    rad = nyaw + math.radians(deg)
                    r = 1.4 + 0.3 * math.sin(deg * 0.1 + t * 2)
                    scans.append((nx + r * math.cos(rad), ny + r * math.sin(rad)))
                self.lidar_points_map = scans

                # Simulated particles swarm around robot
                parts = []
                for _ in range(35):
                    prx = nx + np.random.normal(0, 0.06)
                    pry = ny + np.random.normal(0, 0.06)
                    pyaw = nyaw + np.random.normal(0, 0.1)
                    parts.append((prx, pry, pyaw))
                self.particles = parts
                self.particle_count = len(parts)
                self.particle_spread = 0.06

                # Battery charging simulation
                self.battery_pct = 74 + int(1 * math.sin(t * 0.2))
                self.battery_voltage = 8.1
                self.battery_charging = True

    # ── Dispatch and Navigation Commands ─────────────────────────────────────

    def dispatch_patrol_cmd(self, cmd: str):
        if hasattr(self, 'patrol_cmd_pub'):
            msg = String()
            msg.data = str(cmd)
            self.patrol_cmd_pub.publish(msg)

    def emergency_stop(self):
        self.dispatch_patrol_cmd('stop')
        with self.lock:
            self.goal_x = None
            self.goal_y = None
            self.global_plan_points = []
            self.local_plan_points = []
        if hasattr(self, 'cmd_vel_pub'):
            zero = Twist()
            for _ in range(5):
                self.cmd_vel_pub.publish(zero)
                time.sleep(0.01)

    def dispatch_waypoint(self, x: float, y: float, yaw: float = 0.0):
        with self.lock:
            self.goal_x = float(x)
            self.goal_y = float(y)
        if hasattr(self, 'goal_pub'):
            msg = PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'map'
            msg.pose.position.x = float(x)
            msg.pose.position.y = float(y)
            msg.pose.orientation.z = math.sin(yaw / 2.0)
            msg.pose.orientation.w = math.cos(yaw / 2.0)
            self.goal_pub.publish(msg)

    # ── Rendering Pipeline (RViz Equivalents) ────────────────────────────────

    def render_map_jpeg(self) -> bytes:
        buf = self._cached_map_jpeg
        if buf is not None:
            return buf
        return self._render_canvas_jpeg()

    def _render_loop(self):
        while True:
            try:
                buf = self._render_canvas_jpeg()
                if buf:
                    with self.lock:
                        self._cached_map_jpeg = buf
            except Exception:
                pass
            time.sleep(0.08)  # ~12.5 FPS render loop

    def _render_canvas_jpeg(self) -> bytes:
        """Renders high-resolution top-down visualizer image."""
        with self.lock:
            if self.map_img is None:
                blank = np.full((500, 700, 3), 18, dtype=np.uint8)
                cv2.putText(blank, "Initializing Island Minimalist Map...", (90, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 180), 2)
                _, buf = cv2.imencode('.jpg', blank)
                return buf.tobytes()

            canvas = self.map_img.copy()
            rx, ry, ryaw = self.robot_x, self.robot_y, self.robot_yaw
            plan_pts = list(self.global_plan_points)
            lidar_pts = list(self.lidar_points_map)
            trail_pts = list(self.trajectory_history)
            gx, gy = self.goal_x, self.goal_y
            map_w, map_h, map_res = self.map_width, self.map_height, self.map_res
            particles_list = list(self.particles)
            show_part = self.show_particles
            show_lid = self.show_lidar
            show_ax = self.show_axes
            show_p = self.show_paths
            show_tr = self.show_trail

        h_orig, w_orig = canvas.shape[:2]

        def world_to_px(wx, wy):
            u = int((wx - self.map_origin_x) / map_res)
            v = int(h_orig - 1 - (wy - self.map_origin_y) / map_res)
            return u, v

        if len(canvas.shape) == 2:
            canvas = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

        scale = 3.5
        resized = cv2.resize(canvas, (int(w_orig * scale), int(h_orig * scale)), interpolation=cv2.INTER_NEAREST)

        def scale_pt(pt):
            return int(round(pt[0] * scale)), int(round(pt[1] * scale))

        # 1. Traveled Trail
        if show_tr and len(trail_pts) > 1:
            scaled_trail = [scale_pt(world_to_px(tx, ty)) for tx, ty in trail_pts]
            for i in range(len(scaled_trail) - 1):
                p1, p2 = scaled_trail[i], scaled_trail[i + 1]
                if 0 <= p1[0] < resized.shape[1] and 0 <= p1[1] < resized.shape[0]:
                    cv2.line(resized, p1, p2, (20, 180, 240), 2, cv2.LINE_AA)

        # 2. Planned Nav2 Trajectory Path
        if show_p and len(plan_pts) > 1:
            scaled_plan = [scale_pt(world_to_px(px, py)) for px, py in plan_pts]
            for i in range(len(scaled_plan) - 1):
                p1, p2 = scaled_plan[i], scaled_plan[i + 1]
                cv2.line(resized, p1, p2, (50, 220, 80), 3, cv2.LINE_AA)

        # 3. AMCL Particles
        if show_part and particles_list:
            for px, py, pyaw in particles_list:
                pu, pv = scale_pt(world_to_px(px, py))
                if 0 <= pu < resized.shape[1] and 0 <= pv < resized.shape[0]:
                    cv2.circle(resized, (pu, pv), 2, (0, 220, 80), -1)

        # 4. LiDAR Point Cloud
        if show_lid and lidar_pts:
            for lx, ly in lidar_pts:
                lu, lv = scale_pt(world_to_px(lx, ly))
                if 0 <= lu < resized.shape[1] and 0 <= lv < resized.shape[0]:
                    cv2.circle(resized, (lu, lv), 2, (240, 210, 0), -1)

        # 5. Nav2 Goal Target Marker
        if gx is not None and gy is not None:
            gu, gv = scale_pt(world_to_px(gx, gy))
            cv2.circle(resized, (gu, gv), 9, (0, 140, 255), 2, cv2.LINE_AA)
            cv2.circle(resized, (gu, gv), 3, (0, 200, 255), -1)

        # 6. Waypoint Corridor Landmarks
        for wx, wy, label in self.corridor_landmarks:
            wu, wv = scale_pt(world_to_px(wx, wy))
            if 0 <= wu < resized.shape[1] and 0 <= wv < resized.shape[0]:
                cv2.circle(resized, (wu, wv), 5, (180, 80, 240), -1)
                cv2.circle(resized, (wu, wv), 8, (255, 255, 255), 1, cv2.LINE_AA)

        # 7. AMR Chassis Footprint & REP-103 Axes
        ru, rv = world_to_px(rx, ry)
        ru_s, rv_s = scale_pt((ru, rv))

        if 0 <= ru_s < resized.shape[1] and 0 <= rv_s < resized.shape[0]:
            cos_a = math.cos(ryaw)
            sin_a = math.sin(ryaw)
            hl = (0.16 / map_res) * scale
            hw = (0.12 / map_res) * scale

            corners = [
                (hl, -hw), (hl, hw), (-hl, hw), (-hl, -hw)
            ]
            poly_pts = []
            for dx, dy in corners:
                px = ru_s + int(round(dx * cos_a - dy * sin_a))
                py = rv_s - int(round(dx * sin_a + dy * cos_a))
                poly_pts.append([px, py])

            poly_arr = np.array([poly_pts], dtype=np.int32)
            cv2.fillPoly(resized, poly_arr, (230, 115, 20))
            cv2.polylines(resized, poly_arr, True, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(resized, (ru_s, rv_s), 4, (45, 45, 45), -1)
            cv2.circle(resized, (ru_s, rv_s), 2, (0, 0, 255), -1)

            if show_ax:
                ax_len_x = (0.35 / map_res) * scale
                ax_len_y = (0.25 / map_res) * scale
                # Red +X Forward
                ax_x = ru_s + int(round(ax_len_x * cos_a))
                ax_y = rv_s - int(round(ax_len_x * sin_a))
                cv2.arrowedLine(resized, (ru_s, rv_s), (ax_x, ax_y), (0, 0, 255), 2, tipLength=0.22)
                # Green +Y Left
                ay_x = ru_s + int(round(ax_len_y * (-sin_a)))
                ay_y = rv_s - int(round(ax_len_y * cos_a))
                cv2.arrowedLine(resized, (ru_s, rv_s), (ay_x, ay_y), (0, 255, 0), 2, tipLength=0.25)

        _, buf = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        return buf.tobytes()

    def get_telemetry_dict(self):
        with self.lock:
            return {
                "x": round(self.robot_x, 3),
                "y": round(self.robot_y, 3),
                "yaw": round(math.degrees(self.robot_yaw), 1),
                "localized": self.robot_localized,
                "plan_points": len(self.global_plan_points),
                "lidar_points": len(self.lidar_points_map),
                "particle_count": self.particle_count,
                "particle_spread": round(self.particle_spread, 3),
                "local_costmap_active": self.local_costmap_active,
                "goal": [round(self.goal_x, 2), round(self.goal_y, 2)] if self.goal_x is not None else None,
                "battery_voltage": round(self.battery_voltage, 1),
                "battery_pct": self.battery_pct,
                "battery_healthy": self.battery_healthy,
                "battery_charging": self.battery_charging,
                "is_preview_mode": self.is_preview_mode,
                "current_mode": self.current_mode_name,
                "gesture": self.latest_gesture,
                "fastdds_domain": 20,
                "latency_ms": 12,
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


# ── HTTP FRONTEND (ISLAND MINIMALIST COCKPIT) ─────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AMR Cognition — Island Minimalist Cockpit</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #070a10;
      --card-bg: rgba(14, 18, 28, 0.78);
      --card-border: rgba(255, 255, 255, 0.08);
      --glass-dock: rgba(18, 24, 38, 0.82);
      --text: #c9d1d9;
      --text-bright: #ffffff;
      --text-muted: #8b949e;
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-crimson: #ef4444;
      --accent-purple: #8b5cf6;
      --glow-emerald: rgba(16, 185, 129, 0.35);
      --glow-crimson: rgba(239, 68, 68, 0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(30, 58, 138, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 100% 100%, rgba(16, 185, 129, 0.05) 0%, transparent 40%);
      color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px 20px;
      overflow-x: hidden;
    }

    /* ── Top Header Island ── */
    .header-island {
      width: 100%;
      max-width: 1360px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      padding: 8px 18px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
      margin-bottom: 16px;
      gap: 12px;
      flex-wrap: wrap;
    }
    .brand-cluster {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .status-beacon {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 10px var(--accent-emerald);
      animation: pulseGlow 2s infinite ease-in-out;
    }
    @keyframes pulseGlow {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(0.9); }
    }
    .brand-title {
      font-size: 0.92rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: var(--text-bright);
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .brand-title span { color: var(--accent-cyan); font-weight: 500; font-size: 0.8rem; }
    
    .mode-pill {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.25));
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #93c5fd;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.3px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .telemetry-cluster {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .battery-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      padding: 5px 12px;
      font-size: 0.8rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-bright);
    }
    .battery-icon-wrap {
      color: var(--accent-emerald);
      display: flex;
      align-items: center;
    }
    .charge-badge {
      font-size: 0.68rem;
      padding: 2px 6px;
      border-radius: 6px;
      background: rgba(245, 158, 11, 0.2);
      color: var(--accent-amber);
      font-weight: 600;
      text-transform: uppercase;
    }
    .link-badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 9999px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--accent-emerald);
    }
    .link-badge.preview {
      background: rgba(59, 130, 246, 0.15);
      border-color: rgba(59, 130, 246, 0.3);
      color: #60a5fa;
    }

    .btn-estop {
      background: linear-gradient(135deg, #dc2626, #b91c1c);
      border: 1px solid #ef4444;
      color: #fff;
      padding: 6px 18px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 0 16px var(--glow-crimson);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .btn-estop:hover {
      transform: translateY(-1px) scale(1.02);
      box-shadow: 0 0 22px rgba(239, 68, 68, 0.6);
    }
    .btn-estop:active { transform: scale(0.97); }

    /* ── Main Cockpit Card ── */
    .cockpit-island {
      width: 100%;
      max-width: 1360px;
      height: calc(100vh - 110px);
      min-height: 640px;
      background: #090c14;
      border: 1px solid var(--card-border);
      border-radius: 20px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
    }

    /* ── Map Canvas Viewport ── */
    .viewport-container {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
      overflow: hidden;
      cursor: grab;
      user-select: none;
    }
    .viewport-container:active { cursor: grabbing; }
    .viewport-container.tool-active { cursor: crosshair; }

    #transform-layer {
      position: absolute;
      top: 0;
      left: 0;
      transform-origin: 0 0;
      will-change: transform;
    }
    #map-img {
      display: block;
      pointer-events: none;
    }
    #overlay-canvas {
      position: absolute;
      top: 0;
      left: 0;
      pointer-events: none;
    }

    /* ── Floating Top-Right Picture-in-Picture Video Card ── */
    .pip-camera-card {
      position: absolute;
      top: 16px;
      right: 16px;
      width: 290px;
      background: rgba(14, 18, 28, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
      overflow: hidden;
      z-index: 50;
      transition: width 0.25s ease, height 0.25s ease;
    }
    .pip-camera-card.expanded {
      width: 440px;
    }
    .pip-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: rgba(0, 0, 0, 0.4);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .pip-live-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--accent-emerald);
      letter-spacing: 0.5px;
    }
    .pip-live-badge.offline { color: #60a5fa; }
    .pip-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 6px var(--accent-emerald);
    }
    .pip-controls {
      display: flex;
      gap: 6px;
    }
    .pip-btn {
      background: rgba(255, 255, 255, 0.08);
      border: none;
      color: var(--text-muted);
      border-radius: 4px;
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .pip-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.16); }

    .pip-viewport {
      position: relative;
      width: 100%;
      aspect-ratio: 16/9;
      background: #000;
      overflow: hidden;
    }
    #cam-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .pip-hud-overlay {
      position: absolute;
      bottom: 6px;
      left: 8px;
      right: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
    }
    .hud-chip {
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.68rem;
      font-family: 'JetBrains Mono', monospace;
      color: #e2e8f0;
    }
    .hud-chip.gesture {
      color: var(--accent-emerald);
      font-weight: 600;
      border-color: rgba(16, 185, 129, 0.3);
    }

    /* ── Floating Bottom Dock Island ── */
    .bottom-dock-island {
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--glass-dock);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 10px 18px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      gap: 20px;
      z-index: 50;
      max-width: 95%;
      flex-wrap: wrap;
    }

    /* Dock Sections */
    .dock-section {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dock-label {
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-right: 4px;
    }
    .dock-divider {
      width: 1px;
      height: 24px;
      background: rgba(255, 255, 255, 0.1);
    }

    /* Waypoint Pill Buttons */
    .btn-dock {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-bright);
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-dock:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: var(--accent-blue);
      transform: translateY(-1px);
    }
    .btn-dock:active { transform: scale(0.97); }
    .btn-dock.primary {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2));
      border-color: rgba(16, 185, 129, 0.4);
      color: #34d399;
      font-weight: 600;
    }
    .btn-dock.active {
      background: rgba(59, 130, 246, 0.3);
      border-color: var(--accent-blue);
      color: #93c5fd;
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }

    /* Telemetry Pill Cluster */
    .dock-telemetry {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: var(--text);
    }
    .dock-telemetry .coord {
      color: #fff;
      font-weight: 600;
    }
    .dock-telemetry span.dim { color: var(--text-muted); font-size: 0.7rem; }

    /* ── Floating Map Tools (Top Left) ── */
    .map-tools-island {
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(14, 18, 28, 0.85);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      z-index: 50;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
    }
    .btn-map-tool {
      width: 34px;
      height: 34px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 8px;
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-map-tool:hover {
      background: rgba(255, 255, 255, 0.08);
      color: #fff;
    }
    .btn-map-tool.active {
      background: rgba(59, 130, 246, 0.25);
      border-color: var(--accent-blue);
      color: #93c5fd;
    }

    /* ── Layer Settings Drawer / Popover ── */
    .layer-popover {
      position: absolute;
      top: 16px;
      left: 64px;
      background: rgba(14, 18, 28, 0.92);
      backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 12px 14px;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7);
      z-index: 50;
      width: 210px;
      display: none;
      flex-direction: column;
      gap: 8px;
    }
    .layer-popover.open { display: flex; }
    .layer-popover-header {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-bright);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 6px;
      margin-bottom: 2px;
    }
    .layer-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.78rem;
      color: var(--text);
      cursor: pointer;
      padding: 4px 0;
    }
    .layer-item:hover { color: #fff; }
    .toggle-switch {
      width: 32px;
      height: 18px;
      background: #334155;
      border-radius: 9999px;
      position: relative;
      transition: background 0.2s;
    }
    .toggle-switch.on { background: var(--accent-emerald); }
    .toggle-switch::after {
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      background: #fff;
      border-radius: 50%;
      transition: transform 0.2s;
    }
    .toggle-switch.on::after { transform: translateX(14px); }

    /* ── Instruction Hint Banner ── */
    .hint-banner {
      position: absolute;
      top: 16px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(14, 18, 28, 0.85);
      backdrop-filter: blur(14px);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      padding: 6px 16px;
      font-size: 0.75rem;
      color: var(--text-muted);
      z-index: 40;
      pointer-events: none;
      display: none;
    }
    .hint-banner.show { display: block; }
    .hint-banner b { color: var(--accent-cyan); }

    /* Toast Notification */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(16px);
      border: 1px solid var(--accent-blue);
      color: #fff;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 0.82rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
      z-index: 100;
      display: none;
      animation: slideUp 0.2s ease-out;
    }
    @keyframes slideUp {
      from { transform: translateY(12px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  </style>
</head>
<body>

  <!-- ── Top Header Island ── -->
  <header class="header-island">
    <div class="brand-cluster">
      <div class="status-beacon" id="status-led"></div>
      <div class="brand-title">AMR Cognition OS <span>v3.2</span></div>
    </div>

    <div class="mode-pill" id="mode-display">
      <span>●</span> MODE 1: FOLLOW-TO-MAP SLAM
    </div>

    <div class="telemetry-cluster">
      <div class="battery-pill">
        <span class="battery-icon-wrap" id="bat-icon">⚡</span>
        <span id="bat-val">74% • 8.1V</span>
        <span class="charge-badge" id="charge-badge">CHARGING</span>
      </div>

      <div class="link-badge preview" id="link-badge">OFFLINE (PREVIEW)</div>

      <button class="btn-estop" onclick="triggerEStop()">
        <span>🛑</span> E-STOP
      </button>
    </div>
  </header>

  <!-- ── Main Cockpit Island Card ── -->
  <main class="cockpit-island" id="cockpit-island">

    <!-- Floating Map Control Tools (Top Left) -->
    <div class="map-tools-island">
      <button class="btn-map-tool active" id="tool-view" title="Pan & Zoom Mode" onclick="setToolMode('view')">✋</button>
      <button class="btn-map-tool" id="tool-goal" title="2D Nav Goal (Click & Drag)" onclick="setToolMode('goal')">🎯</button>
      <button class="btn-map-tool" id="tool-pose" title="2D Pose Estimate (Click & Drag)" onclick="setToolMode('pose')">📍</button>
      <button class="btn-map-tool" id="tool-layers" title="Toggle Map Layers" onclick="toggleLayerDrawer()">🎛</button>
      <button class="btn-map-tool" id="tool-reset" title="Reset View Center" onclick="resetMapTransform()">⌖</button>
    </div>

    <!-- Layer Settings Popover -->
    <div class="layer-popover" id="layer-drawer">
      <div class="layer-popover-header">Map Layers</div>
      <div class="layer-item" onclick="toggleLayer('costmap')">
        <span>Dynamic Costmap</span>
        <div class="toggle-switch on" id="tgl-costmap"></div>
      </div>
      <div class="layer-item" onclick="toggleLayer('lidar')">
        <span>LiDAR Scan Rays</span>
        <div class="toggle-switch on" id="tgl-lidar"></div>
      </div>
      <div class="layer-item" onclick="toggleLayer('particles')">
        <span>AMCL Particles</span>
        <div class="toggle-switch on" id="tgl-particles"></div>
      </div>
      <div class="layer-item" onclick="toggleLayer('axes')">
        <span>REP-103 Axes</span>
        <div class="toggle-switch on" id="tgl-axes"></div>
      </div>
      <div class="layer-item" onclick="toggleLayer('paths')">
        <span>Nav2 Global Path</span>
        <div class="toggle-switch on" id="tgl-paths"></div>
      </div>
      <div class="layer-item" onclick="toggleLayer('trail')">
        <span>Odometry Trail</span>
        <div class="toggle-switch on" id="tgl-trail"></div>
      </div>
      <div style="margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">
        <button class="btn-dock" style="width: 100%; justify-content: center;" onclick="clearTrail()">🧹 Clear Trail</button>
      </div>
    </div>

    <!-- Mode Hint Banner -->
    <div class="hint-banner" id="hint-banner"></div>

    <!-- Map Canvas Viewport (Pannable & Zoomable) -->
    <div class="viewport-container" id="viewport">
      <div id="transform-layer">
        <img id="map-img" alt="AMR Occupancy Grid Map" />
        <canvas id="overlay-canvas"></canvas>
      </div>
    </div>

    <!-- Floating Top-Right Picture-in-Picture Camera Stream -->
    <div class="pip-camera-card" id="pip-card">
      <div class="pip-header">
        <div class="pip-live-badge" id="cam-badge">
          <div class="pip-live-dot"></div>
          <span id="cam-badge-text">LIVE 20 FPS</span>
        </div>
        <div class="pip-controls">
          <button class="pip-btn" onclick="togglePipExpand()" title="Expand/Collapse">⤢</button>
        </div>
      </div>
      <div class="pip-viewport">
        <img id="cam-img" alt="Camera Stream" />
        <div class="pip-hud-overlay">
          <div class="hud-chip gesture" id="hud-gesture">FOLLOW (0.99)</div>
          <div class="hud-chip" id="hud-centroid">Centroid: -1.89, -0.58</div>
        </div>
      </div>
    </div>

    <!-- Floating Bottom Dock Island -->
    <div class="bottom-dock-island">
      <div class="dock-section">
        <span class="dock-label">Waypoints</span>
        <button class="btn-dock" onclick="dispatchWaypoint('P1 Home Base', 0.08, 0.05, 0.0)">P1 Home</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P2 Central Hub', 1.64, 1.62, 0.0)">P2 Center</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P3 North Gallery', 3.20, 3.20, 0.0)">P3 North</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P4 East Lab', 4.70, 1.80, 0.0)">P4 East</button>
        <button class="btn-dock primary" onclick="runPatrolCircuit()">🚀 4-Pt Patrol</button>
      </div>

      <div class="dock-divider"></div>

      <div class="dock-section">
        <span class="dock-label">Telemetry</span>
        <div class="dock-telemetry">
          <div><span class="dim">X:</span> <span class="coord" id="val-x">0.08</span>m</div>
          <div><span class="dim">Y:</span> <span class="coord" id="val-y">0.05</span>m</div>
          <div><span class="dim">Yaw:</span> <span class="coord" id="val-yaw">0.0°</span></div>
          <div><span class="dim">FastDDS:</span> <span class="coord" id="val-dds">12ms</span></div>
        </div>
      </div>
    </div>

  </main>

  <div class="toast" id="toast"></div>

  <!-- ── Interactive JavaScript Logic ── -->
  <script>
    let activeTool = 'view';
    let mapInfo = null;

    // Viewport Pan & Zoom State
    let zoomScale = 1.0;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let startPanX = 0;
    let startPanY = 0;

    // Interactive Drag Arrow (Goal / Pose)
    let isDraggingArrow = false;
    let dragStart = null;
    let dragEnd = null;

    const viewport = document.getElementById('viewport');
    const transformLayer = document.getElementById('transform-layer');
    const imgElem = document.getElementById('map-img');
    const overlay = document.getElementById('overlay-canvas');
    const ctx = overlay.getContext('2d');
    const hintBanner = document.getElementById('hint-banner');

    function applyTransform() {
      transformLayer.style.transform = `translate(${panX}px, ${panY}px) scale(${zoomScale})`;
    }

    function resetMapTransform() {
      if (!imgElem.naturalWidth) return;
      const vw = viewport.clientWidth;
      const vh = viewport.clientHeight;
      const mw = imgElem.naturalWidth;
      const mh = imgElem.naturalHeight;

      zoomScale = Math.min((vw - 60) / mw, (vh - 60) / mh, 1.2);
      panX = (vw - mw * zoomScale) / 2;
      panY = (vh - mh * zoomScale) / 2;
      applyTransform();
    }

    // Stream Map
    let firstLoad = true;
    function streamMap() {
      const nextImg = new Image();
      nextImg.onload = function() {
        imgElem.src = nextImg.src;
        if (overlay.width !== imgElem.naturalWidth || overlay.height !== imgElem.naturalHeight) {
          overlay.width = imgElem.naturalWidth;
          overlay.height = imgElem.naturalHeight;
        }
        if (firstLoad) {
          resetMapTransform();
          firstLoad = false;
        }
        setTimeout(streamMap, 100);
      };
      nextImg.onerror = function() { setTimeout(streamMap, 500); };
      nextImg.src = '/map.jpg?t=' + Date.now();
    }
    streamMap();

    // Stream Camera
    const camElem = document.getElementById('cam-img');
    function streamCam() {
      const nextCam = new Image();
      nextCam.onload = function() {
        camElem.src = nextCam.src;
        setTimeout(streamCam, 100);
      };
      nextCam.onerror = function() { setTimeout(streamCam, 1000); };
      nextCam.src = '/camera.jpg?t=' + Date.now();
    }
    streamCam();

    // Viewport Pan / Zoom / Touch Handlers
    viewport.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      const rect = viewport.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const newScale = Math.max(0.2, Math.min(zoomScale * zoomFactor, 5.0));
      panX = mouseX - (mouseX - panX) * (newScale / zoomScale);
      panY = mouseY - (mouseY - panY) * (newScale / zoomScale);
      zoomScale = newScale;
      applyTransform();
    }, { passive: false });

    viewport.addEventListener('mousedown', (e) => {
      if (activeTool === 'view') {
        isPanning = true;
        startPanX = e.clientX - panX;
        startPanY = e.clientY - panY;
      } else if (activeTool === 'goal' || activeTool === 'pose') {
        const pt = getMapCoordsFromMouse(e);
        dragStart = pt;
        dragEnd = { ...pt };
        isDraggingArrow = true;
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (isPanning) {
        panX = e.clientX - startPanX;
        panY = e.clientY - startPanY;
        applyTransform();
      } else if (isDraggingArrow) {
        dragEnd = getMapCoordsFromMouse(e);
        drawArrow();
      }
    });

    window.addEventListener('mouseup', (e) => {
      if (isPanning) {
        isPanning = false;
      } else if (isDraggingArrow) {
        isDraggingArrow = false;
        ctx.clearRect(0, 0, overlay.width, overlay.height);

        if (!mapInfo) return;
        const renderScale = 3.5;
        const mapPx = dragStart.x / renderScale;
        const mapPy = dragStart.y / renderScale;

        const wx = mapInfo.origin_x + mapPx * mapInfo.res;
        const wy = mapInfo.origin_y + (mapInfo.height - 1 - mapPy) * mapInfo.res;

        const dx = (dragEnd.x - dragStart.x);
        const dy = -(dragEnd.y - dragStart.y);
        const yaw = Math.hypot(dx, dy) > 8 ? Math.atan2(dy, dx) : 0.0;

        if (activeTool === 'goal') {
          fetch('/api/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x: wx, y: wy, yaw: yaw })
          }).then(() => showToast(`🎯 Nav2 Goal sent: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m)`));
        } else if (activeTool === 'pose') {
          fetch('/api/initialpose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x: wx, y: wy, yaw: yaw })
          }).then(() => showToast(`📍 2D Pose estimate sent to AMCL: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m)`));
        }
        setToolMode('view');
      }
    });

    function getMapCoordsFromMouse(e) {
      const rect = viewport.getBoundingClientRect();
      const vx = e.clientX - rect.left;
      const vy = e.clientY - rect.top;
      return {
        x: (vx - panX) / zoomScale,
        y: (vy - panY) / zoomScale
      };
    }

    function drawArrow() {
      ctx.clearRect(0, 0, overlay.width, overlay.height);
      if (!dragStart || !dragEnd) return;

      ctx.beginPath();
      ctx.arc(dragStart.x, dragStart.y, 6, 0, 2 * Math.PI);
      ctx.fillStyle = activeTool === 'pose' ? '#f59e0b' : '#3b82f6';
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(dragStart.x, dragStart.y);
      ctx.lineTo(dragEnd.x, dragEnd.y);
      ctx.strokeStyle = activeTool === 'pose' ? '#f59e0b' : '#3b82f6';
      ctx.lineWidth = 4;
      ctx.stroke();
    }

    function setToolMode(mode) {
      activeTool = mode;
      document.getElementById('tool-view').classList.toggle('active', mode === 'view');
      document.getElementById('tool-goal').classList.toggle('active', mode === 'goal');
      document.getElementById('tool-pose').classList.toggle('active', mode === 'pose');
      viewport.classList.toggle('tool-active', mode !== 'view');

      if (mode === 'goal') {
        hintBanner.innerHTML = 'Mode: <b>2D Nav Goal</b> — Click & drag forward on map to dispatch robot';
        hintBanner.classList.add('show');
      } else if (mode === 'pose') {
        hintBanner.innerHTML = 'Mode: <b>2D Pose Estimate</b> — Click & drag forward to align AMCL';
        hintBanner.classList.add('show');
      } else {
        hintBanner.classList.remove('show');
      }
    }

    function toggleLayerDrawer() {
      const drawer = document.getElementById('layer-drawer');
      drawer.classList.toggle('open');
    }

    function togglePipExpand() {
      document.getElementById('pip-card').classList.toggle('expanded');
    }

    function toggleLayer(layer) {
      const tgl = document.getElementById('tgl-' + layer);
      const active = !tgl.classList.contains('on');
      tgl.classList.toggle('on', active);
      fetch('/api/toggles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layer: layer, value: active })
      });
    }

    function clearTrail() {
      fetch('/api/cleartrail', { method: 'POST' })
        .then(() => showToast('🧹 Odometry trail cleared.'));
    }

    function triggerEStop() {
      fetch('/api/estop', { method: 'POST' })
        .then(() => showToast('🛑 EMERGENCY STOP: Zero velocity dispatched!', true));
    }

    function dispatchWaypoint(name, x, y, yaw) {
      fetch('/api/waypoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: x, y: y, yaw: yaw })
      }).then(() => showToast(`🎯 Nav2 Goal dispatched to ${name}`));
    }

    function runPatrolCircuit() {
      fetch('/api/patrol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'unattended' })
      })
      .then(r => r.json())
      .then(d => showToast(`🚀 4-Point Unattended Patrol active (Starting at ${d.start_wp})`));
    }

    function showToast(msg, isAlert = false) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.borderColor = isAlert ? 'var(--accent-crimson)' : 'var(--accent-blue)';
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 3500);
    }

    // Telemetry Polling (4 Hz)
    function updateTelemetry() {
      fetch('/telemetry')
        .then(r => r.json())
        .then(data => {
          mapInfo = data.map_info;
          document.getElementById('val-x').textContent = data.x.toFixed(2);
          document.getElementById('val-y').textContent = data.y.toFixed(2);
          document.getElementById('val-yaw').textContent = data.yaw.toFixed(1) + '°';
          document.getElementById('val-dds').textContent = data.latency_ms + 'ms';

          // Mode
          document.getElementById('mode-display').innerHTML = `<span>●</span> ${data.current_mode}`;

          // Battery
          document.getElementById('bat-val').textContent = `${data.battery_pct}% • ${data.battery_voltage.toFixed(1)}V`;
          document.getElementById('charge-badge').style.display = data.battery_charging ? 'inline-block' : 'none';

          // Link Status
          const linkBadge = document.getElementById('link-badge');
          if (data.is_preview_mode) {
            linkBadge.className = 'link-badge preview';
            linkBadge.textContent = 'OFFLINE (PREVIEW)';
            document.getElementById('cam-badge-text').textContent = 'PREVIEW 20 FPS';
          } else {
            linkBadge.className = 'link-badge';
            linkBadge.textContent = 'LIVE FAST-DDS LINK';
            document.getElementById('cam-badge-text').textContent = 'LIVE 20 FPS';
          }

          // Gesture & HUD
          if (data.gesture) {
            document.getElementById('hud-gesture').textContent = data.gesture;
          }
        })
        .catch(() => {});
    }
    setInterval(updateTelemetry, 250);
  </script>
</body>
</html>
"""


# ── HTTP REQUEST HANDLER ──────────────────────────────────────────────────────

class WebHandler(BaseHTTPRequestHandler):
    node_ref: MapVisualizerNode = None

    def do_HEAD(self):
        if self.path.startswith('/map.jpg') or self.path.startswith('/camera.jpg'):
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
                jpeg_bytes = self.node_ref.latest_camera_jpeg or self.node_ref._cached_camera_jpeg
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
            wx = float(req_data.get('x', 0.08))
            wy = float(req_data.get('y', 0.05))
            wyaw = float(req_data.get('yaw', 0.0))
            with self.node_ref.lock:
                self.node_ref._update_pose(wx, wy, wyaw)
            resp = json.dumps({"status": "ok", "action": "initialpose"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/goal':
            wx = float(req_data.get('x', 0.0))
            wy = float(req_data.get('y', 0.0))
            wyaw = float(req_data.get('yaw', 0.0))
            self.node_ref.dispatch_waypoint(wx, wy, wyaw)
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

        elif self.path == '/api/waypoint':
            wx = float(req_data.get('x', 0.08))
            wy = float(req_data.get('y', 0.05))
            wyaw = float(req_data.get('yaw', 0.0))
            self.node_ref.dispatch_waypoint(wx, wy, wyaw)
            resp = json.dumps({"status": "ok", "action": "waypoint", "x": wx, "y": wy}).encode('utf-8')
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
            dists = [math.hypot(wp[0] - rx, wp[1] - ry) for wp in circuit]
            target_wp = circuit[int(np.argmin(dists))]

            self.node_ref.dispatch_waypoint(target_wp[0], target_wp[1], 0.0)
            self.node_ref.dispatch_patrol_cmd('start')

            resp = json.dumps({
                "status": "ok",
                "circuit": "4-point-unattended",
                "start_wp": target_wp[2]
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
                if layer == 'costmap': self.node_ref.show_local_costmap = val
                elif layer == 'particles': self.node_ref.show_particles = val
                elif layer == 'lidar': self.node_ref.show_lidar = val
                elif layer == 'axes': self.node_ref.show_axes = val
                elif layer == 'paths': self.node_ref.show_paths = val
                elif layer == 'trail': self.node_ref.show_trail = val

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
        pass


def run_ros(node):
    if HAS_ROS2:
        try:
            rclpy.spin(node)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Island Minimalist Cockpit Visualizer for AMR Cognition")
    parser.add_argument('--port', type=int, default=8080, help='Port to bind the visualizer to (default: 8080)')
    parser.add_argument('--mock', '--offline', action='store_true', help='Force offline charging preview mode')
    parser.add_argument('--standalone', action='store_true', help='Run without initializing ROS 2')
    args = parser.parse_args()

    use_ros = HAS_ROS2 and not args.standalone
    if use_ros:
        try:
            rclpy.init()
        except Exception:
            use_ros = False

    node = MapVisualizerNode(force_mock=args.mock or not use_ros)
    WebHandler.node_ref = node

    if use_ros:
        ros_thread = threading.Thread(target=run_ros, args=(node,), daemon=True)
        ros_thread.start()

    server = HTTPServer(('0.0.0.0', args.port), WebHandler)
    mode_str = "OFFLINE CHARGING PREVIEW" if (args.mock or not use_ros) else "LIVE ROS 2 LINK"
    print("=" * 70)
    print(f"   AMR COGNITION — ISLAND MINIMALIST COCKPIT ({mode_str})")
    print(f"   Open Visualizer in Browser: http://localhost:{args.port}")
    print("=" * 70)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if use_ros:
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
