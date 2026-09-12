# Undergraduate Thesis Completion Roadmap & TO-DO List

**Project Title:** Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering, Department of Computer Engineering  
**Authors:** Eleana Osei Owusu (4121230024), Joel Nii Adjetey Ahulu (4121230020)  
**Supervisor:** Mr. Micheal Xenya  

---

## 1. Incremental Chapter Progress Checklist

### [ ] Chapter 1: Introduction — In-Depth Review & Technical Audit
- [ ] Comprehensive read-through of Background to ensure modern collaborative robotics & edge AI context is cohesive.
- [ ] Audit Problem Statement for crisp technical clarity on edge compute limits, perspective domain shift, and collaborative safety.
- [ ] Verify Engineering Research Questions (ERQ 1–4) formulations match exactly with Chapter 4 quantitative validations:
  - ERQ 1: Edge Feasibility & Latency Budget (< 150 ms)
  - ERQ 2: Feature Invariance & Generalization (19-D geometric vector vs raw pixels)
  - ERQ 3: Multi-Person Workspace Disambiguation (Spatial zone & majority voting)
  - ERQ 4: Intention-to-Action Middleware Coupling & Safety (ROS 2 DDS & ISO 15066)
- [ ] Confirm General and Specific Objectives map directly to experimental milestones and Chapter 5 conclusions.
- [ ] Verify Scope and Delimitations clearly define the physical testbed boundaries.
- [ ] Ensure 100% compliance with GCTU handbook formatting rules (minimum 3 sentences per paragraph, zero indentation, no commercial laptop brand names).

### [ ] Chapter 2: Literature Review — In-Depth Review & Technical Audit
- [ ] Re-verify theoretical grounding in Human-Robot Interaction (HRI), human intention theory, and multimodal sensor fusion.
- [ ] Deep-dive review of the three core benchmark studies (Tsitos et al., Mahmud et al., Li & Zhang et al.), ensuring critical appraisal of their methodologies and limitations.
- [ ] Verify Table 2.1 (Comparative Literature Matrix) matches in-text citations and metric comparisons.
- [ ] Review the camera-based optical tracking vs. wearable/sEMG sensor trade-off discussion (Zafar et al.).
- [ ] Check every in-text citation against `references.bib` to ensure 100% IEEE citation key alignment.
- [ ] Confirm paragraph structure rules (minimum 3 sentences per paragraph, zero indentation).

### [x] Chapter 1: Initial Drafting (COMPLETED & PREVIOUSLY INTEGRATED)
- [x] Refine Background to emphasize edge computing and shared-workspace collaborative robotics.
- [x] Tighten Problem Statement (hardware resource constraints, domain shift, ungrounded mobile intention).
- [x] Incorporate Engineering Research Questions (ERQs 1-4).
- [x] Verify General and Specific Objectives alignment with Chapters 3, 4, and 5.
- [x] Ensure Scope and Significance align with GCTU engineering thesis criteria.
- [x] Verify that every paragraph contains at least three sentences with no first-line indentation.

### [x] Chapter 2: Initial Drafting (COMPLETED & PREVIOUSLY INTEGRATED)
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

