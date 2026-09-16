#!/usr/bin/env python3
"""
build_slide_6.py — Formal Academic Slide 6 (Literature Review & Research Gaps)
- Full author and co-author names.
- Exact publication titles from thesis Chapter 2.
- Readable font size (10.5 pt body, 12 pt authors) with strict anti-crowding geometry.
- 4 academic fields per paper: Objective, Methodology, Research Gap, Project Resolution.
- 100% plain-English first-read clarity; calm 2-tone university palette.
"""

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"

def set_para(p, text, font_name="Calisto MT", size_pt=14, bold=False, italic=False, color_rgb=None, space_before_pt=0, space_after_pt=2, line_spacing=1.12, align=PP_ALIGN.LEFT):
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

def add_labeled_block(tf, label, content, c_label, c_content, size_pt=10.5, space_after_pt=4):
    p = tf.add_paragraph()
    p.space_after = Pt(space_after_pt)
    p.line_spacing = 1.12
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

    # Theme colors
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_dark   = RGBColor(30, 41, 59)      # #1E293B High-Contrast Charcoal
    c_body   = RGBColor(51, 65, 85)      # #334155 Slate Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_muted  = RGBColor(100, 116, 139)   # #64748B Muted Slate

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
            set_para(p, "LITERATURE REVIEW & RESEARCH GAPS", font_name="Calisto MT", size_pt=28, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 6
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Lit_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow
    # Left=0.90", Top=1.12", Width=11.50", Height=0.25"
    tx_sub = slide.shapes.add_textbox(Inches(0.90), Inches(1.12), Inches(11.50), Inches(0.25))
    tx_sub.name = "Lit_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "CRITICAL APPRAISAL OF CORE BENCHMARK STUDIES (THESIS CHAPTER 2)", font_name="Calisto MT", size_pt=11.5, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Three Columns for Benchmark Papers
    # Lefts: 0.90", 4.90", 8.90", Width: 3.53", Top: 1.38", Height: 4.80"
    lefts = [Inches(0.90), Inches(4.90), Inches(8.90)]
    col_w = Inches(3.53)
    col_top = Inches(1.38)
    col_h = Inches(4.80)

    papers = [
        {
            "authors": "Athanasios Tsitos, Maria Dagioglou & Theodoros Giannakopoulos (2022)",
            "title": "Real-Time Feasibility of a Human Intention Method Evaluated Through a Competitive Human-Robot Reaching Game",
            "objective": "Predict human reaching intent early to guide robot arm trajectories within a 150 ms reaction threshold.",
            "method": "Tracked hand movements with a depth camera and trained machine learning (SVM) to guide a robot arm.",
            "gap": "Confined to a static desk — lacks mobile base movement and provides no explicit hand gesture command channel.",
            "resolution": "Direct vision-to-wheels coupling for mobile navigation guided by 6 touchless hand gestures."
        },
        {
            "authors": "Jubayer Al Mahmud (2022)",
            "title": "3D Gesture Recognition and Adaptation for Human–Robot Interaction",
            "objective": "Classify 3D pointing and dynamic hand gestures in real time to guide robot interaction across age groups.",
            "method": "Tracked full-body joints using a Kinect sensor and trained deep learning models on 3,600 gestures.",
            "gap": "Relies on heavy cloud / GPU computing clusters; vulnerable to network lag (>200 ms) and connection drops.",
            "resolution": "Executes 100% of vision AI directly onboard a low-cost Raspberry Pi 5 with zero cloud dependency."
        },
        {
            "authors": "Y. Li, H. Zhang, Guang Yang & Shuoyu Wang (2023)",
            "title": "Safe and Efficient Motion Planning for Material Transportation Robots Considering Intention Prediction of Obstacles",
            "objective": "Plan collision-free mobile robot paths by predicting whether human workers will clear the hallway.",
            "method": "Fused LiDAR and camera vision to predict worker paths and adjust navigation maps in a simulator.",
            "gap": "Tested only in computer simulation — never validated on physical robot hardware; lacks touchless gesture control.",
            "resolution": "Physically validated on a real mobile robot with 2D LiDAR SLAM, active visual servoing, and ISO safety stops."
        }
    ]

    for idx, p in enumerate(papers):
        box = slide.shapes.add_textbox(lefts[idx], col_top, col_w, col_h)
        box.name = f"Lit_Paper_{idx}"
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.02)

        # 1. Author Full Names & Year (11.5 pt Bold Navy)
        p_auth = tf.paragraphs[0]
        set_para(p_auth, p["authors"], font_name="Calisto MT", size_pt=11.5, bold=True, color_rgb=c_navy, space_after_pt=1, line_spacing=1.10, align=PP_ALIGN.LEFT)

        # 2. Actual Paper Title in Quotes (9.5 pt Italic Slate)
        p_title = tf.add_paragraph()
        set_para(p_title, f'"{p["title"]}"', font_name="Calisto MT", size_pt=9.5, italic=True, color_rgb=c_muted, space_after_pt=5, line_spacing=1.10, align=PP_ALIGN.LEFT)

        # 3. Objective (10.5 pt)
        add_labeled_block(tf, "Objective", p["objective"], c_dark, c_body, size_pt=10.5, space_after_pt=4)

        # 4. Methodology (10.5 pt)
        add_labeled_block(tf, "Methodology", p["method"], c_dark, c_body, size_pt=10.5, space_after_pt=4)

        # 5. Research Gap (10.5 pt)
        add_labeled_block(tf, "Research Gap", p["gap"], c_dark, c_body, size_pt=10.5, space_after_pt=5)

        # 6. Project Resolution (10.5 pt Bold Navy Header)
        p_sol = tf.add_paragraph()
        p_sol.space_after = Pt(0)
        p_sol.line_spacing = 1.12
        p_sol.alignment = PP_ALIGN.LEFT

        r_sol_lbl = p_sol.add_run()
        r_sol_lbl.text = "• Project Resolution: "
        r_sol_lbl.font.name = "Calisto MT"
        r_sol_lbl.font.size = Pt(10.5)
        r_sol_lbl.font.bold = True
        r_sol_lbl.font.color.rgb = c_navy

        r_sol_txt = p_sol.add_run()
        r_sol_txt.text = p["resolution"]
        r_sol_txt.font.name = "Calisto MT"
        r_sol_txt.font.size = Pt(10.5)
        r_sol_txt.font.bold = False
        r_sol_txt.font.color.rgb = c_dark

    prs.save(PPTX_PATH)
    print(f"Slide 6 rebuilt with actual paper titles and 10.5 pt font in {PPTX_PATH}")

if __name__ == "__main__":
    main()
