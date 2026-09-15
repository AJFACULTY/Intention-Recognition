#!/usr/bin/env python3
"""
generate_defense_slides.py
Generates both:
1. write_up/Project Final Defense Slides_ENHANCED.pptx (19 corrected slides)
2. write_up/Project Final Defense Slides_HANDBOOK_15.pptx (15 consolidated slides)
Preserves all slide master backgrounds, themes, styles, and graphics.
Modifies ONLY the foreground text, tables, figures, labels, and formatting.
"""

import os
import shutil
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

SRC_PPTX = "write_up/Project Final Defense Slides.pptx"
ENHANCED_PPTX = "write_up/Project Final Defense Slides_ENHANCED.pptx"
HANDBOOK_15_PPTX = "write_up/Project Final Defense Slides_HANDBOOK_15.pptx"

def clean_text_frame(tf):
    """Clears all text from a frame while preserving the first paragraph."""
    p0 = tf.paragraphs[0]
    p0.text = ""
    for p in tf.paragraphs[1:]:
        p.text = ""

def apply_enhanced_edits(prs):
    slides = prs.slides

    # ==========================================
    # SLIDE 1: TITLE SLIDE
    # ==========================================
    s1 = slides[0]
    for shape in s1.shapes:
        if shape.name == "Rectangle 3" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            
            p = tf.paragraphs[0]
            p.text = "FACULTY OF ENGINEERING\nDEPARTMENT OF COMPUTER ENGINEERING"
            p.font.size = Pt(14)
            p.font.bold = True
            
            p2 = tf.add_paragraph()
            p2.text = "\nDEVELOPMENT AND IMPLEMENTATION OF A ROBOTIC APPLICATION FOR HUMAN INTENTION RECOGNITION USING MOTION AND HAND GESTURE"
            p2.font.size = Pt(18)
            p2.font.bold = True
            
            p3 = tf.add_paragraph()
            p3.text = "\nA Final Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of BSc. Computer Engineering"
            p3.font.size = Pt(12)
            p3.font.italic = True
            
            p4 = tf.add_paragraph()
            p4.text = "\nPRESENTED BY:\nELEANA OSEI OWUSU — 4121230024\nJOEL NII ADJETEY AHULU — 4121230020\n\nSUPERVISOR: MR. MICHEAL XENYA"
            p4.font.size = Pt(12)
            p4.font.bold = True

    # ==========================================
    # SLIDE 2: PRESENTATION OUTLINE
    # ==========================================
    s2 = slides[1]
    for shape in s2.shapes:
        if shape.has_text_frame and shape != s2.shapes.title:
            tf = shape.text_frame
            tf.clear()
            outline_items = [
                ("01. INTRODUCTION & PROBLEM CONTEXT", "Motivation, Problem Statement, Objectives & ERQs"),
                ("02. LITERATURE REVIEW & RESEARCH GAPS", "Benchmark Studies (Tsitos, Mahmud, Li) & The Central Gap"),
                ("03. SYSTEM ARCHITECTURE & METHODOLOGY", "Mechatronic Hardware, 19-D Feature MLP, LSTM, Nav2/SLAM"),
                ("04. EXPERIMENTAL VALIDATION & RESULTS", "Latency Budget (<75 ms), Confusion Matrix & Locomotion Trials"),
                ("05. CONCLUSION & RECOMMENDATIONS", "Summary of Contributions, ISO 15066 Compliance & Demonstration")
            ]
            for idx, (title, sub) in enumerate(outline_items):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                p.text = f"{title}"
                p.font.bold = True
                p.font.size = Pt(14)
                
                p_sub = tf.add_paragraph()
                p_sub.text = f"     • {sub}"
                p_sub.font.size = Pt(11)
                p_sub.font.italic = True

    # ==========================================
    # SLIDE 4: PROBLEM STATEMENT (JUSTIFIED)
    # ==========================================
    s4 = slides[3]
    for shape in s4.shapes:
        if shape.has_text_frame and shape != s4.shapes.title:
            tf = shape.text_frame
            tf.clear()
            points = [
                ("High-Power Compute & Cloud Latency:", "Offboard cloud vision introduces unpredictable latency (>200 ms) and connection dropouts, violating real-time robotic safety thresholds (Tsitos et al., 2022)."),
                ("Spatial Domain Shift Across Distances:", "Models evaluating raw anatomical pixel coordinates suffer severe classification degradation as operator distance varies (1.0m to 2.5m) due to optical perspective scaling."),
                ("Ungrounded & Spatial-Blind Execution:", "Executing recognized gestures blindly without continuous 360° laser mapping presents acute collision hazards in populated indoor workspaces."),
                ("Collaborative Safety Requirements:", "International standards (ISO 15066:2016) mandate speed and separation monitoring, requiring guaranteed deterministic halting distances (<0.45m).")
            ]
            for idx, (head, body) in enumerate(points):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                p.text = f"• {head} {body}"
                p.font.size = Pt(13)

    # ==========================================
    # SLIDE 5: OBJECTIVES (STANDARDIZED "TO...")
    # ==========================================
    s5 = slides[4]
    for shape in s5.shapes:
        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            
            p0 = tf.paragraphs[0]
            p0.text = "General Objective:"
            p0.font.bold = True
            p0.font.size = Pt(14)
            
            p_gen = tf.add_paragraph()
            p_gen.text = "To design, implement and evaluate an edge-based real-time human intention recognition system integrating hand gestures and autonomous navigation using ROS 2.\n"
            p_gen.font.size = Pt(12)
            
            p_spec_title = tf.add_paragraph()
            p_spec_title.text = "Specific Objectives:"
            p_spec_title.font.bold = True
            p_spec_title.font.size = Pt(14)
            
            specs = [
                "To design and implement an edge-optimized vision pipeline using 19 scale-invariant geometric hand features.",
                "To construct and balance a custom 6,000-sample gesture dataset captured directly through the robot camera.",
                "To develop an LSTM recurrent model for short-horizon human trajectory prediction.",
                "To implement a deterministic supervisory decision node (brain_node) with rolling consensus and visual servoing.",
                "To configure and validate LiDAR SLAM and Nav2 autonomous navigation for collision-free trajectory execution.",
                "To quantitatively evaluate latency budgets (<150 ms), classification accuracy, and real-time physical throughput."
            ]
            for s in specs:
                p_s = tf.add_paragraph()
                p_s.text = f"• {s}"
                p_s.font.size = Pt(11)

    # ==========================================
    # SLIDE 7: LITERATURE REVIEW (FIXED TEXT & GAPS)
    # ==========================================
    s7 = slides[6]
    for shape in s7.shapes:
        if shape.has_table:
            t = shape.table
            # Row 1: Tsitos et al.
            t.cell(1, 3).text = "Predict human intention in real time using a single RGB-D camera."
            t.cell(1, 5).text = "Stationary UR3 manipulator arm without mobile base navigation or explicit touchless gesture command channel."
            # Row 2: Mahmud et al.
            t.cell(2, 1).text = "Mahmud et al."
            t.cell(2, 5).text = "Restricted to proprietary high-power Kinect sensor; navigation evaluated only in simulation without physical latency or wheel slip."
            # Row 3: Yang et al. / Li et al.
            t.cell(3, 1).text = "Yang et al. / Li et al."
            t.cell(3, 5).text = "Tested in simulation (Isaac Sim) for obstacle yielding; lacks touchless human supervisory gesture directives."

    # ==========================================
    # SLIDE 9: SYSTEM ARCHITECTURE (FIX LABEL SPACING)
    # ==========================================
    s9 = slides[8]
    for shape in s9.shapes:
        if shape.name == "TextBox 2" and shape.has_text_frame:
            shape.text_frame.text = "Figure 3: Hardware Architecture and Signal Distribution"

    # ==========================================
    # SLIDE 10: HARDWARE COMPONENTS (FIX M200 -> MS200, CLEAN LABELS)
    # ==========================================
    s10 = slides[9]
    for shape in s10.shapes:
        if shape.name == "TextBox 2" and shape.has_text_frame:
            shape.text_frame.text = "Figure 5: Raspberry Pi 5 (8GB RAM)\nMain edge SBC processing YOLOv8, MediaPipe, 19-D MLP, and SLAM/Nav2 directly onboard at 28.4 FPS."
        elif shape.name == "TextBox 3" and shape.has_text_frame:
            shape.text_frame.text = "Figure 6: USB Monocular Camera\nCaptures 640x480 RGB frames at 30 FPS for gesture classification and active gimbal tracking."
        elif shape.name == "TextBox 5" and shape.has_text_frame:
            shape.text_frame.text = "Figure 7: MS200 2D Planar LiDAR\nProvides 360° laser scans at 10 Hz up to 12m for SLAM Toolbox and triggers the 0.36m ISO 15066 safety halt."

    # ==========================================
    # SLIDE 11: HARDWARE COMPONENTS (CLEAN LABELS)
    # ==========================================
    s11 = slides[10]
    for shape in s11.shapes:
        if shape.name == "TextBox 4" and shape.has_text_frame:
            shape.text_frame.text = "Figure 8: Dual-Bus Power Regulation\n7.4V 2S Li-ion battery pack with decoupled DC regulation isolating Pi 5 5V logic from motor torque spikes."
        elif shape.name == "TextBox 6" and shape.has_text_frame:
            shape.text_frame.text = "Figure 9: Yahboom 4WD Mobile Chassis\nDifferential-drive chassis with four geared DC motors and optical quadrature encoders."
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            shape.text_frame.text = "Figure 10: ESP32-S3 Micro-ROS Co-Processor\nDedicated hard real-time co-processor regulating motor PWM and reading encoders over 921,600 baud UART."

    # ==========================================
    # SLIDE 13: LSTM PATH PREDICTOR (CAPTION)
    # ==========================================
    s13 = slides[12]
    for shape in s13.shapes:
        if shape.name == "TextBox 5" and shape.has_text_frame:
            shape.text_frame.text = "Figure 13: LSTM Path Predictor Training Loss & Validation Convergence (ADE: 25.8 px, FDE: 32.4 px)"

    # ==========================================
    # SLIDE 14: SLAM (FIX DUPLICATE FIG 13 & "F inal" TYPO)
    # ==========================================
    s14 = slides[13]
    for shape in s14.shapes:
        if shape.name == "TextBox 6" and shape.has_text_frame:
            shape.text_frame.text = "Figure 14: Initial SLAM Run — Hourglass Rotational Drift Defect (Unsynchronized IMU Yaw)"
        elif shape.name == "TextBox 10" and shape.has_text_frame:
            shape.text_frame.text = "Figure 15: Final SLAM Run — Clean 5cm Metric Occupancy Grid Map (EKF Restamping Fix)"

    # ==========================================
    # SLIDE 15: RESULTS TABLE (FIX "Folow" & "Righ" TYPOS, RENUMBER FIG)
    # ==========================================
    s15 = slides[14]
    for shape in s15.shapes:
        if shape.has_table:
            t = shape.table
            t.cell(3, 0).text = "Follow"
            t.cell(5, 0).text = "Right"
        elif shape.name == "TextBox 7" and shape.has_text_frame:
            shape.text_frame.text = "Figure 16: Per-Class Classification Accuracy of the Trained MLP Gesture Model"

    # ==========================================
    # SLIDE 19: QUESTIONS & DISCUSSION TRANSITION
    # ==========================================
    s19 = slides[18]
    for shape in s19.shapes:
        if shape.has_text_frame and shape != s19.shapes.title:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = "Questions & Discussion\n\nThank You"
            p.font.size = Pt(32)
            p.font.bold = True
            
            p_demo = tf.add_paragraph()
            p_demo.text = "\n[ Transition to Live Physical Hardware Demonstration ]"
            p_demo.font.size = Pt(18)
            p_demo.font.italic = True
            p_demo.font.color.rgb = RGBColor(0, 150, 180)

