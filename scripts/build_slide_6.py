#!/usr/bin/env python3
"""
build_slide_6.py — Comprehensive, Structured Slide 6 (Literature Review & Gaps)
Captures for each of the 3 core benchmark papers:
1. Full Author Names & Year
2. Core Objective
3. Methodology
4. Research Gap
5. How This Project Resolves the Gap
Clean, highly readable 3-column layout with generous vertical runway.
Strict 2-tone palette (Navy, Gold, Charcoal). Zero traffic-light red/green.
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

def add_labeled_block(tf, label, content, c_label, c_content, size_pt=11, space_after_pt=6):
    p = tf.add_paragraph()
    p.space_after = Pt(space_after_pt)
    p.line_spacing = 1.15
    p.alignment = PP_ALIGN.LEFT

    r_lbl = p.add_run()
    r_lbl.text = f"• {label}: "
    r_lbl.font.name = "Calisto MT"
    r_lbl.font.size = Pt(size_pt)
    r_lbl.font.bold = True
    r_lbl.font.color.rgb = c_label

    r_txt = p.add_run()
    r_txt.text = content
    r_txt.font.name = "Calisto MT"
    r_txt.font.size = Pt(size_pt)
    r_txt.font.bold = False
    r_txt.font.color.rgb = c_content

def main():
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 6:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[5]

    # Harmonious color palette
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_dark   = RGBColor(30, 41, 59)      # #1E293B High-Contrast Charcoal
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_muted  = RGBColor(100, 116, 139)   # #64748B Muted Slate
    c_border = RGBColor(203, 213, 225)   # #CBD5E1 Subtle Slate

    # 1. Slide Title (28 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 1" and shape.has_text_frame:
            shape.left = Inches(0.92)
            shape.top = Inches(0.35)
            shape.width = Inches(11.50)
            shape.height = Inches(0.70)
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

    # 2. Section Subhead: Left-aligned Gold Eyebrow
    # Left=0.90", Top=1.15", Width=11.50", Height=0.28"
    tx_sub = slide.shapes.add_textbox(Inches(0.90), Inches(1.15), Inches(11.50), Inches(0.28))
    tx_sub.name = "Lit_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "CRITICAL APPRAISAL OF CORE BENCHMARK STUDIES (THESIS CHAPTER 2)", font_name="Calisto MT", size_pt=11.5, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Three Comprehensive Columns for the Benchmark Papers
    # Lefts: 0.90", 4.90", 8.90", Width: 3.53", Top: 1.45", Height: 4.65"
    # Bottom = 1.45 + 4.65 = 6.10" (leaves 0.65" whitespace above footer logo)
    lefts = [Inches(0.90), Inches(4.90), Inches(8.90)]
    col_w = Inches(3.53)
    col_top = Inches(1.45)
    col_h = Inches(4.65)

    papers = [
        {
            "author": "Athanasios Tsitos et al. (2022)",
            "paper": "Competitive Reaching Intention Game",
            "objective": "Predict human reaching intent early to govern robot arm trajectories within a 150 ms reaction threshold.",
            "method": "RGB-D camera + OpenPose wrist tracking + SVM / Decision Trees on an industrial 6-DOF UR3 robotic arm.",
            "gap": "Confined to a static desk — lacks mobile base movement and provides no explicit hand gesture command channel.",
            "solution": "Bridges intention directly to mobile wheels via 6 explicit hand gestures and autonomous navigation."
        },
        {
            "author": "J. A. Mahmud et al. (2022)",
            "paper": "3D Gesture Recognition & Adaptation",
            "objective": "Classify 3D pointing and dynamic gestures in real time to guide robot interaction across age groups.",
            "method": "Kinect v2 depth sensor + 3D skeletal normalization + CNN / SVM classifiers on 3,600 gesture samples.",
            "gap": "Relies on heavy cloud / GPU computers; vulnerable to network latency (>200 ms) and connection dropouts.",
            "solution": "Executes 100% of vision AI directly onboard a low-cost Raspberry Pi 5 with zero cloud dependency."
        },
        {
            "author": "Y. Li & H. Zhang et al. (2023)",
            "paper": "Intention-Aware Motion Planning",
            "objective": "Plan mobile robot paths around moving site workers by predicting whether obstacles will clear the hallway.",
            "method": "2D LiDAR + camera object detection + CNN intention prediction integrated into ROS 2 Nav2 in Isaac Sim.",
            "gap": "Tested only in computer simulation — unverified on real physical robot hardware; lacks touchless gesture control.",
            "solution": "Physically deployed on a real mobile robot with 2D LiDAR SLAM, active visual servoing, and ISO 15066 safety stops."
        }
    ]

    for idx, p in enumerate(papers):
        box = slide.shapes.add_textbox(lefts[idx], col_top, col_w, col_h)
        box.name = f"Lit_Paper_{idx}"
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.02)

        # 1. Author Full Name & Year
        p_auth = tf.paragraphs[0]
        set_para(p_auth, p["author"], font_name="Calisto MT", size_pt=13.5, bold=True, color_rgb=c_navy, space_after_pt=1, align=PP_ALIGN.LEFT)

        # 2. Paper Focus / Subtitle
        p_focus = tf.add_paragraph()
        set_para(p_focus, p["paper"], font_name="Calisto MT", size_pt=10.5, italic=True, color_rgb=c_muted, space_after_pt=6, align=PP_ALIGN.LEFT)

        # 3. Objective
        add_labeled_block(tf, "Objective", p["objective"], c_dark, c_body, size_pt=10.8, space_after_pt=5)

        # 4. Methodology
        add_labeled_block(tf, "Method", p["method"], c_dark, c_body, size_pt=10.8, space_after_pt=5)

        # 5. Research Gap
        add_labeled_block(tf, "Research Gap", p["gap"], c_dark, c_body, size_pt=10.8, space_after_pt=7)

        # 6. How Our Work Solves It (Highlight)
        p_sol = tf.add_paragraph()
        p_sol.space_after = Pt(0)
        p_sol.line_spacing = 1.15
        p_sol.alignment = PP_ALIGN.LEFT

        r_sol_lbl = p_sol.add_run()
        r_sol_lbl.text = "👉 Our Solution: "
        r_sol_lbl.font.name = "Calisto MT"
        r_sol_lbl.font.size = Pt(10.8)
        r_sol_lbl.font.bold = True
        r_sol_lbl.font.color.rgb = c_navy

        r_sol_txt = p_sol.add_run()
        r_sol_txt.text = p["solution"]
        r_sol_txt.font.name = "Calisto MT"
        r_sol_txt.font.size = Pt(10.8)
        r_sol_txt.font.bold = False
        r_sol_txt.font.color.rgb = c_dark

    prs.save(PPTX_PATH)
    print(f"Slide 6 rebuilt with comprehensive literature appraisal in {PPTX_PATH}")

if __name__ == "__main__":
    main()