## 1.5. Systematic Figure-by-Figure Textual Interpretation Audit
*Sequential verification of each figure's visual rendering, caption, in-text citation, callout, and descriptive analysis in the thesis body text:*
- [ ] **Figure 3.1 (`assembled_robot_real.jpg`):** Fully assembled robot photo — Verify caption, mechatronic component labels, and mounting positions in §3.2.1.
- [ ] **Figure 3.2 (`raspberry_pi_5.jpg`):** Raspberry Pi 5 SBC — Verify 8GB RAM specifications, edge compute role, and thermal dissipation context in §3.2.2.
- [ ] **Figure 3.3 (`microros_control_board.jpg`):** Yahboom micro-ROS ESP32-S3 board — Verify UART bridge description, pin assignments, and motor driver specs in §3.2.3.
- [ ] **Figure 3.4 (`ms200_lidar.jpg`):** MS200 2D ToF LiDAR — Verify 12.5 Hz scan rate, 12 m radius, and safety plane coverage in §3.2.4.
- [ ] **Figure 3.5 (`camera_gimbal.png`):** 2-DOF Camera Gimbal — Verify pan/tilt servo travel limits, optical axis centering, and active tracking text in §3.2.5.
- [ ] **Figure 3.6 (`robot_chassis_wiring.jpg`):** Internal Chassis Wiring — Verify split power bus, buck converter, and motor inductive isolation text in §3.2.6.
- [ ] **Figure 3.7 (`system_architecture.png`):** System Architecture & Cognitive Flow — Verify 6-tier pipeline, ROS 2 topic names, message types, and emergency safety bypass line in §3.4.
- [ ] **Figure 3.8 (`hardware_design.png`):** Mechatronic Hardware Schematic — Verify electrical power distribution (7.4V/12.6V motor bus vs 5V/5A logic bus) and UART pinouts in §3.4.
- [ ] **Figure 3.9 (`fig_docker_deployment.png`):** Multi-Container Docker Deployment — Verify container breakdown (`yahboom_base`, `micro_ros_agent`, `yahboom_gesture`), `--net=host` loopback, and workstation Wi-Fi DDS bridge in §3.5.
- [ ] **Figure 3.10 (`fig_spatial_zone.png`):** Camera FOV Spatial Acceptance Zone — Verify central $45\% \times 65\%$ coordinate boundaries ($X \in [176, 464]$, $Y \in [84, 396]$), operator error vector, and bystander rejection text in §3.7.1.
- [ ] **Figure 3.11 (`fig_feature_pipeline.png`):** 4-Stage Geometric Feature Extraction Pipeline — Verify 21 MediaPipe hand landmarks, 19-D invariant feature derivations, vector assembly, and MLP inference in §3.7.3.
- [ ] **Figure 3.12 (`path_predictor_loss.png`):** LSTM Path Predictor Training Loss Curve — Verify 150-epoch MSE loss curve discussion, convergence stability, and Adam optimizer parameters in §3.7.4.
- [ ] **Figure 3.13 (`path_prediction_examples.png`):** Multi-Step Kinematic Trajectory Prediction — Verify 6-panel test trajectory interpretation, ADE (25.8 px) / FDE (32.4 px) metrics, and visual anticipation text in §3.7.4.
- [ ] **Figure 3.14 (`fig_brain_state_machine.png`):** Supervisory Brain Node UML State Machine — Verify 5 states, 5-frame rolling consensus, 3.0s command lock, visual servoing steering, and LiDAR (<0.36m) emergency halt preemption in §3.8.
- [ ] **Figure 3.15 (`room_map_20260810_0452.png` & `room_map_clean.png`):** Platform Calibration SLAM Maps Comparison — Verify text comparing Subfigure (a) "hourglass" rotational drift defect against Subfigure (b) Ceres scan-matching calibrated clean map in §3.9.
- [ ] **Figure 4.1 (`per_class_accuracy_chart.png`):** Per-Class Gesture Classification Accuracy Bar Chart — Verify per-class test set percentages (99.1% to 99.8%) and comparative discussion against physical interaction trials in §4.3.2.
- [ ] **Figure 4.2 (`MLP_Confusion_Matrix.png`):** Normalized MLP Gesture Confusion Matrix — Verify true vs predicted label matrix, off-diagonal error analysis, and hand tilt angle discussion in §4.4.
- [ ] **Figure 4.3 (`nav_run_trajectory_empirical.png`):** Empirical Physical Navigation Benchmark Trajectory & Kinematics — Verify 3-panel plot interpretation (2D spatial path, heading deviation $-40.5^\circ$ costmap clearance arc, and $0.236\,\text{m/s}$ velocity cruise/deceleration) in §4.5.

---

## 1.6. Overleaf Online Thesis Synchronization Checklist
*Tasks required to synchronize local Git and LaTeX improvements with the primary Overleaf cloud project:*
- [ ] **Upload All Publication Figures:** Upload all updated figures (`hardware_design.png`, `system_architecture.png`, `fig_spatial_zone.png`, `fig_feature_pipeline.png`, `fig_brain_state_machine.png`, `fig_docker_deployment.png`, `nav_run_trajectory_empirical.png`) to the `figures/` folder on Overleaf.
- [ ] **Sync Chapter 3:** Replace `chapters/ch3_methodology.tex` on Overleaf with the updated local version containing the real hand landmark pipeline, empirical spatial zone with privacy blur, and formal workstation nomenclature.
- [ ] **Sync Chapter 4:** Replace `chapters/ch4_results.tex` on Overleaf with the updated local version containing the empirical navigation benchmark (§4.5.2) and telemetry metrics.
- [ ] **Sync Chapter 5:** Replace `chapters/ch5_conclusion.tex` on Overleaf with the refined limitation text acknowledging the successful lightweight ROS 2 bag telemetry validation.
- [ ] **Verify Overleaf Compilation:** Recompile full document on Overleaf to confirm zero compilation errors, zero missing figure warnings, and clean table floats.

