#!/usr/bin/env python3
"""
build_slide_3.py — Crystal Clear, Accessible Slide 3 (Introduction & Background)
Rewritten so ANY person can pick it up, read it, and understand it instantly in 5 seconds.
Eliminates dense jargon (teach pendants, dynamic spatial compliance) while retaining engineering rigor.
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
IMAGE_PATH = "write_up/figures/shared_workspace_human_robot.jpg"

def set_para(p, text, font_name="Calisto MT", size_pt=14, bold=False, italic=False, color_rgb=None, space_before_pt=0, space_after_pt=2, line_spacing=1.15, align=PP_ALIGN.LEFT):
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
    prs = pptx.Presentation(PPTX_PATH)
    slide = prs.slides[2]

    # Consistent Color System
    c_navy = RGBColor(0, 32, 96)      # #002060 GCTU Deep Navy (Headings)
    c_body = RGBColor(30, 41, 59)     # #1E293B High-Contrast Charcoal (Body Text)
    c_muted = RGBColor(71, 85, 105)   # #475569 Slate (Captions)

    # 1. Slide Title (28 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 1" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "01. INTRODUCTION & RESEARCH BACKGROUND", font_name="Calisto MT", size_pt=28, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes
    shapes_to_remove = [s for s in slide.shapes if s.name in ("Intro_Text", "Intro_Image", "Intro_Caption")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Left Column: Plain-English, Captivating Narrative
    txBox = slide.shapes.add_textbox(Inches(0.85), Inches(1.45), Inches(6.85), Inches(4.90))
    txBox.name = "Intro_Text"
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)

    # Point 1: Plain English
    p1 = tf.paragraphs[0]
    set_para(p1, "Robots Working Directly with Humans", size_pt=18, bold=True, color_rgb=c_navy, space_after_pt=3)
    p1_sub = tf.add_paragraph()
    set_para(p1_sub, "Robots are leaving safety cages to work alongside people in hospitals, warehouses, and homes. For humans and robots to coexist safely, the robot must understand where people are and respect their personal space.",
             size_pt=15, color_rgb=c_body, space_after_pt=14, line_spacing=1.18)

    # Point 2: Plain English
    p2 = tf.add_paragraph()
    set_para(p2, "Natural, Hands-Free Interaction", size_pt=18, bold=True, color_rgb=c_navy, space_after_pt=3)
    p2_sub = tf.add_paragraph()
    set_para(p2_sub, "Instead of requiring handheld controllers, touchscreens, or keyboards, humans can guide the robot using natural hand gestures and body movement—just like signaling to a human coworker.",
             size_pt=15, color_rgb=c_body, space_after_pt=14, line_spacing=1.18)

    # Point 3: Plain English
    p3 = tf.add_paragraph()
    set_para(p3, "Fast Onboard Intelligence (No Cloud Lag)", size_pt=18, bold=True, color_rgb=c_navy, space_after_pt=3)
    p3_sub = tf.add_paragraph()
    set_para(p3_sub, "Sending live video over the internet causes dangerous delays (>200 ms) and fails when Wi-Fi drops. In this project, all AI recognition and navigation decisions happen entirely inside the robot in real time.",
             size_pt=15, color_rgb=c_body, space_after_pt=0, line_spacing=1.18)

    # 3. Right Column: Real Assembled Robot Figure & Caption
    if os.path.exists(IMAGE_PATH):
        img_left = Inches(8.00)
        img_top = Inches(1.55)
        img_w = Inches(4.60)
        img_h = Inches(3.45)
        pic = slide.shapes.add_picture(IMAGE_PATH, img_left, img_top, width=img_w, height=img_h)
        pic.name = "Intro_Image"

        cap_top = Inches(5.12)
        cap_h = Inches(0.80)
        capBox = slide.shapes.add_textbox(img_left, cap_top, img_w, cap_h)
        capBox.name = "Intro_Caption"
        c_tf = capBox.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = Inches(0.05)
        c_tf.margin_right = Inches(0.05)
        c_tf.margin_top = Inches(0.05)
        c_tf.margin_bottom = Inches(0.05)
        cp = c_tf.paragraphs[0]
        set_para(cp, "Figure 1.1: Collaborative Human-Robot Interaction (HRI) in an industrial shared workspace, illustrating contactless gesture coordination.",
                 size_pt=12, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER, line_spacing=1.15)

    prs.save(PPTX_PATH)
    print(f"Slide 3 upgraded to plain-English accessible format in {PPTX_PATH}")

if __name__ == "__main__":
    main()
