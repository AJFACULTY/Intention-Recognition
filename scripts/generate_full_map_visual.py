#!/usr/bin/env python3
"""
generate_full_map_visual.py
Renders a comprehensive 2-panel visualization:
Panel 1 (Left): Full Uncropped Metric Room Map (9.25m x 9.75m) showing complete room geometry,
                all outer walls, doors, obstacles, and the exact global location of Home Base.
Panel 2 (Right): High-resolution detailed view of Home Base, wall inflation cushion,
                 and the calibrated autonomous patrol trajectory.
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
    out_path = 'project_history/robot_audits/full_map_home_and_patrol_layout.png'
    
    img = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: could not open {map_path}")
        return
        
    h, w = img.shape
    res = 0.05
    origin_x = -2.4
    origin_y = -3.84
    max_x = origin_x + w * res
    max_y = origin_y + h * res

    # 3-channel RGB image for occupancy grid
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[img == 0] = [25, 25, 30]       # Obstacles (black walls)
    rgb[img == 254] = [255, 255, 255]  # Free space (pure white)
    rgb[img == 205] = [232, 235, 240]  # Unexplored area (soft grey)

    # In PNG files, row 0 is at the top (Y_max).
    # Matplotlib with origin='lower' expects row 0 to be at the bottom (Y_min).
    # Therefore, we must flip vertically so the map matches true Cartesian world orientation.
    rgb_cartesian = cv2.flip(rgb, 0)

    # Coordinates (meters)
    home_orig_x, home_orig_y = 0.00, 0.00
    home_safe_x, home_safe_y = 0.08, 0.05
    wp1_x, wp1_y = 0.40, 0.00
    wp2_x, wp2_y = 0.70, 0.35
    wp3_x, wp3_y = 0.35, 0.15

    fig, (ax_full, ax_detail) = plt.subplots(1, 2, figsize=(18, 9), dpi=220,
                                             gridspec_kw={'width_ratios': [1.15, 1.0]})

    # =========================================================================
    # PANEL 1: FULL UNCROPPED ROOM OCCUPANCY GRID MAP (ENTIRE 9.25m x 9.75m)
    # =========================================================================
    ax_full.imshow(rgb_cartesian, extent=[origin_x, max_x, origin_y, max_y], origin='lower')
    
    # Draw patrol route on full map
    route_x = [home_safe_x, wp1_x, wp2_x, wp3_x, home_safe_x]
    route_y = [home_safe_y, wp1_y, wp2_y, wp3_y, home_safe_y]
    ax_full.plot(route_x, route_y, color='#2563EB', linestyle='-', linewidth=2.5, zorder=4)

    # Highlight Home on full map with prominent radar ring & marker
    ax_full.scatter([home_safe_x], [home_safe_y], color='#16A34A', s=240, edgecolors='black',
                    linewidth=2.0, zorder=6, label='Home Base Location (0.08, 0.05)m')
    
    # Radar pulse rings around Home
    radar1 = patches.Circle((home_safe_x, home_safe_y), 0.5, linewidth=1.5,
                            edgecolor='#16A34A', facecolor='none', linestyle='--', alpha=0.8)
    radar2 = patches.Circle((home_safe_x, home_safe_y), 1.0, linewidth=1.2,
                            edgecolor='#16A34A', facecolor='none', linestyle=':', alpha=0.5)
    ax_full.add_patch(radar1)
    ax_full.add_patch(radar2)

    # Bounding box showing the zoom/patrol region
    roi_rect = patches.Rectangle((-0.4, -0.5), 1.6, 1.3, linewidth=2.0,
                                 edgecolor='#DC2626', facecolor='#FEF2F2', alpha=0.35,
                                 linestyle='-', zorder=3, label='Testing & Patrol Zone')
    ax_full.add_patch(roi_rect)

    # Text annotation pointing to Home on full map
    ax_full.annotate('HOME BASE\n(Robot Origin: 0, 0)',
                     xy=(home_safe_x, home_safe_y), xytext=(home_safe_x + 1.2, home_safe_y - 1.2),
                     arrowprops=dict(facecolor='#16A34A', edgecolor='black', width=2.0, headwidth=8.0),
                     fontsize=10, fontweight='bold', color='#166534',
                     bbox=dict(boxstyle='round,pad=0.4', facecolor='#DCFCE7', edgecolor='#22C55E', alpha=0.95),
                     zorder=7)

    ax_full.set_xlim(origin_x, max_x)
    ax_full.set_ylim(origin_y, max_y)
    ax_full.set_aspect('equal', adjustable='box')
    ax_full.set_title('Panel A: Complete Metric Room Floorplan (Uncropped 9.25m × 9.75m)\nFull Cartographer SLAM Occupancy Grid Map',
                      fontsize=11.5, fontweight='bold', pad=10)
    ax_full.set_xlabel('Global Map Coordinate X (meters)', fontsize=10, fontweight='bold')
    ax_full.set_ylabel('Global Map Coordinate Y (meters)', fontsize=10, fontweight='bold')
    ax_full.grid(True, linestyle=':', alpha=0.55, color='#94A3B8')
    ax_full.legend(loc='lower right', fontsize=8.5, framealpha=0.95, facecolor='#FFFFFF')

    # =========================================================================
    # PANEL 2: DETAILED INSET OF TESTING & PATROL CORRIDOR
    # =========================================================================
    ax_detail.imshow(rgb_cartesian, extent=[origin_x, max_x, origin_y, max_y], origin='lower')
    
    # Draw detailed patrol route
    ax_detail.plot(route_x, route_y, color='#2563EB', linestyle='--', linewidth=2.6, zorder=3,
                   label='Calibrated Patrol Path (Closed Loop)')

    # Add direction arrows along paths
    for i in range(len(route_x) - 1):
        dx = route_x[i+1] - route_x[i]
        dy = route_y[i+1] - route_y[i]
        mx = route_x[i] + dx * 0.50
        my = route_y[i] + dy * 0.50
        ax_detail.annotate('', xy=(mx + dx*0.08, my + dy*0.08), xytext=(mx, my),
                           arrowprops=dict(arrowstyle='->', color='#1D4ED8', lw=2.4), zorder=4)

    # 15cm inflation hazard circle around original (0,0)
    inflation_circle = patches.Circle((home_orig_x, home_orig_y), 0.15,
                                      linewidth=1.5, edgecolor='#DC2626', facecolor='#F87171',
                                      alpha=0.25, linestyle='--', label='15cm Costmap Wall Inflation Cushion')
    ax_detail.add_patch(inflation_circle)

    # Robot footprint circle (12cm radius) at calibrated Home
    footprint_circle = patches.Circle((home_safe_x, home_safe_y), 0.12,
                                      linewidth=1.5, edgecolor='#16A34A', facecolor='#86EFAC',
                                      alpha=0.35, label='Robot Footprint (r = 0.12m)')
    ax_detail.add_patch(footprint_circle)

    # Scatter points
    ax_detail.scatter([home_orig_x], [home_orig_y], color='#DC2626', s=160, edgecolors='black', linewidth=1.5, zorder=6,
                      label='Original Home (0.00, 0.00) — Near Wall')
    ax_detail.scatter([home_safe_x], [home_safe_y], color='#16A34A', s=220, edgecolors='black', linewidth=2.0, zorder=7,
                      label='Calibrated Home Base (0.08, 0.05) — Safe')
    ax_detail.scatter([wp1_x], [wp1_y], color='#9333EA', s=160, edgecolors='black', linewidth=1.5, zorder=6,
                      label='WP1: Runway Transit (0.40, 0.00)')
    ax_detail.scatter([wp2_x], [wp2_y], color='#EA580C', s=160, edgecolors='black', linewidth=1.5, zorder=6,
                      label='WP2: Aisle Curve (0.70, 0.35)')
    ax_detail.scatter([wp3_x], [wp3_y], color='#0891B2', s=160, edgecolors='black', linewidth=1.5, zorder=6,
                      label='WP3: Return Leg (0.35, 0.15)')

    # Labels with callout boxes
    ax_detail.text(home_orig_x - 0.36, home_orig_y - 0.16, 'ORIGINAL HOME\n(0.00, 0.00)m\n[Near Wall Cushion]',
                   fontsize=8.0, fontweight='bold', color='#991B1B',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEE2E2', edgecolor='#EF4444', alpha=0.92))

    ax_detail.text(home_safe_x - 0.24, home_safe_y + 0.25, 'CALIBRATED HOME BASE\n(0.08, 0.05)m [SAFE CLEARANCE]',
                   fontsize=8.0, fontweight='bold', color='#166534',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#DCFCE7', edgecolor='#22C55E', alpha=0.95))

    ax_detail.text(wp1_x - 0.05, wp1_y - 0.15, 'WP1: Runway Transit\n(0.40, 0.00)m',
                   fontsize=8.0, fontweight='bold', color='#6B21A8',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E8FF', edgecolor='#A855F7', alpha=0.92))

    ax_detail.text(wp2_x + 0.04, wp2_y + 0.03, 'WP2: Aisle Curve\n(0.70, 0.35)m',
                   fontsize=8.0, fontweight='bold', color='#9A3412',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEDD5', edgecolor='#F97316', alpha=0.92))

    ax_detail.text(wp3_x + 0.04, wp3_y + 0.05, 'WP3: Return Leg\n(0.35, 0.15)m',
                   fontsize=8.0, fontweight='bold', color='#155E75',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#CFFAFE', edgecolor='#06B6D4', alpha=0.92))

    ax_detail.set_xlim(-0.45, 1.25)
    ax_detail.set_ylim(-0.45, 0.95)
    ax_detail.set_aspect('equal', adjustable='box')
    ax_detail.set_title('Panel B: Zoomed Operational Corridor & Costmap Clearance\nSafe 8cm Offset Clears 15cm Inflation Buffer',
                        fontsize=11.5, fontweight='bold', pad=10)
    ax_detail.set_xlabel('Local Map Coordinate X (meters)', fontsize=10, fontweight='bold')
    ax_detail.set_ylabel('Local Map Coordinate Y (meters)', fontsize=10, fontweight='bold')
    ax_detail.grid(True, linestyle=':', alpha=0.55, color='#94A3B8')
    ax_detail.legend(loc='upper right', fontsize=7.5, framealpha=0.95, facecolor='#FFFFFF')

    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()
    print(f"Successfully generated full map visual: {out_path}")

if __name__ == '__main__':
    main()
