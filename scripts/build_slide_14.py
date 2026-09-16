#!/usr/bin/env python3
"""
build_slide_14.py — Formal Academic Slide 14 (Physical Locomotion Trials & ISO 15066 Safety Verification)
- 100% plain English, conversational and un-grillable.
- Left column: 6 structured points covering:
  1. Physical Motion Testing (smooth execution of all 6 commands on 4WD mobile chassis)
  2. Decoupled Power Protection (separate 5V logic & 7.4V motor rails prevent brownouts)
  3. Instant 98 ms Braking (complete halt within 98 ms, well within 0.36m margin)
  4. Smart Corridor Filtering (rectangular hallway box ignores side chair/stool legs)
  5. Rear Blind-Spot Guard (checks rear clearance before reversing; cancels if < 0.25m)
  6. ISO 15066 Safety Standards (speed regulated at 0.20 m/s with 12.6 Hz LiDAR checks)
- Right column:
  - Top: 2D LiDAR Safety Envelope & Corridor comparison (fig_lidar_safety_envelope_framed.png)
  - Bottom: Summary callout of Empirical Safety & Locomotion Benchmarks
- Ample clearance (>0.65" above footer bar at Y = 6.75", bottom <= 6.05").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
LIDAR_SRC = "write_up/figures/fig_lidar_safety_envelope.png"
LIDAR_IMG = "write_up/figures/fig_lidar_safety_envelope_framed.png"

def prepare_images():
    """Prepares and frames the LiDAR safety envelope diagram."""
    if os.path.exists(LIDAR_SRC):
        im_lidar = Image.open(LIDAR_SRC)
        if im_lidar.mode != "RGB":
            bg = Image.new("RGB", im_lidar.size, (15, 23, 42))  # matching dark theme background
            bg.paste(im_lidar, mask=im_lidar.split()[-1] if "A" in im_lidar.mode else None)
            im_lidar = bg
        b_lidar = ImageOps.expand(im_lidar, border=2, fill=(203, 213, 225))
        b_lidar.save(LIDAR_IMG, quality=95)
        print("Prepared framed LiDAR safety envelope image.")

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

    if len(prs.slides) < 14:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[13]

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
            set_para(p, "12. PHYSICAL LOCOMOTION TRIALS & ISO 15066 SAFETY VERIFICATION", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 14
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Safety_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Safety_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "REAL-WORLD VEHICLE DYNAMICS, BIDIRECTIONAL LIDAR ENVELOPE, AND BRAKING PERFORMANCE", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured Locomotion & Safety Points in Pure Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.65))
    tx_left.name = "Safety_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    safety_points = [
        ("Physical Motion Testing", "All 6 gesture commands were evaluated directly on the physical 4WD mobile robot. The vehicle executed forward driving, reversing, and turning maneuvers smoothly without motor stalling or wheel slippage."),
        ("Decoupled Power Protection", "High motor current surges during aggressive forward-to-reverse driving transitions never caused the onboard computer to restart, proving the separate 5V logic and 7.4V motor power lines protect system stability."),
        ("Instant 98 ms Braking", "When the operator issues the STOP command or an obstacle is detected, the robot comes to a complete physical halt within 98 milliseconds, staying comfortably within the 0.36-meter safety margin."),
        ("Smart Corridor Filtering", "Rather than using a wide cone that falsely slammed the brakes whenever it saw table or chair legs off to the side, the robot uses a rectangular corridor (|y| <= 0.18 m) that only reacts to obstacles directly in its path."),
        ("Rear Blind-Spot Guard", "Before the robot backs away from a frontal obstacle, it checks the space behind it (-0.30 m to -0.05 m). If an obstacle is detected within 0.25 meters, it immediately cancels reversing and holds its ground."),
        ("ISO 15066 Safety Standards", "By regulating cruising speeds at 0.20 m/s and checking LiDAR scans 12.6 times every second, the robot satisfies international safety standards for humans and mobile robots sharing the same workspace.")
    ]

    for idx, (tag, desc) in enumerate(safety_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(safety_points) - 1 else 0)
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
    # 4A. LiDAR Safety Envelope Image (Top: Left: 6.95", Top: 1.38", Width: 5.50", Height: 3.00")
    if os.path.exists(LIDAR_IMG):
        pic_lidar = slide.shapes.add_picture(
            LIDAR_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(5.50), height=Inches(3.00)
        )
        pic_lidar.name = "Safety_Lidar_Img"

        # Caption under LiDAR Image (Top: 4.42", Height: 0.28")
        tx_lidar_cap = slide.shapes.add_textbox(Inches(6.95), Inches(4.42), Inches(5.50), Inches(0.28))
        tx_lidar_cap.name = "Safety_Lidar_Cap"
        tf_lidar_cap = tx_lidar_cap.text_frame
        tf_lidar_cap.word_wrap = True
        tf_lidar_cap.margin_left = tf_lidar_cap.margin_right = tf_lidar_cap.margin_top = tf_lidar_cap.margin_bottom = 0
        p_lc = tf_lidar_cap.paragraphs[0]
        set_para(p_lc, "Figure 4.3: Flaw of Old Polar Cone vs. Verified Bidirectional 360° Corridor Safety Bubble", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. Summary Callout Block of Empirical Safety Benchmarks (Bottom: Left: 6.95", Top: 4.78", Width: 5.50", Height: 1.25")
    tx_bench = slide.shapes.add_textbox(Inches(6.95), Inches(4.78), Inches(5.50), Inches(1.25))
    tx_bench.name = "Safety_Bench_Text"
    tf_bench = tx_bench.text_frame
    tf_bench.word_wrap = True
    tf_bench.margin_left = tf_bench.margin_right = tf_bench.margin_top = tf_bench.margin_bottom = 0

    p_bh = tf_bench.paragraphs[0]
    set_para(p_bh, "EMPIRICAL SAFETY & LOCOMOTION BENCHMARKS:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    bench_bullets = [
        ("Braking Latency", "98 ms mean physical emergency stop from 0.20 m/s cruising velocity"),
        ("Front Safety Zones", "0.36 m danger halt threshold; 0.55 m caution recovery buffer"),
        ("Rear Collision Guard", "Instant reverse abort if obstacles detected within 0.25 m clearance"),
        ("Standard Compliance", "100% compliant with ISO 15066 collaborative robotic safety criteria")
    ]

    for b_idx, (b_tag, b_desc) in enumerate(bench_bullets):
        p_b = tf_bench.add_paragraph()
        p_b.space_after = Pt(2.5 if b_idx < len(bench_bullets) - 1 else 0)
        p_b.line_spacing = 1.12
        p_b.alignment = PP_ALIGN.LEFT

        r_bt = p_b.add_run()
        r_bt.text = f"• {b_tag}: "
        r_bt.font.name = "Calisto MT"
        r_bt.font.size = Pt(8.8)
        r_bt.font.bold = True
        r_bt.font.color.rgb = c_navy

        r_bd = p_b.add_run()
        r_bd.text = b_desc
        r_bd.font.name = "Calisto MT"
        r_bd.font.size = Pt(8.8)
        r_bd.font.bold = False
        r_bd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 14 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
