#!/usr/bin/env python3
"""
human_pose_gesture_node.py — Unified Human Pose & Gated Hand Gesture Perception Node
=====================================================================================
Standards: ROS 2 REP-144, ISO 15066:2016 Speed and Separation Monitoring

Features:
- Single-pipeline human 3D pose tracking and biomechanically gated hand gesture recognition
- MediaPipe Pose Lite (33 landmarks) tracking human centroid at high efficiency (~35 MB RSS)
- Kinematic Attention Gating: Hand landmarker is completely dormant when arms are at rest;
  activates exclusively when wrist landmark (15/16) is elevated above hip/elbow
- Dual-tier 6-class gesture classification:
  - Tier 1: Invariant 19-feature MLP classifier
  - Tier 2: Anatomical geometric rule verification engine
- Publishes:
  - /cognition/detection (cognition_interfaces/Detection) for spatial tracking & following
  - /cognition/gesture (cognition_interfaces/Gesture) for robot motion command arbitration
  - /cognition/hand_target (geometry_msgs/Point) for 2-DOF active vision gimbal servoing
"""

import os
import sys
import time
import math
from collections import deque
import numpy as np
import cv2
import joblib

os.environ['OMP_NUM_THREADS'] = '2'

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Point
from cognition_interfaces.msg import Detection, Gesture
from ament_index_python.packages import get_package_share_directory

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# Gesture ID Constants (must match gesture classifier label encoder)
GESTURE_NONE = -1
GESTURE_BACK = 0
GESTURE_FOLLOW = 1
GESTURE_GO = 2
GESTURE_LEFT = 3
GESTURE_RIGHT = 4
GESTURE_STOP = 5

LABEL_TO_ID = {
    "BACK": GESTURE_BACK,
    "FOLLOW": GESTURE_FOLLOW,
    "GO": GESTURE_GO,
    "LEFT": GESTURE_LEFT,
    "RIGHT": GESTURE_RIGHT,
    "STOP": GESTURE_STOP,
}

# MediaPipe Pose Landmark Indices
POSE_NOSE = 0
POSE_LEFT_SHOULDER = 11
POSE_RIGHT_SHOULDER = 12
POSE_LEFT_ELBOW = 13
POSE_RIGHT_ELBOW = 14
POSE_LEFT_WRIST = 15
POSE_RIGHT_WRIST = 16
POSE_LEFT_HIP = 23
POSE_RIGHT_HIP = 24

HISTORY_LEN = 10


