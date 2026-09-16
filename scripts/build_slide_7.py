#!/usr/bin/env python3
"""
build_slide_7.py — Formal Academic Slide 7 (6-Phase Engineering Methodology)
- 6-Phase Engineering Research & Implementation Methodology.
- Open Editorial Typography: cardless, breathable, high-contrast.
- 2 rows x 3 columns symmetric layout.
- NO arrows and NO transitional text banners (pure, calm whitespace).
- Conversational, un-grillable engineering phrasing (zero eyebrow-raising jargon).
- Strict 3-field consistency per phase: [Bold Navy Label]: [Plain-English Sentence].
- Dignified GCTU 2-tone palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
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
        p_item.space_after = Pt(4 if i < len(items) - 1 else 0)
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

    # Clean existing custom shapes, banners, and arrows on Slide 7
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
    set_para(p_sub, "STRUCTURED RESEARCH & IMPLEMENTATION LIFECYCLE FROM DESIGN TO VALIDATION", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # Coordinates: 3 balanced columns with generous breathing room
    col_lefts = [Inches(0.85), Inches(4.85), Inches(8.85)]
    col_w = Inches(3.63)
    row0_top = Inches(1.42)
    row_h = Inches(2.15)
    row1_top = Inches(3.95)

    # 3. Row 0: Phases 1 to 3 (Simple, honest, conversational wording)
    phases_row0 = [
        {
            "num": "PHASE 01",
            "title": "Mechatronics & Hardware",
            "items": [
                ("Robot Platform", "4WD mobile base with geared DC motors, wheel encoders, and camera gimbal."),
                ("Dual Processors", "Raspberry Pi 5 for vision AI paired with an ESP32-S3 for real-time motor control."),
                ("Separate Power", "Dedicated battery packs powering the onboard computer and drive motors independently.")
            ]
        },
        {
            "num": "PHASE 02",
            "title": "Data Collection & Setup",
            "items": [
                ("Custom Dataset", "6,000 total gesture images (1,000 per class) collected with the onboard camera."),
                ("6 Core Gestures", "Navigational commands: STOP, GO, FOLLOW, LEFT, RIGHT, and BACK."),
                ("Realistic Testing", "Captured at distances between 1.0 m and 2.5 m under standard room lighting.")
            ]
        },
        {
            "num": "PHASE 03",
            "title": "Feature Extraction & AI Models",
            "items": [
                ("Hand Keypoints", "Detected 21 hand joints with MediaPipe and computed 19 normalized angles and distances."),
                ("Neural Classifier", "Compact neural network (46 KB) classifying gestures in under 2 ms on the CPU."),
                ("Motion Predictor", "Recurrent neural model (LSTM) tracking hand and body movements across consecutive frames.")
            ]
        }
    ]

    for idx, p in enumerate(phases_row0):
        add_phase_column(slide, f"Meth_P{idx+1}", col_lefts[idx], row0_top, col_w, row_h, p["num"], p["title"], p["items"], c_navy, c_gold, c_body)

    # 4. Row 1: Phases 4 to 6 (Simple, honest, conversational wording)
    phases_row1 = [
        {
            "num": "PHASE 04",
            "title": "Robot Control & Safety",
            "items": [
                ("ROS 2 Framework", "Modular software nodes connecting the camera, AI models, and motor drivers."),
                ("Decision Logic", "State machine filters out accidental motions by confirming steady hand gestures."),
                ("Emergency Halt", "2D LiDAR sensor automatically stops the robot if an obstacle is within 0.36 m.")
            ]
        },
        {
            "num": "PHASE 05",
            "title": "Mapping & Navigation",
            "items": [
                ("Indoor Mapping", "2D laser mapping (slam_toolbox) creates a clean 5 cm resolution floor plan."),
                ("Robot Position", "Accurately tracks robot movement by combining wheel encoders with an onboard IMU sensor."),
                ("Path Planning", "Nav2 autonomous navigation plans collision-free paths with safe margins around obstacles.")
            ]
        },
        {
            "num": "PHASE 06",
            "title": "Experimental Testing & Results",
            "items": [
                ("Fast Response", "End-to-end reaction time of 74.2 ms, comfortably below the 150 ms real-time limit."),
                ("Live Driving Trials", "180 real-world physical tests achieving a 96.67% operational success rate."),
                ("Safety Confirmed", "Verified that the robot reliably halts before coming into contact with any human or obstacle.")
            ]
        }
    ]

    for idx, p in enumerate(phases_row1):
        add_phase_column(slide, f"Meth_P{idx+4}", col_lefts[idx], row1_top, col_w, row_h, p["num"], p["title"], p["items"], c_navy, c_gold, c_body)

    prs.save(PPTX_PATH)
    print(f"Slide 7 updated: transitional banner removed, text simplified and un-grillable in {PPTX_PATH}")

if __name__ == "__main__":
    main()
