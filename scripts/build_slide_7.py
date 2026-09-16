#!/usr/bin/env python3
"""
build_slide_7.py — Formal Academic Slide 7 (6-Phase Engineering Methodology)
- 6-Phase Engineering Research & Implementation Methodology.
- Open Editorial Typography: cardless, breathable, high-contrast.
- 2 rows x 3 columns symmetric layout.
- NO arrows (clean, unencumbered whitespace).
- Consistent 3-field structure per phase: [Bold Navy Tag]: [Plain-English Explanation].
- Generous bottom clearance (>0.75" above footer bar).
- Dignified GCTU 2-tone palette: Navy (#002060), Gold (#B8860B), Charcoal (#1E293B).
"""

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"

def set_para(p, text, font_name="Calisto MT", size_pt=14, bold=False, italic=False, color_rgb=None, space_before_pt=0, space_after_pt=2, line_spacing=1.14, align=PP_ALIGN.LEFT):
    p.text = text
    p.font.name = font_name
    p.font.size = Pt(size_pt)
    p.font.bold = bold
    p.font.italic = italic
    p.space_before = Pt(space_before_pt)
    p.space_after = Pt(space_after_pt)
    p.line_spacing = line_spacing
    if color_rgb:
        p.font.color.rgb = color_rgb
    p.alignment = align

def add_phase_column(slide, name, left, top, width, height, phase_num, title, items, c_navy, c_gold, c_body):
    tx = slide.shapes.add_textbox(left, top, width, height)
    tx.name = name
    tf = tx.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.02)

    # 1. Phase Badge (e.g. PHASE 01) in Gold
    p_badge = tf.paragraphs[0]
    set_para(p_badge, phase_num, font_name="Calisto MT", size_pt=10, bold=True, color_rgb=c_gold, space_after_pt=1, line_spacing=1.10)

    # 2. Phase Title in Bold Navy
    p_title = tf.add_paragraph()
    set_para(p_title, title, font_name="Calisto MT", size_pt=12, bold=True, color_rgb=c_navy, space_after_pt=5, line_spacing=1.12)

    # 3. Consistent Bullets: [Bold Navy Tag]: [Slate Body]
    for i, (tag, desc) in enumerate(items):
        p_item = tf.add_paragraph()
        p_item.space_after = Pt(3 if i < len(items) - 1 else 0)
        p_item.line_spacing = 1.14
        p_item.alignment = PP_ALIGN.LEFT

        r_tag = p_item.add_run()
        r_tag.text = f"• {tag}: "
        r_tag.font.name = "Calisto MT"
        r_tag.font.size = Pt(10)
        r_tag.font.bold = True
        r_tag.font.color.rgb = c_navy

        r_desc = p_item.add_run()
        r_desc.text = desc
        r_desc.font.name = "Calisto MT"
        r_desc.font.size = Pt(10)
        r_desc.font.bold = False
        r_desc.font.color.rgb = c_body

