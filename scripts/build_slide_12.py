#!/usr/bin/env python3
"""
build_slide_12.py — Formal Academic Slide 12 (Metric SLAM & Nav2 Autonomous Navigation)
- 100% plain English, conversational and un-grillable.
- Left column: 6 structured points covering:
  1. Laser Room Mapping (SLAM Toolbox 5cm grid resolution)
  2. Resolving Signal Conflicts (TF2 transform collision diagnosis & fix)
  3. Fixing Cornering Drift (wheel odometry yaw fusion correcting 45° hourglass defect)
  4. Self-Localization (AMCL particle filter scan matching)
  5. Safety Padding Costmaps (obstacle padding preventing edge collisions)
  6. Multi-Waypoint Autonomous Patrol (4-destination patrol with 15.5 cm MAE accuracy)
- Right column:
  - Top: Side-by-side comparison of initial drifted map vs final clean metric map
  - Bottom-Left: Multi-waypoint patrol trajectory map (P1 to P4) with preserved 1:1 aspect ratio
  - Bottom-Right: Autonomous patrol performance summary callout
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
DRIFT_IMG = "write_up/figures/room_map_drift_framed.png"
CLEAN_IMG = "write_up/figures/room_map_clean_framed.png"
PATROL_IMG = "write_up/figures/waypoint_patrol_clean.png"

def prepare_images():
    """Prepares and frames all images for Slide 12."""
    if os.path.exists("write_up/figures/room_map_20260810_0452.png"):
        im_d = Image.open("write_up/figures/room_map_20260810_0452.png").convert("RGB")
        b_d = ImageOps.expand(im_d, border=2, fill=(203, 213, 225))
        b_d.save(DRIFT_IMG, quality=95)

    if os.path.exists("write_up/figures/room_map_clean.png"):
        im_c = Image.open("write_up/figures/room_map_clean.png").convert("RGB")
        b_c = ImageOps.expand(im_c, border=2, fill=(203, 213, 225))
        b_c.save(CLEAN_IMG, quality=95)

    if os.path.exists("write_up/figures/multi_waypoint_patrol_empirical.png"):
        orig = Image.open("write_up/figures/multi_waypoint_patrol_empirical.png")
        crop_clean = orig.crop((95, 92, 1850, 2250))
        if crop_clean.mode != "RGB":
            bg = Image.new("RGB", crop_clean.size, (255, 255, 255))
            bg.paste(crop_clean, mask=crop_clean.split()[-1] if "A" in crop_clean.mode else None)
            crop_clean = bg
        b_clean = ImageOps.expand(crop_clean, border=2, fill=(203, 213, 225))
        b_clean.save(PATROL_IMG, quality=95)
    print("Prepared all framed navigation images.")

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

    if len(prs.slides) < 12:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[11]

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
            set_para(p, "10. METRIC SLAM & NAV2 AUTONOMOUS NAVIGATION", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 12
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Nav_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Nav_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "HOW THE ROBOT MAPS INDOOR ROOMS, FIXES SENSOR DRIFT, AND PATROLS AUTONOMOUSLY", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: 6 Structured SLAM & Navigation Points in Pure Plain English (11 pt)
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(5.85), Inches(4.70))
    tx_left.name = "Nav_Points_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    nav_points = [
        ("Laser Room Mapping", "As the robot is steered through the room, its 360° laser distance sensor fires 12.5 times a second to build an exact 2D floor plan with 5-centimeter grid accuracy."),
        ("Resolving Signal Conflicts", "Early mapping tests dropped laser scans because two internal programs reported starting locations at once. Designating the motion tracker (EKF) as the sole authority fixed this immediately."),
        ("Fixing Cornering Drift", "During turns, early maps twisted into distorted hourglass shapes because the compass drifted. Merging wheel rotation with compass readings completely eliminated corner distortion, producing straight walls."),
        ("Self-Localization (AMCL)", "Once the map is saved, the robot constantly compares live laser scans against the map to know its exact physical coordinates (X, Y, and heading angle) within centimeters."),
        ("Safety Padding Costmaps", "The navigation software automatically inflates a safety padding cushion around all walls and furniture, preventing the robot from cutting corners too close or bumping table legs."),
        ("Multi-Waypoint Autonomous Patrol", "Given a sequence of room destinations (Dock → Central Hub → North Corner → East Post), the robot navigates smoothly across 160 seconds, achieving an average tracking accuracy of 15.5 cm.")
    ]

    for idx, (tag, desc) in enumerate(nav_points):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(7 if idx < len(nav_points) - 1 else 0)
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
    # 4A. Side-by-Side SLAM Maps (Top: Left: 6.95", Top: 1.38", Width: 5.50", Height: 2.15")
    # Sub-label for Drift map (Left: 6.95", Top: 1.38", Width: 2.65", Height: 0.22")
    tx_ld = slide.shapes.add_textbox(Inches(6.95), Inches(1.38), Inches(2.65), Inches(0.22))
    tx_ld.name = "Nav_Drift_Label"
    tf_ld = tx_ld.text_frame
    tf_ld.word_wrap = True
    tf_ld.margin_left = tf_ld.margin_right = tf_ld.margin_top = tf_ld.margin_bottom = 0
    p_ld = tf_ld.paragraphs[0]
    set_para(p_ld, "(a) Initial: 45° Corner Drift Defect", font_name="Calisto MT", size_pt=9.0, bold=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # Sub-label for Clean map (Left: 9.75", Top: 1.38", Width: 2.65", Height: 0.22")
    tx_lc = slide.shapes.add_textbox(Inches(9.75), Inches(1.38), Inches(2.65), Inches(0.22))
    tx_lc.name = "Nav_Clean_Label"
    tf_lc = tx_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_right = tf_lc.margin_top = tf_lc.margin_bottom = 0
    p_lc = tf_lc.paragraphs[0]
    set_para(p_lc, "(b) Final: Clean Metric Map", font_name="Calisto MT", size_pt=9.0, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

    # Drift Map Image (Left: 6.95", Top: 1.62", Width: 2.65", Height: 1.55")
    if os.path.exists(DRIFT_IMG):
        pic_d = slide.shapes.add_picture(
            DRIFT_IMG,
            Inches(6.95), Inches(1.62),
            width=Inches(2.65), height=Inches(1.55)
        )
        pic_d.name = "Nav_Drift_Img"

    # Clean Map Image (Left: 9.75", Top: 1.62", Width: 2.65", Height: 1.55")
    if os.path.exists(CLEAN_IMG):
        pic_c = slide.shapes.add_picture(
            CLEAN_IMG,
            Inches(9.75), Inches(1.62),
            width=Inches(2.65), height=Inches(1.55)
        )
        pic_c.name = "Nav_Clean_Img"

    # Caption under SLAM Maps (Top: 3.25", Height: 0.28")
    tx_slam_cap = slide.shapes.add_textbox(Inches(6.95), Inches(3.25), Inches(5.50), Inches(0.28))
    tx_slam_cap.name = "Nav_SLAM_Cap"
    tf_slam_cap = tx_slam_cap.text_frame
    tf_slam_cap.word_wrap = True
    tf_slam_cap.margin_left = tf_slam_cap.margin_right = tf_slam_cap.margin_top = tf_slam_cap.margin_bottom = 0
    p_sc = tf_slam_cap.paragraphs[0]
    set_para(p_sc, "Figure 3.8: Physical SLAM Calibration — Correcting Yaw Drift via Wheel Odometry Fusion", font_name="Calisto MT", size_pt=8.5, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4B. Multi-Waypoint Patrol Map (Bottom-Left: Left: 6.95", Top: 3.65", Width: 1.75", Height: 2.15")
    # Natural aspect ratio of clean crop: 1759 x 2162 -> 0.8136 -> width = 2.15 * 0.8136 = 1.75"
    if os.path.exists(PATROL_IMG):
        pic_patrol = slide.shapes.add_picture(
            PATROL_IMG,
            Inches(6.95), Inches(3.65),
            width=Inches(1.75), height=Inches(2.15)
        )
        pic_patrol.name = "Nav_Patrol_Img"

        # Caption under Patrol (Top: 5.82", Height: 0.26")
        tx_p_cap = slide.shapes.add_textbox(Inches(6.95), Inches(5.82), Inches(1.75), Inches(0.26))
        tx_p_cap.name = "Nav_Patrol_Cap"
        tf_p_cap = tx_p_cap.text_frame
        tf_p_cap.word_wrap = True
        tf_p_cap.margin_left = tf_p_cap.margin_right = tf_p_cap.margin_top = tf_p_cap.margin_bottom = 0
        p_pc = tf_p_cap.paragraphs[0]
        set_para(p_pc, "Figure 3.9: 4-Waypoint Patrol", font_name="Calisto MT", size_pt=8.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    # 4C. Summary Block of Autonomous Patrol Performance (Bottom-Right: Left: 8.90", Top: 3.65", Width: 3.55", Height: 2.25")
    tx_perf = slide.shapes.add_textbox(Inches(8.90), Inches(3.65), Inches(3.55), Inches(2.25))
    tx_perf.name = "Nav_Perf_Text"
    tf_perf = tx_perf.text_frame
    tf_perf.word_wrap = True
    tf_perf.margin_left = tf_perf.margin_right = tf_perf.margin_top = tf_perf.margin_bottom = 0

    p_ph = tf_perf.paragraphs[0]
    set_para(p_ph, "AUTONOMOUS PATROL PERFORMANCE:", font_name="Calisto MT", size_pt=9.5, bold=True, color_rgb=c_gold, space_after_pt=4)

    perf_bullets = [
        ("Map Resolution", "5 cm per grid cell for fine obstacle details"),
        ("Path Accuracy", "15.5 cm average tracking error across 160s run"),
        ("Safe Velocity", "Speed capped smoothly at 0.25 m/s for lab safety"),
        ("Goal Verification", "4 / 4 physical destinations reached (Dock → Hub → Corner → Post)"),
        ("Obstacle Buffer", "Safety inflation maintains >0.30 m clearance from walls")
    ]

    for pf_idx, (pf_tag, pf_desc) in enumerate(perf_bullets):
        p_pf = tf_perf.add_paragraph()
        p_pf.space_after = Pt(2.5 if pf_idx < len(perf_bullets) - 1 else 0)
        p_pf.line_spacing = 1.12
        p_pf.alignment = PP_ALIGN.LEFT

        r_pft = p_pf.add_run()
        r_pft.text = f"• {pf_tag}: "
        r_pft.font.name = "Calisto MT"
        r_pft.font.size = Pt(8.8)
        r_pft.font.bold = True
        r_pft.font.color.rgb = c_navy

        r_pfd = p_pf.add_run()
        r_pfd.text = pf_desc
        r_pfd.font.name = "Calisto MT"
        r_pfd.font.size = Pt(8.8)
        r_pfd.font.bold = False
        r_pfd.font.color.rgb = c_body

    prs.save(PPTX_PATH)
    print(f"Slide 12 successfully updated and compiled in {PPTX_PATH}")

if __name__ == "__main__":
    main()
