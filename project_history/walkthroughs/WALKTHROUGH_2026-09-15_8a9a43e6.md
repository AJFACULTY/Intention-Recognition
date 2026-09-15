# Autonomous Mobile Robot Cognition System
## Undergraduate Final Defense Preparation, Slide Audit & Operational Runbook Walkthrough

**Authors:** Eleana Osei Owusu (4121230024) & Joel Nii Adjetey Ahulu (4121230020)  
**Supervisor:** Mr. Micheal Xenya  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering  

---

## Changes Made & Deliverables Created

### 1. Technical Glossary & Complete Master Acronyms Guide
**Location:** [`write_up/GLOSSARY_AND_ACRONYMS_GUIDE.md`](file:///home/j/ros2_cognition_ws/write_up/GLOSSARY_AND_ACRONYMS_GUIDE.md)
- **Part I: Complete Master Acronyms Directory (73 Acronyms A to Z):**  
  Every single acronym across Chapters 1 to 5 and the presentation slides (ADE, AMCL, BPTT, DDS, DWB, EKF, ERQ, FDE, FSM, FoV, FPS, IBVS, IMU, IQR, ISO, LiDAR, LPDDR4X, LSTM, MLP, MPPI, ONNX, OOM, PID, PWM, QoS, RMW, ROS 2, sEMG, SLAM, TF2, UART, URDF, etc.) with:
  - Official expansion
  - Formal technical engineering definition
  - Exact implementation context in this project
  - Plain-English layperson analogy for non-technical panel members
- **Part II: Non-Everyday English & Specialized Robotics Terms:**  
  Detailed mathematical intuition, coordinate frames, and robotic roles for terms such as *Quaternion, Odometry & Dead-Reckoning, Kinematics, Non-Holonomic Constraints, Occupancy Grids, Costmap Inflation Layers, Covariance Matrices, Yaw Drift, Domain Shift, Softmax, ReLU, Determinism, Micro-ROS Agent vs. Client, and ISO 15066 Speed and Separation Monitoring*.

---

### 2. Forensic PowerPoint Audit & GCTU Handbook Standards Review
**Location:** [`write_up/PRESENTATION_AUDIT_AND_IMPROVEMENT_PLAN.md`](file:///home/j/ros2_cognition_ws/write_up/PRESENTATION_AUDIT_AND_IMPROVEMENT_PLAN.md)
- **Preserved Backup:** [`write_up/Project Final Defense Slides_ORIGINAL_BACKUP.pptx`](file:///home/j/ros2_cognition_ws/write_up/Project%20Final%20Defense%20Slides_ORIGINAL_BACKUP.pptx).
- **Forensic Discrepancy Matrix:** Identified and cataloged all 17 slide defects, including:
  - **Slide 1 Fatal Typo:** Changed *"A Project Work Topic Proposal..."* to *"A Final Project Report Submitted in Partial Fulfillment..."*.
  - **Student ID Correction:** Corrected Joel's index number from `4122530020` to `4121230020`.
  - **Slide 1 Clutter:** Removed redundant labels (`"TITLE:"`, `"PRESENTATION BY:"`).
  - **Duplicate Figures:** Fixed duplicate `Figure 13` across Slides 13 and 14.
  - **Typographical Errors:** Corrected `Folow` $\to$ `Follow`, `Righ` $\to$ `Right`, and `M200 LiDAR` $\to$ `MS200 LiDAR`.
- **Presentation Outline Audit:** Addressed user query regarding Slide 2; replaced the 15 flat, cognitive-overload bullets with a clean 5-Chapter structured thematic block matching GCTU thesis organization.
- **Objectives Formulation:** Rewrote all specific objectives to begin with the formal academic infinitive **"To..."**.
- **Problem Statement Justification:** Added ISO 15066 safety standards and cloud latency failure rate citations.
- **Handbook 15-Slide Limit Blueprint:** Complete mapping consolidating the 19 draft slides into the 15-slide cap prescribed by GCTU Project Handbook Section 1.6.

---

### 3. Oral Defense Master Q&A & Delivery Coaching Handbook
**Location:** [`write_up/ORAL_DEFENSE_MASTER_QNA_HANDBOOK.md`](file:///home/j/ros2_cognition_ws/write_up/ORAL_DEFENSE_MASTER_QNA_HANDBOOK.md)
- Comprehensive, mathematically grounded answers to all defense viva voce questions:
  1. *Why Raspberry Pi 5 (8GB)?* (Edge compute feasibility, Cortex-A76 @ 2.4 GHz, 8GB preventing OOM killer, Tier-1 ROS 2 Humble).
  2. *Why ESP32-S3?* (Hard real-time deterministic co-processor, microsecond PWM/encoder timers, micro-ROS 921,600 baud UART bridge).
  3. *Why LiDAR? What is LiDAR?* (Light Detection and Ranging, 360° FoV, lighting invariance, millimeter accuracy vs camera limitations).
  4. *Why ROS 2 Humble?* (Peer-to-peer DDS bus, QoS reliability policies, standard Nav2/SLAM stacks, fault isolation).
  5. *Literature Review Breakdown:* Deep dive into Tsitos et al., Mahmud et al., Li et al., Zafar et al., and their individual limitations.
  6. *The One Common Gap:* The Perception-Action Disconnect.
  7. *Problem Statement Empirical Justifications:* ISO 15066:2016 collaborative safety standards, distance domain shift.
  8. *Research Questions (ERQ 1–4):* Full alignment with Chapter 4 quantitative evidence (74.2 ms latency, 99.38% accuracy, 0.42 m stopping distance).
  9. *Engineering Methodology:* Detailed 6-phase pipeline workflow.
  10. *ROS 2 Concepts:* Exact definitions and project instances for Nodes, Topics, Messages, Services, Actions, Parameters, TF2, QoS, and Micro-ROS.
- **Presentation Delivery Coaching:** The "Anchor Method", the "Rule of Three", the "Story Arc" narrative, and techniques to de-escalate tough examiner questions without reading from the slides.

---

### 4. Physical Robot Full-System Operational Runbook
**Location:** [`write_up/SYSTEM_OPERATIONAL_TEST_AND_DEMO_RUNBOOK.md`](file:///home/j/ros2_cognition_ws/write_up/SYSTEM_OPERATIONAL_TEST_AND_DEMO_RUNBOOK.md)
- **4-Stage Narrative Arc:** Autonomous Waypoint Patrol $\to$ Human Approach & LSTM Motion Prediction $\to$ Corridor Blockage & ISO 15066 LiDAR Reactive Halt $\to$ Touchless Hand Gesture Preemption (`GO` / `FOLLOW` / `STOP`).
- **"No Bluff" Readiness Punch List (While Charging):**
  - Battery voltage threshold ($\ge 8.0\,\text{V}$ required; $<7.2\,\text{V}$ brownout risk).
  - Pre-flight hardware cable inspections (USB 3.0 camera, baseboard USB-C serial, LiDAR spin clearance).
  - Physical floor placement at Home Base $(0.08, 0.05, 0^\circ)$ to prevent AMCL particle dispersion.
- **Turnkey Execution Commands:** 1-command menu options and 3-terminal split-screen commands with live Web Visualizer projection (`:8080`).
- **Live Demonstration Troubleshooting Matrix:** 5-second rapid fixes for lost localization, camera glare, and false LiDAR stops.

---

### 5. Deployment Script Hardening
**Location:** [`scripts/sync_to_bot.sh`](file:///home/j/ros2_cognition_ws/scripts/sync_to_bot.sh)
- Added [`ml_models/weights/hand_landmarker.task`](file:///home/j/ros2_cognition_ws/ml_models/weights/hand_landmarker.task) (7.5 MB) to the host file synchronization and Docker container injection routines across `/root/cognition_ws/models/` and package share directories, preventing MediaPipe model initialization faults.

---

## Verification & Validation Results

1. **Slide Backup Integrity:** Preserved original PPTX verified intact at [`write_up/Project Final Defense Slides_ORIGINAL_BACKUP.pptx`](file:///home/j/ros2_cognition_ws/write_up/Project%20Final%20Defense%20Slides_ORIGINAL_BACKUP.pptx) (2.3 MB).
2. **Handbook Standards Cross-Check:** Verified against GCTU Undergraduate Project Handbook:
   - Margins, paragraph rules (>= 3 sentences), referencing standards (IEEE), and Section 1.6 presentation constraints (15 slides maximum).
3. **LaTeX Integrity:** Checked writeup chapter sources against glossary entries; all 73 acronyms and technical terms accurately reflect thesis text.
4. **Git Repository State:** All guides and script updates are staged and cleanly structured in the workspace.
