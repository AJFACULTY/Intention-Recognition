#!/usr/bin/env python3
"""
generate_report_figures.py
Generates publication-quality figures for the undergraduate thesis write-up:
1. Hardware connection schematic (hardware_design.png)
2. Docker multi-container deployment architecture (fig_docker_deployment.png)
3. Spatial-zone acceptance filter visualization (fig_spatial_zone.png)
4. Landmark-to-geometric feature extraction pipeline (fig_feature_pipeline.png)
5. UML Brain Node state machine diagram (fig_brain_state_machine.png)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np

os.makedirs("write_up/figures", exist_ok=True)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

def generate_hardware_schematic():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 96, "Hardware System Interconnection & Power Topology", 
            fontsize=13, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Central Processing: Raspberry Pi 5
    rpi_box = patches.FancyBboxPatch((35, 45), 30, 36, boxstyle="round,pad=1.5", 
                                     fc='#EBF8FF', ec='#3182CE', lw=2)
    ax.add_patch(rpi_box)
    ax.text(50, 78, "Raspberry Pi 5 (8GB RAM)\nPrimary Edge Computer", 
            fontsize=10, fontweight='bold', ha='center', va='center', color='#2B6CB0')
    ax.text(50, 69, "• Quad-core ARM Cortex-A76 @ 2.4 GHz\n• Ubuntu 24.04 LTS (Docker Host)\n• Vision & Cognition Pipelines", 
            fontsize=8, ha='center', va='center', color='#4A5568')

    # ESP32-S3 Microcontroller
    esp_box = patches.FancyBboxPatch((35, 8), 30, 26, boxstyle="round,pad=1.5", 
                                     fc='#FEFCBF', ec='#D69E2E', lw=2)
    ax.add_patch(esp_box)
    ax.text(50, 30, "ESP32-S3 Robotics Expansion Board", 
            fontsize=10, fontweight='bold', ha='center', va='center', color='#B7791F')
    ax.text(50, 21, "• micro-ROS Client Node (Firmware)\n• 6-Axis IMU (MPU6050)\n• 4-Ch Quadrature Motor Driver (310 Motors)\n• 2-Ch Pan-Tilt Gimbal Servos", 
            fontsize=8, ha='center', va='center', color='#744210')

    # USB Monocular Camera
    cam_box = patches.FancyBboxPatch((4, 66), 22, 18, boxstyle="round,pad=1.2", 
                                     fc='#EDFDFD', ec='#319795', lw=1.8)
    ax.add_patch(cam_box)
    ax.text(15, 78, "2MP USB Monocular\nCamera", fontsize=9, fontweight='bold', ha='center', va='center', color='#234E52')
    ax.text(15, 70, "• 1080p @ 30 FPS\n• Pan-Tilt Gimbal Mount\n• Monocular Video Stream", fontsize=7.5, ha='center', va='center', color='#2D3748')

    # MS200 LiDAR
    lidar_box = patches.FancyBboxPatch((4, 38), 22, 18, boxstyle="round,pad=1.2", 
                                       fc='#EDFDFD', ec='#319795', lw=1.8)
    ax.add_patch(lidar_box)
    ax.text(15, 50, "MS200 ToF LiDAR", fontsize=9, fontweight='bold', ha='center', va='center', color='#234E52')
    ax.text(15, 42, "• 12m Range, 360° Planar\n• 12.5 Hz Scan Frequency\n• UART Interface", fontsize=7.5, ha='center', va='center', color='#2D3748')

    # Battery & Power
    bat_box = patches.FancyBboxPatch((4, 8), 22, 20, boxstyle="round,pad=1.2", 
                                     fc='#FED7D7', ec='#E53E3E', lw=1.8)
    ax.add_patch(bat_box)
    ax.text(15, 23, "7.4V 2000mAh\nLi-ion Battery", fontsize=9, fontweight='bold', ha='center', va='center', color='#9B2C2C')
    ax.text(15, 13, "• Step-Down Buck Converter (5V 5A)\n• Dual Power Bus Architecture", fontsize=7.5, ha='center', va='center', color='#4A5568')

    # Actuation: 4x 310 DC Encoder Motors
    motor_box = patches.FancyBboxPatch((74, 12), 22, 22, boxstyle="round,pad=1.2", 
                                       fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(motor_box)
    ax.text(85, 28, "4× 310 DC Motors\n& Wheel Encoders", fontsize=9, fontweight='bold', ha='center', va='center', color='#22543D')
    ax.text(85, 18, "• Metal Gearboxes\n• Hall Effect Encoders\n• Differential Drive Base", fontsize=7.5, ha='center', va='center', color='#2D3748')

    # Pan-Tilt Gimbal Servos
    servo_box = patches.FancyBboxPatch((74, 46), 22, 16, boxstyle="round,pad=1.2", 
                                       fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(servo_box)
    ax.text(85, 57, "2-DOF Gimbal Servos", fontsize=9, fontweight='bold', ha='center', va='center', color='#22543D')
    ax.text(85, 50, "• Horizontal Pan (S1)\n• Vertical Tilt (S2)", fontsize=7.5, ha='center', va='center', color='#2D3748')

    # Workstation / Remote Host (RViz2)
    dev_box = patches.FancyBboxPatch((74, 72), 22, 16, boxstyle="round,pad=1.2", 
                                     fc='#E2E8F0', ec='#718096', lw=1.8)
    ax.add_patch(dev_box)
    ax.text(85, 83, "Engineering Host\nWorkstation", fontsize=9, fontweight='bold', ha='center', va='center', color='#2D3748')
    ax.text(85, 76, "• RViz2 Spatial Monitor\n• Gazebo Simulation", fontsize=7.5, ha='center', va='center', color='#4A5568')

    # Connections
    # Camera -> Pi5 (USB 3.0)
    ax.annotate("USB 3.0 (Video Stream)", xy=(35, 75), xytext=(26, 75),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#3182CE'), fontsize=7.5, va='bottom')
    # LiDAR -> ESP32/Pi5
    ax.annotate("LiDAR Data (/scan)", xy=(35, 52), xytext=(26, 48),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#319795'), fontsize=7.5, va='bottom')
    # Pi5 <-> ESP32 (UART 921600 baud)
    ax.annotate("micro-ROS UART Bridge (921,600 baud)\nBi-directional DDS / cmd_vel / odom_raw", 
                xy=(50, 36), xytext=(50, 43),
                arrowprops=dict(arrowstyle="<->", lw=2, color='#D69E2E'), 
                fontsize=8, ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#D69E2E", lw=1))
    # Battery Power
    ax.annotate("5V 5A Power", xy=(35, 58), xytext=(26, 26),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#E53E3E', linestyle='--'), fontsize=7.5, va='bottom')
    ax.annotate("Motor Power Rail", xy=(35, 18), xytext=(26, 18),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#E53E3E', linestyle='--'), fontsize=7.5, va='bottom')
    # ESP32 -> Motors
    ax.annotate("PWM & Direction", xy=(74, 23), xytext=(65, 23),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#38A169'), fontsize=7.5, va='bottom')
    # ESP32 -> Servos
    ax.annotate("PWM Signals", xy=(74, 54), xytext=(65, 34),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#38A169'), fontsize=7.5, va='bottom')
    # Pi5 <-> Workstation (Wi-Fi ROS_DOMAIN_ID=0)
    ax.annotate("Wi-Fi DDS Discovery\nROS_DOMAIN_ID=0", xy=(65, 78), xytext=(74, 78),
                arrowprops=dict(arrowstyle="<->", lw=1.5, color='#718096', linestyle=':'), fontsize=7.5, va='bottom')

    plt.tight_layout()
    plt.savefig("write_up/figures/hardware_design.png", bbox_inches='tight')
    plt.savefig("write_up/figures/fig_hardware_connection.png", bbox_inches='tight')
    plt.close()
    print("✓ Hardware schematic generated.")

def generate_docker_deployment():
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, "Containerized Multi-Node Deployment Architecture (Docker Host Mode)", 
            fontsize=13, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Raspberry Pi 5 Host Box
    host_box = patches.FancyBboxPatch((4, 8), 66, 82, boxstyle="round,pad=1.5", 
                                      fc='#F7FAFC', ec='#4A5568', lw=2)
    ax.add_patch(host_box)
    ax.text(37, 87, "Raspberry Pi 5 Host System (systemd: cognition.service | Host Network)", 
            fontsize=10.5, fontweight='bold', ha='center', va='center', color='#2D3748')

    # Container 1: yahboom_base
    c1 = patches.FancyBboxPatch((8, 56), 28, 26, boxstyle="round,pad=1", fc='#EBF8FF', ec='#3182CE', lw=1.5)
    ax.add_patch(c1)
    ax.text(22, 77, "Container: yahboom_base", fontsize=9.5, fontweight='bold', ha='center', color='#2B6CB0')
    ax.text(22, 67, "• MS200 LiDAR Driver (/scan)\n• Serial Port Binding (/dev/myserial)\n• IMU Publisher (/imu)\n• Odometry Transformer", 
            fontsize=7.5, ha='center', color='#2D3748')

    # Container 2: micro_ros_agent
    c2 = patches.FancyBboxPatch((8, 14), 28, 36, boxstyle="round,pad=1", fc='#FEFCBF', ec='#D69E2E', lw=1.5)
    ax.add_patch(c2)
    ax.text(22, 45, "Container: micro_ros_agent", fontsize=9.5, fontweight='bold', ha='center', color='#B7791F')
    ax.text(22, 30, "• micro-ROS Agent Daemon\n• UART 921600 Baud Transport\n• Bridge: ESP32 <-> ROS2 DDS\n• Subscribes: /cmd_vel\n• Publishes: /odom_raw, /battery", 
            fontsize=7.5, ha='center', color='#4A5568')

    # Container 3: yahboom_gesture (Cognition)
    c3 = patches.FancyBboxPatch((40, 14), 27, 68, boxstyle="round,pad=1", fc='#F0FFF4', ec='#38A169', lw=1.5)
    ax.add_patch(c3)
    ax.text(53.5, 77, "Container: yahboom_gesture\n(Custom Cognition Pipeline)", fontsize=9.5, fontweight='bold', ha='center', color='#22543D')
    ax.text(53.5, 62, "1. camera_pub:\n   • 20 Hz /camera/image_raw/compressed\n\n2. person_detection_node:\n   • YOLOv8n spatial filtering\n   • Kinematic velocity estimator\n   • /cognition/detection\n\n3. gesture_node:\n   • MediaPipe HandLandmarker\n   • 19 Geometric Features\n   • MLP ONNX Classifier (10 Hz)\n   • /cognition/gesture\n\n4. brain_node:\n   • Majority vote (3/5) & 3s lock\n   • Visual servoing (Kp=1.5)\n   • Publishes: /cmd_vel", 
            fontsize=7.5, ha='center', color='#2D3748')

    # Remote Workstation Box
    ws_box = patches.FancyBboxPatch((74, 18), 22, 70, boxstyle="round,pad=1.2", fc='#EDF2F7', ec='#718096', lw=1.8)
    ax.add_patch(ws_box)
    ax.text(85, 83, "Host Development\nWorkstation", fontsize=10, fontweight='bold', ha='center', color='#1A202C')
    ax.text(85, 60, "• RViz2 Live Visualization:\n  - /scan (LiDAR)\n  - /map (SLAM Toolbox)\n  - /tf transforms\n  - Camera image stream\n\n• Headless Simulation:\n  - Gazebo Harmonic\n  - Sim2Real verification\n\n• Teleoperation:\n  - joy_node / joy_ctrl\n  - Joystick override", 
            fontsize=7.5, ha='center', color='#4A5568')

    # DDS Arrows
    ax.annotate("Shared ROS_DOMAIN_ID=0 (DDS Discovery)", xy=(40, 52), xytext=(36, 52),
                arrowprops=dict(arrowstyle="<->", lw=1.5, color='#4A5568'), fontsize=7, ha='center')
    ax.annotate("Secure Wi-Fi DDS Stream", xy=(74, 52), xytext=(67, 52),
                arrowprops=dict(arrowstyle="<->", lw=1.8, color='#3182CE', linestyle='--'), fontsize=7.5, ha='center')

    plt.tight_layout()
    plt.savefig("write_up/figures/fig_docker_deployment.png", bbox_inches='tight')
    plt.close()
    print("✓ Docker deployment diagram generated.")

def generate_spatial_zone_figure():
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.set_xlim(0, 640)
    ax.set_ylim(0, 480)
    ax.invert_yaxis()  # Image coordinate space (0,0 top-left)

    # Frame background
    bg = patches.Rectangle((0, 0), 640, 480, fc='#F7FAFC', ec='#CBD5E0', lw=2)
    ax.add_patch(bg)
    ax.text(320, 25, "Camera Field of View (640 × 480 Resolution)", fontsize=11, fontweight='bold', ha='center', color='#2D3748')

    # Central Acceptance Zone (45% Width = 288px, 65% Height = 312px)
    # Center is at (320, 240) -> X: [176, 464], Y: [84, 396]
    zone = patches.Rectangle((176, 84), 288, 312, fc='#E6FFFA', ec='#319795', lw=2.5, linestyle='--')
    ax.add_patch(zone)
    ax.text(320, 105, "Active Acceptance Zone (45% W × 65% H)", fontsize=9.5, fontweight='bold', ha='center', color='#234E52')
    ax.text(320, 122, "[X: 176 to 464 px, Y: 84 to 396 px]", fontsize=8, ha='center', color='#285E61')

    # Frame Center Origin
    ax.plot(320, 240, marker='+', markersize=14, color='#E53E3E', mew=2)
    ax.text(328, 235, "Frame Origin (Cx=320, Cy=240)", fontsize=7.5, color='#9B2C2C', fontweight='bold')

    # Primary Operator (Centroid inside zone)
    # Box: X=250, Y=140, W=130, H=220 -> Centroid: (315, 250)
    op_box = patches.Rectangle((250, 140), 130, 220, fc='none', ec='#38A169', lw=2.5)
    ax.add_patch(op_box)
    ax.plot(315, 250, marker='o', markersize=7, color='#38A169')
    ax.text(315, 132, "Primary Operator (ID: 1)\nCentroid: (315, 250) -> ACCEPTED", 
            fontsize=8, fontweight='bold', ha='center', color='#22543D',
            bbox=dict(boxstyle="round,pad=0.2", fc="#C6F6D5", ec="#38A169", lw=1))
    
    # Error Vector from Center
    ax.annotate("", xy=(320, 250), xytext=(315, 250),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#2B6CB0'))
    ax.text(317, 268, "Error ex = -5 px", fontsize=7.5, ha='center', color='#2B6CB0', fontweight='bold')

    # Bystander / Non-Operator (Centroid outside zone)
    # Box: X=30, Y=160, W=100, H=190 -> Centroid: (80, 255)
    bystander_box = patches.Rectangle((30, 160), 100, 190, fc='none', ec='#E53E3E', lw=2, linestyle=':')
    ax.add_patch(bystander_box)
    ax.plot(80, 255, marker='x', markersize=8, color='#E53E3E', mew=2)
    ax.text(80, 150, "Bystander (ID: 2)\nCentroid: (80, 255)\nREJECTED (Outside Zone)", 
            fontsize=7.5, fontweight='bold', ha='center', color='#9B2C2C',
            bbox=dict(boxstyle="round,pad=0.2", fc="#FED7D7", ec="#E53E3E", lw=1))

    # Explanatory caption
    ax.text(320, 445, "Multi-person safety logic isolates closest person within central zone.\nDownstream hand landmark tracking and gesture lock engage exclusively on the primary operator.", 
            fontsize=8, ha='center', color='#4A5568', style='italic')

    plt.tight_layout()
    plt.savefig("write_up/figures/fig_spatial_zone.png", bbox_inches='tight')
    plt.close()
    print("✓ Spatial zone figure generated.")

def generate_feature_pipeline():
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, "Landmark Transformation and Geometric Feature Extraction Pipeline", 
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Stage 1: MediaPipe 21 Landmarks
    s1 = patches.FancyBboxPatch((3, 15), 21, 72, boxstyle="round,pad=1.2", fc='#EBF8FF', ec='#3182CE', lw=1.8)
    ax.add_patch(s1)
    ax.text(13.5, 82, "Stage 1: Skeletal Tracking", fontsize=9, fontweight='bold', ha='center', color='#2B6CB0')
    ax.text(13.5, 74, "MediaPipe HandLandmarker", fontsize=8, ha='center', color='#4A5568')
    ax.text(13.5, 48, "• Monocular RGB input\n• 21 3D Anatomical Landmarks\n  - P0: Wrist Origin\n  - P1-P4: Thumb joints\n  - P5-P8: Index finger\n  - P9-P12: Middle finger\n  - P13-P16: Ring finger\n  - P17-P20: Pinky finger\n• Output: (x, y, z) coords\n  [Vulnerable to Distance]", 
            fontsize=7.2, ha='center', color='#2D3748')

    # Stage 2: Geometric Transformation
    s2 = patches.FancyBboxPatch((27, 15), 25, 72, boxstyle="round,pad=1.2", fc='#FEFCBF', ec='#D69E2E', lw=1.8)
    ax.add_patch(s2)
    ax.text(39.5, 82, "Stage 2: Feature Engineering", fontsize=9, fontweight='bold', ha='center', color='#B7791F')
    ax.text(39.5, 74, "Scale & Distance Invariance", fontsize=8, ha='center', color='#4A5568')
    ax.text(39.5, 48, "1. 5 Finger Curl Angles:\n   θ = ∠(MCP-PIP, PIP-TIP)\n\n2. 3 Tip Spread Angles:\n   Thumb-Index, Index-Mid, Mid-Ring\n\n3. 5 Normalized Distances:\n   D_norm = ||P_tip - P0|| / PalmWidth\n   (PalmWidth = ||P5 - P17||)\n\n4. Palm & Pointing Angles:\n   2D orientation relative to gravity\n\n5. Thumb Height & Separation", 
            fontsize=7.2, ha='center', color='#2D3748')

    # Stage 3: 19-Feature Vector
    s3 = patches.FancyBboxPatch((55, 25), 18, 52, boxstyle="round,pad=1.2", fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(s3)
    ax.text(64, 72, "Stage 3: Vector", fontsize=9, fontweight='bold', ha='center', color='#22543D')
    ax.text(64, 65, "19 Geometric Features", fontsize=8, ha='center', color='#4A5568')
    ax.text(64, 46, "[ f1:  Thumb Curl\n  f2:  Index Curl\n  f3:  Middle Curl\n  f4:  Ring Curl\n  f5:  Pinky Curl\n  f6-f8: Tip Spreads\n  f9-f13: Norm Dists\n  f14-f17: Joint Angles\n  f18: Tip Separation\n  f19: Thumb Height ]^T", 
            fontsize=7, ha='center', color='#1A202C', family='monospace')

    # Stage 4: MLP Classifier
    s4 = patches.FancyBboxPatch((76, 15), 21, 72, boxstyle="round,pad=1.2", fc='#FAF5FF', ec='#805AD5', lw=1.8)
    ax.add_patch(s4)
    ax.text(86.5, 82, "Stage 4: MLP Model", fontsize=9, fontweight='bold', ha='center', color='#553C9A')
    ax.text(86.5, 74, "gesture_model.onnx", fontsize=8, ha='center', color='#4A5568')
    ax.text(86.5, 48, "• Architecture:\n  - Input Layer: 19 units\n  - Hidden 1: 64 (ReLU)\n  - Hidden 2: 32 (ReLU)\n  - Output: 6 units (Softmax)\n\n• Trained on 6,000 samples\n• ONNX Runtime Inference\n• 99.38% Test Accuracy\n• Inference Time: 1.2 ms\n\nOutput Command:\n{STOP, GO, LEFT,\n RIGHT, BACK, FOLLOW}", 
            fontsize=7.2, ha='center', color='#2D3748')

    # Arrows between stages
    ax.annotate("", xy=(27, 51), xytext=(24, 51), arrowprops=dict(arrowstyle="->", lw=2, color='#4A5568'))
    ax.annotate("", xy=(55, 51), xytext=(52, 51), arrowprops=dict(arrowstyle="->", lw=2, color='#4A5568'))
    ax.annotate("", xy=(76, 51), xytext=(73, 51), arrowprops=dict(arrowstyle="->", lw=2, color='#4A5568'))

    plt.tight_layout()
    plt.savefig("write_up/figures/fig_feature_pipeline.png", bbox_inches='tight')
    plt.close()
    print("✓ Feature pipeline diagram generated.")

def generate_state_machine_figure():
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, "UML State Machine: Brain Node Control Logic & Preemption Architecture", 
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Initial State
    ax.plot(8, 70, marker='o', markersize=14, color='#1A202C')
    ax.annotate("", xy=(16, 70), xytext=(9, 70), arrowprops=dict(arrowstyle="->", lw=1.8, color='#1A202C'))

    # State: IDLE
    s_idle = patches.FancyBboxPatch((16, 58), 18, 24, boxstyle="round,pad=1", fc='#EDF2F7', ec='#4A5568', lw=1.8)
    ax.add_patch(s_idle)
    ax.text(25, 75, "IDLE", fontsize=10, fontweight='bold', ha='center', color='#2D3748')
    ax.text(25, 66, "Entry: cmd_vel = (0, 0)\nMonitoring camera feed\nSearching for operator", fontsize=7.5, ha='center', color='#4A5568')

    # State: WAITING_CONFIRMATION
    s_wait = patches.FancyBboxPatch((42, 58), 22, 24, boxstyle="round,pad=1", fc='#FEFCBF', ec='#D69E2E', lw=1.8)
    ax.add_patch(s_wait)
    ax.text(53, 75, "WAITING_CONFIRM", fontsize=10, fontweight='bold', ha='center', color='#B7791F')
    ax.text(53, 66, "Person inside spatial zone\nPopulate 5-frame rolling buffer\nFilter confidence < 0.65", fontsize=7.5, ha='center', color='#744210')

    # State: LOCKED & EXECUTING
    s_exec = patches.FancyBboxPatch((72, 58), 24, 24, boxstyle="round,pad=1", fc='#F0FFF4', ec='#38A169', lw=1.8)
    ax.add_patch(s_exec)
    ax.text(84, 75, "LOCKED & EXECUTING", fontsize=10, fontweight='bold', ha='center', color='#22543D')
    ax.text(84, 66, "Lock active operator (3.0s)\nPublish Twist velocity:\n• STOP / GO / LEFT\n• RIGHT / BACK", fontsize=7.5, ha='center', color='#2D3748')

    # Sub-State: FOLLOW_MODE (Visual Servoing)
    s_follow = patches.FancyBboxPatch((55, 12), 38, 28, boxstyle="round,pad=1", fc='#EBF8FF', ec='#3182CE', lw=1.8)
    ax.add_patch(s_follow)
    ax.text(74, 34, "FOLLOW MODE (Visual Servoing)", fontsize=9.5, fontweight='bold', ha='center', color='#2B6CB0')
    ax.text(74, 22, "Calculate error: ex = (Cx - Bx)\nProportional steering: v_ω = -1.5 × ex\nProximity check:\n• If PersonWidth > 0.40: Halt (Safety Distance)\n• Else: Move forward (vx = 0.20 m/s)", 
            fontsize=7.5, ha='center', color='#2D3748')

    # Emergency Stop Halt State
    s_halt = patches.FancyBboxPatch((16, 12), 24, 26, boxstyle="round,pad=1", fc='#FED7D7', ec='#E53E3E', lw=2)
    ax.add_patch(s_halt)
    ax.text(28, 31, "EMERGENCY HALT", fontsize=10, fontweight='bold', ha='center', color='#9B2C2C')
    ax.text(28, 21, "Zero velocity forced\nAll buffers cleared\nSafety interlock engaged", fontsize=7.5, ha='center', color='#742A2A')

    # Transitions
    # IDLE -> WAITING
    ax.annotate("Person In Zone\n[Confidence > 0.65]", xy=(42, 70), xytext=(34, 70),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#4A5568'), fontsize=7, ha='center', va='bottom')
    # WAITING -> EXECUTING
    ax.annotate("Majority Vote Confirmed\n[>= 3 of 5 frames match]", xy=(72, 70), xytext=(64, 70),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#38A169'), fontsize=7, ha='center', va='bottom')
    # EXECUTING -> IDLE (Timeout)
    ax.annotate("Lock Expired (t > 3.0s) / No Gesture", xy=(28, 82), xytext=(80, 85),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#718096', connectionstyle="arc3,rad=-0.25"),
                fontsize=7.5, ha='center')
    # EXECUTING -> FOLLOW
    ax.annotate("Confirmed: FOLLOW", xy=(78, 58), xytext=(78, 40),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#3182CE'), fontsize=7.5, ha='left')
    # FOLLOW -> IDLE
    ax.annotate("Operator Lost / STOP", xy=(26, 58), xytext=(55, 26),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#718096', connectionstyle="arc3,rad=-0.15"),
                fontsize=7.5, ha='center')
    # Global Emergency Preemption
    ax.annotate("ASYNCHRONOUS OVERRIDE:\n/brain_node/emergency_stop Service OR Joystick Preemption", 
                xy=(28, 38), xytext=(55, 48),
                arrowprops=dict(arrowstyle="->", lw=2, color='#E53E3E', linestyle='--'),
                fontsize=7.5, ha='center', color='#9B2C2C', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#E53E3E", lw=1))

    plt.tight_layout()
    plt.savefig("write_up/figures/fig_brain_state_machine.png", bbox_inches='tight')
    plt.close()
    print("✓ State machine diagram generated.")

if __name__ == '__main__':
    generate_hardware_schematic()
    generate_docker_deployment()
    generate_spatial_zone_figure()
    generate_feature_pipeline()
    generate_state_machine_figure()
    print("\nAll 5 figures generated successfully in write_up/figures/.")
