# Autonomous Mobile Robot Cognition System
## PowerPoint Defense Deck: Forensic Audit, Discrepancy Matrix & Enhancement Plan

**File Audited:** `write_up/Project Final Defense Slides.pptx`  
**Preserved Original Backup:** `write_up/Project Final Defense Slides_ORIGINAL_BACKUP.pptx`  
**Target Event:** BSc. Computer Engineering Final Project Oral Defense  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering  
**Authors:** Eleana Osei Owusu (4121230024) & Joel Nii Adjetey Ahulu (4121230020)  
**Supervisor:** Mr. Micheal Xenya  

---

## Executive Summary: Does the PowerPoint Meet Final Defense Standards?

### The Direct Verdict
**Partially.** While the slide deck contains the core technical elements of the work (hardware photos, confusion matrix, accuracy tables, and trajectory plots), in its current form it **violates several explicit academic standards** set by the GCTU Faculty of Engineering Handbook and suffers from critical typographical and structural errors that will attract immediate panel penalties if not corrected prior to defense day.

### Core Critical Issues Identified:
1. **Handbook Slide Count Violation:** GCTU Project Handbook Section 1.6 states: *"Students are required to prepare at most 15 PowerPoint slides that should give insight of their entire work after which they will proceed to demonstrate their software applications or hardware."* The current deck has **19 slides**.
2. **Proposal vs. Final Defense Fatal Wording:** Slide 1 explicitly states: *"A Project Work Topic Proposal in Partial Fulfillment..."*. Presenting a "Proposal" slide at a **Final Defense** tells examiners that the slide deck was recycled without diligence.
3. **Student ID Number Typo:** Joel's index number is typed as `4122530020` on Slide 1, whereas his official institutional index number is `4121230020`.
4. **Duplicate Figure Enumeration:** Slide 13 and Slide 14 are **both labeled Figure 13**.
5. **Presentation Outline Overload:** Slide 2 contains 15 flat, un-nested bullet points, confusing major chapter divisions with minor sub-topics.
6. **Objectives Grammar Defect:** The specific objectives in Slide 5 do not begin with the mandatory formal academic infinitive *"To..."*.
7. **Typographical Errors on Core Data:** Slide 15 contains misspelled gesture classes (`Folow` instead of `Follow`, `Righ` instead of `Right`), and Slide 10 refers to `M200 LiDAR` instead of `MS200 LiDAR`.

---

## 1. Forensic Discrepancy & Error Matrix

| Slide # | Current Slide Title | Identified Error / Discrepancy | Severity | Mandatory Correction |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Title Slide | Reads: *"A Project Work Topic Proposal in Partial Fulfillment..."* | **CRITICAL** | Change to: *"A Final Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of Bachelor of Science in Computer Engineering"*. |
| **1** | Title Slide | Joel's index number is typed as `4122530020`. | **CRITICAL** | Correct index number to `4121230020` (matching official transcript and thesis `main.tex`). |
| **1** | Title Slide | Cluttered with redundant text labels: `"TITLE:"`, `"PRESENTATION BY:"`, repetitive department names. | **MEDIUM** | Remove labels. Format author names cleanly with index numbers beneath; add Supervisor name: *Mr. Micheal Xenya*. |
| **2** | Presentation Outline | Contains 15 unstructured bullets. Places *"Research Gaps"* before *"Literature Review"*. | **HIGH** | Group into 5 logical chapter themes (matching the 5 thesis chapters). Place Literature Review before Gaps. |
| **4** | Problem Statement | Raw bullet points without empirical/industrial justification or grounding citations. | **HIGH** | Add explicit engineering justifications: ISO 15066 safety thresholds, cloud latency instability (>200 ms), and distance domain shift. |
| **5** | Objectives | Specific objectives start with raw verbs (`"Develop..."`, `"Train..."`, `"Implement..."`). | **HIGH** | Standardize every specific objective to start with **"To..."** (*"To design..."*, *"To construct..."*, *"To develop..."*, *"To implement..."*). |
| **6** | Significance & Gaps | Crammed with two distinct topics on a single slide; font size is excessively small. | **MEDIUM** | Split or streamline: move research gaps to follow the Literature Review table where they logically belong. |
| **7** | Literature Review | Table cells are cramped; author citations lack clear engineering takeaways. | **MEDIUM** | Ensure clear contrast between what each author did, their technical methodology, and the exact research gap left open. |
| **8** | Methodology | Displays a bare bullet list without any visual workflow or architectural block diagram. | **HIGH** | Replace with a high-level 6-Phase Engineering Pipeline diagram (Sensors $\to$ Preprocessing $\to$ Perception $\to$ Brain FSM $\to$ Nav2 $\to$ Chassis). |
| **9** | System Architecture | Lacks visual breathing room; label reads `"Figure 3:Hardware Architecture"` (missing space after colon). | **LOW** | Correct label spacing; ensure high-resolution rendering of hardware signal distribution. |
| **10** | Hardware Components | Refers to `"M200 LiDAR Sensor"`. | **MEDIUM** | Correct to **MS200 LiDAR Sensor** (Yahboom / Orbbec planar laser scanner). |
| **11** | Hardware Components | Figure 8, 9, 10 enumerate sub-components individually, spreading hardware across 2 slides. | **MEDIUM** | Merge Slides 10 & 11 into a single unified Mechatronics & Embedded Compute slide to satisfy the 15-slide limit. |
| **13** | Human Movement Prediction | Contains `"Figure 13: LSTM Loss and Trajectory Prediction"`. | **HIGH** | Keep as Figure 13. Ensure ADE/FDE metrics are highlighted prominently (**25.8 px / 32.4 px**). |
| **14** | SLAM Mapping & Localisation| Labeled `"Figure 13: Initial Run: 'Hourglass' Rotational Drift"`. | **CRITICAL** | **Duplicate figure number!** Rename to **Figure 14**. Highlight the EKF yaw drift resolution. |
| **15** | Testing & Results | Table row 3 reads **"Folow"**; Table row 5 reads **"Righ"**. | **HIGH** | Correct typos immediately to **"Follow"** and **"Right"**. |
| **16** | Testing & Results | Table lists movement classes, but duplicates the results theme of Slide 15. | **MEDIUM** | Consolidate physical gesture trials and kinematic trajectory results into a unified validation slide. |
| **17** | Conclusion & Future Works | Both Conclusion and Future Works crammed into one slide with competing bullet styles. | **MEDIUM** | Separate into crisp quantitative achievements (left) and realistic engineering recommendations (right). |

