#!/usr/bin/env python3
"""
simulate_visual_servoing.py — Image-Based Visual Servoing Kinematic Simulator
Cognition Robot Project — Milestone 10 (Option C Visual Servoing & Social Standoff)

Simulates the closed-loop differential drive robot tracking a walking human:
- Lateral steering law: omega = -Kp * e_x (Kp = 1.5, deadband = +/-0.04)
- Longitudinal velocity: 3-tier social distance standoff based on bounding box width
- Smooth acceleration and slew-rate limiting (0.5 m/s^2 linear, 1.2 rad/s^2 angular)
- Generates 3-panel publication-quality kinematic analysis plot
"""

import math
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate():
    dt = 0.05  # 20 Hz simulation step
    total_time = 22.0
    time_steps = int(total_time / dt)

    # Physical parameters
    FOV_H = math.radians(65.0)  # Camera horizontal FOV (65 deg)
    CAMERA_K = 0.55  # Box width scale factor: W = CAMERA_K / distance_m

    # Human Initial State [x, y, theta, speed]
    hx, hy, h_theta = 0.0, 2.2, math.pi / 2.0  # Walking along +Y
    
    # Robot Initial State [x, y, theta, v, w]
    rx, ry, r_theta = 0.0, 0.0, math.pi / 2.0
    rv, rw = 0.0, 0.0
    g_pan = 0.0

    # Control parameters (identical to brain_node.py)
    KP_ANGULAR = 1.5
    MAX_ANGULAR = 0.40
    MAX_LINEAR = 0.20
    DEADBAND = 0.04
    W_STOP = 0.42     # Distance < 1.3m -> Stop
    W_DAMP = 0.32     # Distance 1.3m - 1.7m -> 50% speed
    
    # Slew rate limiters (smooth physical acceleration)
    MAX_A_LIN = 0.50   # m/s^2
    MAX_A_ANG = 1.20   # rad/s^2

    # Data logs
    t_log = []
    hx_log, hy_log = [], []
    rx_log, ry_log = [], []
    dist_log = []
    w_log = []
    ex_log = []
    rv_log, rw_log = [], []

    for step in range(time_steps):
        t = step * dt
        t_log.append(t)

        # ── 1. Human Motion Profile ───────────────────────────────
        if t < 4.0:
            # Straight walk forward (+Y)
            h_v = 0.45
            h_w = 0.0
        elif t < 8.0:
            # Gentle curve to the right (+X)
            h_v = 0.40
            h_w = -0.22
        elif t < 12.0:
            # S-curve weave back to left (-X)
            h_v = 0.40
            h_w = 0.25
        elif t < 16.0:
            # Abrupt stop (social interaction dwell)
            h_v = 0.0
            h_w = 0.0
        elif t < 18.0:
            # Operator takes a step backward (-0.15 m/s)
            h_v = -0.15
            h_w = 0.0
        else:
            # Stationary final stance
            h_v = 0.0
            h_w = 0.0

        h_theta += h_w * dt
        hx += h_v * math.cos(h_theta) * dt
        hy += h_v * math.sin(h_theta) * dt

        hx_log.append(hx)
        hy_log.append(hy)

        # ── 2. Camera Observation & Visual Servoing ───────────────
        dx = hx - rx
        dy = hy - ry
        dist = math.hypot(dx, dy)
        dist_log.append(dist)

        # Bearing angle of human relative to robot heading
        bearing = math.atan2(dy, dx) - r_theta
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))  # Wrap to [-pi, pi]

        # ── 2-DOF Pan Gimbal Kinematics (Active Vision Node) ─────
        # Gimbal pans toward human up to +/-60 deg (+/-1.05 rad) with 3.0 rad/s servo speed
        target_pan = max(-math.radians(60.0), min(math.radians(60.0), bearing))
        max_dpan = 3.0 * dt
        dpan = target_pan - g_pan
        g_pan += max(-max_dpan, min(max_dpan, dpan))

        # Optical error on camera image plane: residual angle between human and camera optical axis
        optical_residual = bearing - g_pan
        norm_error = -optical_residual / (FOV_H / 2.0)
        norm_error = max(-0.5, min(0.5, norm_error))
        ex = norm_error
        ex_log.append(ex)

        # Bounding box width inversely proportional to distance
        box_w = min(1.0, max(0.05, CAMERA_K / dist))
        w_log.append(box_w)

        # ── 3. Coupled Eye-to-Base Visual Servoing Control Law ────
        # Total target bearing = gimbal pan angle + residual optical offset
        total_bearing = g_pan + optical_residual

        # Lateral Steering Law (Coupled Eye-to-Base)
        if abs(total_bearing) < DEADBAND:
            target_w = 0.0
        else:
            target_w = -total_bearing * KP_ANGULAR
            target_w = max(-MAX_ANGULAR, min(MAX_ANGULAR, target_w))

        # Longitudinal Velocity Law (Social Distance Standoff)
        if box_w > W_STOP:
            target_v = 0.0
        elif box_w > W_DAMP:
            target_v = MAX_LINEAR * 0.5
        else:
            target_v = MAX_LINEAR

        # ── 4. Acceleration Ramping (Slew Limiting) ────────────────
        max_dv = MAX_A_LIN * dt
        dv = target_v - rv
        rv += max(-max_dv, min(max_dv, dv))

        max_dw = MAX_A_ANG * dt
        dw = target_w - rw
        rw += max(-max_dw, min(max_dw, dw))

        rv_log.append(rv)
        rw_log.append(rw)

        # ── 5. Robot Kinematic Integration (Diff Drive) ───────────
        r_theta += rw * dt
        rx += rv * math.cos(r_theta) * dt
        ry += rv * math.sin(r_theta) * dt

        rx_log.append(rx)
        ry_log.append(ry)

    # ── 6. Generate Publication Plot ──────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [1.6, 1.0, 1.0]})
    fig.patch.set_facecolor('#FFFFFF')

    # Color palette
    color_human = '#2563EB'  # Deep Blue
    color_robot = '#059669'  # Emerald Green
    color_accent = '#D97706' # Amber

    # Panel 1: 2D Spatial Trajectory
    ax1 = axes[0]
    ax1.plot(hx_log, hy_log, label='Human Trajectory (Target)', color=color_human, linewidth=2.5, linestyle='--')
    ax1.plot(rx_log, ry_log, label='Robot Servoing Path (Chassis)', color=color_robot, linewidth=2.5)

    # Timestamp markers every 4 seconds
    for mark_t in [0.0, 4.0, 8.0, 12.0, 16.0, 20.0]:
        idx = int(mark_t / dt)
        if idx < len(hx_log):
            ax1.scatter(hx_log[idx], hy_log[idx], color=color_human, s=40, zorder=5)
            ax1.scatter(rx_log[idx], ry_log[idx], color=color_robot, s=40, zorder=5)
            ax1.text(hx_log[idx] + 0.08, hy_log[idx], f"H ({mark_t:.0f}s)", fontsize=9, color=color_human, weight='bold')
            ax1.text(rx_log[idx] - 0.28, ry_log[idx], f"R ({mark_t:.0f}s)", fontsize=9, color=color_robot, weight='bold')

    ax1.set_title('(a) Closed-Loop Visual Servoing Spatial Trajectory Tracking (FOLLOW Mode)', fontsize=12, weight='bold', pad=10)
    ax1.set_xlabel('Lateral Displacement X (meters)', fontsize=10)
    ax1.set_ylabel('Forward Displacement Y (meters)', fontsize=10)
    ax1.legend(loc='lower right', framealpha=0.95, fontsize=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.axis('equal')

    # Panel 2: Distance & Bounding Box Width Standoff
    ax2 = axes[1]
    color_d = '#4338CA'
    color_w = '#DC2626'
    
    line1 = ax2.plot(t_log, dist_log, color=color_d, linewidth=2.0, label='Physical Separation d (m)')
    ax2.axhline(1.30, color='#94A3B8', linestyle=':', label='Damping Threshold (1.30m)')
    ax2.axhline(1.50, color='#10B981', linestyle='--', label='Target Social Distance (1.50m)')
    ax2.set_ylabel('Separation Distance (m)', color=color_d, fontsize=10)
    ax2.tick_params(axis='y', labelcolor=color_d)
    ax2.set_ylim(0.8, 2.6)

    ax2_twin = ax2.twinx()
    line2 = ax2_twin.plot(t_log, w_log, color=color_w, linewidth=1.8, linestyle='-.', label='Optical Box Width W')
    ax2_twin.axhline(W_STOP, color='#EF4444', linestyle=':', alpha=0.7, label='Stop Margin (W=0.42)')
    ax2_twin.set_ylabel('Norm. Box Width W', color=color_w, fontsize=10)
    ax2_twin.tick_params(axis='y', labelcolor=color_w)
    ax2_twin.set_ylim(0.15, 0.65)

    ax2.set_title('(b) Inter-Agent Separation & Optical Bounding Box Width Regulation', fontsize=12, weight='bold', pad=10)
    ax2.set_xlabel('Time (seconds)', fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.6)

    # Panel 3: Commanded Velocities & Lateral Centering Error
    ax3 = axes[2]
    ax3.plot(t_log, rv_log, label='Linear Velocity v_x (m/s)', color=color_robot, linewidth=2.0)
    ax3.plot(t_log, rw_log, label='Angular Velocity omega_z (rad/s)', color=color_accent, linewidth=2.0)
    ax3.plot(t_log, ex_log, label='Lateral Centering Error e_x', color='#6B7280', linewidth=1.5, linestyle=':')
    ax3.axhline(0.0, color='black', linewidth=0.8, alpha=0.4)
    
    ax3.set_title('(c) Chassis Velocity Actuation Profiles & Visual Centering Error', fontsize=12, weight='bold', pad=10)
    ax3.set_xlabel('Time (seconds)', fontsize=10)
    ax3.set_ylabel('Velocity / Error Units', fontsize=10)
    ax3.legend(loc='upper right', framealpha=0.95, fontsize=9)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.set_ylim(-0.45, 0.45)

    plt.tight_layout()

    out_path = "/home/j/ros2_cognition_ws/write_up/figures/fig_visual_servoing_kinematics.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ High-resolution visual servoing kinematics plot saved to: {out_path}")

    # Copy to artifact directory for presentation
    art_path = "/home/j/.gemini/antigravity-ide/brain/0993ee47-346b-4124-804b-eb47d2e3e8df/fig_visual_servoing_kinematics.png"
    import shutil
    shutil.copy(out_path, art_path)
    print(f"✓ Copied to artifact directory: {art_path}")

if __name__ == '__main__':
    simulate()
