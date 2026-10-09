#!/usr/bin/env python3
"""
slam_real.launch.py

FIX (2026-08-10): Enabled odom yaw in EKF's odom0_config.

Evidence gathered before this change (see yaw_investigation.sh output,
2026-08-10):
  1. History check: backup files (pi5_sim.launch.py.bak and
     .backup_fixes_20260520) show odom yaw ENABLED as the standard
     pattern used elsewhere in this project. No commit, comment, or
     history entry anywhere indicates it was deliberately disabled for
     real hardware for a specific reason -- most likely just copied
     from a different template as False.
  2. Live data check: captured /odom_raw continuously through a real,
     hand-driven ~720 degree rotation (two directions). Orientation.z
     and .w traced a smooth, continuous, correctly-behaving sinusoidal
     path with proper sign-flip wraparound near +/-180 degrees -- no
     jumps, freezes, or discontinuities. This is genuine, trustworthy
     data.
  3. Covariance check: odom's yaw variance reports as exactly 0.0,
     which is unusual, but weighed against check 2's clean data trace,
     this reads as the ESP32 firmware not populating covariance
     properly -- a reporting gap, not a data-quality problem.

Previously, EKF fused ONLY integrated gyro angular velocity for heading
(imu0_config vyaw=True), with no absolute heading reference at all --
classic dead-reckoning drift, worst during turns. This matches the
"hourglass" / rotated-segment drift pattern seen in both prior mapping
attempts (room_map_v1, room_map_20260810_0452, and the re-drive after
it). Odom yaw now provides that missing absolute reference; IMU's
angular velocity remains enabled too -- EKF fuses both as intended
(slow-but-absolute + fast-but-relative), this is the standard, correct
approach, not a replacement of one source with another.

The odom_tf fix from earlier (removed conflicting static transform
broadcaster) is UNCHANGED and remains in place below.
"""
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    # Static TF: base_footprint -> laser_frame (0.079m z offset)
    # Genuine fixed mechanical offset -- unchanged, no conflict.
    laser_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='laser_tf',
        arguments=['0', '0', '0.079', '0', '0', '0', 'base_footprint', 'laser_frame'],
        output='screen'
    )

    # Scan re-stamper
    scan_restamper = Node(
        package='cognition_simulation',
        executable='scan_republisher',
        name='scan_republisher',
        output='screen'
    )

    # Odom/IMU re-stamper (fixes ESP32 clock drift feeding EKF)
    odom_imu_restamper = Node(
        package='cognition_simulation',
        executable='odom_imu_republisher',
        name='odom_imu_republisher',
        output='screen'
    )

    # EKF -- sole broadcaster of odom_frame -> base_footprint.
    # odom0_config yaw (position 6) now TRUE -- was False. This is the
    # only change from the previous version of this file.
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'frequency': 12.5,
            'sensor_timeout': 0.1,
            'two_d_mode': True,
            'publish_tf': True,
            'odom_frame': 'odom_frame',
            'base_link_frame': 'base_footprint',
            'world_frame': 'odom_frame',
            'odom0': '/odom_raw_restamped',
            # [x, y, z, roll, pitch, yaw, vx, vy, vz, vroll, vpitch, vyaw, ax, ay, az]
            'odom0_config': [True, True, False, False, False, True, True, True, False, False, False, False, False, False, False],
            'odom0_differential': False,
            'odom0_relative': False,
            'imu0': '/imu_restamped',
            'imu0_config': [False, False, False, False, False, False, False, False, False, True, True, True, True, True, True],
            'imu0_differential': False,
            'imu0_remove_gravitational_acceleration': True,
        }]
    )

    # SLAM Toolbox -- delayed 3s so EKF has published at least one
    # transform before slam_toolbox's message filter starts looking for it.
    slam = TimerAction(
        period=3.0,
        actions=[Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=['/root/cognition_ws/src/cognition_simulation/config/slam_toolbox_real.yaml']
        )]
    )

    return LaunchDescription([laser_tf, scan_restamper, odom_imu_restamper, ekf, slam])
