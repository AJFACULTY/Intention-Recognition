#!/usr/bin/env python3
"""
face_recognition_node.py — Production ROS 2 Facial Recognition Node
Cognition Robot Project

Features:
- Subscribes to /camera/image_raw/compressed (sensor_msgs/CompressedImage)
- Extracts 512-d ArcFace embeddings via InsightFace buffalo_sc (MobileFaceNet)
- Compares against enrolled identities in known_embeddings.pkl via cosine distance
- Publishes identity events on /cognition/face_identity (JSON string)
- Publishes normalized target coordinates on /cognition/face_target (geometry_msgs/Point)
  for direct consumption by active_vision_node.py (Gimbal Tracking)
- Publishes optional annotated visual stream on /cognition/face_debug/compressed
- Dynamic path discovery: Zero hardcoded directories
- Auto-reload: Detects file modifications to known_embeddings.pkl and hot-reloads database
- CPU Throttling: Configurable inference_interval (default: 3) to skip frames and maintain low thermals
"""

import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy

from geometry_msgs.msg import Point
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

# Import shared InsightFace library
try:
    from .face_id_lib import (
        DEFAULT_DB_DIR,
        MATCH_THRESHOLD,
        best_match,
        get_faces,
        load_db,
        load_face_app,
    )
except ImportError:
    try:
        from face_id_lib import (
            DEFAULT_DB_DIR,
            MATCH_THRESHOLD,
            best_match,
            get_faces,
            load_db,
            load_face_app,
        )
    except ImportError:
        dev_path = os.path.expanduser("~/cognition_ws/face_id_dev")
        if os.path.exists(dev_path) and dev_path not in sys.path:
            sys.path.insert(0, dev_path)
        from face_id_lib import (
            DEFAULT_DB_DIR,
            MATCH_THRESHOLD,
            best_match,
            get_faces,
            load_db,
            load_face_app,
        )


