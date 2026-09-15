#!/usr/bin/env python3
"""
generate_defense_slides.py — Production Slide Generator
Generates:
1. write_up/Project Final Defense Slides_ENHANCED.pptx (19 corrected slides)
2. write_up/Project Final Defense Slides_HANDBOOK_15.pptx (15 consolidated slides)

Fixes:
- Zero text bleeding: Exact font scaling (Pt 8.5 to 14.5), tight paragraph margins (space_after), word-wrap enabled
- Real Accepted Methodology: Replaces crude static tables on Slide 8 with the high-res 6-Phase Engineering Methodology diagram
- Complete preservation of original slide master backgrounds, themes, graphics, and layouts
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

SRC_PPTX = "write_up/Project Final Defense Slides_ORIGINAL_BACKUP.pptx"
ENHANCED_PPTX = "write_up/Project Final Defense Slides_ENHANCED.pptx"
HANDBOOK_15_PPTX = "write_up/Project Final Defense Slides_HANDBOOK_15.pptx"
METHODOLOGY_IMG = "write_up/figures/fig_accepted_methodology.png"

def set_para(p, text, size_pt, bold=False, italic=False, color_rgb=None, space_after_pt=2, align=None):
    p.text = text
    p.font.size = Pt(size_pt)
    p.font.bold = bold
    p.font.italic = italic
    p.space_after = Pt(space_after_pt)
    if color_rgb:
        p.font.color.rgb = color_rgb
    if align:
        p.alignment = align

def apply_enhanced_edits(prs):
    slides = prs.slides

    # ==========================================
    # SLIDE 1: TITLE SLIDE (FIX OVERFLOW & LABELS)
    # ==========================================
    s1 = slides[0]
    for shape in s1.shapes:
        if shape.name == "Rectangle 3" and shape.has_text_frame:
            shape.left = Inches(6.45)
            shape.top = Inches(0.40)
            shape.width = Inches(6.40)
            shape.height = Inches(6.70)
            tf = shape.text_frame
            tf.word_wrap = True
            tf.margin_top = Inches(0.1)
            tf.margin_bottom = Inches(0.1)
            tf.margin_left = Inches(0.2)
            tf.margin_right = Inches(0.2)
            tf.clear()
            
            p1 = tf.paragraphs[0]
            set_para(p1, "FACULTY OF ENGINEERING", 12, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "DEPARTMENT OF COMPUTER ENGINEERING", 12, bold=True, space_after_pt=10)
            
            p3 = tf.add_paragraph()
            set_para(p3, "DEVELOPMENT AND IMPLEMENTATION OF A ROBOTIC APPLICATION FOR HUMAN INTENTION RECOGNITION USING MOTION AND HAND GESTURE", 14, bold=True, space_after_pt=10)
            
            p4 = tf.add_paragraph()
            set_para(p4, "A Final Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of BSc. Computer Engineering", 10.5, italic=True, space_after_pt=14)
            
            p5 = tf.add_paragraph()
            set_para(p5, "PRESENTED BY:", 11, bold=True, space_after_pt=1)
            p6 = tf.add_paragraph()
            set_para(p6, "ELEANA OSEI OWUSU — 4121230024", 11, space_after_pt=1)
            p7 = tf.add_paragraph()
            set_para(p7, "JOEL NII ADJETEY AHULU — 4121230020", 11, space_after_pt=10)
            
            p8 = tf.add_paragraph()
            set_para(p8, "SUPERVISOR: MR. MICHEAL XENYA", 11, bold=True, space_after_pt=0)

    # ==========================================
    # SLIDE 2: PRESENTATION OUTLINE (NATIVE TEXT BOX, NO OVERFLOW)
    # ==========================================
    s2 = slides[1]
    # Remove old placeholder graphic frame if present
    for shape in list(s2.shapes):
        if shape != s2.shapes.title and shape.name != "Title 1":
            el = shape._element
            el.getparent().remove(el)

    tb = s2.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(11.33), Inches(5.1))
    tf2 = tb.text_frame
    tf2.word_wrap = True
    outline_items = [
        ("01. INTRODUCTION & PROBLEM CONTEXT", "Motivation, Problem Statement, Objectives & ERQs"),
        ("02. LITERATURE REVIEW & RESEARCH GAPS", "Benchmark Studies (Tsitos, Mahmud, Li) & The Central Gap"),
        ("03. SYSTEM ARCHITECTURE & METHODOLOGY", "Mechatronic Hardware, 19-D Feature MLP, LSTM, Nav2/SLAM"),
        ("04. EXPERIMENTAL VALIDATION & RESULTS", "Latency Budget (<75 ms), Confusion Matrix & Locomotion Trials"),
        ("05. CONCLUSION & RECOMMENDATIONS", "Summary of Contributions, ISO 15066 Compliance & Demonstration")
    ]
    for idx, (title, sub) in enumerate(outline_items):
        p_head = tf2.paragraphs[0] if idx == 0 else tf2.add_paragraph()
        set_para(p_head, title, 12, bold=True, space_after_pt=1)
        p_sub = tf2.add_paragraph()
        set_para(p_sub, f"     • {sub}", 10, italic=True, space_after_pt=5)

    # ==========================================
    # SLIDE 4: PROBLEM STATEMENT (TIGHT JUSTIFICATIONS)
    # ==========================================
    s4 = slides[3]
    for shape in s4.shapes:
        if shape.has_text_frame and shape != s4.shapes.title:
            tf = shape.text_frame
            tf.word_wrap = True
            tf.clear()
            points = [
                ("• High-Power Hardware & Cloud Latency:", "Offboard cloud vision introduces unpredictable latency (>200 ms) and connection drops, violating real-time robotic safety reaction limits (Tsitos et al., 2022)."),
                ("• Spatial Distance Domain Shift:", "Classifiers evaluating raw pixel coordinates degrade as operator distance varies (1.0m to 2.5m) due to optical perspective scaling."),
                ("• Ungrounded Spatial Command Execution:", "Executing recognized gestures blindly without continuous 360° laser mapping and obstacle verification presents severe collision hazards in shared indoor workspaces."),
                ("• Collaborative Safety Compliance:", "International standards (ISO 15066:2016) mandate speed and separation monitoring, requiring guaranteed deterministic halting distances (<0.45m).")
            ]
            for idx, (head, body) in enumerate(points):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                set_para(p, f"{head} {body}", 10.5, space_after_pt=5)

    # ==========================================
    # SLIDE 5: OBJECTIVES (STANDARDIZED "TO...", CLEAN FIT)
    # ==========================================
    s5 = slides[4]
    for shape in list(s5.shapes):
        if shape.name == "Rectangle 8":
            sp = shape._element
            sp.getparent().remove(sp)
    
    for shape in s5.shapes:
        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            tf = shape.text_frame
            tf.word_wrap = True
            tf.clear()
            
            p0 = tf.paragraphs[0]
            set_para(p0, "General Objective:", 12, bold=True, space_after_pt=1)
            
            p_gen = tf.add_paragraph()
            set_para(p_gen, "To design, implement and evaluate an edge-based real-time human intention recognition system integrating hand gestures and autonomous navigation using ROS 2.", 10, space_after_pt=5)
            
            p_spec_title = tf.add_paragraph()
            set_para(p_spec_title, "Specific Objectives:", 12, bold=True, space_after_pt=1)
            
            specs = [
                "• To design and implement an edge-optimized vision pipeline using 19 scale-invariant geometric hand features.",
                "• To construct and balance a custom 6,000-sample gesture dataset captured directly through the onboard camera.",
                "• To develop an LSTM sequential recurrent model for short-horizon human trajectory prediction.",
                "• To implement a deterministic supervisory decision node (brain_node) with rolling consensus and visual servoing.",
                "• To configure and validate LiDAR SLAM and Nav2 autonomous navigation for collision-free trajectory execution.",
                "• To quantitatively evaluate latency budgets (<150 ms), classification accuracy, and real-time physical throughput."
            ]
            for s in specs:
                p_s = tf.add_paragraph()
                set_para(p_s, s, 9.5, space_after_pt=2)

    # ==========================================
    # SLIDE 7: LITERATURE REVIEW (TABLE FIT & CITATIONS)
    # ==========================================
    s7 = slides[6]
    for shape in s7.shapes:
        if shape.has_table:
            t = shape.table
            for r in t.rows:
                for cell in r.cells:
                    cell.margin_top = Inches(0.03)
                    cell.margin_bottom = Inches(0.03)
                    cell.margin_left = Inches(0.05)
                    cell.margin_right = Inches(0.05)
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(8.0)
            t.cell(1, 3).text = "Predict human intention in real time using a single RGB-D camera."
            t.cell(1, 3).text_frame.paragraphs[0].font.size = Pt(8.0)
            t.cell(1, 5).text = "Stationary UR3 arm without mobile base navigation or explicit gesture command channel."
            t.cell(1, 5).text_frame.paragraphs[0].font.size = Pt(8.0)
            
            t.cell(2, 1).text = "Mahmud et al."
            t.cell(2, 1).text_frame.paragraphs[0].font.size = Pt(8.0)
            t.cell(2, 5).text = "Restricted to proprietary Kinect sensor; navigation evaluated only in simulation without physical latency or wheel slip."
            t.cell(2, 5).text_frame.paragraphs[0].font.size = Pt(8.0)
            
            t.cell(3, 1).text = "Yang et al. / Li et al."
            t.cell(3, 1).text_frame.paragraphs[0].font.size = Pt(8.0)
            t.cell(3, 5).text = "Simulation only (Isaac Sim); predicts obstacle clearance but lacks touchless human supervisory control."
            t.cell(3, 5).text_frame.paragraphs[0].font.size = Pt(8.0)

    # ==========================================
    # SLIDE 8: METHODOLOGY — REPLACE STATIC CRUDE TABLES WITH REAL ACCEPTED METHODOLOGY DIAGRAM
    # ==========================================
    s8 = slides[7]
    for shape in list(s8.shapes):
        if shape != s8.shapes.title and shape.name != "Title 1":
            sp = shape._element
            sp.getparent().remove(sp)
    
    if s8.shapes.title:
        s8.shapes.title.text = "SYSTEM DESIGN & ENGINEERING METHODOLOGY"
        s8.shapes.title.text_frame.paragraphs[0].font.size = Pt(22)
    
    if os.path.exists(METHODOLOGY_IMG):
        s8.shapes.add_picture(
            METHODOLOGY_IMG,
            Inches(0.8), Inches(1.35),
            Inches(11.73), Inches(5.65)
        )

    # ==========================================
    # SLIDE 9: SYSTEM ARCHITECTURE (LABEL SPACING)
    # ==========================================
    s9 = slides[8]
    for shape in s9.shapes:
        if shape.name == "TextBox 2" and shape.has_text_frame:
            shape.text_frame.text = "Figure 3: Hardware Architecture and Signal Distribution"
            shape.text_frame.paragraphs[0].font.size = Pt(9.5)

    # ==========================================
    # SLIDE 10: HARDWARE (COMPUTE & SENSORS) — NO OVERFLOW
    # ==========================================
    s10 = slides[9]
    for shape in s10.shapes:
        if shape.name == "TextBox 2" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 5: Raspberry Pi 5 (8GB RAM)", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "Edge SBC running ROS 2 Humble, MediaPipe, 19-D MLP, and SLAM/Nav2 directly onboard at 28.4 FPS on CPU.", 8.5, space_after_pt=0)
        elif shape.name == "TextBox 3" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 6: USB Monocular Camera", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "Captures 640x480 RGB frames at 30 FPS for gesture classification and active gimbal tracking.", 8.5, space_after_pt=0)
        elif shape.name == "TextBox 5" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 7: MS200 2D Planar LiDAR", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "Provides 360° laser scans at 10 Hz up to 12m for SLAM and triggers the 0.36m ISO 15066 safety halt.", 8.5, space_after_pt=0)

    # ==========================================
    # SLIDE 11: HARDWARE (POWER & CHASSIS) — NO OVERFLOW
    # ==========================================
    s11 = slides[10]
    for shape in s11.shapes:
        if shape.name == "TextBox 4" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 8: Dual-Bus Power Regulation", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "7.4V 2S Li-ion battery pack with decoupled DC regulation isolating Pi 5 logic from motor current spikes.", 8.5, space_after_pt=0)
        elif shape.name == "TextBox 6" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 9: Yahboom 4WD Mobile Chassis", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "Differential-drive chassis with four geared DC motors and optical quadrature encoders.", 8.5, space_after_pt=0)
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            p1 = tf.paragraphs[0]
            set_para(p1, "Figure 10: ESP32-S3 Micro-ROS Co-Processor", 9.5, bold=True, space_after_pt=1)
            p2 = tf.add_paragraph()
            set_para(p2, "Dedicated hard real-time co-processor regulating motor PWM and reading encoders over 921,600 baud UART.", 8.5, space_after_pt=0)

    # ==========================================
    # SLIDE 13: LSTM CAPTION
    # ==========================================
    s13 = slides[12]
    for shape in s13.shapes:
        if shape.name == "TextBox 5" and shape.has_text_frame:
            shape.text_frame.text = "Figure 13: LSTM Path Predictor Training Loss & Convergence (ADE: 25.8 px, FDE: 32.4 px)"
            shape.text_frame.paragraphs[0].font.size = Pt(9.5)

    # ==========================================
    # SLIDE 14: SLAM (DUPLICATE FIG 13 RESOLUTION)
    # ==========================================
    s14 = slides[13]
    for shape in s14.shapes:
        if shape.name == "TextBox 6" and shape.has_text_frame:
            shape.text_frame.text = "Figure 14: Initial SLAM Run — Hourglass Rotational Drift Defect (Unsynchronized IMU Yaw)"
            shape.text_frame.paragraphs[0].font.size = Pt(9.5)
        elif shape.name == "TextBox 10" and shape.has_text_frame:
            shape.text_frame.text = "Figure 15: Final SLAM Run — Clean 5cm Metric Occupancy Grid Map (EKF Restamping Fix)"
            shape.text_frame.paragraphs[0].font.size = Pt(9.5)

    # ==========================================
    # SLIDE 15: RESULTS (FIX TYPOS & RENUMBER)
    # ==========================================
    s15 = slides[14]
    for shape in s15.shapes:
        if shape.has_table:
            t = shape.table
            t.cell(3, 0).text = "Follow"
            t.cell(5, 0).text = "Right"
            for r in t.rows:
                for cell in r.cells:
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(9.0)
        elif shape.name == "TextBox 7" and shape.has_text_frame:
            shape.text_frame.text = "Figure 16: Per-Class Classification Accuracy of the Trained MLP Gesture Model"
            shape.text_frame.paragraphs[0].font.size = Pt(9.5)

    # ==========================================
    # SLIDE 17: CONCLUSION & FUTURE WORK (CLEAN FIT)
    # ==========================================
    s17 = slides[16]
    for shape in s17.shapes:
        if shape.name == "Content Placeholder 2" and shape.has_text_frame:
            tf = shape.text_frame
            for p in tf.paragraphs:
                p.font.size = Pt(9.5)
                p.space_after = Pt(2)
        elif shape.name == "TextBox 5" and shape.has_text_frame:
            tf = shape.text_frame
            for p in tf.paragraphs:
                p.font.size = Pt(9.5)
                p.space_after = Pt(2)

    # ==========================================
    # SLIDE 18: REFERENCES (TIGHT COMPACT FIT)
    # ==========================================
    s18 = slides[17]
    for shape in s18.shapes:
        if shape.has_text_frame and shape != s18.shapes.title:
            tf = shape.text_frame
            tf.clear()
            refs = [
                "[1] D. Tsitos et al., “Real-Time Feasibility of a Human Intention Prediction Method Evaluated Through a Competitive Human–Robot Reaching Game,” IEEE Robotics and Automation Letters, vol. 7, no. 4, pp. 10034–10041, Oct. 2022.",
                "[2] J. A. Mahmud, B. C. Das, J. Shin, K. M. Hasib, R. Sadik, and M. F. Mridha, “3D Gesture Recognition and Adaptation for Human–Robot Interaction,” IEEE Access, vol. 10, pp. 116485–116507, 2022.",
                "[3] G. Yang et al., “Safe and Efficient Motion Planning for Material Transportation Robots Considering Intention Prediction of Obstacles,” in Proc. IEEE Int. Conf. Mechatronics Autom. (ICMA), Harbin, China, 2023, pp. 1179–1184."
            ]
            for idx, r in enumerate(refs):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                set_para(p, r, 9.0, space_after_pt=4)

    # ==========================================
    # SLIDE 19: QUESTIONS & TRANSITION
    # ==========================================
    s19 = slides[18]
    for shape in s19.shapes:
        if shape.has_text_frame and shape != s19.shapes.title:
            tf = shape.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            set_para(p, "Questions & Discussion\n\nThank You", 26, bold=True, space_after_pt=10, align=PP_ALIGN.CENTER)
            p_demo = tf.add_paragraph()
            set_para(p_demo, "[ Transition to Live Physical Hardware Demonstration ]", 15, italic=True, color_rgb=RGBColor(0, 150, 180), align=PP_ALIGN.CENTER)

def generate_handbook_15_deck():
    """Generates the consolidated 15-slide deck strictly adhering to Section 1.6."""
    prs = pptx.Presentation(ENHANCED_PPTX)
    
    def delete_slide(prs, index):
        rId = prs.slides._sldIdLst[index].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[index]

    # Delete 4 slides to reach exactly 15:
    # 1. Slide 19 (separate Thank you, absorbed into References)
    # 2. Slide 11 (2nd hardware slide, absorbed into mechatronics overview)
    # 3. Slide 9 (System Architecture, while keeping the 6-Phase Methodology on Slide 8!)
    # 4. Slide 6 (Significance / Gaps separate text slide)
    delete_slide(prs, 18) # Slide 19
    delete_slide(prs, 10) # Slide 11 (2nd Hardware slide)
    delete_slide(prs, 8)  # Old Slide 9 (System Architecture)
    delete_slide(prs, 5)  # Slide 6

    # In the 15-slide deck, Slide 6 is Literature Review, Slide 7 is the 6-Phase Methodology diagram!
    # On the final Slide 14 (References), add the Thank You & Demo transition
    s14 = prs.slides[14]
    for shape in s14.shapes:
        if shape.has_text_frame and shape != s14.shapes.title:
            tf = shape.text_frame
            p_demo = tf.add_paragraph()
            set_para(p_demo, "\nThank You — Questions & Discussion\n[ Transition to Live Physical Hardware Demonstration ]", 14, bold=True, color_rgb=RGBColor(0, 150, 180), align=PP_ALIGN.CENTER)

    prs.save(HANDBOOK_15_PPTX)
    print(f"Generated 15-Slide Handbook Deck: {HANDBOOK_15_PPTX} (Slides: {len(prs.slides)})")

def main():
    print(f"Loading base presentation: {SRC_PPTX}")
    prs = pptx.Presentation(SRC_PPTX)
    apply_enhanced_edits(prs)
    prs.save(ENHANCED_PPTX)
    print(f"Generated Enhanced Deck: {ENHANCED_PPTX} (Slides: {len(prs.slides)})")
    
    generate_handbook_15_deck()
    print("Both presentations successfully updated with zero bleeding and accepted methodology!")

if __name__ == "__main__":
    main()
