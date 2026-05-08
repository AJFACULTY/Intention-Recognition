import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from cognition_interfaces.msg import Detection
from ultralytics import YOLO
import cv2
import os

os.environ['YOLO_VERBOSE'] = 'False'


class PersonDetectionNode(Node):
    def __init__(self):
        super().__init__('person_detection_node')
        self.publisher = self.create_publisher(Detection, '/cognition/detection', 10)
        self.subscription = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.bridge = CvBridge()
        self.model = YOLO(os.path.expanduser(
            '~/cognition_ws/src/cognition_perception/cognition_perception/models/yolov8n.pt'))
        self.person_class_id = 0
        self.prev_center_x = None
        self.prev_center_y = None
        self.prev_time = None
        self.frame_count = 0
        self.last_frame = None
        self.get_logger().info('PersonDetectionNode started')

    def image_callback(self, msg):
        self.frame_count += 1
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        h, w = frame.shape[:2]

        if self.frame_count % 3 != 0:
            if self.last_frame is not None:
                cv2.imshow('Person Detection Debug', self.last_frame)
                cv2.waitKey(1)
            return

        results = self.model(frame, classes=[self.person_class_id], verbose=False)
        detection_msg = Detection()
        detection_msg.stamp = self.get_clock().now().to_msg()
        best_confidence = 0.0
        best_box = None

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf > best_confidence:
                    best_confidence = conf
                    best_box = box

        if best_box is not None and best_confidence > 0.5:
            x1, y1, x2, y2 = best_box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            center_x = ((x1 + x2) / 2) / w
            center_y = ((y1 + y2) / 2) / h
            current_time = self.get_clock().now().nanoseconds
            vel_x, vel_y = 0.0, 0.0
            if self.prev_center_x is not None and self.prev_time is not None:
                dt = (current_time - self.prev_time) / 1e9
                if dt > 0:
                    vel_x = (center_x - self.prev_center_x) / dt
                    vel_y = (center_y - self.prev_center_y) / dt
            self.prev_center_x = center_x
            self.prev_center_y = center_y
            self.prev_time = current_time
            detection_msg.center_x = center_x
            detection_msg.center_y = center_y
            detection_msg.width = (x2 - x1) / w
            detection_msg.height = (y2 - y1) / h
            detection_msg.confidence = best_confidence
            detection_msg.label = 'person'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'Person {best_confidence:.2f}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cx = int(center_x * w)
            cy = int(center_y * h)
            cv2.circle(frame, (cx, cy), 6, (255, 0, 0), -1)
            if vel_x != 0 or vel_y != 0:
                arrow_scale = 50
                end_x = max(0, min(w - 1, int(cx + vel_x * arrow_scale)))
                end_y = max(0, min(h - 1, int(cy + vel_y * arrow_scale)))
                cv2.arrowedLine(frame, (cx, cy), (end_x, end_y), (0, 165, 255), 2)
        else:
            detection_msg.label = 'none'
            detection_msg.confidence = 0.0
            self.prev_center_x = None
            self.prev_center_y = None
            self.prev_time = None
            cv2.putText(frame, 'No person', (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        self.publisher.publish(detection_msg)
        self.last_frame = frame.copy()
        cv2.imshow('Person Detection Debug', frame)
        key =cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            raise KeyboardInterrupt


def main(args=None):
    rclpy.init(args=args)
    node = PersonDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
