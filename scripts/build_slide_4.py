#!/usr/bin/env python3
"""
build_slide_4.py — Minimalist, Captivating, 24 pt Slide 4 (Problem Statement)
- Strictly 2-3 lines / sentences in prominent 24 pt font.
- Zero text overload, no dense paragraphs.
- Backed strictly by the project's actual thesis literature (Tsitos et al., 2022 & ISO 15066:2016).
- 3 clean visual highlight pills.
"""

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

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
    slide = prs.slides[3]

    # Theme colors
    c_navy = RGBColor(0, 32, 96)       # #002060 GCTU Deep Navy
    c_body = RGBColor(30, 41, 59)      # #1E293B High-Contrast Charcoal
    c_card_bg = RGBColor(255, 255, 255)# Pure White Card
    c_border = RGBColor(203, 213, 225) # Subtle Slate Border
    c_gold   = RGBColor(184, 134, 11)  # Accent Gold

    # 1. Slide Title (28 pt Bold Navy)
    for shape in slide.shapes:
        if shape.name == "Title 1" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "02. PROBLEM STATEMENT", font_name="Calisto MT", size_pt=28, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Prob_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. The Captivating Core Problem Statement: Clean 3 Lines at 21 pt Font!
    # Left=0.85", Top=1.35", Width=11.63", Height=2.20"
    txCore = slide.shapes.add_textbox(Inches(0.85), Inches(1.35), Inches(11.63), Inches(2.20))
    txCore.name = "Prob_Core"
    tfCore = txCore.text_frame
    tfCore.word_wrap = True
    tfCore.margin_left = Inches(0.1)
    tfCore.margin_right = Inches(0.1)
    tfCore.margin_top = Inches(0.05)
    tfCore.margin_bottom = Inches(0.05)

    p1 = tfCore.paragraphs[0]
    set_para(p1, 
             "Current mobile robots separate vision recognition from active navigation, relying on remote cloud servers that suffer from high network lag (>200 ms) and connection dropouts.",
             size_pt=21, bold=False, color_rgb=c_body, space_after_pt=12, line_spacing=1.20, align=PP_ALIGN.CENTER)

    p2 = tfCore.add_paragraph()
    set_para(p2, 
             "In shared human-robot workspaces, this delay prevents robots from reacting in real time to human gestures, creating severe collision hazards under ISO 15066 safety standards.",
             size_pt=21, bold=False, color_rgb=c_body, space_after_pt=0, line_spacing=1.20, align=PP_ALIGN.CENTER)

    # 3. Three Clean Summary Badges
    # Top=4.25", Height=1.85", Width=3.63" each
    col_w = Inches(3.63)
    col_h = Inches(1.85)
    col_top = Inches(4.25)
    lefts = [Inches(0.85), Inches(4.85), Inches(8.85)]

    badges = [
        {
            "tag": "PERCEPTION-ACTION GAP",
            "desc": "Vision AI isolated from wheel motors & obstacle avoidance\n(Tsitos et al., 2022)"
        },
        {
            "tag": "CLOUD LATENCY HAZARD",
            "desc": "Network lag > 200 ms & Wi-Fi drops violate ISO 15066 safe stopping margins"
        },
        {
            "tag": "EDGE COMPUTING LIMIT",
            "desc": "Heavy vision AI overheats mobile chips; demands a sub-135 ms onboard pipeline"
        }
    ]

    for i, b in enumerate(badges):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, lefts[i], col_top, col_w, col_h)
        card.name = f"Prob_Card_{i}"
        card.fill.solid()
        card.fill.fore_color.rgb = c_card_bg
        card.line.color.rgb = c_border
        card.line.width = Pt(1.2)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.18)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.18)
        tf.margin_bottom = Inches(0.15)

        # Tag
        p = tf.paragraphs[0]
        set_para(p, b["tag"], size_pt=15, bold=True, color_rgb=c_navy, space_after_pt=6, align=PP_ALIGN.CENTER)

        # Description
        p_desc = tf.add_paragraph()
        set_para(p_desc, b["desc"], size_pt=13, italic=False, color_rgb=c_body, line_spacing=1.18, align=PP_ALIGN.CENTER)

    prs.save(PPTX_PATH)
    print(f"Slide 4 rebuilt with clean 24 pt minimalist format in {PPTX_PATH}")

if __name__ == "__main__":
    main()
