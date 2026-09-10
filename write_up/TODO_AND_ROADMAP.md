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
- [x] Reiterate key contributions: edge-only inference, 99.38% test accuracy, 96.67% physical accuracy across 180 trials, 132 ms latency budget without GPU/cloud.
- [x] Articulate limitations honestly: small participant pool (180 trials), MicroSD I/O logging constraints (absence of high-bandwidth `rosbag2`), Nav2 autonomous validation scope (1.5 m linear goal vs. multi-room navigation), SLAM state serialization limits, container dependency/compute limits for onboard facial recognition, and kinematic decoupling of active gimbal during chassis visual servoing.
- [x] Eliminated phantom references to uncreated `test_logger_node.py`.
- [x] Expand actionable engineering recommendations into a **Dual-Mode Operational Architecture**:
  - *Mode 1 (Unmapped Environments):* Human-lead collaborative mapping ("Follow-to-Map" SLAM) and autonomous frontier exploration with reactive LiDAR safety bubble.
  - *Mode 2 (Mapped Environments):* Nav2 semantic waypoint navigation and socially-aware dynamic costmaps fusing LSTM human trajectory prediction.
  - *Hardware & Perception Extensions:* Kinematic gimbal-chassis TF2 coupling, edge NPU acceleration (Hailo-8) for concurrent ArcFace/YOLOv8, and PCIe NVMe logging.
- [x] Verify that 100% of body paragraphs contain at least three sentences with zero first-line indentation (`scripts/verify_writeup.py` PASS).

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

---

## 4. Pool of Engineering Battle Scars (Inventory to Select From)
*Practical engineering hurdles, diagnostics, and solutions to weave in naturally where appropriate:*
1. **The 2GB to 8GB RAM Upgrade (OOM Killer):** The initial 2GB Raspberry Pi 5 ran out of memory when running MediaPipe, camera capture, and ROS 2 nodes simultaneously; Linux kernel OOM killer terminated the vision process. Upgrading to 8GB provided the necessary headroom for smooth multi-node execution.
2. **EKF Yaw Sensor Fusion Race Condition:** In the `robot_localization` EKF node, fusing yaw velocity from differential drive wheel encoders caused transform race conditions and starburst map distortion during SLAM. Resolved by disabling yaw fusion in the EKF and letting LiDAR scan-matching handle heading.
3. **2-DOF Gimbal Sign Inversion & Servo Clamping:** During physical bench tests, panning had an inverted sign causing the camera to pan away from the human operator, and the STM32 board clamped angles below 0°. Solved with zero-centric recalibration and clamping fixes.
4. **Physical Cable Tension & Servo Stall:** Camera and servo USB ribbon cables caused physical drag on the pan/tilt mechanism, stalling the servos. Fixed through cable rerouting and strain relief.
5. **Perspective Scale Variance (Distance Domain Shift):** Raw pixel coordinates of hand landmarks caused classification to fail whenever the operator stood further away. Solved by calculating 19 scale-invariant geometric feature ratios (palm distance normalization and joint angles).
6. **Bystander Interference in Shared Spaces:** In crowded rooms, bystanders moving in the background caused false gesture triggers. Solved with a central spatial acceptance zone filter (center bounding box) and a rolling majority-vote temporal buffer.
7. **Open-Loop Gesture vs. Obstacle Collision:** A robot executing gestures blindly could crash into walls or furniture. Solved by linking LiDAR costmap inflation with an automatic reactive safety stop if an obstacle is within 0.35 m.

---

## 5. Model Names & Naming Polish (To-Do Later)
- [ ] Review and standardize neural network and model nomenclature across chapters during final polish.

---

## 6. Advanced Mathematical Formulations (Kept in Reserve / To-Do Later)
*Mathematical derivations kept in reserve on the to-do list so the main write-up remains friendly, accessible, and not overly dense:*
- [ ] Vector palm-width normalization equations ($D_{\text{norm}, i} = D_i / W_{\text{palm}}$).
- [ ] 3D cosine finger curl joint angle equations ($\theta_{\text{curl}} = \arccos\left(\frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}\right)$).
- [ ] Formal bounding box centroid calculation ($B_x = x_{\text{min}} + w/2$, $B_y = y_{\text{min}} + h/2$).
- [ ] Discrete temporal majority-vote mathematical definition ($\sum_{k=1}^N \mathbb{I}(g_k = g) \ge \tau$).
- [ ] EKF state vector and covariance equations for sensor fusion.
