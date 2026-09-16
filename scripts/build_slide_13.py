#!/usr/bin/env python3
"""
build_slide_13.py — Formal Academic Slide 13 (Testing & Results: System Latency & Accuracy)
- Title: 11. TESTING & RESULTS: SYSTEM LATENCY & ACCURACY
- Eyebrow: REAL-TIME RESPONSE SPEED, GESTURE ACCURACY, AND MULTI-CONDITION RELIABILITY
- 100% plain English, reduced text, concise and scannable on first read.
- Left column: 5 punchy points:
  1. 132 ms Total Response Time
  2. Instant AI on Low-Cost CPU (1.8 ms inference)
  3. 96.67% Physical Mobile Success (180 real-world trials)
  4. Reliable Operating Range (1.0m to 2.5m)
  5. Lighting Independence (daylight vs fluorescent)
- Right column:
  - Top: Easy-to-explain Accuracy Bar Chart (fig_accuracy_by_condition_framed.png)
  - Bottom: Clear 132.0 ms Latency Breakdown & ISO 15066 safety block
- Ample clearance (>0.70" above footer bar at Y = 6.75", bottom <= 6.00").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
ACC_SRC = "write_up/figures/fig_accuracy_by_condition.png"
ACC_IMG = "write_up/figures/fig_accuracy_by_condition_framed.png"

def prepare_images():
    """Prepares and frames the accuracy bar chart."""
    if os.path.exists(ACC_SRC):
        im = Image.open(ACC_SRC)
        if im.mode != "RGB":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1] if "A" in im.mode else None)
            im = bg
        framed = ImageOps.expand(im, border=2, fill=(203, 213, 225))
        framed.save(ACC_IMG, quality=95)
        print("Prepared framed accuracy bar chart.")

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

    if len(prs.slides) < 13:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[12]

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
            set_para(p, "11. TESTING & RESULTS: SYSTEM LATENCY & ACCURACY", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 13
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Latency_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Latency_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "REAL-TIME RESPONSE SPEED, GESTURE ACCURACY, AND MULTI-CONDITION RELIABILITY", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 5 Concise, Plain English Points (Reduced text, easy to understand)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.50))
    tx_left.name = "Latency_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    latency_points = [
        ("132 ms Total Response Time", "From the camera seeing a hand gesture to the wheels turning takes only 132 milliseconds—twice as fast as an eye blink (300 ms) and well within the 150 ms safety limit."),
        ("Fast AI on Low-Cost Hardware", "The compact neural network makes recognition decisions in just 1.8 milliseconds, proving intelligent AI runs smoothly on an affordable Raspberry Pi without graphics cards."),
        ("96.67% Physical Driving Success", "In 180 real-world driving trials with operators walking in the lab, the robot correctly recognized and executed commands 96.67% of the time."),
        ("Reliable Operating Range", "Because hand features are scaled automatically by palm size, accuracy stays strong from 1.0 meter (100%) up to 2.5 meters (92.6%) away."),
        ("Consistent in Any Lighting", "The robot achieved identical 96.7% accuracy under bright natural sunlight and fluorescent office lights, ensuring reliable all-day operation.")
    ]

    for idx, (tag, desc) in enumerate(latency_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(10 if idx < len(latency_points) - 1 else 0)
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
    # 4A. Easy-to-Explain Accuracy Bar Chart (Top: Left: 6.95", Top: 1.38", Width: 5.50", Height: 2.28")
    if os.path.exists(ACC_IMG):
        pic_acc = slide.shapes.add_picture(
            ACC_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(5.50), height=Inches(2.28)
        )
        pic_acc.name = "Latency_Boxplot_Img"

        # Caption under Bar Chart (Top: 3.70", Height: 0.25")
        tx_acc_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.70), Inches(5.50), Inches(0.25))
        tx_acc_cap.name = "Latency_Boxplot_Cap"
        tf_acc_cap = tx_acc_cap.text_frame
        tf_acc_cap.word_wrap = True
        tf_acc_cap.margin_left = tf_acc_cap.margin_right = tf_acc_cap.margin_top = tf_acc_cap.margin_bottom = 0
        p_ac = tf_acc_cap.paragraphs[0]
        set_para(p_ac, "Figure 4.1: Observed Physical Accuracy Across Gestures, Operating Distances & Lighting (180 Trials)", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. Summary Latency Breakdown & Benchmarks Box (Bottom: Left: 6.95", Top: 4.05", Width: 5.50", Height: 1.95")
    tx_bench = slide.shapes.add_textbox(Inches(6.95), Inches(4.05), Inches(5.50), Inches(1.95))
    tx_bench.name = "Latency_Bench_Text"
    tf_bench = tx_bench.text_frame
    tf_bench.word_wrap = True
    tf_bench.margin_left = tf_bench.margin_right = tf_bench.margin_top = tf_bench.margin_bottom = 0

    p_bh = tf_bench.paragraphs[0]
    set_para(p_bh, "END-TO-END LATENCY BUDGET & SPEED BREAKDOWN (132.0 ms TOTAL):", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    latency_breakdown = [
        ("Camera Video Capture", "50.0 ms (640×480 @ 30 FPS video streaming)"),
        ("Hand Tracking", "38.2 ms (MediaPipe landmark extraction on quad-core CPU)"),
        ("Neural Classifier", "1.8 ms (instant geometric feature classification)"),
        ("Motor Communication", "40.0 ms (micro-ROS UART command delivery to wheels)"),
        ("Safety Standard", "100% of runs below 150 ms ISO 15066 safety deadline")
    ]

    for b_idx, (b_tag, b_desc) in enumerate(latency_breakdown):
        p_b = tf_bench.add_paragraph()
        p_b.space_after = Pt(2.5 if b_idx < len(latency_breakdown) - 1 else 0)
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
    print(f"Slide 13 successfully updated in {PPTX_PATH}")

if __name__ == "__main__":
    main()
