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

    def resolve_path(candidates, default_rel):
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(ws_dir, default_rel)

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
    declare_visualizer = DeclareLaunchArgument(
        "enable_visualizer",
        default_value="true",
        description="Launch live web map visualizer dashboard on http://localhost:8080",
    )

    # ── 2. Twist Mux Priority Arbiter ────────────────────────────────────────
    twist_mux_config = resolve_path([
        os.path.join(ws_dir, "config", "twist_mux.yaml"),
        os.path.join(ws_dir, "launch", "twist_mux.yaml"),
        os.path.join(ws_dir, "twist_mux.yaml"),
        "/root/cognition_ws/twist_mux.yaml",
        "/root/cognition_ws/config/twist_mux.yaml",
        "/root/cognition_ws/src/cognition_simulation/config/twist_mux.yaml",
    ], "config/twist_mux.yaml")

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
    safety_audio_script = resolve_path([
        os.path.join(ws_dir, "src_nodes", "safety_audio_node.py"),
        os.path.join(ws_dir, "safety_audio_node.py"),
        "/root/cognition_ws/safety_audio_node.py",
        "/root/cognition_ws/src_nodes/safety_audio_node.py",
        "/root/cognition_ws/src/cognition_perception/cognition_perception/safety_audio_node.py",
        "/root/cognition_ws/src/cognition_simulation/src_nodes/safety_audio_node.py",
        "/root/cognition_ws/src/cognition_simulation/safety_audio_node.py",
    ], "src_nodes/safety_audio_node.py")

    safety_audio_node = ExecuteProcess(
        cmd=[sys.executable, safety_audio_script],
        name="safety_audio_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_audio")),
    )

    # ── 4. SLAM Toolbox (Online Asynchronous Mapping & EKF) ──────────────────
    slam_launch_path = resolve_path([
        os.path.join(ws_dir, "launch", "slam_real.launch.py"),
        os.path.join(ws_dir, "slam_real.launch.py"),
        "/root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py",
        "/root/cognition_ws/slam_real.launch.py",
    ], "launch/slam_real.launch.py")

    slam_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_path)
    )

    # ── 5. Cognition Perception & Brain Include (Follow Mode) ────────────────
    cognition_launch_path = resolve_path([
        os.path.join(ws_dir, "launch", "cognition_autonomy.launch.py"),
        os.path.join(ws_dir, "cognition_autonomy.launch.py"),
        "/root/cognition_ws/src/cognition_simulation/launch/cognition_autonomy.launch.py",
        "/root/cognition_ws/cognition_autonomy.launch.py",
    ], "launch/cognition_autonomy.launch.py")

    cognition_include = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(cognition_launch_path),
                launch_arguments={
                    "cmd_vel_topic": "/cmd_vel_gesture",
                    "require_face_auth": "false",
                }.items(),
            )
        ],
    )

    # ── 6. Live Web Map Visualizer Dashboard (Port :8080) ───────────────────
    visualizer_script = resolve_path([
        os.path.join(ws_dir, "scripts", "web_map_visualizer.py"),
        os.path.join(ws_dir, "web_map_visualizer.py"),
        "/root/cognition_ws/web_map_visualizer.py",
        "/root/cognition_ws/scripts/web_map_visualizer.py",
        "/root/cognition_ws/src/cognition_simulation/scripts/web_map_visualizer.py",
        "/root/cognition_ws/src/cognition_simulation/web_map_visualizer.py",
    ], "scripts/web_map_visualizer.py")

    visualizer_process = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=[sys.executable, visualizer_script, '--mode', 'MODE 1.1: FOLLOW-TO-MAP SLAM', '--unmapped', '--view', 'slam'],
                name="web_map_visualizer",
                output="screen",
                condition=IfCondition(LaunchConfiguration("enable_visualizer")),
            )
        ],
    )

    return LaunchDescription(
        [
            declare_audio,
            declare_twist_mux,
            declare_visualizer,
            twist_mux_node,
            safety_audio_node,
            slam_include,
            cognition_include,
            visualizer_process,
        ]
    )
