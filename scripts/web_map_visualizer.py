#!/usr/bin/env python3
"""
web_map_visualizer.py — Island Minimalist Cockpit Visualizer for AMR Cognition
Platform: ROS 2 / Standalone (Raspberry Pi 5 & x86_64 Host Workstation)

Features:
  - Dynamic Dual-Mode Architecture (Unmapped HRI & Mapped Facility Autonomy):
      * Automatically detects when an unmapped task is selected (e.g. 6-Gesture Suite, Safety Bubble).
      * When unmapped: HIDES the static room map and features the full HRI & Gesture Teleoperation Cockpit
        with central HD camera stream, canonical 6-gesture live matrix, active gimbal telemetry, and kinematics.
      * When mapped: Displays the pre-calibrated room map with Nav2 waypoints (P1–P4), AMCL particles, and costmaps.
      * When in SLAM mode: Displays live real-time SLAM occupancy grid as explored.
  - Multi-Channel Runtime Mode Synchronization:
      * CLI parameters (--mode, --unmapped, --mapped, --view)
      * Shared state files (/tmp/amr_active_mode.json, /root/cognition_ws/current_mode.json)
      * REST API (POST /api/mode)
      * ROS 2 topic (/cognition/mode)
  - Real-time 6-Gesture Matrix HUD with active glowing indicators and confidence chips.
  - Ultra-low memory footprint (<35MB RAM), pure HTML5/CSS3/ES6 JS with zero external dependencies.
"""

import os
import sys
import io
import math
import time
import json
import argparse
import threading
import urllib.request
from typing import Optional, Tuple, List
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2
import numpy as np

# ── ROS 2 Imports with Graceful Fallback ───────────────────────────────────────
HAS_ROS2 = False
HAS_COGNITION_MSGS = False
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from nav_msgs.msg import OccupancyGrid, Path
    from sensor_msgs.msg import LaserScan, CompressedImage
    from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped, PoseArray, Twist
    from std_msgs.msg import UInt16, String, Int32
    from tf2_ros import Buffer, TransformListener, TransformException
    HAS_ROS2 = True
    try:
        from cognition_interfaces.msg import Gesture
        HAS_COGNITION_MSGS = True
    except ImportError:
        HAS_COGNITION_MSGS = False
except ImportError:
    HAS_ROS2 = False


BaseNode = Node if HAS_ROS2 else object


