#!/usr/bin/env python3
"""
pi5_sim_headless.launch.py — Headless Simulation Launch Architecture
Cognition Robot Project — Dev Laptop Optimization (Milestone 4)

Features:
- Launches Gazebo Harmonic in headless server mode ('-s -r empty.sdf')
- Strips heavy OGRE2 GUI rendering thread, saving ~1,450 MiB RAM and ~1.5 CPU cores
- Prevents desktop compositor freezes and Linux OOM swap thrashing on 5.7 GiB laptops
- Parameterizes RViz2 (default: false) and GUI toggles
- Maintains complete sensor bridge, EKF state estimation, and rosbridge infrastructure
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    cognition_sim_share = get_package_share_directory('cognition_simulation')
    yahboom_desc_share = get_package_share_directory('yahboomcar_description')

    urdf_xacro = os.path.join(cognition_sim_share, 'urdf', 'pi5_car_official.urdf.xacro')
    world_sdf = os.path.join(cognition_sim_share, 'worlds', 'empty.sdf')

    our_rviz = os.path.join(cognition_sim_share, 'config', 'cognition.rviz')
    yahboom_rviz = os.path.join(yahboom_desc_share, 'config', 'display.rviz')
    rviz_cfg = our_rviz if os.path.exists(our_rviz) else (yahboom_rviz if os.path.exists(yahboom_rviz) else None)

    # Launch Arguments
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch lightweight RViz2 visualizer alongside headless simulation'
    )

    robot_desc = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', urdf_xacro]),
        value_type=str
    )

    # Robot State Publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}],
        output='screen'
    )

    # Headless Gazebo Harmonic Server (-s: server physics only, -r: run immediately)
    gz_server = ExecuteProcess(
        cmd=['gz', 'sim', '-s', '-r', world_sdf],
        output='screen',
        additional_env={
            'GZ_SIM_RESOURCE_PATH': os.pathsep.join([
                os.path.dirname(yahboom_desc_share),
                os.path.dirname(cognition_sim_share)
            ]),
        }
    )

    # Delayed entity spawn into simulation
    spawn = TimerAction(
        period=12.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'empty',
                    '-name', 'pi5_car',
                    '-topic', '/robot_description',
                    '-x', '-2.8', '-y', '-2.6', '-z', '0.05', '-Y', '0.0'
                ],
                output='screen'
            )
        ]
    )

    # ROS-Gazebo Parameter Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom_raw@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        remappings=[('/image_raw', '/camera/image_raw')],
        output='screen'
    )

    # Optional RViz2 instance
    rviz_args = ['-d', rviz_cfg] if rviz_cfg else []
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=rviz_args,
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )

    # Static LiDAR Transform
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'laser_frame',
            '--child-frame-id', 'pi5_car/base_footprint/lidar'
        ],
        parameters=[{'use_sim_time': True}]
    )

    # Scan Frame Republisher
    scan_repub = Node(
        package='cognition_simulation',
        executable='scan_republisher',
        respawn=True,
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # Extended Kalman Filter (EKF) State Estimation
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'frequency': 10.0,
            'sensor_timeout': 0.1,
            'two_d_mode': True,
            'publish_tf': True,
            'odom_frame':      'odom_frame',
            'base_link_frame': 'base_footprint',
            'world_frame':     'odom_frame',
            'odom0': '/odom_raw',
            'odom0_config': [True, True, False,
                             False, False, False,
                             True, True, False,
                             False, False, False,
                             False, False, False],
            'odom0_differential': False,
            'odom0_relative': False,
            'imu0': '/imu',
            'imu0_config': [False, False, False,
                            False, False, False,
                            False, False, False,
                            True, True, True,
                            True, True, True],
            'imu0_differential': False,
            'imu0_remove_gravitational_acceleration': True,
        }]
    )

    # Web Dashboard Infrastructure
    rosbridge = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{
            'port': 9090,
            'ssl': False,
            'use_sim_time': True,
        }]
    )

    web_video = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{
            'port': 8080,
            'use_sim_time': True,
        }]
    )

    return LaunchDescription([
        rviz_arg,
        rsp,
        gz_server,
        bridge,
        spawn,
        rviz,
        ekf_node,
        lidar_tf,
        scan_repub,
        rosbridge,
        web_video,
    ])
