#!/usr/bin/env python3
"""
follow_to_map.launch.py — Unmapped Environment "Follow-to-Map" Collaborative SLAM (Mode 1)
========================================================================================
Platform: Yahboom Micro-ROS Pi 5 Autonomous Mobile Robot
Author: Autonomous Systems Engineering Team
Thesis Reference: Chapter 5 (§5.4 Dual-Mode Architecture — Mode 1)

Enables intuitive, collaborative room mapping without manual joystick driving:
1. Human raises the FOLLOW hand gesture.
2. Active Vision locks onto the human operator and visual servoing shadows their path.
3. SLAM Toolbox (online asynchronous) constructs the metric occupancy grid map in the background.
4. Reactive planar LiDAR safety bubble (0.36m buffer) continuously prevents collisions.
5. Safety Audio Node alerts bystanders with reversing and movement beeps.

Usage:
    ros2 launch launch/follow_to_map.launch.py
"""

import os
import sys
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    ExecuteProcess,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ws_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # ── 1. Launch Arguments ──────────────────────────────────────────────────
    declare_audio = DeclareLaunchArgument(
        "enable_audio",
        default_value="true",
        description="Launch industrial acoustic safety buzzer node (/beep)",
    )
    declare_twist_mux = DeclareLaunchArgument(
        "enable_twist_mux",
        default_value="true",
        description="Launch twist_mux priority velocity multiplexer",
    )

    # ── 2. Twist Mux Priority Arbiter ────────────────────────────────────────
    twist_mux_config = os.path.join(ws_dir, "launch", "twist_mux.yaml")
    twist_mux_node = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        output="screen",
        parameters=[twist_mux_config],
        remappings=[("cmd_vel_out", "/cmd_vel")],
        condition=IfCondition(LaunchConfiguration("enable_twist_mux")),
    )

    # ── 3. Industrial Safety Audio Node ──────────────────────────────────────
    safety_audio_script = os.path.join(ws_dir, "src_nodes", "safety_audio_node.py")
    safety_audio_node = ExecuteProcess(
        cmd=[sys.executable, safety_audio_script],
        name="safety_audio_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_audio")),
    )

    # ── 4. SLAM Toolbox (Online Asynchronous Mapping & EKF) ──────────────────
    slam_launch_path = os.path.join(ws_dir, "launch", "slam_real.launch.py")
    slam_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_path)
    )

    # ── 5. Cognition Perception & Brain Include (Follow Mode) ────────────────
    cognition_launch_path = os.path.join(ws_dir, "launch", "cognition_autonomy.launch.py")
    cognition_include = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(cognition_launch_path),
                launch_arguments={"cmd_vel_topic": "/cmd_vel_gesture"}.items(),
            )
        ],
    )

    return LaunchDescription(
        [
            declare_audio,
            declare_twist_mux,
            twist_mux_node,
            safety_audio_node,
            slam_include,
            cognition_include,
        ]
    )
