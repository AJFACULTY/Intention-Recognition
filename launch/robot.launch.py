#!/usr/bin/env python3
"""
robot.launch.py — real hardware, no simulation.
Camera runs inside Yahboom Docker container on Pi.
This launch file runs on the dev machine.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    perc_params  = os.path.join(
        get_package_share_directory('cognition_perception'), 'config', 'perception_params.yaml')
    brain_params = os.path.join(
        get_package_share_directory('cognition_brain'), 'config', 'brain_params.yaml')

    gesture = Node(
        package='cognition_perception',
        executable='gesture_node',
        name='gesture_node',
        parameters=[perc_params, {'headless': True, 'use_sim_time': False}],
        output='screen'
    )

    detection = Node(
        package='cognition_perception',
        executable='person_detection_node',
        name='person_detection_node',
        parameters=[perc_params, {'headless': True, 'use_sim_time': False}],
        output='screen'
    )

    brain = TimerAction(
        period=3.0,
        actions=[Node(
            package='cognition_brain',
            executable='brain_node',
            name='brain_node',
            parameters=[brain_params, {'use_sim_time': False}],
            output='screen'
        )]
    )

    return LaunchDescription([gesture, detection, brain])
