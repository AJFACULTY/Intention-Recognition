#!/usr/bin/env python3
"""
build_slide_11.py — Formal Academic Slide 11 (Human Motion Prediction & Supervisory Control)
- 100% plain English, conversational and un-grillable.
- Left column: 6 structured points covering:
  1. Anticipating User Steps (LSTM path predictor, 1.0s history -> 0.5s forecast)
  2. Motorized Camera Tracking (2-DOF pan-tilt gimbal, active person centering)
  3. Central Software Brain (brain_node 5-state supervisory manager)
  4. Preventing Accidental Starts (5-frame temporal consensus filter)
  5. Safe Distance Buffer (0.8m to 1.5m following buffer, stop on approach)
  6. Instant Laser Safety Override (twist_mux priority preemption, 0.36m halt in 5ms)
- Right column:
  - Top: AI Human Motion Prediction plot (lstm_path_prediction_clean.png)
  - Bottom-Left: 2-Axis Motorized Camera Head (camera_gimbal_framed.jpg)
  - Bottom-Right: Supervisory Safety Interlocks callout block
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
LSTM_IMG = "write_up/figures/lstm_path_prediction_clean.png"
GIMBAL_SRC = "write_up/figures/camera_gimbal_cropped.png"
GIMBAL_IMG = "write_up/figures/camera_gimbal_framed.jpg"

def prepare_images():
    """Frames the gimbal image cleanly with subtle border and white background."""
    if os.path.exists(GIMBAL_SRC):
        im_gimbal = Image.open(GIMBAL_SRC)
        if im_gimbal.mode != "RGB":
            bg = Image.new("RGB", im_gimbal.size, (255, 255, 255))
            if "A" in im_gimbal.mode:
                bg.paste(im_gimbal, mask=im_gimbal.split()[-1])
            else:
                bg.paste(im_gimbal)
            im_gimbal = bg
        b_gimbal = ImageOps.expand(im_gimbal, border=2, fill=(203, 213, 225))
        b_gimbal.save(GIMBAL_IMG, quality=95)
        print("Prepared framed camera gimbal image.")

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

    if len(prs.slides) < 11:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[10]

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
            set_para(p, "09. HUMAN MOTION PREDICTION & SUPERVISORY CONTROL", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 11
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Control_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Control_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "HOW THE ROBOT ANTICIPATES USER PATHS, TRACKS WITH ITS CAMERA, AND STAYS SAFE", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured Control & Prediction Points in Pure Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.70))
    tx_left.name = "Control_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    control_points = [
        ("Anticipating User Steps", "The robot tracks the person's walking path over the past 1 second (30 camera frames) and uses an AI model to predict where they will step 0.5 seconds ahead, preventing jerky turns or delayed following."),
        ("Motorized Camera Tracking", "A 2-axis motorized camera head pans left/right and tilts up/down automatically, keeping the interacting person centered in view even while the robot chassis is turning or braking."),
        ("Central Software Brain", "A master controller (brain_node) coordinates all actions through distinct operational stages: Standing By, Confirming Command, Driving, Following User, and Safety Stop."),
        ("Preventing Accidental Starts", "To stop accidental hand waves or brief gestures from moving the robot, every command must be held consistently for at least 5 camera frames before motors turn."),
        ("Safe Distance Buffer", "When following a walking user, the robot automatically stays between 0.8 and 1.5 meters away; if the person stops or steps closer than 0.8 meters, it halts immediately."),
        ("Instant Laser Safety Override", "The 360° laser distance sensor constantly scans the surroundings; if an obstacle or person enters within 0.36 meters, motor power cuts in 5 milliseconds, overriding all AI.")
    ]

    for idx, (tag, desc) in enumerate(control_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(control_points) - 1 else 0)
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
    # 4A. LSTM Path Prediction Plot (Top: Left: 6.95", Top: 1.38", Width: 5.50", Height: 2.05")
    if os.path.exists(LSTM_IMG):
        pic_lstm = slide.shapes.add_picture(
            LSTM_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(5.50), height=Inches(2.05)
        )
        pic_lstm.name = "Control_LSTM_Img"

        # Caption under LSTM plot (Top: 3.46", Height: 0.28")
        tx_lstm_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.46), Inches(5.50), Inches(0.28))
        tx_lstm_cap.name = "Control_LSTM_Cap"
        tf_lstm_cap = tx_lstm_cap.text_frame
        tf_lstm_cap.word_wrap = True
        tf_lstm_cap.margin_left = tf_lstm_cap.margin_right = tf_lstm_cap.margin_top = tf_lstm_cap.margin_bottom = 0
        p_lc = tf_lstm_cap.paragraphs[0]
        set_para(p_lc, "Figure 3.6: AI Human Motion Prediction (Blue = Past 1.0s Walk, Green = Actual Steps, Red = AI Forecast)", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. 2-Axis Motorized Camera Gimbal (Bottom-Left of right half: Left: 6.95", Top: 3.82", Width: 2.30", Height: 1.75")
    if os.path.exists(GIMBAL_IMG):
        pic_gimbal = slide.shapes.add_picture(
            GIMBAL_IMG,
            Inches(6.95), Inches(3.82),
            width=Inches(2.30), height=Inches(1.75)
        )
        pic_gimbal.name = "Control_Gimbal_Img"

        # Caption under Gimbal (Top: 5.60", Height: 0.35")
        tx_gimbal_cap = slide.shapes.add_textbox(Inches(6.95), Inches(5.60), Inches(2.30), Inches(0.35))
        tx_gimbal_cap.name = "Control_Gimbal_Cap"
        tf_gimbal_cap = tx_gimbal_cap.text_frame
        tf_gimbal_cap.word_wrap = True
        tf_gimbal_cap.margin_left = tf_gimbal_cap.margin_right = tf_gimbal_cap.margin_top = tf_gimbal_cap.margin_bottom = 0
        p_gc = tf_gimbal_cap.paragraphs[0]
        set_para(p_gc, "Figure 3.7: 2-Axis Motorized Camera Head", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4C. Summary Block of Supervisory Safety Interlocks (Bottom-Right of right half: Left: 9.45", Top: 3.82", Width: 3.00", Height: 2.15")
    tx_safety = slide.shapes.add_textbox(Inches(9.45), Inches(3.82), Inches(3.00), Inches(2.15))
    tx_safety.name = "Control_Safety_Text"
    tf_safety = tx_safety.text_frame
    tf_safety.word_wrap = True
    tf_safety.margin_left = tf_safety.margin_right = tf_safety.margin_top = tf_safety.margin_bottom = 0

    p_sh = tf_safety.paragraphs[0]
    set_para(p_sh, "SUPERVISORY SAFETY INTERLOCKS:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    safety_bullets = [
        ("4 Safe Modes", "Standby → Confirming → Driving → Safety Halt"),
        ("5-Frame Filter", "Requires 5 matching frames to stop accidental wave triggers"),
        ("Safe Gap (0.8m)", "Stops immediately if user approaches closer than 0.8 meters"),
        ("Instant E-Stop", "Laser barrier (< 0.36m) cuts motor power within 5 milliseconds")
    ]

    for s_idx, (s_tag, s_desc) in enumerate(safety_bullets):
        p_s = tf_safety.add_paragraph()
        p_s.space_after = Pt(2.5 if s_idx < len(safety_bullets) - 1 else 0)
        p_s.line_spacing = 1.12
        p_s.alignment = PP_ALIGN.LEFT

        r_st = p_s.add_run()
        r_st.text = f"• {s_tag}: "
        r_st.font.name = "Calisto MT"
        r_st.font.size = Pt(8.8)
        r_st.font.bold = True
        r_st.font.color.rgb = c_navy

        r_sd = p_s.add_run()
        r_sd.text = s_desc
        r_sd.font.name = "Calisto MT"
        r_sd.font.size = Pt(8.8)
        r_sd.font.bold = False
        r_sd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 11 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
