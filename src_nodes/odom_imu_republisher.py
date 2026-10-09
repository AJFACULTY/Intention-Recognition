#!/usr/bin/env python3
"""
odom_imu_republisher.py

Re-stamps /odom_raw and /imu messages with this node's own clock at the
moment of receipt, instead of trusting the ESP32's onboard clock.

Why this exists:
The ESP32 (via the micro-ROS agent) publishes /odom_raw and /imu with
header.stamp values taken from its own onboard clock, which has been
observed to drift by hours relative to the Pi's system clock. EKF
(robot_localization) uses header.stamp for time-ordering and prediction;
a large, systematic offset causes it to treat incoming messages as
stale, which starves its effective output rate even though the raw
topics are being published at a healthy frequency.

This mirrors the existing fix already applied to /scan in
scan_republisher.py (same package), which solved the same class of
problem for LiDAR data. This node applies the identical fix to the two
remaining ESP32-sourced topics that feed EKF.

Subscribes:
    /odom_raw   (nav_msgs/msg/Odometry)
    /imu        (sensor_msgs/msg/Imu)

Publishes:
    /odom_raw_restamped   (nav_msgs/msg/Odometry)
    /imu_restamped        (sensor_msgs/msg/Imu)

Only header.stamp is modified. All other fields, including frame_id,
are passed through unchanged.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu


class OdomImuRepublisher(Node):
    """Restamps /odom_raw and /imu with the Pi's clock at receipt time."""

    def __init__(self):
        super().__init__('odom_imu_republisher')

        # Match the QoS the ESP32 bridge actually publishes with (RELIABLE,
        # per `ros2 topic info /odom_raw --verbose`), so we don't introduce
        # a new QoS mismatch of our own.
        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # EKF subscribes BEST_EFFORT (confirmed via `ros2 topic info`), so
        # publish with the same depth/history but let RELIABLE default
        # remain compatible either way.
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.odom_pub = self.create_publisher(
            Odometry, '/odom_raw_restamped', pub_qos)
        self.imu_pub = self.create_publisher(
            Imu, '/imu_restamped', pub_qos)

        self.odom_sub = self.create_subscription(
            Odometry, '/odom_raw', self.odom_callback, sub_qos)
        self.imu_sub = self.create_subscription(
            Imu, '/imu', self.imu_callback, sub_qos)

        self._odom_count = 0
        self._imu_count = 0

        # Periodic low-noise status log, same spirit as scan_republisher's
        # startup log line, so this node's presence/activity is visible in
        # `docker logs` / launch output without spamming per-message.
        self.create_timer(10.0, self._log_status)

        self.get_logger().info(
            'OdomImuRepublisher: /odom_raw -> /odom_raw_restamped, '
            '/imu -> /imu_restamped (re-stamped with Pi clock on receipt)'
        )

    def odom_callback(self, msg: Odometry) -> None:
        msg.header.stamp = self.get_clock().now().to_msg()
        self.odom_pub.publish(msg)
        self._odom_count += 1

    def imu_callback(self, msg: Imu) -> None:
        msg.header.stamp = self.get_clock().now().to_msg()
        self.imu_pub.publish(msg)
        self._imu_count += 1

    def _log_status(self) -> None:
        self.get_logger().info(
            f'odom_imu_republisher: relayed {self._odom_count} odom, '
            f'{self._imu_count} imu messages in last window'
        )
        self._odom_count = 0
        self._imu_count = 0


def main(args=None):
    rclpy.init(args=args)
    node = OdomImuRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
