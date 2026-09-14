#!/usr/bin/env python3
"""
generate_simulation_animation.py — High-Definition Animated Simulation Video
Cognition Robot Project — Milestone 10 (Options A & C Visual Demo)

Renders a 25 FPS MP4 video demonstrating:
1. Closed-loop visual servoing tracking human S-curve
2. Hall's Proxemics social distance deceleration and complete stop
3. Sudden obstacle breach (< 0.36m) triggering LiDAR emergency halt & 20cm active reverse
4. Pivot escape maneuver and safety restoration
"""

import math
import os
import sys
import numpy as np
import cv2

def render_demo():
    fps = 25
    total_time = 18.0  # 18 seconds
    total_frames = int(total_time * fps)
    dt = 1.0 / fps

    width, height = 960, 540
    arena_w = 620
    hud_w = width - arena_w

    temp_video_path = "/tmp/raw_sim_demo.mp4"
    final_video_path = "/home/j/.gemini/antigravity-ide/brain/0993ee47-346b-4124-804b-eb47d2e3e8df/visual_servoing_and_safety_demo.mp4"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    # World coordinate to canvas coordinate mapping
    # World: X in [-1.5, 2.0] m, Y in [-0.5, 4.5] m
    origin_canvas_x = 310
    origin_canvas_y = 480
    scale = 90.0  # pixels per meter

    def to_canvas(wx, wy):
        cx = int(origin_canvas_x + wx * scale)
        cy = int(origin_canvas_y - wy * scale)
        return cx, cy

    # Initial states
    # Human [x, y, theta, v, w]
    hx, hy, h_theta = 0.0, 1.8, math.pi / 2.0
    # Robot [x, y, theta, v, w]
    rx, ry, r_theta = 0.0, 0.0, math.pi / 2.0
    rv, rw = 0.0, 0.0

    # Obstacle state
    obstacle_active = False
    ox, oy = 0.0, 0.0

    # Safety state
    safety_reverse_active = False
    safety_reverse_timer = 0.0
    safety_halt_active = False

    # Trace history
    h_trail = []
    r_trail = []

    for frame_idx in range(total_frames):
        t = frame_idx * dt

        # ── 1. Scenario Timeline & Human Kinematics ───────────────
        if t < 4.0:
            # Stage 1: Straight march forward
            h_v = 0.40
            h_w = 0.0
            phase_text = "STAGE 1: Straight-Line Approach"
            fsm_state = "FOLLOW: CRUISE (v = 0.20 m/s)"
            state_color = (0, 200, 0)
        elif t < 8.0:
            # Stage 2: S-curve weave
            h_v = 0.38
            h_w = -0.30 if t < 6.0 else 0.35
            phase_text = "STAGE 2: S-Curve Lateral Tracking"
            fsm_state = "FOLLOW: SERVOING STEER (Kp = 1.5)"
            state_color = (0, 220, 255)
        elif t < 11.5:
            # Stage 3: Human halts, social distance damping
            h_v = 0.0
            h_w = 0.0
            phase_text = "STAGE 3: Social Distance Hold (1.35m)"
            fsm_state = "FOLLOW: SOCIAL STANDOFF HOLD"
            state_color = (255, 180, 0)
        elif t < 15.0:
            # Stage 4: Obstacle pops in! (<0.36m)
            h_v = 0.0
            h_w = 0.0
            obstacle_active = True
            ox = rx + 0.28 * math.cos(r_theta)
            oy = ry + 0.28 * math.sin(r_theta)
            phase_text = "STAGE 4: LiDAR Obstacle Breach (< 0.36m)!"
            fsm_state = "EMERGENCY: ACTIVE REVERSE 20cm"
            state_color = (0, 0, 255)
        else:
            # Stage 5: Pivot away and resume
            h_v = 0.0
            h_w = 0.0
            obstacle_active = True
            phase_text = "STAGE 5: Escape Pivot & Safety Restored"
            fsm_state = "MANEUVER: PIVOTING AWAY"
            state_color = (0, 255, 180)

        # Update human
        h_theta += h_w * dt
        hx += h_v * math.cos(h_theta) * dt
        hy += h_v * math.sin(h_theta) * dt
        h_trail.append((hx, hy))

        # ── 2. Robot Perception & Control Law ─────────────────────
        # Distance and bearing to human
        dx = hx - rx
        dy = hy - ry
        dist_to_human = math.hypot(dx, dy)
        bearing = math.atan2(dy, dx) - r_theta
        bearing = math.atan2(math.sin(bearing), math.cos(bearing))

        # Centering error in camera frame [-0.5, 0.5]
        fov_half = math.radians(32.5)
        ex = max(-0.5, min(0.5, -bearing / fov_half))

        # Optical box width
        box_w = min(1.0, 0.55 / dist_to_human)

        # LiDAR distance check
        if obstacle_active:
            dist_to_obs = math.hypot(ox - rx, oy - ry)
        else:
            dist_to_obs = 99.0

        # LiDAR Safety Logic
        if dist_to_obs < 0.36:
            if not safety_halt_active and not safety_reverse_active:
                safety_halt_active = True
                safety_reverse_active = True
                safety_reverse_timer = 1.67  # 20 cm reverse
        elif dist_to_obs >= 0.45:
            safety_halt_active = False

        # Control decision
        if safety_reverse_active:
            safety_reverse_timer -= dt
            if safety_reverse_timer > 0:
                target_v = -0.12
                target_w = 0.0
            else:
                safety_reverse_active = False
                target_v = 0.0
                target_w = 0.0
        elif t >= 15.0:
            # Pivot escape
            target_v = 0.0
            target_w = 0.40
        else:
            # Normal visual servoing
            if abs(ex) < 0.04:
                target_w = 0.0
            else:
                target_w = max(-0.40, min(0.40, -ex * 1.5))

            if box_w > 0.42:
                target_v = 0.0
            elif box_w > 0.32:
                target_v = 0.10
            else:
                target_v = 0.20

            # Clamping if safety halt active
            if safety_halt_active and target_v > 0.0:
                target_v = 0.0

        # Slew rate
        max_dv = 0.60 * dt
        rv += max(-max_dv, min(max_dv, target_v - rv))
        max_dw = 1.50 * dt
        rw += max(-max_dw, min(max_dw, target_w - rw))

        # Integrate robot
        r_theta += rw * dt
        rx += rv * math.cos(r_theta) * dt
        ry += rv * math.sin(r_theta) * dt
        r_trail.append((rx, ry))

        # ── 3. Render Canvas ──────────────────────────────────────
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        # Background: dark slate for sleek dark mode aesthetics
        canvas[:] = (22, 27, 34)

        # ── A. Render 2D Arena ────────────────────────────────────
        # Draw grid
        for gx in np.arange(-2.0, 3.0, 0.5):
            c1 = to_canvas(gx, -1.0)
            c2 = to_canvas(gx, 5.0)
            cv2.line(canvas, (c1[0], 0), (c1[0], height), (35, 42, 54), 1)
        for gy in np.arange(-1.0, 5.5, 0.5):
            c1 = to_canvas(-2.0, gy)
            cv2.line(canvas, (0, c1[1]), (arena_w, c1[1]), (35, 42, 54), 1)

        # Draw trails
        if len(h_trail) > 1:
            pts_h = np.array([to_canvas(x, y) for x, y in h_trail[-150:]], dtype=np.int32)
            cv2.polylines(canvas, [pts_h], False, (235, 120, 40), 2, cv2.LINE_AA)
        if len(r_trail) > 1:
            pts_r = np.array([to_canvas(x, y) for x, y in r_trail[-150:]], dtype=np.int32)
            cv2.polylines(canvas, [pts_r], False, (80, 200, 100), 2, cv2.LINE_AA)

        # Draw Camera FOV cone
        rcx, rcy = to_canvas(rx, ry)
        fov_len = 1.8 * scale
        c_left_ang = r_theta + fov_half
        c_right_ang = r_theta - fov_half
        p_left = (int(rcx + fov_len * math.cos(c_left_ang)), int(rcy - fov_len * math.sin(c_left_ang)))
        p_right = (int(rcx + fov_len * math.cos(c_right_ang)), int(rcy - fov_len * math.sin(c_right_ang)))
        
        fov_poly = np.array([[rcx, rcy], p_left, p_right], dtype=np.int32)
        fov_overlay = canvas.copy()
        cv2.fillPoly(fov_overlay, [fov_poly], (50, 70, 90))
        cv2.addWeighted(fov_overlay, 0.35, canvas, 0.65, 0, canvas)
        cv2.line(canvas, (rcx, rcy), p_left, (80, 120, 160), 1, cv2.LINE_AA)
        cv2.line(canvas, (rcx, rcy), p_right, (80, 120, 160), 1, cv2.LINE_AA)

        # Draw LiDAR Safety Arc (< 0.36m frontal cone)
        lidar_color = (0, 0, 255) if (obstacle_active and dist_to_obs < 0.36) else (0, 220, 80)
        lidar_radius = int(0.36 * scale)
        cv2.ellipse(canvas, (rcx, rcy), (lidar_radius, lidar_radius),
                    0, -int(math.degrees(r_theta) + 45), -int(math.degrees(r_theta) - 45),
                    lidar_color, 2, cv2.LINE_AA)

        # Draw Obstacle (if active)
        if obstacle_active:
            ocx, ocy = to_canvas(ox, oy)
            cv2.rectangle(canvas, (ocx - 12, ocy - 12), (ocx + 12, ocy + 12), (0, 0, 240), -1)
            cv2.rectangle(canvas, (ocx - 12, ocy - 12), (ocx + 12, ocy + 12), (255, 255, 255), 1)
            cv2.putText(canvas, "OBSTACLE", (ocx - 30, ocy - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 100, 255), 1)

        # Draw Human
        hcx, hcy = to_canvas(hx, hy)
        cv2.circle(canvas, (hcx, hcy), 12, (235, 120, 40), -1, cv2.LINE_AA)
        cv2.circle(canvas, (hcx, hcy), 14, (255, 255, 255), 2, cv2.LINE_AA)
        h_heading_end = (int(hcx + 20 * math.cos(h_theta)), int(hcy - 20 * math.sin(h_theta)))
        cv2.arrowedLine(canvas, (hcx, hcy), h_heading_end, (255, 255, 255), 2, tipLength=0.3)
        cv2.putText(canvas, "HUMAN", (hcx - 22, hcy - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (235, 180, 100), 1)

        # Draw Robot Chassis (Rectangle + Wheels)
        r_w_px = int(0.22 * scale)
        r_l_px = int(0.28 * scale)
        # Rotated rectangle for robot
        rect = ((rcx, rcy), (r_w_px, r_l_px), -math.degrees(r_theta) + 90)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.fillPoly(canvas, [box], (40, 160, 80))
        cv2.polylines(canvas, [box], True, (200, 255, 200), 2, cv2.LINE_AA)
        
        # Robot heading arrow
        r_heading_end = (int(rcx + 22 * math.cos(r_theta)), int(rcy - 22 * math.sin(r_theta)))
        cv2.arrowedLine(canvas, (rcx, rcy), r_heading_end, (255, 255, 255), 2, tipLength=0.3)
        cv2.putText(canvas, "ROBOT", (rcx - 20, rcy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 140), 1)

        # Separation line
        cv2.line(canvas, (rcx, rcy), (hcx, hcy), (120, 120, 140), 1, cv2.LINE_AA)
        mid_x, mid_y = int((rcx + hcx)/2), int((rcy + hcy)/2)
        cv2.putText(canvas, f"d={dist_to_human:.2f}m", (mid_x + 8, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 220), 1)

        # ── B. Render Right HUD Panel ─────────────────────────────
        cv2.line(canvas, (arena_w, 0), (arena_w, height), (50, 60, 75), 2)
        cv2.rectangle(canvas, (arena_w, 0), (width, height), (18, 22, 28), -1)

        hx_hud = arena_w + 15
        cv2.putText(canvas, "COGNITION AUTONOMY HUD", (hx_hud, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.line(canvas, (hx_hud, 42), (width - 15, 42), (70, 85, 105), 1)

        # Timer & Stage
        cv2.putText(canvas, f"TIME: {t:04.1f} s", (hx_hud, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 200, 220), 1)
        cv2.putText(canvas, phase_text, (hx_hud, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1)

        # FSM State Box
        cv2.rectangle(canvas, (hx_hud, 115), (width - 15, 160), (30, 36, 46), -1)
        cv2.rectangle(canvas, (hx_hud, 115), (width - 15, 160), state_color, 2)
        cv2.putText(canvas, "FSM STATE:", (hx_hud + 8, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 170, 185), 1)
        cv2.putText(canvas, fsm_state, (hx_hud + 8, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.48, state_color, 2)

        # Kinematic Gauges
        y_pos = 190
        cv2.putText(canvas, "KINEMATICS & CONTROL", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)
        cv2.line(canvas, (hx_hud, y_pos + 5), (width - 15, y_pos + 5), (50, 60, 75), 1)

        # Linear velocity v_x
        y_pos += 30
        cv2.putText(canvas, f"Linear  v_x: {rv:+.2f} m/s", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 220, 180), 1)
        bar_len = int(abs(rv) / 0.25 * 100)
        bar_color = (0, 200, 100) if rv >= 0 else (0, 80, 240)
        cv2.rectangle(canvas, (hx_hud + 180, y_pos - 12), (hx_hud + 180 + bar_len, y_pos - 2), bar_color, -1)

        # Angular velocity w_z
        y_pos += 25
        cv2.putText(canvas, f"Angular w_z: {rw:+.2f} rad/s", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 200, 100), 1)

        # Centering error e_x
        y_pos += 25
        cv2.putText(canvas, f"Visual  e_x: {ex:+.2f}", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 255), 1)

        # Separation distance
        y_pos += 25
        cv2.putText(canvas, f"Human Dist:  {dist_to_human:.2f} m", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

        # Safety Diagnostics
        y_pos += 40
        cv2.putText(canvas, "ISO 15066 SAFETY ENVELOPE", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)
        cv2.line(canvas, (hx_hud, y_pos + 5), (width - 15, y_pos + 5), (50, 60, 75), 1)

        y_pos += 30
        if obstacle_active:
            obs_txt = f"Min Obstacle: {dist_to_obs:.2f} m"
            obs_col = (0, 0, 255) if dist_to_obs < 0.36 else (0, 255, 100)
            cv2.putText(canvas, obs_txt, (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, obs_col, 1)
        else:
            cv2.putText(canvas, "Min Obstacle: CLEAR (> 12m)", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 80), 1)

        y_pos += 25
        if safety_halt_active or safety_reverse_active:
            cv2.putText(canvas, "SAFETY STATUS: INTERLOCK TRIP", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 2)
            y_pos += 22
            cv2.putText(canvas, "REACTION: 20cm REVERSE RECOVERY", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
        else:
            cv2.putText(canvas, "SAFETY STATUS: PROTECTIVE CLEAR", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 80), 1)
            y_pos += 22
            cv2.putText(canvas, "REACTION: NOMINAL MOTION", (hx_hud, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 160, 180), 1)

        out.write(canvas)

    out.release()
    print(f"Raw animation written to {temp_video_path}")

    # Transcode to high-compatibility H.264 MP4 with ffmpeg
    cmd = f"ffmpeg -y -i {temp_video_path} -c:v libx264 -pix_fmt yuv420p -movflags +faststart {final_video_path}"
    os.system(cmd)
    print(f"Final MP4 video generated at: {final_video_path}")

if __name__ == '__main__':
    render_demo()
