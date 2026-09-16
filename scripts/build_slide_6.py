#!/usr/bin/env python3
"""
build_slide_6.py — 1-to-1 Paired Literature Review & Solutions Slide
- Title: 04. LITERATURE REVIEW & RESEARCH GAPS
- Top Section: BENCHMARK RESEARCH GAPS IN LITERATURE
  Col 1: Mahmud et al. (Cloud/GPU dependency)
  Col 2: Tsitos et al. (Stationary arm without mobile base)
  Col 3: Li et al. (Virtual simulation without physical robot)
- Subtle Divider Rule.
- Bottom Section: HOW OUR SYSTEM CLOSES THESE GAPS
  Col 1: 01. All-Onboard Edge AI (Direct answer to Mahmud)
  Col 2: 02. Direct Vision-to-Wheels (Direct answer to Tsitos)
  Col 3: 03. Physical Deployment & Safety (Direct answer to Li)
- Calm 2-tone palette: Navy, Gold, Charcoal. Zero traffic-light red/green.
"""

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_CONNECTOR

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"

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

    # If slide 6 does not exist yet, add it using Layout 1
    if len(prs.slides) < 6:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[5]

    # Theme colors — Strictly harmonized 2-tone palette
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_dark   = RGBColor(30, 41, 59)      # #1E293B High-Contrast Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_border = RGBColor(203, 213, 225)   # #CBD5E1 Subtle Slate
    c_muted  = RGBColor(100, 116, 139)   # #64748B Muted Slate

    # 1. Slide Title (28 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 1" and shape.has_text_frame:
            shape.left = Inches(0.92)
            shape.top = Inches(0.40)
            shape.width = Inches(11.50)
            shape.height = Inches(0.75)
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "04. LITERATURE REVIEW & RESEARCH GAPS", font_name="Calisto MT", size_pt=28, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 6
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Lit_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Top Section Label: Left-aligned Gold Eyebrow
    # Left=1.00", Top=1.20", Width=5.50", Height=0.28"
    tx_bench_lbl = slide.shapes.add_textbox(Inches(1.00), Inches(1.20), Inches(5.50), Inches(0.28))
    tx_bench_lbl.name = "Lit_Bench_Label"
    tf_lbl = tx_bench_lbl.text_frame
    tf_lbl.word_wrap = True
    tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
    p_lbl = tf_lbl.paragraphs[0]
    set_para(p_lbl, "BENCHMARK RESEARCH GAPS IN LITERATURE", font_name="Calisto MT", size_pt=12, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Top Section: 3 Benchmark Studies (Vertically paired with solutions below)
    # 3 Columns: Lefts = 1.00", 4.90", 8.80", Width = 3.53", Top = 1.48", Height = 1.90"
    lefts = [Inches(1.00), Inches(4.90), Inches(8.80)]
    col_w = Inches(3.53)
    bench_top = Inches(1.48)
    bench_h = Inches(1.90)

    studies = [
        {
            "author": "Mahmud et al. (2022)",
            "focus": "3D Deep Gesture Tracking",
            "method": "Kinect v2 3D skeleton + deep neural nets.",
            "gap": "Cloud/GPU Dependency: Relies on offboard computing clusters; vulnerable to network lag & Wi-Fi drops."
        },
        {
            "author": "Tsitos et al. (2022)",
            "focus": "Fast Reaching Intention (Robotic Arm)",
            "method": "Monocular depth camera + SVM on UR3 arm.",
            "gap": "No Mobile Navigation: Confined to a static tabletop; cannot drive on wheels or accept gesture navigation."
        },
        {
            "author": "Li et al. (2023)",
            "focus": "Intention-Aware Navigation",
            "method": "2D LiDAR + CNN in Isaac Sim simulator.",
            "gap": "Simulation Only: Never verified on physical robot hardware; lacks touchless human gesture steering."
        }
    ]

    for idx, s in enumerate(studies):
        box = slide.shapes.add_textbox(lefts[idx], bench_top, col_w, bench_h)
        box.name = f"Lit_Study_{idx}"
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.04)

        # Author & Year
        p_auth = tf.paragraphs[0]
        set_para(p_auth, s["author"], font_name="Calisto MT", size_pt=14, bold=True, color_rgb=c_navy, space_after_pt=1, align=PP_ALIGN.LEFT)

        # Focus / Scope
        p_foc = tf.add_paragraph()
        set_para(p_foc, s["focus"], font_name="Calisto MT", size_pt=11, italic=True, color_rgb=c_muted, space_after_pt=4, align=PP_ALIGN.LEFT)

        # Method
        p_met = tf.add_paragraph()
        p_met.space_after = Pt(3)
        p_met.line_spacing = 1.15
        p_met.alignment = PP_ALIGN.LEFT
        r_met_lbl = p_met.add_run()
        r_met_lbl.text = "• Method: "
        r_met_lbl.font.name = "Calisto MT"
        r_met_lbl.font.size = Pt(11.5)
        r_met_lbl.font.bold = True
        r_met_lbl.font.color.rgb = c_dark
        r_met_txt = p_met.add_run()
        r_met_txt.text = s["method"]
        r_met_txt.font.name = "Calisto MT"
        r_met_txt.font.size = Pt(11.5)
        r_met_txt.font.bold = False
        r_met_txt.font.color.rgb = c_body

        # Research Gap
        p_gap = tf.add_paragraph()
        p_gap.space_after = Pt(0)
        p_gap.line_spacing = 1.15
        p_gap.alignment = PP_ALIGN.LEFT
        r_gap_lbl = p_gap.add_run()
        r_gap_lbl.text = "• Gap: "
        r_gap_lbl.font.name = "Calisto MT"
        r_gap_lbl.font.size = Pt(11.5)
        r_gap_lbl.font.bold = True
        r_gap_lbl.font.color.rgb = c_dark
        r_gap_txt = p_gap.add_run()
        r_gap_txt.text = s["gap"]
        r_gap_txt.font.name = "Calisto MT"
        r_gap_txt.font.size = Pt(11.5)
        r_gap_txt.font.bold = False
        r_gap_txt.font.color.rgb = c_body

    # 4. Subtle Horizontal Divider Rule
    # Y = 3.55", spanning from X=1.00" to X=12.33"
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(1.00), Inches(3.55), Inches(12.33), Inches(3.55))
    line.name = "Lit_Divider_Line"
    line.line.color.rgb = c_border
    line.line.width = Pt(0.8)

    # 5. Bottom Section Label: Left-aligned Gold Eyebrow
    # Left=1.00", Top=3.75", Width=5.50", Height=0.28"
    tx_gap_lbl = slide.shapes.add_textbox(Inches(1.00), Inches(3.75), Inches(5.50), Inches(0.28))
    tx_gap_lbl.name = "Lit_Gap_Label"
    tf_gap = tx_gap_lbl.text_frame
    tf_gap.word_wrap = True
    tf_gap.margin_left = tf_gap.margin_right = tf_gap.margin_top = tf_gap.margin_bottom = 0
    p_gap_hdr = tf_gap.paragraphs[0]
    set_para(p_gap_hdr, "HOW OUR SYSTEM CLOSES THESE GAPS", font_name="Calisto MT", size_pt=12, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 6. Bottom Section: 3 Vertically Paired Solutions
    # Top = 4.08", Height = 1.95", Bottom = 6.03" (clean 0.72" margin above footer)
    gap_top = Inches(4.08)
    gap_h = Inches(1.95)

    gaps = [
        {
            "num": "01",
            "title": "All-Onboard Edge AI",
            "desc": "Executes 100% of vision AI directly on the robot (Raspberry Pi 5) with zero cloud lag, zero internet dependency, and zero Wi-Fi dropouts."
        },
        {
            "num": "02",
            "title": "Direct Vision-to-Wheels",
            "desc": "Bridges hand gestures directly to physical wheel motors in real time through an active visual-tracking camera gimbal and ROS 2 middleware."
        },
        {
            "num": "03",
            "title": "Physical Hardware & Safety",
            "desc": "Empirically validated on a physical robot with 2D LiDAR SLAM, continuous human tracking, and automatic ISO 15066 safety stops."
        }
    ]

    for idx, g in enumerate(gaps):
        box = slide.shapes.add_textbox(lefts[idx], gap_top, col_w, gap_h)
        box.name = f"Lit_Gap_{idx}"
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.04)

        # Title
        p_title = tf.paragraphs[0]
        p_title.text = f"{g['num']}.  {g['title']}"
        p_title.font.name = "Calisto MT"
        p_title.font.size = Pt(13.5)
        p_title.font.bold = True
        p_title.font.color.rgb = c_navy
        p_title.space_after = Pt(3)
        p_title.alignment = PP_ALIGN.LEFT

        # Description
        p_desc = tf.add_paragraph()
        set_para(p_desc, g["desc"], font_name="Calisto MT", size_pt=11.5, color_rgb=c_body, line_spacing=1.15, align=PP_ALIGN.LEFT)

    prs.save(PPTX_PATH)
    print(f"Slide 6 rebuilt with 1-to-1 paired layout in {PPTX_PATH}")

if __name__ == "__main__":
    main()
