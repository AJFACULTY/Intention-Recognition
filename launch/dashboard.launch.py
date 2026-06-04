#!/usr/bin/env python3
"""
dashboard.launch.py — Web Dashboard ROS Bridge & Video Server Launcher
Cognition Robot Project — Operator Web Interface
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    rosbridge = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{
            'port': 9090,
            'ssl': False,
            'use_sim_time': False,
        }]
    )

    web_video = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{
            'port': 8080,
            'use_sim_time': False,
        }]
    )

    return LaunchDescription([
        rosbridge,
        web_video,
    ])
