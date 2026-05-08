#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

class DirectDrive(Node):
    def __init__(self):
        super().__init__('direct_drive')
        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.left_pub = self.create_publisher(Float64, '/left_wheel_vel', 10)
        self.right_pub = self.create_publisher(Float64, '/right_wheel_vel', 10)
        self.wheel_separation = 0.25
        self.wheel_radius = 0.05

    def cmd_callback(self, msg):
        v = msg.linear.x
        w = msg.angular.z
        left_vel = (v - w * self.wheel_separation / 2) / self.wheel_radius
        right_vel = (v + w * self.wheel_separation / 2) / self.wheel_radius
        self.left_pub.publish(Float64(data=left_vel))
        self.right_pub.publish(Float64(data=right_vel))

def main(args=None):
    rclpy.init(args=args)
    node = DirectDrive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
