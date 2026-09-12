#!/usr/bin/env python3
"""
demo_system.launch.py — Turnkey Demonstration & Defense Master Launcher
======================================================================
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Authors: Eleana Osei Owusu & Joel Nii Adjetey Ahulu
Institution: Ghana Communication Technology University (GCTU)

Launches the complete, unified Cognition stack for live thesis evaluation:
  1. Sensor & TF Transform Chain (laser_tf, base_link_tf, restampers, EKF)
  2. Full Perception & Gesture Cognition Pipeline (Camera, YOLO, MediaPipe, Brain)
  3. Nav2 Navigation Stack & AMCL Localization (Calibrated Room Map)
  4. Real-Time Web Map Visualizer Dashboard (HTTP Port 8080)

Usage:
  # Master Turnkey Demo (Full Autonomy + Nav2 + Live Web Map):
  ros2 launch launch/demo_system.launch.py

  # Pure Gesture Control & Human-Following Mode:
  ros2 launch launch/demo_system.launch.py mode:=gesture with_nav2:=false

  # Pure Nav2 Waypoint Navigation Mode:
  ros2 launch launch/demo_system.launch.py mode:=patrol with_cognition:=false
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── 1. Declare Configurable Arguments ──
    declare_mode = DeclareLaunchArgument(
        'mode', default_value='full',
        description='Operational mode: full (default), patrol, or gesture'
    )
    declare_with_nav2 = DeclareLaunchArgument(
        'with_nav2', default_value='true',
        description='Launch Nav2 and AMCL metric localization stack'
    )
    declare_with_cognition = DeclareLaunchArgument(
        'with_cognition', default_value='true',
        description='Launch Camera, MediaPipe gesture cognition, and Brain node'
    )
    declare_with_visualizer = DeclareLaunchArgument(
        'with_visualizer', default_value='true',
        description='Launch live HTTP map visualizer dashboard on port 8080'
    )
    declare_map_yaml = DeclareLaunchArgument(
        'map_yaml',
        default_value='/root/cognition_ws/maps_new/room_map_20260812_0826.yaml',
        description='Absolute path to calibrated room map YAML file'
    )
    declare_nav2_params = DeclareLaunchArgument(
        'nav2_params',
        default_value='/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml',
        description='Path to Nav2 parameter configuration file'
    )
    declare_headless = DeclareLaunchArgument(
        'headless', default_value='true',
        description='Run perception nodes in headless mode without local GUI'
    )
    declare_face_auth = DeclareLaunchArgument(
        'require_face_auth', default_value='false',
        description='Require enrolled ArcFace face ID authorization before gestures execute'
    )
    declare_cmd_vel_topic = DeclareLaunchArgument(
        'cmd_vel_topic', default_value='/cmd_vel',
        description='Target velocity topic (/cmd_vel for direct, /cmd_vel_gesture for mux)'
    )

    with_nav2 = LaunchConfiguration('with_nav2')
    with_cognition = LaunchConfiguration('with_cognition')
    with_visualizer = LaunchConfiguration('with_visualizer')
    map_yaml = LaunchConfiguration('map_yaml')
    nav2_params = LaunchConfiguration('nav2_params')
    headless = LaunchConfiguration('headless')
    require_face_auth = LaunchConfiguration('require_face_auth')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    # ── 2. Sensor & Transform Chain (Foundational for both Nav2 and SLAM) ──
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

    ekf_node = Node(
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

    # ── 3. Perception & Cognition Pipeline ──
    camera_node = Node(
        package='cognition_perception',
        executable='camera_pub',
        name='camera_publisher',
        parameters=[{
            'device_index': -1,
            'publish_fps': 20.0,
            'capture_width': 640,
            'capture_height': 480,
            'output_width': 320,
            'output_height': 240,
            'jpeg_quality': 80,
        }],
        output='screen',
        condition=IfCondition(with_cognition)
    )

    person_det_node = Node(
        package='cognition_perception',
        executable='person_detection_node',
        name='person_detection_node',
        parameters=[{
            'headless': headless,
            'use_sim_time': False,
            'confidence_threshold': 0.50,
            'frame_skip': 3,
        }],
        output='screen',
        condition=IfCondition(with_cognition)
    )

    active_vision_node = Node(
        package='cognition_perception',
        executable='active_vision_node',
        name='active_vision_node',
        parameters=[{
            'pan_home': 0,
            'tilt_home': 25,
            'pan_min': -60,
            'pan_max': 60,
            'tilt_min': 10,
            'tilt_max': 55,
            'kp_pan': 18.0,
            'ki_pan': 1.2,
            'kd_pan': 2.5,
            'kp_tilt': 14.0,
            'ki_tilt': 1.0,
            'kd_tilt': 2.0,
            'alpha_ema': 0.35,
            'deadband': 0.05,
            'max_slew_deg': 0.8,
            'search_amplitude': 30.0,
            'search_freq': 0.2,
            'control_rate_hz': 20.0,
            'target_timeout': 1.5,
        }],
        output='screen',
        condition=IfCondition(with_cognition)
    )

    gesture_node = Node(
        package='cognition_perception',
        executable='gesture_node',
        name='gesture_node',
        parameters=[{
            'headless': headless,
            'use_sim_time': False,
            'min_hand_size': 0.04,
            'frame_skip': 3,
        }],
        output='screen',
        condition=IfCondition(with_cognition)
    )

    brain_node = TimerAction(
        period=2.5,
        actions=[
            Node(
                package='cognition_brain',
                executable='brain_node',
                name='brain_node',
                parameters=[{
                    'use_sim_time': False,
                    'linear_speed': 0.25,
                    'angular_speed': 0.40,
                    'follow_speed': 0.20,
                    'gesture_buffer_size': 5,
                    'lock_timeout': 3.0,
                    'require_face_auth': require_face_auth,
                    'cmd_vel_topic': cmd_vel_topic,
                }],
                output='screen'
            )
        ]
    )

    # ── 4. Nav2 Navigation Stack & AMCL Localization ──
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_yaml, 'use_sim_time': False}],
        condition=IfCondition(with_nav2)
    )

    amcl = TimerAction(
        period=3.5,
        actions=[
            Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                parameters=[nav2_params, {'use_sim_time': False}],
                condition=IfCondition(with_nav2)
            )
        ]
    )

    nav2_bringup = TimerAction(
        period=4.5,
        actions=[
            Node(
                package='nav2_controller', executable='controller_server',
                name='controller_server', output='screen',
                parameters=[nav2_params, {'use_sim_time': False}],
                condition=IfCondition(with_nav2)
            ),
            Node(
                package='nav2_planner', executable='planner_server',
                name='planner_server', output='screen',
                parameters=[nav2_params, {'use_sim_time': False}],
                condition=IfCondition(with_nav2)
            ),
            Node(
                package='nav2_recoveries', executable='recoveries_server',
                name='recoveries_server', output='screen',
                parameters=[nav2_params, {'use_sim_time': False}],
                condition=IfCondition(with_nav2)
            ),
            Node(
                package='nav2_bt_navigator', executable='bt_navigator',
                name='bt_navigator', output='screen',
                parameters=[nav2_params, {'use_sim_time': False}],
                condition=IfCondition(with_nav2)
            ),
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_navigation', output='screen',
                parameters=[{
                    'use_sim_time': False,
                    'autostart': True,
                    'node_names': [
                        'map_server', 'amcl',
                        'controller_server', 'planner_server',
                        'recoveries_server', 'bt_navigator'
                    ]
                }],
                condition=IfCondition(with_nav2)
            )
        ]
    )

    # ── 5. Real-Time Web Map Visualizer Dashboard ──
    web_visualizer_process = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=['python3', '/root/cognition_ws/web_map_visualizer.py', '--port', '8080'],
                name='web_map_visualizer',
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        # Arguments
        declare_mode,
        declare_with_nav2,
        declare_with_cognition,
        declare_with_visualizer,
        declare_map_yaml,
        declare_nav2_params,
        declare_headless,
        declare_face_auth,
        declare_cmd_vel_topic,

        # Core Transforms & Sensor Restampers
        laser_tf,
        base_link_tf,
        scan_restamper,
        odom_imu_restamper,
        ekf_node,

        # Perception & Cognition Nodes
        camera_node,
        person_det_node,
        active_vision_node,
        gesture_node,
        brain_node,

        # Nav2 Localization & Motion Planning
        map_server,
        amcl,
        nav2_bringup,

        # Live Web Dashboard
        web_visualizer_process,
    ])
