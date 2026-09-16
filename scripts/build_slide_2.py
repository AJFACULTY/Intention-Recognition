#!/usr/bin/env python3
"""
build_slide_2.py — Upgraded Slide 2 (Presentation Outline)
- Removes Part I / Part II divisions for a seamless, unified flow.
- Maps directly to the 5 thesis chapters.
- Larger, highly readable font sizes: 18 pt bold headings, 14 pt bullet points.
- Consistent color palette: Primary Navy (#002060) and Slate/Charcoal (#1E293B).
"""

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

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
    slide = prs.slides[1]

    # Consistent Color System
    c_navy = RGBColor(0, 32, 96)      # #002060 GCTU Deep Navy

    # 1. Slide Title (28 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 3" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "PRESENTATION OUTLINE", font_name="Calisto MT", size_pt=28, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 4" and shape.has_text_frame:
            shape.text_frame.clear()

    # Remove previous custom outline boxes
    shapes_to_remove = [s for s in slide.shapes if s.name in ("Outline_Col1", "Outline_Col2", "Outline_Box")]
    for s in shapes_to_remove:
        sp = s._sp
        sp.getparent().remove(sp)

    # 2. Clean 6-Section Academic Outline at 24 pt (Without Sub-bullets)
    items = [
        "01. Introduction, Problem Statement & Objectives",
        "02. Literature Review & Critical Research Gaps",
        "03. System Architecture & 6-Phase Methodology",
        "04. Implementation & Intelligent Algorithms",
        "05. Experimental Results & ISO Safety Compliance",
        "06. Conclusion & Physical Demonstration Transition"
    ]

    txBox = slide.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.33), Inches(4.5))
    txBox.name = "Outline_Box"
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)

    for i, itm in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = itm
        p.font.name = "Calisto MT"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = c_navy
        p.space_after = Pt(18)
        p.line_spacing = 1.2
        p.alignment = PP_ALIGN.LEFT

    prs.save(PPTX_PATH)
    print(f"Slide 2 upgraded successfully in {PPTX_PATH} with 24 pt font and no sub-bullets.")

if __name__ == "__main__":
    main()