---

## 1.7. Overleaf Reviewer & Supervisor Feedback Action Plan
*Directly addressing the three critical supervisor/reviewer comments posted on Overleaf:*

### [x] 1. Literature Result Reporting Analysis & Python Test Logging Script
- [x] **Literature Result Reporting Patterns:**
  - Audit recent peer-reviewed HRI and robotics literature (e.g. IEEE Transactions on Human-Machine Systems, Robotics and Autonomous Systems, Automation in Construction) to extract standard reporting conventions (confusion matrices, latency breakdowns, mean $\pm$ standard deviation, boxplots, success rates under distance and lighting variations).
- [x] **Python Live Experiment Logger (`scripts/experiment_logger.py`):**
  - Develop a dedicated Python/ROS 2 test logging node that subscribes to `/cognition/gesture`, `/camera/image_raw`, `/cmd_vel`, `/scan`, `/odom_raw`, and `/diagnostics`.
  - Record structured empirical test trials into standard `.csv` files (`experiment_logs/trial_data.csv`).
  - Fields logged: `trial_id`, `timestamp`, `participant`, `distance_m`, `lighting`, `ground_truth`, `predicted`, `is_correct`, `confidence`, `consensus_votes`, `e2e_latency_ms`, `linear_cmd`, `angular_cmd`, `min_lidar_m`, `safety_status`.

### [ ] 2. Comprehensive Bibliography & References Overhaul
- [ ] **Investigate Overleaf Citation Visibility:**
  - Identify why only two references were appearing in the compiled Overleaf bibliography (ensure BibTeX/biber correctly resolves all keys and citations are called via `\cite{}` rather than plaintext).
- [ ] **Expand `references.bib`:**
  - Broaden the bibliography beyond the initial set to include 25+ high-impact peer-reviewed journal and conference publications spanning:
    - Edge Deep Learning & Real-Time Computer Vision (YOLO, MediaPipe, MobileNet, ONNX).
    - ROS 2 Architecture, DDS Middleware, and Real-Time Robot Operating Systems.
    - Human-Robot Interaction (HRI), Touchless Gesture Interfaces, and Ergonomic Cobots.
    - 2D LiDAR SLAM, Cartographer, Ceres Scan-Matching, and Nav2 Costmaps.
    - Safety Standards: ISO 15066:2016, ISO 12100:2010, ROS REP-103/105.
- [ ] **Enrich In-Text Citations Across Chapters 1–5:**
  - Strategically embed citations throughout Chapters 1, 2, 3, 4, and 5 to demonstrate deep scholarship and contextual grounding.

### [x] 3. Statistical Analysis of Logged Data (.csv)
- [x] **Statistical Processing Script (`scripts/analyze_trial_data.py`):**
  - Ingest acquired experimental CSV datasets using Python (`pandas`, `scipy.stats`, `numpy`).
  - Compute central tendency and dispersion metrics: Mean, Median, Standard Deviation, Interquartile Range (IQR), and 95% Confidence Intervals for:
    - Classification accuracy across 6 gesture classes.
    - Latency per pipeline stage (capture $\to$ MediaPipe $\to$ MLP $\to$ DDS $\to$ UART $\to$ motor response).
    - Physical stopping distance upon emergency preemption (< 0.36 m).
- [x] **Hypothesis Testing & Inferential Statistics:**
  - Perform Two-Sample $t$-tests and One-Way ANOVA across operational distances (1.0m, 1.75m, 2.5m) and lighting environments (natural daylight vs. artificial fluorescent).
  - Verify statistical significance ($p < 0.05$ or $p > 0.05$ for scale invariance) to prove geometric invariance and spatial zone robustness.
- [x] **Publication-Grade Statistical Plots for Chapter 4:**
  - Generate boxplots with scatter jitter points for latency distributions (`fig_latency_boxplot.png`).
  - Generate confidence interval plots and error-bar charts comparing accuracy across operating conditions (`fig_accuracy_by_condition.png`).
  - Update Chapter 4 text and tables with the derived inferential statistical values.

