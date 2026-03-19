#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from gesture_interfaces.msg import Gesture
from collections import deque
import numpy as np

class FSMBrainNode(Node):
    def __init__(self):
        super().__init__('fsm_brain_node')
        self.declare_parameter('forward_speed', 0.3)
        self.declare_parameter('reverse_speed', -0.2)
        self.declare_parameter('safety_distance', 0.5)
        self.declare_parameter('filter_window', 5)
        self.declare_parameter('watchdog_timeout', 0.5)
        self.forward_speed = self.get_parameter('forward_speed').value
        self.reverse_speed = self.get_parameter('reverse_speed').value
        self.safety_distance = self.get_parameter('safety_distance').value
        self.filter_window = self.get_parameter('filter_window').value
        self.watchdog_timeout = self.get_parameter('watchdog_timeout').value

        self.gesture_sub = self.create_subscription(Gesture, '/gesture', self.gesture_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.gesture_history = deque(maxlen=self.filter_window)
        self.last_gesture_time = self.get_clock().now()
        self.obstacle_detected = False
        self.current_gesture_id = 0
        self.timer = self.create_timer(0.1, self.control_loop)

    def scan_callback(self, msg):
        angle_min = msg.angle_min
        angle_max = msg.angle_max
        angle_increment = msg.angle_increment
        ranges = np.array(msg.ranges)
        front_idx = int((0 - angle_min) / angle_increment)
        window = int((np.pi/6) / angle_increment)
        start = max(0, front_idx - window)
        end = min(len(ranges), front_idx + window + 1)
        front_ranges = ranges[start:end]
        front_ranges = front_ranges[np.isfinite(front_ranges)]
        if len(front_ranges) > 0 and np.min(front_ranges) < self.safety_distance:
            self.obstacle_detected = True
        else:
            self.obstacle_detected = False

    def gesture_callback(self, msg):
        if msg.confidence > 0.8:
            self.gesture_history.append(msg.gesture_id)
        else:
            self.gesture_history.append(0)
        self.last_gesture_time = self.get_clock().now()
        if len(self.gesture_history) == self.filter_window:
            counts = np.bincount(self.gesture_history)
            most_common = np.argmax(counts)
            if counts[most_common] >= self.filter_window // 2 + 1:
                self.current_gesture_id = most_common
            else:
                self.current_gesture_id = 0
        else:
            self.current_gesture_id = self.gesture_history[-1]

    def control_loop(self):
        time_since_last = (self.get_clock().now() - self.last_gesture_time).nanoseconds / 1e9
        if time_since_last > self.watchdog_timeout:
            self.current_gesture_id = 0
        twist = Twist()
        if self.obstacle_detected:
            if self.current_gesture_id == 1:
                twist.linear.x = self.reverse_speed
            else:
                twist.linear.x = 0.0
        else:
            if self.current_gesture_id == 1:
                twist.linear.x = self.forward_speed
            else:
                twist.linear.x = 0.0
        self.cmd_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = FSMBrainNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()