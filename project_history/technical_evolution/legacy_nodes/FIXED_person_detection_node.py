#!/usr/bin/env python3
"""
Person Detection Node - FIXED VERSION
All Priority 1 issues resolved:
- ✅ Uses package resource paths (not hardcoded)
- ✅ Headless mode parameter
- ✅ Configurable parameters
- ✅ Error handling
- ✅ Proper logging levels
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
import cv2
import numpy as np
from cv_bridge import CvBridge
import os

from sensor_msgs.msg import Image
from cognition_interfaces.msg import Detection
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory


class PersonDetectionNode(Node):
    def __init__(self):
        super().__init__('person_detection_node')
        
        # Parameters (NEW - all configurable)
        self.declare_parameter('headless', False)
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('frame_skip', 3)
        self.declare_parameter('use_sim_time', False)
        
        self.headless = self.get_parameter('headless').value
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.frame_skip = self.get_parameter('frame_skip').value
        
        # FIXED: Use package resource path instead of hardcoded
        try:
            package_share = get_package_share_directory('cognition_perception')
            model_path = os.path.join(package_share, 'models', 'yolov8n.pt')
            self.get_logger().info(f'Loading YOLO model from: {model_path}')
            self.model = YOLO(model_path)
            self.get_logger().info('✅ YOLO model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load YOLO model: {e}')
            self.get_logger().error(f'Expected path: {model_path}')
            raise
        
        self.bridge = CvBridge()
        
        # QoS for camera subscription (BEST_EFFORT for simulation compatibility)
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/image_raw', self.image_callback, qos)
        
        # Publishers
        self.detection_pub = self.create_publisher(Detection, '/cognition/detection', 10)
        
        # State
        self.frame_count = 0
        self.prev_center_x = None
        self.prev_center_y = None
        self.prev_time = None
        self.last_frame = None
        
        self.get_logger().info(
            f'Person Detection Node started (headless={self.headless}, '
            f'confidence_threshold={self.confidence_threshold}, frame_skip={self.frame_skip})'
        )
    
    def image_callback(self, msg):
        """Process camera images for person detection"""
        
        self.frame_count += 1
        
        # FIXED: Configurable frame skip (was hardcoded to 3)
        if self.frame_count % self.frame_skip != 0:
            return
        
        try:
            # Convert ROS Image to OpenCV
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.last_frame = frame.copy()
            
            # Run YOLO inference (person class only = 0)
            results = self.model(frame, classes=[0], verbose=False)
            
            # Extract best detection (highest confidence)
            best_box = None
            best_confidence = 0.0
            
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf > best_confidence:
                        best_confidence = conf
                        best_box = box
            
            # Build detection message
            detection_msg = Detection()
            detection_msg.stamp = self.get_clock().now().to_msg()
            
            # FIXED: Configurable confidence threshold (was hardcoded to 0.5)
            if best_box is not None and best_confidence > self.confidence_threshold:
                # Get bounding box (xywh format from YOLO)
                x, y, w, h = best_box.xywh[0]
                img_h, img_w = frame.shape[:2]
                
                # Normalize to [0, 1] range
                detection_msg.center_x = float(x / img_w)
                detection_msg.center_y = float(y / img_h)
                detection_msg.width = float(w / img_w)
                detection_msg.height = float(h / img_h)
                detection_msg.confidence = best_confidence
                detection_msg.label = 'person'
                
                # Calculate velocity (simple finite difference)
                current_time = self.get_clock().now().nanoseconds
                if self.prev_center_x is not None and self.prev_time is not None:
                    dt = (current_time - self.prev_time) / 1e9  # ns to seconds
                    if dt > 0:
                        vel_x = (detection_msg.center_x - self.prev_center_x) / dt
                        vel_y = (detection_msg.center_y - self.prev_center_y) / dt
                        self.get_logger().debug(
                            f'Velocity: vx={vel_x:.2f}, vy={vel_y:.2f}'
                        )
                
                # Update tracking state
                self.prev_center_x = detection_msg.center_x
                self.prev_center_y = detection_msg.center_y
                self.prev_time = current_time
                
                # FIXED: Only draw if not headless
                if not self.headless and self.last_frame is not None:
                    x1 = int(x - w/2)
                    y1 = int(y - h/2)
                    x2 = int(x + w/2)
                    y2 = int(y + h/2)
                    
                    # Draw bounding box
                    cv2.rectangle(self.last_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw label
                    label = f'Person {best_confidence:.2f}'
                    cv2.putText(self.last_frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                self.get_logger().debug(
                    f'Person detected: center=({detection_msg.center_x:.2f}, {detection_msg.center_y:.2f}), '
                    f'confidence={best_confidence:.2f}'
                )
            else:
                # No detection or below threshold
                detection_msg.center_x = 0.0
                detection_msg.center_y = 0.0
                detection_msg.width = 0.0
                detection_msg.height = 0.0
                detection_msg.confidence = 0.0
                detection_msg.label = 'none'
                
                # Reset velocity tracking
                self.prev_center_x = None
                self.prev_center_y = None
                self.prev_time = None
                
                self.get_logger().debug('No person detected')
            
            # Publish detection
            self.detection_pub.publish(detection_msg)
            
            # FIXED: Only show window if not headless
            if not self.headless and self.last_frame is not None:
                cv2.imshow('Person Detection Debug', self.last_frame)
                cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Detection error: {e}', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    
    node = None
    try:
        node = PersonDetectionNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info('Shutting down (Ctrl+C)')
    except Exception as e:
        if node:
            node.get_logger().error(f'Fatal error: {e}')
        else:
            print(f'Fatal error during node creation: {e}')
    finally:
        if node and not node.headless:
            cv2.destroyAllWindows()
        if node:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