### [x] 4. Visual Fine-Tuning & Aesthetic Polish of Thesis Figures
- [x] **Figure Fine-Tuning & Layout Polish:**
  - Continuously fine-tune font sizes, bounding box padding, line weights, and text clearances across all 6 core publication figures (`hardware_design.png`, `system_architecture.png`, `fig_spatial_zone.png`, `fig_feature_pipeline.png`, `fig_brain_state_machine.png`, `fig_docker_deployment.png`).
  - Verify that all embedded hardware and telemetry photographs strictly preserve 1:1 native aspect ratio with zero pixel stretch or distortion.
  - Audit whitespace utilization, container balance, and high-contrast typography across both digital PDF and monochrome print renderings.
  - Align figure sub-labels, callouts, and captions with the final compiled chapter narratives.

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
8. **OpenCV V4L2 Buffer Starvation (`select() timeout`):** In `camera_pub.py`, configuring `CAP_PROP_BUFFERSIZE = 1` starved the Linux UVC kernel ring-buffer, causing OpenCV `cap_v4l.cpp` to block for 10.0 seconds per frame. Solved by removing the manual buffer restriction, restoring a deterministic 20.006 Hz capture rate (std dev $0.00008\text{ s}$).
9. **Pan Servo Cable Drag & Mechanical USB Disconnects:** A wide $\pm 50^\circ$ search sweep arc physically pulled the camera USB ribbon cable against the port, causing kernel `USB disconnect` drops during bench testing. Solved by calibrating a cable-safe $\pm 28^\circ$ sweep arc and routing a loose slack strain-relief loop around the pan/tilt bracket.
10. **Fronto-Parallel vs. Lateral Pointing Disambiguation:** Planar gestures (`STOP`, `GO`, `FOLLOW`) present fronto-parallel silhouettes with 99.38% test accuracy, but horizontal pointing (`LEFT`, `RIGHT`) suffered landmark depth foreshortening when using strict vertical Cartesian rules. Solved by evaluating lateral coordinate displacement ($\Delta x$) relative to the metacarpophalangeal (MCP) joint alongside the trained MLP.

## 5. Current Physical Robot & Deployment Status (Robot Powered On & Online)
*Verified technical status and live robot connectivity:*
- [x] **Physical Robot Powered On & Network Reachable:** Confirmed physical Raspberry Pi 5 car is active, connected to local network, and responsive to ping at `10.27.122.136` (`raspberrypi.local`, ~10 ms latency).
- [x] **Verified Ground-Truth Path Prediction Status on Physical Bot:** Confirmed `path_predictor.onnx` is present on the robot and successfully loaded into memory by ONNXRuntime in `person_detection_node.py` (`Path predictor ONNX loaded (threads=2)`). Acknowledged that runtime loop computes 1st-order linear velocity extrapolation (`predicted_x = cx + vx * 0.5`).
- [x] **Restored True 19-Feature Invariant MLP Gesture Engine:** Synchronized the balanced 6,000-sample Campaign 2 dataset (`gesture_dataset.csv`, 1,000 samples per class) and the trained 19-feature MLP weights (`gesture_model_features.pkl`, `scaler_features.pkl`, `label_encoder_features.pkl`, `gesture_model.onnx`, `path_predictor.onnx`) into `ml_models/`.
- [x] **Upgraded `gesture_node.py` Architecture:** Made the 19-feature MLP the primary classifier (Tier 1) via `hand_features.py` (99.50% holdout accuracy across all 6 classes), with the anatomical geometric engine acting as secondary fallback (Tier 2).
- [x] **Resolved Active Vision Gimbal Bugs:** Fixed FSM target loss ($z \le 0$ drops `latest_target` to trigger `MEMORY_HOLD`) and decoupled face tracking timestamp (`last_face_time`) from target timestamp, eliminating the 2 Hz artificial throttling bug.
- [x] **Enhanced Bench Monitor HUD Legend:** Updated `scripts/bench_autonomy_monitor.py` to explicitly display all 6 gestures (`STOP`, `GO`, `FOLLOW`, `LEFT`, `RIGHT`, `BACK`) and their corresponding robot reactions.
- [x] **Master Verification Suite (100% Green PASS):** Executed `scripts/run_all_local_verifications.py`, passing all 5 local unit & integration test suites in 18.10s (`test_perception_throttling`, `test_active_vision_logic`, `test_face_recognition`, `test_brain_logic`, `test_gesture_mlp`).
- [x] **Packaged One-Click Robot Sync Script:** Created and made executable `scripts/sync_to_bot.sh` for seamless container deployment.
- [x] **Live Container Sync to Physical Bot (COMPLETED):** Executed `./scripts/sync_to_bot.sh 10.27.122.135` (100% transfer and container injection into `yahboom_gesture`).
- [x] **Live Bench Pipeline Launch Verified:** Launched `bash ~/start_bench_pipeline.sh` on physical robot; verified all 5 autonomy nodes (`camera_pub`, `person_detection`, `active_vision`, `gesture_node`, `brain_node`), battery reporting 79-80% (Healthy), active gimbal search, and clean Ctrl+C signal traps.
- [ ] **Current Hardware State (Battery Recharging):** Robot battery is currently charging on the 12.6V balance charger after physical benchmarks. Offline planning and logic refinement in progress.
- [ ] **FOLLOW Gesture Logic & Visual Servoing Refinement:**
  - Audit and tune proportional steering response ($v_\omega = -K_p \cdot e_x$) in `brain_node.py` during `FOLLOW` mode.
  - Refine social distance holding threshold (smooth deceleration when operator box width $> 0.40$ or LiDAR $< 0.50$ m to prevent overshoot).
  - Gimbal-chassis tracking coordination: couple gimbal pan angle to chassis heading commands so the chassis turns into the direction the gimbal is looking.
