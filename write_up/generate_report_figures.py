#!/usr/bin/env python3
"""
Publication-Quality Report Figure Generator
Generates clean, cohesive draw.io / Lucidchart style architectural diagrams for the thesis.
Includes:
1. hardware_design.png: Mechatronic hardware layout & signal flow
2. system_architecture.png: End-to-end cognitive architecture & data pipeline
3. fig_docker_deployment.png: Multi-node container deployment architecture
4. fig_spatial_zone.png: Camera FOV spatial acceptance zone & bystander rejection
5. fig_feature_pipeline.png: 4-stage geometric feature extraction pipeline
6. fig_brain_state_machine.png: UML state machine with preemption logic
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs('write_up/figures', exist_ok=True)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# ------------------------------------------------------------------------------
# HELPER: Draw.io Style Card / Container with Header Banner
# ------------------------------------------------------------------------------
def draw_card(ax, x, y, w, h, bg_color, border_color, title, body_text='', 
              title_color=None, body_color='#1E293B', title_size=10, body_size=8,
              header_h=None, radius=1.0, is_mono=False):
    """Draws a container box in draw.io style with rounded corners and a title divider."""
    if title_color is None:
        title_color = border_color
    
    # Outer box
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad={radius}', 
                                 fc=bg_color, ec=border_color, lw=1.8)
    ax.add_patch(box)
    
    # Title divider line
    if header_h is None:
        header_h = h * 0.26 if '\n' in title else h * 0.20
    div_y = y + h - header_h
    ax.plot([x, x + w], [div_y, div_y], color=border_color, lw=1.2)
    
    # Title text
    ax.text(x + w / 2, y + h - header_h / 2, title, 
            fontsize=title_size, fontweight='bold', ha='center', va='center', color=title_color)
    
    # Body text
    if body_text:
        family = 'monospace' if is_mono else 'sans-serif'
        ax.text(x + 1.2, div_y - 1.5, body_text, 
                fontsize=body_size, ha='left', va='top', color=body_color, 
                family=family, linespacing=1.35)


# ------------------------------------------------------------------------------
# 1. HARDWARE SYSTEM ARCHITECTURE (Vertical Top-Down Mechatronic Flow)
# ------------------------------------------------------------------------------
def generate_hardware_schematic():
    fig, ax = plt.subplots(figsize=(10, 13), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(-18, 122)
    ax.axis('off')

    # Title
    ax.text(50, 117, 'System Hardware Architecture & Mechatronic Signal Flow', 
            fontsize=14, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Sensor layer (Top)
    # Camera
    draw_card(ax, 10, 96, 36, 15, '#E6FFFA', '#319795', 
              '2MP USB Monocular Camera', 
              '• Wide-Angle Lens | 640×480 @ 20 FPS\n• Mounted on 2-DOF Active Gimbal', 
              title_color='#234E52', body_color='#2D3748', title_size=9.5, body_size=8, header_h=4.5)

    # LiDAR
    draw_card(ax, 54, 96, 36, 15, '#E6FFFA', '#319795', 
              'MS200 2D ToF LiDAR Sensor', 
              '• 360° Planar Sweep | 12.5 Hz Frequency\n• Ranging: 0.12 m – 12.0 m Radius', 
              title_color='#234E52', body_color='#2D3748', title_size=9.5, body_size=8, header_h=4.5)

    # Primary Edge Computer: Raspberry Pi 5
    draw_card(ax, 15, 62, 70, 26, '#DAE8FC', '#6C8EBF', 
              'Primary Embedded Edge Computer: Raspberry Pi 5 (8GB RAM)', 
              '• Quad-Core ARM Cortex-A76 @ 2.4 GHz | Ubuntu 24.04 LTS (Docker Engine)\n• Visual Perception: Spatial Person Detection (YOLOv8) & Hand Landmarks (MediaPipe)\n• Intention Cognition: 19-D Geometric Feature Vector & MLP Classification Network\n• Supervisory Decision Logic: ROS2 Humble State Machine (brain_node) & SLAM Toolbox', 
              title_color='#1D4ED8', body_color='#1E293B', title_size=10.5, body_size=8.2, header_h=6.5)

    # Arrows from Sensors to Pi 5
    ax.annotate('', xy=(28, 88), xytext=(28, 96), arrowprops=dict(arrowstyle='->', lw=1.8, color='#319795'))
    ax.text(28, 92, 'USB 3.0 (/camera/image_raw)', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    ax.annotate('', xy=(72, 88), xytext=(72, 96), arrowprops=dict(arrowstyle='->', lw=1.8, color='#319795'))
    ax.text(72, 92, 'USB Serial (/scan @ 12.5Hz)', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    # Link between Pi 5 and ESP32
    ax.annotate('', xy=(50, 48), xytext=(50, 62), arrowprops=dict(arrowstyle='<->', lw=2.2, color='#D69E2E'))
    ax.text(50, 55, 'High-Speed micro-ROS UART Serial Bridge (921,600 baud)\nBi-directional DDS: /cmd_vel, /odom_raw, /imu/data_raw', 
            fontsize=8.5, ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', fc='#FFF2CC', ec='#D6B656', lw=1.2))

    # ESP32 Expansion Board Box
    draw_card(ax, 18, 30, 64, 18, '#FFF2CC', '#D6B656', 
              'Embedded Microcontroller Co-Processor: ESP32-S3 Expansion Board', 
              '• FreeRTOS Real-Time micro-ROS Client Firmware | Deterministic Actuation Loops\n• Onboard 6-Axis Inertial Measurement Unit (MPU6050 IMU @ 50 Hz)\n• Closed-Loop Wheel Odometry Computation & Quadrature Decoding', 
              title_color='#B45309', body_color='#451A03', title_size=10, body_size=8.2, header_h=5.5)

    # Arrow from ESP32 to Motor Driver
    ax.annotate('', xy=(50, 22), xytext=(50, 30), arrowprops=dict(arrowstyle='->', lw=1.8, color='#38A169'))
    ax.text(50, 26, '4-Channel PWM Drive Signals & Direction Logic', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    # Motor Driver Box
    draw_card(ax, 24, 14, 52, 8, '#D5E8D4', '#82B366', 
              'Onboard 4-Channel H-Bridge Motor Drivers & Power MOSFETs', 
              title_color='#15803D', body_size=8, title_size=9.5, header_h=8)

    # Arrow from Motor Driver to Motors
    ax.annotate('', xy=(50, 6.5), xytext=(50, 14), arrowprops=dict(arrowstyle='->', lw=1.8, color='#38A169'))
    ax.text(50, 10.2, 'High-Current Drive Current & Hall Feedback', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    # Motors Box
    draw_card(ax, 16, -1.5, 68, 8, '#D5E8D4', '#82B366', 
              '4× 310 DC Geared Motors & Magnetic Hall Quadrature Encoders', 
              title_color='#15803D', body_size=8, title_size=10, header_h=8)

    # Arrow from Motors to Movement
    ax.annotate('', xy=(50, -9.5), xytext=(50, -1.5), arrowprops=dict(arrowstyle='->', lw=2, color='#2563EB'))

    # Final Motion Execution Box
    draw_card(ax, 25, -17.5, 50, 8, '#DAE8FC', '#6C8EBF', 
              'Differential-Drive Mobile Locomotion & Spatial Response', 
              title_color='#1D4ED8', body_size=8, title_size=9.5, header_h=8)

    # Power Subsystem side-block (Draw.io Red)
    draw_card(ax, 1, 32, 14, 24, '#F8CECC', '#B85450', 
              'Power Subsystem', 
              '7.4V 2000mAh\nLi-ion Battery\n\nDecoupled 5V/5A\nBuck Converter', 
              title_color='#991B1B', body_color='#7F1D1D', title_size=8.5, body_size=7.5, header_h=5.5)

    ax.annotate('', xy=(15, 72), xytext=(8, 56),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='#B85450', linestyle='--'))
    ax.text(9, 66, '5V Logic', fontsize=7, color='#991B1B', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#F8CECC', lw=0.6))

    ax.annotate('', xy=(18, 38), xytext=(15, 38),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='#B85450', linestyle='--'))
    ax.text(16, 40, '7.4V Motor', fontsize=7, color='#991B1B', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#F8CECC', lw=0.6))

    # Gimbal Servos side-block (Draw.io Green)
    draw_card(ax, 85, 32, 14, 24, '#D5E8D4', '#82B366', 
              'Active Gimbal', 
              '2-DOF Pan/Tilt\nMicro Servos\n\n• Pan S1 (Horiz)\n• Tilt S2 (Vert)', 
              title_color='#15803D', body_color='#14532D', title_size=8.5, body_size=7.5, header_h=5.5)

    ax.annotate('', xy=(85, 40), xytext=(82, 40), arrowprops=dict(arrowstyle='->', lw=1.5, color='#82B366'))
    ax.text(83.5, 43, 'PWM', fontsize=7, color='#15803D', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#D5E8D4', lw=0.6))

    plt.tight_layout()
    plt.savefig('write_up/figures/hardware_design.png', bbox_inches='tight')
    plt.savefig('write_up/figures/fig_hardware_connection.png', bbox_inches='tight')
    plt.close()
    print('✓ Hardware schematic generated (Draw.io style).')


# ------------------------------------------------------------------------------
# 2. END-TO-END SYSTEM ARCHITECTURE & COGNITIVE FLOW (Twins with Hardware Design)
# ------------------------------------------------------------------------------
def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(10.5, 14.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(-16, 126)
    ax.axis('off')

    # Document Title
    ax.text(50, 123, 'Autonomous Mobile Robot System Architecture & Cognitive Flow', 
            fontsize=13.5, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Tier 1: Multimodal Sensing Layer
    draw_card(ax, 7, 103, 36, 15, '#E6FFFA', '#319795', 
              '2MP Monocular USB Camera', 
              '• RGB Video Stream: 640×480 @ 20 FPS\n• Active 2-DOF Pan/Tilt Servoing Support\n• Topic: /camera/image_raw', 
              title_color='#234E52', body_color='#2D3748', title_size=9.5, body_size=7.8, header_h=4.5)

    draw_card(ax, 47, 103, 36, 15, '#E6FFFA', '#319795', 
              'MS200 2D Time-of-Flight LiDAR', 
              '• 360° Planar Scan Sweep @ 12.5 Hz\n• Ranging: 0.12 m – 12.0 m (mm precision)\n• Topic: /scan (Direct Safety Interlock)', 
              title_color='#234E52', body_color='#2D3748', title_size=9.5, body_size=7.8, header_h=4.5)

    # Connector 1: Sensors -> Vision
    ax.annotate('', xy=(25, 95), xytext=(25, 103), arrowprops=dict(arrowstyle='->', lw=1.8, color='#319795'))
    ax.text(25, 99, 'USB 3.0 (/camera/image_raw)', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    # Tier 2: Spatial Gating & Skeletal Tracking
    draw_card(ax, 7, 77, 76, 18, '#DAE8FC', '#6C8EBF', 
              'Edge Vision & Spatial Operator Gating (YOLOv8n + MediaPipe)', 
              '• YOLOv8n Person Detector: Evaluates bounding box centroids against central zone (45% W × 65% H)\n• Spatial Gating Interlock: Discards bystanders outside active acceptance zone to prevent rogue tracking\n• MediaPipe HandLandmarker: Localizes 21 3D hand landmarks natively on Pi 5 (x, y, z coordinates)', 
              title_color='#1D4ED8', body_color='#1E293B', title_size=10, body_size=8, header_h=5.2)

    # Connector 2: Vision -> Feature Engineering
    ax.annotate('', xy=(45, 69), xytext=(45, 77), arrowprops=dict(arrowstyle='->', lw=1.8, color='#6C8EBF'))
    ax.text(45, 73, 'Isolated Operator Coordinates & 21 3D Hand Landmarks', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#6C8EBF', lw=0.8))

    # Tier 3: Feature Extraction & Neural Classifier
    draw_card(ax, 7, 51, 76, 18, '#FFF2CC', '#D6B656', 
              'Geometric Feature Extraction & Lightweight Neural Classifier', 
              '• 19-D Feature Extraction: Scale/distance-invariant curls, finger spreads, normalized wrist-to-tip distances\n• Lightweight MLP Classifier: 19 → 64 (ReLU) → 32 (ReLU) → 6 (Softmax) trained on 6,000 samples\n• Edge Inference: ONNX Runtime native execution @ 10 Hz, 1.2 ms inference latency, 99.38% test accuracy', 
              title_color='#B45309', body_color='#451A03', title_size=10, body_size=8, header_h=5.2)

    # Connector 3: Classification -> Supervisory Decision
    ax.annotate('', xy=(45, 43), xytext=(45, 51), arrowprops=dict(arrowstyle='->', lw=2.0, color='#D6B656'))
    ax.text(45, 47, 'Discrete Control Token (/cognition/gesture: STOP, GO, LEFT, RIGHT, BACK, FOLLOW)', 
            fontsize=7.8, ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#D6B656', lw=1.0))

    # Tier 4: Supervisory Control & Safety Arbitration (brain_node)
    draw_card(ax, 7, 22, 76, 21, '#D5E8D4', '#82B366', 
              'Supervisory Decision Engine & Safety Preemption Architecture (brain_node)', 
              '• Temporal Consensus Filter: 5-frame rolling majority voting (requires 3/5 agreement before locking state)\n• Stateful Command Lock: 3.0s deterministic velocity execution for discrete motions (GO, BACK, LEFT, RIGHT)\n• Visual Servoing Steering: Proportional heading tracking (v_ω = -1.5 × ex) during continuous FOLLOW mode\n• Asynchronous Safety Preemption: Immediate override halt on LiDAR obstacle (< 0.36 m) or hardware joystick', 
              title_color='#15803D', body_color='#14532D', title_size=10, body_size=8, header_h=5.5)

    # Direct LiDAR Safety Preemption Route (Orthogonal dashed line on right)
    ax.plot([83, 92, 92, 83], [110, 110, 32.5, 32.5], color='#B85450', lw=1.8, linestyle='--')
    ax.annotate('', xy=(83, 32.5), xytext=(88, 32.5), arrowprops=dict(arrowstyle='->', lw=1.8, color='#B85450'))
    ax.text(92, 71, 'Direct LiDAR Safety\nInterlock (Obstacle < 0.36m)', 
            fontsize=7.2, ha='center', va='center', color='#991B1B', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#B85450', lw=1.0))

    # Connector 4: Supervisory -> Middleware
    ax.annotate('', xy=(45, 14), xytext=(45, 22), arrowprops=dict(arrowstyle='->', lw=1.8, color='#82B366'))
    ax.text(45, 18, 'Safety-Arbitrated Velocity Commands (/cmd_vel Twist: vx, vω)', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#82B366', lw=0.8))

    # Tier 5: Middleware & Real-Time Bridge
    draw_card(ax, 7, 0, 76, 14, '#FFE6CC', '#D79B00', 
              'Distributed ROS2 DDS Middleware & micro-ROS Serial Bridge', 
              '• ROS2 Humble Hawksbill DDS Pub/Sub Highway with Host Network Shared Memory (--net=host)\n• High-Speed micro-ROS Agent Daemon bridging ROS2 DDS to FreeRTOS over 921,600 baud UART\n• Subscribes: /cmd_vel | Publishes: /odom_raw, /imu/data_raw, /battery_state', 
              title_color='#B45309', body_color='#451A03', title_size=10, body_size=8, header_h=4.5)

    # Connector 5: Middleware -> Microcontroller
    ax.annotate('', xy=(45, -7), xytext=(45, 0), arrowprops=dict(arrowstyle='->', lw=1.8, color='#D79B00'))
    ax.text(45, -3.5, 'micro-ROS Serial Packets (Motor PWM & Direction Logic)', fontsize=7.5, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E0', lw=0.8))

    # Tier 6: Low-Level Microcontroller & Actuation
    draw_card(ax, 12, -16, 66, 9, '#E1D5E7', '#9673A6', 
              'ESP32-S3 Microcontroller Firmware & Closed-Loop Motor Actuation', 
              '• FreeRTOS Real-Time Tasks: Closed-Loop PID Velocity Control & Quadrature Encoder Ticks\n• 4-Channel H-Bridge Motor Drivers & 4× 310 DC Geared Motors delivering Differential Locomotion', 
              title_color='#581C87', body_color='#3B0764', title_size=9.5, body_size=7.6, header_h=4.2)

    plt.tight_layout()
    plt.savefig('write_up/figures/system_architecture.png', bbox_inches='tight')
    plt.close()
    print('✓ System architecture diagram generated (Draw.io style).')


# ------------------------------------------------------------------------------
# 3. DOCKER DEPLOYMENT ARCHITECTURE (Draw.io Container Layout)
# ------------------------------------------------------------------------------
def generate_docker_deployment():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(65, 96.5, 'Containerized Multi-Node Deployment Architecture (Docker Host Mode)', 
            fontsize=14, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Host container (Pi 5)
    host_box = patches.FancyBboxPatch((4, 5), 89, 87, boxstyle='round,pad=1.2', 
                                      fc='#F9F9F9', ec='#666666', lw=1.8, linestyle='--')
    ax.add_patch(host_box)
    ax.text(18, 90, 'Raspberry Pi 5 Host OS (Ubuntu 24.04 LTS)', 
            fontsize=10.5, fontweight='bold', ha='left', va='center', color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', fc='#E0E0E0', ec='#999999', lw=1))
    ax.text(89, 90, 'Network: --net=host | systemd daemon', fontsize=8.5, ha='right', va='center', color='#666666', style='italic')

    # 1. Container: yahboom_base (Hardware Drivers) - Draw.io Blue
    draw_card(ax, 7, 48, 38, 36, '#DAE8FC', '#6C8EBF', 
              'Container: yahboom_base\n[Hardware Driver Services]', 
              '• MS200 LiDAR Node (/scan @ 12.5 Hz)\n• Serial Port Binding (/dev/myserial)\n• 6-Axis IMU Publisher (/imu @ 50 Hz)\n• Differential Odometry Transformer\n• Base Coordinate TF Broadcaster', 
              title_color='#1D4ED8', body_color='#1E293B', title_size=9.5, body_size=8, header_h=9)

    # 2. Container: micro_ros_agent (Bridge) - Draw.io Yellow
    draw_card(ax, 7, 9, 38, 33, '#FFF2CC', '#D6B656', 
              'Container: micro_ros_agent\n[Deterministic Hardware Bridge]', 
              '• micro-ROS Agent Daemon (Client Bridge)\n• Serial UART 921,600 Baud Link\n• Subscribes: /cmd_vel (Twist Commands)\n• Publishes: /odom_raw (Wheel Ticks)\n• Publishes: /battery_state (Voltage Telemetry)', 
              title_color='#B45309', body_color='#451A03', title_size=9.5, body_size=8, header_h=8.5)

    # 3. Container: yahboom_gesture (Cognition Pipeline) - Draw.io Green
    draw_card(ax, 52, 9, 39, 75, '#D5E8D4', '#82B366', 
              'Container: yahboom_gesture\n[Edge Vision & Decision Cognition]', 
              '1. camera_pub (20 FPS):\n   • /camera/image_raw/compressed\n\n2. person_detection_node:\n   • YOLOv8n spatial zone filter\n   • Primary operator bounding box isolation\n   • Publishes: /cognition/detection\n\n3. gesture_node:\n   • MediaPipe HandLandmarker (21 3D pts)\n   • 19 Geometric Feature vector extraction\n   • MLP ONNX Classifier (10 Hz, 1.2 ms)\n   • Publishes: /cognition/gesture\n\n4. brain_node (Supervisory Logic):\n   • 3/5 Majority filter & 3s execution lock\n   • Visual servoing steering (Kp = 1.5)\n   • Publishes: /cmd_vel to motor base', 
              title_color='#15803D', body_color='#14532D', title_size=9.5, body_size=7.8, header_h=8.5)

    # Inter-container arrows (DDS Shared Memory Loopback)
    ax.annotate('', xy=(52, 62), xytext=(45, 62),
                arrowprops=dict(arrowstyle='<->', lw=1.8, color='#3B82F6'))
    ax.text(48.5, 65, '/scan\n/camera', fontsize=7, ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#3B82F6', lw=0.8))

    ax.annotate('', xy=(52, 24), xytext=(45, 24),
                arrowprops=dict(arrowstyle='<->', lw=1.8, color='#D97706'))
    ax.text(48.5, 27, '/cmd_vel\n/odom_raw', fontsize=7, ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#D97706', lw=0.8))

    # Right side: Engineering Host Workstation - Draw.io Purple
    draw_card(ax, 98, 9, 29, 83, '#E1D5E7', '#9673A6', 
              'Engineering Host\nWorkstation', 
              '• x86_64 Dev Workstation\n  (AMD Ryzen 5, 8GB RAM)\n\n• RViz2 Live Monitoring:\n  - /scan (LiDAR 2D points)\n  - /map (SLAM 2D grid)\n  - /tf transforms\n  - Camera frame display\n\n• Simulation & Testing:\n  - Gazebo Harmonic\n  - Sim2Real verification\n\n• Safety Intervention:\n  - joy_node / joy_ctrl\n  - Hardware joystick override\n\n• Offline Deep Learning:\n  - PyTorch MLP & LSTM\n  - ONNX model compilation', 
              title_color='#581C87', body_color='#3B0764', title_size=10, body_size=7.6, header_h=9)

    # Network Bridge arrow (Wi-Fi ROS_DOMAIN_ID=0)
    ax.annotate('', xy=(98, 50), xytext=(93, 50),
                arrowprops=dict(arrowstyle='<->', lw=2.2, color='#7C3AED', linestyle=':'))
    ax.text(95.5, 52.5, 'Wi-Fi DDS\nROS_DOMAIN_ID=0', fontsize=7.5, ha='center', va='bottom', color='#6D28D9', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#7C3AED', lw=0.8))

    plt.tight_layout()
    plt.savefig('write_up/figures/fig_docker_deployment.png', bbox_inches='tight')
    plt.close()
    print('✓ Docker deployment diagram generated (Draw.io style).')


# ------------------------------------------------------------------------------
# 4. SPATIAL RECEPTIVE ZONE FIGURE (Draw.io Coordinate Layout)
# ------------------------------------------------------------------------------
def generate_spatial_zone_figure():
    fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)
    ax.set_xlim(0, 640)
    ax.set_ylim(0, 480)
    ax.invert_yaxis()

    bg = patches.Rectangle((0, 0), 640, 480, fc='#F9FAFB', ec='#9CA3AF', lw=1.8)
    ax.add_patch(bg)
    ax.text(320, 25, 'Camera Field of View (640 × 480 Resolution)', fontsize=11, fontweight='bold', ha='center', color='#1F2937')

    zone = patches.Rectangle((176, 84), 288, 312, fc='#E6FFFA', ec='#319795', lw=2.2, linestyle='--')
    ax.add_patch(zone)
    ax.text(320, 105, 'Active Acceptance Zone (45% W × 65% H)', fontsize=9.5, fontweight='bold', ha='center', color='#234E52')
    ax.text(320, 122, '[X: 176 to 464 px, Y: 84 to 396 px]', fontsize=8, ha='center', color='#285E61')

    ax.plot(320, 240, marker='+', markersize=14, color='#B85450', mew=2)
    ax.text(328, 235, 'Frame Origin (Cx=320, Cy=240)', fontsize=7.5, color='#991B1B', fontweight='bold')

    op_box = patches.Rectangle((250, 140), 130, 220, fc='#D5E8D4', ec='#82B366', lw=2.2)
    ax.add_patch(op_box)
    ax.plot(315, 250, marker='o', markersize=7, color='#15803D')
    ax.text(315, 132, 'Primary Operator (ID: 1)\nCentroid: (315, 250) -> ACCEPTED', 
            fontsize=8, fontweight='bold', ha='center', color='#15803D',
            bbox=dict(boxstyle='round,pad=0.25', fc='#D5E8D4', ec='#82B366', lw=1))
    
    ax.annotate('', xy=(320, 250), xytext=(315, 250), arrowprops=dict(arrowstyle='->', lw=1.5, color='#1D4ED8'))
    ax.text(317, 268, 'Error ex = -5 px', fontsize=7.5, ha='center', color='#1D4ED8', fontweight='bold')

    bystander_box = patches.Rectangle((30, 160), 100, 190, fc='#F8CECC', ec='#B85450', lw=2, linestyle=':')
    ax.add_patch(bystander_box)
    ax.plot(80, 255, marker='x', markersize=8, color='#B85450', mew=2)
    ax.text(80, 150, 'Bystander (ID: 2)\nCentroid: (80, 255)\nREJECTED (Outside Zone)', 
            fontsize=7.5, fontweight='bold', ha='center', color='#991B1B',
            bbox=dict(boxstyle='round,pad=0.25', fc='#F8CECC', ec='#B85450', lw=1))

    ax.text(320, 450, 'Multi-person safety logic isolates closest person within central zone.\nDownstream hand landmark tracking engages exclusively on the primary operator.', 
            fontsize=8, ha='center', color='#4B5563', style='italic')

    plt.tight_layout()
    plt.savefig('write_up/figures/fig_spatial_zone.png', bbox_inches='tight')
    plt.close()
    print('✓ Spatial zone figure generated (Draw.io style).')


# ------------------------------------------------------------------------------
# 5. FEATURE EXTRACTION PIPELINE (Draw.io 4-Stage Horizontal Flow)
# ------------------------------------------------------------------------------
def generate_feature_pipeline():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=300)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(65, 96.5, 'Landmark Transformation and Geometric Feature Extraction Pipeline', 
            fontsize=14, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Stage 1: Blue (#DAE8FC)
    draw_card(ax, 4, 8, 28, 80, '#DAE8FC', '#6C8EBF', 
              'Stage 1: Skeletal Tracking', 
              'MediaPipe HandLandmarker:\n• 640×480 RGB Video Input\n• 21 3D Anatomical Landmarks:\n   P0: Wrist Origin\n   P1–P4: Thumb Joints\n   P5–P8: Index Finger\n   P9–P12: Middle Finger\n   P13–P16: Ring Finger\n   P17–P20: Pinky Finger\n• Raw (x, y, z) Coordinates\n• Scale-dependent and sensitive\n  to camera distance', 
              title_color='#1D4ED8', body_color='#1E293B', title_size=9.5, body_size=7.6, header_h=5.5)

    # Stage 2: Yellow (#FFF2CC)
    draw_card(ax, 36, 8, 29, 80, '#FFF2CC', '#D6B656', 
              'Stage 2: Feature Extraction', 
              'Scale & Distance Invariance:\n1. 5 Finger Curl Angles:\n   θ = ∠(MCP–PIP, PIP–TIP)\n\n2. 3 Tip Spread Angles:\n   Thumb–Index, Index–Mid,\n   Mid–Ring\n\n3. 5 Normalized Distances:\n   D_norm = ||P_tip - P0|| / W\n   (PalmWidth W = ||P5 - P17||)\n\n4. Palm Orientation:\n   2D gravity-referenced angle\n\n5. Thumb Height & Separation', 
              title_color='#B45309', body_color='#451A03', title_size=9.5, body_size=7.6, header_h=5.5)

    # Stage 3: Green (#D5E8D4)
    draw_card(ax, 69, 8, 26, 80, '#D5E8D4', '#82B366', 
              'Stage 3: Vector Encoding', 
              '19-D Geometric Vector:\n[ f1:  Thumb Curl\n  f2:  Index Curl\n  f3:  Middle Curl\n  f4:  Ring Curl\n  f5:  Pinky Curl\n  f6:  Spread Thumb-Index\n  f7:  Spread Index-Mid\n  f8:  Spread Mid-Ring\n  f9-f13: Norm Dists (T,I,M,R,P)\n  f14-f17: Joint Angles\n  f18: Tip Separation\n  f19: Thumb Height ]^T', 
              title_color='#15803D', body_color='#14532D', title_size=9.5, body_size=7.2, header_h=5.5, is_mono=True)

    # Stage 4: Purple (#E1D5E7)
    draw_card(ax, 99, 8, 27, 80, '#E1D5E7', '#9673A6', 
              'Stage 4: MLP Classifier', 
              'Neural Architecture:\n• Input: 19 units\n• Hidden 1: 64 (ReLU)\n• Hidden 2: 32 (ReLU)\n• Output: 6 units (Softmax)\n\nMetrics & Performance:\n• Trained: 6,000 samples\n• ONNX Edge Inference (10 Hz)\n• Accuracy: 99.38% (Test)\n• Latency: 1.2 ms on Pi 5\n\nDiscrete Control Tokens:\n{STOP, GO, LEFT, RIGHT,\n BACK, FOLLOW}', 
              title_color='#581C87', body_color='#3B0764', title_size=9.5, body_size=7.4, header_h=5.5)

    # Connector Arrows
    ax.annotate('', xy=(36, 48), xytext=(32, 48), arrowprops=dict(arrowstyle='->', lw=2.2, color='#6C8EBF'))
    ax.annotate('', xy=(69, 48), xytext=(65, 48), arrowprops=dict(arrowstyle='->', lw=2.2, color='#D6B656'))
    ax.annotate('', xy=(99, 48), xytext=(95, 48), arrowprops=dict(arrowstyle='->', lw=2.2, color='#82B366'))

    plt.tight_layout()
    plt.savefig('write_up/figures/fig_feature_pipeline.png', bbox_inches='tight')
    plt.close()
    print('✓ Feature pipeline diagram generated (Draw.io style).')


# ------------------------------------------------------------------------------
# 6. UML STATE MACHINE DIAGRAM (Draw.io State Layout with Spacious Routing)
# ------------------------------------------------------------------------------
def generate_state_machine_figure():
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(65, 97, 'UML State Machine: Brain Node Control Logic & Preemption Architecture', 
            fontsize=14, fontweight='bold', ha='center', va='top', color='#1A202C')

    # Initial State (Solid Circle)
    ax.plot(5, 68, marker='o', markersize=14, color='#1A202C')
    ax.annotate('', xy=(12, 68), xytext=(6, 68), arrowprops=dict(arrowstyle='->', lw=1.8, color='#1A202C'))

    # State 1: IDLE (Gray #F5F5F5 / #666666)
    draw_card(ax, 12, 54, 26, 28, '#F5F5F5', '#666666', 
              'IDLE', 
              '• Entry: cmd_vel = (0, 0)\n• Monitoring camera feed\n• Operator detection search\n• Spatial zone gating active', 
              title_color='#333333', body_color='#4B5563', title_size=10.5, body_size=7.8, header_h=6.5)

    # State 2: WAITING_CONFIRMATION (Yellow #FFF2CC / #D6B656)
    draw_card(ax, 48, 54, 28, 28, '#FFF2CC', '#D6B656', 
              'WAITING_CONFIRM', 
              '• Person inside spatial zone\n• 5-frame rolling buffer\n• Confidence threshold >= 0.65\n• Hand landmark tracking engaged', 
              title_color='#B45309', body_color='#451A03', title_size=10.5, body_size=7.8, header_h=6.5)

    # State 3: LOCKED & EXECUTING (Green #D5E8D4 / #82B366)
    draw_card(ax, 88, 54, 36, 28, '#D5E8D4', '#82B366', 
              'LOCKED & EXECUTING', 
              '• Lock operator intent (3.0s lock)\n• Publish Twist commands on /cmd_vel:\n   STOP / GO / LEFT / RIGHT / BACK\n• Enforce smooth acceleration limits', 
              title_color='#15803D', body_color='#14532D', title_size=10.5, body_size=7.8, header_h=6.5)

    # State 4: FOLLOW MODE (Blue #DAE8FC / #6C8EBF)
    draw_card(ax, 70, 10, 54, 28, '#DAE8FC', '#6C8EBF', 
              'FOLLOW MODE (Visual Servoing)', 
              '• Calculate heading error: ex = (Cx - Bx)\n• Proportional steering: v_ω = -1.5 × ex\n• Proximity distance check:\n   If PersonWidth > 0.40: Halt (Safety Zone Preserve)\n   Else: Drive forward (vx = 0.20 m/s)', 
              title_color='#1D4ED8', body_color='#1E293B', title_size=10.5, body_size=7.8, header_h=6.5)

    # State 5: EMERGENCY HALT (Red #F8CECC / #B85450)
    draw_card(ax, 12, 10, 34, 28, '#F8CECC', '#B85450', 
              'EMERGENCY HALT', 
              '• Forced zero velocity (cmd_vel = 0)\n• Clear rolling buffers & lock timer\n• Safety hardware interlock engaged\n• Priority preemption over all states', 
              title_color='#991B1B', body_color='#7F1D1D', title_size=10.5, body_size=7.8, header_h=6.5)

    # Transitions
    # 1: IDLE -> WAITING
    ax.annotate('', xy=(48, 68), xytext=(38, 68), arrowprops=dict(arrowstyle='->', lw=1.8, color='#4A5568'))
    ax.text(43, 70.5, 'Operator\nin Zone', fontsize=7.2, ha='center', va='bottom', color='#333333', fontweight='bold')

    # 2: WAITING -> EXECUTING
    ax.annotate('', xy=(88, 68), xytext=(76, 68), arrowprops=dict(arrowstyle='->', lw=1.8, color='#82B366'))
    ax.text(82, 70.5, 'Majority\n(3/5 Confirmed)', fontsize=7.2, ha='center', va='bottom', color='#15803D', fontweight='bold')

    # 3: EXECUTING -> IDLE (Draw.io clean orthogonal return above top boxes)
    ax.plot([106, 106, 25, 25], [82, 90, 90, 82], color='#666666', lw=1.6)
    ax.annotate('', xy=(25, 82), xytext=(25, 83), arrowprops=dict(arrowstyle='->', lw=1.6, color='#666666'))
    ax.text(65.5, 90, 'Lock Expired (t > 3.0s) / Gesture Complete', fontsize=7.8, ha='center', va='center', color='#333333', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#666666', lw=0.9))

    # 4: EXECUTING -> FOLLOW (Straight down)
    ax.annotate('', xy=(97, 38), xytext=(97, 54), arrowprops=dict(arrowstyle='->', lw=1.8, color='#1D4ED8'))
    ax.text(99, 46, 'Gesture == FOLLOW', fontsize=7.8, ha='left', va='center', color='#1D4ED8', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#6C8EBF', lw=0.8))

    # 5: FOLLOW -> IDLE (Orthogonal return via spacious route along y=48)
    ax.plot([70, 56, 56, 34, 34], [30, 30, 48, 48, 54], color='#666666', lw=1.5)
    ax.annotate('', xy=(34, 54), xytext=(34, 53), arrowprops=dict(arrowstyle='->', lw=1.5, color='#666666'))
    ax.text(45, 48, 'Operator Lost / STOP', fontsize=7.2, ha='center', va='center', color='#333333', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#999999', lw=0.8))

    # 6: Preemption into EMERGENCY HALT (Asynchronous override from WAITING at y=54 down to y=41)
    ax.plot([65, 65, 29], [54, 41, 41], color='#B85450', lw=1.8, linestyle='--')
    ax.annotate('', xy=(29, 38), xytext=(29, 41), arrowprops=dict(arrowstyle='->', lw=1.8, color='#B85450'))
    ax.text(47, 41, 'ASYNCHRONOUS PREEMPTION:\nLiDAR Obstacle < 0.36m OR Joystick Override', 
            fontsize=6.8, ha='center', va='center', color='#991B1B', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#B85450', lw=1.0))

    # 7: Recovery from EMERGENCY HALT back to IDLE
    ax.annotate('', xy=(19, 54), xytext=(19, 38), arrowprops=dict(arrowstyle='->', lw=1.6, color='#666666'))
    ax.text(18, 46, 'Clear &\nReset', fontsize=7, ha='right', va='center', color='#4B5563', fontweight='bold')

    plt.tight_layout()
    plt.savefig('write_up/figures/fig_brain_state_machine.png', bbox_inches='tight')
    plt.close()
    print('✓ State machine diagram generated (Draw.io style).')


# ------------------------------------------------------------------------------
# MAIN RUNNER
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    generate_hardware_schematic()
    generate_system_architecture()
    generate_docker_deployment()
    generate_spatial_zone_figure()
    generate_feature_pipeline()
    generate_state_machine_figure()
    print('\nAll 6 figures generated successfully with unified Draw.io styling.')