---

## 2. In-Depth Analysis: The Presentation Outline Slide (Slide 2)

### The User's Question: *"Is the content in the presentation outline okay though?"*
**Answer: No, the current presentation outline is suboptimal for three distinct reasons:**

1. **Cognitive Overload (15 Bullets):** Slide 2 currently throws 15 separate lines of text at the examiners:
   - *Introduction, Problem Statement, Objectives of Study, Significance of Study, Research Gaps, Literature Review, Methodology, System Architecture, Hardware and Software Components, Dataset Preparation and Gesture Recognition, SLAM, Testing and Results, Conclusion, Future works, References.*
   - In a 15-minute defense, an outline slide should be shown for **15 to 20 seconds maximum**. When a panel sees 15 tiny bullets, they cannot read them quickly, and it gives the impression that the project lacks high-level structure.
2. **Category Hierarchy Error:** "System Architecture", "Hardware and Software Components", "Dataset Preparation", and "SLAM" are **sub-sections of Chapter 3 (Methodology)**. Presenting them as top-level bullets on equal footing with "Methodology" is an academic formatting flaw.
3. **Flawed Logical Sequence:** The current outline lists *Research Gaps* BEFORE *Literature Review*. In rigorous academic engineering, you cannot identify research gaps before you review the literature. The gaps emerge directly *from* reviewing prior works.

