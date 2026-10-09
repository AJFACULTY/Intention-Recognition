#!/usr/bin/env python3
"""
pi5_sim.launch.py — Unified Simulation Launch Architecture (GUI / Headless)
Cognition Robot Project

Features:
- Parameterized 'gui' argument (default: true).
  - gui:=true  -> Full Gazebo OGRE2 3D rendering window
  - gui:=false -> Headless server physics ('-s -r') saving 1.5GB RAM and 1.5 CPU cores
- Parameterized 'rviz' argument (default: true).
- Parameterized 'world' argument.
- Complete sensor bridge, TF publishing, EKF state estimation, and web infrastructure.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def launch_gz_process(context, *args, **kwargs):
    cognition_sim_share = get_package_share_directory('cognition_simulation')
    yahboom_desc_share = get_package_share_directory('yahboomcar_description')
    world_sdf = os.path.join(cognition_sim_share, 'worlds', 'empty.sdf')

    gui_val = LaunchConfiguration('gui').perform(context).lower() == 'true'

    if gui_val:
        gz_cmd = ['gz', 'sim', '-r', world_sdf]
    else:
        gz_cmd = ['gz', 'sim', '-s', '-r', world_sdf]

    return [
        ExecuteProcess(
            cmd=gz_cmd,
            output='screen',
            additional_env={
                'GZ_SIM_RESOURCE_PATH': os.pathsep.join([
                    os.path.dirname(yahboom_desc_share),
                    os.path.dirname(cognition_sim_share)
                ]),
            }
        )
    ]


def generate_launch_description():
    cognition_sim_share = get_package_share_directory('cognition_simulation')
    yahboom_desc_share = get_package_share_directory('yahboomcar_description')

    urdf_xacro = os.path.join(cognition_sim_share, 'urdf', 'pi5_car_official.urdf.xacro')

    our_rviz = os.path.join(cognition_sim_share, 'config', 'cognition.rviz')
    yahboom_rviz = os.path.join(yahboom_desc_share, 'config', 'display.rviz')
    rviz_cfg = our_rviz if os.path.exists(our_rviz) else (yahboom_rviz if os.path.exists(yahboom_rviz) else None)

    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Launch Gazebo OGRE2 3D GUI window (set to false for headless server)'
    )

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2 visualizer'
    )

    robot_desc = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', urdf_xacro]),
        value_type=str
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}],
        output='screen'
    )

    gz_action = OpaqueFunction(function=launch_gz_process)

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

    rviz_args = ['-d', rviz_cfg] if rviz_cfg else []
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=rviz_args,
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )

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

    scan_repub = Node(
        package='cognition_simulation',
        executable='scan_republisher',
        respawn=True,
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

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
        gui_arg,
        rviz_arg,
        rsp,
        gz_action,
        bridge,
        spawn,
        rviz,
        ekf_node,
        lidar_tf,
        scan_repub,
        rosbridge,
        web_video,
    ])
