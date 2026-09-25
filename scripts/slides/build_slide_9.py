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

def prepare_robot_images():
    """Crops both robot photos cleanly to exact matching 1.15 aspect ratio and adds a subtle 1px frame border."""
    im_wired = Image.open("write_up/figures/chassis_wired_cropped.jpg")
    crop_wired = im_wired.crop((0, 7, 575, 507)) # 575 x 500 -> aspect 1.15
    b_wired = ImageOps.expand(crop_wired, border=2, fill=(203, 213, 225))
    b_wired.save("write_up/figures/wired_bot_side.jpg", quality=95)

    im_asm = Image.open("write_up/figures/assembled_robot_real.jpg")
    crop_asm = im_asm.crop((250, 80, 1010, 740)) # 760 x 660 -> aspect 1.151
    b_asm = ImageOps.expand(crop_asm, border=2, fill=(203, 213, 225))
    b_asm.save("write_up/figures/assembled_bot_side.jpg", quality=95)
    print("Prepared undistorted side-by-side images.")

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
    prepare_robot_images()
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
            set_para(p, "MECHATRONIC HARDWARE & POWER DISTRIBUTION", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

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
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.90), Inches(4.70))
    tx_left.name = "Hw_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    hardware_points = [
        ("Onboard Computer (Raspberry Pi 5)", "8GB RAM single-board computer running all camera tracking, gesture artificial intelligence, and navigation programs directly on the robot."),
        ("Motor Controller (ESP32-S3)", "Dedicated microcontroller that manages wheel speed and reads motor sensors smoothly without overloading the main computer."),
        ("Laser Scanner (MS200 LiDAR)", "360-degree laser sensor measuring room distances up to 12 meters for indoor mapping and reactive emergency halts."),
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

    # 4. Right Column: Side-by-Side Images (Wired Stack vs Fully Assembled)
    img_wired = "write_up/figures/wired_bot_side.jpg"
    img_asm   = "write_up/figures/assembled_bot_side.jpg"

    if os.path.exists(img_wired) and os.path.exists(img_asm):
        # Photo 1: Internal Wiring Stack (Left: 7.10", Top: 1.50", Width: 2.88", Height: 2.50")
        pic1 = slide.shapes.add_picture(
            img_wired,
            Inches(7.10), Inches(1.50),
            width=Inches(2.88), height=Inches(2.50)
        )
        pic1.name = "Hw_Photo_Wired"

        # Caption 1 (Top: 4.10", Height: 0.45")
        tx_c1 = slide.shapes.add_textbox(Inches(7.10), Inches(4.10), Inches(2.88), Inches(0.45))
        tx_c1.name = "Hw_Cap_Wired"
        tf_c1 = tx_c1.text_frame
        tf_c1.word_wrap = True
        tf_c1.margin_left = tf_c1.margin_right = tf_c1.margin_top = tf_c1.margin_bottom = 0
        p_c1 = tf_c1.paragraphs[0]
        set_para(p_c1, "Figure 3.2: Internal Electronics Stack\n(Raspberry Pi 5, ESP32-S3 & Motor Drivers)", font_name="Calisto MT", size_pt=9.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

        # Photo 2: Fully Assembled Robot (Left: 10.18", Top: 1.50", Width: 2.88", Height: 2.50")
        pic2 = slide.shapes.add_picture(
            img_asm,
            Inches(10.18), Inches(1.50),
            width=Inches(2.88), height=Inches(2.50)
        )
        pic2.name = "Hw_Photo_Assembled"

        # Caption 2 (Top: 4.10", Height: 0.45")
        tx_c2 = slide.shapes.add_textbox(Inches(10.18), Inches(4.10), Inches(2.88), Inches(0.45))
        tx_c2.name = "Hw_Cap_Assembled"
        tf_c2 = tx_c2.text_frame
        tf_c2.word_wrap = True
        tf_c2.margin_left = tf_c2.margin_right = tf_c2.margin_top = tf_c2.margin_bottom = 0
        p_c2 = tf_c2.paragraphs[0]
        set_para(p_c2, "Figure 3.3: Fully Enclosed Platform\n(360° MS200 LiDAR & Active Gimbal)", font_name="Calisto MT", size_pt=9.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    prs.save(PPTX_PATH)
    print(f"Slide 9 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