### Recommended Redesign: The 5-Chapter Thematic Outline
Instead of 15 scattered bullets, organize Slide 2 into **5 structured blocks** that map directly to the 5 chapters of your GCTU thesis:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION OUTLINE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   01. INTRODUCTION & PROBLEM CONTEXT                                            │
│       • Motivation & Industrial Problem Statement                               │
│       • General & Specific Objectives | Engineering Research Questions (ERQs)   │
│                                                                                 │
│   02. LITERATURE REVIEW & RESEARCH GAPS                                         │
│       • Benchmark Prior Works (Tsitos et al., Mahmud et al., Li et al.)         │
│       • Theoretical Grounding & The Central Perception-Action Gap               │
│                                                                                 │
│   03. SYSTEM ARCHITECTURE & METHODOLOGY                                         │
│       • Mechatronic & Embedded Edge Architecture (Pi 5 + ESP32-S3 + LiDAR)      │
│       • Scale-Invariant 19-D Geometric Feature Pipeline & LSTM Motion Model     │
│       • ROS 2 Middleware, Brain FSM & Nav2 SLAM Integration                     │
│                                                                                 │
│   04. EXPERIMENTAL VALIDATION & RESULTS                                         │
│       • End-to-End Latency Budget & Real-Time Throughput Benchmark              │
│       • Gesture Classification Confusion Matrix & Physical Locomotion Trials   │
│                                                                                 │
│   05. CONCLUSION & ENGINEERING RECOMMENDATIONS                                 │
│       • Summary of Contributions & ISO 15066 Compliance                         │
│       • Limitations & Future Work | Live Hardware Demonstration                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```
*Why this wins over panels:* It immediately tells the examiners that you have a structured, disciplined engineering mindset and that your presentation mirrors the formal thesis book in their hands.

---

## 3. Addressing Specific Mock Defense Panel Feedback

### 1. "Minimize Content on the First Slide (Which slide will that be?)"
- **Clarification:** The first slide is **Slide 1 (The Title Slide)**.
- **Why the panel critiqued it:** Slide 1 currently has redundant labels ("TITLE:", "PRESENTATION BY:"), multiple institutional affiliations, and the fatal phrase *"A Project Work Topic Proposal"*.
- **The Optimal Slide 1 Structure:**
  - **Header:** GHANA COMMUNICATION TECHNOLOGY UNIVERSITY | FACULTY OF ENGINEERING | DEPARTMENT OF COMPUTER ENGINEERING
  - **Project Title (Large, Bold, Centered):** DEVELOPMENT AND IMPLEMENTATION OF A ROBOTIC APPLICATION FOR HUMAN INTENTION RECOGNITION USING MOTION AND HAND GESTURE
  - **Degree Qualification (Sub-header):** A Final Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of Bachelor of Science in Computer Engineering
  - **Authors (Two Columns or Clean Centered Block):**
    - **Eleana Osei Owusu** (Index: 4121230024)
    - **Joel Nii Adjetey Ahulu** (Index: 4121230020)
  - **Supervisor:** Mr. Micheal Xenya
  - **Date:** September 2026

### 2. "Write the Author Names in Full"
- Ensure no abbreviations like "Joel N. A. Ahulu" or missing middle names.
- Use exact registered names:
  1. **Eleana Osei Owusu** (4121230024)
  2. **Joel Nii Adjetey Ahulu** (4121230020)

### 3. "The Objectives Should Read as Follows: 'To...'"
On Slide 5, eliminate raw command verbs. Format all specific objectives using active infinitive verbs matching Chapter 1:
- **General Objective:**  
  *To design, implement, and empirically evaluate an edge-deployed, real-time human intention recognition and navigation system integrating scale-invariant hand gestures, temporal motion prediction, and spatial mapping into a unified ROS 2 middleware pipeline.*
- **Specific Objectives:**  
  1. **To design and implement** an edge-optimized vision pipeline utilizing 19 scale-invariant geometric hand features.
  2. **To construct and balance** a custom 6,000-sample gesture dataset captured directly through the onboard robot camera.
  3. **To develop** an LSTM recurrent neural network to forecast short-horizon operator trajectories from body pose landmarks.
  4. **To implement** a deterministic supervisory decision node (`brain_node`) with temporal majority voting and visual servoing.
  5. **To configure and validate** LiDAR SLAM and Nav2 autonomous navigation for collision-free spatial execution.
  6. **To quantitatively evaluate** end-to-end latency budgets, classification accuracy, and real-time physical throughput.

### 4. "Justify the Problem Statement"
On Slide 4, do not just list symptoms ("High computing demands", "Cloud dependence"). Provide the **engineering justifications**:
- **Why Cloud Fails:** Offboard cloud vision incurs round-trip network latencies exceeding $200\,\text{ms}$ and single-point Wi-Fi dropouts, violating real-time robotic safety reaction limits (citing Tsitos et al., 2022).
- **Why Raw Pixels Fail (Domain Shift):** Classifiers trained on raw pixel coordinates degrade when the user stands at varying distances ($1.0\,\text{m} \to 2.5\,\text{m}$) because pixel coordinates scale with distance.
- **Why Isolated Gesture Recognition is Dangerous:** Executing motion commands without continuous 360° laser mapping causes collisions with static furniture or unobserved bystanders.
- **Standards Justification:** ISO 15066:2016 requires guaranteed collaborative stopping separation distances ($S \le 0.45\,\text{m}$), impossible without integrated local costmaps and deterministic edge compute.

### 5. "Enumerate the Figures in the PowerPoint"
Every technical figure in the deck must follow standard engineering caption enumeration:
- `Figure 1: Conceptual Multi-Modal HRI Framework`
- `Figure 2: End-to-End System Deployment & Middleware Architecture`
- `Figure 3: Mechatronic Hardware Signal & Power Distribution`
- `Figure 4: Physical Yahboom 4WD Testbed & Sensor Assembly`
- `Figure 5: 21-Point Hand Skeleton & 19-D Geometric Feature Pipeline`
- `Figure 6: LSTM Trajectory Predictor Architecture & Displacement Error`
- `Figure 7: LiDAR 2D Occupancy Grid Facility Map & AMCL Particle Cloud`
- `Figure 8: 6-Class Gesture Classification Confusion Matrix (Physical Trials)`
- `Figure 9: End-to-End Component Latency Budget Breakdown (74.2 ms Total)`
- `Figure 10: Multi-Waypoint Autonomous Patrol & Dynamic Obstacle Avoidance Trajectory`

---

## 4. The 15-Slide Handbook Consolidation Blueprint

To strictly comply with GCTU Project Handbook Section 1.6 ("at most 15 PowerPoint slides"), we compress the 19-slide draft into 15 high-impact, professional slides:

| Slide # | Slide Title | Content & Visual Focus | Replaces Old Slides |
| :---: | :--- | :--- | :---: |
| **01** | **Title Page** | Minimalist, clean academic layout. Full names, supervisor, correct index numbers, "Final Project Report". | Slide 1 |
| **02** | **Presentation Outline** | 5-Chapter structured thematic blocks. | Slide 2 |
| **03** | **Introduction & Background** | HRI paradigm shift, edge AI necessity, contactless collaborative mobile robotics. | Slide 3 |
| **04** | **Problem Statement & Justification**| 3 core bottlenecks: Cloud latency, distance domain shift, ungrounded spatial motion + ISO 15066 justification. | Slide 4 |
| **05** | **Project Objectives & ERQs** | General Objective + 6 Specific Objectives ("To...") + 4 Engineering Research Questions. | Slide 5 |
| **06** | **Literature Review & Research Gaps**| Benchmark comparative matrix (Tsitos, Mahmud, Li) + Identification of the Central Perception-Action Gap. | Slides 6 & 7 |
| **07** | **System Architecture Overview** | High-level 4-tier architectural block diagram (Perception $\to$ Cognition $\to$ Middleware $\to$ Actuation). | Slide 8 & 9 |
| **08** | **Mechatronics & Embedded Hardware** | Raspberry Pi 5 SBC, ESP32-S3 Micro-ROS co-processor, MS200 LiDAR, dual-power rail regulation. | Slides 10 & 11 |
| **09** | **Scale-Invariant Gesture Pipeline** | 6,000-sample custom dataset, MediaPipe 21 landmarks $\to$ 19-D normalized geometric features $\to$ MLP classifier. | Slide 12 |
| **10** | **Predictive Motion Tracking (LSTM)**| Sequential human pose tracking, 10-frame sliding window, LSTM trajectory prediction (ADE: 25.8 px). | Slide 13 |
| **11** | **SLAM Mapping & Nav2 Navigation** | MS200 LiDAR 360° scan, SLAM Toolbox occupancy grid, AMCL localization, EKF yaw drift solution. | Slide 14 |
| **12** | **Experimental Results: AI & Latency**| Confusion matrix (99.38% test / 96.67% physical), component latency breakdown table (74.2 ms end-to-end). | Slide 15 |
| **13** | **Experimental Results: Locomotion & Safety** | Kinematic motion validation table, LiDAR obstacle avoidance corridor (<0.36m reactive reverse, ISO 15066). | Slide 16 |
| **14** | **Conclusion & Future Work** | Summary of contributions against ERQs 1–4, system limitations, concrete future engineering extensions. | Slide 17 |
| **15** | **References & Demonstration Transition** | Key IEEE citations [1–5] + "Thank You / Questions & Live Hardware Demonstration Transition". | Slides 18 & 19 |

---

## 5. Visual Design & Presentation Delivery Principles for High Honors

1. **The 6 $\times$ 6 Presentation Rule:** No slide should have more than 6 bullet points, and no bullet point should exceed 6–8 words. Slides are visual anchors for the speaker, not reading scripts for the audience.
2. **Visual Hierarchy & Contrast:** Dark headers with crisp blue/teal accent cards on a clean light or deep charcoal background. Avoid harsh pure black or generic rainbow colors.
3. **Data Over Adjectives:** Replace subjective statements like *"The model was very fast and accurate"* with quantitative engineering evidence: *"The 19-D MLP achieved 99.38% accuracy with an inference latency of 1.2 ms on the Raspberry Pi 5 CPU."*
4. **Hardware Demonstration Handover:** Slide 15 should end with an explicit invitation: *"We now invite the panel to observe the live physical hardware demonstration of autonomous patrol, human intention prediction, and touchless gesture control."*
