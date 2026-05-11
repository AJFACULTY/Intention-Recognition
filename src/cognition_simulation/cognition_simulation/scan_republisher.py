import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class ScanRepublisher(Node):
    def __init__(self):
        super().__init__('scan_republisher')
        self.sub = self.create_subscription(
            LaserScan, '/scan', self.callback, 10)
        self.pub = self.create_publisher(
            LaserScan, '/scan_fixed', 10)
        self.get_logger().info('Republishing /scan -> /scan_fixed with frame_id=laser_frame')

    def callback(self, msg):
        msg.header.frame_id = 'laser_frame'
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ScanRepublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
