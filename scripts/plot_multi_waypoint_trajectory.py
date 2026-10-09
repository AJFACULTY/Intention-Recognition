#!/usr/bin/env python3
"""
plot_multi_waypoint_trajectory.py — Publication Trajectory & Kinematics Plotter
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Standards Compliance: IEEE Robotics / ROS REP-103/105

Decodes empirical ROS 2 SQLite3 bag files (*.db3) from physical AMR mission runs:
  - Extracts /amcl_pose, /odometry/filtered, /odom_raw, /cmd_vel, and /plan
  - Evaluates trajectory adherence against the calibrated Geometric L-Corridor topology:
      P1 (0.08, 0.05) -> P2 (1.64, 1.62) -> P3 (3.20, 3.20) -> P4 (4.70, 1.80)
  - Computes Mean Absolute Error (MAE), cross-track error, and kinematic profiles
  - Generates a publication-grade 3-panel figure for thesis Chapter 4 (Fig 4.3 / §4.5)
"""

import os
import sys
import math
import glob
import sqlite3
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

# Import ROS 2 message deserialization
try:
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry, Path
    from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
    HAS_ROS2 = True
except ImportError:
    HAS_ROS2 = False


@dataclass
class Waypoint:
    name: str
    x: float
    y: float
    yaw_deg: float
    role: str


# Calibrated Ground-Truth Geometric L-Form Topology
CALIBRATED_WAYPOINTS = [
    Waypoint("P1: Dock Base", 0.08, 0.05, 45.0, "Base of L (Home)"),
    Waypoint("P2: Central Hub", 1.64, 1.62, 45.0, "Collinear Midpoint"),
    Waypoint("P3: North Corner", 3.20, 3.20, 90.0, "Elbow Vertex of L"),
    Waypoint("P4: East Lab Post", 4.70, 1.80, -43.0, "End of Short Leg"),
]


