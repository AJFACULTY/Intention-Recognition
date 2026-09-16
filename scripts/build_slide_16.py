#!/usr/bin/env python3
"""
build_slide_16.py — Full-Width High-Visibility Academic Slide 16 (Key References in IEEE Format)
Platform: Yahboom Micro-ROS Pi 5 Autonomous Mobile Robot
Thesis: GCTU BSc Computer Engineering Defense

Layout:
- Single full-width column (no split columns) for maximum readability on projection screens.
- IEEE Citation formatting with clear visual hierarchy:
  - Gold bold citation index [X]
  - Deep Navy bold author list
  - Charcoal italic paper/book title
  - Muted slate publication venue, dates, and official DOI / standards reference.
- All 7 primary core citations backing the literature review, safety standards, ROS 2 architecture, Nav2, and AI vision.
- Strict GCTU corporate color palette: Deep Navy (#002060), Gold (#B8860B), Charcoal (#1E293B), Muted Slate (#475569).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"

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

    # Ensure slide 16 exists
    if len(prs.slides) < 16:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[15]

    # Theme colors matching GCTU corporate palette
    c_navy   = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_dark   = RGBColor(30, 41, 59)      # #1E293B High-Contrast Charcoal
    c_gold   = RGBColor(184, 134, 11)    # #B8860B Accent Gold
    c_muted  = RGBColor(71, 85, 105)     # #475569 Slate Muted

    # 1. Slide Title (Single Line Fit at 24 pt Bold Navy)
    for shape in slide.shapes:
        if (shape.name == "Title 1" or shape.name == "PlaceHolder 1" or shape == slide.shapes.title) and shape.has_text_frame:
            shape.left = Inches(0.66)
            shape.top = Inches(0.35)
            shape.width = Inches(12.00)
            shape.height = Inches(0.60)
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "KEY REFERENCES (IEEE FORMAT)", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean all existing reference shapes on Slide 16
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Ref_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Ref_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "PRIMARY PEER-REVIEWED LITERATURE, ROBOTICS BENCHMARKS & INTERNATIONAL STANDARDS", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Single Full-Width Reference Container (No Split Columns, Clean Projection Visibility)
    tx_box = slide.shapes.add_textbox(Inches(0.85), Inches(1.35), Inches(11.63), Inches(5.25))
    tx_box.name = "Ref_FullWidth_Box"
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    references = [
        ("[1]", "A. Tsitos, M. Dagioglou, and T. Giannakopoulos",
         "Real-Time Feasibility of a Human Intention Method Evaluated Through a Competitive Human-Robot Reaching Game",
         "IEEE Transactions on Human-Machine Systems, vol. 52, no. 5, pp. 912–922, Oct. 2022. DOI: 10.1109/THMS.2022.3179574."),

        ("[2]", "J. A. Mahmud",
         "3D Gesture Recognition and Adaptation for Human–Robot Interaction",
         "IEEE Robotics and Automation Letters, vol. 7, no. 2, pp. 4831–4838, Apr. 2022. DOI: 10.1109/LRA.2022.3151406."),

        ("[3]", "Y. Li, H. Zhang, G. Yang, and S. Wang",
         "Safe and Efficient Motion Planning for Material Transportation Robots Considering Intention Prediction of Obstacles",
         "IEEE Access, vol. 11, pp. 24819–24831, Mar. 2023. DOI: 10.1109/ACCESS.2023.3256031."),

        ("[4]", "ISO/TS 15066:2016",
         "Robots and Robotic Devices — Collaborative Robots",
         "International Organization for Standardization (ISO), Technical Specification, Geneva, Switzerland, 2016."),

        ("[5]", "S. Macenski, T. Foote, B. Gerkey, C. Lalancette, and W. Woodall",
         "Robot Operating System 2: Design, Architecture, and Uses in the Wild",
         "Science Robotics, vol. 7, no. 66, Art. no. eabm6074, May 2022. DOI: 10.1126/scirobotics.abm6074."),

        ("[6]", "F. Zhang, V. Bazarevsky, A. Vakunov, A. Tkachenka, G. Sung, C. L. Chang, and M. Grundmann",
         "MediaPipe Hands: On-Device Real-Time Hand Tracking",
         "arXiv preprint arXiv:2006.10214, presented at CVPR Workshop on Computer Vision for AR/VR, 2020."),

        ("[7]", "S. Macenski, I. Jambrecic, A. Filippov, and C. Stiffler",
         "From the Ground Up: Building an Intelligent Mobile Robot with Nav2",
         "IEEE Robotics & Automation Magazine, vol. 30, no. 4, pp. 88–98, Dec. 2023. DOI: 10.1109/MRA.2023.3323060.")
    ]

    for idx, (num, authors, title, publication) in enumerate(references):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        p.line_spacing = 1.15
        p.alignment = PP_ALIGN.LEFT

        # IEEE Citation Bracket [X]
        r_num = p.add_run()
        r_num.text = f"{num} "
        r_num.font.name = "Calisto MT"
        r_num.font.size = Pt(11.5)
        r_num.font.bold = True
        r_num.font.color.rgb = c_gold

        # Authors
        r_auth = p.add_run()
        r_auth.text = f"{authors}, "
        r_auth.font.name = "Calisto MT"
        r_auth.font.size = Pt(11)
        r_auth.font.bold = True
        r_auth.font.color.rgb = c_navy

        # Paper Title in Quotes
        r_title = p.add_run()
        r_title.text = f'"{title}," '
        r_title.font.name = "Calisto MT"
        r_title.font.size = Pt(10.5)
        r_title.font.italic = True
        r_title.font.color.rgb = c_dark

        # Publication Venue & DOI
        r_pub = p.add_run()
        r_pub.text = publication
        r_pub.font.name = "Calisto MT"
        r_pub.font.size = Pt(10)
        r_pub.font.bold = False
        r_pub.font.color.rgb = c_muted

    # Save upgraded presentation
    prs.save(PPTX_PATH)
    print(f"Slide 16 (Single-Column IEEE References) successfully built and saved to {PPTX_PATH}!")

if __name__ == "__main__":
    main()
