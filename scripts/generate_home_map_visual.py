#!/usr/bin/env python3
"""
generate_home_map_visual.py
Renders an annotated, publication-grade visualization of the room occupancy grid map,
highlighting the exact Home Base coordinate (0.00, 0.00), the wall clearance boundary,
and the calibrated patrol waypoints (WP1, WP2, WP3, and calibrated Home).
"""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2
import numpy as np

def main():
    map_path = 'project_history/robot_audits/room_map_20260812_0826.png'
    out_path = 'project_history/robot_audits/map_home_and_waypoints_explained.png'
    
    img = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: could not open {map_path}")
        return
        
    h, w = img.shape
    res = 0.05
    origin_x = -2.4
    origin_y = -3.84

    fig, ax = plt.subplots(figsize=(10, 10), dpi=220)

    # 3-channel RGB image for occupancy grid
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[img == 0] = [25, 25, 30]       # Obstacles (black walls)
    rgb[img == 254] = [255, 255, 255]  # Free space (pure white)
    rgb[img == 205] = [235, 238, 242]  # Unexplored area (soft light blue-grey)

    # Flip vertically so Row 0 (top of PNG) maps to Y_max in Cartesian axes
    rgb_cartesian = cv2.flip(rgb, 0)

    ax.imshow(rgb_cartesian, extent=[origin_x, origin_x + w * res, origin_y, origin_y + h * res], origin='lower')

    # Coordinates (meters)
    home_orig_x, home_orig_y = 0.00, 0.00
    home_safe_x, home_safe_y = 0.08, 0.05
    wp1_x, wp1_y = 0.40, 0.00
    wp2_x, wp2_y = 0.70, 0.35
    wp3_x, wp3_y = 0.35, 0.15

    # Trajectory loop
    route_x = [home_safe_x, wp1_x, wp2_x, wp3_x, home_safe_x]
    route_y = [home_safe_y, wp1_y, wp2_y, wp3_y, home_safe_y]
    ax.plot(route_x, route_y, color='#2563EB', linestyle='--', linewidth=2.4, zorder=3, label='Calibrated Patrol Path (Closed Loop)')

    # Add direction arrows along paths
    for i in range(len(route_x) - 1):
        dx = route_x[i+1] - route_x[i]
        dy = route_y[i+1] - route_y[i]
        mx = route_x[i] + dx * 0.50
        my = route_y[i] + dy * 0.50
        ax.annotate('', xy=(mx + dx*0.08, my + dy*0.08), xytext=(mx, my),
                    arrowprops=dict(arrowstyle='->', color='#1D4ED8', lw=2.2), zorder=4)

    # 15cm inflation hazard circle around original (0,0)
    inflation_circle = patches.Circle((home_orig_x, home_orig_y), 0.15,
                                      linewidth=1.5, edgecolor='#DC2626', facecolor='#F87171',
                                      alpha=0.25, linestyle='--', label='15cm Costmap Wall Inflation Cushion')
    ax.add_patch(inflation_circle)

    # Robot footprint circle (12cm radius) at calibrated Home
    footprint_circle = patches.Circle((home_safe_x, home_safe_y), 0.12,
                                      linewidth=1.5, edgecolor='#16A34A', facecolor='#86EFAC',
                                      alpha=0.35, label='Robot Footprint (r = 0.12m)')
    ax.add_patch(footprint_circle)

    # Scatter points
    ax.scatter([home_orig_x], [home_orig_y], color='#DC2626', s=160, edgecolors='black', linewidth=1.5, zorder=6,
               label='Original Home (0.00, 0.00) — Borderline Inflation Risk')
    ax.scatter([home_safe_x], [home_safe_y], color='#16A34A', s=220, edgecolors='black', linewidth=2.0, zorder=7,
               label='Calibrated Home Base (0.08, 0.05) — Safe Clearance')
    ax.scatter([wp1_x], [wp1_y], color='#9333EA', s=160, edgecolors='black', linewidth=1.5, zorder=6,
               label='WP1: Runway Transit (0.40, 0.00)')
    ax.scatter([wp2_x], [wp2_y], color='#EA580C', s=160, edgecolors='black', linewidth=1.5, zorder=6,
               label='WP2: Aisle Curve Inspection (0.70, 0.35)')
    ax.scatter([wp3_x], [wp3_y], color='#0891B2', s=160, edgecolors='black', linewidth=1.5, zorder=6,
               label='WP3: Return Leg Midpoint (0.35, 0.15)')

    # Labels with callout boxes
    ax.text(home_orig_x - 0.36, home_orig_y - 0.16, 'ORIGINAL HOME\n(0.00, 0.00)m\n[Near Wall Cushion]',
            fontsize=8.5, fontweight='bold', color='#991B1B',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEE2E2', edgecolor='#EF4444', alpha=0.92))

    ax.text(home_safe_x - 0.24, home_safe_y + 0.25, 'CALIBRATED HOME BASE\n(0.08, 0.05)m [SAFE CLEARANCE]',
            fontsize=8.5, fontweight='bold', color='#166534',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#DCFCE7', edgecolor='#22C55E', alpha=0.95))

    ax.text(wp1_x - 0.05, wp1_y - 0.15, 'WP1: Runway Transit\n(0.40, 0.00)m',
            fontsize=8.5, fontweight='bold', color='#6B21A8',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E8FF', edgecolor='#A855F7', alpha=0.92))

    ax.text(wp2_x + 0.04, wp2_y + 0.03, 'WP2: Aisle Curve\n(0.70, 0.35)m',
            fontsize=8.5, fontweight='bold', color='#9A3412',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEDD5', edgecolor='#F97316', alpha=0.92))

    ax.text(wp3_x + 0.04, wp3_y + 0.05, 'WP3: Return Leg\n(0.35, 0.15)m',
            fontsize=8.5, fontweight='bold', color='#155E75',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#CFFAFE', edgecolor='#06B6D4', alpha=0.92))

    # Zoom window on operational room quadrant
    ax.set_xlim(-0.5, 2.0)
    ax.set_ylim(-0.7, 1.8)
    ax.set_aspect('equal', adjustable='box')

    ax.set_title('Physical Testing Environment: Home Base & Nav2 Patrol Coordinates\n(Occupancy Grid Map Frame: Cartesian (X, Y) in Meters)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('Map Coordinate X (meters) — Forward Corridor Axis', fontsize=10, fontweight='bold')
    ax.set_ylabel('Map Coordinate Y (meters) — Lateral Aisle Axis', fontsize=10, fontweight='bold')

    ax.grid(True, linestyle=':', alpha=0.55, color='#94A3B8')
    ax.legend(loc='upper right', fontsize=8.0, framealpha=0.95, facecolor='#FFFFFF', edgecolor='#CBD5E1')

    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()
    print(f"Successfully generated: {out_path}")

if __name__ == '__main__':
    main()
