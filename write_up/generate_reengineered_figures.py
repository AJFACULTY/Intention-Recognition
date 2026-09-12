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
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.25,rounding_size=3.5',
                                 fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(box)
    return box


def draw_process(ax, x, y, w, h, fc='#F8FAFC', ec='#64748B', lw=1.4):
    box = patches.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=3)
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
    fig, ax = plt.subplots(figsize=(10.8, 9.8), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(-12, 102)
    ax.axis('off')

    ax.text(55, 99.5, 'Mechatronic Hardware Architecture & Signal Distribution Flow',
            fontsize=13.0, fontweight='bold', ha='center', va='top', color='#0F172A')

    # Top Sensors: USB Camera Gimbal & MS200 LiDAR
    embed_photo_clean(ax, 'write_up/figures/camera_gimbal.png', 8, 80, 20, 15, border_c='#0284C7')
    ax.text(18, 78.5, '2MP Monocular Camera\nActive RGB Video Input',
            fontsize=7.8, fontweight='bold', ha='center', va='top', color='#0369A1')

    embed_photo_clean(ax, 'write_up/figures/ms200_lidar.jpg', 82, 80, 20, 15, border_c='#0284C7')
    ax.text(92, 78.5, 'MS200 2D ToF LiDAR\n360° Planar Laser Scanner',
            fontsize=7.8, fontweight='bold', ha='center', va='top', color='#0369A1')

    # Middle top card: 2-DOF Active Vision Gimbal & Servos
    gimbal_box = patches.FancyBboxPatch((29.5, 79), 51.5, 16.5, boxstyle='round,pad=0.3', fc='#F0FDF4', ec='#16A34A', lw=1.3)
    ax.add_patch(gimbal_box)
    ax.text(55, 93.0, '2-DOF Active Vision Gimbal Mount', fontsize=9.0, fontweight='bold', ha='center', va='center', color='#15803D')
    gimbal_text = (
        "• Dual SG90 Micro Servos (Pan & Tilt Motion)\n"
        "• Closed-Loop Visual Servoing Target Tracking\n"
        "• Hardware PWM Driven directly from Expansion Board"
    )
    ax.text(32.0, 89.5, gimbal_text, fontsize=7.4, va='top', color='#14532D', linespacing=1.4)

    # Sensor data bus arrows into Pi 5
    ax.annotate('', xy=(18, 66.5), xytext=(18, 73.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(18, 70.0, 'USB 3.0 (/camera/image_raw)', fontsize=7.0, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#38BDF8', lw=0.8))

    ax.annotate('', xy=(92, 66.5), xytext=(92, 73.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(92, 70.0, 'USB Serial (/scan)', fontsize=7.0, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#38BDF8', lw=0.8))

    # Tier 1: Primary Embedded SBC (Raspberry Pi 5) - Full width
    tier_w = 96.5
    tier_x = 7.5
    pi_box = patches.FancyBboxPatch((tier_x, 46), tier_w, 20, boxstyle='round,pad=0.4', fc='#F0F9FF', ec='#0284C7', lw=1.6)
    ax.add_patch(pi_box)
    embed_photo_clean(ax, 'write_up/figures/raspberry_pi_5.jpg', 9.5, 47.5, 20, 17, border_c='#0284C7')

    ax.text(32, 63.2, 'Host Single-Board Computer: Raspberry Pi 5 (8GB RAM)', fontsize=9.8, fontweight='bold', color='#0369A1')
    pi_desc = (
        "• Deep Learning Vision Pipeline (YOLOv8 Person Gating + MediaPipe Landmarks)\n"
        "• Cognitive Decision Engine & Multi-Class MLP Gesture Recognition\n"
        "• Autonomous Navigation, Costmap Planning & ROS 2 Humble Runtime\n"
        "• High-Speed USB 3.0 & Serial Communication Hub"
    )
    ax.text(32, 59.8, pi_desc, fontsize=7.6, va='top', color='#1E293B', linespacing=1.45)

    # Inter-board micro-ROS Bridge
    ax.annotate('', xy=(55, 38.5), xytext=(55, 45.5), arrowprops=dict(arrowstyle='<->', lw=2.0, color='#D97706'))
    ax.text(55, 42.0, 'High-Speed micro-ROS Serial Bridge (921,600 baud)\nControl Commands (/cmd_vel, servos)  ⇄  Sensor Telemetry (/odom, /imu)',
            fontsize=7.4, fontweight='bold', ha='center', va='center', color='#92400E',
            bbox=dict(boxstyle='round,pad=0.22', fc='#FEF3C7', ec='#F59E0B', lw=0.9))

    # Tier 2: Yahboom ESP32-S3 micro-ROS Board + Cropped Wiring Photo - Width: 96.5
    esp_box = patches.FancyBboxPatch((tier_x, 17), tier_w, 20.5, boxstyle='round,pad=0.4', fc='#FEFCE8', ec='#EAB308', lw=1.6)
    ax.add_patch(esp_box)
    embed_photo_clean(ax, 'write_up/figures/microros_control_board.jpg', 9.5, 18.5, 18, 17.5, border_c='#EAB308')
    embed_photo_clean(ax, 'write_up/figures/chassis_wired_cropped.jpg', 86.0, 18.5, 16.5, 17.5, border_c='#EAB308')
    ax.text(29.5, 34.5, 'Real-Time Sub-Controller: Yahboom ESP32-S3 Board', fontsize=9.8, fontweight='bold', color='#A16207')
    esp_desc = (
        "• FreeRTOS micro-ROS Client with Deterministic 50 Hz Closed-Loop Velocity PID\n"
        "• 4-Channel DC Motor PWM Bridges & Quadrature Encoder Decoding\n"
        "• 2-Channel 50 Hz Hardware PWM Gimbal Servicing & Onboard 6-Axis IMU\n"
        "• Dedicated Real-Time Reflex Layer Decoupled from High-Level Vision"
    )
    ax.text(29.5, 31.0, esp_desc, fontsize=7.5, va='top', color='#422006', linespacing=1.45)

    # Actuation bus arrow into Mobile Base
    ax.annotate('', xy=(55, 7.5), xytext=(55, 16.5), arrowprops=dict(arrowstyle='->', lw=1.8, color='#16A34A'))
    ax.text(55, 12.0, '4-Channel Motor Drive Voltages  |  Quadrature Encoder Telemetry', fontsize=7.4,
            ha='center', va='center', fontweight='bold', color='#15803D',
            bbox=dict(boxstyle='round,pad=0.2', fc='#DCFCE7', ec='#86EFAC', lw=0.8))

    # Tier 3: Differential-Drive Mobile Base & Underside Drivetrain - Width: 96.5
    bot_box = patches.FancyBboxPatch((tier_x, -10), tier_w, 17, boxstyle='round,pad=0.4', fc='#F0FDF4', ec='#16A34A', lw=1.6)
    ax.add_patch(bot_box)
    embed_photo_clean(ax, 'write_up/figures/assembled_robot_real.jpg', 9.5, -8.8, 19, 14.5, border_c='#16A34A')
    embed_photo_clean(ax, 'write_up/figures/robot_drivetrain_underside.jpg', 86.0, -8.8, 16.5, 14.5, border_c='#16A34A')
    ax.text(30.5, 4.2, 'Mobile Base & Physical Actuation Chassis', fontsize=9.6, fontweight='bold', color='#15803D')
    bot_desc = (
        "• 4WD Differential Skid-Steer Locomotion (4× 310 DC Geared Motors)\n"
        "• 65 mm High-Traction Rubber Wheels & High-Resolution Optical Encoders\n"
        "• Dual-Tier Acrylic Chassis Deck with Low-Center-of-Gravity Battery Bay"
    )
    ax.text(30.5, 0.8, bot_desc, fontsize=7.6, va='top', color='#14532D', linespacing=1.45)

    # Power Rail on left side with 7.4V 2S Battery specs
    pwr_box = patches.FancyBboxPatch((0.5, -8), 4.2, 74, boxstyle='round,pad=0.18', fc='#FEF2F2', ec='#DC2626', lw=1.3)
    ax.add_patch(pwr_box)
    ax.text(2.6, 29.0, 'POWER DISTRIBUTION  •  7.4V 2S Li-ion Battery (8.4V Peak)',
            fontsize=7.4, fontweight='bold', ha='center', va='center', color='#991B1B', rotation=90)

    # Labeled Power connections into Pi 5 (5V/5A Buck), ESP32 (7.4V Direct), and Motors (7.4V VMOT)
    ax.plot([4.7, 7.5], [56.0, 56.0], color='#EA580C', lw=1.5, linestyle='--')
    ax.text(6.1, 57.5, '5V / 5A', fontsize=5.8, ha='center', va='bottom', color='#EA580C', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='#EA580C', lw=0.6))

    ax.plot([4.7, 7.5], [27.0, 27.0], color='#DC2626', lw=1.5, linestyle='--')
    ax.text(6.1, 28.5, '7.4V', fontsize=5.8, ha='center', va='bottom', color='#DC2626', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='#DC2626', lw=0.6))

    ax.plot([4.7, 7.5], [-1.5, -1.5], color='#DC2626', lw=1.5, linestyle='--')
    ax.text(6.1, 0.0, '7.4V VMOT', fontsize=5.4, ha='center', va='bottom', color='#DC2626', fontweight='bold',
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

    # Panel (a): Robot Onboard Camera POV with Clean Bystander Privacy Blur
    ax1 = fig.add_subplot(gs[0, 0])
    img_bot = Image.open('write_up/figures/robot_spatial_zone_clean.jpg')
    ax1.imshow(img_bot)
    ax1.axis('off')
    ax1.set_title('(a) Empirical Robot Camera Perception (/dev/video0)\n[Bystander Privacy Blur & Central Acceptance Zone HUD]',
                  fontsize=9.0, fontweight='bold', color='#0F172A', pad=8)

    # Panel (b): ISO 5807 Standard Gating Decision Flowchart
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis('off')
    ax2.set_title('(b) ISO 5807 Spatial Acceptance Gating Logic\n[Centroid Evaluation & Intention-to-Action Dispatch]',
                  fontsize=9.0, fontweight='bold', color='#0F172A', pad=8)

    # 1. Input Data Block (Parallelogram - ISO 5807 Data)
    draw_parallelogram(ax2, 12, 84, 76, 10, slant=0.06, fc='#EFF6FF', ec='#3B82F6', lw=1.4)
    ax2.text(50, 89, 'INPUT: Video Stream (/camera/image_raw)',
             fontsize=7.8, fontweight='bold', ha='center', va='center', color='#1E40AF')

    ax2.annotate('', xy=(50, 75.5), xytext=(50, 84), arrowprops=dict(arrowstyle='->', lw=1.6, color='#334155'))

    # 2. Process Block (Rectangle - ISO 5807 Process)
    draw_process(ax2, 12, 63, 76, 12.5, fc='#F8FAFC', ec='#475569', lw=1.4)
    ax2.text(50, 69.2, 'Human Operator Localization (YOLOv8n)\nExtract Bounding Box → Centroid (cx, cy)',
             fontsize=7.3, ha='center', va='center', color='#0F172A', linespacing=1.25)

    ax2.annotate('', xy=(50, 50.5), xytext=(50, 63), arrowprops=dict(arrowstyle='->', lw=1.6, color='#334155'))

    # 3. Decision Block (Diamond - ISO 5807 Decision)
    draw_diamond(ax2, 50, 41, 66, 19, fc='#FEF3C7', ec='#D97706', lw=1.5)
    ax2.text(50, 41, 'Centroid in Acceptance Zone?\n(cx, cy) ∈ Ω_ROI',
             fontsize=7.3, fontweight='bold', ha='center', va='center', color='#92400E', linespacing=1.25)

    # Branch [NO]: Left side -> Terminator (Stadium - ISO 5807 Terminator)
    ax2.plot([17, 26], [41, 41], color='#DC2626', lw=1.6)
    ax2.plot([26, 26], [41, 24.5], color='#DC2626', lw=1.6)
    ax2.annotate('', xy=(26, 23), xytext=(26, 25), arrowprops=dict(arrowstyle='->', lw=1.6, color='#DC2626'))
    ax2.text(21, 43.5, '[NO]', fontsize=7.4, fontweight='bold', ha='center', va='bottom', color='#DC2626')

    draw_stadium(ax2, 6, 8, 40, 15, fc='#FEE2E2', ec='#DC2626', lw=1.4)
    ax2.text(26, 15.5, 'Bystander Suppression\nDiscard Frame | Zero Velocity (v = 0)',
             fontsize=6.8, fontweight='bold', ha='center', va='center', color='#991B1B', linespacing=1.25)

    # Branch [YES]: Right side -> Process (Rectangle - ISO 5807 Process)
    ax2.plot([83, 74], [41, 41], color='#16A34A', lw=1.6)
    ax2.plot([74, 74], [41, 24.5], color='#16A34A', lw=1.6)
    ax2.annotate('', xy=(74, 23), xytext=(74, 25), arrowprops=dict(arrowstyle='->', lw=1.6, color='#16A34A'))
    ax2.text(79, 43.5, '[YES]', fontsize=7.4, fontweight='bold', ha='center', va='bottom', color='#16A34A')

    draw_process(ax2, 54, 8, 40, 15, fc='#DCFCE7', ec='#16A34A', lw=1.4)
    ax2.text(74, 15.5, 'Primary Operator Accepted\nTarget Lock & Visual Servoing\nForward to Gesture Pipeline',
             fontsize=6.7, fontweight='bold', ha='center', va='center', color='#14532D', linespacing=1.22)

    fig.suptitle('Empirical Spatial Receptive Zone Gating & Bystander Suppression Flow',
                 fontsize=12.5, fontweight='bold', color='#0F172A', y=0.98)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 3. FEATURE PIPELINE (Real Hand Landmarks + Visible Inter-Stage Chevrons)
# ==============================================================================
def generate_reengineered_feature_pipeline(output_path='write_up/preview_figures/preview_fig_feature_pipeline.png'):
    fig = plt.figure(figsize=(14.5, 5.5), dpi=300)
    gs = fig.add_gridspec(1, 4, width_ratios=[1.15, 1.25, 1.25, 1.35], wspace=0.22,
                          top=0.88, bottom=0.06, left=0.03, right=0.97)

    # ==============================================================================
    # STAGE 1: Real Hand (Clean transparent float, zero inner bounding box)
    # ==============================================================================
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.axis('off')
    ax1.set_title('Stage 1: Real Hand Landmarks\n[MediaPipe 21 Joints]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage1_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#FFFFFF', ec='#CBD5E1', lw=1.2)
    ax1.add_patch(stage1_box)

    # Embed hand directly without ANY inner card or blue border!
    img_hand = Image.open('write_up/figures/real_hand_landmarks_annotated.png')
    ax_ins = ax1.inset_axes([17.0, 9.0, 66.0, 78.0], transform=ax1.transData, zorder=3)
    ax_ins.imshow(img_hand, aspect='equal')
    ax_ins.axis('off')

    ax1.text(50, 91.0, '21-Joint 3D Landmark Topology', fontsize=7.2, fontweight='bold', ha='center', va='center', color='#1E40AF')
    ax1.text(50, 5.5, 'Reference Anchor: Wrist & MCP Span', fontsize=7.0, fontweight='bold', ha='center', va='center',
             color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.18', fc='#EFF6FF', ec='#93C5FD', lw=0.8))

    # ==============================================================================
    # STAGE 2: Invariance Transforms (Conceptual High-Level + Visual Icons)
    # ==============================================================================
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis('off')
    ax2.set_title('Stage 2: Invariance Transforms\n[Scale & Translation Invariant]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage2_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax2.add_patch(stage2_box)

    # 1. Translation Invariance with visual origin shift icon
    c1 = patches.FancyBboxPatch((5, 73), 90, 20, boxstyle='round,pad=0.2', fc='#EFF6FF', ec='#3B82F6', lw=1.2)
    ax2.add_patch(c1)
    ax2.text(10, 87, '1. Translation Normalization', fontsize=7.4, fontweight='bold', color='#1D4ED8')
    ax2.text(10, 78.0, 'Zero-center coordinates to wrist origin\n(Eliminates robot-to-hand position offset)', fontsize=6.7, color='#1E293B', linespacing=1.2)
    ax2.annotate('', xy=(88, 86), xytext=(78, 86), arrowprops=dict(arrowstyle='->', lw=1.2, color='#3B82F6'))
    ax2.annotate('', xy=(78, 92), xytext=(78, 82), arrowprops=dict(arrowstyle='->', lw=1.2, color='#3B82F6'))
    ax2.text(80, 80, 'Origin', fontsize=5.8, color='#1D4ED8', fontweight='bold')

    # 2. Scale & Distance Normalization with visual span icon
    c2 = patches.FancyBboxPatch((5, 50), 90, 20, boxstyle='round,pad=0.2', fc='#FEFCE8', ec='#EAB308', lw=1.2)
    ax2.add_patch(c2)
    ax2.text(10, 64, '2. Scale Normalization', fontsize=7.4, fontweight='bold', color='#A16207')
    ax2.text(10, 55.0, 'Divide distances by dynamic palm span\n(Eliminates camera distance & hand size variation)', fontsize=6.7, color='#1E293B', linespacing=1.2)
    ax2.annotate('', xy=(88, 62), xytext=(76, 62), arrowprops=dict(arrowstyle='<->', lw=1.4, color='#EAB308'))
    ax2.text(82, 65, 'Palm Span', fontsize=5.8, ha='center', color='#A16207', fontweight='bold')

    # 3. Finger Flexion Curl Angles with visual vector angle
    c3 = patches.FancyBboxPatch((5, 27), 90, 20, boxstyle='round,pad=0.2', fc='#F0FDF4', ec='#16A34A', lw=1.2)
    ax2.add_patch(c3)
    ax2.text(10, 41, '3. Finger Flexion Angles', fontsize=7.4, fontweight='bold', color='#15803D')
    ax2.text(10, 32.0, 'Calculate joint curl across all five digits\n(Robust invariant curvature descriptor)', fontsize=6.7, color='#1E293B', linespacing=1.2)
    ax2.plot([78, 86], [32, 38], color='#16A34A', lw=1.3)
    ax2.plot([78, 86], [32, 28], color='#16A34A', lw=1.3)
    arc = patches.Arc((78, 32), 6, 6, angle=0, theta1=-25, theta2=35, color='#16A34A', lw=1.2)
    ax2.add_patch(arc)
    ax2.text(82, 32, 'Angle', fontsize=5.8, color='#15803D', fontweight='bold')

    # 4. Relative Geometric Vectors
    c4 = patches.FancyBboxPatch((5, 5), 90, 19, boxstyle='round,pad=0.2', fc='#FAF5FF', ec='#A855F7', lw=1.2)
    ax2.add_patch(c4)
    ax2.text(10, 18, '4. Thumb Relative Vector', fontsize=7.4, fontweight='bold', color='#7E22CE')
    ax2.text(10, 9.5, '3D vector from palm base to thumb tip\n(Distinguishes open hand vs thumbs gestures)', fontsize=6.7, color='#1E293B', linespacing=1.2)
    ax2.annotate('', xy=(88, 14), xytext=(78, 14), arrowprops=dict(arrowstyle='->', lw=1.4, color='#A855F7'))
    ax2.text(83, 17, 'Vector', fontsize=5.8, ha='center', color='#7E22CE', fontweight='bold')

    # ==============================================================================
    # STAGE 3: 19-D Feature Vector (Visual Feature Ribbon + High-Level Breakdown)
    # ==============================================================================
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 100)
    ax3.axis('off')
    ax3.set_title('Stage 3: 19-D Feature Vector\n[Normalized Invariant Descriptor]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage3_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax3.add_patch(stage3_box)

    # Visual Feature Ribbon at top of Stage 3 (Continuous 19-slot descriptor)
    ax3.text(50, 91.5, '19-D Invariant Feature Vector (Slots 1–19)',
             fontsize=7.0, fontweight='bold', ha='center', va='center', color='#0F172A')

    ribbon_x = np.linspace(6, 94, 20)
    for i in range(19):
        rx = ribbon_x[i]
        rw = ribbon_x[i+1] - rx - 0.4
        if i < 5:
            col = '#3B82F6'  # 5 angles
        elif i < 10:
            col = '#EAB308'  # 5 distances
        else:
            col = '#16A34A'  # 9 relative
        ax3.add_patch(patches.Rectangle((rx, 83), rw, 5.0, fc=col, ec='#1E293B', lw=0.5))
        if i in [0, 4, 5, 9, 10, 18]:
            ax3.text(rx + rw/2, 85.5, str(i+1), fontsize=4.8, ha='center', va='center', color='white', fontweight='bold')

    # Group 1: 5-D Finger Curl Angles
    f1 = patches.FancyBboxPatch((5, 56), 90, 24, boxstyle='round,pad=0.2', fc='#EFF6FF', ec='#3B82F6', lw=1.2)
    ax3.add_patch(f1)
    ax3.text(8, 74.0, 'Finger Flexion Angles (5-D)', fontsize=7.4, fontweight='bold', color='#1D4ED8')
    ax3.text(8, 64.0, '• Joint curl for thumb, index, middle, ring & pinky\n• Full flexion (0 rad) to full extension (π rad)', fontsize=6.8, color='#1E293B', linespacing=1.25)

    # Group 2: 5-D Tip-to-Wrist Distances
    f2 = patches.FancyBboxPatch((5, 30), 90, 23, boxstyle='round,pad=0.2', fc='#FEFCE8', ec='#EAB308', lw=1.2)
    ax3.add_patch(f2)
    ax3.text(8, 47.0, 'Normalized Tip Distances (5-D)', fontsize=7.4, fontweight='bold', color='#A16207')
    ax3.text(8, 37.0, '• Radial reach from wrist origin to each fingertip\n• Normalized by palm width for distance invariance', fontsize=6.8, color='#1E293B', linespacing=1.25)

    # Group 3: 9-D Relative Geometric Descriptors
    f3 = patches.FancyBboxPatch((5, 5), 90, 22, boxstyle='round,pad=0.2', fc='#F0FDF4', ec='#16A34A', lw=1.2)
    ax3.add_patch(f3)
    ax3.text(8, 21.0, 'Relative Spatial Descriptors (9-D)', fontsize=7.4, fontweight='bold', color='#15803D')
    ax3.text(8, 12.0, '• Thumb 3D directional vector (3-D)\n• Inter-fingertip spread distances (4-D)\n• Palm aspect ratio & hand geometry (2-D)', fontsize=6.5, color='#1E293B', linespacing=1.2)

    # ==============================================================================
    # STAGE 4: MLP Neural Network (19 -> 128 -> 64 -> 6 Verified Nodes!)
    # ==============================================================================
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.set_xlim(0, 100)
    ax4.set_ylim(0, 100)
    ax4.axis('off')
    ax4.set_title('Stage 4: MLP Classifier & Actions\n[1.2 ms Latency | 99.38% Accuracy]', fontsize=8.6, fontweight='bold', color='#0F172A', pad=6)

    stage4_box = patches.FancyBboxPatch((2, 2), 96, 96, boxstyle='round,pad=0.3', fc='#F8FAFC', ec='#CBD5E1', lw=1.2)
    ax4.add_patch(stage4_box)

    # Neural Network Diagram with verified architecture: 19 -> 128 -> 64 -> 6
    layers = [3, 6, 5, 3]
    layer_x = [15, 38, 62, 85]
    layer_names = ['Input\n19-D', 'Hidden 1\n128 (ReLU)', 'Hidden 2\n64 (ReLU)', 'Output\n6 (Softmax)']
    for l_idx, (num_nodes, lx) in enumerate(zip(layers, layer_x)):
        ys = np.linspace(58, 86, num_nodes)
        for y in ys:
            circle = plt.Circle((lx, y), 2.2, fc='#3B82F6', ec='#1D4ED8', lw=1.0, zorder=4)
            ax4.add_patch(circle)
        ax4.text(lx, 51.5, layer_names[l_idx], fontsize=6.3, ha='center', va='top', color='#334155', fontweight='bold')

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
    fig = plt.figure(figsize=(17.5, 7.6), dpi=300)
    ax = fig.add_axes([0.012, 0.02, 0.976, 0.92])
    ax.set_xlim(0, 175)
    ax.set_ylim(0, 76)
    ax.axis('off')

    fig.suptitle('Supervisory Cognition Architecture: Multi-Modal Gating, OMG UML 2.5 State Machine & twist_mux Arbitration',
                 fontsize=12.5, fontweight='bold', color='#0F172A', y=0.978)

    # ==============================================================================
    # 1. LEFT FLANK: MULTI-MODAL INGESTION & GATING (x=3 to 42, width 39)
    # ==============================================================================
    flank_left = patches.FancyBboxPatch((3, 3), 39, 68.5, boxstyle='round,pad=0.35', fc='#F8FAFC', ec='#94A3B8', lw=1.3)
    ax.add_patch(flank_left)
    ax.text(22.5, 69.0, 'Multi-Modal Ingestion & Safety Gating', fontsize=8.6, fontweight='bold', ha='center', va='center', color='#0F172A')

    # ROS 2 Input Topics (4 topics)
    topics = [
        ('/cognition/detection', 'YOLOv8n Person Centroid & Box (20 Hz)', '#2563EB', '#EFF6FF', 58.0),
        ('/cognition/gesture', '19-D MLP Gesture Classifier (10 Hz)', '#7C3AED', '#F5F3FF', 50.0),
        ('/cognition/face_identity', 'Biometric Authorization (5 Hz)', '#D97706', '#FFFBEB', 42.0),
        ('/system/mode', 'Operational Mode [GESTURE/AUTO]', '#475569', '#F1F5F9', 34.0),
    ]
    for topic_name, desc, ec, fc, ty in topics:
        t_box = patches.FancyBboxPatch((5.0, ty), 35.0, 6.8, boxstyle='round,pad=0.2', fc=fc, ec=ec, lw=1.1)
        ax.add_patch(t_box)
        ax.text(6.5, ty + 4.8, topic_name, fontsize=6.8, fontweight='bold', color=ec)
        ax.text(6.5, ty + 1.8, desc, fontsize=5.8, color='#334155')

    # Connecting arrow from topics down to Gating
    ax.annotate('', xy=(22.5, 29.5), xytext=(22.5, 33.5),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='#475569'))

    # Software Safety Gating Blocks
    # Gate 1: Spatial Zone Filter
    g1 = patches.FancyBboxPatch((5.0, 17.5), 35.0, 10.5, boxstyle='round,pad=0.2', fc='#ECFDF5', ec='#10B981', lw=1.2)
    ax.add_patch(g1)
    ax.text(6.5, 25.5, 'Gate 1: Spatial Acceptance Zone ROI', fontsize=6.9, fontweight='bold', color='#047857')
    ax.text(6.5, 20.2, '• Filters out background bystanders\n• Central Acceptance Window: [45% × 65%]', fontsize=5.8, color='#065F46', linespacing=1.2)

    # Gate 2: Biometric Gate
    g2 = patches.FancyBboxPatch((5.0, 5.0), 35.0, 10.5, boxstyle='round,pad=0.2', fc='#FEF2F2', ec='#EF4444', lw=1.2)
    ax.add_patch(g2)
    ax.text(6.5, 13.0, 'Gate 2: Biometric Identity Gate', fontsize=6.9, fontweight='bold', color='#B91C1C')
    ax.text(6.5, 8.0, '• require_face_auth parameter check\n• Discards unauthorized bystander gestures', fontsize=5.8, color='#991B1B', linespacing=1.2)

    # Inter-flank connection arrow to FSM: exits from Gate 1/2 up into the FSM transition
    ax.plot([40.0, 44.5, 44.5], [22.75, 22.75, 50.0], color='#0284C7', lw=1.6)
    ax.annotate('', xy=(47.5, 50.0), xytext=(44.5, 50.0),
                arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(44.0, 36.0, 'Validated\nCommand\nEvents', fontsize=6.2, ha='center', va='center',
            fontweight='bold', color='#0284C7', bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#38BDF8', lw=0.8))

    # ==============================================================================
    # 2. CENTER: OMG UML 2.5 BRAIN STATE MACHINE CORE (x=46.5 to 127.5, width 81)
    # ==============================================================================
    fsm_bg = patches.FancyBboxPatch((46.5, 3), 81.0, 68.5, boxstyle='round,pad=0.35', fc='#FFFFFF', ec='#64748B', lw=1.4)
    ax.add_patch(fsm_bg)
    ax.text(87.0, 69.0, 'Supervisory Cognition: OMG UML 2.5 Brain State Machine',
            fontsize=8.8, fontweight='bold', ha='center', va='center', color='#0F172A')

    # Initial Pseudo-State
    init_circle = plt.Circle((49.5, 50.0), 1.8, fc='#0F172A', ec='#0F172A', zorder=5)
    ax.add_patch(init_circle)
    ax.annotate('', xy=(52.5, 50.0), xytext=(51.3, 50.0), arrowprops=dict(arrowstyle='->', lw=1.5, color='#0F172A'))

    st_h = 16.5

    # State 1: IDLE / STANDBY (x=52.5 to 73.5, width 21.0, y=41.5 to 58.0)
    draw_uml_state(ax, 52.5, 41.5, 21.0, st_h, '1. IDLE / STANDBY',
                   "entry / stop_motors()\n"
                   "do / monitor_heartbeat()\n"
                   "exit / log_activation()",
                   border_c='#64748B', bg_c='#F8FAFC', badge_c='#334155')

    # State 2: WAITING_CONFIRM (x=80.5 to 102.5, width 22.0, y=41.5 to 58.0)
    draw_uml_state(ax, 80.5, 41.5, 22.0, st_h, '2. WAITING_CONFIRM',
                   "entry / start_consensus_timer()\n"
                   "do / rolling_majority_filter()\n"
                   "exit / commit_consensus()",
                   border_c='#D97706', bg_c='#FEFCE8', badge_c='#B45309')

    # State 3: EXECUTING_MOTION (x=109.5 to 125.5, width 16.0, y=41.5 to 58.0)
    draw_uml_state(ax, 109.5, 41.5, 16.0, st_h, '3. EXECUTING',
                   "entry / dispatch_cmd()\n"
                   "do / monitor_odom()\n"
                   "exit / zero_velocity()",
                   border_c='#16A34A', bg_c='#DCFCE7', badge_c='#15803D')

    # State 4: FOLLOW MODE (Visual Servoing) (x=80.5 to 125.5, width 45.0, y=9.5 to 26.0)
    draw_uml_state(ax, 80.5, 9.5, 45.0, st_h, '4. FOLLOW MODE (Visual Servoing)',
                   "entry / init_servoing_loop()\n"
                   "do / track_operator_centroid(Cx)\n"
                   "do / publish_proportional_twist()\n"
                   "exit / zero_velocity()",
                   border_c='#2563EB', bg_c='#DBEAFE', badge_c='#1D4ED8')

    # State 5: EMERGENCY HALT [OVERRIDE] (x=52.5 to 73.5, width 21.0, y=9.5 to 26.0)
    draw_uml_state(ax, 52.5, 9.5, 21.0, st_h, '5. EMERGENCY HALT',
                   "entry / FORCE_STOP()\n"
                   "entry / clear_buffers()\n"
                   "do / engage_lockout()\n"
                   "exit / manual_reset()",
                   border_c='#DC2626', bg_c='#FEE2E2', badge_c='#991B1B')

    # Transitions inside FSM:
    # 1 -> 2
    ax.annotate('', xy=(80.5, 50.0), xytext=(73.5, 50.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#334155'))
    ax.text(77.0, 52.5, 'Operator\nin Zone', fontsize=5.8, ha='center', va='bottom',
            fontweight='bold', color='#1E293B', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='#CBD5E1', lw=0.7))

    # 2 -> 3
    ax.annotate('', xy=(109.5, 50.0), xytext=(102.5, 50.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#16A34A'))
    ax.text(106.0, 52.5, 'Consensus\n[Votes >= 3/5]', fontsize=5.6, ha='center', va='bottom',
            fontweight='bold', color='#15803D', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='#86EFAC', lw=0.7))

    # 3 -> 1 (Timeout return arc)
    ax.plot([117.5, 117.5, 63.0, 63.0], [58.0, 64.0, 64.0, 58.0], color='#64748B', lw=1.5)
    ax.annotate('', xy=(63.0, 58.0), xytext=(63.0, 59.0), arrowprops=dict(arrowstyle='->', lw=1.5, color='#64748B'))
    ax.text(90.25, 64.0, 'Timeout [t > 3.0s] / Motion Complete', fontsize=6.2, ha='center', va='center',
            fontweight='bold', color='#334155', bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#64748B', lw=0.8))

    # 3 -> 4
    ax.annotate('', xy=(114.0, 26.0), xytext=(114.0, 41.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#2563EB'))
    ax.text(112.5, 33.75, 'Gesture ==\nFOLLOW', fontsize=5.8, ha='right', va='center',
            fontweight='bold', color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='#93C5FD', lw=0.7))

    # 4 -> 1 Return via top arc (Zero crossings)
    ax.plot([125.5, 126.8, 126.8, 117.5], [17.75, 17.75, 64.0, 64.0], color='#2563EB', lw=1.3, linestyle=':')
    ax.text(126.8, 38.0, 'Lost/STOP', fontsize=5.4, ha='center', va='center',
            fontweight='bold', color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='#93C5FD', lw=0.6))

    # Global Asynchronous Preemption Line (interrupting active states into State 5)
    ax.plot([91.5, 76.5, 76.5, 73.5], [41.5, 41.5, 17.75, 17.75], color='#DC2626', lw=1.8, linestyle='--')
    ax.annotate('', xy=(73.5, 17.75), xytext=(75.0, 17.75), arrowprops=dict(arrowstyle='->', lw=1.8, color='#DC2626'))
    ax.text(76.5, 30.0, '⚡ E-STOP\nPREEMPTION', fontsize=5.5, ha='center', va='center',
            fontweight='bold', color='#991B1B', bbox=dict(boxstyle='round,pad=0.15', fc='#FEF2F2', ec='#DC2626', lw=0.8))

    # 5 -> 1 Reset
    ax.annotate('', xy=(57.5, 41.5), xytext=(57.5, 26.0), arrowprops=dict(arrowstyle='->', lw=1.5, color='#64748B'))
    ax.text(56.5, 33.75, 'Clear &\nReset', fontsize=5.8, ha='right', va='center', fontweight='bold', color='#475569')

    # ==============================================================================
    # 3. RIGHT FLANK: VELOCITY ARBITRATION & SAFETY INTERLOCK (x=130.5 to 172, width 41.5)
    # ==============================================================================
    flank_right = patches.FancyBboxPatch((130.5, 3), 41.5, 68.5, boxstyle='round,pad=0.35', fc='#F8FAFC', ec='#94A3B8', lw=1.3)
    ax.add_patch(flank_right)
    ax.text(151.25, 69.0, 'twist_mux Priority & Safety Arbitration', fontsize=8.6, fontweight='bold', ha='center', va='center', color='#0F172A')

    # Output from FSM to Priority 40 in twist_mux (Clean orthogonal route!)
    ax.plot([125.5, 128.5, 128.5, 134.5], [45.0, 45.0, 29.5, 29.5], color='#16A34A', lw=1.8)
    ax.annotate('', xy=(134.5, 29.5), xytext=(132.5, 29.5),
                arrowprops=dict(arrowstyle='->', lw=1.8, color='#16A34A'))
    ax.text(128.5, 37.5, '/cmd_vel_gesture\n(Priority 40)', fontsize=5.6, ha='center', va='center',
            fontweight='bold', color='#15803D', bbox=dict(boxstyle='round,pad=0.15', fc='#DCFCE7', ec='#16A34A', lw=0.7))

    # twist_mux Priority Matrix
    mux_box = patches.FancyBboxPatch((133.0, 23.5), 36.5, 40.0, boxstyle='round,pad=0.25', fc='#FFFFFF', ec='#CBD5E1', lw=1.2)
    ax.add_patch(mux_box)
    ax.text(151.25, 60.5, 'ROS 2 twist_mux Priority Arbitrator', fontsize=7.2, fontweight='bold', ha='center', va='center', color='#0F172A')

    mux_slots = [
        ('PRIORITY 100 [CRITICAL]: /cmd_vel_emergency', 'LiDAR Safety Zone (< 0.36m Collision Halt)', '#DC2626', '#FEE2E2', 51.5),
        ('PRIORITY 90 [OVERRIDE]: /joy_teleop', 'Manual Wireless Joystick / Teleoperation', '#D97706', '#FEF3C7', 43.0),
        ('PRIORITY 50 [AUTONOMY]: /cmd_vel_nav', 'Nav2 Path Planner (Costmap Navigation)', '#2563EB', '#DBEAFE', 34.5),
        ('PRIORITY 40 [COGNITION]: /cmd_vel_gesture', 'Cognitive Brain Node State Machine', '#16A34A', '#DCFCE7', 26.0),
    ]
    for pri_name, pri_desc, ec, fc, my in mux_slots:
        p_box = patches.FancyBboxPatch((134.5, my), 33.5, 7.0, boxstyle='round,pad=0.18', fc=fc, ec=ec, lw=1.0)
        ax.add_patch(p_box)
        ax.text(136.0, my + 4.9, pri_name, fontsize=5.8, fontweight='bold', color=ec)
        ax.text(136.0, my + 1.8, pri_desc, fontsize=5.3, color='#334155')

    # Output to Hardware
    ax.annotate('', xy=(151.25, 17.5), xytext=(151.25, 23.5),
                arrowprops=dict(arrowstyle='->', lw=2.0, color='#0F172A'))
    ax.text(152.0, 20.5, 'Arbitrated /cmd_vel', fontsize=6.2, ha='left', va='center', fontweight='bold', color='#0F172A')

    # ESP32-S3 Base Controller
    hw_box = patches.FancyBboxPatch((134.5, 5.0), 33.5, 11.5, boxstyle='round,pad=0.2', fc='#EDE9FE', ec='#7C3AED', lw=1.2)
    ax.add_patch(hw_box)
    ax.text(151.25, 13.5, 'ESP32-S3 Base Controller', fontsize=7.2, fontweight='bold', ha='center', va='center', color='#6D28D9')
    ax.text(151.25, 8.5, '• micro-ROS Client | FreeRTOS Motor PID\n• 4WD Mecanum / Differential Locomotion', fontsize=5.8, ha='center', va='center', color='#4C1D95', linespacing=1.2)

    # Clean Preemption Feedback route: drops from Priority 100 down along right flank and into State 5!
    ax.plot([134.5, 130.5, 130.5, 73.5], [55.0, 55.0, 14.5, 14.5], color='#DC2626', lw=1.4, linestyle=':')
    ax.annotate('', xy=(73.5, 14.5), xytext=(75.5, 14.5), arrowprops=dict(arrowstyle='->', lw=1.4, color='#DC2626'))
    ax.text(102.5, 13.0, 'LiDAR Obstacle Trigger / E-Stop Lockout', fontsize=5.6, ha='center', va='center',
            fontweight='bold', color='#B91C1C', bbox=dict(boxstyle='round,pad=0.15', fc='#FEF2F2', ec='#DC2626', lw=0.7))

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
            fontsize=13.0, fontweight='bold', ha='center', va='top', color='#0F172A')

    # All Tiers share the EXACT same width: tier_w = 98.0, x=8.0 to x=106.0
    tier_w = 98.0
    tier_x = 8.0

    # Tier 1: Sensing Layer (Camera, LiDAR, IMU)
    t1_box = patches.FancyBboxPatch((tier_x, 82), tier_w, 18, boxstyle='round,pad=0.35', fc='#F8FAFC', ec='#64748B', lw=1.4)
    ax.add_patch(t1_box)
    embed_photo_clean(ax, 'write_up/figures/camera_gimbal.png', tier_x + 2.0, 83.5, 18, 15, border_c='#0284C7')
    embed_photo_clean(ax, 'write_up/figures/ms200_lidar.jpg', tier_x + tier_w - 20.0, 83.5, 18, 15, border_c='#0284C7')
    ax.text(57.0, 96.8, 'Tier 1: Physical Sensing & Environment Transduction', fontsize=9.4, fontweight='bold', ha='center', color='#0F172A')
    t1_desc = (
        "• 2MP Monocular RGB Vision on Active 2-DOF Pan/Tilt Gimbal\n"
        "• MS200 2D ToF LiDAR (360° Planar Laser Range Scanning)\n"
        "• Onboard 6-Axis IMU (Real-Time Inertial Transduction)"
    )
    ax.text(57.0, 93.2, t1_desc, fontsize=7.5, ha='center', va='top', color='#334155', linespacing=1.45)

    ax.annotate('', xy=(57.0, 75.0), xytext=(57.0, 82.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(57.0, 78.5, 'Raw Sensor Telemetry (/camera/image_raw, /scan, /imu/data_raw)', fontsize=7.2, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#38BDF8', lw=0.8))

    # Tier 2: Spatial Gating & Skeletal Tracking (With robot camera POV on left)
    t2_box = patches.FancyBboxPatch((tier_x, 59.5), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#F0F9FF', ec='#0284C7', lw=1.6)
    ax.add_patch(t2_box)
    embed_photo_clean(ax, 'write_up/figures/robot_spatial_zone_blurred.jpg', tier_x + 2.0, 60.5, 18, 13.5, border_c='#0284C7')

    ax.text(tier_x + 23.0, 72.0, 'Tier 2: Edge Perception & Spatial Acceptance Gating', fontsize=9.6, fontweight='bold', color='#0369A1')
    t2_desc = (
        "• YOLOv8n Neural Person Detection & Centroid Spatial Gating\n"
        "• Central 45% × 65% Interaction HUD: Automatically Discards Peripheral Bystanders\n"
        "• MediaPipe HandLandmarker: Localizes 21 3D Anatomical Landmarks in Real Time"
    )
    ax.text(tier_x + 23.0, 68.8, t2_desc, fontsize=7.6, va='top', color='#1E293B', linespacing=1.45)

    ax.annotate('', xy=(57.0, 52.5), xytext=(57.0, 59.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#0284C7'))
    ax.text(57.0, 56.0, '21 Hand Landmarks & Isolated Operator Centroid', fontsize=7.2, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#64748B', lw=0.8))

    # Tier 3: Feature Extraction & Neural Classifier (Real Hand Landmarks on left)
    t3_box = patches.FancyBboxPatch((tier_x, 37.0), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#FEFCE8', ec='#EAB308', lw=1.6)
    ax.add_patch(t3_box)
    embed_photo_clean(ax, 'write_up/figures/real_hand_landmarks_annotated.png', tier_x + 2.0, 38.0, 18, 13.5, border_c='#EAB308')

    ax.text(tier_x + 23.0, 49.5, 'Tier 3: Geometric Feature Extraction & Neural Classifier', fontsize=9.6, fontweight='bold', color='#A16207')
    t3_desc = (
        "• 19-D Translation-, Scale- & Distance-Invariant Geometric Feature Extraction\n"
        "• Multilayer Perceptron (MLP) Deep Neural Gesture Recognition Network\n"
        "• Real-Time Edge Inference Engine via Native Embedded ONNX Runtime Execution"
    )
    ax.text(tier_x + 23.0, 46.2, t3_desc, fontsize=7.6, va='top', color='#422006', linespacing=1.45)

    ax.annotate('', xy=(57.0, 30.0), xytext=(57.0, 37.0), arrowprops=dict(arrowstyle='->', lw=1.6, color='#EAB308'))
    ax.text(57.0, 33.5, 'Discrete Gesture Tokens (/cognition/gesture)', fontsize=7.2, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#EAB308', lw=0.8))

    # Tier 4: Cognition & Supervisory Control (Clean Full-Width Left-Aligned Box)
    t4_box = patches.FancyBboxPatch((tier_x, 14.5), tier_w, 15.5, boxstyle='round,pad=0.35', fc='#FAF5FF', ec='#A855F7', lw=1.6)
    ax.add_patch(t4_box)

    ax.text(tier_x + 6.0, 27.2, 'Tier 4: Supervisory Cognition & Trajectory Planning', fontsize=9.6, fontweight='bold', color='#7E22CE')
    t4_desc = (
        "• Supervisory Finite State Machine (brain_node) with Temporal Consensus Filter\n"
        "• LSTM Recurrent Neural Network for 5-Step Operator Path Forecasting (1.5 s Lookahead)\n"
        "• Nav2 Autonomous Path Planner, Dynamic Obstacle Costmaps & Trajectory Dispatch"
    )
    ax.text(tier_x + 6.0, 23.8, t4_desc, fontsize=7.6, va='top', color='#3B0764', linespacing=1.45)

    ax.annotate('', xy=(57.0, 7.5), xytext=(57.0, 14.5), arrowprops=dict(arrowstyle='->', lw=1.6, color='#A855F7'))
    ax.text(57.0, 11.0, 'Velocity Setpoints (/cmd_vel)  |  micro-ROS Bridge (921,600 baud)', fontsize=7.2, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#A855F7', lw=0.8))

    # Tier 5: Physical Execution & Mechatronics
    t5_box = patches.FancyBboxPatch((tier_x, -10.0), tier_w, 17.5, boxstyle='round,pad=0.35', fc='#F0FDF4', ec='#16A34A', lw=1.6)
    ax.add_patch(t5_box)
    embed_photo_clean(ax, 'write_up/figures/microros_control_board.jpg', tier_x + 2.0, -8.5, 18, 14.5, border_c='#16A34A')
    embed_photo_clean(ax, 'write_up/figures/assembled_robot_real.jpg', tier_x + tier_w - 20.0, -8.5, 18, 14.5, border_c='#16A34A')
    ax.text(tier_x + 22.0, 4.8, 'Tier 5: Real-Time Actuation & Mobile Base', fontsize=9.4, fontweight='bold', color='#15803D')
    t5_desc = (
        "• FreeRTOS micro-ROS Client Running 50 Hz Closed-Loop Velocity PID\n"
        "• 4-Channel DC Motor PWM Bridges & Quadrature Optical Encoder Decoding\n"
        "• 4WD Differential-Drive Base Executing Smooth Trajectories"
    )
    ax.text(tier_x + 22.0, 1.5, t5_desc, fontsize=7.5, va='top', color='#14532D', linespacing=1.45)

    # Direct LiDAR Safety Bypass Interlock Line (Red dashed line down to Tier 4)
    ax.plot([102, 110, 110, tier_x + tier_w], [83.5, 83.5, 22.0, 22.0], color='#DC2626', lw=1.8, linestyle='--')
    ax.annotate('', xy=(tier_x + tier_w, 22.0), xytext=(tier_x + tier_w + 3.0, 22.0), arrowprops=dict(arrowstyle='->', lw=1.8, color='#DC2626'))
    ax.text(111.5, 52.0, 'DIRECT HARDWARE SAFETY BYPASS (LiDAR Obstacle < 0.36 m → Immediate Halt)',
            fontsize=6.8, fontweight='bold', color='#DC2626', rotation=-90, va='center', ha='left')

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f'✓ Generated: {output_path}')


# ==============================================================================
# 6. DOCKER DEPLOYMENT ARCHITECTURE (Publication Grade, Zero Text Collisions)
# ==============================================================================
def generate_reengineered_docker_deployment(output_path='write_up/preview_figures/preview_fig_docker_deployment.png'):
    fig, ax = plt.subplots(figsize=(14.2, 8.2), dpi=300)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 94)
    ax.axis('off')

    # Main Title
    ax.text(70, 91.8, 'Containerized Multi-Node Deployment Architecture (Docker Host Mode & DDS Loopback)',
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # --------------------------------------------------------------------------
    # LEFT CONTAINER: Raspberry Pi 5 Host OS (x=4 to 88, y=6 to 87)
    # --------------------------------------------------------------------------
    host_box = patches.FancyBboxPatch((4, 6), 84, 81, boxstyle='round,pad=0.7',
                                      fc='#F8FAFC', ec='#475569', lw=1.8, linestyle='--')
    ax.add_patch(host_box)
    
    # Unified Header Bar across top of Pi 5 host (x=6 to 86, y=79.8 to 85.6)
    hdr_box = patches.FancyBboxPatch((6, 79.8), 80, 5.8, boxstyle='round,pad=0.2', fc='#E2E8F0', ec='#94A3B8', lw=1.0)
    ax.add_patch(hdr_box)
    ax.text(46, 83.6, 'Primary Embedded Host Computer: Raspberry Pi 5 (8GB DDR4 RAM)',
            fontsize=8.6, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(46, 81.4, 'Linux Host OS  |  Docker Containers: Ubuntu 20.04 (ROS 2 Humble)  |  --net=host',
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

    # 2. Container: micro_ros_agent (Bridge) - Bottom Left (x=7 to 43, y=8 to 41)
    c2_box = patches.FancyBboxPatch((7, 8), 36, 33, boxstyle='round,pad=0.3', fc='#FEFCE8', ec='#EAB308', lw=1.4)
    ax.add_patch(c2_box)
    ax.text(25, 37.7, 'Container: micro_ros_agent\n[Deterministic Hardware Bridge]',
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#A16207', linespacing=1.2)
    ax.plot([7, 43], [34.0, 34.0], color='#EAB308', lw=0.9)
    c2_text = (
        "• micro-ROS Agent Daemon (Client Bridge)\n"
        "• Hardware UART Link @ 921,600 Baud\n"
        "• Subscribes: /cmd_vel (Twist Commands)\n"
        "• Publishes: /odom_raw (Wheel Ticks)\n"
        "• Publishes: /battery_state (7.4V Telemetry)\n"
        "• Deterministic 50 Hz Hardware Clock\n"
        "• Target: ESP32-S3 Motor Co-Processor"
    )
    ax.text(8.5, 32.2, c2_text, fontsize=6.8, va='top', color='#422006', linespacing=1.28)

    # 3. Container: yahboom_gesture (Cognition Pipeline) - Middle Column (x=50 to 86, y=8 to 77)
    c3_box = patches.FancyBboxPatch((50, 8), 36, 69, boxstyle='round,pad=0.3', fc='#F0FDF4', ec='#16A34A', lw=1.5)
    ax.add_patch(c3_box)
    ax.text(68, 74.2, 'Container: yahboom_gesture\n[Edge Vision & Decision Cognition]',
            fontsize=8.4, fontweight='bold', ha='center', va='center', color='#15803D', linespacing=1.2)
    ax.plot([50, 86], [70.5, 70.5], color='#16A34A', lw=0.9)

    # 4 Well-Spaced Node Tiles Inside yahboom_gesture filling from y=70 down to y=10
    nodes = [
        ("1. camera_pub (20 FPS)",
         "• Video capture: /dev/video0\n• Publishes: /camera/image_raw (Compressed)", 58.5, 11.5),
        ("2. person_detection_node (YOLOv8n)",
         "• Spatial ROI gate [45% × 65%]\n• Isolates closest interacting operator\n• Publishes: /cognition/detection", 43.0, 13.5),
        ("3. gesture_node (10 Hz, 1.2 ms)",
         "• MediaPipe HandLandmarker (21 3D pts)\n• 19-D invariant feature extraction\n• MLP ONNX classifier (99.38% test acc)\n• Publishes: /cognition/gesture", 26.5, 14.5),
        ("4. brain_node (Supervisory Logic)",
         "• 3/5 Majority filter & 3.0s subject lock\n• Visual servoing follow mode (Kp = 1.5)\n• LiDAR Emergency Preemption (< 0.36m)\n• Publishes: /cmd_vel_gesture (Pri 40)", 9.5, 15.0),
    ]
    for n_title, n_body, n_y, n_h in nodes:
        n_box = patches.FancyBboxPatch((51.5, n_y), 33.0, n_h, boxstyle='round,pad=0.18', fc='#FFFFFF', ec='#86EFAC', lw=1.0)
        ax.add_patch(n_box)
        ax.text(53.0, n_y + n_h - 2.2, n_title, fontsize=6.9, fontweight='bold', color='#15803D')
        ax.text(53.0, n_y + n_h - 4.2, n_body, fontsize=6.1, va='top', color='#14532D', linespacing=1.2)

    # Connecting arrows between pipeline nodes in the gaps
    arrow_gaps = [(58.5, 56.5), (43.0, 41.0), (26.5, 24.5)]
    for top_y, bot_y in arrow_gaps:
        ax.annotate('', xy=(68.0, bot_y), xytext=(68.0, top_y),
                    arrowprops=dict(arrowstyle='->', lw=1.4, color='#15803D'))

    # Inter-Container Connectors (DDS Shared Memory Loopback) - Clean channel (x=43 to 50)
    ax.annotate('', xy=(50, 60), xytext=(43, 60), arrowprops=dict(arrowstyle='<->', lw=1.8, color='#3B82F6'))
    ax.text(46.5, 64.2, 'DDS Loopback\n/scan, /camera', fontsize=6.0, ha='center', va='center',
            fontweight='bold', color='#1D4ED8',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#3B82F6', lw=0.8))

    ax.annotate('', xy=(50, 24), xytext=(43, 24), arrowprops=dict(arrowstyle='<->', lw=1.8, color='#D97706'))
    ax.text(46.5, 28.2, 'micro-ROS Bridge\n/cmd_vel, /odom', fontsize=6.0, ha='center', va='center',
            fontweight='bold', color='#B45309',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#D97706', lw=0.8))

    # --------------------------------------------------------------------------
    # RIGHT CONTAINER: Engineering Host Workstation (x=98 to 136, y=6 to 87)
    # --------------------------------------------------------------------------
    ws_box = patches.FancyBboxPatch((98, 6), 38, 81, boxstyle='round,pad=0.7',
                                    fc='#FAF5FF', ec='#9333EA', lw=1.8)
    ax.add_patch(ws_box)
    ax.text(117, 83.6, 'Engineering Host Workstation\n(x86_64 Development PC)',
            fontsize=8.6, fontweight='bold', ha='center', va='center', color='#7E22CE', linespacing=1.2)
    ax.plot([98, 136], [79.8, 79.8], color='#9333EA', lw=0.9)

    # 4 Elegant Functional Cards Filling the Workstation from y=78 down to y=8 (ZERO WHITE SPACE!)
    ws_cards = [
        ("Compute Host & Software Stack",
         "• AMD Ryzen 5 Hexa-Core CPU | 8GB DDR4 RAM\n"
         "• Host OS: Ubuntu 24.04 LTS (Noble Numbat)\n"
         "• ROS 2 Jazzy Jalisco Development Workspace\n"
         "• Shared DDS Middleware (ROS_DOMAIN_ID=0)", 62.5, 15.5, '#7C3AED', '#F3E8FF'),
        ("RViz2 Visualization & SLAM Operations",
         "• /scan (MS200 LiDAR 2D Planar Point Cloud)\n"
         "• /map (SLAM Toolbox Occupancy Grid Map)\n"
         "• /tf Dynamic Coordinate Frames Tree\n"
         "• Live Compressed Video Camera Display", 44.5, 16.0, '#2563EB', '#EFF6FF'),
        ("Gazebo Harmonic Digital Twin Simulation",
         "• Sim-to-Real Multi-Body Dynamics & Physics\n"
         "• Virtual Planar LiDAR & 6-Axis IMU Models\n"
         "• Wheel Slip & Surface Friction Calibration\n"
         "• Synthetic Sensor Noise Benchmarking", 26.5, 16.0, '#0D9488', '#F0FDFA'),
        ("Safety Teleoperation & ML Optimization",
         "• /joy Low-Latency Bluetooth Joystick Teleop\n"
         "• Priority 90 Hardware E-Stop Cutoff Override\n"
         "• PyTorch Gesture Training Pipeline (MLP/LSTM)\n"
         "• ONNX Runtime Edge Model Quantization", 8.5, 16.0, '#DC2626', '#FEF2F2'),
    ]

    for c_title, c_text, c_y, c_h, ec_c, fc_c in ws_cards:
        c_patch = patches.FancyBboxPatch((99.8, c_y), 34.4, c_h, boxstyle='round,pad=0.2', fc=fc_c, ec=ec_c, lw=1.1)
        ax.add_patch(c_patch)
        ax.text(101.5, c_y + c_h - 2.3, c_title, fontsize=6.8, fontweight='bold', color=ec_c)
        ax.text(101.5, c_y + c_h - 4.4, c_text, fontsize=6.0, va='top', color='#1E293B', linespacing=1.22)

    # High-Speed Wi-Fi DDS Network Link in Clean Center Channel (x=88 to 98)
    ax.annotate('', xy=(98, 45), xytext=(88, 45),
                arrowprops=dict(arrowstyle='<->', lw=2.2, color='#7C3AED', linestyle=':'))
    ax.text(93.0, 50.5, 'Wi-Fi 5 GHz\nDDS Link\nDOMAIN=0', fontsize=6.5, ha='center', va='bottom',
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
