#!/usr/bin/env python3
"""
nav2.launch.py  -- Nav2 AMCL localisation stack (pre-built map required)

FIX (2026-08-12): Now starts the sensor/transform chain (laser_tf,
scan_republisher, odom_imu_republisher, EKF) alongside Nav2's own nodes.
Previously this launch file only started Nav2 itself -- with no scan
data or odom_frame->base_footprint transform being published, AMCL and
both costmaps had nothing to localize or plan against. This mirrors
slam_real.launch.py's chain exactly, minus slam_toolbox (AMCL replaces
that role: localizing against a pre-built map instead of building one).

Also fixed in nav2_params.yaml (not this file): 3x /scan_fixed
references corrected to /scan_downsampled (the real topic name), and
bt_navigator's odom_topic corrected from raw /odom_raw to the fused
/odometry/filtered.

Found via 6_check_nav2_config_consistency.sh audit, 2026-08-12.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction, ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    ws_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Dynamic parameter file discovery
    possible_params = [
        os.path.join(ws_dir, 'config', 'nav2_params.yaml'),
        '/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml',
        '/root/cognition_ws/nav2_params.yaml',
        '/home/pi/cognition_ws/config/nav2_params.yaml',
    ]
    params = next((p for p in possible_params if os.path.exists(p)), possible_params[0])

    # Dynamic map file discovery
    possible_maps = [
        os.path.join(ws_dir, 'maps', 'room_map_20260812_0826.yaml'),
        os.path.join(ws_dir, 'maps_new', 'room_map_20260812_0826.yaml'),
        '/root/cognition_ws/maps_new/room_map_20260812_0826.yaml',
        '/root/cognition_ws/maps/room_map_20260812_0826.yaml',
        '/home/pi/maps_new/room_map_20260812_0826.yaml',
        '/home/pi/maps/room_map_20260812_0826.yaml',
    ]
    map_yaml = next((m for m in possible_maps if os.path.exists(m)), possible_maps[0])
    sim_time = {'use_sim_time': False}

    # --- Sensor / transform chain (same as slam_real.launch.py, minus slam_toolbox) ---

    laser_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='laser_tf',
        arguments=['0', '0', '0.079', '0', '0', '0', 'base_footprint', 'laser_frame'],
        output='screen'
    )

    base_link_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'base_link'],
        output='screen'
    )

    scan_restamper = Node(
        package='cognition_simulation',
        executable='scan_republisher',
        name='scan_republisher',
        output='screen'
    )

    odom_imu_restamper = Node(
        package='cognition_simulation',
        executable='odom_imu_republisher',
        name='odom_imu_republisher',
        output='screen'
    )

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
            'odom0_config': [True, True, False, False, False, True, True, True, False, False, False, False, False, False, False],
            'odom0_differential': False,
            'odom0_relative': False,
            'imu0': '/imu_restamped',
            'imu0_config': [False, False, False, False, False, False, False, False, False, True, True, True, True, True, True],
            'imu0_differential': False,
            'imu0_remove_gravitational_acceleration': True,
        }]
    )

    # --- Nav2 stack, delayed to let the sensor chain establish first ---

    map_server = Node(
        package='nav2_map_server', executable='map_server',
        name='map_server', output='screen',
        parameters=[{'yaml_filename': map_yaml, 'use_sim_time': False}])

    amcl = TimerAction(period=4.0, actions=[Node(
        package='nav2_amcl', executable='amcl',
        name='amcl', output='screen',
        parameters=[params, sim_time])])

    planner = TimerAction(period=5.0, actions=[Node(
        package='nav2_planner', executable='planner_server',
        name='planner_server', output='screen',
        parameters=[params, sim_time])])

    controller = TimerAction(period=5.0, actions=[Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=[params, sim_time])])

    behaviors = TimerAction(period=5.0, actions=[Node(
        package='nav2_behaviors', executable='behavior_server',
        name='behavior_server', output='screen',
        parameters=[params, sim_time])])

    bt_navigator = TimerAction(period=5.0, actions=[Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[params, sim_time])])

    waypoint = TimerAction(period=5.0, actions=[Node(
        package='nav2_waypoint_follower', executable='waypoint_follower',
        name='waypoint_follower', output='screen',
        parameters=[params, sim_time])])

    lifecycle_manager = TimerAction(period=6.0, actions=[Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'bond_timeout': 4.0,
            'node_names': [
                'map_server', 'amcl',
                'planner_server', 'controller_server',
                'behavior_server', 'bt_navigator', 'waypoint_follower',
            ],
        }])])

    initial_pose_cmd = TimerAction(
        period=10.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2', 'topic', 'pub', '--once', '/initialpose',
                'geometry_msgs/msg/PoseWithCovarianceStamped',
                ('{header: {frame_id: map}, pose: {pose: {position: '
                 '{x: 0.08, y: 0.05, z: 0.0}, orientation: {w: 1.0}}, '
                 'covariance: [0.25,0,0,0,0,0,0,0.25,0,0,0,0,0,0,0,0,0,0,'
                 '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.068]}}'),
            ],
            output='screen'
        )])

    return LaunchDescription([
        laser_tf, base_link_tf, scan_restamper, odom_imu_restamper, ekf,
        map_server, amcl, planner, controller,
        behaviors, bt_navigator, waypoint, lifecycle_manager,
        initial_pose_cmd,
    ])