import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from cognition_interfaces.msg import Gesture, Detection

GESTURE_NONE   = 0
GESTURE_STOP   = 1
GESTURE_GO     = 2
GESTURE_LEFT   = 3
GESTURE_RIGHT  = 4
GESTURE_FOLLOW = 5


class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # Publishers — TwistStamped for TurtleBot4
        self.cmd_vel_pub = self.create_publisher(
            TwistStamped, '/cmd_vel', 10)

        # Subscribers
        self.gesture_sub = self.create_subscription(
            Gesture, '/cognition/gesture', self.gesture_callback, 10)
        self.detection_sub = self.create_subscription(
            Detection, '/cognition/detection', self.detection_callback, 10)

        # State
        self.current_gesture = GESTURE_NONE
        self.gesture_buffer = []
        self.buffer_size = 5
        self.person_detected = False
        self.person_center_x = 0.5
        self.person_width = 0.0

        # Control loop at 10Hz
        self.timer = self.create_timer(0.1, self.control_loop)

        # Speed parameters
        self.linear_speed  = 0.3
        self.angular_speed = 0.5
        self.follow_speed  = 0.2

        self.get_logger().info('BrainNode started — service robot mode')

    def gesture_callback(self, msg):
        self.gesture_buffer.append(msg.gesture_id)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)
        if self.gesture_buffer.count(msg.gesture_id) >= 3:
            if self.current_gesture != msg.gesture_id:
                self.current_gesture = msg.gesture_id
                self.get_logger().info(f'Gesture confirmed: {msg.gesture_label}')

    def detection_callback(self, msg):
        if msg.label == 'person' and msg.confidence > 0.5:
            self.person_detected = True
            self.person_center_x = msg.center_x
            self.person_width = msg.width
        else:
            self.person_detected = False

    def make_cmd(self, linear_x=0.0, angular_z=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_link'
        cmd.twist.linear.x  = linear_x
        cmd.twist.angular.z = angular_z
        return cmd

    def control_loop(self):
        if self.current_gesture == GESTURE_STOP:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
            self.get_logger().info('CMD: STOP', throttle_duration_sec=1.0)

        elif self.current_gesture == GESTURE_GO:
            self.cmd_vel_pub.publish(self.make_cmd(self.linear_speed, 0.0))
            self.get_logger().info('CMD: GO', throttle_duration_sec=1.0)

        elif self.current_gesture == GESTURE_LEFT:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, self.angular_speed))
            self.get_logger().info('CMD: LEFT', throttle_duration_sec=1.0)

        elif self.current_gesture == GESTURE_RIGHT:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, -self.angular_speed))
            self.get_logger().info('CMD: RIGHT', throttle_duration_sec=1.0)

        elif self.current_gesture == GESTURE_FOLLOW:
            if self.person_detected:
                error = self.person_center_x - 0.5
                if self.person_width > 0.4:
                    self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
                    self.get_logger().info(
                        'CMD: FOLLOW — holding', throttle_duration_sec=1.0)
                else:
                    self.cmd_vel_pub.publish(
                        self.make_cmd(self.follow_speed, -error * 1.5))
                    self.get_logger().info(
                        'CMD: FOLLOW — tracking', throttle_duration_sec=1.0)
            else:
                self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.2))
                self.get_logger().info(
                    'CMD: FOLLOW — searching', throttle_duration_sec=1.0)
        else:
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_vel_pub.publish(node.make_cmd(0.0, 0.0))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
