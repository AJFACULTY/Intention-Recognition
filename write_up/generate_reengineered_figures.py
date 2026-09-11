#!/usr/bin/env python3
"""
Publication-Grade Re-Engineered Figure Generator (Comprehensive Final Production Edition)
Covers all 6 primary architectural figures:
1. hardware_design.png: Mechatronic Hardware Architecture & Signal Distribution Flow
2. system_architecture.png: End-to-End Cognitive System Architecture (5 Standardized Tiers)
3. fig_spatial_zone.png: Spatial Receptive Zone Perception & ISO 5807 Gating Flow
4. fig_feature_pipeline.png: Real Hand Landmark Transformation & Neural Classifier Pipeline
5. fig_brain_state_machine.png: Supervisory Cognition OMG UML 2.5 State Machine
6. fig_docker_deployment.png: Containerized Multi-Node Deployment Architecture (Host Mode DDS)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

os.makedirs('write_up/preview_figures', exist_ok=True)
os.makedirs('write_up/figures', exist_ok=True)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'


def embed_photo_clean(ax, img_path, x, y, w, h, border_c='#64748B', bg_c='#FFFFFF', pad=0.3):
    """Embeds an image inside a rounded card preserving 100% native aspect ratio with zero distortion."""
    if not os.path.exists(img_path):
        return
    card = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15',
                                  fc=bg_c, ec=border_c, lw=1.1, zorder=2)
    ax.add_patch(card)
    
    ins_x = x + pad
    ins_y = y + pad
    ins_w = max(0.1, w - 2 * pad)
    ins_h = max(0.1, h - 2 * pad)
    
    ax_ins = ax.inset_axes([ins_x, ins_y, ins_w, ins_h], transform=ax.transData, zorder=3)
    img = Image.open(img_path)
    ax_ins.imshow(img, aspect='equal')
    ax_ins.axis('off')


def draw_parallelogram(ax, x, y, w, h, slant=0.08, fc='#EFF6FF', ec='#3B82F6', lw=1.4):
    dx = w * slant
    verts = [(x + dx, y), (x + w, y), (x + w - dx, y + h), (x, y + h), (x + dx, y)]
    poly = patches.Polygon(verts, closed=True, fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(poly)
    return poly


def draw_diamond(ax, cx, cy, w, h, fc='#FEF3C7', ec='#D97706', lw=1.5):
    verts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy), (cx, cy + h / 2)]
    poly = patches.Polygon(verts, closed=True, fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(poly)
    return poly


def draw_stadium(ax, x, y, w, h, fc='#F3E8FF', ec='#9333EA', lw=1.4):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2', fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(box)
    return box


def draw_uml_state(ax, x, y, w, h, title, actions, border_c='#3B82F6', bg_c='#EFF6FF', badge_c='#1D4ED8'):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.35', fc=bg_c, ec=border_c, lw=1.5, zorder=3)
    ax.add_patch(box)
    header_h = h * 0.30
    div_y = y + h - header_h
    ax.plot([x, x + w], [div_y, div_y], color=border_c, lw=1.1, zorder=4)
    ax.text(x + w / 2, y + h - header_h / 2, title, fontsize=8.4, fontweight='bold',
            ha='center', va='center', color=badge_c, zorder=5)
    ax.text(x + 1.2, div_y - 1.0, actions, fontsize=6.8, ha='left', va='top',
            color='#1E293B', family='sans-serif', linespacing=1.28, zorder=5)


# ==============================================================================
# 1. HARDWARE SYSTEM SCHEMATIC (Equal-Width Containers, Zero Distortion, Strict Order)
# ==============================================================================
def generate_reengineered_hardware_design(output_path='write_up/preview_figures/preview_hardware_design.png'):
    fig, ax = plt.subplots(figsize=(10.5, 9.8), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(-12, 102)
    ax.axis('off')

    ax.text(55, 99.5, 'Mechatronic Hardware Architecture & Signal Distribution Flow',
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # Top Sensors: USB Camera Gimbal & MS200 LiDAR
    embed_photo_clean(ax, 'write_up/figures/camera_gimbal.png', 8, 80, 20, 15, border_c='#0284C7')
    ax.text(18, 78.5, '2MP USB Camera (2-DOF Gimbal)\n640×480 @ 20 FPS | Wide-Angle',
            fontsize=7.0, fontweight='bold', ha='center', va='top', color='#0369A1')

    embed_photo_clean(ax, 'write_up/figures/ms200_lidar.jpg', 82, 80, 20, 15, border_c='#0284C7')
    ax.text(92, 78.5, 'MS200 2D ToF LiDAR Sensor\n360° Sweep | 12.5 Hz | 0.12–12 m',
            fontsize=7.0, fontweight='bold', ha='center', va='top', color='#0369A1')

    # Sensor data bus arrows into Pi 5
    ax.annotate('', xy=(18, 66.5), xytext=(18, 73.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(18, 70.0, 'USB 3.0 (/camera/image_raw)', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#38BDF8', lw=0.8))

    ax.annotate('', xy=(92, 66.5), xytext=(92, 73.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(92, 70.0, 'USB Serial (/scan @ 12.5Hz)', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#38BDF8', lw=0.8))

    # Tier 1: Primary Embedded SBC (Raspberry Pi 5) - Width: 96.5, x=7.5 to 104.0
    tier_w = 96.5
    tier_x = 7.5
    pi_box = patches.FancyBboxPatch((tier_x, 46), tier_w, 20, boxstyle='round,pad=0.4', fc='#F0F9FF', ec='#0284C7', lw=1.6)
    ax.add_patch(pi_box)
    embed_photo_clean(ax, 'write_up/figures/raspberry_pi_5.jpg', 9.5, 47.5, 20, 17, border_c='#0284C7')
    
    # Right-side Edge Compute Hub badge to balance Tier 1 with Tiers 2 & 3
    pi_hub_card = patches.FancyBboxPatch((88.0, 47.5), 14, 17, boxstyle='round,pad=0.2', fc='#E0F2FE', ec='#0284C7', lw=1.1)
    ax.add_patch(pi_hub_card)
    ax.text(95.0, 62.2, 'EDGE COMPUTE\nHUB', fontsize=6.8, fontweight='bold', ha='center', va='center', color='#0369A1')
    ax.text(95.0, 53.5, '• Dual USB 3.0\n• 40-Pin GPIO\n• PCIe 2.0 Bus\n• Docker Engine\n• Ubuntu 24.04',
            fontsize=5.8, ha='center', va='center', color='#0C4A6E', linespacing=1.22)

    ax.text(32, 63.2, 'Primary Embedded SBC: Raspberry Pi 5 (8GB RAM)', fontsize=9.2, fontweight='bold', color='#0369A1')
    
    # Concise, non-colliding bullet points tailored to width of 55 units
    pi_desc = (
        "• Compute Architecture: Quad-Core ARM Cortex-A76 @ 2.4 GHz | 8GB LPDDR4X\n"
        "• Operating Environment: Ubuntu 24.04 LTS (Kernel 6.8) | Docker (--net=host)\n"
        "• Vision Perception: YOLOv8n Spatial Gating (45% × 65%) + MediaPipe Landmarks\n"
        "• Supervisory Decision: Stateful ROS 2 Brain State Machine & SLAM Toolbox"
    )
    ax.text(32, 60.2, pi_desc, fontsize=6.9, va='top', color='#1E293B', linespacing=1.35)

    # Inter-board micro-ROS Bridge
    ax.annotate('', xy=(55, 38.5), xytext=(55, 45.5), arrowprops=dict(arrowstyle='<->', lw=2.0, color='#D97706'))
    ax.text(55, 42.0, 'High-Speed micro-ROS UART Serial Bridge (921,600 baud)\nBi-directional DDS: /cmd_vel (Twist), /odom_raw (Ticks), /imu/data_raw',
            fontsize=7.2, fontweight='bold', ha='center', va='center', color='#92400E',
            bbox=dict(boxstyle='round,pad=0.2', fc='#FEF3C7', ec='#F59E0B', lw=0.9))

    # Tier 2: Yahboom ESP32-S3 micro-ROS Board + Chassis Wiring - Width: 96.5
    esp_box = patches.FancyBboxPatch((tier_x, 17), tier_w, 20.5, boxstyle='round,pad=0.4', fc='#FEFCE8', ec='#EAB308', lw=1.6)
    ax.add_patch(esp_box)
    embed_photo_clean(ax, 'write_up/figures/microros_control_board.jpg', 9.5, 18.5, 18, 17.5, border_c='#EAB308')
    embed_photo_clean(ax, 'write_up/figures/robot_chassis_wiring.jpg', 88.0, 18.5, 14, 17.5, border_c='#EAB308')
    ax.text(29.5, 34.5, 'Embedded Microcontroller: Yahboom ESP32-S3 Board', fontsize=9.4, fontweight='bold', color='#A16207')
    esp_desc = (
        "• Real-Time OS: FreeRTOS micro-ROS Client (50 Hz Closed-Loop Velocity PID Cycle)\n"
        "• Inertial Measurement: Onboard 6-Axis MPU6050 IMU Transducer (/imu/data_raw)\n"
        "• Motor Drive Bridges: 4-Channel High-Current MOSFET H-Bridges (PWM Drive)\n"
        "• Encoder Decoding: Optical Quadrature Hall Feedback Interrupt Decoders\n"
        "• Chassis Harness: Multi-Rail DuPont & Heavy-Gauge Screw Terminal Bus"
    )
    ax.text(29.5, 31.5, esp_desc, fontsize=7.1, va='top', color='#422006', linespacing=1.3)

    # Actuation bus arrow into Mobile Base
    ax.annotate('', xy=(55, 7.5), xytext=(55, 16.5), arrowprops=dict(arrowstyle='->', lw=1.8, color='#16A34A'))
    ax.text(55, 12.0, '4-Channel PWM Drive Voltages & Quadrature Hall Feedback', fontsize=7.0,
            ha='center', va='center', fontweight='bold', color='#15803D',
            bbox=dict(boxstyle='round,pad=0.18', fc='#DCFCE7', ec='#86EFAC', lw=0.8))

    # Tier 3: Differential-Drive Mobile Base & Underside Drivetrain - Width: 96.5
    bot_box = patches.FancyBboxPatch((tier_x, -10), tier_w, 17, boxstyle='round,pad=0.4', fc='#F0FDF4', ec='#16A34A', lw=1.6)
    ax.add_patch(bot_box)
    embed_photo_clean(ax, 'write_up/figures/assembled_robot_real.jpg', 9.5, -8.8, 19, 14.5, border_c='#16A34A')
    embed_photo_clean(ax, 'write_up/figures/robot_drivetrain_underside.jpg', 88.0, -8.8, 14, 14.5, border_c='#16A34A')
    ax.text(30.5, 4.2, 'Differential-Drive Mobile Base & Actuation Chassis', fontsize=9.2, fontweight='bold', color='#15803D')
    bot_desc = (
        "• Geared DC Motors: 4× 310 DC Motors with 1:45 Precision Planetary Gearboxes\n"
        "• Optical Feedback: Dual-Channel Optical Quadrature Encoders (High-Resolution Ticks)\n"
        "• Chassis Structure: Solid Acrylic Lower Deck, Ground Bumpers, 12.6V 3S Li-ion Battery"
    )
    ax.text(30.5, 1.2, bot_desc, fontsize=7.1, va='top', color='#14532D', linespacing=1.3)

    # Clean Power Rail along left side with labeled terminals
    pwr_box = patches.FancyBboxPatch((0.5, -8), 4.2, 74, boxstyle='round,pad=0.18', fc='#FEF2F2', ec='#DC2626', lw=1.3)
    ax.add_patch(pwr_box)
    ax.text(2.6, 29.0, 'POWER RAIL  •  12.6V 3S Li-ion Battery  •  5V/5A Buck Regulator  •  VMOT 12.6V',
            fontsize=6.8, fontweight='bold', ha='center', va='center', color='#991B1B', rotation=90)

    # Labeled Power connections into Pi 5 (5V PD), ESP32 (12V VMOT), and Motors (12.6V BATT)
    # Positioned with zero collision
    ax.plot([4.7, 7.5], [56.0, 56.0], color='#EA580C', lw=1.5, linestyle='--')
    ax.text(6.1, 57.5, '5V PD', fontsize=5.6, ha='center', va='bottom', color='#EA580C', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='#EA580C', lw=0.6))
    
    ax.plot([4.7, 7.5], [27.0, 27.0], color='#DC2626', lw=1.5, linestyle='--')
    ax.text(6.1, 28.5, '12V', fontsize=5.6, ha='center', va='bottom', color='#DC2626', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='#DC2626', lw=0.6))
    
    ax.plot([4.7, 7.5], [-1.5, -1.5], color='#DC2626', lw=1.5, linestyle='--')
    ax.text(6.1, 0.0, '12.6V', fontsize=5.4, ha='center', va='bottom', color='#DC2626', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='#DC2626', lw=0.6))

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 2. SPATIAL ACCEPTANCE ZONE (Robot Camera Onboard POV + ISO 5807 Flowchart)
# ==============================================================================
def generate_reengineered_spatial_zone(output_path='write_up/preview_figures/preview_fig_spatial_zone.png'):
    fig = plt.figure(figsize=(13.2, 5.2), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.14,
                          top=0.86, bottom=0.06, left=0.04, right=0.96)

    # Panel (a): Robot Onboard Camera POV with Privacy-Blurred Bystanders
    ax1 = fig.add_subplot(gs[0, 0])
    img_bot = Image.open('write_up/figures/robot_spatial_zone_blurred.jpg')
    ax1.imshow(img_bot)
    ax1.axis('off')
    ax1.set_title('(a) Empirical Robot Camera Perception (/dev/video0)\n[Bystander Privacy Blur & Central Acceptance Zone HUD]',
                  fontsize=9.0, fontweight='bold', color='#0F172A', pad=8)

    # Panel (b): ISO 5807 Standard Gating Decision Flowchart
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis('off')
    ax2.set_title('(b) ISO 5807 Spatial Acceptance Gating Logic\n[Centroid Evaluation & Steering Error Computation]',
                  fontsize=9.0, fontweight='bold', color='#0F172A', pad=8)

    # Flowchart Nodes (Sized to fit text snugly with zero spillover)
    draw_parallelogram(ax2, 10, 84, 80, 10, slant=0.06, fc='#EFF6FF', ec='#3B82F6', lw=1.4)
    ax2.text(50, 89, 'INPUT: /camera/image_raw (640×480 @ 20 FPS)',
             fontsize=7.5, fontweight='bold', ha='center', va='center', color='#1E40AF')

    ax2.annotate('', xy=(50, 77), xytext=(50, 84), arrowprops=dict(arrowstyle='->', lw=1.6, color='#334155'))

    p_box = patches.FancyBboxPatch((12, 65), 76, 12, boxstyle='round,pad=0.2', fc='#F8FAFC', ec='#64748B', lw=1.4)
    ax2.add_patch(p_box)
    ax2.text(50, 71, 'YOLOv8n Person Centroid Localization\nExtract Bounding Box (Bx, By, Bw, Bh) → Centroid (Cx, Cy)',
             fontsize=7.0, ha='center', va='center', color='#0F172A', linespacing=1.2)

    ax2.annotate('', xy=(50, 56), xytext=(50, 65), arrowprops=dict(arrowstyle='->', lw=1.6, color='#334155'))

    draw_diamond(ax2, 50, 44, 76, 18, fc='#FEF3C7', ec='#D97706', lw=1.5)
    ax2.text(50, 44, 'Candidate Centroid inside Zone?\nCx ∈ [176, 464] ∧ Cy ∈ [84, 396]',
             fontsize=7.2, fontweight='bold', ha='center', va='center', color='#92400E', linespacing=1.2)

    # Branch [No]: Suppress (Left side: x=8 to 36, width 28)
    ax2.annotate('', xy=(12, 44), xytext=(6, 44), arrowprops=dict(arrowstyle='-', lw=1.5, color='#DC2626'))
    ax2.plot([6, 6], [44, 18], color='#DC2626', lw=1.5)
    ax2.annotate('', xy=(8, 18), xytext=(6, 18), arrowprops=dict(arrowstyle='->', lw=1.5, color='#DC2626'))
    ax2.text(9, 46, '[NO]', fontsize=7.2, fontweight='bold', ha='center', va='bottom', color='#DC2626')

    draw_stadium(ax2, 8, 11, 30, 14, fc='#FEE2E2', ec='#DC2626', lw=1.4)
    ax2.text(23, 18, 'Silent Suppression\nDrop Frame (v = 0)', fontsize=6.8, fontweight='bold',
             ha='center', va='center', color='#991B1B', linespacing=1.2)

    # Branch [Yes]: Accept & Compute Steering Error (Right side: x=44 to 96, width 52)
    ax2.annotate('', xy=(50, 28), xytext=(50, 35), arrowprops=dict(arrowstyle='->', lw=1.6, color='#16A34A'))
    ax2.text(52, 31.5, '[YES]', fontsize=7.2, fontweight='bold', ha='left', va='center', color='#15803D')

    acc_box = patches.FancyBboxPatch((44, 10), 52, 17, boxstyle='round,pad=0.2', fc='#DCFCE7', ec='#16A34A', lw=1.4)
    ax2.add_patch(acc_box)
    ax2.text(70, 18.5, 'Primary Operator Accepted\nCompute Heading Error: ex = Cx - 320\nVisual Servoing: v_ω = -1.5 × ex, vx = 0.20 m/s',
             fontsize=6.8, fontweight='bold', ha='center', va='center', color='#14532D', linespacing=1.25)

    fig.suptitle('Empirical Spatial Receptive Zone Gating & Bystander Suppression Flow',
                 fontsize=12.5, fontweight='bold', color='#0F172A', y=0.98)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 3. FEATURE PIPELINE (Real Hand Landmarks + Visible Inter-Stage Chevrons)
# ==============================================================================
def generate_reengineered_feature_pipeline(output_path='write_up/preview_figures/preview_fig_feature_pipeline.png'):
    fig = plt.figure(figsize=(14.2, 5.4), dpi=300)
    gs = fig.add_gridspec(1, 4, width_ratios=[1.15, 1.2, 1.1, 1.35], wspace=0.22,
                          top=0.88, bottom=0.06, left=0.03, right=0.97)

    # Stage 1: Real Hand with 21 Landmarks + Anatomical Callouts
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.axis('off')
    ax1.set_title('Stage 1: Real Hand Landmarks\n[MediaPipe 21 Joints]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage1_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax1.add_patch(stage1_box)

    # Mathematically exact card matching physical aspect ratio (515x983 hand in 14.2x5.4 figure)
    # W = 62.5, H = 74.0, centered at x = 18.75 -> Zero dead margin on all 4 sides!
    embed_photo_clean(ax1, 'write_up/figures/real_hand_landmarks_annotated.png', 18.75, 12.0, 62.5, 74.0, border_c='#3B82F6', pad=0.15)
    
    # Clean top topology badge
    ax1.text(50, 90.0, 'MediaPipe 21 Joint Topology (P0–P20)', fontsize=7.2, fontweight='bold', ha='center', va='center', color='#1E40AF')

    # Palm normalization reference formula at bottom
    ax1.text(50, 6.0, 'Palm Metric: W_palm = ||P5 - P17||_2', fontsize=7.0, fontweight='bold', ha='center', va='center',
             color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.18', fc='#EFF6FF', ec='#93C5FD', lw=0.8))

    # Stage 2: Geometric Invariance Transformations
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis('off')
    ax2.set_title('Stage 2: Invariance Transforms\n[Scale & Translation Proof]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage2_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax2.add_patch(stage2_box)

    c1 = patches.FancyBboxPatch((6, 73), 88, 20, boxstyle='round,pad=0.2', fc='#EFF6FF', ec='#3B82F6', lw=1.2)
    ax2.add_patch(c1)
    ax2.text(50, 87, '1. Translation Invariance', fontsize=7.6, fontweight='bold', ha='center', color='#1D4ED8')
    ax2.text(50, 78, "p'_i = p_i - p_0  (Origin at Wrist P0)", fontsize=7.2, ha='center', color='#1E293B')

    c2 = patches.FancyBboxPatch((6, 50), 88, 20, boxstyle='round,pad=0.2', fc='#FEFCE8', ec='#EAB308', lw=1.2)
    ax2.add_patch(c2)
    ax2.text(50, 64, '2. Scale & Distance Normalization', fontsize=7.6, fontweight='bold', ha='center', color='#A16207')
    ax2.text(50, 55, "p̂_i = p'_i / W_palm  (Normalized by Palm)", fontsize=7.2, ha='center', color='#1E293B')

    c3 = patches.FancyBboxPatch((6, 27), 88, 20, boxstyle='round,pad=0.2', fc='#F0FDF4', ec='#16A34A', lw=1.2)
    ax2.add_patch(c3)
    ax2.text(50, 41, '3. Finger Flexion Curl Angles', fontsize=7.6, fontweight='bold', ha='center', color='#15803D')
    ax2.text(50, 32, "θ_j = arccos((u·v) / (||u||·||v||))", fontsize=7.2, ha='center', color='#1E293B')

    c4 = patches.FancyBboxPatch((6, 6), 88, 18, boxstyle='round,pad=0.2', fc='#FAF5FF', ec='#A855F7', lw=1.2)
    ax2.add_patch(c4)
    ax2.text(50, 18, '4. Thumb Relative Vector', fontsize=7.6, fontweight='bold', ha='center', color='#7E22CE')
    ax2.text(50, 10, "Δp_thumb = p_4 - p_5  (Tip to MCP)", fontsize=7.2, ha='center', color='#1E293B')

    # Stage 3: 19-D Feature Representation
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 100)
    ax3.axis('off')
    ax3.set_title('Stage 3: 19-D Feature Vector\n[f ∈ ℝ¹⁹ Invariant Descriptor]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage3_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax3.add_patch(stage3_box)

    f1 = patches.FancyBboxPatch((6, 67), 88, 24, boxstyle='round,pad=0.2', fc='#EFF6FF', ec='#3B82F6', lw=1.2)
    ax3.add_patch(f1)
    ax3.text(10, 84, 'Finger Curl Angles (5-D)', fontsize=7.4, fontweight='bold', color='#1D4ED8')
    ax3.text(10, 73, '[θ_thumb, θ_index, θ_middle,\n θ_ring, θ_pinky]', fontsize=7.0, color='#1E293B', linespacing=1.2)

    f2 = patches.FancyBboxPatch((6, 38), 88, 24, boxstyle='round,pad=0.2', fc='#FEFCE8', ec='#EAB308', lw=1.2)
    ax3.add_patch(f2)
    ax3.text(10, 55, 'Tip-to-Wrist Distances (5-D)', fontsize=7.4, fontweight='bold', color='#A16207')
    ax3.text(10, 44, '[d(P4,P0), d(P8,P0), d(P12,P0),\n d(P16,P0), d(P20,P0)] / W_palm', fontsize=7.0, color='#1E293B', linespacing=1.2)

    f3 = patches.FancyBboxPatch((6, 9), 88, 24, boxstyle='round,pad=0.2', fc='#F0FDF4', ec='#16A34A', lw=1.2)
    ax3.add_patch(f3)
    ax3.text(10, 26, 'Relative Displacements (9-D)', fontsize=7.4, fontweight='bold', color='#15803D')
    ax3.text(10, 15, '• Thumb-Index Vector: (Δx, Δy, Δz)\n• Inter-Tip Spreads: 4 Spacing Dists\n• Palm Aspect Ratio: W_palm / L_palm', fontsize=6.7, color='#1E293B', linespacing=1.2)

    # Stage 4: MLP Neural Network & 6 Discrete Action Tokens
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.set_xlim(0, 100)
    ax4.set_ylim(0, 100)
    ax4.axis('off')
    ax4.set_title('Stage 4: MLP Classifier & Actions\n[1.2 ms Latency | 99.38% Accuracy]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage4_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax4.add_patch(stage4_box)

    # Neural Network Node Diagram
    layers = [3, 5, 4, 3]
    layer_x = [15, 38, 62, 85]
    layer_names = ['Input\n19-D', 'Hidden 1\n64 (ReLU)', 'Hidden 2\n32 (ReLU)', 'Output\n6 (Softmax)']
    for l_idx, (num_nodes, lx) in enumerate(zip(layers, layer_x)):
        ys = np.linspace(58, 86, num_nodes)
        for y in ys:
            circle = plt.Circle((lx, y), 2.2, fc='#3B82F6', ec='#1D4ED8', lw=1.0, zorder=4)
            ax4.add_patch(circle)
        ax4.text(lx, 52, layer_names[l_idx], fontsize=6.2, ha='center', va='top', color='#334155', fontweight='bold')

    for l_idx in range(len(layers) - 1):
        x_a = layer_x[l_idx]
        x_b = layer_x[l_idx + 1]
        ys_a = np.linspace(58, 86, layers[l_idx])
        ys_b = np.linspace(58, 86, layers[l_idx + 1])
        for ya in ys_a:
            for yb in ys_b:
                ax4.plot([x_a, x_b], [ya, yb], color='#CBD5E1', lw=0.45, zorder=2)

    # 6 Discrete Tokens
    tokens = [
        ('STOP', '#DC2626', '#FEE2E2', 8, 30),
        ('GO', '#16A34A', '#DCFCE7', 38, 30),
        ('FOLLOW', '#9333EA', '#F3E8FF', 68, 30),
        ('LEFT', '#2563EB', '#DBEAFE', 8, 15),
        ('RIGHT', '#2563EB', '#DBEAFE', 38, 15),
        ('BACK', '#D97706', '#FEF3C7', 68, 15),
    ]
    for name, ec, fc, tx, ty in tokens:
        draw_stadium(ax4, tx, ty, 26, 11, fc=fc, ec=ec, lw=1.2)
        ax4.text(tx + 13, ty + 5.5, name, fontsize=7.2, fontweight='bold', ha='center', va='center', color=ec)

    # Performance badge at bottom
    ax4.text(50, 6.2, 'Latency: 1.2 ms | Test Acc: 99.38% | Latency Budget: 132 ms',
             fontsize=6.5, fontweight='bold', ha='center', va='center', color='#0F172A',
             bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#CBD5E1', lw=0.8))

    fig.suptitle('Real-Time MediaPipe Feature Engineering & Invariant Neural Classifier Pipeline',
                 fontsize=12.5, fontweight='bold', color='#0F172A', y=0.98)

    # Visible Inter-Stage Sequential Flow Chevrons in Figure Coordinates
    fig.canvas.draw()
    bbox1 = ax1.get_position()
    bbox2 = ax2.get_position()
    bbox3 = ax3.get_position()
    bbox4 = ax4.get_position()

    arrow_y = (bbox1.y0 + bbox1.y1) / 2.0
    arrow_pairs = [
        (bbox1.x1 + 0.005, bbox2.x0 - 0.005, '#3B82F6'),
        (bbox2.x1 + 0.005, bbox3.x0 - 0.005, '#EAB308'),
        (bbox3.x1 + 0.005, bbox4.x0 - 0.005, '#16A34A'),
    ]
    for x_start, x_end, col in arrow_pairs:
        arrow = patches.FancyArrowPatch((x_start, arrow_y), (x_end, arrow_y),
                                        transform=fig.transFigure,
                                        arrowstyle='-|>', mutation_scale=16,
                                        lw=2.4, color=col, zorder=10)
        fig.patches.append(arrow)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 4. BRAIN STATE MACHINE (Zero Collisions, Unobstructed Preemption, Clean UML)
# ==============================================================================
def generate_reengineered_brain_state_machine(output_path='write_up/preview_figures/preview_fig_brain_state_machine.png'):
    fig, ax = plt.subplots(figsize=(13.6, 5.8), dpi=300)
    ax.set_xlim(0, 142)
    ax.set_ylim(0, 76)
    ax.axis('off')

    ax.text(71, 73.5, 'Supervisory Cognition: OMG UML 2.5 Brain State Machine & Safety Preemption',
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # Initial Pseudo-State
    init_circle = plt.Circle((4, 49.75), 2.0, fc='#0F172A', ec='#0F172A', zorder=5)
    ax.add_patch(init_circle)
    ax.annotate('', xy=(8, 49.75), xytext=(6.0, 49.75), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0F172A'))

    # Compact state height: h = 16.5 perfectly hugs the 3 action lines!
    st_h = 16.5

    # State 1: IDLE / STANDBY (x=8 to 38, width 30, y=41.5 to 58.0)
    draw_uml_state(ax, 8, 41.5, 30, st_h, '1. IDLE / STANDBY',
                   "entry / stop_motors()\n"
                   "do / monitor_heartbeat()\n"
                   "exit / log_activation()",
                   border_c='#64748B', bg_c='#F8FAFC', badge_c='#334155')

    # State 2: WAITING_CONFIRM (x=52 to 84, width 32, y=41.5 to 58.0)
    draw_uml_state(ax, 52, 41.5, 32, st_h, '2. WAITING_CONFIRM',
                   "entry / start_consensus_timer()\n"
                   "do / filter_sliding_window()\n"
                   "exit / publish_consensus()",
                   border_c='#D97706', bg_c='#FEFCE8', badge_c='#B45309')

    # State 3: EXECUTING_MOTION (x=98 to 134, width 36, y=41.5 to 58.0)
    draw_uml_state(ax, 98, 41.5, 36, st_h, '3. EXECUTING_MOTION',
                   "entry / dispatch_cmd_vel()\n"
                   "do / monitor_odom_progress()\n"
                   "exit / zero_velocity()",
                   border_c='#16A34A', bg_c='#DCFCE7', badge_c='#15803D')

    # State 4: FOLLOW MODE (Visual Servoing) (x=76 to 132, width 56, y=9.5 to 26.0)
    draw_uml_state(ax, 76, 9.5, 56, st_h, '4. FOLLOW MODE (Visual Servoing)',
                   "entry / init_servoing_loop()\n"
                   "do / compute_heading_error(ex = Cx - 320)\n"
                   "do / steer(v_ω = -1.5 × ex, vx = 0.20 m/s)\n"
                   "exit / zero_velocity()",
                   border_c='#2563EB', bg_c='#DBEAFE', badge_c='#1D4ED8')

    # State 5: EMERGENCY HALT [OVERRIDE] (x=8 to 42, width 34, y=9.5 to 26.0)
    draw_uml_state(ax, 8, 9.5, 34, st_h, '5. EMERGENCY HALT [OVERRIDE]',
                   "entry / FORCE_ZERO_VELOCITY()\n"
                   "entry / clear_consensus_buffers()\n"
                   "do / engage_hardware_lockout()\n"
                   "exit / require_manual_reset()",
                   border_c='#DC2626', bg_c='#FEE2E2', badge_c='#991B1B')

    # Forward Transition 1 -> 2 (Gap x=38 to 52, width 14)
    ax.annotate('', xy=(52, 49.75), xytext=(38, 49.75), arrowprops=dict(arrowstyle='->', lw=1.8, color='#334155'))
    ax.text(45, 53.0, 'Operator\nin Zone', fontsize=6.8, ha='center', va='bottom',
            fontweight='bold', color='#1E293B', bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#CBD5E1', lw=0.8))

    # Transition 2 -> 3 (Gap x=84 to 98, width 14)
    ax.annotate('', xy=(98, 49.75), xytext=(84, 49.75), arrowprops=dict(arrowstyle='->', lw=1.8, color='#16A34A'))
    ax.text(91, 53.0, 'Consensus\n[Votes >= 3/5]', fontsize=6.8, ha='center', va='bottom',
            fontweight='bold', color='#15803D', bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#86EFAC', lw=0.8))

    # Timeout Return Arc from State 3 to State 1
    ax.plot([116, 116, 23, 23], [58.0, 65.5, 65.5, 58.0], color='#64748B', lw=1.6)
    ax.annotate('', xy=(23, 58.0), xytext=(23, 59.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#64748B'))
    ax.text(69.5, 65.5, 'Timeout [t > 3.0s] / Motion Complete', fontsize=7.4, ha='center', va='center',
            fontweight='bold', color='#334155', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#64748B', lw=0.9))

    # Follow Transition from State 3 to State 4
    ax.annotate('', xy=(106, 26.0), xytext=(106, 41.5), arrowprops=dict(arrowstyle='->', lw=1.8, color='#2563EB'))
    ax.text(108, 33.75, 'Gesture == FOLLOW', fontsize=7.4, ha='left', va='center',
            fontweight='bold', color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#93C5FD', lw=0.8))

    # FOLLOW Return Route to State 1 via right margin into top return arc (ZERO line crossings!)
    ax.plot([132, 136, 136, 116], [17.75, 17.75, 65.5, 65.5], color='#2563EB', lw=1.5, linestyle=':')
    ax.text(135.5, 38.0, 'Operator Lost\n[STOP]', fontsize=6.4, ha='center', va='center',
            fontweight='bold', color='#1D4ED8', rotation=-90,
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#93C5FD', lw=0.8))

    # Asynchronous Preemption Route: Dropping down along x=46 from State 2 into State 5 (ZERO line crossings!)
    ax.plot([56, 46, 46, 42], [41.5, 41.5, 17.75, 17.75], color='#DC2626', lw=2.0, linestyle='--')
    ax.annotate('', xy=(42, 17.75), xytext=(44, 17.75), arrowprops=dict(arrowstyle='->', lw=2.0, color='#DC2626'))

    # Warning badge placed in the open space x in [49, 73], y in [22, 30] - ZERO OVERLAP with any state or line!
    shield_box = patches.FancyBboxPatch((49.0, 20.0), 24.5, 7.5, boxstyle='round,pad=0.2', fc='#FEF2F2', ec='#DC2626', lw=1.2)
    ax.add_patch(shield_box)
    ax.text(61.25, 23.75, '⚡ ASYNCHRONOUS PREEMPTION\n[LiDAR < 0.36m] OR [/joy Kill]',
            fontsize=6.2, ha='center', va='center', color='#991B1B', fontweight='bold', linespacing=1.2)

    # Emergency Recovery back into State 1
    ax.annotate('', xy=(14, 41.5), xytext=(14, 26.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#64748B'))
    ax.text(13, 33.75, 'Clear Obstacle\n& Reset', fontsize=6.8, ha='right', va='center', fontweight='bold', color='#475569')

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 5. COGNITIVE SYSTEM ARCHITECTURE (Equal-Width Tiers, Dual Visual Anchors)
# ==============================================================================
def generate_reengineered_system_architecture(output_path='write_up/preview_figures/preview_system_architecture.png'):
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=300)
    ax.set_xlim(0, 118)
    ax.set_ylim(-12, 106)
    ax.axis('off')

    ax.text(58.0, 103.5, 'Autonomous Mobile Robot Cognitive System Architecture',
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # All Tiers share the EXACT same width: tier_w = 98.0, x=8.0 to x=106.0
    tier_w = 98.0
    tier_x = 8.0

    # Tier 1: Sensing Layer (Camera, LiDAR, IMU)
    t1_box = patches.FancyBboxPatch((tier_x, 82), tier_w, 18, boxstyle='round,pad=0.35', fc='#F8FAFC', ec='#64748B', lw=1.4)
    ax.add_patch(t1_box)
    embed_photo_clean(ax, 'write_up/figures/camera_gimbal.png', tier_x + 2.0, 83.5, 18, 15, border_c='#0284C7')
    embed_photo_clean(ax, 'write_up/figures/ms200_lidar.jpg', tier_x + tier_w - 20.0, 83.5, 18, 15, border_c='#0284C7')
    ax.text(57.0, 96.5, 'Tier 1: Physical Sensing & Environment Transduction', fontsize=8.8, fontweight='bold', ha='center', color='#0F172A')
    t1_desc = (
        "• 2MP Camera on 2-DOF Gimbal: 640×480 @ 20 FPS (/camera/image_raw)\n"
        "• MS200 2D ToF LiDAR: 360° Planar Sweep, 0.12–12 m @ 12.5 Hz (/scan)\n"
        "• Onboard MPU6050 6-Axis IMU: Real-Time Inertial Transduction @ 50 Hz"
    )
    ax.text(57.0, 93.2, t1_desc, fontsize=6.5, ha='center', va='top', color='#334155', linespacing=1.22)

    ax.annotate('', xy=(57.0, 75.0), xytext=(57.0, 82.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(57.0, 78.5, 'Raw Sensor Telemetry (/camera/image_raw, /scan, /imu/data)', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#38BDF8', lw=0.8))

    # Tier 2: Spatial Gating & Skeletal Tracking (With robot camera POV + Right Badge)
    t2_box = patches.FancyBboxPatch((tier_x, 59.5), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#F0F9FF', ec='#0284C7', lw=1.6)
    ax.add_patch(t2_box)
    embed_photo_clean(ax, 'write_up/figures/robot_spatial_zone_blurred.jpg', tier_x + 2.0, 60.5, 18, 13.5, border_c='#0284C7')
    
    # Right-side Spatial Zone Badge
    t2_badge = patches.FancyBboxPatch((tier_x + tier_w - 20.0, 60.5), 18, 13.5, boxstyle='round,pad=0.2', fc='#E0F2FE', ec='#0284C7', lw=1.1)
    ax.add_patch(t2_badge)
    ax.text(tier_x + tier_w - 11.0, 70.8, 'CENTRAL HUD\n[45% × 65%]', fontsize=6.6, fontweight='bold', ha='center', va='center', color='#0369A1')
    ax.text(tier_x + tier_w - 11.0, 64.5, '• Centroid Gating\n• ex = Cx - 320\n• Periphery Drop\n• Bystander Lock',
            fontsize=5.8, ha='center', va='center', color='#0C4A6E', linespacing=1.18)

    ax.text(tier_x + 22.0, 71.8, 'Tier 2: Edge Perception & Spatial Acceptance Gating', fontsize=8.8, fontweight='bold', color='#0369A1')
    t2_desc = (
        "• YOLOv8n Gating: Isolates candidate operator within 45% W × 65% H ROI\n"
        "• Bystander Lockout: Peripheral detections dropped to prevent spurious tracking\n"
        "• MediaPipe HandLandmarker: Localizes 21 3D anatomical hand landmarks"
    )
    ax.text(tier_x + 22.0, 68.8, t2_desc, fontsize=6.5, va='top', color='#1E293B', linespacing=1.22)

    ax.annotate('', xy=(57.0, 52.5), xytext=(57.0, 59.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(57.0, 56.0, '21 Hand Landmarks & Isolated Operator Centroid', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#64748B', lw=0.8))

    # Tier 3: Feature Extraction & Neural Classifier (Real Hand + Right Badge)
    t3_box = patches.FancyBboxPatch((tier_x, 37.0), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#FEFCE8', ec='#EAB308', lw=1.6)
    ax.add_patch(t3_box)
    embed_photo_clean(ax, 'write_up/figures/real_hand_landmarks_annotated.png', tier_x + 2.0, 38.0, 18, 13.5, border_c='#EAB308')
    
    # Right-side MLP Classifier Badge
    t3_badge = patches.FancyBboxPatch((tier_x + tier_w - 20.0, 38.0), 18, 13.5, boxstyle='round,pad=0.2', fc='#FEF9C3', ec='#EAB308', lw=1.1)
    ax.add_patch(t3_badge)
    ax.text(tier_x + tier_w - 11.0, 48.3, 'MLP CLASSIFIER\n[ONNX Runtime]', fontsize=6.6, fontweight='bold', ha='center', va='center', color='#A16207')
    ax.text(tier_x + tier_w - 11.0, 42.0, '• 19-D Invariant\n• 64 → 32 ReLUs\n• 1.2 ms Latency\n• 99.38% Test Acc',
            fontsize=5.8, ha='center', va='center', color='#713F12', linespacing=1.18)

    ax.text(tier_x + 22.0, 49.3, 'Tier 3: Geometric Feature Extraction & Neural Classifier', fontsize=8.8, fontweight='bold', color='#A16207')
    t3_desc = (
        "• 19-D Feature Vector: Scale & distance-invariant curls, spreads, and distances\n"
        "• MLP Architecture: 19 → 64 (ReLU) → 32 (ReLU) → 6 (Softmax) Classifier\n"
        "• Edge Inference: ONNX Runtime native execution @ 10 Hz | 1.2 ms latency"
    )
    ax.text(tier_x + 22.0, 46.3, t3_desc, fontsize=6.5, va='top', color='#422006', linespacing=1.22)

    ax.annotate('', xy=(57.0, 30.0), xytext=(57.0, 37.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#EAB308'))
    ax.text(57.0, 33.5, 'Discrete Gesture Tokens (/cognition/gesture)', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#EAB308', lw=0.8))

    # Tier 4: Cognition & Supervisory Control (Balanced with Left and Right Badges)
    t4_box = patches.FancyBboxPatch((tier_x, 14.5), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#FAF5FF', ec='#A855F7', lw=1.6)
    ax.add_patch(t4_box)
    
    # Left Cognition Diagram Badge
    cog_card = patches.FancyBboxPatch((tier_x + 2.0, 15.5), 18, 13.5, boxstyle='round,pad=0.2', fc='#F3E8FF', ec='#A855F7', lw=1.1)
    ax.add_patch(cog_card)
    ax.text(tier_x + 11.0, 25.8, 'SUPERVISORY\nCOGNITION', fontsize=6.6, fontweight='bold', ha='center', va='center', color='#7E22CE')
    ax.text(tier_x + 11.0, 19.5, '• 5-State FSM\n• 3/5 Consensus\n• LSTM Predictor\n• 1.5s Horizon',
            fontsize=5.8, ha='center', va='center', color='#4C1D95', linespacing=1.18)

    # Right Safety Interlock Badge
    safety_card = patches.FancyBboxPatch((tier_x + tier_w - 20.0, 15.5), 18, 13.5, boxstyle='round,pad=0.2', fc='#FEE2E2', ec='#DC2626', lw=1.1)
    ax.add_patch(safety_card)
    ax.text(tier_x + tier_w - 11.0, 25.8, 'SAFETY\nINTERLOCK', fontsize=6.6, fontweight='bold', ha='center', va='center', color='#991B1B')
    ax.text(tier_x + tier_w - 11.0, 19.5, '• LiDAR < 0.36m\n• Async Preemption\n• Zero Latency\n• ISO 15066 Safe',
            fontsize=5.8, ha='center', va='center', color='#7F1D1D', linespacing=1.18)

    ax.text(tier_x + 22.0, 26.8, 'Tier 4: Supervisory Cognition & Trajectory Planning', fontsize=8.8, fontweight='bold', color='#7E22CE')
    t4_desc = (
        "• ROS 2 brain_node: 5-State Machine with sliding window consensus filter (3/5)\n"
        "• LSTM Intent Predictor: 5-step ahead human trajectory forecasting (1.5s horizon)\n"
        "• Deterministic Safety: Direct preemption on LiDAR proximity (< 0.36 m)"
    )
    ax.text(tier_x + 22.0, 23.8, t4_desc, fontsize=6.5, va='top', color='#3B0764', linespacing=1.22)

    ax.annotate('', xy=(57.0, 7.5), xytext=(57.0, 14.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#A855F7'))
    ax.text(57.0, 11.0, 'Velocity Setpoints (/cmd_vel via micro-ROS UART @ 921,600 baud)', fontsize=6.6, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#A855F7', lw=0.8))

    # Tier 5: Physical Execution & Mechatronics
    t5_box = patches.FancyBboxPatch((tier_x, -10.0), tier_w, 17.5, boxstyle='round,pad=0.35', fc='#F0FDF4', ec='#16A34A', lw=1.6)
    ax.add_patch(t5_box)
    embed_photo_clean(ax, 'write_up/figures/microros_control_board.jpg', tier_x + 2.0, -8.5, 18, 14.5, border_c='#16A34A')
    embed_photo_clean(ax, 'write_up/figures/assembled_robot_real.jpg', tier_x + tier_w - 20.0, -8.5, 18, 14.5, border_c='#16A34A')
    ax.text(tier_x + 22.0, 4.5, 'Tier 5: Real-Time Actuation, Motor Control & Mobile Base', fontsize=9.0, fontweight='bold', color='#15803D')
    t5_desc = (
        "• ESP32-S3 micro-ROS Client: Deterministic 50 Hz closed-loop PID velocity control\n"
        "• Actuation Subsystem: 4× 310 DC Geared Motors with 1:45 Planetary Gearboxes\n"
        "• Odometry Feedback: Dual-channel optical quadrature encoders publish /odom_raw"
    )
    ax.text(tier_x + 22.0, 1.5, t5_desc, fontsize=6.6, va='top', color='#14532D', linespacing=1.22)

    # Direct LiDAR Safety Bypass Interlock Line (Red dashed line down to Tier 4)
    ax.plot([102, 110, 110, 106], [83.5, 83.5, 22.0, 22.0], color='#DC2626', lw=1.8, linestyle='--')
    ax.annotate('', xy=(106, 22.0), xytext=(108, 22.0), arrowprops=dict(arrowstyle='->', lw=1.8, color='#DC2626'))
    ax.text(111.5, 52.0, 'DIRECT HARDWARE SAFETY BYPASS (LiDAR Obstacle < 0.36 m → Immediate Halt)',
            fontsize=6.2, fontweight='bold', color='#DC2626', rotation=-90, va='center', ha='left')

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 6. DOCKER DEPLOYMENT ARCHITECTURE (Publication Grade, Zero Text Collisions)
# ==============================================================================
def generate_reengineered_docker_deployment(output_path='write_up/preview_figures/preview_fig_docker_deployment.png'):
    fig, ax = plt.subplots(figsize=(13.6, 8.0), dpi=300)
    ax.set_xlim(0, 136)
    ax.set_ylim(0, 94)
    ax.axis('off')

    # Main Title
    ax.text(68, 91.5, 'Containerized Multi-Node Deployment Architecture (Docker Host Mode & DDS Loopback)',
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # --------------------------------------------------------------------------
    # LEFT CONTAINER: Raspberry Pi 5 Host OS (x=4 to 88, y=6 to 87)
    # --------------------------------------------------------------------------
    host_box = patches.FancyBboxPatch((4, 6), 84, 81, boxstyle='round,pad=0.7',
                                      fc='#F8FAFC', ec='#475569', lw=1.8, linestyle='--')
    ax.add_patch(host_box)
    
    # Unified Header Bar across top of Pi 5 host (x=6 to 86, y=80.0 to 85.8)
    hdr_box = patches.FancyBboxPatch((6, 79.8), 80, 5.8, boxstyle='round,pad=0.2', fc='#E2E8F0', ec='#94A3B8', lw=1.0)
    ax.add_patch(hdr_box)
    ax.text(46, 83.6, 'Primary Embedded Host Computer: Raspberry Pi 5 (8GB DDR4 RAM)',
            fontsize=8.6, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(46, 81.4, 'Ubuntu 24.04 LTS (Kernel 6.8)  |  Docker Engine 24.0  |  Network: --net=host',
            fontsize=7.2, ha='center', va='center', color='#475569', style='italic')

    # 1. Container: yahboom_base (Hardware Drivers) - Top Left (x=7 to 43, y=44 to 77)
    c1_box = patches.FancyBboxPatch((7, 44), 36, 33, boxstyle='round,pad=0.3', fc='#EFF6FF', ec='#3B82F6', lw=1.4)
    ax.add_patch(c1_box)
    ax.text(25, 74.2, 'Container: yahboom_base\n[Hardware Driver Services]',
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#1D4ED8', linespacing=1.2)
    ax.plot([7, 43], [70.5, 70.5], color='#3B82F6', lw=0.9)
    c1_text = (
        "• MS200 LiDAR Node (/scan @ 12.5 Hz)\n"
        "• Serial Port Binding (/dev/ttyUSB0)\n"
        "• 6-Axis IMU Publisher (/imu @ 50 Hz)\n"
        "• Differential Odometry Transformer\n"
        "• Base Coordinate TF Broadcaster\n"
        "  (base_footprint -> odom)\n"
        "• Device Privilege: --privileged"
    )
    ax.text(8.5, 68.8, c1_text, fontsize=6.8, va='top', color='#1E293B', linespacing=1.28)

    # 2. Container: micro_ros_agent (Bridge) - Bottom Left (x=7 to 43, y=8 to 40)
    c2_box = patches.FancyBboxPatch((7, 8), 36, 32, boxstyle='round,pad=0.3', fc='#FEFCE8', ec='#EAB308', lw=1.4)
    ax.add_patch(c2_box)
    ax.text(25, 37.2, 'Container: micro_ros_agent\n[Deterministic Hardware Bridge]',
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#A16207', linespacing=1.2)
    ax.plot([7, 43], [33.5, 33.5], color='#EAB308', lw=0.9)
    c2_text = (
        "• micro-ROS Agent Daemon (Client Bridge)\n"
        "• Hardware UART Link @ 921,600 Baud\n"
        "• Subscribes: /cmd_vel (Twist Commands)\n"
        "• Publishes: /odom_raw (Wheel Ticks)\n"
        "• Publishes: /battery_state (12.6V Telemetry)\n"
        "• Deterministic 50 Hz Hardware Clock"
    )
    ax.text(8.5, 31.8, c2_text, fontsize=6.8, va='top', color='#422006', linespacing=1.28)

    # 3. Container: yahboom_gesture (Cognition Pipeline) - Middle Column (x=50 to 86, y=8 to 77)
    c3_box = patches.FancyBboxPatch((50, 8), 36, 69, boxstyle='round,pad=0.3', fc='#F0FDF4', ec='#16A34A', lw=1.5)
    ax.add_patch(c3_box)
    ax.text(68, 74.2, 'Container: yahboom_gesture\n[Edge Vision & Decision Cognition]',
            fontsize=8.4, fontweight='bold', ha='center', va='center', color='#15803D', linespacing=1.2)
    ax.plot([50, 86], [70.5, 70.5], color='#16A34A', lw=0.9)

    c3_sections = [
        ("1. camera_pub (20 FPS)",
         "• Video capture: /dev/video0\n• Publishes: /camera/image_raw", 68.2),
        ("2. person_detection_node (YOLOv8n)",
         "• Spatial zone gating (45% W × 65% H)\n• Isolates closest operator in frame\n• Publishes: /cognition/detection", 58.8),
        ("3. gesture_node (10 Hz, 1.2 ms)",
         "• MediaPipe HandLandmarker (21 3D pts)\n• 19 Geometric Feature extraction\n• MLP ONNX Classifier (99.38% test acc)\n• Publishes: /cognition/gesture", 46.2),
        ("4. brain_node (Supervisory Logic)",
         "• 3/5 Majority filter & 3s execution lock\n• Visual servoing steering (Kp = 1.5)\n• LiDAR Emergency Preemption (< 0.36 m)\n• Publishes: /cmd_vel to motor base", 29.5),
    ]
    for sec_title, sec_body, y_pos in c3_sections:
        ax.text(52, y_pos, sec_title, fontsize=7.1, fontweight='bold', color='#15803D')
        ax.text(53, y_pos - 1.6, sec_body, fontsize=6.5, va='top', color='#14532D', linespacing=1.22)

    # Inter-Container Connectors (DDS Shared Memory Loopback) - Clean 7-unit channel (x=43 to 50)
    ax.annotate('', xy=(50, 60), xytext=(43, 60), arrowprops=dict(arrowstyle='<->', lw=1.8, color='#3B82F6'))
    ax.text(46.5, 64.2, 'DDS Loopback\n/scan, /camera', fontsize=6.0, ha='center', va='center',
            fontweight='bold', color='#1D4ED8',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#3B82F6', lw=0.8))

    ax.annotate('', xy=(50, 24), xytext=(43, 24), arrowprops=dict(arrowstyle='<->', lw=1.8, color='#D97706'))
    ax.text(46.5, 28.2, 'micro-ROS Bridge\n/cmd_vel, /odom', fontsize=6.0, ha='center', va='center',
            fontweight='bold', color='#B45309',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#D97706', lw=0.8))

    # --------------------------------------------------------------------------
    # RIGHT CONTAINER: Engineering Host Workstation (x=102 to 134, y=6 to 87)
    # --------------------------------------------------------------------------
    ws_box = patches.FancyBboxPatch((102, 6), 32, 81, boxstyle='round,pad=0.7',
                                    fc='#FAF5FF', ec='#9333EA', lw=1.8)
    ax.add_patch(ws_box)
    ax.text(118, 83.6, 'Engineering Host Workstation\n(x86_64 Development PC)',
            fontsize=8.6, fontweight='bold', ha='center', va='center', color='#7E22CE', linespacing=1.2)
    ax.plot([102, 134], [79.8, 79.8], color='#9333EA', lw=0.9)

    ws_text = (
        "• Compute Workstation:\n"
        "  AMD Ryzen 5 | 8GB RAM | Ubuntu 24.04\n"
        "  ROS 2 Humble Development Workspace\n\n"
        "• RViz2 Operational Visualization:\n"
        "  - /scan (LiDAR 2D planar point cloud)\n"
        "  - /map (SLAM Toolbox occupancy grid)\n"
        "  - /tf dynamic coordinate frames tree\n"
        "  - Camera compressed frame display\n\n"
        "• Safety & Manual Intervention:\n"
        "  - Low-latency joystick override (/joy)\n"
        "  - Asynchronous teleoperation E-stop\n\n"
        "• Simulation & Sim-to-Real Twin:\n"
        "  - Gazebo Harmonic digital twin physics\n"
        "  - Sensor noise & friction calibration\n\n"
        "• Deep Learning Edge Toolchain:\n"
        "  - PyTorch MLP & LSTM gesture training\n"
        "  - ONNX runtime model optimization"
    )
    ax.text(104, 77.2, ws_text, fontsize=6.6, va='top', color='#3B0764', linespacing=1.24)

    # High-Speed Wi-Fi DDS Network Link in Wide 14-unit Channel (x=88 to 102) - ZERO OVERLAP!
    ax.annotate('', xy=(102, 45), xytext=(88, 45),
                arrowprops=dict(arrowstyle='<->', lw=2.2, color='#7C3AED', linestyle=':'))
    ax.text(95.0, 50.5, 'Wi-Fi 5 GHz DDS Link\nROS_DOMAIN_ID=0', fontsize=6.8, ha='center', va='bottom',
            fontweight='bold', color='#6D28D9',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#7C3AED', lw=0.9))

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


def generate_all_production_figures():
    print("================================================================================")
    print("GENERATING ALL 6 PUBLICATION-GRADE PRODUCTION RE-ENGINEERED FIGURES")
    print("================================================================================")
    
    # Generate into preview_figures/
    generate_reengineered_hardware_design('write_up/preview_figures/preview_hardware_design.png')
    generate_reengineered_spatial_zone('write_up/preview_figures/preview_fig_spatial_zone.png')
    generate_reengineered_feature_pipeline('write_up/preview_figures/preview_fig_feature_pipeline.png')
    generate_reengineered_brain_state_machine('write_up/preview_figures/preview_fig_brain_state_machine.png')
    generate_reengineered_system_architecture('write_up/preview_figures/preview_system_architecture.png')
    generate_reengineered_docker_deployment('write_up/preview_figures/preview_fig_docker_deployment.png')

    # Also generate directly into production write_up/figures/
    generate_reengineered_hardware_design('write_up/figures/hardware_design.png')
    generate_reengineered_spatial_zone('write_up/figures/fig_spatial_zone.png')
    generate_reengineered_feature_pipeline('write_up/figures/fig_feature_pipeline.png')
    generate_reengineered_brain_state_machine('write_up/figures/fig_brain_state_machine.png')
    generate_reengineered_system_architecture('write_up/figures/system_architecture.png')
    generate_reengineered_docker_deployment('write_up/figures/fig_docker_deployment.png')

    print("\n✓ ALL 6 PRODUCTION FIGURES GENERATED SUCCESSFULLY IN write_up/figures/ AND preview_figures/")


if __name__ == '__main__':
    generate_all_production_figures()
