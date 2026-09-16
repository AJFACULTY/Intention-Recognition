#!/usr/bin/env python3
"""
build_slide_8.py — Formal Academic Slide 8 (Software Architecture & Flowchart)
- Plain English, zero jargon traps: completely effortless to explain on first read.
- Pure black-and-white flowchart on the right (No colors, crisp black shapes/lines).
- Left: Open Editorial structured discussion of how software processes sensor data.
- Generous bottom clearance (>0.75" above footer bar).
- Dignified GCTU 2-tone palette for slide headers: Navy (#002060), Gold (#B8860B), Slate Charcoal (#334155).
"""

import os
import subprocess
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PPTX_PATH = "write_up/Project Final Defense Slides_FINAL.pptx"
FLOWCHART_IMG = "write_up/figures/software_flowchart.png"
DOT_PATH = "write_up/figures/software_flowchart.dot"

def generate_monochrome_flowchart():
    """Generates the clean black-and-white flowchart using Graphviz dot with plain-English labels."""
    dot_code = """
digraph SoftwareDataflow {
    rankdir=TB;
    nodesep=0.40;
    ranksep=0.34;
    splines=true;
    bgcolor="transparent";

    node [fontname="DejaVu Sans", fontsize=9.0, penwidth=1.6, color="black", fillcolor="white", style="filled"];
    edge [fontname="DejaVu Sans", fontsize=8.0, color="black", penwidth=1.4, arrowhead="vee"];

    // Inputs (Top Row)
    { rank=same;
        cam [label="Camera Video Stream\\n(20 Frames per Second)", shape=box, style="rounded,filled"];
        lidar [label="2D Laser Sensor (LiDAR)\\n(360° Continuous Scan)", shape=box, style="rounded,filled"];
    }

    // Vision Pipeline
    person [label="Person Detection\\n(Focus on Human Operator)", shape=box];
    gesture [label="Hand Tracking & AI\\n(Identify Hand Gesture)", shape=box];
    consensus [label="Same Gesture Seen\\n5 Times in a Row?", shape=diamond];
    
    // Control & Safety
    brain [label="Decision Brain (brain_node)\\n(Create Driving Command)", shape=box];
    safety [label="Obstacle Closer\\nThan 0.36 Meters?", shape=diamond];
    mux [label="Safety Switch (twist_mux)\\n(Safety Stop Takes Top Priority)", shape=box];

    // Bridge & Output
    bridge [label="micro-ROS Serial Bridge\\n(High-Speed Communication)", shape=box];
    esp32 [label="Motor Controller (ESP32-S3)\\n(Drives the 4 Wheels)", shape=box, style="rounded,filled"];

    // Connections
    cam -> person [label=" Live video "];
    person -> gesture [label=" Hand area "];
    gesture -> consensus [label=" Detected gesture "];
    
    consensus -> brain [label=" Yes (Confirmed) "];
    
    lidar -> safety [label=" Distance readings "];
    safety -> mux [label=" Yes (Emergency Stop) "];
    brain -> mux [label=" Driving command "];

    mux -> bridge [label=" Approved command "];
    bridge -> esp32 [label=" Motor signals "];
}
"""
    with open(DOT_PATH, "w") as f:
        f.write(dot_code)
    
    subprocess.run(["dot", "-Tpng", "-Gdpi=250", DOT_PATH, "-o", FLOWCHART_IMG], check=True)
    print(f"Generated plain-English monochrome flowchart: {FLOWCHART_IMG}")

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
    generate_monochrome_flowchart()
    prs = pptx.Presentation(PPTX_PATH)

    if len(prs.slides) < 8:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
    else:
        slide = prs.slides[7]

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
            set_para(p, "06. SOFTWARE ARCHITECTURE & INTER-NODE DATAFLOW", font_name="Calisto MT", size_pt=24, bold=True, color_rgb=c_navy, align=PP_ALIGN.CENTER)

        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            shape.text_frame.clear()

    # Clean existing custom shapes on Slide 8
    shapes_to_remove = [s for s in slide.shapes if s.name.startswith("Arch_")]
    for s in shapes_to_remove:
        el = s._element
        el.getparent().remove(el)

    # 2. Section Subhead: Left-aligned Gold Eyebrow (Plain English)
    tx_sub = slide.shapes.add_textbox(Inches(0.85), Inches(1.05), Inches(11.63), Inches(0.25))
    tx_sub.name = "Arch_Subhead"
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    set_para(p_sub, "HOW THE ROBOT PROCESSES SENSOR DATA AND MAKES SAFE DRIVING DECISIONS", font_name="Calisto MT", size_pt=11, bold=True, color_rgb=c_gold, align=PP_ALIGN.LEFT)

    # 3. Left Column: Structured Discussion in Plain English (11 pt)
    # Left: 0.85", Top: 1.38", Width: 6.45", Height: 4.70"
    tx_left = slide.shapes.add_textbox(Inches(0.85), Inches(1.38), Inches(6.45), Inches(4.70))
    tx_left.name = "Arch_Tiers_Text"
    tf_left = tx_left.text_frame
    tf_left.word_wrap = True
    tf_left.margin_left = tf_left.margin_right = tf_left.margin_top = tf_left.margin_bottom = Inches(0.02)

    software_pipeline = [
        ("System Software (ROS 2)", "Connects all camera, artificial intelligence, and motor programs so they exchange data instantly without delays."),
        ("Live Sensor Feeds", "The camera captures live video at 20 frames per second while the laser sensor constantly scans 360 degrees for obstacles."),
        ("Vision & Hand Tracking", "Focuses on the person standing in front of the robot, locates 21 finger joints, and identifies the gesture being shown."),
        ("Gesture Confirmation", "The robot checks that it sees the exact same gesture 5 times in a row before moving, ignoring accidental hand motions."),
        ("Safety Override", "If the laser detects any obstacle closer than 0.36 meters, it instantly overrides driving commands and halts the robot immediately."),
        ("Smooth Wheel Control", "Approved movement commands are transmitted directly to the motor controller board, which drives the 4 wheels smoothly.")
    ]

    for idx, (tag, desc) in enumerate(software_pipeline):
        p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
        p.space_after = Pt(8 if idx < len(software_pipeline) - 1 else 0)
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

    # 4. Right Column: Monochrome Black-and-White Flowchart
    if os.path.exists(FLOWCHART_IMG):
        # Flowchart width: 4.85", height: 4.65", Left: 7.55", Top: 1.38"
        pic = slide.shapes.add_picture(
            FLOWCHART_IMG,
            Inches(7.55), Inches(1.38),
            width=Inches(4.85), height=Inches(4.65)
        )
        pic.name = "Arch_Diagram_Img"

        # Caption underneath flowchart
        tx_cap = slide.shapes.add_textbox(Inches(7.55), Inches(6.10), Inches(4.85), Inches(0.25))
        tx_cap.name = "Arch_Caption"
        tf_cap = tx_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
        p_cap = tf_cap.paragraphs[0]
        set_para(p_cap, "Figure 3.1: Dataflow Pipeline from Sensor Feeds to Wheel Actuation", font_name="Calisto MT", size_pt=9.0, italic=True, color_rgb=c_muted, align=PP_ALIGN.CENTER)

    prs.save(PPTX_PATH)
    print(f"Slide 8 successfully updated with plain-English text and flowchart in {PPTX_PATH}")

if __name__ == "__main__":
    main()
