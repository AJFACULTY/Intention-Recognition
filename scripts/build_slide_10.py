#!/usr/bin/env python3
"""
build_slide_10.py — Formal Academic Slide 10 (Vision Perception & Gesture AI Pipeline)
- 100% plain English, conversational and un-grillable.
- Left column: 6 structured points covering operator gating, MediaPipe skeletal tracking,
  distance invariance normalization, 19D feature engineering, and 1.2 ms MLP neural classification.
- Right column:
  - Top-left: Camera spatial zone HUD (isolating operator, blurring bystanders).
  - Right: 21-joint skeletal hand model (P0 to P20).
  - Bottom-left: The 6 recognized operational gesture commands.
- Ample clearance (>0.70" above footer bar at Y = 6.75").
- Dignified GCTU palette: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image, ImageOps

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
HUD_SRC = "write_up/figures/robot_spatial_zone_clean.jpg"
HUD_IMG = "write_up/figures/spatial_zone_framed.jpg"
HAND_SRC = "write_up/figures/real_hand_landmarks_annotated.png"
HAND_IMG = "write_up/figures/hand_landmarks_framed.jpg"

def prepare_images():
    """Frames the HUD and hand landmarks cleanly with subtle borders."""
    if os.path.exists(HUD_SRC):
        im_hud = Image.open(HUD_SRC)
        b_hud = ImageOps.expand(im_hud, border=2, fill=(203, 213, 225))
        b_hud.save(HUD_IMG, quality=95)

    if os.path.exists(HAND_SRC):
        im_hand = Image.open(HAND_SRC)
        if im_hand.mode == "RGBA":
            bg = Image.new("RGB", im_hand.size, (255, 255, 255))
            bg.paste(im_hand, mask=im_hand.split()[3])
            im_hand = bg
        bbox = im_hand.getbbox()
        crop_hand = im_hand.crop(bbox)
        b_hand = ImageOps.expand(crop_hand, border=2, fill=(203, 213, 225))
        b_hand.save(HAND_IMG, quality=95)
    print("Prepared framed vision images.")

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

    if len(prs.slides) < 10:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[9]

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
            set_para(p, "08. VISION PERCEPTION & GESTURE AI PIPELINE", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 10
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Vision_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Vision_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "OPERATOR ISOLATION, 21-POINT SKELETON TRACKING & 19D NEURAL CLASSIFIER", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured Vision & AI Points in Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.70))
    tx_left.name = "Vision_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    vision_points = [
        ("Operator Spatial Focus", "The camera strictly accepts commands from an operator centered in front of the robot, automatically blurring and ignoring passersby in the background."),
        ("21-Point Skeletal Tracking", "Once focused, MediaPipe extracts 21 finger and palm joint landmarks in 3D coordinates from the live video stream in real time."),
        ("Distance-Proof Scaling", "Joint coordinates are centered on the wrist and divided by palm width, ensuring gestures look identical whether the user stands 1 meter or 3 meters away."),
        ("19-D Feature Extraction", "Compresses the 21 joints into 19 geometric measurements: 5 finger curl angles, 5 fingertip distances, 4 spread angles, 3D thumb vector, and 2 palm angles."),
        ("Fast Neural Classifier", "A 4-layer neural network (MLP) evaluates the 19 features in just 1.2 ms on the Raspberry Pi 5 CPU, achieving 99.38% test accuracy."),
        ("6 Discrete Motion Commands", "Translates recognized hand poses into unambiguous motion intents: STOP (open palm), GO (point forward), LEFT, RIGHT, BACK, and FOLLOW.")
    ]

    for idx, (tag, desc) in enumerate(vision_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(vision_points) - 1 else 0)
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
    # 4A. Spatial Zone HUD (Top-Left of right half: Left: 6.95", Top: 1.38", Width: 3.30", Height: 2.48")
    if os.path.exists(HUD_IMG):
        pic_hud = slide.shapes.add_picture(
            HUD_IMG,
            Inches(6.95), Inches(1.38),
            width=Inches(3.30), height=Inches(2.48)
        )
        pic_hud.name = "Vision_HUD_Img"

        # Caption under HUD (Top: 3.90", Height: 0.35")
        tx_hud_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.90), Inches(3.30), Inches(0.35))
        tx_hud_cap.name = "Vision_HUD_Cap"
        tf_hud_cap = tx_hud_cap.text_frame
        tf_hud_cap.word_wrap = True
        tf_hud_cap.margin_left = tf_hud_cap.margin_right = tf_hud_cap.margin_top = tf_hud_cap.margin_bottom = 0
        p_hc = tf_hud_cap.paragraphs[0]
        set_para(p_hc, "Figure 3.4: Operator Acceptance HUD & Bystander Blur", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. 21-Joint Hand Landmark Model (Right of right half: Left: 10.45", Top: 1.38", Width: 2.15", Height: 4.10")
    if os.path.exists(HAND_IMG):
        pic_hand = slide.shapes.add_picture(
            HAND_IMG,
            Inches(10.45), Inches(1.38),
            width=Inches(2.15), height=Inches(4.10)
        )
        pic_hand.name = "Vision_Hand_Img"

        # Caption under Hand (Top: 5.52", Height: 0.40")
        tx_hand_cap = slide.shapes.add_textbox(Inches(10.45), Inches(5.52), Inches(2.15), Inches(0.40))
        tx_hand_cap.name = "Vision_Hand_Cap"
        tf_hand_cap = tx_hand_cap.text_frame
        tf_hand_cap.word_wrap = True
        tf_hand_cap.margin_left = tf_hand_cap.margin_right = tf_hand_cap.margin_top = tf_hand_cap.margin_bottom = 0
        p_hnc = tf_hand_cap.paragraphs[0]
        set_para(p_hnc, "Figure 3.5: 21-Joint 3D Hand Model", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4C. Summary Block of 6 Gestures (Bottom-Left of right half: Left: 6.95", Top: 4.35", Width: 3.40", Height: 1.65")
    tx_vocab = slide.shapes.add_textbox(Inches(6.95), Inches(4.35), Inches(3.40), Inches(1.65))
    tx_vocab.name = "Vision_Vocab_Text"
    tf_vocab = tx_vocab.text_frame
    tf_vocab.word_wrap = True
    tf_vocab.margin_left = tf_vocab.margin_right = tf_vocab.margin_top = tf_vocab.margin_bottom = 0

    p_vh = tf_vocab.paragraphs[0]
    set_para(p_vh, "CLASSIFIER VOCABULARY & BENCHMARKS:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=3)

    vocab_bullets = [
        ("Commands", "STOP, GO, LEFT, RIGHT, BACK, FOLLOW"),
        ("Inference Speed", "1.2 ms on Raspberry Pi 5 CPU (100x real-time)"),
        ("Model Accuracy", "99.38% test accuracy (6,000 verified samples)")
    ]

    for v_idx, (v_tag, v_desc) in enumerate(vocab_bullets):
        p_v = tf_vocab.add_paragraph()
        p_v.space_after = Pt(2 if v_idx < len(vocab_bullets) - 1 else 0)
        p_v.line_spacing = 1.12
        p_v.alignment = PP_ALIGN.LEFT

        r_vt = p_v.add_run()
        r_vt.text = f"• {v_tag}: "
        r_vt.font.name = "Calisto MT"
        r_vt.font.size = Pt(9.0)
        r_vt.font.bold = True
        r_vt.font.color.rgb = c_navy

        r_vd = p_v.add_run()
        r_vd.text = v_desc
        r_vd.font.name = "Calisto MT"
        r_vd.font.size = Pt(9.0)
        r_vd.font.bold = False
        r_vd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 10 successfully added and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
