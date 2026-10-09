#!/usr/bin/env python3
"""
twist_mux.launch.py — Safety Velocity Multiplexer
Cognition Robot Project

Priority hierarchy on /cmd_vel:
- Priority 100: Manual Wireless Joystick (/cmd_vel_joy) -> Instantly overrides autonomy
- Priority 50: Autonomous Nav2 Planner (/cmd_vel_nav)
- Priority 40: Cognition Gesture Tracker (/cmd_vel_gesture)
- Priority 255 (Lock): Emergency Stop (/e_stop)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # Dynamic path resolution: check src/ config first, fallback to install/ share
    user_home = os.path.expanduser("~")
    src_config = os.path.join(user_home, "cognition_ws", "src", "cognition_simulation", "config", "twist_mux.yaml")
    
    if os.path.exists(src_config):
        config_path = src_config
    else:
        try:
            config_path = os.path.join(
                get_package_share_directory("cognition_simulation"), "config", "twist_mux.yaml"
            )
        except Exception:
            config_path = "/root/cognition_ws/src/cognition_simulation/config/twist_mux.yaml"

    twist_mux_node = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        output="screen",
        parameters=[config_path],
        remappings=[
            ("cmd_vel_out", "/cmd_vel")
        ]
    )

    return LaunchDescription([twist_mux_node])