def find_db3_file(target_path: str) -> str:
    """Locates the .db3 sqlite file from a directory or direct file path."""
    if os.path.isfile(target_path) and target_path.endswith(".db3"):
        return target_path
    if os.path.isdir(target_path):
        db_files = sorted(glob.glob(os.path.join(target_path, "*.db3")))
        if db_files:
            return db_files[0]
        # Check subdirectories
        db_files = sorted(glob.glob(os.path.join(target_path, "**", "*.db3"), recursive=True))
        if db_files:
            return db_files[0]
    raise FileNotFoundError(f"Could not locate any .db3 sqlite database inside: {target_path}")


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    """Computes planar Euler yaw (radians) from a quaternion."""
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def distance_point_to_segment(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    """Computes perpendicular Euclidean distance from point p to line segment ab."""
    ab = b - a
    ab_len_sq = np.dot(ab, ab)
    if ab_len_sq < 1e-9:
        return np.linalg.norm(p - a)
    t = max(0.0, min(1.0, np.dot(p - a, ab) / ab_len_sq))
    projection = a + t * ab
    return np.linalg.norm(p - projection)


def parse_ros2_bag(db_path: str):
    """Parses telemetry streams from SQLite3 rosbag."""
    if not HAS_ROS2:
        raise RuntimeError("rclpy.serialization or standard ROS 2 message packages not available.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, type FROM topics")
    all_topics = cursor.fetchall()
    topic_map = {row[0]: (row[1], row[2]) for row in all_topics}
    inv_topic_map = {row[1]: (row[0], row[2]) for row in all_topics}

    # Check for available pose topics (prefer AMCL, fallback to EKF, then raw odom)
    pose_stream = []
    vel_stream = []
    
    # Priority for pose: /amcl_pose > /odometry/filtered > /odom_raw
    chosen_pose_topic = None
    for candidate in ['/amcl_pose', '/odometry/filtered', '/odom_raw']:
        if candidate in inv_topic_map:
            t_id = inv_topic_map[candidate][0]
            cursor.execute("SELECT COUNT(*) FROM messages WHERE topic_id = ?", (t_id,))
            cnt = cursor.fetchone()[0]
            if cnt > 0:
                chosen_pose_topic = candidate
                break

    if not chosen_pose_topic:
        raise ValueError("No valid pose topic (/amcl_pose, /odometry/filtered, /odom_raw) found in bag.")

    print(f"[*] Ingesting pose trajectory from topic: {chosen_pose_topic}")
    pose_tid, pose_type = inv_topic_map[chosen_pose_topic]

    cursor.execute("SELECT timestamp, data FROM messages WHERE topic_id = ? ORDER BY timestamp ASC", (pose_tid,))
    rows = cursor.fetchall()

    t0 = rows[0][0] if rows else 0

    for ts, data in rows:
        t_rel = (ts - t0) * 1e-9
        if chosen_pose_topic == '/amcl_pose':
            msg = deserialize_message(data, PoseWithCovarianceStamped)
            px = msg.pose.pose.position.x
            py = msg.pose.pose.position.y
            orient = msg.pose.pose.orientation
            yaw = quaternion_to_yaw(orient.x, orient.y, orient.z, orient.w)
            pose_stream.append((t_rel, px, py, yaw))
        else:
            msg = deserialize_message(data, Odometry)
            px = msg.pose.pose.position.x
            py = msg.pose.pose.position.y
            orient = msg.pose.pose.orientation
            yaw = quaternion_to_yaw(orient.x, orient.y, orient.z, orient.w)
            pose_stream.append((t_rel, px, py, yaw))
            # Also capture twist if available in Odometry
            vx = msg.twist.twist.linear.x
            wz = msg.twist.twist.angular.z
            vel_stream.append((t_rel, vx, wz))

    # If vel_stream is empty, look for /cmd_vel or /cmd_vel_nav
    if not vel_stream:
        for v_cand in ['/cmd_vel', '/cmd_vel_nav']:
            if v_cand in inv_topic_map:
                v_tid = inv_topic_map[v_cand][0]
                cursor.execute("SELECT timestamp, data FROM messages WHERE topic_id = ? ORDER BY timestamp ASC", (v_tid,))
                v_rows = cursor.fetchall()
                if v_rows:
                    print(f"[*] Ingesting command velocities from topic: {v_cand}")
                    for ts, data in v_rows:
                        t_rel = (ts - t0) * 1e-9
                        msg = deserialize_message(data, Twist)
                        vel_stream.append((t_rel, msg.linear.x, msg.angular.z))
                    break

    conn.close()
    return chosen_pose_topic, pose_stream, vel_stream


def compute_metrics(pose_stream, waypoints: List[Waypoint]):
    """Computes quantitative tracking metrics (displacement, velocity, cross-track error)."""
    t_vals = np.array([p[0] for p in pose_stream])
    x_vals = np.array([p[1] for p in pose_stream])
    y_vals = np.array([p[2] for p in pose_stream])
    yaw_vals = np.array([p[3] for p in pose_stream])

    # Compute step-by-step displacement
    dx = np.diff(x_vals)
    dy = np.diff(y_vals)
    step_lens = np.sqrt(dx**2 + dy**2)
    total_distance = np.sum(step_lens)
    duration = t_vals[-1] - t_vals[0] if len(t_vals) > 1 else 0.0

    # Cross-track error against the closest active corridor segment
    # Segment 1: P1 -> P2, Segment 2: P2 -> P3, Segment 3: P3 -> P4
    segments = [
        (np.array([waypoints[0].x, waypoints[0].y]), np.array([waypoints[1].x, waypoints[1].y])),
        (np.array([waypoints[1].x, waypoints[1].y]), np.array([waypoints[2].x, waypoints[2].y])),
        (np.array([waypoints[2].x, waypoints[2].y]), np.array([waypoints[3].x, waypoints[3].y])),
    ]

    cte_vals = []
    for x, y in zip(x_vals, y_vals):
        pt = np.array([x, y])
        min_dist = min(distance_point_to_segment(pt, s[0], s[1]) for s in segments)
        cte_vals.append(min_dist)

    cte_vals = np.array(cte_vals)
    mae_cte = float(np.mean(cte_vals))
    max_cte = float(np.max(cte_vals))
    rmse_cte = float(np.sqrt(np.mean(cte_vals**2)))

    # Per-waypoint closest approach
    wp_errors = {}
    for wp in waypoints:
        dists = np.sqrt((x_vals - wp.x)**2 + (y_vals - wp.y)**2)
        min_approach = float(np.min(dists))
        wp_errors[wp.name] = min_approach

    return {
        "duration_sec": duration,
        "total_distance_m": total_distance,
        "mae_cte_m": mae_cte,
        "max_cte_m": max_cte,
        "rmse_cte_m": rmse_cte,
        "wp_errors": wp_errors,
        "t": t_vals,
        "x": x_vals,
        "y": y_vals,
        "yaw": yaw_vals,
        "cte": cte_vals,
    }


def generate_publication_plot(metrics, vel_stream, waypoints, output_path: str, pose_topic: str):
    """Renders a publication-grade 3-panel figure with spatial trajectory, cross-track error, and velocity profiles."""
    fig = plt.figure(figsize=(15, 10), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0], hspace=0.32, wspace=0.25)

    ax_spatial = fig.add_subplot(gs[:, 0])      # Left column: 2D Spatial Layout (full height)
    ax_cte = fig.add_subplot(gs[0, 1])          # Top right: Cross-Track Error & Yaw
    ax_vel = fig.add_subplot(gs[1, 1])          # Bottom right: Kinematics & Velocity

    t = metrics["t"]
    x = metrics["x"]
    y = metrics["y"]
    yaw_deg = np.rad2deg(metrics["yaw"])
    cte = metrics["cte"]

    # ── 1. Panel 1: 2D Spatial Trajectory & L-Corridor Guideline ─────────────
    ax_spatial.set_title(
        "(a) Empirical Physical Navigation Trajectory (Geometric L-Form)",
        fontsize=12, fontweight='bold', pad=12
    )

    # Reference corridor guideline
    wp_x = [wp.x for wp in waypoints]
    wp_y = [wp.y for wp in waypoints]
    ax_spatial.plot(
        wp_x, wp_y,
        color='#7E57C2', linestyle='--', linewidth=2.5, alpha=0.85,
        label='Geometric L-Corridor Guideline (Planned)'
    )

    # Empirical driven trajectory path
    # Color-code by time progression
    scatter = ax_spatial.scatter(
        x, y, c=t, cmap='viridis', s=18, alpha=0.9,
        edgecolors='none', label=f'Driven Trajectory ({pose_topic})'
    )
    cbar = plt.colorbar(scatter, ax=ax_spatial, orientation='horizontal', pad=0.08, fraction=0.046)
    cbar.set_label('Mission Elapsed Time (s)', fontsize=10)

    # Directional heading quiver arrows every 10 samples
    skip = max(1, len(x) // 25)
    u = np.cos(metrics["yaw"][::skip]) * 0.15
    v = np.sin(metrics["yaw"][::skip]) * 0.15
    ax_spatial.quiver(
        x[::skip], y[::skip], u, v,
        color='#E91E63', scale=1, scale_units='xy', angles='xy',
        width=0.005, alpha=0.75, label='Heading Vector (Yaw)'
    )

    # Waypoint Markers & Pins
    wp_colors = ['#4CAF50', '#00ACC1', '#E91E63', '#FF9800']
    for i, wp in enumerate(waypoints):
        ax_spatial.scatter(
            wp.x, wp.y, color=wp_colors[i % len(wp_colors)],
            s=160, zorder=6, edgecolors='black', linewidth=1.5
        )
        # Tolerance radius circle (0.12m)
        circle = Circle((wp.x, wp.y), 0.12, color=wp_colors[i % len(wp_colors)], fill=False, linestyle=':', linewidth=1.2, alpha=0.6)
        ax_spatial.add_patch(circle)
        
        offset_x = 0.18 if i != 3 else -0.45
        offset_y = 0.12 if i != 2 else -0.22
        ax_spatial.annotate(
            f"{wp.name}\n({wp.x:.2f}m, {wp.y:.2f}m)",
            (wp.x, wp.y),
            xytext=(wp.x + offset_x, wp.y + offset_y),
            fontsize=8.5, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=wp_colors[i % len(wp_colors)], alpha=0.9),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8)
        )

    ax_spatial.set_xlabel('Global X Coordinate (meters)', fontsize=11)
    ax_spatial.set_ylabel('Global Y Coordinate (meters)', fontsize=11)
    ax_spatial.grid(True, linestyle=':', alpha=0.6)
    ax_spatial.axis('equal')
    ax_spatial.legend(loc='lower right', fontsize=8.5, framealpha=0.9)

    # ── 2. Panel 2: Cross-Track Error & Heading Deviation vs Time ─────────────
    ax_cte.set_title(
        f"(b) Path Tracking Error (MAE = {metrics['mae_cte_m']*100:.1f} cm | RMSE = {metrics['rmse_cte_m']*100:.1f} cm)",
        fontsize=11, fontweight='bold', pad=10
    )
    line1 = ax_cte.plot(t, cte * 100.0, color='#D32F2F', linewidth=2.0, label='Cross-Track Error (cm)')
    ax_cte.axhline(12.0, color='gray', linestyle='--', linewidth=1.2, label='Goal Tolerance Limit (12 cm)')
    ax_cte.set_xlabel('Mission Time (seconds)', fontsize=10)
    ax_cte.set_ylabel('Cross-Track Error (cm)', fontsize=10, color='#D32F2F')
    ax_cte.tick_params(axis='y', labelcolor='#D32F2F')
    ax_cte.grid(True, linestyle=':', alpha=0.6)

    # Secondary axis for heading yaw
    ax_yaw = ax_cte.twinx()
    line2 = ax_yaw.plot(t, yaw_deg, color='#1976D2', linewidth=1.5, linestyle='-.', alpha=0.85, label='Chassis Yaw (deg)')
    ax_yaw.set_ylabel('Heading Yaw (°)', fontsize=10, color='#1976D2')
    ax_yaw.tick_params(axis='y', labelcolor='#1976D2')

    lines = line1 + line2 + [ax_cte.get_lines()[1]]
    labels = [l.get_label() for l in lines]
    ax_cte.legend(lines, labels, loc='upper right', fontsize=8.5, framealpha=0.9)

    # ── 3. Panel 3: Kinematics & Velocity Profile ────────────────────────────
    ax_vel.set_title("(c) Dynamic Velocity & Locomotion Kinematics", fontsize=11, fontweight='bold', pad=10)
    
    if vel_stream:
        v_t = np.array([v[0] for v in vel_stream])
        v_x = np.array([v[1] for v in vel_stream])
        v_w = np.array([v[2] for v in vel_stream])
        ax_vel.plot(v_t, v_x, color='#2E7D32', linewidth=2.0, label='Linear Velocity vx (m/s)')
        ax_vel.axhline(0.25, color='orange', linestyle='--', linewidth=1.2, label='Software Limit (0.25 m/s)')
        ax_vel.set_xlabel('Mission Time (seconds)', fontsize=10)
        ax_vel.set_ylabel('Linear Speed vx (m/s)', fontsize=10, color='#2E7D32')
        ax_vel.tick_params(axis='y', labelcolor='#2E7D32')
        ax_vel.grid(True, linestyle=':', alpha=0.6)

        ax_wz = ax_vel.twinx()
        ax_wz.plot(v_t, np.rad2deg(v_w), color='#7B1FA2', linewidth=1.5, linestyle=':', label='Angular Yaw Rate wz (°/s)')
        ax_wz.set_ylabel('Yaw Rate wz (°/s)', fontsize=10, color='#7B1FA2')
        ax_wz.tick_params(axis='y', labelcolor='#7B1FA2')

        h1, l1 = ax_vel.get_legend_handles_labels()
        h2, l2 = ax_wz.get_legend_handles_labels()
        ax_vel.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=8.5, framealpha=0.9)
    else:
        # Fallback: estimate derivative from pose
        dt = np.diff(t)
        dt[dt == 0] = 1e-4
        vx_est = np.diff(np.sqrt(x**2 + y**2)) / dt
        ax_vel.plot(t[1:], vx_est, color='#2E7D32', label='Estimated Linear Speed (m/s)')
        ax_vel.set_xlabel('Mission Time (seconds)', fontsize=10)
        ax_vel.set_ylabel('Estimated Speed (m/s)', fontsize=10)
        ax_vel.grid(True, linestyle=':', alpha=0.6)
        ax_vel.legend(loc='upper right', fontsize=8.5)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"[✓] Publication figure successfully saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Waypoint Trajectory & Kinematics Analyzer")
    parser.add_argument("bag_path", help="Path to ROS 2 bag folder or .db3 file")
    parser.add_argument("--output", "-o", default="write_up/figures/multi_waypoint_trajectory_empirical.png",
                        help="Path to output PNG publication figure")
    parser.add_argument("--docs-copy", default="docs/multi_waypoint_trajectory_empirical.png",
                        help="Optional secondary copy for repository documentation")
    args = parser.parse_args()

    db3_file = find_db3_file(args.bag_path)
    print(f"[*] Found SQLite3 bag database: {db3_file}")

    pose_topic, pose_stream, vel_stream = parse_ros2_bag(db3_file)
    print(f"[*] Ingested {len(pose_stream)} pose samples and {len(vel_stream)} velocity samples.")

    metrics = compute_metrics(pose_stream, CALIBRATED_WAYPOINTS)

    print("\n" + "="*70)
    print("      PHYSICAL MULTI-WAYPOINT AUTONOMOUS MISSION AUDIT REPORT")
    print("="*70)
    print(f"  Mission Duration:           {metrics['duration_sec']:.2f} seconds")
    print(f"  Total Trajectory Length:    {metrics['total_distance_m']:.3f} meters")
    print(f"  Mean Absolute Error (CTE):  {metrics['mae_cte_m']*100.0:.2f} cm")
    print(f"  Root Mean Square Error:     {metrics['rmse_cte_m']*100.0:.2f} cm")
    print(f"  Maximum Cross-Track Error:  {metrics['max_cte_m']*100.0:.2f} cm")
    print("-" * 70)
    print("  Closest Approach to Calibrated Waypoints:")
    for wp_name, err in metrics["wp_errors"].items():
        status = "PASSED (Goal Reached)" if err <= 0.15 else "MARGINAL"
        print(f"    • {wp_name:30s} -> Closest: {err*100.0:5.1f} cm  [{status}]")
    print("="*70 + "\n")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    generate_publication_plot(metrics, vel_stream, CALIBRATED_WAYPOINTS, args.output, pose_topic)

    if args.docs_copy:
        os.makedirs(os.path.dirname(args.docs_copy), exist_ok=True)
        import shutil
        shutil.copy2(args.output, args.docs_copy)
        print(f"[✓] Documentation artifact synchronized: {args.docs_copy}")


if __name__ == "__main__":
    main()
