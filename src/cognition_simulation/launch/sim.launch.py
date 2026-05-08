from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
import os

def generate_launch_description():
    pkg_path = os.path.join(
        os.path.dirname(__file__), '..', 'models', 'diff_robot'
    )

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', os.path.join(pkg_path, 'model.sdf')],
        output='screen'
    )

    bridge_left = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/left_wheel/vel@std_msgs/msg/Float64@gz.msgs.Double'],
        output='screen'
    )

    bridge_right = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/right_wheel/vel@std_msgs/msg/Float64@gz.msgs.Double'],
        output='screen'
    )

    direct_drive = Node(
        package='cognition_simulation',
        executable='direct_drive',
        name='direct_drive',
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        TimerAction(period=3.0, actions=[bridge_left, bridge_right]),
        TimerAction(period=5.0, actions=[direct_drive]),
    ])
