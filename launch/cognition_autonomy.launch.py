#!/usr/bin/env python3
"""
cognition_autonomy.launch.py — Unified Multi-Modal Autonomy Pipeline Launch
==========================================================================
Launches the complete Cognition perception, biometric, active vision, and
arbitration pipeline:
1. Robust Auto-Probing Camera Publisher (/camera/image_raw/compressed)
2. Throttled Person Detection & Extrapolation (YOLOv8n ONNX 10 Hz)
3. Active Vision Gimbal Visual Servoing (0-Centric Calibrated Pan/Tilt PID + FSM)
4. InsightFace ArcFace Biometric Authorization (512-d Face ID)
5. Position-Invariant MediaPipe Gesture Classifier (STOP/GO/FOLLOW/LEFT/RIGHT/BACK)
6. Cognition Brain Decision & Mode Arbitration Node (twist_mux /cmd_vel_gesture)
7. Optional Operator Web Dashboard (rosbridge_websocket + web_video_server)

Usage:
    ros2 launch launch/cognition_autonomy.launch.py
    ros2 launch launch/cognition_autonomy.launch.py require_face_auth:=true
    ros2 launch launch/cognition_autonomy.launch.py cmd_vel_topic:=/cmd_vel
    ros2 launch launch/cognition_autonomy.launch.py dashboard:=true
"""

import os
import sys
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── Declare Configurable Launch Arguments ──
    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='true',
        description='Run nodes in headless mode without local GUI rendering'
    )
    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock time (/clock)'
    )
    declare_face_auth = DeclareLaunchArgument(
        'require_face_auth',
        default_value='false',
        description='Require enrolled ArcFace authorization before executing gestures'
    )
    declare_cmd_vel_topic = DeclareLaunchArgument(
        'cmd_vel_topic',
        default_value='/cmd_vel_gesture',
        description='Topic for wheel velocity commands (/cmd_vel_gesture for twist_mux, /cmd_vel for direct)'
    )
    declare_camera = DeclareLaunchArgument(
        'launch_camera',
        default_value='true',
        description='Launch physical camera publisher node'
    )
    declare_dashboard = DeclareLaunchArgument(
        'dashboard',
        default_value='false',
        description='Launch web dashboard backend (rosbridge on :9090, web_video on :8080)'
    )

    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')
    require_face_auth = LaunchConfiguration('require_face_auth')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    launch_camera = LaunchConfiguration('launch_camera')
    dashboard = LaunchConfiguration('dashboard')

    ws_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def resolve_path(candidates, default_rel):
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(ws_dir, default_rel)

    camera_script = resolve_path([
        os.path.join(ws_dir, "src_nodes", "camera_pub.py"),
        os.path.join(ws_dir, "camera_pub.py"),
        "/root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py",
        "/root/cognition_ws/camera_pub.py",
    ], "src_nodes/camera_pub.py")

    # ── 1. Robust Camera Publisher ──
    camera_node = ExecuteProcess(
        cmd=[sys.executable, "-u", camera_script],
        name="camera_publisher",
        output="screen",
        condition=IfCondition(launch_camera)
    )

    # ── 2. Throttled YOLOv8n Person Detector ──
    person_det_node = Node(
        package='cognition_perception',
        executable='person_detection_node',
        name='person_detection_node',
        parameters=[{
            'headless': headless,
            'use_sim_time': use_sim_time,
            'confidence_threshold': 0.50,
            'frame_skip': 3,
        }],
        output='screen'
    )

    # ── 3. Active Vision 2-DOF Pan/Tilt Gimbal Controller (0-Centric Calibrated) ──
    active_vision_node = Node(
        package='cognition_perception',
        executable='active_vision_node',
        name='active_vision_node',
        parameters=[{
            'pan_home': 0,
            'tilt_home': 30,
            'pan_min': -60,
            'pan_max': 60,
            'tilt_min': -15,
            'tilt_max': 36,
            'kp_pan': 18.0,
            'ki_pan': 1.2,
            'kd_pan': 2.5,
            'kp_tilt': 14.0,
            'ki_tilt': 1.0,
            'kd_tilt': 2.0,
            'alpha_ema': 0.35,
            'deadband': 0.05,
            'max_slew_deg': 0.6,
            'search_amplitude': 30.0,
            'search_freq': 0.2,
            'control_rate_hz': 30.0,
            'target_timeout': 1.5,
        }],
        output='screen'
    )

    # ── 4. InsightFace ArcFace 512-d Biometric Face ID Node ──
    face_id_node = Node(
        package='cognition_perception',
        executable='face_recognition_node',
        name='face_recognition_node',
        parameters=[{
            'headless': headless,
            'use_sim_time': use_sim_time,
            'confidence_threshold': 0.50,
            'frame_skip': 5,
        }],
        output='screen',
        condition=IfCondition(require_face_auth)
    )

    # ── 5. Position-Invariant MediaPipe Gesture Classifier ──
    gesture_node = Node(
        package='cognition_perception',
        executable='gesture_node',
        name='gesture_node',
        parameters=[{
            'headless': headless,
            'use_sim_time': use_sim_time,
            'min_hand_size': 0.04,
            'frame_skip': 3,
        }],
        output='screen'
    )

    # ── 6. Brain Decision & Mode Arbitration Node (Delayed 2.0s for perception warm-up) ──
    brain_node = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='cognition_brain',
                executable='brain_node',
                name='brain_node',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'linear_speed': 0.25,
                    'angular_speed': 0.40,
                    'follow_speed': 0.20,
                    'gesture_buffer_size': 5,
                    'lock_timeout': 3.0,
                    'require_face_auth': require_face_auth,
                    'cmd_vel_topic': cmd_vel_topic,
                }],
                output='screen'
            )
        ]
    )

    # ── 7. Web Dashboard Infrastructure (Optional) ──
    rosbridge_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{
            'port': 9090,
            'ssl': False,
            'use_sim_time': use_sim_time,
        }],
        condition=IfCondition(dashboard)
    )

    web_video_node = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{
            'port': 8080,
            'use_sim_time': use_sim_time,
        }],
        condition=IfCondition(dashboard)
    )

    return LaunchDescription([
        declare_headless,
        declare_sim_time,
        declare_face_auth,
        declare_cmd_vel_topic,
        declare_camera,
        declare_dashboard,
        camera_node,
        person_det_node,
        active_vision_node,
        face_id_node,
        gesture_node,
        brain_node,
        rosbridge_node,
        web_video_node,
    ])
