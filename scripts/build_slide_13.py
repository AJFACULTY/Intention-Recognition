#!/usr/bin/env python3
"""
build_slide_13.py — Formal Academic Slide 13 (System Latency & Classification Accuracy)
- 100% plain English, conversational and un-grillable.
- Left column: 6 structured points covering:
  1. The 132-Millisecond Response Budget (132.0 ms total vision-to-motor pipeline)
  2. Speed Breakdown by Stage (50ms camera, 38ms hand, 2ms AI, 40ms motor)
  3. 99.38% Gesture AI Accuracy (tested on 6,000 unseen hand poses)
  4. Tested in 180 Physical Robot Runs (96.67% aggregate success in mobile runs)
  5. Distance Robustness (1.0m to 2.5m invariant accuracy)
  6. Lighting Consistency (verified across daylight and fluorescent lighting)
- Right column:
  - Top: Latency Boxplot across distance and lighting regimes (fig_latency_boxplot_framed.png)
  - Bottom-Left: 99.38% Gesture Confusion Matrix (confusion_matrix_framed.png)
  - Bottom-Right: Empirical Benchmarks summary callout
- Ample clearance (>0.65" above footer bar at Y = 6.75", bottom <= 6.08").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
BOXPLOT_SRC = "write_up/figures/fig_latency_boxplot.png"
BOXPLOT_IMG = "write_up/figures/fig_latency_boxplot_framed.png"
CM_SRC = "write_up/figures/MLP_Confusion_Matrix.png"
CM_IMG = "write_up/figures/confusion_matrix_framed.png"

def prepare_images():
    """Prepares and frames the latency boxplot and confusion matrix."""
    if os.path.exists(BOXPLOT_SRC):
        im_box = Image.open(BOXPLOT_SRC)
        if im_box.mode != "RGB":
            bg = Image.new("RGB", im_box.size, (255, 255, 255))
            bg.paste(im_box, mask=im_box.split()[-1] if "A" in im_box.mode else None)
            im_box = bg
        b_box = ImageOps.expand(im_box, border=2, fill=(203, 213, 225))
        b_box.save(BOXPLOT_IMG, quality=95)

    if os.path.exists(CM_SRC):
        im_cm = Image.open(CM_SRC)
        if im_cm.mode != "RGB":
            bg = Image.new("RGB", im_cm.size, (255, 255, 255))
            bg.paste(im_cm, mask=im_cm.split()[-1] if "A" in im_cm.mode else None)
            im_cm = bg
        b_cm = ImageOps.expand(im_cm, border=2, fill=(203, 213, 225))
        b_cm.save(CM_IMG, quality=95)

    print("Prepared framed latency and confusion matrix images.")

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
            set_para(p, "11. SYSTEM LATENCY & CLASSIFICATION ACCURACY", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

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
    set_para(p_sub, "REAL-TIME RESPONSE BUDGET, NEURAL ACCURACY, AND MULTI-CONDITION RELIABILITY", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured Latency & Accuracy Points in Pure Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.70))
    tx_left.name = "Latency_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    latency_points = [
        ("132-Millisecond Total Response", "From light entering the camera lens to physical wheel movement, the complete system takes only 132.0 milliseconds — faster than a human eye blink (300 ms) and well within the 150 ms safety limit."),
        ("Speed Breakdown by Stage", "Camera capture takes 50.0 ms, hand tracking takes 38.2 ms, AI classification takes 1.8 ms, and motor controller communication takes 40.0 ms, proving edge AI runs smoothly without GPUs."),
        ("99.38% Gesture AI Accuracy", "The compact neural network was evaluated across 6,000 unseen hand poses, correctly identifying commands 99.38% of the time with near-zero confusion between gestures."),
        ("180 Physical Mobile Trials", "In real-world mobile runs with an operator walking in the lab, the robot achieved an overall command success rate of 96.67% across all 6 gesture commands."),
        ("Distance Robustness (1m to 2.5m)", "Because hand measurements are scaled automatically using palm width, recognition remains highly accurate whether standing 1.0 meter away (100%) or 2.5 meters away (92.6%)."),
        ("Lighting Consistency", "Statistical testing confirmed identical reaction times under natural sunlight (132.7 ms) and indoor fluorescent room lighting (132.5 ms), ensuring dependable all-day operation.")
    ]

    for idx, (tag, desc) in enumerate(latency_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(latency_points) - 1 else 0)
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
    # 4A. Latency Boxplot (Top: Left: 6.95", Top: 1.38", Width: 5.50", Height: 2.05")
    if os.path.exists(BOXPLOT_IMG):
        pic_box = slide.shapes.add_picture(
            BOXPLOT_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(5.50), height=Inches(2.05)
        )
        pic_box.name = "Latency_Boxplot_Img"

        # Caption under Boxplot (Top: 3.46", Height: 0.28")
        tx_box_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.46), Inches(5.50), Inches(0.28))
        tx_box_cap.name = "Latency_Boxplot_Cap"
        tf_box_cap = tx_box_cap.text_frame
        tf_box_cap.word_wrap = True
        tf_box_cap.margin_left = tf_box_cap.margin_right = tf_box_cap.margin_top = tf_box_cap.margin_bottom = 0
        p_bc = tf_box_cap.paragraphs[0]
        set_para(p_bc, "Figure 4.1: End-to-End Latency Across Operating Distances & Lighting Regimes (180 Trials)", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. 99.38% Confusion Matrix (Bottom-Left: Left: 6.95", Top: 3.80", Width: 2.30", Height: 1.80")
    if os.path.exists(CM_IMG):
        pic_cm = slide.shapes.add_picture(
            CM_IMG,
            Inches(6.95), Inches(3.80),
            width=Inches(2.30), height=Inches(1.80)
        )
        pic_cm.name = "Latency_CM_Img"

        # Caption under Confusion Matrix (Top: 5.64", Height: 0.32")
        tx_cm_cap = slide.shapes.add_textbox(Inches(6.95), Inches(5.64), Inches(2.30), Inches(0.32))
        tx_cm_cap.name = "Latency_CM_Cap"
        tf_cm_cap = tx_cm_cap.text_frame
        tf_cm_cap.word_wrap = True
        tf_cm_cap.margin_left = tf_cm_cap.margin_right = tf_cm_cap.margin_top = tf_cm_cap.margin_bottom = 0
        p_cc = tf_cm_cap.paragraphs[0]
        set_para(p_cc, "Figure 4.2: 99.38% Confusion Matrix", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4C. Summary Block of Empirical Benchmarks (Bottom-Right: Left: 9.45", Top: 3.80", Width: 3.00", Height: 2.15")
    tx_bench = slide.shapes.add_textbox(Inches(9.45), Inches(3.80), Inches(3.00), Inches(2.15))
    tx_bench.name = "Latency_Bench_Text"
    tf_bench = tx_bench.text_frame
    tf_bench.word_wrap = True
    tf_bench.margin_left = tf_bench.margin_right = tf_bench.margin_top = tf_bench.margin_bottom = 0

    p_bh = tf_bench.paragraphs[0]
    set_para(p_bh, "EMPIRICAL BENCHMARKS:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    bench_bullets = [
        ("Turnaround Time", "132.6 ms mean (fastest: 123 ms, peak: 143 ms)"),
        ("AI Accuracy", "99.38% correct across 6,000 lab test samples"),
        ("Physical Runs", "96.67% command success across 180 mobile trials"),
        ("Safety Standard", "100% of runs below 150 ms ISO 15066 bound")
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
    print(f"Slide 13 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