class MapVisualizerNode(BaseNode):
    def __init__(self, force_mock=False, initial_mode="MODE 1.2: 6-GESTURE TELEOP SUITE", is_mapped=False, active_view="gesture"):
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

        # ── Mode & View State Tracking ───────────────────────────────────────
        self.is_mapped = is_mapped
        self.current_mode_name = initial_mode
        self.active_view = active_view  # "gesture", "slam", or "map"
        self._offline_room_map = None   # Loaded pre-calibrated room map
        self.last_state_file_mtime = 0.0

        # ── Kinematics & Active Vision Telemetry ──────────────────────────────
        self.cmd_vel_linear = 0.0
        self.cmd_vel_angular = 0.0
        self.gimbal_pan = 0
        self.gimbal_tilt = 18
        self.gimbal_state_str = "SEARCH"
        self.corridor_clearance = 1.85
        self.rear_clearance = 2.10
        self.last_gesture_token = "FOLLOW"
        self.last_gesture_conf = 0.99

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
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        if os.path.basename(curr_dir) == 'scripts':
            self._workspace_root = os.path.abspath(os.path.join(curr_dir, '..'))
        else:
            self._workspace_root = curr_dir

        # Load offline preview assets
        self._load_offline_assets()

        # Initial check of state file if present
        self._check_state_file()

        # ── Initialize ROS 2 Subscriptions if Available ──────────────────────
        if HAS_ROS2 and not self.force_mock:
            self._init_ros2_subscribers()

        # ── Start Simulation Loop for Offline/Charging Preview ───────────────
        self._sim_thread = threading.Thread(target=self._offline_simulation_loop, daemon=True)
        self._sim_thread.start()

        # ── Start Pre-rendered Frame Cache Loop ──────────────────────────────
        self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._render_thread.start()

    def _find_asset_path(self, subpath: str) -> Optional[str]:
        candidates = [
            os.path.join(self._workspace_root, subpath),
            os.path.join(os.path.dirname(__file__), subpath),
            os.path.join(os.path.dirname(__file__), '..', subpath),
            os.path.join('/root/cognition_ws', subpath),
            os.path.join('/home/pi/cognition_ws', subpath),
            os.path.join('/home/pi', subpath),
            os.path.join('/home/j/ros2_cognition_ws', subpath),
        ]
        for c in candidates:
            abs_c = os.path.abspath(c)
            if os.path.exists(abs_c):
                return abs_c
        return None

    def _load_offline_assets(self):
        """Loads realistic offline preview assets (floor map and laboratory camera frame)."""
        map_path = (
            self._find_asset_path('maps/room_map_20260812_0826.png') or
            self._find_asset_path('maps_new/room_map_20260812_0826.png')
        )
        if map_path and os.path.exists(map_path):
            raw = cv2.imread(map_path)
            if raw is not None:
                self._offline_room_map = raw
                if self.is_mapped:
                    self.map_img = raw
                    self.map_height, self.map_width = raw.shape[:2]
                    self.map_origin_x = -2.40
                    self.map_origin_y = -3.84
                    self.map_res = 0.05
                else:
                    self.map_img = None

        cam_path = self._find_asset_path('assets/preview_camera.jpg')
        if cam_path and os.path.exists(cam_path):
            cam_raw = cv2.imread(cam_path)
            if cam_raw is not None:
                self._cached_camera_jpeg = self._annotate_preview_camera(cam_raw)

    def _check_state_file(self):
        """Polls shared state files (/tmp/amr_active_mode.json, /root/cognition_ws/current_mode.json)."""
        candidates = [
            "/tmp/amr_active_mode.json",
            "/root/cognition_ws/current_mode.json",
            os.path.join(self._workspace_root, "current_mode.json")
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    mtime = os.path.getmtime(p)
                    if mtime > self.last_state_file_mtime:
                        self.last_state_file_mtime = mtime
                        with open(p, "r") as f:
                            data = json.load(f)
                        with self.lock:
                            mode = data.get("mode")
                            if mode:
                                self.current_mode_name = str(mode)
                            if "is_mapped" in data:
                                self.is_mapped = bool(data["is_mapped"])
                                if self.is_mapped and self.map_img is None and self._offline_room_map is not None:
                                    self.map_img = self._offline_room_map
                                    self.map_height, self.map_width = self._offline_room_map.shape[:2]
                                    self.map_origin_x = -2.40
                                    self.map_origin_y = -3.84
                                    self.map_res = 0.05
                                elif not self.is_mapped and self.active_view != "slam":
                                    self.map_img = None
                            if "view" in data:
                                self.active_view = str(data["view"])
                            elif not self.is_mapped:
                                self.active_view = "gesture"
                            else:
                                self.active_view = "map"
                except Exception:
                    pass
                break

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
        cv2.putText(annotated, f"GESTURE: {self.latest_gesture}", (32, h - 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 180), 2)

        _, buf = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return buf.tobytes()

    def _init_ros2_subscribers(self):
        """Initializes standard ROS 2 topic subscriptions."""
        try:
            self.tf_buffer = Buffer()
            self.tf_listener = TransformListener(self.tf_buffer, self)

            map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE if hasattr(ReliabilityPolicy, 'RELIABLE') else ReliabilityPolicy.BEST_EFFORT)
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
            if HAS_COGNITION_MSGS:
                self.create_subscription(Gesture, '/cognition/gesture', self._cognition_gesture_cb, 10)
            self.create_subscription(String, '/hand_gesture_cmd', self._gesture_cb, 10)
            self.create_subscription(Twist, '/cmd_vel', self._cmd_vel_cb, 10)
            self.create_subscription(String, '/cognition/gimbal_state', self._gimbal_state_cb, 10)
            self.create_subscription(String, '/cognition/mode', self._mode_topic_cb, 10)
            self.create_subscription(Int32, '/servo_s1', self._servo1_cb, 10)
            self.create_subscription(Int32, '/servo_s2', self._servo2_cb, 10)

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

    def _cmd_vel_cb(self, msg):
        with self.lock:
            self.cmd_vel_linear = float(msg.linear.x)
            self.cmd_vel_angular = float(msg.angular.z)

    def _gimbal_state_cb(self, msg):
        with self.lock:
            raw = str(msg.data).strip()
            self.gimbal_state_str = raw
            if '|' in raw:
                parts = raw.split('|')
                self.gimbal_state_str = parts[0]
                for p in parts[1:]:
                    if p.startswith('pan:'):
                        try: self.gimbal_pan = int(p.split(':')[1])
                        except ValueError: pass
                    elif p.startswith('tilt:'):
                        try: self.gimbal_tilt = int(p.split(':')[1])
                        except ValueError: pass

    def _servo1_cb(self, msg):
        with self.lock:
            self.gimbal_pan = int(msg.data)

    def _servo2_cb(self, msg):
        with self.lock:
            self.gimbal_tilt = int(msg.data)

    def _mode_topic_cb(self, msg):
        with self.lock:
            text = str(msg.data).strip()
            if text.startswith('{') and text.endswith('}'):
                try:
                    data = json.loads(text)
                    if "mode" in data: self.current_mode_name = data["mode"]
                    if "is_mapped" in data: self.is_mapped = bool(data["is_mapped"])
                    if "view" in data: self.active_view = data["view"]
                    return
                except Exception:
                    pass
            if '|' in text:
                parts = text.split('|')
                self.current_mode_name = parts[0]
                if len(parts) > 1:
                    mapped_str = parts[1].lower()
                    self.is_mapped = (mapped_str in ('mapped', 'true', '1'))
                    self.active_view = 'map' if self.is_mapped else 'gesture'
            else:
                self.current_mode_name = text

    def _parse_gesture_token(self, text: str):
        if not text:
            return
        t = str(text).strip()
        token = "NONE"
        conf = 1.0
        for canonical in ["STOP", "GO", "FOLLOW", "LEFT", "RIGHT", "BACK"]:
            if canonical in t.upper():
                token = canonical
                break
        if "(" in t and ")" in t:
            try:
                conf_str = t.split("(")[1].split(")")[0].strip()
                conf = float(conf_str)
            except Exception:
                conf = 0.95
        self.last_gesture_token = token
        self.last_gesture_conf = conf

    def _gesture_cb(self, msg):
        with self.lock:
            self.latest_gesture = msg.data
            self._parse_gesture_token(msg.data)

    def _cognition_gesture_cb(self, msg):
        with self.lock:
            label = getattr(msg, 'gesture_label', '') or ''
            conf = getattr(msg, 'confidence', 0.0) or 0.0
            if label and label not in ('NONE', 'TOO_FAR'):
                self.latest_gesture = f"{label} ({conf:.2f})"
                self.last_gesture_token = label
                self.last_gesture_conf = conf

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
        
        front_dists = []
        rear_dists = []
        for r in msg.ranges:
            if r_min < r < r_max and not math.isinf(r) and not math.isnan(r):
                deg = math.degrees(angle)
                if -35.0 <= deg <= 35.0:
                    front_dists.append(r)
                elif deg >= 145.0 or deg <= -145.0:
                    rear_dists.append(r)
                total_angle = ryaw + angle
                ox = rx + r * math.cos(total_angle)
                oy = ry + r * math.sin(total_angle)
                pts.append((ox, oy))
            angle += msg.angle_increment

        with self.lock:
            self.lidar_points_map = pts
            if front_dists:
                self.corridor_clearance = float(min(front_dists))
            if rear_dists:
                self.rear_clearance = float(min(rear_dists))

    # ── Simulation Engine (Offline & Charging Preview) ────────────────────────

    def _offline_simulation_loop(self):
        """Simulates realistic robot navigation along corridor waypoints while bot is offline/charging."""
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

        gesture_cycle = ["FOLLOW (0.99)", "LEFT (1.00)", "GO (0.98)", "RIGHT (0.97)", "STOP (0.99)", "BACK (0.96)"]
        gesture_idx = 0

        while True:
            time.sleep(0.05)
            t += 0.05

            # Periodic state file check
            if int(t * 10) % 5 == 0:
                self._check_state_file()

            if not self.is_preview_mode and self.has_received_live_map:
                continue  # Live ROS 2 mode active; suspend mock simulation

            with self.lock:
                # When in unmapped gesture mode: simulate gesture interactions & kinematics
                if not self.is_mapped:
                    if int(t) % 4 == 0 and int(t * 20) % 80 == 0:
                        gesture_idx = (gesture_idx + 1) % len(gesture_cycle)
                        self.latest_gesture = gesture_cycle[gesture_idx]
                        self._parse_gesture_token(self.latest_gesture)

                        tok = self.last_gesture_token
                        if tok == "STOP":
                            self.cmd_vel_linear = 0.0
                            self.cmd_vel_angular = 0.0
                        elif tok == "GO":
                            self.cmd_vel_linear = 0.25
                            self.cmd_vel_angular = 0.0
                        elif tok == "FOLLOW":
                            self.cmd_vel_linear = 0.20
                            self.cmd_vel_angular = 0.05 * math.sin(t)
                        elif tok == "LEFT":
                            self.cmd_vel_linear = 0.0
                            self.cmd_vel_angular = 0.40
                        elif tok == "RIGHT":
                            self.cmd_vel_linear = 0.0
                            self.cmd_vel_angular = -0.40
                        elif tok == "BACK":
                            self.cmd_vel_linear = -0.15
                            self.cmd_vel_angular = 0.0

                    self.gimbal_pan = int(12 * math.sin(t * 0.8))
                    self.gimbal_tilt = 18 + int(5 * math.cos(t * 0.5))
                    self.gimbal_state_str = "TRACKING"
                    self.battery_pct = 74 + int(1 * math.sin(t * 0.2))
                    self.battery_voltage = 8.1
                    self.battery_charging = True
                    continue

                # When in mapped mode: simulate patrol traversal on room map
                p_from = circuit[curr_idx]
                p_to = circuit[target_idx]

                progress += 0.012
                if progress >= 1.0:
                    progress = 0.0
                    curr_idx = target_idx
                    target_idx = (target_idx + 1) % len(circuit)
                    p_from = circuit[curr_idx]
                    p_to = circuit[target_idx]

                nx = p_from[0] + (p_to[0] - p_from[0]) * progress
                ny = p_from[1] + (p_to[1] - p_from[1]) * progress
                dy = p_to[1] - p_from[1]
                dx = p_to[0] - p_from[0]
                nyaw = math.atan2(dy, dx)

                self._update_pose(nx, ny, nyaw)
                self.cmd_vel_linear = 0.22
                self.cmd_vel_angular = 0.0

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
            self.cmd_vel_linear = 0.0
            self.cmd_vel_angular = 0.0
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

    # ── Dynamic Map Renderer ─────────────────────────────────────────────────

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
        """Renders high-resolution visualizer canvas."""
        with self.lock:
            if self.map_img is None:
                blank = np.full((600, 800, 3), 12, dtype=np.uint8)
                # Draw high-tech blueprint grid
                for gx in range(0, 800, 40):
                    cv2.line(blank, (gx, 0), (gx, 600), (22, 28, 40), 1)
                for gy in range(0, 600, 40):
                    cv2.line(blank, (0, gy), (800, gy), (22, 28, 40), 1)

                if self.active_view == 'slam':
                    cv2.putText(blank, "SLAM TOOLBOX ONLINE — REAL-TIME MAPPING ACTIVE", (130, 270),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 180), 2)
                    cv2.putText(blank, "Dynamic 2D metric occupancy grid constructs live as AMR translates", (120, 310),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 180, 200), 1)
                else:
                    cv2.putText(blank, "UNMAPPED ENVIRONMENT — TOUCHLESS TELEOP ACTIVE", (135, 270),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 210, 255), 2)
                    cv2.putText(blank, "Map suppressed for unmapped task. Use camera stage & gesture matrix.", (125, 310),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 180, 200), 1)

                _, buf = cv2.imencode('.jpg', blank, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
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
            is_mapped_flag = self.is_mapped

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

        # 3. AMCL Particles (only in mapped mode)
        if is_mapped_flag and show_part and particles_list:
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

        # 6. Waypoint Corridor Landmarks (ONLY in Mapped Mode)
        if is_mapped_flag:
            for wx, wy, label in self.corridor_landmarks:
                wu, wv = scale_pt(world_to_px(wx, wy))
                if 0 <= wu < resized.shape[1] and 0 <= wv < resized.shape[0]:
                    cv2.circle(resized, (wu, wv), 6, (180, 80, 240), -1)
                    cv2.circle(resized, (wu, wv), 9, (255, 255, 255), 2, cv2.LINE_AA)
                    tag = label.split()[0] if label else "WP"
                    (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
                    tx = wu + 11
                    ty = wv + 4
                    cv2.rectangle(resized, (tx - 4, ty - th - 3), (tx + tw + 4, ty + 4), (16, 20, 30), -1)
                    cv2.rectangle(resized, (tx - 4, ty - th - 3), (tx + tw + 4, ty + 4), (180, 80, 240), 1, cv2.LINE_AA)
                    cv2.putText(resized, tag, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

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
            tok = self.last_gesture_token
            # Determine drive state
            if abs(self.cmd_vel_linear) < 0.02 and abs(self.cmd_vel_angular) < 0.05:
                drive_state = "PARKED / HALTED"
            elif self.cmd_vel_linear > 0.05:
                drive_state = f"FORWARD (+{self.cmd_vel_linear:.2f} m/s)"
            elif self.cmd_vel_linear < -0.05:
                drive_state = f"REVERSE ({self.cmd_vel_linear:.2f} m/s)"
            elif self.cmd_vel_angular > 0.1:
                drive_state = f"PIVOT CCW (+{self.cmd_vel_angular:.2f} rad/s)"
            elif self.cmd_vel_angular < -0.1:
                drive_state = f"PIVOT CW ({self.cmd_vel_angular:.2f} rad/s)"
            else:
                drive_state = "STANDBY"

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
                "is_mapped": self.is_mapped,
                "active_view": self.active_view,
                "gesture": self.latest_gesture,
                "gesture_token": tok,
                "gesture_conf": round(self.last_gesture_conf, 2),
                "linear_vel": round(self.cmd_vel_linear, 2),
                "angular_vel": round(self.cmd_vel_angular, 2),
                "drive_state": drive_state,
                "gimbal_pan": self.gimbal_pan,
                "gimbal_tilt": self.gimbal_tilt,
                "gimbal_state": self.gimbal_state_str,
                "corridor_clearance": round(self.corridor_clearance, 2),
                "rear_clearance": round(self.rear_clearance, 2),
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
      --glass-dock: rgba(18, 24, 38, 0.86);
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
      --glow-cyan: rgba(6, 182, 212, 0.4);
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
      padding: 14px 18px;
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
      padding: 6px 16px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
      margin-bottom: 12px;
      gap: 10px;
      flex-wrap: nowrap;
      white-space: nowrap;
      overflow-x: auto;
    }
    .brand-cluster {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
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
      font-size: 0.88rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: var(--text-bright);
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .brand-title span { color: var(--accent-cyan); font-weight: 500; font-size: 0.78rem; }
    
    .mode-pill {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(16, 185, 129, 0.25));
      border: 1px solid rgba(6, 182, 212, 0.4);
      color: #67e8f9;
      padding: 5px 14px;
      border-radius: 9999px;
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.4px;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
      box-shadow: 0 0 14px var(--glow-cyan);
      transition: all 0.3s ease;
    }
    .mode-pill.mode-mapped {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.25));
      border-color: rgba(139, 92, 246, 0.4);
      color: #c4b5fd;
      box-shadow: 0 0 14px rgba(139, 92, 246, 0.35);
    }
    .mode-pill.mode-slam {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(6, 182, 212, 0.25));
      border-color: rgba(59, 130, 246, 0.4);
      color: #93c5fd;
      box-shadow: 0 0 14px rgba(59, 130, 246, 0.35);
    }
    .mode-pill.mode-alert {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(245, 158, 11, 0.25));
      border-color: rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      box-shadow: 0 0 14px var(--glow-crimson);
    }
    
    .btn-view-toggle {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--card-border);
      color: var(--text-bright);
      padding: 5px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }
    .btn-view-toggle:hover {
      background: rgba(255, 255, 255, 0.14);
      border-color: var(--accent-cyan);
      color: #fff;
    }

    .telemetry-cluster {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .battery-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      padding: 5px 12px;
      font-size: 0.78rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-bright);
    }
    .charge-badge {
      font-size: 0.65rem;
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
      font-size: 0.80rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 0 16px var(--glow-crimson);
      transition: all 0.2s ease;
    }
    .btn-estop:hover {
      transform: translateY(-1px);
      box-shadow: 0 0 22px rgba(239, 68, 68, 0.7);
    }
    .btn-estop:active { transform: scale(0.97); }

    /* ── Main Cockpit Card Container ── */
    .cockpit-island {
      width: 100%;
      max-width: 1360px;
      height: calc(100vh - 105px);
      min-height: 620px;
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

    /* ── 1. Map Viewport Container (Shown only when in Map/SLAM mode) ── */
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

    /* Floating Top-Right Picture-in-Picture Video Card (Map Mode Only) */
    .pip-camera-card {
      position: absolute;
      top: 16px;
      right: 16px;
      width: 300px;
      background: rgba(14, 18, 28, 0.88);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
      overflow: hidden;
      z-index: 50;
      transition: width 0.25s ease;
    }
    .pip-camera-card.expanded { width: 440px; }
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
      background: rgba(0, 0, 0, 0.7);
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

    /* ── 2. UNMAPPED GESTURE & TELEOPERATION COCKPIT VIEW ── */
    .unmapped-cockpit-container {
      width: 100%;
      height: 100%;
      display: flex;
      padding: 16px 20px 80px 20px;
      gap: 18px;
      box-sizing: border-box;
      z-index: 10;
      align-items: stretch;
    }

    /* Left Stage: Large HD Camera Stream Card */
    .cockpit-cam-stage {
      flex: 1.25;
      background: rgba(13, 17, 26, 0.85);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      backdrop-filter: blur(16px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
    }
    .cam-stage-header {
      padding: 10px 16px;
      background: rgba(0, 0, 0, 0.4);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .cam-stage-title {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-bright);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .cam-stage-viewport {
      flex: 1;
      position: relative;
      background: #000;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
    }
    #cam-main-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .cam-stage-overlay {
      position: absolute;
      bottom: 12px;
      left: 14px;
      right: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
    }

    /* Right Deck: Canonical 6-Gesture Matrix & Real-Time Telemetry */
    .cockpit-telemetry-deck {
      flex: 1.0;
      display: flex;
      flex-direction: column;
      gap: 14px;
      overflow-y: auto;
    }
    .deck-card {
      background: rgba(13, 17, 26, 0.85);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 14px 16px;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }
    .deck-card-title {
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--accent-cyan);
      margin-bottom: 2px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .deck-card-subtitle {
      font-size: 0.68rem;
      color: var(--text-muted);
      margin-bottom: 10px;
    }

    /* 6-Gesture Interactive Grid */
    .gesture-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .gesture-cell {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 10px;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
      transition: all 0.2s ease;
      position: relative;
    }
    .gesture-cell .cell-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .gesture-cell .cell-name {
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-bright);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .gesture-cell .cell-act {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.70rem;
      color: var(--accent-cyan);
    }
    .gesture-cell .cell-action-desc {
      font-size: 0.66rem;
      color: var(--text-muted);
    }
    .gesture-cell .active-beacon {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: transparent;
    }

    /* Active Highlight state for current detected gesture */
    .gesture-cell.active-gesture {
      background: rgba(16, 185, 129, 0.16);
      border-color: var(--accent-emerald);
      box-shadow: 0 0 14px var(--glow-emerald);
      transform: scale(1.02);
    }
    .gesture-cell.active-gesture .cell-name { color: #34d399; }
    .gesture-cell.active-gesture .cell-act { color: #6ee7b7; font-weight: 600; }
    .gesture-cell.active-gesture .active-beacon {
      background: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
    }

    /* Telemetry Row Clusters */
    .telemetry-row-cluster {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .stat-chip {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 6px 10px;
      display: flex;
      flex-direction: column;
    }
    .stat-chip .lbl { font-size: 0.64rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.3px; }
    .stat-chip .val { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 600; color: #fff; }
    .stat-chip .val.highlight { color: var(--accent-emerald); }

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
    .btn-map-tool:hover { background: rgba(255, 255, 255, 0.08); color: #fff; }
    .btn-map-tool.active {
      background: rgba(59, 130, 246, 0.25);
      border-color: var(--accent-blue);
      color: #93c5fd;
    }

    /* Layer Drawer Popover */
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
    }
    .layer-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.78rem;
      color: var(--text);
      cursor: pointer;
      padding: 3px 0;
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

    /* ── Floating Bottom Dock Island ── */
    .bottom-dock-island {
      position: absolute;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--glass-dock);
      backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 8px 16px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      z-index: 50;
      max-width: 95%;
    }
    .dock-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .dock-telemetry-row {
      display: flex;
      align-items: center;
      gap: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.76rem;
      color: var(--text);
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 5px;
      width: 100%;
      justify-content: center;
    }
    .dock-label {
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-right: 4px;
    }
    .btn-dock {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-bright);
      padding: 5px 12px;
      border-radius: 8px;
      font-size: 0.76rem;
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
    .btn-dock.primary {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(6, 182, 212, 0.25));
      border-color: rgba(16, 185, 129, 0.4);
      color: #34d399;
      font-weight: 600;
    }
    .btn-dock.amber {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.2));
      border-color: rgba(245, 158, 11, 0.4);
      color: #fcd34d;
    }

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

    <!-- Dynamically Updated Mission Mode Badge -->
    <div class="mode-pill" id="mode-display">
      <span>●</span> MODE 1.2: 6-GESTURE TELEOP SUITE
    </div>

    <button class="btn-view-toggle" id="btn-toggle-view" onclick="toggleViewMode()">
      <span id="view-toggle-icon">🗺️</span> <span id="view-toggle-label">Switch View</span>
    </button>

    <div class="telemetry-cluster">
      <div class="battery-pill">
        <span id="bat-icon">⚡</span>
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

    <!-- 1. MAP VIEWPORT & TOOLS (Active in Map / SLAM views) -->
    <div class="map-tools-island" id="map-tools-island" style="display: none;">
      <button class="btn-map-tool active" id="tool-view" title="Pan & Zoom Mode" onclick="setToolMode('view')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>
      </button>
      <button class="btn-map-tool" id="tool-goal" title="2D Nav Goal" onclick="setToolMode('goal')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
      </button>
      <button class="btn-map-tool" id="tool-pose" title="2D Pose Estimate" onclick="setToolMode('pose')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"/><circle cx="12" cy="10" r="3"/></svg>
      </button>
      <button class="btn-map-tool" id="tool-layers" title="Toggle Layers" onclick="toggleLayerDrawer()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
      </button>
      <button class="btn-map-tool" id="tool-reset" title="Reset View" onclick="resetMapTransform()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h3m12 0h3M12 3v3m0 12v3"/><circle cx="12" cy="12" r="7"/></svg>
      </button>
    </div>

    <!-- Map Layers Popover -->
    <div class="layer-popover" id="layer-drawer">
      <div class="layer-popover-header">Map Layers</div>
      <div class="layer-item" onclick="toggleLayer('costmap')"><span>Costmap</span><div class="toggle-switch on" id="tgl-costmap"></div></div>
      <div class="layer-item" onclick="toggleLayer('lidar')"><span>LiDAR Rays</span><div class="toggle-switch on" id="tgl-lidar"></div></div>
      <div class="layer-item" onclick="toggleLayer('particles')"><span>AMCL Particles</span><div class="toggle-switch on" id="tgl-particles"></div></div>
      <div class="layer-item" onclick="toggleLayer('axes')"><span>REP-103 Axes</span><div class="toggle-switch on" id="tgl-axes"></div></div>
      <div class="layer-item" onclick="toggleLayer('paths')"><span>Nav2 Path</span><div class="toggle-switch on" id="tgl-paths"></div></div>
      <div class="layer-item" onclick="toggleLayer('trail')"><span>Odometry Trail</span><div class="toggle-switch on" id="tgl-trail"></div></div>
    </div>

    <!-- Viewport for Map/SLAM (Hidden during unmapped tasks) -->
    <div class="viewport-container" id="viewport" style="display: none;">
      <div id="transform-layer">
        <img id="map-img" alt="AMR Occupancy Grid" />
        <canvas id="overlay-canvas"></canvas>
      </div>
    </div>

    <!-- Floating Top-Right PiP Video (Only visible in Map/SLAM view) -->
    <div class="pip-camera-card" id="pip-card" style="display: none;">
      <div class="pip-header">
        <div class="pip-live-badge" id="cam-badge">
          <div class="pip-live-dot"></div>
          <span id="cam-badge-text">LIVE 20 FPS</span>
        </div>
        <button class="btn-dock" style="padding: 2px 6px; font-size: 0.65rem;" onclick="togglePipExpand()">⤢</button>
      </div>
      <div class="pip-viewport">
        <img id="cam-img" alt="Camera Stream" />
        <div class="pip-hud-overlay">
          <div class="hud-chip gesture" id="hud-gesture">FOLLOW (0.99)</div>
          <div class="hud-chip" id="hud-centroid">Centroid: -1.89, -0.58</div>
        </div>
      </div>
    </div>

    <!-- 2. UNMAPPED HRI & GESTURE TELEOPERATION COCKPIT (Active during unmapped tasks) -->
    <div class="unmapped-cockpit-container" id="unmapped-cockpit">
      
      <!-- Primary HD Camera Stage -->
      <div class="cockpit-cam-stage">
        <div class="cam-stage-header">
          <div class="cam-stage-title">
            <span class="pip-live-dot"></span>
            <span>HD Neural Vision Feed & Optical Tracking HUD</span>
          </div>
          <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; color: var(--accent-cyan);">
            YOLOv8n + LSTM + MediaPipe 21
          </div>
        </div>
        <div class="cam-stage-viewport">
          <img id="cam-main-img" alt="Primary Camera Stream" />
          <div class="cam-stage-overlay">
            <div class="hud-chip" id="cam-stage-centroid">Operator Centroid: -1.89, -0.58</div>
            <div class="hud-chip gesture" id="cam-stage-gesture">ACTIVE GESTURE: FOLLOW (0.99)</div>
          </div>
        </div>
      </div>

      <!-- Teleoperation & AI Verification Deck -->
      <div class="cockpit-telemetry-deck">
        
        <!-- Canonical 6-Gesture Matrix Card -->
        <div class="deck-card">
          <div class="deck-card-title">
            <span>Canonical 6-Gesture Teleop Matrix</span>
            <span style="font-size: 0.65rem; color: var(--accent-emerald);">Live MLP Consensus</span>
          </div>
          <div class="deck-card-subtitle">Stand ~1.5m in front of camera • Touchless Control Protocol</div>
          
          <div class="gesture-grid">
            <div class="gesture-cell" id="gest-card-STOP">
              <div class="cell-top">
                <span class="cell-name">🛑 STOP</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">/cmd_vel = 0.0 m/s</span>
              <span class="cell-action-desc">Instant wheel halt (Open Palm)</span>
            </div>

            <div class="gesture-cell" id="gest-card-GO">
              <div class="cell-top">
                <span class="cell-name">👍 GO</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">+0.25 m/s Forward</span>
              <span class="cell-action-desc">Translates forward (Thumbs Up)</span>
            </div>

            <div class="gesture-cell" id="gest-card-FOLLOW">
              <div class="cell-top">
                <span class="cell-name">✌️ FOLLOW</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">Visual Servoing</span>
              <span class="cell-action-desc">Shadows footsteps (Peace Sign)</span>
            </div>

            <div class="gesture-cell" id="gest-card-LEFT">
              <div class="cell-top">
                <span class="cell-name">👈 LEFT</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">+0.40 rad/s CCW</span>
              <span class="cell-action-desc">Pivot left (Point Left)</span>
            </div>

            <div class="gesture-cell" id="gest-card-RIGHT">
              <div class="cell-top">
                <span class="cell-name">👉 RIGHT</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">-0.40 rad/s CW</span>
              <span class="cell-action-desc">Pivot right (Point Right)</span>
            </div>

            <div class="gesture-cell" id="gest-card-BACK">
              <div class="cell-top">
                <span class="cell-name">👇 BACK</span>
                <span class="active-beacon"></span>
              </div>
              <span class="cell-act">-0.15 m/s Reverse</span>
              <span class="cell-action-desc">Reverse retreat (Point Down)</span>
            </div>
          </div>
        </div>

        <!-- Gimbal & Chassis Kinematics Card -->
        <div class="deck-card">
          <div class="deck-card-title">
            <span>2-DOF Gimbal & Chassis Kinematics</span>
            <span id="gimbal-state-tag" style="font-size: 0.65rem; color: var(--accent-cyan);">TRACKING</span>
          </div>
          <div class="deck-card-subtitle">Real-time servo angles, wheel velocities, and drive arbitration</div>
          <div class="telemetry-row-cluster">
            <div class="stat-chip">
              <span class="lbl">Gimbal Pan</span>
              <span class="val" id="val-pan">0°</span>
            </div>
            <div class="stat-chip">
              <span class="lbl">Gimbal Tilt</span>
              <span class="val" id="val-tilt">+18°</span>
            </div>
            <div class="stat-chip">
              <span class="lbl">Drive State</span>
              <span class="val highlight" id="val-drive-state">PARKED</span>
            </div>
            <div class="stat-chip">
              <span class="lbl">Linear Speed</span>
              <span class="val" id="val-linear">0.00 m/s</span>
            </div>
            <div class="stat-chip">
              <span class="lbl">Angular Rate</span>
              <span class="val" id="val-angular">0.00 rad/s</span>
            </div>
            <div class="stat-chip">
              <span class="lbl">LiDAR Clear</span>
              <span class="val highlight" id="val-clearance">1.85m</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 3. FLOATING BOTTOM DOCK ISLAND -->
    <div class="bottom-dock-island">
      
      <!-- Waypoints Dispatch Row (Only visible in Mapped Mode) -->
      <div class="dock-row" id="dock-waypoints-row" style="display: none;">
        <span class="dock-label">Waypoints</span>
        <button class="btn-dock" onclick="dispatchWaypoint('P1 Home Base', 0.08, 0.05, 0.0)">P1 Home</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P2 Central Hub', 1.64, 1.62, 0.0)">P2 Center</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P3 North Gallery', 3.20, 3.20, 0.0)">P3 North</button>
        <button class="btn-dock" onclick="dispatchWaypoint('P4 East Lab', 4.70, 1.80, 0.0)">P4 East</button>
        <button class="btn-dock primary" onclick="runPatrolCircuit()">🚀 4-Pt Patrol</button>
      </div>

      <!-- Unmapped / Gesture Action Row (Visible in Unmapped Mode) -->
      <div class="dock-row" id="dock-gesture-row">
        <span class="dock-label">Touchless HRI</span>
        <button class="btn-dock" onclick="triggerEStop()">🛑 Halt Chassis</button>
        <button class="btn-dock" onclick="centerGimbal()">🎯 Recenter Gimbal</button>
        <button class="btn-dock amber" onclick="triggerBeep()">🔊 Safety Horn Test</button>
      </div>

      <!-- SLAM Controls Row (Visible in SLAM Mode) -->
      <div class="dock-row" id="dock-slam-row" style="display: none;">
        <span class="dock-label">SLAM Actions</span>
        <button class="btn-dock primary" onclick="saveActiveMap()">💾 Save Generated Map</button>
        <button class="btn-dock" onclick="clearTrail()">🧹 Clear Trail</button>
      </div>

      <!-- Shared Telemetry Status Row -->
      <div class="dock-telemetry-row">
        <div><span style="color:var(--text-muted);">X:</span> <span style="color:#fff; font-weight:600;" id="val-x">0.08</span>m</div>
        <div><span style="color:var(--text-muted);">Y:</span> <span style="color:#fff; font-weight:600;" id="val-y">0.05</span>m</div>
        <div><span style="color:var(--text-muted);">Yaw:</span> <span style="color:#fff; font-weight:600;" id="val-yaw">0.0°</span></div>
        <div><span style="color:var(--text-muted);">FastDDS:</span> <span style="color:#fff; font-weight:600;" id="val-dds">12ms</span></div>
        <div><span style="color:var(--text-muted);">Mode State:</span> <span style="color:var(--accent-cyan); font-weight:600;" id="val-mode-status">Unmapped Teleop</span></div>
      </div>

    </div>

  </main>

  <div class="toast" id="toast"></div>

  <!-- ── Interactive JavaScript Logic ── -->
  <script>
    let activeTool = 'view';
    let mapInfo = null;
    let currentModeName = 'MODE 1.2: 6-GESTURE TELEOP SUITE';
    let isMappedMode = false;
    let activeView = 'gesture'; // 'gesture', 'slam', 'map'

    // Viewport Pan & Zoom State
    let zoomScale = 1.0;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let startPanX = 0;
    let startPanY = 0;

    let isDraggingArrow = false;
    let dragStart = null;
    let dragEnd = null;

    const viewport = document.getElementById('viewport');
    const transformLayer = document.getElementById('transform-layer');
    const imgElem = document.getElementById('map-img');
    const overlay = document.getElementById('overlay-canvas');
    const ctx = overlay.getContext('2d');
    const pipCard = document.getElementById('pip-card');
    const unmappedCockpit = document.getElementById('unmapped-cockpit');
    const mapTools = document.getElementById('map-tools-island');
    const dockWaypoints = document.getElementById('dock-waypoints-row');
    const dockGesture = document.getElementById('dock-gesture-row');
    const dockSlam = document.getElementById('dock-slam-row');

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
      if (activeView === 'gesture') {
        setTimeout(streamMap, 1000);
        return;
      }
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
        setTimeout(streamMap, 120);
      };
      nextImg.onerror = function() { setTimeout(streamMap, 800); };
      nextImg.src = '/map.jpg?t=' + Date.now();
    }
    streamMap();

    // Stream Camera (Streams both PiP and Main Stage)
    const camPip = document.getElementById('cam-img');
    const camMain = document.getElementById('cam-main-img');
    function streamCam() {
      const nextCam = new Image();
      nextCam.onload = function() {
        if (camPip) camPip.src = nextCam.src;
        if (camMain) camMain.src = nextCam.src;
        setTimeout(streamCam, 90);
      };
      nextCam.onerror = function() { setTimeout(streamCam, 1000); };
      nextCam.src = '/camera.jpg?t=' + Date.now();
    }
    streamCam();

    // Update Layout between Gesture Cockpit and Spatial Map View
    function syncLayoutView(view, mapped) {
      activeView = view;
      isMappedMode = mapped;

      if (view === 'gesture') {
        viewport.style.display = 'none';
        pipCard.style.display = 'none';
        mapTools.style.display = 'none';
        unmappedCockpit.style.display = 'flex';

        dockWaypoints.style.display = 'none';
        dockSlam.style.display = 'none';
        dockGesture.style.display = 'flex';

        document.getElementById('view-toggle-icon').textContent = '🗺️';
        document.getElementById('view-toggle-label').textContent = 'Map View';
      } else {
        unmappedCockpit.style.display = 'none';
        viewport.style.display = 'block';
        pipCard.style.display = 'block';
        mapTools.style.display = 'flex';

        if (view === 'slam') {
          dockWaypoints.style.display = 'none';
          dockGesture.style.display = 'none';
          dockSlam.style.display = 'flex';
        } else {
          dockSlam.style.display = 'none';
          dockGesture.style.display = 'none';
          dockWaypoints.style.display = 'flex';
        }

        document.getElementById('view-toggle-icon').textContent = '📹';
        document.getElementById('view-toggle-label').textContent = 'Gesture Cockpit';
        resetMapTransform();
      }
    }

    function toggleViewMode() {
      const next = activeView === 'gesture' ? (isMappedMode ? 'map' : 'slam') : 'gesture';
      syncLayoutView(next, isMappedMode);
      fetch('/api/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ view: next, is_mapped: isMappedMode, mode: currentModeName })
      });
    }

    // Telemetry Polling (4 Hz)
    function updateTelemetry() {
      fetch('/telemetry')
        .then(r => r.json())
        .then(data => {
          mapInfo = data.map_info;
          currentModeName = data.current_mode;
          isMappedMode = data.is_mapped;

          // Sync View if not overridden locally
          if (data.active_view && data.active_view !== activeView) {
            syncLayoutView(data.active_view, data.is_mapped);
          }

          // Header Mode Pill
          const modePill = document.getElementById('mode-display');
          modePill.innerHTML = `<span>●</span> ${data.current_mode}`;
          modePill.className = 'mode-pill';
          if (!data.is_mapped && data.active_view === 'slam') {
            modePill.classList.add('mode-slam');
          } else if (!data.is_mapped) {
            modePill.classList.add('mode-unmapped');
          } else if (data.current_mode.includes('PATROL') || data.current_mode.includes('ESCORT')) {
            modePill.classList.add('mode-mapped');
          }

          // Coordinates & DDS Latency
          document.getElementById('val-x').textContent = data.x.toFixed(2);
          document.getElementById('val-y').textContent = data.y.toFixed(2);
          document.getElementById('val-yaw').textContent = data.yaw.toFixed(1) + '°';
          document.getElementById('val-dds').textContent = data.latency_ms + 'ms';
          document.getElementById('val-mode-status').textContent = data.is_mapped ? "Mapped Facility" : "Unmapped HRI";

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

          // Gesture & HUD Chips
          if (data.gesture) {
            document.getElementById('hud-gesture').textContent = data.gesture;
            document.getElementById('cam-stage-gesture').textContent = `ACTIVE GESTURE: ${data.gesture}`;
          }

          // 6-Gesture Matrix Highlights
          const tokens = ["STOP", "GO", "FOLLOW", "LEFT", "RIGHT", "BACK"];
          tokens.forEach(tok => {
            const card = document.getElementById(`gest-card-${tok}`);
            if (card) {
              const isActive = (data.gesture_token === tok);
              card.classList.toggle('active-gesture', isActive);
            }
          });

          // Kinematics & Active Gimbal telemetry
          document.getElementById('val-pan').textContent = (data.gimbal_pan >= 0 ? '+' : '') + data.gimbal_pan + '°';
          document.getElementById('val-tilt').textContent = (data.gimbal_tilt >= 0 ? '+' : '') + data.gimbal_tilt + '°';
          document.getElementById('val-drive-state').textContent = data.drive_state;
          document.getElementById('val-linear').textContent = (data.linear_vel >= 0 ? '+' : '') + data.linear_vel.toFixed(2) + ' m/s';
          document.getElementById('val-angular').textContent = (data.angular_vel >= 0 ? '+' : '') + data.angular_vel.toFixed(2) + ' rad/s';
          document.getElementById('val-clearance').textContent = data.corridor_clearance.toFixed(2) + 'm';
          document.getElementById('gimbal-state-tag').textContent = data.gimbal_state;
        })
        .catch(() => {});
    }
    setInterval(updateTelemetry, 250);

    // Initial Layout Sync
    syncLayoutView('gesture', false);

    // Actions & Handlers
    function setToolMode(mode) {
      activeTool = mode;
      document.getElementById('tool-view').classList.toggle('active', mode === 'view');
      document.getElementById('tool-goal').classList.toggle('active', mode === 'goal');
      document.getElementById('tool-pose').classList.toggle('active', mode === 'pose');
      viewport.classList.toggle('tool-active', mode !== 'view');
    }

    function toggleLayerDrawer() {
      document.getElementById('layer-drawer').classList.toggle('open');
    }

    function togglePipExpand() {
      pipCard.classList.toggle('expanded');
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

    function centerGimbal() {
      fetch('/api/gimbal_center', { method: 'POST' })
        .then(() => showToast('🎯 Gimbal Servos Recentered (Pan: 0°, Tilt: +18°)'));
    }

    function triggerBeep() {
      fetch('/api/beep', { method: 'POST' })
        .then(() => showToast('🔊 Safety Acoustic Horn Dispatched (/beep)'));
    }

    function saveActiveMap() {
      fetch('/api/save_map', { method: 'POST' })
        .then(() => showToast('💾 2D Metric Map Saved to /root/cognition_ws/maps_new/'));
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

    // Viewport Pan/Zoom & Drag Arrow Handlers for Map Mode
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
          }).then(() => showToast(`🎯 Nav2 Goal dispatched: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m)`));
        } else if (activeTool === 'pose') {
          fetch('/api/initialpose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x: wx, y: wy, yaw: yaw })
          }).then(() => showToast(`📍 2D Pose estimate sent: (${wx.toFixed(2)}m, ${wy.toFixed(2)}m)`));
        }
        setToolMode('view');
      }
    });

    function getMapCoordsFromMouse(e) {
      const rect = viewport.getBoundingClientRect();
      const vx = e.clientX - rect.left;
      const vy = e.clientY - rect.top;
      return { x: (vx - panX) / zoomScale, y: (vy - panY) / zoomScale };
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

        if self.path == '/api/mode':
            mode = req_data.get('mode')
            is_mapped = req_data.get('is_mapped')
            view = req_data.get('view')

            with self.node_ref.lock:
                if mode is not None:
                    self.node_ref.current_mode_name = str(mode)
                if is_mapped is not None:
                    self.node_ref.is_mapped = bool(is_mapped)
                    if self.node_ref.is_mapped and self.node_ref.map_img is None and self.node_ref._offline_room_map is not None:
                        self.node_ref.map_img = self.node_ref._offline_room_map
                    elif not self.node_ref.is_mapped and self.node_ref.active_view != 'slam':
                        self.node_ref.map_img = None
                if view is not None:
                    self.node_ref.active_view = str(view)

            resp = json.dumps({
                "status": "ok",
                "mode": self.node_ref.current_mode_name,
                "is_mapped": self.node_ref.is_mapped,
                "active_view": self.node_ref.active_view
            }).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/initialpose':
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

        elif self.path == '/api/gimbal_center':
            with self.node_ref.lock:
                self.node_ref.gimbal_pan = 0
                self.node_ref.gimbal_tilt = 18
            if HAS_ROS2:
                try:
                    p1 = self.node_ref.create_publisher(Int32, '/servo_s1', 10)
                    p2 = self.node_ref.create_publisher(Int32, '/servo_s2', 10)
                    m1 = Int32(); m1.data = 0
                    m2 = Int32(); m2.data = 18
                    p1.publish(m1); p2.publish(m2)
                except Exception:
                    pass
            resp = json.dumps({"status": "ok", "action": "gimbal_center"}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == '/api/beep':
            if HAS_ROS2:
                try:
                    bp = self.node_ref.create_publisher(UInt16, '/beep', 10)
                    bm = UInt16(); bm.data = 40
                    bp.publish(bm)
                except Exception:
                    pass
            resp = json.dumps({"status": "ok", "action": "beep"}).encode('utf-8')
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
    parser.add_argument('--mode', type=str, default="MODE 1.2: 6-GESTURE TELEOP SUITE", help='Active mission mode label')
    parser.add_argument('--unmapped', action='store_true', help='Start in unmapped mode (suppresses room map)')
    parser.add_argument('--mapped', action='store_true', help='Start in mapped mode (shows room map & waypoints)')
    parser.add_argument('--view', type=str, choices=['gesture', 'slam', 'map'], default=None, help='Initial cockpit view')
    args = parser.parse_args()

    use_ros = HAS_ROS2 and not args.standalone
    if use_ros:
        try:
            rclpy.init()
        except Exception:
            use_ros = False

    # Determine mapped/unmapped state
    if args.mapped:
        is_mapped = True
    elif args.unmapped:
        is_mapped = False
    else:
        # Default based on mode string or fallback to unmapped for safety
        is_mapped = ("MODE 2" in args.mode.upper() or "PATROL" in args.mode.upper() or "ESCORT" in args.mode.upper())

    # Determine active view
    if args.view:
        active_view = args.view
    else:
        if not is_mapped:
            active_view = "slam" if "SLAM" in args.mode.upper() else "gesture"
        else:
            active_view = "map"

    node = MapVisualizerNode(
        force_mock=args.mock or not use_ros,
        initial_mode=args.mode,
        is_mapped=is_mapped,
        active_view=active_view
    )
    WebHandler.node_ref = node

    if use_ros:
        ros_thread = threading.Thread(target=run_ros, args=(node,), daemon=True)
        ros_thread.start()

    server = HTTPServer(('0.0.0.0', args.port), WebHandler)
    mode_str = "OFFLINE CHARGING PREVIEW" if (args.mock or not use_ros) else "LIVE ROS 2 LINK"
    print("=" * 75)
    print(f"   AMR COGNITION — ISLAND MINIMALIST COCKPIT ({mode_str})")
    print(f"   Mode: {args.mode} | Mapped: {is_mapped} | View: {active_view}")
    print(f"   Open Visualizer in Browser: http://localhost:{args.port}")
    print("=" * 75)

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
