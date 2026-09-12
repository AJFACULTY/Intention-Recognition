#!/usr/bin/env python3
"""
Upgraded Figure Preview Generator: Visual & Reader-Friendly Enhancements
Generates enhanced previews for the 4 core figures:
1. preview_fig_spatial_zone.png (Camera HUD, silhouettes, optical reticles)
2. preview_fig_feature_pipeline.png (21-joint skeleton, curl arcs, MLP architecture)
3. preview_fig_brain_state_machine.png (UML state icons, priority safety preemption)
4. preview_fig_docker_deployment.png (Container architecture, DDS shared memory)
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

os.makedirs('write_up/preview_figures', exist_ok=True)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# ------------------------------------------------------------------------------
# HELPER: Draw Human Silhouette
# ------------------------------------------------------------------------------
def draw_human_silhouette(ax, center_x, base_y, width, height, color, alpha=0.85, is_operator=True):
    """Draws a stylized human silhouette (head, shoulders, torso, legs/arms)."""
    # Head
    head_radius = width * 0.18
    head_cy = base_y - height + head_radius * 1.5
    head = patches.Circle((center_x, head_cy), head_radius, fc=color, ec='none', alpha=alpha, zorder=5)
    ax.add_patch(head)

    # Neck & Torso
    torso_top = head_cy + head_radius * 0.8
    torso_bot = base_y - height * 0.40
    shoulder_w = width * 0.70
    waist_w = width * 0.45

    verts = [
        (center_x - shoulder_w / 2, torso_top),
        (center_x + shoulder_w / 2, torso_top),
        (center_x + waist_w / 2, torso_bot),
        (center_x - waist_w / 2, torso_bot),
        (center_x - shoulder_w / 2, torso_top)
    ]
    poly = patches.Polygon(verts, closed=True, fc=color, ec='none', alpha=alpha, zorder=5)
    ax.add_patch(poly)

    # Legs
    leg_w = width * 0.16
    leg_l = patches.Rectangle((center_x - waist_w / 2, torso_bot), leg_w, height * 0.38,
                              fc=color, ec='none', alpha=alpha, zorder=5)
    leg_r = patches.Rectangle((center_x + waist_w / 2 - leg_w, torso_bot), leg_w, height * 0.38,
                              fc=color, ec='none', alpha=alpha, zorder=5)
    ax.add_patch(leg_l)
    ax.add_patch(leg_r)

    # Arms
    if is_operator:
        # Left arm down
        arm_l = patches.Polygon([
            (center_x - shoulder_w / 2, torso_top),
            (center_x - shoulder_w / 2 - width * 0.14, torso_bot + height * 0.1),
            (center_x - shoulder_w / 2, torso_bot + height * 0.1),
            (center_x - shoulder_w / 2 + width * 0.1, torso_top)
        ], closed=True, fc=color, ec='none', alpha=alpha, zorder=5)
        ax.add_patch(arm_l)

        # Right arm raised in gesture signaling
        arm_r = patches.Polygon([
            (center_x + shoulder_w / 2, torso_top),
            (center_x + shoulder_w / 2 + width * 0.28, torso_top - height * 0.18),
            (center_x + shoulder_w / 2 + width * 0.20, torso_top - height * 0.24),
            (center_x + shoulder_w / 2 - width * 0.08, torso_top)
        ], closed=True, fc=color, ec='none', alpha=alpha, zorder=5)
        ax.add_patch(arm_r)
        # Hand indicator
        hand_c = patches.Circle((center_x + shoulder_w / 2 + width * 0.26, torso_top - height * 0.22),
                                width * 0.10, fc='#EAB308', ec='#CA8A04', lw=1.2, alpha=0.95, zorder=6)
        ax.add_patch(hand_c)
    else:
        # Bystander both arms down at sides
        arm_l = patches.Rectangle((center_x - shoulder_w / 2 - width * 0.12, torso_top),
                                  width * 0.12, height * 0.32, fc=color, ec='none', alpha=alpha, zorder=5)
        arm_r = patches.Rectangle((center_x + shoulder_w / 2, torso_top),
                                  width * 0.12, height * 0.32, fc=color, ec='none', alpha=alpha, zorder=5)
        ax.add_patch(arm_l)
        ax.add_patch(arm_r)


# ------------------------------------------------------------------------------
# 1. UPGRADED SPATIAL ZONE FIGURE (Camera Viewfinder HUD & Silhouettes)
# ------------------------------------------------------------------------------
def generate_preview_spatial_zone():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 640)
    ax.set_ylim(0, 480)
    ax.invert_yaxis()  # Image pixel coordinates (0,0 top-left)

    # Dark high-tech camera viewfinder background
    bg = patches.Rectangle((0, 0), 640, 480, fc='#0F172A', ec='#334155', lw=2)
    ax.add_patch(bg)

    # Top HUD Bar
    top_bar = patches.Rectangle((0, 0), 640, 36, fc='#1E293B', ec='none')
    ax.add_patch(top_bar)
    ax.text(18, 22, 'LIVE SENSOR STREAM: /camera/image_raw  |  DEV: USB 2.0 HD CAM  |  20.0 FPS',
            fontsize=9, color='#94A3B8', family='monospace', va='center')
    ax.text(622, 22, '● REC [640×480 RGB]', fontsize=9, color='#EF4444', fontweight='bold',
            family='monospace', ha='right', va='center')

    # Viewfinder Corner Brackets (4 corners)
    bracket_len = 28
    b_color = '#64748B'
    lw_b = 2.5
    # Top-Left
    ax.plot([14, 14 + bracket_len], [46, 46], color=b_color, lw=lw_b)
    ax.plot([14, 14], [46, 46 + bracket_len], color=b_color, lw=lw_b)
    # Top-Right
    ax.plot([626 - bracket_len, 626], [46, 46], color=b_color, lw=lw_b)
    ax.plot([626, 626], [46, 46 + bracket_len], color=b_color, lw=lw_b)
    # Bottom-Left
    ax.plot([14, 14 + bracket_len], [466, 466], color=b_color, lw=lw_b)
    ax.plot([14, 14], [466 - bracket_len, 466], color=b_color, lw=lw_b)
    # Bottom-Right
    ax.plot([626 - bracket_len, 626], [466, 466], color=b_color, lw=lw_b)
    ax.plot([626, 626], [466 - bracket_len, 466], color=b_color, lw=lw_b)

    # Frame Optical Center Crosshairs (Cx=320, Cy=240)
    ax.axvline(320, color='#38BDF8', lw=0.8, linestyle=':', alpha=0.5)
    ax.axhline(240, color='#38BDF8', lw=0.8, linestyle=':', alpha=0.5)
    center_circle = patches.Circle((320, 240), 12, fc='none', ec='#38BDF8', lw=1.5, linestyle='--', alpha=0.7)
    ax.add_patch(center_circle)
    ax.plot(320, 240, marker='+', markersize=10, color='#38BDF8', mew=1.8)
    ax.text(328, 232, 'Optical Center (Cx=320, Cy=240)', fontsize=7.5, color='#38BDF8',
            family='monospace', fontweight='bold')

    # Central Acceptance Zone (45% W × 65% H) -> 288 × 312 px
    zone_x, zone_y, zone_w, zone_h = 176, 84, 288, 312
    zone_rect = patches.Rectangle((zone_x, zone_y), zone_w, zone_h,
                                  fc='#0284C7', ec='#38BDF8', lw=2.2, linestyle='--', alpha=0.15)
    ax.add_patch(zone_rect)
    # Zone Title Ribbon
    ax.text(320, zone_y + 16, 'ACTIVE ACCEPTANCE ZONE (45% W × 65% H)',
            fontsize=9.5, fontweight='bold', ha='center', color='#38BDF8', family='sans-serif')
    ax.text(320, zone_y + 30, '[X: 176px to 464px | Y: 84px to 396px]',
            fontsize=8, ha='center', color='#7DD3FC', family='monospace')

    # 1. Primary Operator (Inside Zone)
    op_x, op_y, op_w, op_h = 248, 138, 134, 232
    # Operator Silhouette
    draw_human_silhouette(ax, center_x=315, base_y=op_y + op_h, width=op_w * 0.82, height=op_h * 0.90,
                           color='#22C55E', alpha=0.35, is_operator=True)

    # Operator Bounding Box
    op_box = patches.Rectangle((op_x, op_y), op_w, op_h, fc='none', ec='#22C55E', lw=2.5)
    ax.add_patch(op_box)
    # Operator Header Pill
    ax.text(op_x + op_w / 2, op_y - 12, 'PRIMARY OPERATOR [ID: 1]  CONF: 0.94\nSTATUS: ACCEPTED (INSIDE ZONE)',
            fontsize=8, fontweight='bold', ha='center', va='bottom', color='#22C55E',
            bbox=dict(boxstyle='round,pad=0.3', fc='#064E3B', ec='#22C55E', lw=1.2))

    # Operator Centroid Bullseye
    centroid_x, centroid_y = 315, 248
    ax.plot(centroid_x, centroid_y, marker='o', markersize=8, color='#4ADE80', zorder=7)
    ax.plot(centroid_x, centroid_y, marker='+', markersize=14, color='#15803D', mew=2, zorder=8)

    # Steering Tracking Vector (ex = Cx - Bx = 320 - 315 = +5 px)
    ax.annotate('', xy=(320, 248), xytext=(315, 248),
                arrowprops=dict(arrowstyle='->', lw=2.2, color='#FACC15'), zorder=9)
    ax.text(317.5, 268, 'Heading Error ex = -5 px\nv_ω = -1.5 × ex = +0.023 rad/s',
            fontsize=8, color='#FEF08A', ha='center', fontweight='bold',
            family='monospace', bbox=dict(boxstyle='round,pad=0.25', fc='#78350F', ec='#FACC15', lw=1))

    # 2. Bystander (Outside Zone - Left)
    by_x, by_y, by_w, by_h = 24, 155, 108, 205
    # Bystander Silhouette
    draw_human_silhouette(ax, center_x=78, base_y=by_y + by_h, width=by_w * 0.85, height=by_h * 0.90,
                           color='#EF4444', alpha=0.30, is_operator=False)

    # Bystander Bounding Box (Red Dashed)
    by_box = patches.Rectangle((by_x, by_y), by_w, by_h, fc='none', ec='#EF4444', lw=2.0, linestyle=':')
    ax.add_patch(by_box)
    # Bystander Centroid 'X'
    ax.plot(78, 257, marker='x', markersize=12, color='#EF4444', mew=2.5, zorder=7)
    # Bystander Header Pill
    ax.text(by_x + by_w / 2, by_y - 12, 'BYSTANDER [ID: 2]\nSTATUS: REJECTED (OUTSIDE ZONE)',
            fontsize=7.5, fontweight='bold', ha='center', va='bottom', color='#FCA5A5',
            bbox=dict(boxstyle='round,pad=0.3', fc='#7F1D1D', ec='#EF4444', lw=1))

    # Bottom Safety & Pipeline Info Footer
    footer = patches.Rectangle((0, 444), 640, 36, fc='#1E293B', ec='none')
    ax.add_patch(footer)
    ax.text(320, 462,
            'SPATIAL FILTER RULE: Only candidate centroid within central 45%×65% initiates landmark extraction.\n'
            'Prevents false actuation from incidental bystanders. Downstream hand tracker binds strictly to ID: 1.',
            fontsize=8, color='#E2E8F0', ha='center', va='center')

    plt.tight_layout()
    plt.savefig('write_up/preview_figures/preview_fig_spatial_zone.png', bbox_inches='tight')
    plt.close()
    print('✓ Generated preview: preview_fig_spatial_zone.png')


# ------------------------------------------------------------------------------
# 2. UPGRADED FEATURE PIPELINE (21-Joint Skeleton & MLP Architecture)
# ------------------------------------------------------------------------------
def generate_preview_feature_pipeline():
    fig, ax = plt.subplots(figsize=(14, 7.8), dpi=300)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Main Title
    ax.text(70, 97, 'MediaPipe Anatomical Hand Skeleton, Geometric Feature Extraction & MLP Classifier',
            fontsize=13.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # =========================================================================
    # STAGE 1: 21-Joint Skeletal Model (Real Vector Hand Diagram!)
    # =========================================================================
    box1 = patches.FancyBboxPatch((3, 6), 33, 86, boxstyle='round,pad=0.8',
                                 fc='#F0F9FF', ec='#0284C7', lw=1.8)
    ax.add_patch(box1)
    ax.text(19.5, 89.5, 'Stage 1: Skeletal Tracking', fontsize=10.5, fontweight='bold',
            ha='center', color='#0369A1')
    ax.text(19.5, 86.5, 'MediaPipe HandLandmarker (21 3D Pts)', fontsize=8,
            ha='center', color='#0284C7', style='italic')

    # 21 Anatomical Joint Coordinates (carefully mapped to hand shape in box 1)
    # Box 1 center is approx x=19.5, y range 12 to 82
    pts = {
        0: (19.5, 16.0),   # Wrist Origin
        # Thumb
        1: (15.5, 23.0), 2: (13.0, 31.0), 3: (11.5, 39.0), 4: (10.5, 47.0),
        # Index
        5: (16.2, 38.0), 6: (15.5, 49.0), 7: (15.0, 59.0), 8: (14.5, 68.0),
        # Middle
        9: (19.5, 39.0), 10: (19.5, 51.0), 11: (19.5, 62.0), 12: (19.5, 72.0),
        # Ring
        13: (22.8, 37.5), 14: (23.2, 48.0), 15: (23.5, 57.5), 16: (23.8, 66.5),
        # Pinky
        17: (25.8, 35.0), 18: (26.8, 44.0), 19: (27.5, 52.0), 20: (28.2, 60.0)
    }

    # Bones (Segments)
    bones = [
        # Palm connections
        (0, 1), (1, 2), (2, 5), (5, 9), (9, 13), (13, 17), (17, 0), (0, 5),
        # Thumb
        (2, 3), (3, 4),
        # Index
        (5, 6), (6, 7), (7, 8),
        # Middle
        (9, 10), (10, 11), (11, 12),
        # Ring
        (13, 14), (14, 15), (15, 16),
        # Pinky
        (17, 18), (18, 19), (19, 20)
    ]

    for p_start, p_end in bones:
        x0, y0 = pts[p_start]
        x1, y1 = pts[p_end]
        ax.plot([x0, x1], [y0, y1], color='#64748B', lw=1.8, zorder=3)

    # Highlight palm polygon (P0, P5, P9, P13, P17)
    palm_poly = patches.Polygon([pts[0], pts[5], pts[9], pts[13], pts[17]],
                                closed=True, fc='#BAE6FD', ec='none', alpha=0.45, zorder=2)
    ax.add_patch(palm_poly)

    # Draw Landmarks (Nodes)
    for idx, (px, py) in pts.items():
        if idx == 0:
            c = '#EF4444' # Wrist
            r = 1.2
        elif idx in [4, 8, 12, 16, 20]:
            c = '#F59E0B' # Fingertips
            r = 1.0
        elif idx in [5, 9, 13, 17]:
            c = '#0284C7' # Base MCP
            r = 0.9
        else:
            c = '#10B981' # Intermediate joints
            r = 0.8
        node = patches.Circle((px, py), r, fc=c, ec='#0F172A', lw=1.0, zorder=5)
        ax.add_patch(node)

    # Key Labels on Skeleton
    ax.text(pts[0][0], pts[0][1] - 3.2, 'P0 (Wrist Origin)', fontsize=7.5,
            fontweight='bold', ha='center', color='#DC2626')
    ax.text(pts[4][0] - 1.5, pts[4][1], 'P4', fontsize=7, fontweight='bold', color='#D97706')
    ax.text(pts[8][0], pts[8][1] + 2.2, 'P8 (Index Tip)', fontsize=7.5, fontweight='bold',
            ha='center', color='#D97706')
    ax.text(pts[12][0], pts[12][1] + 2.2, 'P12', fontsize=7, fontweight='bold', ha='center', color='#D97706')
    ax.text(pts[20][0] + 1.8, pts[20][1], 'P20', fontsize=7, fontweight='bold', color='#D97706')

    # Baseline Palm Width Indicator (W_palm between P5 and P17)
    ax.annotate('', xy=pts[5], xytext=pts[17],
                arrowprops=dict(arrowstyle='<->', lw=1.6, color='#7C3AED', linestyle='--'))
    ax.text(21.0, 34.0, 'W_palm', fontsize=7.5, color='#7C3AED', fontweight='bold', ha='center')

    # Finger Curl Angle Arc Indicator on Index finger (P5-P6-P8)
    arc = patches.Arc((pts[6][0], pts[6][1]), 6, 6, angle=0, theta1=60, theta2=115,
                      color='#DC2626', lw=1.6)
    ax.add_patch(arc)
    ax.text(pts[6][0] - 3.0, pts[6][1] + 1.5, 'θ_curl', fontsize=7, color='#DC2626', fontweight='bold')

    # =========================================================================
    # STAGE 2: Mathematical Feature Extraction (Formulas & Glyphs)
    # =========================================================================
    box2 = patches.FancyBboxPatch((39, 6), 31, 86, boxstyle='round,pad=0.8',
                                 fc='#FFFBEB', ec='#D97706', lw=1.8)
    ax.add_patch(box2)
    ax.text(54.5, 89.5, 'Stage 2: Feature Engineering', fontsize=10.5, fontweight='bold',
            ha='center', color='#B45309')
    ax.text(54.5, 86.5, 'Scale- & Distance-Invariant Transformation', fontsize=8,
            ha='center', color='#D97706', style='italic')

    f_text = (
        "1. Finger Curl Angles (5 Features):\n"
        "   θ_i = ∠(MCP - PIP, PIP - TIP)\n"
        "   Measures joint flexion [0° to 180°]\n\n"
        "2. Inter-Finger Spreads (3 Features):\n"
        "   α_spread = ∠(Tip_i - Wrist, Tip_j - Wrist)\n"
        "   (Thumb-Index, Index-Mid, Mid-Ring)\n\n"
        "3. Normalized Distances (5 Features):\n"
        "   d_norm = ||P_tip - P_wrist|| / W_palm\n"
        "   Normalized by Palm Width (W_palm)\n\n"
        "4. Gravity & Palm Orientation (3 Features):\n"
        "   Elevation angle & normal vector\n\n"
        "5. Key Joint Separations (3 Features):\n"
        "   Thumb-to-Index tip clearance,\n"
        "   Thumb height ratio"
    )
    ax.text(41.5, 83.5, f_text, fontsize=7.8, va='top', color='#78350F', family='sans-serif', linespacing=1.35)

    # =========================================================================
    # STAGE 3: 19-Dimensional Feature Vector Strip
    # =========================================================================
    box3 = patches.FancyBboxPatch((73, 6), 28, 86, boxstyle='round,pad=0.8',
                                 fc='#F0FDF4', ec='#16A34A', lw=1.8)
    ax.add_patch(box3)
    ax.text(87, 89.5, 'Stage 3: Vector Encoding', fontsize=10.5, fontweight='bold',
            ha='center', color='#15803D')
    ax.text(87, 86.5, 'Structured 19-D Feature Array', fontsize=8,
            ha='center', color='#16A34A', style='italic')

    # Visual Feature Vector Blocks
    groups = [
        ("f1 - f5 : Curl Angles", "#DC2626", "#FEE2E2"),
        ("f6 - f8 : Spread Angles", "#2563EB", "#DBEAFE"),
        ("f9 - f13: Norm Distances", "#7C3AED", "#EDE9FE"),
        ("f14 - f16: Palm Angles", "#D97706", "#FEF3C7"),
        ("f17 - f19: Key Separations", "#059669", "#D1FAE5")
    ]
    cur_y = 82
    for label, stroke_c, fill_c in groups:
        p_box = patches.FancyBboxPatch((75.5, cur_y - 9.5), 23, 9.5, boxstyle='round,pad=0.3',
                                      fc=fill_c, ec=stroke_c, lw=1.2)
        ax.add_patch(p_box)
        ax.text(87, cur_y - 4.8, label, fontsize=8.2, fontweight='bold', ha='center', va='center', color=stroke_c)
        cur_y -= 12.5

    ax.text(87, 18,
            "Properties:\n"
            "• Dimension: 19 floats\n"
            "• Scale-Invariant: ||x|| / W_palm\n"
            "• Robust from 0.5 m to 3.0 m",
            fontsize=7.8, ha='center', va='top', color='#166534', family='sans-serif', linespacing=1.3)

    # =========================================================================
    # STAGE 4: Multi-Layer Perceptron (MLP) Classifier & Tokens
    # =========================================================================
    box4 = patches.FancyBboxPatch((104, 6), 33, 86, boxstyle='round,pad=0.8',
                                 fc='#FAF5FF', ec='#9333EA', lw=1.8)
    ax.add_patch(box4)
    ax.text(120.5, 89.5, 'Stage 4: MLP Neural Classifier', fontsize=10.5, fontweight='bold',
            ha='center', color='#7E22CE')
    ax.text(120.5, 86.5, 'ONNX Runtime Edge Inference (10 Hz)', fontsize=8,
            ha='center', color='#9333EA', style='italic')

    # Miniature Neural Network Diagram
    layers = [
        ("Input\n19", 108.5, 4),
        ("Hidden1\n64", 114.5, 5),
        ("Hidden2\n32", 120.5, 4),
        ("Output\n6", 126.5, 3)
    ]
    for name, lx, n_nodes in layers:
        ax.text(lx, 79, name, fontsize=7, fontweight='bold', ha='center', color='#6B21A8')
        ys = np.linspace(62, 74, n_nodes)
        for y in ys:
            node = patches.Circle((lx, y), 1.0, fc='#E9D5FF', ec='#9333EA', lw=1.0)
            ax.add_patch(node)

    # Connect nodes schematically
    for i in range(len(layers) - 1):
        x1_l = layers[i][1]
        x2_l = layers[i+1][1]
        ys1 = np.linspace(62, 74, layers[i][2])
        ys2 = np.linspace(62, 74, layers[i+1][2])
        for y1_n in ys1:
            for y2_n in ys2:
                ax.plot([x1_l + 1.0, x2_l - 1.0], [y1_n, y2_n], color='#D8B4FE', lw=0.4, alpha=0.6)

    # Output Tokens Badges
    tokens = [
        ("STOP", "#EF4444", "#FEE2E2"),
        ("GO", "#22C55E", "#DCFCE7"),
        ("LEFT", "#3B82F6", "#DBEAFE"),
        ("RIGHT", "#3B82F6", "#DBEAFE"),
        ("BACK", "#F59E0B", "#FEF3C7"),
        ("FOLLOW", "#8B5CF6", "#EDE9FE")
    ]
    ax.text(120.5, 56.5, 'Discrete Output Tokens (/cognition/gesture):',
            fontsize=7.5, fontweight='bold', ha='center', color='#4C1D95')
    tok_x = [107.5, 120.5, 133.5]
    tok_y = [49, 41]
    idx = 0
    for r in range(2):
        for c in range(3):
            t_name, stroke_c, fill_c = tokens[idx]
            t_box = patches.FancyBboxPatch((tok_x[c] - 5.5, tok_y[r] - 3.2), 11, 6.4, boxstyle='round,pad=0.2',
                                          fc=fill_c, ec=stroke_c, lw=1.2)
            ax.add_patch(t_box)
            ax.text(tok_x[c], tok_y[r], t_name, fontsize=7.2, fontweight='bold',
                    ha='center', va='center', color=stroke_c)
            idx += 1

    # Metrics Pill at Bottom of Stage 4
    m_box = patches.FancyBboxPatch((106.5, 11), 28, 23, boxstyle='round,pad=0.3',
                                  fc='#FFFFFF', ec='#9333EA', lw=1.2)
    ax.add_patch(m_box)
    ax.text(120.5, 29, "EMPIRICAL PERFORMANCE", fontsize=7.5, fontweight='bold', ha='center', color='#7E22CE')
    metrics_str = (
        "• Accuracy: 99.38% (Test Set)\n"
        "• Inference Latency: 1.2 ms\n"
        "• Training Set: 6,000 frames\n"
        "• Execution: ONNX on Pi 5 CPU\n"
        "• Frame Rate: 10 Hz Fixed Rate"
    )
    ax.text(108.5, 26, metrics_str, fontsize=7.2, va='top', color='#3B0764', linespacing=1.3)

    # Connector Arrows between stages
    ax.annotate('', xy=(39, 49), xytext=(36, 49), arrowprops=dict(arrowstyle='->', lw=2.2, color='#0284C7'))
    ax.annotate('', xy=(73, 49), xytext=(70, 49), arrowprops=dict(arrowstyle='->', lw=2.2, color='#D97706'))
    ax.annotate('', xy=(104, 49), xytext=(101, 49), arrowprops=dict(arrowstyle='->', lw=2.2, color='#16A34A'))

    plt.tight_layout()
    plt.savefig('write_up/preview_figures/preview_fig_feature_pipeline.png', bbox_inches='tight')
    plt.close()
    print('✓ Generated preview: preview_fig_feature_pipeline.png')


# ------------------------------------------------------------------------------
# 3. UPGRADED BRAIN STATE MACHINE (UML Icons & Safety Preemption Shield)
# ------------------------------------------------------------------------------
def generate_preview_state_machine():
    fig, ax = plt.subplots(figsize=(13.5, 9.0), dpi=300)
    ax.set_xlim(0, 135)
    ax.set_ylim(0, 105)
    ax.axis('off')

    # Title
    ax.text(67.5, 101, 'UML State Machine: Supervisory Decision Engine & Asynchronous Safety Preemption',
            fontsize=13.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # Initial State Marker
    ax.plot(6, 73, marker='o', markersize=14, color='#1E293B')
    ax.annotate('', xy=(13, 73), xytext=(7, 73), arrowprops=dict(arrowstyle='->', lw=2.0, color='#1E293B'))

    def draw_state(x, y, w, h, bg_c, border_c, title, body, badge_c='#334155'):
        b = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=1.0', fc=bg_c, ec=border_c, lw=2.0)
        ax.add_patch(b)
        div_y = y + h - 7.5
        ax.plot([x, x + w], [div_y, div_y], color=border_c, lw=1.2)
        ax.text(x + w / 2, y + h - 3.8, title, fontsize=10, fontweight='bold',
                ha='center', va='center', color=badge_c)
        ax.text(x + 1.5, div_y - 2.0, body, fontsize=7.8, ha='left', va='top',
                color='#1E293B', linespacing=1.35)

    # State 1: IDLE
    draw_state(13, 58, 28, 30, '#F8FAFC', '#64748B',
               '1. IDLE [SEARCH]',
               '• cmd_vel = (0.0, 0.0)\n• Video stream: 20 FPS\n• YOLOv8n person detector active\n• Spatial zone gating engaged\n• Reject bystanders outside zone',
               badge_c='#334155')

    # State 2: WAITING_CONFIRM
    draw_state(50, 58, 30, 30, '#FEF3C7', '#D97706',
               '2. WAITING_CONFIRM',
               '• Operator in spatial zone\n• Engage MediaPipe landmarks\n• 5-Frame rolling consensus\n• Confidence threshold >= 0.65\n• Prevent spurious single-frame triggers',
               badge_c='#B45309')

    # State 3: LOCKED & EXECUTING
    draw_state(90, 58, 38, 30, '#DCFCE7', '#16A34A',
               '3. LOCKED & EXECUTING',
               '• Intent locked for 3.0s window\n• Publish motion commands (/cmd_vel):\n   STOP, GO, LEFT, RIGHT, BACK\n• Closed-loop encoder speed control\n• Ignore hand changes during lock',
               badge_c='#15803D')

    # State 4: FOLLOW MODE
    draw_state(74, 12, 54, 30, '#DBEAFE', '#2563EB',
               '4. FOLLOW MODE (Visual Servoing)',
               '• Continuous tracking loop (10 Hz):\n• Heading error: ex = (Cx - Bx_operator)\n• Steering: v_ω = -1.5 × ex (Proportional Gain)\n• Forward cruise: vx = 0.20 m/s\n• Proximity cutoff: If PersonWidth > 0.40 -> Halt',
               badge_c='#1D4ED8')

    # State 5: EMERGENCY HALT (With Hazard Red Shield)
    draw_state(13, 12, 36, 30, '#FEE2E2', '#DC2626',
               '5. EMERGENCY HALT [OVERRIDE]',
               '• FORCED ZERO VELOCITY (cmd_vel = 0)\n• Instant asynchronous preemption\n• Clear rolling consensus buffers\n• Requires manual operator reset\n• Highest priority supervisory state',
               badge_c='#991B1B')

    # Normal Transitions
    # 1 -> 2
    ax.annotate('', xy=(50, 73), xytext=(41, 73), arrowprops=dict(arrowstyle='->', lw=2.0, color='#334155'))
    ax.text(45.5, 75.5, 'Operator\nin Zone', fontsize=7.5, ha='center', va='bottom',
            fontweight='bold', color='#1E293B', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E1', lw=0.8))

    # 2 -> 3
    ax.annotate('', xy=(90, 73), xytext=(80, 73), arrowprops=dict(arrowstyle='->', lw=2.0, color='#16A34A'))
    ax.text(85, 75.5, 'Consensus\n(3/5 Confirmed)', fontsize=7.5, ha='center', va='bottom',
            fontweight='bold', color='#15803D', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#86EFAC', lw=0.8))

    # 3 -> IDLE (Return via clean upper route)
    ax.plot([109, 109, 27, 27], [88, 96, 96, 88], color='#64748B', lw=1.8)
    ax.annotate('', xy=(27, 88), xytext=(27, 89), arrowprops=dict(arrowstyle='->', lw=1.8, color='#64748B'))
    ax.text(68, 96, 'Lock Expired (t > 3.0s) / Motion Completed', fontsize=8, ha='center', va='center',
            fontweight='bold', color='#334155', bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#64748B', lw=1))

    # 3 -> 4 (Follow mode transition)
    ax.annotate('', xy=(100, 42), xytext=(100, 58), arrowprops=dict(arrowstyle='->', lw=2.0, color='#2563EB'))
    ax.text(102, 50, 'Gesture == FOLLOW', fontsize=8, ha='left', va='center',
            fontweight='bold', color='#1D4ED8', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#93C5FD', lw=0.8))

    # 4 -> IDLE (Return route)
    ax.plot([74, 59, 59, 36, 36], [32, 32, 50, 50, 58], color='#64748B', lw=1.6)
    ax.annotate('', xy=(36, 58), xytext=(36, 57), arrowprops=dict(arrowstyle='->', lw=1.6, color='#64748B'))
    ax.text(47.5, 50, 'Operator Lost / STOP Gesture', fontsize=7.2, ha='center', va='center',
            fontweight='bold', color='#475569', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#CBD5E1', lw=0.8))

    # =========================================================================
    # ASYNCHRONOUS SAFETY PREEMPTION (Red Warning Shield & Lightning)
    # =========================================================================
    # Lightning Preemption Route from States to EMERGENCY HALT
    ax.plot([65, 65, 31], [58, 45, 45], color='#DC2626', lw=2.2, linestyle='--')
    ax.annotate('', xy=(31, 42), xytext=(31, 45), arrowprops=dict(arrowstyle='->', lw=2.2, color='#DC2626'))

    # Warning Shield Badge
    shield_box = patches.FancyBboxPatch((35, 42), 33, 6.5, boxstyle='round,pad=0.3',
                                       fc='#FEF2F2', ec='#DC2626', lw=1.5)
    ax.add_patch(shield_box)
    ax.text(51.5, 45.2, '⚠ ASYNCHRONOUS SAFETY OVERRIDE\nLiDAR Obstacle < 0.36m OR Joystick Kill',
            fontsize=7.2, ha='center', va='center', color='#991B1B', fontweight='bold')

    # Recovery from EMERGENCY HALT to IDLE
    ax.annotate('', xy=(20, 58), xytext=(20, 42), arrowprops=dict(arrowstyle='->', lw=1.8, color='#64748B'))
    ax.text(19, 50, 'Clear Obstacle\n& System Reset', fontsize=7, ha='right', va='center',
            fontweight='bold', color='#475569')

    plt.tight_layout()
    plt.savefig('write_up/preview_figures/preview_fig_brain_state_machine.png', bbox_inches='tight')
    plt.close()
    print('✓ Generated preview: preview_fig_brain_state_machine.png')


# ------------------------------------------------------------------------------
# 4. UPGRADED DOCKER DEPLOYMENT (Clean Container Topology & Bus Architecture)
# ------------------------------------------------------------------------------
def generate_preview_docker_deployment():
    fig, ax = plt.subplots(figsize=(13.5, 8.5), dpi=300)
    ax.set_xlim(0, 135)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(67.5, 96.5, 'Containerized Multi-Node Deployment Architecture (Docker Host Mode & DDS Loopback)',
            fontsize=13.5, fontweight='bold', ha='center', va='top', color='#0F172A')

    # Raspberry Pi 5 Host Machine Outer Box
    host_box = patches.FancyBboxPatch((4, 6), 92, 86, boxstyle='round,pad=1.2',
                                      fc='#F8FAFC', ec='#475569', lw=2.0, linestyle='--')
    ax.add_patch(host_box)
    # Host Header
    ax.text(18, 89, 'Primary Embedded Computer: Raspberry Pi 5 (8GB RAM)',
            fontsize=10.5, fontweight='bold', ha='left', va='center', color='#1E293B',
            bbox=dict(boxstyle='round,pad=0.35', fc='#E2E8F0', ec='#94A3B8', lw=1))
    ax.text(93, 89, 'Linux Host OS | Containers: Ubuntu 20.04 (ROS 2 Humble) | --net=host',
            fontsize=8.5, ha='right', va='center', color='#64748B', style='italic')

    def draw_container(x, y, w, h, bg_c, border_c, title, body, badge_c='#1E293B'):
        b = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.8', fc=bg_c, ec=border_c, lw=1.8)
        ax.add_patch(b)
        div_y = y + h - 8.5
        ax.plot([x, x + w], [div_y, div_y], color=border_c, lw=1.2)
        ax.text(x + w / 2, y + h - 4.2, title, fontsize=9.5, fontweight='bold',
                ha='center', va='center', color=badge_c)
        ax.text(x + 1.5, div_y - 2.0, body, fontsize=7.8, ha='left', va='top',
                color='#1E293B', linespacing=1.35)

    # 1. Container: yahboom_base
    draw_container(7, 48, 40, 36, '#EFF6FF', '#3B82F6',
                   'Container: yahboom_base\n[Hardware Driver Services]',
                   '• MS200 LiDAR Node (/scan @ 12.5 Hz)\n• Serial Binding (/dev/myserial)\n• 6-Axis IMU Publisher (/imu @ 50 Hz)\n• Differential Odometry Transformer\n• Base TF Broadcaster (base_footprint -> odom)',
                   badge_c='#1D4ED8')

    # 2. Container: micro_ros_agent
    draw_container(7, 10, 40, 34, '#FEF3C7', '#D97706',
                   'Container: micro_ros_agent\n[Deterministic Hardware Bridge]',
                   '• micro-ROS Agent Daemon (Client Bridge)\n• Serial UART 921,600 Baud Link\n• Subscribes: /cmd_vel (Twist Commands)\n• Publishes: /odom_raw (Quadrature Encoders)\n• Publishes: /battery_state (Voltage Telemetry)',
                   badge_c='#B45309')

    # 3. Container: yahboom_gesture
    draw_container(54, 10, 39, 74, '#DCFCE7', '#16A34A',
                   'Container: yahboom_gesture\n[Edge Vision & Decision Cognition]',
                   '1. camera_pub (20 FPS):\n   • Video capture: /dev/video0\n   • Publishes: /camera/image_raw/compressed\n\n2. person_detection_node (YOLOv8n):\n   • Spatial zone gating (45% W × 65% H)\n   • Isolates closest operator in frame\n   • Publishes: /cognition/detection\n\n3. gesture_node (10 Hz):\n   • MediaPipe 21 Hand Landmarks\n   • 19 Geometric Features extraction\n   • MLP Classifier (1.2 ms inference)\n   • Publishes: /cognition/gesture\n\n4. brain_node (Supervisory Logic):\n   • 3/5 Majority filter & 3s lock\n   • Visual servoing steering (Kp = 1.5)\n   • Safety preemption (< 0.36m obstacle)\n   • Publishes: /cmd_vel',
                   badge_c='#15803D')

    # DDS Shared Memory Bus in Pi 5
    ax.annotate('', xy=(54, 62), xytext=(47, 62), arrowprops=dict(arrowstyle='<->', lw=2.2, color='#2563EB'))
    ax.text(50.5, 65, 'DDS Shared Memory Loopback\n/scan  |  /camera/image_raw',
             fontsize=7.2, ha='center', va='bottom', color='#1D4ED8', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#93C5FD', lw=0.8))

    ax.annotate('', xy=(54, 25), xytext=(47, 25), arrowprops=dict(arrowstyle='<->', lw=2.2, color='#D97706'))
    ax.text(50.5, 28, 'micro-ROS Inter-Process Bridge\n/cmd_vel  |  /odom_raw',
             fontsize=7.2, ha='center', va='bottom', color='#B45309', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#FDE68A', lw=0.8))

    # Engineering Workstation Box (Host Dev Machine)
    draw_container(101, 10, 30, 82, '#F3E8FF', '#9333EA',
                   'Engineering Host Workstation\n(x86_64 Development PC)',
                   '• AMD Ryzen 5, 8GB DDR4 RAM\n• Ubuntu 24.04 LTS / ROS 2 Jazzy\n\n• RViz2 Real-Time Visualizer:\n  - /scan (LiDAR 2D point cloud)\n  - /map (SLAM Toolbox grid)\n  - /tf coordinate tree\n  - Camera video live window\n\n• Safety Intervention Tools:\n  - Hardware joystick override (/joy)\n  - Teleoperation emergency stop\n\n• Simulation Verification:\n  - Gazebo Harmonic digital twin\n  - Sim-to-real parameter tuning\n\n• Offline Deep Learning Pipeline:\n  - PyTorch MLP training\n  - ONNX edge model export',
                   badge_c='#7E22CE')

    # Wi-Fi DDS Bridge
    ax.annotate('', xy=(101, 52), xytext=(96, 52),
                arrowprops=dict(arrowstyle='<->', lw=2.2, color='#7C3AED', linestyle=':'))
    ax.text(98.5, 55, 'Wi-Fi 5 GHz DDS Link\nROS_DOMAIN_ID=0',
            fontsize=7.5, ha='center', va='bottom', color='#6D28D9', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#C4B5FD', lw=0.8))

    plt.tight_layout()
    plt.savefig('write_up/preview_figures/preview_fig_docker_deployment.png', bbox_inches='tight')
    plt.close()
    print('✓ Generated preview: preview_fig_docker_deployment.png')


if __name__ == '__main__':
    generate_preview_spatial_zone()
    generate_preview_feature_pipeline()
    generate_preview_state_machine()
    generate_preview_docker_deployment()
    print('\nAll upgraded preview figures generated successfully.')
