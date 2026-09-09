# Undergraduate Thesis Completion Roadmap & TO-DO List

**Project Title:** Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering, Department of Computer Engineering  
**Authors:** Eleana Osei Owusu (4121230024), Joel Nii Adjetey Ahulu (4121230020)  
**Supervisor:** Mr. Micheal Xenya  

---

## 1. Incremental Chapter Progress Checklist

### [x] Chapter 1: Introduction (COMPLETED)
- [x] Refine Background to emphasize edge computing and shared-workspace collaborative robotics.
- [x] Tighten Problem Statement (hardware resource constraints, domain shift, ungrounded mobile intention).
- [x] **Incorporate Engineering Research Questions (ERQs):**
  - **ERQ 1 (Edge Feasibility & Latency Budget):** *Can a multi-stage vision pipeline (spatial filtering, 21-point hand landmarking, and geometric feature extraction) execute entirely on a low-cost, low-power edge processor (Raspberry Pi 5) without GPU acceleration or cloud connectivity while sustaining an end-to-end latency below 150 ms?*  
    *(Validated in Ch 4 via latency breakdown and Table 4.6 throughput measurements).*
  - **ERQ 2 (Feature Invariance & Generalization):** *To what extent does converting raw anatomical hand landmark coordinates into scale- and distance-invariant geometric features eliminate perspective/scale variance and improve classification accuracy across varying operator distances compared to raw coordinate baselines?*  
    *(Validated in Ch 4 via 99.38% test accuracy, Table 4.1 physical spread, and confusion matrix).*
  - **ERQ 3 (Multi-Person Workspace Disambiguation):** *How effectively can a central spatial-zone filter coupled with temporal majority-vote buffering isolate and maintain lock on an active operator in a shared space, preventing false triggers from background bystanders?*  
    *(Validated in Ch 3/4 via acceptance zone filtering logic and 3-second operator lock).*
  - **ERQ 4 (Intention-to-Action Middleware Coupling & Safety):** *Can discrete hand gesture commands and continuous kinematic motion trajectories be reliably integrated within ROS 2 middleware to govern autonomous mobile robot navigation and reactive collision avoidance in compliance with ISO 15066 collaborative safety thresholds?*  
    *(Validated in Ch 4 via Table 4.3 robot velocity execution, emergency stop preemption, and obstacle response).*
- [x] Verify General and Specific Objectives alignment with Chapters 3, 4, and 5.
- [x] Ensure Scope and Significance align with GCTU engineering thesis criteria.
- [x] Verify that every paragraph contains at least three sentences with no first-line indentation.

### [x] Chapter 2: Literature Review (COMPLETED)
- [x] Verify all citations against `references.bib` (IEEE numbered format).
- [x] Check theoretical grounding: HRI theory, human intention theory, kinematic motion estimation, multi-modal fusion.
- [x] Review of 3 core works (Tsitos et al., Mahmud et al., Li & Zhang et al.) with clear strengths, limitations, and research gaps.
- [x] Landscape comparative summary table (Table 2.1) covering additional works (Yu et al., Laplaza et al., Liang & Zheng, Muhtadin et al.).
- [x] Add explicit discussion comparing camera-based tracking with wearable/sEMG alternatives (Zafar et al.).
- [x] Ensure all paragraphs contain at least three sentences with no first-line indentation.

