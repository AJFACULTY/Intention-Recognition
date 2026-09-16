#!/usr/bin/env python3
"""
build_slide_15.py — Formal Academic Slide 15 (Conclusion & Physical Demonstration Transition)
- 100% plain English, conversational and un-grillable.
- Left column: 5 structured takeaway points covering:
  1. Complete Edge Autonomy (runs entirely on Raspberry Pi 5 without clouds or external GPUs)
  2. High-Accuracy Gesture AI (99.38% test accuracy, 96.67% across 180 mobile trials)
  3. Deterministic Real-Time Safety (132 ms latency with 98 ms braking, ISO 15066 compliant)
  4. Smart Bidirectional Safety Bubble (Cartesian corridor + rear blind-spot guard prevents crashes)
  5. Unattended Autonomous Navigation (100% completion across 15.89 m multi-room patrol route)
- Right column:
  - Top-Left: High-resolution framed photo of physical robot (assembled_demo_framed.jpg)
  - Top-Right: Key Milestones Summary block
  - Bottom: Structured Live Demonstration Protocol sequence
- Ample clearance (>0.70" above footer bar at Y = 6.75", bottom <= 6.02").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
ROBOT_SRC = "write_up/figures/assembled_robot_real.jpg"
ROBOT_IMG = "write_up/figures/assembled_demo_framed.jpg"

def prepare_images():
    """Prepares and frames the physical robot showcase photo."""
    if os.path.exists(ROBOT_SRC):
        im = Image.open(ROBOT_SRC)
        # Crop tightly around robot (x: 240 to 1080, y: 120 to 780)
        crop_im = im.crop((240, 120, 1080, 780))
        framed = ImageOps.expand(crop_im, border=2, fill=(203, 213, 225))
        framed.save(ROBOT_IMG, quality=95)
        print("Prepared framed demo robot image.")

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

def main():
    prepare_images()
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 15:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[14]

    # Theme colors
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_muted  = RGBColor(100, 116, 139)   # #64748B Muted Slate

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
            set_para(p, "13. CONCLUSION & PHYSICAL DEMONSTRATION TRANSITION", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 15
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Conclusion_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Conclusion_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "SUMMARY OF ENGINEERING CONTRIBUTIONS, SYSTEM IMPACT, AND LIVE DEMO READINESS", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 5 Structured Conclusion Points in Pure Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.65))
    tx_left.name = "Conclusion_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    conclusion_points = [
        ("Complete Edge Autonomy", "Demonstrated that computer vision, neural gesture recognition, human trajectory prediction, and SLAM navigation execute entirely onboard an affordable Raspberry Pi 5 without relying on clouds or external GPUs."),
        ("High-Accuracy Gesture AI", "The lightweight neural classifier achieved 99.38% test accuracy across 6,000 hand poses, and delivered 96.67% reliable physical command execution across 180 mobile trials in the laboratory."),
        ("Guaranteed Real-Time Safety", "The complete vision-to-motor control pipeline executes in 132.0 milliseconds with 98 ms physical braking—faster than a human eye blink (300 ms) and fully compliant with ISO 15066 collaborative safety criteria."),
        ("Smart Bidirectional Safety Bubble", "Replacing wide cone sensors with a rectangular corridor (|y| <= 0.18 m) and rear blind-spot guard safely eliminates false alarms from side obstacles while preventing collisions during reverse maneuvers."),
        ("Unattended Autonomous Navigation", "Physical testing confirmed the robot reliably maps indoor environments and autonomously executes multi-waypoint patrol missions with sub-decimeter accuracy and proactive obstacle clearance.")
    ]

    for idx, (tag, desc) in enumerate(conclusion_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(8 if idx < len(conclusion_points) - 1 else 0)
        p.line_spacing = 1.15
        p.alignment = PP_ALIGN.LEFT

        r_tag = p.add_run()
        r_tag.text = f"• {tag}: "
        r_tag.font.name = "Calisto MT"
        r_tag.font.size = Pt(11)
        r_tag.font.bold = True
        r_tag.font.color.rgb = c_navy

        r_desc = p.add_run()
        r_desc.text = desc
        r_desc.font.name = "Calisto MT"
        r_desc.font.size = Pt(11)
        r_desc.font.bold = False
        r_desc.font.color.rgb = c_body

    # 4. Right Column Visuals
    # 4A. Robot Showcase Photo (Top-Left of Right Col: Left: 6.95", Top: 1.38", Width: 2.80", Height: 2.20")
    if os.path.exists(ROBOT_IMG):
        pic_robot = slide.shapes.add_picture(
            ROBOT_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(2.80), height=Inches(2.20)
        )
        pic_robot.name = "Conclusion_Robot_Img"

        # Caption under Photo (Top: 3.60", Height: 0.22")
        tx_pic_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.60), Inches(2.80), Inches(0.22))
        tx_pic_cap.name = "Conclusion_Robot_Cap"
        tf_pic_cap = tx_pic_cap.text_frame
        tf_pic_cap.word_wrap = True
        tf_pic_cap.margin_left = tf_pic_cap.margin_right = tf_pic_cap.margin_top = tf_pic_cap.margin_bottom = 0
        p_rc = tf_pic_cap.paragraphs[0]
        set_para(p_rc, "Figure 5.1: Physical Mobile Robot Platform", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. Key Project Milestones Box (Top-Right of Right Col: Left: 9.95", Top: 1.38", Width: 2.50", Height: 2.44")
    tx_milestones = slide.shapes.add_textbox(Inches(9.95), Inches(1.38), Inches(2.50), Inches(2.44))
    tx_milestones.name = "Conclusion_Milestones_Text"
    tf_milestones = tx_milestones.text_frame
    tf_milestones.word_wrap = True
    tf_milestones.margin_left = tf_milestones.margin_right = tf_milestones.margin_top = tf_milestones.margin_bottom = 0

    p_mh = tf_milestones.paragraphs[0]
    set_para(p_mh, "CORE MILESTONES:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    milestones = [
        ("Edge Computing", "100% onboard processing"),
        ("Gesture AI", "99.38% test accuracy"),
        ("Total Latency", "132 ms response budget"),
        ("Braking Time", "98 ms emergency halt"),
        ("Facility Patrol", "15.89 m autonomous run")
    ]

    for m_idx, (m_tag, m_desc) in enumerate(milestones):
        p_m = tf_milestones.add_paragraph()
        p_m.space_after = Pt(2.5 if m_idx < len(milestones) - 1 else 0)
        p_m.line_spacing = 1.12
        p_m.alignment = PP_ALIGN.LEFT

        r_mt = p_m.add_run()
        r_mt.text = f"• {m_tag}: "
        r_mt.font.name = "Calisto MT"
        r_mt.font.size = Pt(8.8)
        r_mt.font.bold = True
        r_mt.font.color.rgb = c_navy

        r_md = p_m.add_run()
        r_md.text = m_desc
        r_md.font.name = "Calisto MT"
        r_md.font.size = Pt(8.8)
        r_md.font.bold = False
        r_md.font.color.rgb = c_body

    # 4C. Live Demonstration Protocol Box (Bottom: Left: 6.95", Top: 3.92", Width: 5.50", Height: 2.10")
    tx_demo = slide.shapes.add_textbox(Inches(6.95), Inches(3.92), Inches(5.50), Inches(2.10))
    tx_demo.name = "Conclusion_Demo_Text"
    tf_demo = tx_demo.text_frame
    tf_demo.word_wrap = True
    tf_demo.margin_left = tf_demo.margin_right = tf_demo.margin_top = tf_demo.margin_bottom = 0

    p_dh = tf_demo.paragraphs[0]
    set_para(p_dh, "PHYSICAL DEMONSTRATION TRANSITION PROTOCOL:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    demo_steps = [
        ("1. Platform Bring-Up", "Confirm 7.4V battery voltage, calibrate IMU, and verify micro-ROS serial bridge."),
        ("2. Real-Time Gesture Driving", "Demonstrate live recognition and chassis motion across all 6 gesture commands."),
        ("3. Person-Tracking Follow Mode", "Showcase 2-DOF vision gimbal operator tracking and closed-loop chassis following."),
        ("4. Autonomous Safety Overrides", "Demonstrate reactive 0.36 m obstacle halt, rear collision abort, and audio chimes."),
        ("5. Nav2 Autonomous Navigation", "Dispatch multi-waypoint goal poses across the calibrated indoor metric map.")
    ]

    for d_idx, (d_tag, d_desc) in enumerate(demo_steps):
        p_d = tf_demo.add_paragraph()
        p_d.space_after = Pt(2.5 if d_idx < len(demo_steps) - 1 else 0)
        p_d.line_spacing = 1.12
        p_d.alignment = PP_ALIGN.LEFT

        r_dt = p_d.add_run()
        r_dt.text = f"{d_tag}: "
        r_dt.font.name = "Calisto MT"
        r_dt.font.size = Pt(8.8)
        r_dt.font.bold = True
        r_dt.font.color.rgb = c_navy

        r_dd = p_d.add_run()
        r_dd.text = d_desc
        r_dd.font.name = "Calisto MT"
        r_dd.font.size = Pt(8.8)
        r_dd.font.bold = False
        r_dd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 15 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
