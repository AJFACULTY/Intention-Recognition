#!/usr/bin/env python3
"""
build_slide_9.py — Formal Academic Slide 9 (Mechatronic Hardware & Power Distribution)
- Plain English, zero jargon traps: completely effortless to explain on first read.
- Left column: 6 structured hardware points (Open Editorial, cardless, breathable).
- Right column: Cropped photograph of the assembled physical robot with crisp frame,
  formal academic caption, and 3 key physical & electrical specification bullet points.
- Generous bottom clearance (>0.60" above footer bar at Y = 6.75").
- Dignified GCTU 2-tone palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
SRC_IMG = "write_up/figures/assembled_robot_real.jpg"
ROBOT_IMG = "write_up/figures/assembled_robot_cropped.jpg"

def prepare_robot_image():
    """Crops the robot photo cleanly and adds a subtle 1px frame border."""
    if os.path.exists(SRC_IMG):
        im = Image.open(SRC_IMG)
        # Tight, centered crop of the robot
        cropped = im.crop((180, 80, 1120, 740))
        # Add subtle 1px border (#CBD5E1 - 203, 213, 225)
        bordered = ImageOps.expand(cropped, border=2, fill=(203, 213, 225))
        bordered.save(ROBOT_IMG, quality=95)
        print(f"Prepared bordered robot image: {ROBOT_IMG}")

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
    prepare_robot_image()
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 9:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[8]

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
            set_para(p, "07. MECHATRONIC HARDWARE & POWER DISTRIBUTION", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 9
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Hw_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Hw_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "PHYSICAL EMBEDDED COMPUTING, SENSORS, CHASSIS & POWER ISOLATION", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured Hardware Points in Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(6.45), Inches(4.70))
    tx_left.name = "Hw_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    hardware_points = [
        ("Onboard Computer (Raspberry Pi 5)", "8GB RAM single-board computer running all camera tracking, gesture artificial intelligence, and navigation programs directly on the robot."),
        ("Motor Controller (ESP32-S3)", "Dedicated microcontroller that manages wheel speed and reads motor sensors smoothly without overloading the main computer."),
        ("Laser Scanner (MS200 LiDAR)", "360-degree laser sensor measuring room distances up to 12 meters for indoor mapping and instant emergency stops."),
        ("Motorized Camera Mount", "2-axis motorized camera gimbal that tilts and pans automatically to keep the operator's face and hands centered in view."),
        ("4-Wheel Drive Chassis", "Sturdy aluminium robot base powered by 4 geared DC motors with wheel sensors for smooth and steady movement."),
        ("Dual-Rail Power System", "Separate battery power circuits for the computer and motors to prevent electrical interference and sudden power shutdowns.")
    ]

    for idx, (tag, desc) in enumerate(hardware_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(hardware_points) - 1 else 0)
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

    # 4. Right Column: Assembled Physical Robot Photograph & Specifications
    if os.path.exists(ROBOT_IMG):
        # Image dimensions: Width = 5.00", Height = 3.51", Left = 7.48", Top = 1.38"
        pic = slide.shapes.add_picture(
            ROBOT_IMG,
            Inches(7.48), Inches(1.38),
            width=Inches(5.00), height=Inches(3.51)
        )
        pic.name = "Hw_Photo_Img"

        # Caption underneath photograph (Top: 4.94", Height: 0.22")
        tx_cap = slide.shapes.add_textbox(Inches(7.48), Inches(4.94), Inches(5.00), Inches(0.22))
        tx_cap.name = "Hw_Caption"
        tf_cap = tx_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
        p_cap = tf_cap.paragraphs[0]
        set_para(p_cap, "Figure 3.2: Assembled 4WD Mobile Robot with Active Vision & 2D LiDAR", font_name="Calisto MT", size_pt=9.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

        # Specifications Block underneath Caption (Top: 5.22", Height: 0.88", Bottom: 6.10")
        tx_spec = slide.shapes.add_textbox(Inches(7.48), Inches(5.22), Inches(5.00), Inches(0.88))
        tx_spec.name = "Hw_Specs_Text"
        tf_spec = tx_spec.text_frame
        tf_spec.word_wrap = True
        tf_spec.margin_left = tf_spec.margin_right = tf_spec.margin_top = tf_spec.margin_bottom = 0

        specs_list = [
            ("Dimensions & Mass", "220 × 180 × 165 mm | Total Platform Weight: 1.65 kg"),
            ("Operating Speeds", "0.20 m/s cruise speed | ±0.50 rad/s rotation | 98 ms halt"),
            ("Power Isolation", "7.4V Li-ion (2000 mAh) with dedicated 5V/5A buck converter")
        ]

        for s_idx, (s_tag, s_desc) in enumerate(specs_list):
            p_s = tf_spec.paragraphs[0] if s_idx == 0 else tf_spec.add_paragraph()
            p_s.space_after = Pt(3 if s_idx < len(specs_list) - 1 else 0)
            p_s.line_spacing = 1.12
            p_s.alignment = PP_ALIGN.LEFT

            r_s_tag = p_s.add_run()
            r_s_tag.text = f"• {s_tag}: "
            r_s_tag.font.name = "Calisto MT"
            r_s_tag.font.size = Pt(9.5)
            r_s_tag.font.bold = True
            r_s_tag.font.color.rgb = c_navy

            r_s_desc = p_s.add_run()
            r_s_desc.text = s_desc
            r_s_desc.font.name = "Calisto MT"
            r_s_desc.font.size = Pt(9.5)
            r_s_desc.font.bold = False
            r_s_desc.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 9 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