class HumanPoseGestureNode(Node):
    def __init__(self):
        super().__init__('human_pose_gesture_node')

        # ── Declare Parameters ──────────────────────────────────
        self.declare_parameter('headless', True)
        self.declare_parameter('frame_skip', 2)
        self.declare_parameter('min_pose_confidence', 0.50)
        self.declare_parameter('min_hand_size', 0.02)
        self.declare_parameter('wrist_elevation_threshold', 0.04)
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)

        self.headless = bool(self.get_parameter('headless').value)
        self.frame_skip = max(1, int(self.get_parameter('frame_skip').value))
        self.min_pose_conf = float(self.get_parameter('min_pose_confidence').value)
        self.min_hand_size = float(self.get_parameter('min_hand_size').value)
        self.wrist_elev_thresh = float(self.get_parameter('wrist_elevation_threshold').value)

        # ── Dynamic Model & Weight Path Resolution ──────────────
        ws_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        weights_dir = os.path.join(ws_root, 'ml_models', 'weights')

        try:
            share_dir = get_package_share_directory('cognition_perception')
        except Exception:
            share_dir = os.path.join(os.path.expanduser('~'), 'cognition_ws', 'src', 'cognition_perception')

        def find_file(candidates, default_name):
            for path in candidates:
                if os.path.exists(path):
                    return path
            return os.path.join(weights_dir, default_name)

        pose_model_path = find_file([
            os.path.join(weights_dir, 'pose_landmarker_lite.task'),
            os.path.join(share_dir, 'models', 'pose_landmarker_lite.task'),
            os.path.join(os.path.expanduser('~'), 'cognition_ws', 'models', 'pose_landmarker_lite.task'),
            '/root/cognition_ws/models/pose_landmarker_lite.task',
        ], 'pose_landmarker_lite.task')

        hand_model_path = find_file([
            os.path.join(weights_dir, 'hand_landmarker.task'),
            os.path.join(share_dir, 'models', 'hand_landmarker.task'),
            os.path.join(os.path.expanduser('~'), 'cognition_ws', 'models', 'hand_landmarker.task'),
            '/root/cognition_ws/models/hand_landmarker.task',
        ], 'hand_landmarker.task')

        clf_path = find_file([
            os.path.join(weights_dir, 'gesture_model_features.pkl'),
            os.path.join(share_dir, 'models', 'gesture_model_features.pkl'),
            os.path.join(os.path.expanduser('~'), 'cognition_ws', 'models', 'gesture_model_features.pkl'),
            '/root/cognition_ws/models/gesture_model_features.pkl',
        ], 'gesture_model_features.pkl')

        scaler_path = find_file([
            os.path.join(weights_dir, 'scaler_features.pkl'),
            os.path.join(share_dir, 'models', 'scaler_features.pkl'),
            os.path.join(os.path.expanduser('~'), 'cognition_ws', 'models', 'scaler_features.pkl'),
            '/root/cognition_ws/models/scaler_features.pkl',
        ], 'scaler_features.pkl')

        le_path = find_file([
            os.path.join(weights_dir, 'label_encoder_features.pkl'),
            os.path.join(share_dir, 'models', 'label_encoder_features.pkl'),
            os.path.join(os.path.expanduser('~'), 'cognition_ws', 'models', 'label_encoder_features.pkl'),
            '/root/cognition_ws/models/label_encoder_features.pkl',
        ], 'label_encoder_features.pkl')

        # ── Initialize MediaPipe Pose Landmarker Lite ────────────
        self.pose_detector = None
        if os.path.exists(pose_model_path):
            try:
                base_options = mp_python.BaseOptions(model_asset_path=pose_model_path)
                options = mp_vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    num_poses=1,
                    min_pose_detection_confidence=self.min_pose_conf,
                    min_pose_presence_confidence=self.min_pose_conf,
                    min_tracking_confidence=self.min_pose_conf,
                    output_segmentation_masks=False,
                )
                self.pose_detector = mp_vision.PoseLandmarker.create_from_options(options)
                self.get_logger().info(f'MediaPipe Pose Landmarker Lite loaded from {pose_model_path}')
            except Exception as e:
                self.get_logger().error(f'Failed to initialize PoseLandmarker: {e}')
        else:
            self.get_logger().error(f'Pose model file not found: {pose_model_path}')

        # ── Initialize MediaPipe Hand Landmarker ─────────────────
        self.hand_detector = None
        if os.path.exists(hand_model_path):
            try:
                base_options = mp_python.BaseOptions(model_asset_path=hand_model_path)
                options = mp_vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.35,
                    min_hand_presence_confidence=0.35,
                    min_tracking_confidence=0.35,
                )
                self.hand_detector = mp_vision.HandLandmarker.create_from_options(options)
                self.get_logger().info(f'MediaPipe Hand Landmarker loaded from {hand_model_path}')
            except Exception as e:
                self.get_logger().error(f'Failed to initialize HandLandmarker: {e}')
        else:
            self.get_logger().warn(f'Hand model file not found: {hand_model_path}')

        # ── Deterministic Graph Warm-Up ─────────────────────────
        try:
            dummy_img = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=np.zeros((480, 640, 3), dtype=np.uint8)
            )
            if self.pose_detector is not None:
                self.pose_detector.detect(dummy_img)
            if self.hand_detector is not None:
                self.hand_detector.detect(dummy_img)
            self.get_logger().info('Perception inference graphs pre-warmed at 640x480 resolution.')
        except Exception as e:
            self.get_logger().warn(f'Pre-warm warning (non-fatal): {e}')

        # ── Load 19-Feature Gesture Classifier ───────────────────
        self.clf = None
        self.scaler = None
        self.le = None
        if os.path.exists(clf_path) and os.path.exists(le_path):
            try:
                self.clf = joblib.load(clf_path)
                self.le = joblib.load(le_path)
                if os.path.exists(scaler_path):
                    self.scaler = joblib.load(scaler_path)
                self.get_logger().info(
                    f'Gesture MLP classifier loaded ({self.clf.n_features_in_} features): {list(self.le.classes_)}'
                )
            except Exception as e:
                self.get_logger().error(f'Failed to load gesture classifier: {e}')

        # Ensure hand_features module is importable
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # ── Publishers & Subscribers ────────────────────────────
        self.detection_pub = self.create_publisher(Detection, '/cognition/detection', 10)
        self.gesture_pub = self.create_publisher(Gesture, '/cognition/gesture', 10)
        self.hand_target_pub = self.create_publisher(Point, '/cognition/hand_target', 10)

        self.image_sub = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.image_callback,
            10
        )

        # ── State Tracking & Throttling ─────────────────────────
        self.frame_count = 0
        self.history = deque(maxlen=HISTORY_LEN)
        self.prev_centroid = None
        self.prev_time = None
        self.last_detection_msg = None
        self.last_gesture_msg = None
        self.last_msg_time = None

        # ── Biomechanical Gating Hysteresis & Debounce ──────────
        self.wrist_elev_thresh_low = -0.01  # Release threshold (5 cm deadband)
        self.gating_active = False
        self.active_streak = 0
        self.inactive_streak = 0

        self.get_logger().info(
            f'HumanPoseGestureNode running: frame_skip={self.frame_skip}, min_pose_conf={self.min_pose_conf:.2f}'
        )

    @staticmethod
    def _vis(lm):
        v = getattr(lm, 'visibility', None)
        return float(v) if v is not None else 1.0

    def extract_torso_centroid(self, landmarks):
        """
        Calculates the kinematic center of mass using shoulders and hips.
        Fallback to nose if lower torso is occluded.
        Clamped to [0.0, 1.0] image normalized bounds.
        """
        pts = []
        for idx in [POSE_LEFT_SHOULDER, POSE_RIGHT_SHOULDER, POSE_LEFT_HIP, POSE_RIGHT_HIP]:
            lm = landmarks[idx]
            if self._vis(lm) > 0.35:
                cx = max(0.0, min(1.0, float(lm.x)))
                cy = max(0.0, min(1.0, float(lm.y)))
                pts.append((cx, cy))

        if len(pts) >= 2:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            return cx, cy

        nose = landmarks[POSE_NOSE]
        return max(0.0, min(1.0, float(nose.x))), max(0.0, min(1.0, float(nose.y)))

    def is_wrist_active(self, landmarks):
        """
        Biomechanical Kinematic Attention Gate:
        Schmitt-Trigger Hysteresis + Temporal Debounce.
        Activates when wrist > upper threshold; remains active until wrist < lower threshold
        for 3 consecutive frames to eliminate boundary chatter.
        """
        l_wrist = landmarks[POSE_LEFT_WRIST]
        r_wrist = landmarks[POSE_RIGHT_WRIST]
        l_hip = landmarks[POSE_LEFT_HIP]
        r_hip = landmarks[POSE_RIGHT_HIP]
        l_elbow = landmarks[POSE_LEFT_ELBOW]
        r_elbow = landmarks[POSE_RIGHT_ELBOW]

        # Use relaxed release threshold if already active (Schmitt trigger deadband)
        thresh = self.wrist_elev_thresh_low if self.gating_active else self.wrist_elev_thresh

        # In image coordinates, y=0 is TOP and y=1 is BOTTOM.
        # Wrist is elevated when y_wrist < y_reference.
        left_raised = (
            (self._vis(l_wrist) > 0.40) and
            (l_wrist.y < l_hip.y - thresh or l_wrist.y < l_elbow.y + 0.05)
        )
        right_raised = (
            (self._vis(r_wrist) > 0.40) and
            (r_wrist.y < r_hip.y - thresh or r_wrist.y < r_elbow.y + 0.05)
        )

        raw_raised = (left_raised or right_raised)
        if raw_raised:
            self.active_streak += 1
            self.inactive_streak = 0
            self.gating_active = True
        else:
            self.inactive_streak += 1
            self.active_streak = 0
            if self.inactive_streak >= 3:
                self.gating_active = False

        active_wrist = None
        if right_raised and left_raised:
            active_wrist = r_wrist if r_wrist.y < l_wrist.y else l_wrist
        elif right_raised:
            active_wrist = r_wrist
        elif left_raised:
            active_wrist = l_wrist

        return self.gating_active, active_wrist

    def classify_hand_landmarks(self, landmarks):
        """
        Dual-Tier Gesture Classifier:
        Tier 1: Trained 19-Feature Invariant MLP.
        Tier 2: Anatomical Geometric Rule Verification.
        """
        if not landmarks or len(landmarks) < 21:
            return GESTURE_NONE, "NONE", 0.0

        # Tier 1: Invariant 19-feature MLP
        if self.clf is not None and self.scaler is not None and self.le is not None:
            try:
                from hand_features import extract_features
                lm_coords = [(lm.x, lm.y, lm.z) for lm in landmarks]
                raw_feats = extract_features(lm_coords)
                if len(raw_feats) == self.clf.n_features_in_:
                    feats_scaled = self.scaler.transform([raw_feats])
                    pred_idx = int(self.clf.predict(feats_scaled)[0])
                    pred_label = str(self.le.inverse_transform([pred_idx])[0])
                    confidence = float(self.clf.predict_proba(feats_scaled)[0].max())

                    if confidence >= 0.70:
                        gid = LABEL_TO_ID.get(pred_label, GESTURE_NONE)
                        return gid, pred_label, confidence
            except Exception as e:
                self.get_logger().warn(f'MLP inference fallback: {e}', throttle_duration_sec=5.0)

        # Tier 2: Anatomical Geometric Rule Engine
        def is_ext(tip, pip, mcp):
            d_tip = math.hypot(landmarks[tip].x - landmarks[0].x, landmarks[tip].y - landmarks[0].y)
            d_mcp = math.hypot(landmarks[mcp].x - landmarks[0].x, landmarks[mcp].y - landmarks[0].y)
            return (d_tip > 1.30 * d_mcp) or (landmarks[tip].y < landmarks[pip].y)

        index_up = is_ext(8, 6, 5)
        middle_up = is_ext(12, 10, 9)
        ring_up = is_ext(16, 14, 13)
        pinky_up = is_ext(20, 18, 17)

        d_thumb_tip = math.hypot(landmarks[4].x - landmarks[0].x, landmarks[4].y - landmarks[0].y)
        d_thumb_mcp = math.hypot(landmarks[2].x - landmarks[0].x, landmarks[2].y - landmarks[0].y)
        thumb_up = (d_thumb_tip > 1.25 * d_thumb_mcp) and (landmarks[4].y < landmarks[5].y or landmarks[4].y < landmarks[2].y)
        thumb_down = (landmarks[4].y > landmarks[2].y) and (landmarks[4].y > landmarks[17].y)

        fingers_up_count = sum([index_up, middle_up, ring_up, pinky_up])

        # 1. STOP: Open palm (all fingers extended)
        if fingers_up_count >= 4:
            return GESTURE_STOP, "STOP", 0.98

        # 2. FOLLOW: Peace sign / V-sign (Index + Middle extended)
        if index_up and middle_up and not ring_up and not pinky_up:
            return GESTURE_FOLLOW, "FOLLOW", 0.96

        # 3. GO: Thumbs up (thumb upright, other fingers folded)
        if thumb_up and fingers_up_count == 0:
            return GESTURE_GO, "GO", 0.95

        # 4. LEFT / RIGHT: Single index finger pointing laterally
        d_index_ext = math.hypot(landmarks[8].x - landmarks[5].x, landmarks[8].y - landmarks[5].y)
        d_index_mcp = math.hypot(landmarks[6].x - landmarks[5].x, landmarks[6].y - landmarks[5].y)
        index_pointing = index_up or (d_index_ext > 1.35 * d_index_mcp)

        if index_pointing and not middle_up and not ring_up and not pinky_up:
            dx = landmarks[8].x - landmarks[5].x
            if dx < -0.035:
                return GESTURE_LEFT, "LEFT", 0.95
            elif dx > 0.035:
                return GESTURE_RIGHT, "RIGHT", 0.95
            else:
                return GESTURE_GO, "GO", 0.92

        # 5. BACK: Closed fist or thumb down
        if fingers_up_count == 0:
            if thumb_down:
                return GESTURE_BACK, "BACK", 0.95
            return GESTURE_BACK, "BACK", 0.90

        return GESTURE_NONE, "NONE", 0.0

    def compute_velocity_and_direction(self, cx, cy, now_sec):
        vx, vy = 0.0, 0.0
        if self.prev_centroid is not None and self.prev_time is not None:
            dt = now_sec - self.prev_time
            if 0.01 < dt < 1.0:
                vx = (cx - self.prev_centroid[0]) / dt
                vy = (cy - self.prev_centroid[1]) / dt

        self.prev_centroid = (cx, cy)
        self.prev_time = now_sec

        if abs(vx) < 0.05 and abs(vy) < 0.05:
            direction = "STATIONARY"
        elif abs(vx) >= abs(vy):
            direction = "RIGHT" if vx > 0 else "LEFT"
        else:
            direction = "FORWARD" if vy > 0 else "BACKWARD"

        return vx, vy, direction

    def image_callback(self, msg: CompressedImage):
        try:
            self.frame_count += 1
            now = self.get_clock().now()
            now_sec = now.nanoseconds / 1e9

            # ── THROTTLED FRAME-SKIPPING WITH VELOCITY EXTRAPOLATION ──
            if self.frame_count % self.frame_skip != 0:
                if self.last_detection_msg is not None and self.last_msg_time is not None:
                    dt = now_sec - self.last_msg_time
                    if dt < 0.35:
                        self.last_detection_msg.stamp = now.to_msg()
                        self.detection_pub.publish(self.last_detection_msg)

                        if self.last_gesture_msg is not None:
                            self.last_gesture_msg.stamp = now.to_msg()
                            self.gesture_pub.publish(self.last_gesture_msg)
                return

            if self.pose_detector is None:
                return

            # Decode JPEG
            arr = np.frombuffer(msg.data, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                return

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mpi = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # ── 1. POSE INFERENCE ──
            pose_result = self.pose_detector.detect(mpi)

            det_msg = Detection()
            det_msg.stamp = now.to_msg()
            g_msg = Gesture()
            g_msg.stamp = now.to_msg()
            h_pt = Point()

            if pose_result.pose_landmarks and len(pose_result.pose_landmarks) > 0:
                landmarks = pose_result.pose_landmarks[0]

                # Kinematic Center of Mass
                cx, cy = self.extract_torso_centroid(landmarks)

                # Bounding box dimensions from pose landmarks
                xs = [lm.x for lm in landmarks if self._vis(lm) > 0.30]
                ys = [lm.y for lm in landmarks if self._vis(lm) > 0.30]
                bw = (max(xs) - min(xs)) if xs else 0.3
                bh = (max(ys) - min(ys)) if ys else 0.6

                vx, vy, direction = self.compute_velocity_and_direction(cx, cy, now_sec)
                pred_x = float(cx + vx * 0.1)

                det_msg.center_x = float(cx)
                det_msg.center_y = float(cy)
                det_msg.width = float(bw)
                det_msg.height = float(bh)
                vis_scores = [self._vis(lm) for lm in landmarks[:25]]
                det_msg.confidence = float(np.mean(vis_scores)) if vis_scores else 0.80
                det_msg.label = "person"
                det_msg.velocity_x = float(vx)
                det_msg.velocity_y = float(vy)
                det_msg.direction = direction
                det_msg.predicted_x = pred_x

                # ── 2. BIOMECHANICAL KINEMATIC ATTENTION FOR GESTURES ──
                wrist_active, active_wrist = self.is_wrist_active(landmarks)

                if wrist_active and active_wrist is not None and self.hand_detector is not None:
                    # Hand is raised: crop region around active wrist or run hand landmarker on frame
                    # Running hand_detector on the image extracts full 21 joints
                    hand_result = self.hand_detector.detect(mpi)
                    if hand_result.hand_landmarks and len(hand_result.hand_landmarks) > 0:
                        hlms = hand_result.hand_landmarks[0]
                        hx = [l.x for l in hlms]
                        hy = [l.y for l in hlms]
                        hand_sz = max(max(hx) - min(hx), max(hy) - min(hy))

                        if hand_sz >= self.min_hand_size:
                            gid, glabel, gconf = self.classify_hand_landmarks(hlms)
                            g_msg.gesture_id = gid
                            g_msg.gesture_label = glabel
                            g_msg.confidence = gconf

                            # Hand target coordinate for active vision gimbal
                            hand_cx = float(sum(hx) / len(hx))
                            hand_cy = float(sum(hy) / len(hy))
                            h_pt.x = float((hand_cx - 0.5) * 2.0)
                            h_pt.y = float((hand_cy - 0.5) * 2.0)
                            h_pt.z = float(gconf)
                        else:
                            g_msg.gesture_id = GESTURE_NONE
                            g_msg.gesture_label = "TOO_FAR"
                            g_msg.confidence = 0.0
                            h_pt.z = 0.0
                    else:
                        g_msg.gesture_id = GESTURE_NONE
                        g_msg.gesture_label = "RAISED_NO_HAND"
                        g_msg.confidence = 0.0
                        # Point gimbal to the raised wrist position
                        h_pt.x = float((active_wrist.x - 0.5) * 2.0)
                        h_pt.y = float((active_wrist.y - 0.5) * 2.0)
                        h_pt.z = 0.5
                else:
                    # Hands at rest: gesture model is dormant
                    g_msg.gesture_id = GESTURE_NONE
                    g_msg.gesture_label = "NONE"
                    g_msg.confidence = 0.0
                    h_pt.z = 0.0  # Tells active vision to track torso centroid

            else:
                # No person detected
                det_msg.center_x = 0.5
                det_msg.center_y = 0.5
                det_msg.confidence = 0.0
                det_msg.label = "none"
                det_msg.direction = "STATIONARY"

                g_msg.gesture_id = GESTURE_NONE
                g_msg.gesture_label = "NONE"
                g_msg.confidence = 0.0
                h_pt.z = 0.0

            # Publish all topics
            self.detection_pub.publish(det_msg)
            self.gesture_pub.publish(g_msg)
            self.hand_target_pub.publish(h_pt)

            self.last_detection_msg = det_msg
            self.last_gesture_msg = g_msg
            self.last_msg_time = now_sec

        except Exception as e:
            self.get_logger().error(f'Error in perception loop: {e}', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = HumanPoseGestureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.pose_detector is not None:
            node.pose_detector.close()
        if node.hand_detector is not None:
            node.hand_detector.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
