#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import mediapipe as mp
import numpy as np
import urllib.request
import os
from gesture_interfaces.msg import Gesture

# URL for Hand Landmarker model (float16 version)
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "/tmp/hand_landmarker.task"

# Download the model if not already present
if not os.path.exists(MODEL_PATH):
    print("Downloading hand landmarker model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Download complete.")

# Configure MediaPipe Tasks
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1
)

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.publisher_ = self.create_publisher(Gesture, '/gesture', 10)
        self.timer = self.create_timer(0.033, self.timer_callback)  # ~30 fps
        self.cap = cv2.VideoCapture(0)
        self.landmarker = HandLandmarker.create_from_options(options)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert to MediaPipe Image
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Detect hand landmarks
        detection_result = self.landmarker.detect(mp_image)

        gesture_id = 0      # 0 = unknown, 1 = fist, 2 = palm
        confidence = 0.0

        if detection_result.hand_landmarks:
            hand_landmarks = detection_result.hand_landmarks[0]
            # Landmark indices: 8 = index fingertip, 6 = index finger PIP joint
            tip = hand_landmarks[8]
            knuckle = hand_landmarks[6]

            # Simple rule: tip y smaller (higher) than knuckle → fist
            if tip.y < knuckle.y:
                gesture_id = 1   # fist
            else:
                gesture_id = 2   # palm

            # Use handedness score if available, else default 0.9
            if detection_result.handedness:
                confidence = detection_result.handedness[0][0].score
            else:
                confidence = 0.9

            # Draw landmarks (green circles)
            for landmark in hand_landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

        # Determine text for overlay
        if gesture_id == 1:
            gesture_name = "FIST (forward)"
            color = (0, 255, 0)      # green
        elif gesture_id == 2:
            gesture_name = "PALM (stop)"
            color = (0, 0, 255)      # red
        else:
            gesture_name = "UNKNOWN"
            color = (255, 255, 255)  # white

        # Put text on frame
        cv2.putText(frame, gesture_name, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # Publish gesture message
        msg = Gesture()
        msg.gesture_id = gesture_id
        msg.confidence = confidence
        msg.stamp = self.get_clock().now().to_msg()
        self.publisher_.publish(msg)

        # Show frame
        cv2.imshow('Vision Node', frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.landmarker.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()