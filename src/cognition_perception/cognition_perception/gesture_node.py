import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from cognition_interfaces.msg import Gesture
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import cv2
import numpy as np
import os

GESTURE_NONE   = 0
GESTURE_STOP   = 1
GESTURE_GO     = 2
GESTURE_LEFT   = 3
GESTURE_RIGHT  = 4
GESTURE_FOLLOW = 5

MODEL_PATH = os.path.expanduser(
    '~/cognition_ws/src/cognition_perception/cognition_perception/models/hand_landmarker.task'
)


class GestureNode(Node):
    def __init__(self):
        super().__init__('gesture_node')
        self.publisher = self.create_publisher(Gesture, '/cognition/gesture', 10)
        self.subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        self.bridge = CvBridge()
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = mp_vision.HandLandmarker.create_from_options(options)
        self.get_logger().info('GestureNode started — listening on /camera/image_raw')

    def get_finger_states(self, landmarks, handedness='Right'):
        fingers = []
        tips = [4, 8, 12, 16, 20]
        mcp  = [2, 5, 9, 13, 17]
        if handedness == 'Right':
            fingers.append(landmarks[tips[0]].x < landmarks[mcp[0]].x)
        else:
            fingers.append(landmarks[tips[0]].x > landmarks[mcp[0]].x)
        for i in range(1, 5):
            fingers.append(landmarks[tips[i]].y < landmarks[mcp[i]].y)
        return fingers

    def classify_gesture(self, landmarks, handedness='Right'):
        f = self.get_finger_states(landmarks, handedness)
        if not f[0] and f[1] and not f[2] and not f[3] and not f[4]:
            wrist_x = landmarks[0].x
            wrist_y = landmarks[0].y
            index_tip_x = landmarks[8].x
            index_tip_y = landmarks[8].y
            horizontal = abs(index_tip_y - wrist_y) < abs(index_tip_x - wrist_x)
            if horizontal:
                if index_tip_x < wrist_x:
                    return GESTURE_LEFT, 'LEFT', 0.90
                else:
                    return GESTURE_RIGHT, 'RIGHT', 0.90
        if all(f):
            return GESTURE_STOP, 'STOP', 0.95
        if f[0] and not f[1] and not f[2] and not f[3] and not f[4]:
            return GESTURE_GO, 'GO', 0.95
        if not f[0] and f[1] and f[2] and not f[3] and not f[4]:
            return GESTURE_FOLLOW, 'FOLLOW', 0.90
        return GESTURE_NONE, 'NONE', 0.0

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.detector.detect(mp_image)
        gesture_msg = Gesture()
        gesture_msg.stamp = self.get_clock().now().to_msg()
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            x_coords = [lm.x for lm in landmarks]
            y_coords = [lm.y for lm in landmarks]
            hand_size = max(max(x_coords) - min(x_coords),
                            max(y_coords) - min(y_coords))
            if hand_size < 0.08:
                gesture_msg.gesture_id    = GESTURE_NONE
                gesture_msg.gesture_label = 'TOO_FAR'
                gesture_msg.confidence    = 0.0
                self.publisher.publish(gesture_msg)
                cv2.putText(frame, 'TOO FAR', (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
                cv2.imshow('Gesture Debug', frame)
                cv2.waitKey(1)
                return
            handedness = 'Right'
            if result.handedness:
                handedness = result.handedness[0][0].display_name
            g_id, g_label, confidence = self.classify_gesture(landmarks, handedness)
            gesture_msg.gesture_id    = g_id
            gesture_msg.gesture_label = g_label
            gesture_msg.confidence    = confidence
            h, w, _ = frame.shape
            for connection in [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                               (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),
                               (15,16),(0,17),(17,18),(18,19),(19,20)]:
                pt1 = (int(landmarks[connection[0]].x * w),
                       int(landmarks[connection[0]].y * h))
                pt2 = (int(landmarks[connection[1]].x * w),
                       int(landmarks[connection[1]].y * h))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
            for lm in landmarks:
                cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 5, (255, 0, 0), -1)
        else:
            gesture_msg.gesture_id    = GESTURE_NONE
            gesture_msg.gesture_label = 'NONE'
            gesture_msg.confidence    = 0.0
        self.publisher.publish(gesture_msg)
        cv2.putText(frame, gesture_msg.gesture_label, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.imshow('Gesture Debug', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            raise KeyboardInterrupt


def main(args=None):
    rclpy.init(args=args)
    node = GestureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.detector.close()
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