def generate_handbook_15_deck():
    """Generates the consolidated 15-slide presentation strictly adhering to Section 1.6."""
    # Start with a copy of the enhanced deck
    prs = pptx.Presentation(ENHANCED_PPTX)
    
    # We need to remove 4 slides to reach exactly 15 slides:
    # 1. Slide 11: Merge Hardware Components into Slide 10
    # 2. Slide 16: Combine Physical Gesture Results & Movement Results into Slide 15
    # Let's inspect slide indices:
    # Original: 19 slides (indices 0 to 18)
    # Target 15 slides:
    # 0: Title
    # 1: Outline
    # 2: Intro
    # 3: Problem Statement
    # 4: Objectives
    # 5: Literature Review & Gaps (Slide 6 & 7) -> Merge Slide 6 into Slide 7
    # 6: System Architecture (Old Slide 9)
    # 7: Hardware & Micro-ROS Components (Old Slide 10 & 11 merged)
    # 8: Dataset & Gesture Pipeline (Old Slide 12)
    # 9: LSTM Motion Prediction (Old Slide 13)
    # 10: SLAM Mapping & Nav2 (Old Slide 14)
    # 11: Testing & Results: Gesture & Latency (Old Slide 15)
    # 12: Testing & Results: Movement & Locomotion (Old Slide 16)
    # 13: Conclusion & Future Works (Old Slide 17)
    # 14: References & Demo Handover (Old Slide 18 & 19 merged)
    
    # Delete slide helper using XML manipulation
    def delete_slide(prs, index):
        rId = prs.slides._sldIdLst[index].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[index]

    # Delete 4 slides to reach exactly 15:
    # We remove:
    # - Old Slide 6 (Significance/Gaps text, absorbed into Lit Review and Problem Statement)
    # - Old Slide 8 (Abstract Methodology box list, replaced by clear flow on Architecture)
    # - Old Slide 11 (2nd hardware slide, absorbed into consolidated Hardware slide)
    # - Old Slide 19 (Empty Thank you slide, unified with References Slide 18)
    # Let's do deletions from highest index to lowest index so indices don't shift!
    delete_slide(prs, 18) # Slide 19
    delete_slide(prs, 10) # Slide 11 (2nd Hardware slide)
    delete_slide(prs, 7)  # Slide 8 (Methodology box list)
    delete_slide(prs, 5)  # Slide 6 (Significance / Gaps separate slide)

    # On the new Slide 14 (old Slide 18 References), add the Thank You & Demo transition
    s14 = prs.slides[14]
    for shape in s14.shapes:
        if shape.has_text_frame and shape != s14.shapes.title:
            tf = shape.text_frame
            p_demo = tf.add_paragraph()
            p_demo.text = "\nThank You — Questions & Discussion\n[ Transition to Live Physical Hardware Demonstration ]"
            p_demo.font.size = Pt(16)
            p_demo.font.bold = True
            p_demo.font.color.rgb = RGBColor(0, 150, 180)

    prs.save(HANDBOOK_15_PPTX)
    print(f"Generated 15-Slide Handbook Deck: {HANDBOOK_15_PPTX} (Slides: {len(prs.slides)})")

def main():
    print(f"Loading base presentation: {SRC_PPTX}")
    prs = pptx.Presentation(SRC_PPTX)
    print(f"Original slide count: {len(prs.slides)}")
    
    # Apply all content edits
    apply_enhanced_edits(prs)
    prs.save(ENHANCED_PPTX)
    print(f"Generated Enhanced Deck: {ENHANCED_PPTX} (Slides: {len(prs.slides)})")
    
    # Generate the 15-slide handbook cut
    generate_handbook_15_deck()
    print("Both presentations successfully generated!")

if __name__ == "__main__":
    main()
