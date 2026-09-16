#!/usr/bin/env python3
"""
build_slide_15.py — Formal Academic Slide 15 (Conclusion, Limitations & Recommendations)
- Title: 13. CONCLUSION, LIMITATIONS & RECOMMENDATIONS
- Eyebrow: PROJECT CONTRIBUTIONS, TECHNICAL LIMITATIONS, AND FUTURE WORK
- 100% plain English, reduced text, concise and scannable on first read.
- Completely stripped of any hint of demo.
- Left column:
  - Part A: Key Research Conclusions (3 punchy points)
  - Part B: Technical Limitations of the Study (3 honest points)
- Right column:
  - Top-Left: High-resolution framed photo of physical robot (assembled_demo_framed.jpg)
  - Top-Right: Project Impact & Reach block
  - Bottom: Recommendations for Future Work (4 actionable points)
- Ample clearance (>0.70" above footer bar at Y = 6.75", bottom <= 6.02").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
ROBOT_SRC = "write_up/figures/assembled_robot_real.jpg"
ROBOT_IMG = "write_up/figures/assembled_demo_framed.jpg"

def prepare_images():
    """Prepares and frames the physical robot showcase photo."""
    if os.path.exists(ROBOT_SRC):
        im = Image.open(ROBOT_SRC)
        crop_im = im.crop((240, 120, 1080, 780))
        framed = ImageOps.expand(crop_im, border=2, fill=(203, 213, 225))
        framed.save(ROBOT_IMG, quality=95)
        print("Prepared framed demo robot image.")

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

    if len(prs.slides) < 15:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[14]

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
            set_para(p, "13. CONCLUSION, LIMITATIONS & RECOMMENDATIONS", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 15
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Conclusion_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Conclusion_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "PROJECT CONTRIBUTIONS, TECHNICAL LIMITATIONS, AND RECOMMENDATIONS FOR FUTURE WORK", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: Conclusions (Top) & Limitations (Bottom)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.65))
    tx_left.name = "Conclusion_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    # Part A: Conclusions
    p_ch = tf_left.paragraphs[0]
    set_para(p_ch, "KEY RESEARCH CONCLUSIONS:", font_name="Calisto MT", size_pt=10, bold=True, color_rgb=c_gold, space_after_pt=3)

    conclusions = [
        ("Complete Edge Autonomy", "AI vision, gesture recognition, human tracking, and SLAM execute 100% onboard the Raspberry Pi 5 without clouds or external GPUs."),
        ("High Real-World Accuracy", "Achieved 99.38% lab test accuracy and 96.67% physical driving success across 180 mobile trials in the laboratory."),
        ("Certified Collaborative Safety", "132 ms total response time and 98 ms physical braking fully satisfy ISO 15066 safety standards for human-robot shared spaces.")
    ]

    for c_idx, (c_tag, c_desc) in enumerate(conclusions):
        p = tf_left.add_paragraph()
        p.space_after = Pt(5)
        p.line_spacing = 1.13
        p.alignment = PP_ALIGN.LEFT

        r_tag = p.add_run()
        r_tag.text = f"• {c_tag}: "
        r_tag.font.name = "Calisto MT"
        r_tag.font.size = Pt(10)
        r_tag.font.bold = True
        r_tag.font.color.rgb = c_navy

        r_desc = p.add_run()
        r_desc.text = c_desc
        r_desc.font.name = "Calisto MT"
        r_desc.font.size = Pt(10)
        r_desc.font.bold = False
        r_desc.font.color.rgb = c_body

    # Part B: Limitations
    p_lh = tf_left.add_paragraph()
    p_lh.space_before = Pt(8)
    set_para(p_lh, "TECHNICAL LIMITATIONS OF THE STUDY:", font_name="Calisto MT", size_pt=10, bold=True, color_rgb=c_gold, space_after_pt=3)

    limitations = [
        ("Single Indoor Environment", "Evaluated in a single research lab; extreme direct sunlight washout and transparent glass partitions were not tested."),
        ("Edge CPU Compute Headroom", "Running continuous facial recognition alongside hand and person tracking saturated the 4-core CPU, requiring face ID to run offline."),
        ("Evaluation Cohort Size", "Physical driving trials involved 3 participants across 180 runs; broader demographic testing across diverse hand shapes is recommended.")
    ]

    for l_idx, (l_tag, l_desc) in enumerate(limitations):
        p = tf_left.add_paragraph()
        p.space_after = Pt(5 if l_idx < len(limitations) - 1 else 0)
        p.line_spacing = 1.13
        p.alignment = PP_ALIGN.LEFT

        r_tag = p.add_run()
        r_tag.text = f"• {l_tag}: "
        r_tag.font.name = "Calisto MT"
        r_tag.font.size = Pt(10)
        r_tag.font.bold = True
        r_tag.font.color.rgb = c_navy

        r_desc = p.add_run()
        r_desc.text = l_desc
        r_desc.font.name = "Calisto MT"
        r_desc.font.size = Pt(10)
        r_desc.font.bold = False
        r_desc.font.color.rgb = c_body

    # 4. Right Column Visuals
    # 4A. Robot Showcase Photo (Top-Left: Left: 6.95", Top: 1.38", Width: 2.65", Height: 2.05")
    if os.path.exists(ROBOT_IMG):
        pic_robot = slide.shapes.add_picture(
            ROBOT_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(2.65), height=Inches(2.05)
        )
        pic_robot.name = "Conclusion_Robot_Img"

        # Caption under Photo (Top: 3.46", Height: 0.22")
        tx_pic_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.46), Inches(2.65), Inches(0.22))
        tx_pic_cap.name = "Conclusion_Robot_Cap"
        tf_pic_cap = tx_pic_cap.text_frame
        tf_pic_cap.word_wrap = True
        tf_pic_cap.margin_left = tf_pic_cap.margin_right = tf_pic_cap.margin_top = tf_pic_cap.margin_bottom = 0
        p_rc = tf_pic_cap.paragraphs[0]
        set_para(p_rc, "Figure 5.1: Fully Integrated Mobile Robot", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. Project Impact Box (Top-Right: Left: 9.80", Top: 1.38", Width: 2.65", Height: 2.25")
    tx_impact = slide.shapes.add_textbox(Inches(9.80), Inches(1.38), Inches(2.65), Inches(2.25))
    tx_impact.name = "Conclusion_Milestones_Text"
    tf_impact = tx_impact.text_frame
    tf_impact.word_wrap = True
    tf_impact.margin_left = tf_impact.margin_right = tf_impact.margin_top = tf_impact.margin_bottom = 0

    p_ih = tf_impact.paragraphs[0]
    set_para(p_ih, "PROJECT IMPACT & REACH:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    impacts = [
        ("Zero Cloud Dependency", "Complete privacy, security, and offline field reliability"),
        ("Low-Cost Platform", "Accessible edge robotics under modest computing budgets"),
        ("Industry Standards", "100% compliant with ISO 15066 and ROS REP-103/105")
    ]

    for i_idx, (i_tag, i_desc) in enumerate(impacts):
        p_i = tf_impact.add_paragraph()
        p_i.space_after = Pt(4 if i_idx < len(impacts) - 1 else 0)
        p_i.line_spacing = 1.12
        p_i.alignment = PP_ALIGN.LEFT

        r_it = p_i.add_run()
        r_it.text = f"• {i_tag}: "
        r_it.font.name = "Calisto MT"
        r_it.font.size = Pt(8.8)
        r_it.font.bold = True
        r_it.font.color.rgb = c_navy

        r_id = p_i.add_run()
        r_id.text = i_desc
        r_id.font.name = "Calisto MT"
        r_id.font.size = Pt(8.8)
        r_id.font.bold = False
        r_id.font.color.rgb = c_body

    # 4C. Recommendations for Future Work Box (Bottom: Left: 6.95", Top: 3.75", Width: 5.50", Height: 2.25")
    tx_recom = slide.shapes.add_textbox(Inches(6.95), Inches(3.75), Inches(5.50), Inches(2.25))
    tx_recom.name = "Conclusion_Demo_Text"
    tf_recom = tx_recom.text_frame
    tf_recom.word_wrap = True
    tf_recom.margin_left = tf_recom.margin_right = tf_recom.margin_top = tf_recom.margin_bottom = 0

    p_rh = tf_recom.paragraphs[0]
    set_para(p_rh, "RECOMMENDATIONS FOR FUTURE WORK:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    recommendations = [
        ("Edge NPU Acceleration", "Add an M.2 Neural Processing Unit (Hailo-8) to run face recognition, hand gestures, and body tracking concurrently at 30 FPS."),
        ("Dual-Mode Navigation", "Implement human-led mapping in unknown areas ('Follow-to-Map'), and autonomous semantic waypoint dispatch in mapped spaces."),
        ("High-Speed PCIe NVMe Storage", "Equip the Pi 5 with an NVMe SSD to record full-rate video streams and sensor logs without SD card bottlenecks."),
        ("Multi-Sensor Redundancy", "Add ultrasonic sonar or depth cameras to detect transparent glass walls and low obstacles below the 2D LiDAR plane.")
    ]

    for r_idx, (r_tag, r_desc) in enumerate(recommendations):
        p_r = tf_recom.add_paragraph()
        p_r.space_after = Pt(2.5 if r_idx < len(recommendations) - 1 else 0)
        p_r.line_spacing = 1.12
        p_r.alignment = PP_ALIGN.LEFT

        r_rt = p_r.add_run()
        r_rt.text = f"• {r_tag}: "
        r_rt.font.name = "Calisto MT"
        r_rt.font.size = Pt(8.8)
        r_rt.font.bold = True
        r_rt.font.color.rgb = c_navy

        r_rd = p_r.add_run()
        r_rd.text = r_desc
        r_rd.font.name = "Calisto MT"
        r_rd.font.size = Pt(8.8)
        r_rd.font.bold = False
        r_rd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 15 successfully updated in {PPTX_PATH}")

if __name__ == "__main__":
    main()