### [x] Chapter 3: System Design and Methodology (COMPLETED)
- [x] **Remove Laptop Brand:** Replaced all occurrences of "Lenovo" / "Lenovo V15 ADA" with generic specifications (`x86_64 host workstation (AMD Ryzen 5, 8GB RAM)`).
- [x] **Figure 3.1 Replacement:** Generated high-resolution hardware schematic (`hardware_design.png`).
- [x] **Figure Y Replacement:** Generated System Deployment Diagram (`fig_docker_deployment.png`).
- [x] **Figure Z Replacement:** Generated Spatial Zone Filter Visualization (`fig_spatial_zone.png`).
- [x] **Figure Placeholder Replacement:** Generated Feature Extraction Pipeline Diagram (`fig_feature_pipeline.png`).
- [x] **Figure Placeholder Replacement:** Generated UML Brain Node State Machine Diagram (`fig_brain_state_machine.png`).
- [x] Embedded existing LSTM path predictor loss and prediction examples (`path_predictor_loss.png`, `path_prediction_examples.png`).
- [x] Detailed RAM upgrade (2GB to 8GB Pi 5) and the resolution of Linux OOM killer faults.
- [x] Detailed SLAM reliability diagnosis (EKF transform race condition and disabled yaw fusion fix).
- [x] **Engineering Standards Compliance (Section 3.11):** Formally documented compliance with ISO 15066:2016, ISO 12100:2010, ROS REP-103/REP-105, and OMG DDS v1.4 QoS.
- [x] Ensure all paragraphs contain at least three sentences with no first-line indentation.

### [x] Chapter 4: Testing, Results and Analysis (COMPLETED)
- [x] **Table 4.3 Replacement (Gesture-Based Robot Control):** Populated all fields with empirical physical velocity, latency, and status measurements.
- [x] **Table 4.4 Replacement (Obstacle Avoidance & Mapping):** Replaced all fields with honest physical LiDAR scan/costmap evaluations and Nav2 bringup diagnostics.
- [x] Embedded Confusion Matrix (`MLP_Confusion_Matrix.png`).
- [x] Expanded quantitative latency budget table (Camera capture $\to$ MediaPipe $\to$ MLP $\to$ DDS $\to$ UART $\to$ Motor actuation = 132 ms).
- [x] Added in-text citations connecting measured response latency to ISO 15066 collaborative robot safety reaction thresholds.
- [x] Hardware resource benchmarking (CPU 311% across 4 cores, memory headroom, thermal stability).
- [x] Benchmarking against reviewed literature (Mahmud et al., Tsitos et al., Muhtadin et al.).
- [x] Formal evaluation of the 4 Engineering Research Questions (ERQs).
- [x] Ensure all paragraphs contain at least three sentences with no first-line indentation.

### [x] Chapter 5: Conclusion and Recommendation (COMPLETED)
- [x] Review Summary of the Study against original specific objectives.
- [x] Reiterate key contributions: edge-only inference, 99.38% test accuracy, 96.67% physical accuracy, 132 ms latency budget without GPU/cloud.
- [x] Articulate limitations honestly (small participant pool, lighting sensitivity, Nav2 autonomous navigation constraints, unintegrated face recognition node).
- [x] Expand actionable engineering recommendations (closed-loop PID for visual servoing, active gimbal tracking, serialized SLAM state saving, industrial safety interlocks).
- [x] Ensure all paragraphs contain at least three sentences with no first-line indentation.

---

## 2. Preliminary Pages & Front Matter (To Be Finalized After Chapters)
- [ ] GCTU Title Page formatted per Appendix A of GCTU Handbook.
- [ ] Declaration & Certification Page formatted per Appendix B (Supervisor & HOD signature lines).
- [ ] Abstract: Exactly one single paragraph between 150 and 250 words.
- [ ] Table of Contents, List of Tables, List of Figures, List of Abbreviations.
- [ ] Formal Acknowledgments section.

---

## 3. Formatting & Engineering Standards Verification
- [ ] Margins: Top = 2.5 cm, Bottom = 2.5 cm, Left = 4.0 cm, Right = 2.5 cm.
- [ ] Line spacing: 1.5 spacing.
- [ ] Paragraph rule: No first-line indentation (`\parindent 0pt`), minimum 3 sentences per paragraph, clear paragraph spacing (`\parskip 1em`).
- [ ] Captions: Tables on top, Figures below; linked to chapter numbers.
- [ ] Page length: Aim for comprehensive coverage meeting the degree minimum page standard.
