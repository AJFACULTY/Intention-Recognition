#!/usr/bin/env python3
"""
cognition_autonomy.launch.py — Unified Autonomy Pipeline Launch
================================================================
Launches the complete perception, biometric, active vision, and arbitration pipeline:
1. FastDDS Low-Memory Dynamic Profile (FASTRTPS_DEFAULT_PROFILES_FILE)
2. Robust Auto-Probing Camera Publisher (/camera/image_raw/compressed)
3. Unified Human Pose & Gated Gesture Perception Node (MediaPipe Pose + Gated MLP)
   (or fallback to separate YOLOv8n + MediaPipe Hands via use_pose_gesture:=false)
4. Active Vision Gimbal Visual Servoing (0-Centric Calibrated Pan/Tilt PID + FSM)
5. InsightFace ArcFace Biometric Authorization (Optional via require_face_auth:=true)
6. Cognition Brain Decision & Mode Arbitration Node (twist_mux /cmd_vel_gesture)
7. Optional Operator Web Dashboard (rosbridge_websocket + web_video_server)

Usage:
    ros2 launch launch/cognition_autonomy.launch.py
    ros2 launch launch/cognition_autonomy.launch.py require_face_auth:=true
    ros2 launch launch/cognition_autonomy.launch.py cmd_vel_topic:=/cmd_vel
    ros2 launch launch/cognition_autonomy.launch.py dashboard:=true
    ros2 launch launch/cognition_autonomy.launch.py use_pose_gesture:=false
"""

import os
import sys
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ws_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def resolve_path(candidates, default_rel):
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(ws_dir, default_rel)

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
    declare_use_pose = DeclareLaunchArgument(
        'use_pose_gesture',
        default_value='true',
        description='Use unified MediaPipe human pose & gated gesture perception node'
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
    use_pose_gesture = LaunchConfiguration('use_pose_gesture')
    require_face_auth = LaunchConfiguration('require_face_auth')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    launch_camera = LaunchConfiguration('launch_camera')
    dashboard = LaunchConfiguration('dashboard')

    # ── 0. Set FastDDS Low-Memory Dynamic Profile ──
    fastdds_profile = resolve_path([
        os.path.join(ws_dir, "config", "fastdds_lowmem.xml"),
        "/root/cognition_ws/config/fastdds_lowmem.xml",
        "/home/pi/cognition_ws/config/fastdds_lowmem.xml",
    ], "config/fastdds_lowmem.xml")

    set_fastdds_env = SetEnvironmentVariable(
        name="FASTRTPS_DEFAULT_PROFILES_FILE",
        value=fastdds_profile
    )

    # ── 1. Robust Camera Publisher ──
    camera_script = resolve_path([
        os.path.join(ws_dir, "src_nodes", "camera_pub.py"),
        os.path.join(ws_dir, "camera_pub.py"),
        "/root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py",
        "/root/cognition_ws/camera_pub.py",
    ], "src_nodes/camera_pub.py")

    camera_node = ExecuteProcess(
        cmd=[sys.executable, "-u", camera_script],
        name="camera_publisher",
        output="screen",
        condition=IfCondition(launch_camera)
    )

    # ── 2. Unified Human Pose & Gated Gesture Perception Node ──
    human_pose_script = resolve_path([
        os.path.join(ws_dir, "src_nodes", "human_pose_gesture_node.py"),
        os.path.join(ws_dir, "human_pose_gesture_node.py"),
        "/root/cognition_ws/src/cognition_perception/cognition_perception/human_pose_gesture_node.py",
        "/root/cognition_ws/human_pose_gesture_node.py",
    ], "src_nodes/human_pose_gesture_node.py")

    human_pose_node = ExecuteProcess(
        cmd=[sys.executable, "-u", human_pose_script],
        name="human_pose_gesture_node",
        output="screen",
        condition=IfCondition(use_pose_gesture)
    )

    # ── Legacy Perception Nodes (Used if use_pose_gesture:=false) ──
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
        output='screen',
        condition=UnlessCondition(use_pose_gesture)
    )

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
        output='screen',
        condition=UnlessCondition(use_pose_gesture)
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

    # ── 5. Brain Decision & Mode Arbitration Node (Delayed 2.0s for perception warm-up) ──
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

    # ── 6. Web Dashboard Infrastructure (Optional) ──
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
        set_fastdds_env,
        declare_headless,
        declare_sim_time,
        declare_use_pose,
        declare_face_auth,
        declare_cmd_vel_topic,
        declare_camera,
        declare_dashboard,
        camera_node,
        human_pose_node,
        person_det_node,
        gesture_node,
        active_vision_node,
        face_id_node,
        brain_node,
        rosbridge_node,
        web_video_node,
    ])
