#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    cognition_sim = os.path.expanduser('~/cognition_ws/src/cognition_simulation')
    yahboom_desc  = os.path.expanduser('~/yahboomcar_jazzy_ws/src/yahboomcar_description')
    yahboom_src   = os.path.expanduser('~/yahboomcar_jazzy_ws/src')
    urdf_xacro = os.path.join(cognition_sim, 'urdf', 'pi5_car_official.urdf.xacro')
    world_sdf  = os.path.join(cognition_sim, 'worlds', 'empty.sdf')
    rviz_cfg   = os.path.join(yahboom_desc, 'config', 'display.rviz')
    robot_desc = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', urdf_xacro]),
        value_type=str)
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}],
        output='screen')
    gz = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_sdf],
        output='screen',
        additional_env={
            'GZ_SIM_RESOURCE_PATHS': yahboom_src,
            'GZ_RESOURCE_PATH': yahboom_src,
            'IGN_GAZEBO_RESOURCE_PATH': yahboom_src,
        }
    )
    spawn = TimerAction(period=5.0, actions=[
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-world', 'empty', '-name', 'pi5_car',
                       '-topic', '/robot_description',
                       '-x', '0.0', '-y', '0.0', '-z', '0.05', '-Y', '0.0'],
            output='screen')])
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
        output='screen')
    rviz_args = ['-d', rviz_cfg] if os.path.exists(rviz_cfg) else []
    rviz = Node(package='rviz2', executable='rviz2',
                arguments=rviz_args,
                parameters=[{'use_sim_time': True}], output='screen')
    lidar_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "laser_frame", "pi5_car/base_footprint/lidar"],
        parameters=[{"use_sim_time": True}]
    )
    scan_repub = Node(
        package="cognition_simulation",
        executable="scan_republisher",
        output="screen",
        parameters=[{"use_sim_time": True}]
    )
    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[
            os.path.join(cognition_sim, "config", "ekf.yaml"),
            {"use_sim_time": True},
        ])
    return LaunchDescription([rsp, gz, bridge, spawn, rviz, ekf_node, lidar_tf, scan_repub])
