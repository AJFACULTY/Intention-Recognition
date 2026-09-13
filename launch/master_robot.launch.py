#!/usr/bin/env python3
"""
master_robot.launch.py — Consolidated Industrial AMR Bringup Launch File
========================================================================
Platform: Yahboom Micro-ROS Pi 5 Autonomous Mobile Robot
Author: Autonomous Systems Engineering Team
Standards Compliance: ROS REP-103 / REP-105, ISO 15066:2016, OMG DDS v1.4

Orchestrates all robot subsystems into a single lifecycle-synchronized bringup:
1. Twist Multiplexer (Priority arbitration: E-Stop 255 > Joy 100 > Nav2 50 > Gesture 40)
2. Industrial Safety Audio Node (/beep acoustic reversing and warning chimes)
3. Nav2 Autonomous Navigation (AMCL, costmaps, global planner, local controller)
4. Cognition Autonomy (Active vision tracking, MediaPipe gesture classifier, Brain FSM)
5. Web Map Visualizer (RViz-equivalent HTTP map dashboard on :8080)

Usage:
    ros2 launch launch/master_robot.launch.py
    ros2 launch launch/master_robot.launch.py enable_cognition:=false
    ros2 launch launch/master_robot.launch.py enable_nav2:=false
    ros2 launch launch/master_robot.launch.py enable_visualizer:=false
"""

import os
import sys
from ament_index_python.packages import get_package_share_directory
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
    declare_nav2 = DeclareLaunchArgument(
        "enable_nav2",
        default_value="true",
        description="Launch Nav2 autonomous navigation & AMCL stack",
    )
    declare_cognition = DeclareLaunchArgument(
        "enable_cognition",
        default_value="true",
        description="Launch active vision, gesture perception & cognition brain",
    )
    declare_audio = DeclareLaunchArgument(
        "enable_audio",
        default_value="true",
        description="Launch industrial acoustic safety buzzer node (/beep)",
    )
    declare_visualizer = DeclareLaunchArgument(
        "enable_visualizer",
        default_value="true",
        description="Launch live RViz-equivalent Web Map Visualizer on http://localhost:8080",
    )
    declare_twist_mux = DeclareLaunchArgument(
        "enable_twist_mux",
        default_value="true",
        description="Launch twist_mux priority velocity multiplexer",
    )

    def resolve_path(candidates, default_rel):
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(ws_dir, default_rel)

    # ── 2. Twist Mux Priority Arbiter ────────────────────────────────────────
    twist_mux_config = resolve_path([
        os.path.join(ws_dir, "launch", "twist_mux.yaml"),
        os.path.join(ws_dir, "twist_mux.yaml"),
        "/root/cognition_ws/twist_mux.yaml",
    ], "launch/twist_mux.yaml")

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
        "/root/cognition_ws/src/cognition_perception/cognition_perception/safety_audio_node.py",
    ], "src_nodes/safety_audio_node.py")

    safety_audio_node = ExecuteProcess(
        cmd=[sys.executable, safety_audio_script],
        name="safety_audio_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_audio")),
    )

    # ── 4. Nav2 Autonomous Navigation Include ────────────────────────────────
    nav2_launch_path = resolve_path([
        os.path.join(ws_dir, "launch", "nav2.launch.py"),
        os.path.join(ws_dir, "nav2.launch.py"),
        "/root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py",
        "/root/cognition_ws/nav2.launch.py",
    ], "launch/nav2.launch.py")

    nav2_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_path),
        condition=IfCondition(LaunchConfiguration("enable_nav2")),
    )

    # ── 5. Cognition Perception & Brain Include (Delayed for Nav2 bringup) ────
    cognition_launch_path = resolve_path([
        os.path.join(ws_dir, "launch", "cognition_autonomy.launch.py"),
        os.path.join(ws_dir, "cognition_autonomy.launch.py"),
        "/root/cognition_ws/src/cognition_simulation/launch/cognition_autonomy.launch.py",
        "/root/cognition_ws/cognition_autonomy.launch.py",
    ], "launch/cognition_autonomy.launch.py")

    cognition_include = TimerAction(
        period=4.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(cognition_launch_path),
                launch_arguments={"cmd_vel_topic": "/cmd_vel_gesture"}.items(),
                condition=IfCondition(LaunchConfiguration("enable_cognition")),
            )
        ],
    )

    # ── 6. Web Map Visualizer (Port :8080) ───────────────────────────────────
    visualizer_script = resolve_path([
        os.path.join(ws_dir, "scripts", "web_map_visualizer.py"),
        os.path.join(ws_dir, "web_map_visualizer.py"),
        "/root/cognition_ws/web_map_visualizer.py",
    ], "scripts/web_map_visualizer.py")

    visualizer_process = TimerAction(
        period=6.0,
        actions=[
            ExecuteProcess(
                cmd=[sys.executable, visualizer_script],
                name="web_map_visualizer",
                output="screen",
                condition=IfCondition(LaunchConfiguration("enable_visualizer")),
            )
        ],
    )

    return LaunchDescription(
        [
            declare_nav2,
            declare_cognition,
            declare_audio,
            declare_visualizer,
            declare_twist_mux,
            twist_mux_node,
            safety_audio_node,
            nav2_include,
            cognition_include,
            visualizer_process,
        ]
    )