- [ ] **Bench Autonomy Pipeline Hardening & Display Polish:**
  - Polish `bench_autonomy_monitor.py` ANSI escape sequence redraws to ensure rock-solid in-place terminal HUD without duplicate header scrolling.
  - Live qualification of all 6 gestures (`STOP`, `GO`, `FOLLOW`, `LEFT`, `RIGHT`, `BACK`) with operator in active acceptance zone.
- [ ] **Nav2 Multi-Waypoint & Room Patrol Implementation Plan (On Deck Post-Charge):**
  - [ ] **Task 9.3.1:** Implement `scripts/navigate_waypoints.py` CLI supporting `NavigateThroughPoses` and sequential `NavigateToPose` with distance-remaining feedback, ETA, and Ctrl+C emergency stop.
  - [ ] **Task 9.3.2:** Implement `scripts/run_nav2_patrol.sh` with automatic non-saturating bag recorder (`/tf`, `/odom_raw`, `/odometry/filtered`, `/scan`, `/cmd_vel`, `/amcl_pose`, `/plan`).
  - [ ] **Task 9.3.3:** Implement `scripts/plot_multi_waypoint_trajectory.py` to extract bag telemetry and generate empirical multi-waypoint tracking curves (MAE, cross-track error, velocity profiles).
  - [ ] **Task 9.3.4:** Execute Return-to-Home mission ($(1.44\,\text{m}, 0.02\,\text{m}) \to (0.00\,\text{m}, 0.00\,\text{m})$) and 3-waypoint room patrol loop.
  - [ ] **Task 9.3.5:** Validate dynamic obstacle avoidance and costmap clearing when operator steps into patrol path.
- [ ] **Milestone 10 (Master 6-Phase Live Hardware Verification Gate):** Execute live hardware verification matrix.

---

## 6. Model Names & Naming Polish (To-Do Later)
- [ ] Review and standardize neural network and model nomenclature across chapters during final polish.

---

## 7. Advanced Mathematical Formulations (Kept in Reserve / To-Do Later)
*Mathematical derivations kept in reserve on the to-do list so the main write-up remains friendly, accessible, and not overly dense:*
- [ ] Vector palm-width normalization equations ($D_{\text{norm}, i} = D_i / W_{\text{palm}}$).
- [ ] 3D cosine finger curl joint angle equations ($\theta_{\text{curl}} = \arccos\left(\frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}\right)$).
- [ ] Formal bounding box centroid calculation ($B_x = x_{\text{min}} + w/2$, $B_y = y_{\text{min}} + h/2$).
- [ ] Discrete temporal majority-vote mathematical definition ($\sum_{k=1}^N \mathbb{I}(g_k = g) \ge \tau$).
- [ ] EKF state vector and covariance equations for sensor fusion.