def main():
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 7:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[6]

    # Theme colors
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_slate  = RGBColor(100, 116, 139)   # #64748B Muted Slate

    # 1. Slide Title (Single Line Fit at 24 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 1" and shape.has_text_frame:
            shape.left = Inches(0.66)
            shape.top = Inches(0.35)
            shape.width = Inches(12.00)
            shape.height = Inches(0.60)
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "05. 6-PHASE RESEARCH & IMPLEMENTATION METHODOLOGY", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes and arrows on Slide 7
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Meth_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Meth_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "STRUCTURED RESEARCH & IMPLEMENTATION LIFECYCLE FROM EMBEDDED DESIGN TO VALIDATION", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # Coordinates: 3 balanced columns with generous breathing room (no arrows needed)
    col_lefts = [Inches(0.85), Inches(4.85), Inches(8.85)]
    col_w = Inches(3.63)
    row0_top = Inches(1.38)
    row_h = Inches(2.05)
    row1_top = Inches(3.88)

    # 3. Row 0: Phases 1 to 3 (Consistent 3-field tag & description)
    phases_row0 = [
        {
            "num": "PHASE 01",
            "title": "Mechatronics & Embedded Hardware",
            "items": [
                ("Robot Chassis", "Yahboom 4WD mobile base with DC encoder motors and 2-DOF camera gimbal."),
                ("Edge Compute", "Raspberry Pi 5 (8GB) paired with an ESP32-S3 real-time micro-ROS co-processor."),
                ("Power Isolation", "Decoupled dual battery circuits protecting computer logic from motor electrical spikes.")
            ]
        },
        {
            "num": "PHASE 02",
            "title": "Data Acquisition & Calibration",
            "items": [
                ("Dataset Size", "6,000 balanced gesture samples (1,000 per class) captured directly onboard."),
                ("Gesture Classes", "6 operational commands: STOP, GO, FOLLOW, LEFT, RIGHT, and BACK."),
                ("Testing Range", "Recorded across 1.0 m to 2.5 m under natural, unconstrained indoor lighting.")
            ]
        },
        {
            "num": "PHASE 03",
            "title": "Feature Engineering & Edge AI",
            "items": [
                ("Geometric Features", "21 hand landmarks converted into 19 scale- and distance-invariant features."),
                ("Neural Classifier", "Lightweight MLP model (46 KB) running in under 2 ms on the Raspberry Pi CPU."),
                ("Motion Predictor", "10-frame recurrent LSTM predicting operator movement trajectories.")
            ]
        }
    ]

    for idx, p in enumerate(phases_row0):
        add_phase_column(slide, f"Meth_P{idx+1}", col_lefts[idx], row0_top, col_w, row_h, p["num"], p["title"], p["items"], c_navy, c_gold, c_body)

    # 4. Transitional Flow Ribbon between Row 0 and Row 1
    tx_trans = slide.shapes.add_textbox(Inches(1.50), Inches(3.52), Inches(10.33), Inches(0.26))
    tx_trans.name = "Meth_Transition"
    tf_trans = tx_trans.text_frame
    tf_trans.word_wrap = True
    tf_trans.margin_left = tf_trans.margin_right = tf_trans.margin_top = tf_trans.margin_bottom = 0
    p_trans = tf_trans.paragraphs[0]
    set_para(p_trans, "──  SEQUENTIAL PROGRESSION TO SUPERVISORY MIDDLEWARE & NAVIGATION INTEGRATION  ──", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_slate, align=PP_ALIGN.CENTER)

    # 5. Row 1: Phases 4 to 6 (Consistent 3-field tag & description)
    phases_row1 = [
        {
            "num": "PHASE 04",
            "title": "Supervisory Control & Safety",
            "items": [
                ("ROS 2 Middleware", "Unified node architecture operating on dedicated communication Domain 20."),
                ("Decision Engine", "brain_node state machine with 5-frame rolling consensus and visual servoing."),
                ("Collision Safety", "Hard-coded reactive LiDAR safety stop halting the robot at 0.36 m.")
            ]
        },
        {
            "num": "PHASE 05",
            "title": "Metric SLAM & Autonomous Navigation",
            "items": [
                ("Laser Mapping", "2D occupancy grid maps generated at 5 cm resolution using slam_toolbox."),
                ("Sensor Fusion", "Extended Kalman Filter (EKF) combining wheel encoders and 6-axis IMU data."),
                ("Path Planning", "Nav2 autonomous navigation with 0.25 m obstacle inflation safety zones.")
            ]
        },
        {
            "num": "PHASE 06",
            "title": "Empirical Benchmarking & Validation",
            "items": [
                ("Latency Budget", "End-to-end reaction time clocked at 74.2 ms (well within 150 ms threshold)."),
                ("Locomotion Trials", "180 physical real-world tests achieving 96.67% operational accuracy."),
                ("Safety Compliance", "Deterministic stopping distance confirmed under ISO 15066 safety standards.")
            ]
        }
    ]

    for idx, p in enumerate(phases_row1):
        add_phase_column(slide, f"Meth_P{idx+4}", col_lefts[idx], row1_top, col_w, row_h, p["num"], p["title"], p["items"], c_navy, c_gold, c_body)

    prs.save(PPTX_PATH)
    print(f"Slide 7 (6-Phase Methodology) updated with consistent structure and no arrows in {PPTX_PATH}")

if __name__ == "__main__":
    main()
