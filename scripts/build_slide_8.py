#!/usr/bin/env python3
"""
build_slide_8.py — Formal Academic Slide 8 (Software Architecture & Inter-Node Dataflow)
- ROS 2 Humble Middleware & Inter-Process Topic Dataflow.
- 2-Column Split:
  * Left: Open Editorial structured breakdown of the Software & Communication Pipeline (11 pt).
  * Right: Publication-grade system architecture diagram (system_architecture.png).
- Un-grillable plain English, zero jargon traps.
- Generous bottom clearance (>0.75" above footer bar).
- Dignified GCTU 2-tone palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
ARCH_IMG = "write_up/figures/system_architecture.png"

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
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 8:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[7]

    # Theme colors
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_muted  = RGBColor(100, 116, 139)   # #64748B Muted Slate
    c_red    = RGBColor(180, 40, 40)     # Subtle crimson for safety bypass tag

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
            set_para(p, "06. SOFTWARE ARCHITECTURE & INTER-NODE DATAFLOW", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 8
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Arch_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Arch_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "MODULAR ROS 2 HUMBLE MIDDLEWARE, TOPIC PIPELINES & HARDWARE BRIDGE", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: Structured Software & Dataflow Breakdown (11 pt)
    # Left: 0.85", Top: 1.38", Width: 6.35", Height: 4.70"
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(6.35), Inches(4.70))
    tx_left.name = "Arch_Tiers_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    software_pipeline = [
        ("Middleware Core (ROS 2 Humble)", "Executes modular software nodes communicating over asynchronous publish/subscribe topics on dedicated Domain 20.", c_navy),
        ("Sensory Streaming", "Camera and 2D LiDAR continuously stream uncompressed video (/camera/image_raw at 20 FPS) and laser scans (/scan at 12.5 Hz).", c_navy),
        ("Neural Perception Node", "Consumes camera frames, extracts hand joint coordinates, and publishes discrete gesture tokens (/cognition/gesture).", c_navy),
        ("Supervisory Control (brain_node)", "Filters accidental motions through multi-frame consensus and computes directional driving commands (/cmd_vel).", c_navy),
        ("Real-Time Bridge (micro-ROS)", "Streams velocity setpoints across a high-speed 921,600 baud serial UART link to the ESP32-S3 motor co-processor.", c_navy),
        ("Priority Multiplexer (twist_mux)", "Hardware safety monitor immediately preempts autonomous gestures and halts the robot if a LiDAR obstacle is within 0.36 m.", c_red)
    ]

    for idx, (tag, desc, tag_color) in enumerate(software_pipeline):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(8 if idx < len(software_pipeline) - 1 else 0)
        p.line_spacing = 1.15
        p.alignment = PP_ALIGN.LEFT

        r_tag = p.add_run()
        r_tag.text = f"• {tag}: "
        r_tag.font.name = "Calisto MT"
        r_tag.font.size = Pt(11)
        r_tag.font.bold = True
        r_tag.font.color.rgb = tag_color

        r_desc = p.add_run()
        r_desc.text = desc
        r_desc.font.name = "Calisto MT"
        r_desc.font.size = Pt(11)
        r_desc.font.bold = False
        r_desc.font.color.rgb = c_body

    # 4. Right Column: Publication-Grade Architecture Diagram
    if os.path.exists(ARCH_IMG):
        # Left: 7.45", Top: 1.38", Width: 4.95", Height: 4.70"
        pic = slide.shapes.add_picture(
            ARCH_IMG,
            Inches(7.45), Inches(1.38),
            width=Inches(4.95), height=Inches(4.70)
        )
        pic.name = "Arch_Diagram_Img"

        # Caption underneath diagram
        tx_cap = slide.shapes.add_textbox(Inches(7.45), Inches(6.12), Inches(4.95), Inches(0.25))
        tx_cap.name = "Arch_Caption"
        tf_cap = tx_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
        p_cap = tf_cap.paragraphs[0]
        set_para(p_cap, "Figure 3.1: End-to-End Cognitive System Architecture & Safety Interlock", font_name="Calisto MT", size_pt=9.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    prs.save(PPTX_PATH)
    print(f"Slide 8 (Software Architecture & Dataflow) successfully updated in {PPTX_PATH}")

if __name__ == "__main__":
    main()