def resolve_database_dir(configured_path: str = "") -> str:
    """Resolve face_data directory without hardcoded paths."""
    if configured_path and os.path.isdir(configured_path):
        return configured_path

    env_dir = os.environ.get("FACE_DB_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    user_home = os.path.expanduser("~")
    candidates = [
        os.path.join(user_home, "cognition_ws", "face_id_dev", "face_data"),
        os.path.join(user_home, "ros2_cognition_ws", "face_id_dev", "face_data"),
        os.path.join(user_home, ".cognition", "face_data"),
        os.path.join(os.getcwd(), "face_data"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    fallback = os.path.join(user_home, "cognition_ws", "face_id_dev", "face_data")
    os.makedirs(fallback, exist_ok=True)
    return fallback


class FaceRecognitionNode(Node):
    def __init__(self):
        super().__init__("face_recognition_node")

        self.declare_parameter("camera_topic", "/camera/image_raw/compressed")
        self.declare_parameter("db_dir", "")
        self.declare_parameter("match_threshold", MATCH_THRESHOLD)
        self.declare_parameter("inference_interval", 3)
        self.declare_parameter("enable_debug_image", True)
        self.declare_parameter("debug_topic", "/cognition/face_debug/compressed")

        self.camera_topic = self.get_parameter("camera_topic").value
        configured_db = self.get_parameter("db_dir").value
        self.db_dir = resolve_database_dir(configured_db)
        self.match_threshold = float(self.get_parameter("match_threshold").value)
        self.inference_interval = max(1, int(self.get_parameter("inference_interval").value))
        self.enable_debug = bool(self.get_parameter("enable_debug_image").value)
        self.debug_topic = self.get_parameter("debug_topic").value

        self.get_logger().info(f"Resolved Face DB Directory: {self.db_dir}")
        self.get_logger().info(f"Match Threshold: {self.match_threshold:.2f} | Inference Interval: every {self.inference_interval} frames")

        self.get_logger().info("Initializing InsightFace buffalo_sc engine (MobileFaceNet)...")
        try:
            self.app = load_face_app()
            self.get_logger().info("InsightFace engine successfully loaded.")
        except Exception as e:
            self.get_logger().error(f"Failed to load InsightFace engine: {e}")
            raise e

        self.db_file = os.path.join(self.db_dir, "known_embeddings.pkl")
        self.last_db_mtime = 0.0
        self.db = {}
        self.load_known_faces()

        self.identity_pub = self.create_publisher(String, "/cognition/face_identity", 10)
        self.target_pub = self.create_publisher(Point, "/cognition/face_target", 10)

        if self.enable_debug:
            self.debug_pub = self.create_publisher(CompressedImage, self.debug_topic, 10)

        self.frame_counter = 0
        self.last_target_point = Point(x=0.0, y=0.0, z=-1.0)
        self.last_identity_json = ""

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.sub_cam = self.create_subscription(
            CompressedImage,
            self.camera_topic,
            self.image_callback,
            qos_profile,
        )

        self.create_timer(5.0, self.check_db_update)
        self.get_logger().info(f"Subscribed to {self.camera_topic}. Ready for face recognition.")

    def load_known_faces(self):
        if os.path.exists(self.db_file):
            try:
                self.db = load_db(self.db_dir)
                self.last_db_mtime = os.path.getmtime(self.db_file)
                identities = list(self.db.keys())
                self.get_logger().info(f"Loaded {len(identities)} enrolled identities: {identities}")
            except Exception as e:
                self.get_logger().warn(f"Error loading {self.db_file}: {e}")
        else:
            self.get_logger().warn(f"No database file found at {self.db_file}. Enrolled faces list is currently empty.")
            self.db = {}

    def check_db_update(self):
        if os.path.exists(self.db_file):
            current_mtime = os.path.getmtime(self.db_file)
            if current_mtime > self.last_db_mtime:
                self.get_logger().info("Detected update to known_embeddings.pkl. Hot-reloading database...")
                self.load_known_faces()

    def image_callback(self, msg: CompressedImage):
        self.frame_counter += 1

        if (self.frame_counter % self.inference_interval) != 0:
            if self.last_target_point.z > 0:
                self.target_pub.publish(self.last_target_point)
            return

        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                return
        except Exception as e:
            self.get_logger().warn(f"JPEG decompression failed: {e}")
            return

        h, w = frame.shape[:2]
        c_x, c_y = w / 2.0, h / 2.0

        faces = get_faces(self.app, frame)

        if not faces:
            if self.enable_debug:
                self.publish_debug_frame(frame)
            return

        faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
        primary_face = faces[0]

        name, score = best_match(primary_face.normed_embedding, self.db)
        is_authorized = bool(name is not None and score >= self.match_threshold)

        x1, y1, x2, y2 = [int(v) for v in primary_face.bbox]
        centroid_x = (x1 + x2) / 2.0
        centroid_y = (y1 + y2) / 2.0

        norm_u = float((centroid_x - c_x) / c_x)
        norm_v = float((centroid_y - c_y) / c_y)

        target = Point(x=norm_u, y=norm_v, z=float(score if score > 0 else 0.05))
        self.target_pub.publish(target)
        self.last_target_point = target

        identity_payload = {
            "name": name if name else "Unknown",
            "score": round(float(score), 4),
            "authorized": is_authorized,
            "bbox": [x1, y1, x2, y2],
            "centroid": [round(centroid_x, 1), round(centroid_y, 1)],
            "centroid_norm": [round(norm_u, 4), round(norm_v, 4)],
            "face_count": len(faces),
            "timestamp": time.time(),
        }
        identity_msg = String()
        identity_msg.data = json.dumps(identity_payload)
        self.identity_pub.publish(identity_msg)

        if self.enable_debug:
            for i, face in enumerate(faces):
                bx1, by1, bx2, by2 = [int(v) for v in face.bbox]
                f_name, f_score = best_match(face.normed_embedding, self.db)
                f_auth = bool(f_name is not None and f_score >= self.match_threshold)

                color = (0, 255, 0) if f_auth else (0, 0, 255)
                label = f"{f_name} ({f_score:.2f})" if f_name else f"Unknown ({f_score:.2f})"

                cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (bx1, max(20, by1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                )

            cv2.circle(frame, (int(c_x), int(c_y)), 6, (255, 255, 255), 1)
            cv2.circle(frame, (int(centroid_x), int(centroid_y)), 5, (0, 255, 255), -1)
            cv2.line(frame, (int(c_x), int(c_y)), (int(centroid_x), int(centroid_y)), (0, 255, 255), 1)

            self.publish_debug_frame(frame)

    def publish_debug_frame(self, frame):
        try:
            success, encoded_image = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                debug_msg = CompressedImage()
                debug_msg.header.stamp = self.get_clock().now().to_msg()
                debug_msg.format = "jpeg"
                debug_msg.data = encoded_image.tobytes()
                self.debug_pub.publish(debug_msg)
        except Exception as e:
            self.get_logger().debug(f"Failed to publish debug image: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = FaceRecognitionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
