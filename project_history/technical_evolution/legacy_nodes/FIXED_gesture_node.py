#!/usr/bin/env python3
"""
Gesture Recognition Node - FIXED VERSION
Improvements:
- ✅ Headless mode parameter
- ✅ Configurable parameters
- ✅ Better error handling
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
import cv2
import numpy as np
from cv_bridge import CvBridge
import mediapipe as mp
import os

from sensor_msgs.msg import Image
from cognition_interfaces.msg import Gesture
from ament_index_python.packages import get_package_share_directory


class GestureNode(Node):
    
    # Gesture IDs (aligned across all nodes and models)
    GESTURE_NONE = -1
    GESTURE_BACK = 0
    GESTURE_FOLLOW = 1
    GESTURE_GO = 2
    GESTURE_LEFT = 3
    GESTURE_RIGHT = 4
    GESTURE_STOP = 5
    
    def __init__(self):
        super().__init__('gesture_node')
        
        # Parameters (NEW - configurable)
        self.declare_parameter('headless', False)
        self.declare_parameter('min_hand_size', 0.08)
        self.declare_parameter('use_sim_time', False)
        
        self.headless = self.get_parameter('headless').value
        self.min_hand_size = self.get_parameter('min_hand_size').value
        
        # FIXED: Load model from package resources
        try:
            package_share = get_package_share_directory('cognition_perception')
            model_path = os.path.join(package_share, 'models', 'hand_landmarker.task')
            
            self.get_logger().info(f'Loading MediaPipe model from: {model_path}')
            
            # MediaPipe Hand Landmarker setup
            BaseOptions = mp.tasks.BaseOptions
            HandLandmarker = mp.tasks.vision.HandLandmarker
            HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode
            
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=VisionRunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            self.detector = HandLandmarker.create_from_options(options)
            self.get_logger().info('✅ MediaPipe hand landmarker ready')
            
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load MediaPipe model: {e}')
            raise
        
        self.bridge = CvBridge()
        
        # QoS for camera
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/image_raw', self.image_callback, qos)
        
        # Publishers
        self.gesture_pub = self.create_publisher(Gesture, '/cognition/gesture', 10)
        
        self.get_logger().info(
            f'Gesture Node started (headless={self.headless}, min_hand_size={self.min_hand_size})'
        )
    
    def get_finger_states(self, landmarks, handedness):
        """
        Determine which fingers are extended
        Returns: [thumb, index, middle, ring, pinky] as boolean array
        """
        # Landmark indices for fingertips and bases
        tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        mcp = [2, 5, 9, 13, 17]    # Metacarpal joints
        
        fingers = []
        
        # Thumb (special case - check X coordinate)
        if handedness == 'Right':
            thumb_up = landmarks[tips[0]].x < landmarks[mcp[0]].x
        else:  # Left hand
            thumb_up = landmarks[tips[0]].x > landmarks[mcp[0]].x
        fingers.append(thumb_up)
        
        # Other fingers (check Y coordinate - tip above MCP = extended)
        for i in range(1, 5):
            finger_up = landmarks[tips[i]].y < landmarks[mcp[i]].y
            fingers.append(finger_up)
        
        return fingers
    
    def classify_gesture(self, landmarks, handedness):
        """
        Classify gesture based on hand landmarks
        Returns: (gesture_id, gesture_label, confidence)
        """
        fingers = self.get_finger_states(landmarks, handedness)
        thumb, index, middle, ring, pinky = fingers
        
        # STOP: All fingers up (open palm)
        if all([thumb, index, middle, ring, pinky]):
            return self.GESTURE_STOP, 'STOP', 0.95
        
        # GO: Only thumb up
        if thumb and not any([index, middle, ring, pinky]):
            return self.GESTURE_GO, 'GO', 0.95
        
        # FOLLOW: Index + middle up (peace sign)
        if not thumb and index and middle and not ring and not pinky:
            return self.GESTURE_FOLLOW, 'FOLLOW', 0.90
        
        # LEFT/RIGHT: Only index up
        if not thumb and index and not any([middle, ring, pinky]):
            # Determine direction from wrist to index finger
            wrist_x = landmarks[0].x
            index_x = landmarks[8].x
            
            if handedness == 'Right':
                if index_x < wrist_x:
                    return self.GESTURE_LEFT, 'LEFT', 0.90
                else:
                    return self.GESTURE_RIGHT, 'RIGHT', 0.90
            else:  # Left hand
                if index_x > wrist_x:
                    return self.GESTURE_LEFT, 'LEFT', 0.90
                else:
                    return self.GESTURE_RIGHT, 'RIGHT', 0.90
        
        # No recognized gesture
        return self.GESTURE_NONE, 'NONE', 0.0
    
    def image_callback(self, msg):
        """Process camera images for gesture recognition"""
        
        try:
            # Convert ROS Image to OpenCV
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Detect hands
            detection_result = self.detector.detect(mp_image)
            
            # Build gesture message
            gesture_msg = Gesture()
            gesture_msg.stamp = self.get_clock().now().to_msg()
            
            if detection_result.hand_landmarks:
                # Get first hand
                hand_landmarks = detection_result.hand_landmarks[0]
                handedness = detection_result.handedness[0][0].category_name
                
                # Calculate hand size (for filtering small/far hands)
                x_coords = [lm.x for lm in hand_landmarks]
                y_coords = [lm.y for lm in hand_landmarks]
                hand_size = max(max(x_coords) - min(x_coords),
                               max(y_coords) - min(y_coords))
                
                # FIXED: Configurable minimum hand size
                if hand_size > self.min_hand_size:
                    # Classify gesture
                    gesture_id, gesture_label, confidence = self.classify_gesture(
                        hand_landmarks, handedness
                    )
                    
                    gesture_msg.gesture_id = gesture_id
                    gesture_msg.gesture_label = gesture_label
                    gesture_msg.confidence = confidence
                    
                    # FIXED: Only draw if not headless
                    if not self.headless:
                        # Draw hand landmarks
                        for landmark in hand_landmarks:
                            x = int(landmark.x * frame.shape[1])
                            y = int(landmark.y * frame.shape[0])
                            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                        
                        # Draw gesture label
                        cv2.putText(frame, f'{gesture_label} ({confidence:.2f})',
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                   1, (0, 255, 0), 2)
                    
                    self.get_logger().debug(
                        f'Gesture: {gesture_label} (confidence={confidence:.2f})'
                    )
                else:
                    # Hand too small (too far away)
                    gesture_msg.gesture_id = self.GESTURE_NONE
                    gesture_msg.gesture_label = 'TOO_FAR'
                    gesture_msg.confidence = 0.0
                    
                    if not self.headless:
                        cv2.putText(frame, 'Hand too far', (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                # No hand detected
                gesture_msg.gesture_id = self.GESTURE_NONE
                gesture_msg.gesture_label = 'NO_HAND'
                gesture_msg.confidence = 0.0
                
                if not self.headless:
                    cv2.putText(frame, 'No hand detected', (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Publish gesture
            self.gesture_pub.publish(gesture_msg)
            
            # FIXED: Only show window if not headless
            if not self.headless:
                cv2.imshow('Gesture Recognition', frame)
                cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Gesture processing error: {e}', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    
    node = None
    try:
        node = GestureNode()
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
