#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node

def generate_launch_description():
    world_sdf = os.path.expanduser('~/cognition_ws/src/cognition_simulation/worlds/empty.sdf')
    robot_sdf = '/tmp/pi5_car.sdf'
    bridge_cfg = os.path.expanduser('~/cognition_ws/src/cognition_simulation/config/pi5_bridge.yaml')
    urdf_xacro = os.path.expanduser('~/cognition_ws/src/cognition_simulation/urdf/pi5_car_official.urdf.xacro')

    gz = ExecuteProcess(cmd=['gz', 'sim', '-r', world_sdf], output='screen')

    spawn = ExecuteProcess(
        cmd=['ros2', 'run', 'ros_gz_sim', 'create',
             '-world', 'empty', '-name', 'pi5_car', '-file', robot_sdf],
        output='screen')

    # Spawn after Gazebo has fully started
    delayed_spawn = TimerAction(period=5.0, actions=[spawn])

    robot_desc = Command([FindExecutable(name='xacro'), ' ', urdf_xacro])
    robot_state_pub = Node(package='robot_state_publisher', executable='robot_state_publisher',
                           parameters=[{'robot_description': robot_desc, 'use_sim_time': True}])

    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge',
                  parameters=[{'config_file': bridge_cfg}], output='screen')

    return LaunchDescription([gz, robot_state_pub, bridge, delayed_spawn])
