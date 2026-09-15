#!/usr/bin/env python3
"""
generate_methodology_figure.py
Generates a publication-grade 6-Phase Engineering Research & Implementation
Methodology Diagram for the GCTU Computer Engineering Undergraduate Final Defense.
Saves to: write_up/figures/fig_accepted_methodology.png (high resolution 300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_methodology_diagram(output_path="write_up/figures/fig_accepted_methodology.png"):
    fig, ax = plt.subplots(figsize=(15.5, 7.8), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Color Palette: Clean Engineering Corporate Modern
    c_phase_head = "#0F2B48"     # Deep Navy
    c_phase_bg   = "#F0F4F8"     # Crisp Light Slate
    c_card_border= "#1E3A8A"     # Royal Blue
    c_accent_sub = "#0284C7"     # Vibrant Blue
    c_bullet     = "#1E293B"     # Slate Charcoal
    c_arrow      = "#0284C7"     # Connector Blue

    # 6 Phases: 2 Rows x 3 Columns Layout
    phases = [
        {
            "phase": "PHASE 1",
            "title": "Mechatronics & Hardware Integration",
            "items": [
                "• Yahboom 4WD chassis & DC motor encoders",
                "• Raspberry Pi 5 (8GB) edge compute node",
                "• ESP32-S3 Micro-ROS real-time co-processor",
                "• MS200 2D LiDAR (360°) & 2-DOF camera gimbal",
                "• Decoupled dual-bus power regulation (7.4V Li-ion)"
            ],
            "col": 0, "row": 0
        },
        {
            "phase": "PHASE 2",
            "title": "Data Acquisition & Calibration",
            "items": [
                "• Direct onboard camera collection (640x480)",
                "• 6,000 balanced samples (1,000 / class)",
                "• 6 gestures: STOP, GO, FOLLOW, LEFT, RIGHT, BACK",
                "• Varying operational distances (1.0m to 2.5m)",
                "• Sensor calibration under real indoor lighting"
            ],
            "col": 1, "row": 0
        },
        {
            "phase": "PHASE 3",
            "title": "Feature Engineering & Edge AI",
            "items": [
                "• 21 MediaPipe 3D anatomical hand landmarks",
                "• 19-D scale-invariant geometric feature vector",
                "• Lightweight MLP classifier (PyTorch -> ONNX, 46KB)",
                "• LSTM sequential motion predictor (10-frame window)",
                "• Sub-2ms neural inference on Raspberry Pi 5 CPU"
            ],
            "col": 2, "row": 0
        },
        {
            "phase": "PHASE 4",
            "title": "Supervisory State Machine & Control",
            "items": [
                "• Centralized ROS 2 Humble node graph (Domain 20)",
                "• brain_node 5-frame consensus & visual servoing",
                "• Multi-tier priority arbitration via twist_mux",
                "• Dedicated 921,600 baud UART micro-ROS bridge",
                "• Acoustic safety chime notification system"
            ],
            "col": 0, "row": 1
        },
        {
            "phase": "PHASE 5",
            "title": "Metric SLAM & Nav2 Navigation",
            "items": [
                "• slam_toolbox 2D occupancy grid mapping (5cm)",
                "• AMCL probabilistic particle filter localization",
                "• Nav2 global/local costmaps with 0.25m inflation",
                "• Extended Kalman Filter (EKF) sensor fusion",
                "• Restamped odometry/IMU neutralizing yaw drift"
            ],
            "col": 1, "row": 1
        },
        {
            "phase": "PHASE 6",
            "title": "Empirical Benchmarking & Validation",
            "items": [
                "• End-to-end component latency budget (74.2 ms)",
                "• 180 physical closed-loop gesture locomotion trials",
                "• 99.38% test accuracy / 96.67% physical trial accuracy",
                "• ISO 15066 safety stopping verification (<0.36m)",
                "• Synchronized telemetry rosbag recording & analysis"
            ],
            "col": 2, "row": 1
        }
    ]

    card_w = 4.8
    card_h = 3.3
    col_x = [0.4, 5.6, 10.8]
    row_y = [5.0, 0.8]  # row 0 top, row 1 bottom

    for p in phases:
        x = col_x[p["col"]]
        y = row_y[p["row"]]

        # Card Background with Rounded Box
        rect = patches.FancyBboxPatch(
            (x, y), card_w, card_h,
            boxstyle="round,pad=0.08,rounding_size=0.18",
            linewidth=1.6, edgecolor=c_card_border, facecolor=c_phase_bg,
            zorder=2
        )
        ax.add_patch(rect)

        # Header Badge
        header_h = 0.72
        head_rect = patches.FancyBboxPatch(
            (x, y + card_h - header_h), card_w, header_h,
            boxstyle="round,pad=0.04,rounding_size=0.14",
            linewidth=0, facecolor=c_phase_head,
            zorder=3
        )
        ax.add_patch(head_rect)

        # Phase Label (e.g. PHASE 1)
        ax.text(
            x + 0.25, y + card_h - 0.25, p["phase"],
            fontsize=10, fontweight='bold', color="#38BDF8",
            va='center', zorder=4, fontfamily='sans-serif'
        )
        # Phase Title
        ax.text(
            x + 0.25, y + card_h - 0.50, p["title"],
            fontsize=11.5, fontweight='bold', color="#FFFFFF",
            va='center', zorder=4, fontfamily='sans-serif'
        )

        # Bullets
        bullet_start_y = y + card_h - header_h - 0.32
        for i, item in enumerate(p["items"]):
            ax.text(
                x + 0.22, bullet_start_y - (i * 0.44), item,
                fontsize=9.2, color=c_bullet, va='center', zorder=4,
                fontfamily='sans-serif', fontweight='medium'
            )

    # Connecting Flow Arrows between Phases
    # 1 -> 2
    ax.annotate("", xy=(5.5, 6.65), xytext=(5.25, 6.65),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=c_arrow, lw=3.0, zorder=5))
    # 2 -> 3
    ax.annotate("", xy=(10.7, 6.65), xytext=(10.45, 6.65),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=c_arrow, lw=3.0, zorder=5))
    
    # 3 -> 4 (Looping down: from Phase 3 right down to Phase 4 left)
    # Draw a clean curved path or step path
    ax.annotate("", xy=(1.0, 4.15), xytext=(15.2, 4.8),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=c_arrow, lw=2.5,
                                connectionstyle="arc3,rad=-0.15", zorder=5))
    ax.text(8.0, 4.55, "Sequential Progression to Supervisory Middleware & Navigation Integration",
            fontsize=9.5, fontweight='bold', color="#0369A1", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#E0F2FE", edgecolor="#38BDF8", lw=1.2), zorder=6)

    # 4 -> 5
    ax.annotate("", xy=(5.5, 2.45), xytext=(5.25, 2.45),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=c_arrow, lw=3.0, zorder=5))
    # 5 -> 6
    ax.annotate("", xy=(10.7, 2.45), xytext=(10.45, 2.45),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=c_arrow, lw=3.0, zorder=5))

    # Master Title Header at the top
    ax.text(
        8.0, 8.65, "6-PHASE ENGINEERING RESEARCH & IMPLEMENTATION METHODOLOGY",
        fontsize=14.5, fontweight='bold', color="#0F172A", ha='center', va='center',
        fontfamily='sans-serif'
    )
    ax.text(
        8.0, 8.32, "Autonomous Mobile Robot Human Intention Recognition & Collaborative Navigation Framework",
        fontsize=10.5, fontstyle='italic', color="#475569", ha='center', va='center',
        fontfamily='sans-serif'
    )

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_methodology_diagram()
