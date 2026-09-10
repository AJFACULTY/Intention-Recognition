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

## 2. In-Depth Chapter & Visual Figure Review Checklists (Active Review Phase)

### 2.1 One-by-One Visual Figure & In-Text Interpretation Audit
*Detailed review protocol for all 18 figures (12 generated + 6 hardware photographs) to ensure visual clarity, caption accuracy, rigorous in-text interpretation, and empirical data alignment:*

- [ ] **Figure 3.1 (`assembled_robot_real.jpg` - §3.2.1):** Assembled Mobile Robot Platform.
  - [ ] Audit image sharpness, crop, and hardware visibility (chassis, LiDAR, 2-DOF gimbal, wheels).
  - [ ] Review LaTeX caption, figure placement, and cross-reference labels (`\label{fig:physical_robot}`).
  - [ ] Verify surrounding in-text description matches physical BOM specifications and dimensions.
- [ ] **Figure 3.2 (`raspberry_pi_5.jpg` - §3.2.2):** Raspberry Pi 5 Single-Board Computer.
  - [ ] Check macro photograph clarity and annotation of compute interfaces (USB 3.0, PCIe, GPIO).
  - [ ] Review paragraph detailing the ARM Cortex-A76 processor, 8GB LPDDR4X RAM, and cooling solution.
  - [ ] Ensure strict adherence to non-commercial branding (no retail laptop/consumer PC comparisons).
- [ ] **Figure 3.3 (`microros_control_board.jpg` - §3.2.3):** Yahboom micro-ROS ESP32-S3 Expansion Board.
  - [ ] Verify image shows motor terminal blocks, UART port, and onboard power regulation circuitry.
  - [ ] Check text explanation of real-time micro-ROS client firmware, FreeRTOS tasks, and 921,600 baud UART bridge.
- [ ] **Figure 3.4 (`ms200_lidar.jpg` - §3.2.4):** MS200 2D Time-of-Flight LiDAR Scanner.
  - [ ] Verify photographic detail of 360° rotating turret and optical transceiver window.
  - [ ] Check text description of 12.5 Hz scan frequency, 0.12 m–12.0 m ranging, and millimeter precision.
- [ ] **Figure 3.5 (`camera_gimbal.png` - §3.2.5):** 2-DOF Active Pan/Tilt Camera Gimbal Assembly.
  - [ ] Verify image quality showing horizontal (S1) and vertical (S2) micro-servos and monocular camera.
  - [ ] Review description of angular travel ranges ($\pm 45^\circ$ pan, $-20^\circ$ to $+35^\circ$ tilt) and visual servoing capability.
- [ ] **Figure 3.6 (`robot_chassis_wiring.jpg` - §3.2.6):** Internal Chassis Wiring & Power Routing.
  - [ ] Audit photo showing battery bay, step-down buck converter, and high-current motor lead separation.
  - [ ] Review text explaining inductive kickback isolation and separate logic (5V/5A) vs motor (7.4V/12.6V) power rails.
- [ ] **Figure 3.7 (`system_architecture.png` - §3.4):** System Architecture & End-to-End Cognitive Flow.
  - [ ] Verify 6-tier block diagram rendering (sensing, vision gating, MLP classification, brain FSM, DDS, micro-ROS).
  - [ ] Check ROS2 topic names (`/camera/image_raw`, `/scan`, `/cognition/gesture`, `/cmd_vel`) and latency budgets.
  - [ ] Review text explaining asynchronous emergency LiDAR preemption interlock (< 0.36 m) bypassing high-level FSM.
- [ ] **Figure 3.8 (`hardware_design.png` - §3.4):** Mechatronic Hardware Signal Flow & Power Distribution.
  - [ ] Check electrical schematic readability, connector pinouts, UART lines, and PWM signal paths.
  - [ ] Review in-text explanation of power bus decoupling (LM2596 buck converter) protecting the Raspberry Pi 5.
- [ ] **Figure 3.9 (`fig_docker_deployment.png` - §3.5):** Containerized Multi-Node Docker Deployment Topology.
  - [ ] Audit container boundaries (`yahboom_base`, `micro_ros_agent`, `yahboom_gesture`) and `--net=host` networking.
  - [ ] Check depiction of remote engineering workstation (`x86_64 Host Workstation`) over Wi-Fi DDS (`ROS_DOMAIN_ID=0`).
  - [ ] Review text explaining how Docker isolates Ubuntu 24.04 dependencies and prevents ROS2 Python conflicts.
- [ ] **Figure 3.10 (`fig_spatial_zone.png` - §3.7.1):** Camera FOV Spatial Acceptance Zone & Bystander Rejection.
  - [ ] Verify coordinate layout ($640 \times 480$), central $45\% \times 65\%$ zone, optical origin $(320, 240)$, and tracking error $e_x$.
  - [ ] Check visual differentiation between accepted operator (centroid inside zone) and rejected bystander (outside zone).
  - [ ] Review mathematical formulation of spatial gating and its role in answering ERQ 3.
- [ ] **Figure 3.11 (`fig_feature_pipeline.png` - §3.7.3):** 4-Stage Hand Landmark Geometric Feature Pipeline.
  - [ ] Audit 4 stages: MediaPipe 21 landmarks $\to$ 19-D geometric invariants $\to$ vector encoding $\to$ MLP classification.
  - [ ] Verify formula callouts (curl angles, fingertip spreads, palm-normalized Euclidean distances $D_{\text{norm}}$).
  - [ ] Review narrative explaining scale/distance invariance and why this design solves perspective domain shift (ERQ 2).
- [ ] **Figure 3.12 (`path_predictor_loss.png` - §3.7.4):** LSTM Path Predictor Training Loss Curve.
  - [ ] Check axis labels (Epochs 0–150 vs MSE Loss), grid alignment, and descent from $0.082$ to $<0.0015$.
  - [ ] Review text discussing convergence rate, Adam optimization hyperparameters, and absence of overfitting.
- [ ] **Figure 3.13 (`path_prediction_examples.png` - §3.7.4):** Kinematic Multi-Step Trajectory Prediction Benchmarks.
  - [ ] Verify $2 \times 3$ grid clarity: 10 observed history points (blue) vs 5 true points (green) vs 5 LSTM predictions (red).
  - [ ] Review interpretation of Average Displacement Error (ADE = 25.8 px) and Final Displacement Error (FDE = 32.4 px).
  - [ ] Confirm alignment with Chapter 4 discussion of proactive collision avoidance during continuous motion.
- [ ] **Figure 3.14 (`fig_brain_state_machine.png` - §3.8):** UML Brain Node Finite State Machine & Safety Logic.
  - [ ] Verify 5 states: `IDLE`, `WAITING_CONFIRMATION`, `LOCKED_AND_EXECUTING`, `FOLLOW_MODE`, `EMERGENCY_HALT`.
  - [ ] Check transition rules: 5-frame consensus ($3/5$ agreement), 3.0s command lock, visual servoing steering ($v_\omega = -1.5 e_x$).
  - [ ] Review text detailing compliance with ISO 15066 collaborative robot safety standards.
- [ ] **Figure 3.15(a) (`room_map_20260810_0452.png` - §3.9):** Initial Distorted SLAM Mapping Run.
  - [ ] Audit subfigure visual quality showing "hourglass" rotational drift defect and overlapping wall ghosting.
  - [ ] Review in-text diagnostic explanation: Extended Kalman Filter disabled yaw fusion and transform race conditions.
- [ ] **Figure 3.15(b) (`room_map_clean.png` - §3.9):** Final Calibrated Metric SLAM Map.
  - [ ] Check subfigure rendering showing sharp, perpendicular, closed room walls at 5 cm grid resolution.
  - [ ] Review text explaining resolution via wheel odometry yaw fusion and Ceres scan-matching optimization.
- [ ] **Figure 4.1 (`per_class_accuracy_chart.png` - §4.3.2):** Per-Class Classification Accuracy Bar Chart.
  - [ ] Verify bar values across all 6 classes (`RIGHT`: 99.8%, `STOP`: 99.7%, `BACK`: 99.5%, `GO`: 99.4%, `LEFT`: 99.1%, `FOLLOW`: 99.1%).
  - [ ] Review comparative discussion contrasting offline test accuracy (99.38%) with physical bench trials (96.67%, Table 4.1).
  - [ ] Check explanation of `STOP` gesture variation due to oblique palm angle compression ($> 25^\circ$).
- [ ] **Figure 4.2 (`MLP_Confusion_Matrix.png` - §4.4):** Normalized Confusion Matrix of the 6-Class Gesture Classifier.
  - [ ] Audit $6 \times 6$ matrix labels (`BACK`, `FOLLOW`, `GO`, `LEFT`, `RIGHT`, `STOP`) and colorbar intensity scale.
  - [ ] Review text interpreting strong diagonal dominance and near-zero off-diagonal cross-contamination.
  - [ ] Verify alignment with Table 4.5 precision/recall metrics ($F_1$-scores: 0.990 to 0.998).

---

### 2.2 Chapter 1 (Introduction) One-by-One Section Review Checklist
*Paragraph-by-paragraph audit of Chapter 1 to ensure theoretical depth, research question alignment, and strict adherence to formatting rules:*

- [ ] **Section 1.1: Background of the Study**
  - [ ] Verify opening paragraphs contextualize collaborative mobile robotics in industrial, healthcare, and domestic spaces.
  - [ ] Audit transition from traditional physical guards to non-contact vision-based human-robot interaction (HRI).
  - [ ] Review the discussion on edge computing advantages (privacy preservation, low latency, bandwidth independence).
  - [ ] Confirm minimum 3 sentences per paragraph and no first-line indentation throughout.
- [ ] **Section 1.2: Problem Statement**
  - [ ] Verify formulation of the three primary engineering hurdles:
    - [ ] 1. Edge compute bottlenecks (high CPU/memory overhead of deep learning models on embedded processors).
    - [ ] 2. Perspective domain shift (scale and orientation variance degrading raw landmark classifiers across distances).
    - [ ] 3. Multi-person ambiguity (accidental gesture triggering and runaway tracking caused by bystanders).
  - [ ] Ensure clear link between the identified engineering gaps and the proposed multi-tier solution.
- [ ] **Section 1.3: Objectives of the Study**
  - [ ] **General Objective:** Verify clarity of overall goal (low-cost, edge-native intention recognition on mobile robot).
  - [ ] **Specific Objective 1:** Design and integrate low-cost differential drive chassis with Raspberry Pi 5 and micro-ROS.
  - [ ] **Specific Objective 2:** Develop spatial-gated edge vision pipeline combining YOLOv8n and MediaPipe hand tracking.
  - [ ] **Specific Objective 3:** Engineer 19-D invariant geometric feature extractor and train lightweight MLP classifier.
  - [ ] **Specific Objective 4:** Construct supervisory finite state machine (`brain_node`) with priority safety preemption.
  - [ ] **Specific Objective 5:** Empirically benchmark throughput, latency budgets, mapping, and physical command execution.
- [ ] **Section 1.4: Engineering Research Questions (ERQs)**
  - [ ] **ERQ 1 (Edge Feasibility & Latency Budget):** Confirm hypothesis on $<150$ ms end-to-end latency without GPU/cloud.
  - [ ] **ERQ 2 (Feature Invariance & Generalization):** Confirm hypothesis on eliminating scale variance across distance.
  - [ ] **ERQ 3 (Multi-Person Workspace Disambiguation):** Confirm hypothesis on spatial gating and majority-vote buffering.
  - [ ] **ERQ 4 (Intention-to-Action Middleware Coupling & Safety):** Confirm hypothesis on ISO 15066 collaborative safety.
  - [ ] Verify that every ERQ is cross-referenced to its empirical validation sections in Chapters 3 and 4.
- [ ] **Section 1.5: Scope of the Study**
  - [ ] Review indoor laboratory environment constraints (ambient lighting, structured and semi-structured obstacles).
  - [ ] Audit operational boundaries (interaction distance: 0.8 m to 3.0 m; camera FOV: 640x480 @ 20 FPS).
  - [ ] Confirm explicit declaration of hardware boundaries (Raspberry Pi 5 edge compute, no offboard GPU server).
- [ ] **Section 1.6: Significance of the Study**
  - [ ] Review academic contributions to edge-native human intention recognition and robotics literature.
  - [ ] Review industrial and societal impact (affordable collaborative robotics for SMEs, logistics, and assistive living).
  - [ ] Confirm emphasis on safety standard compliance (ISO 15066 / ISO 12100).
- [ ] **Section 1.7: Organization of the Study**
  - [ ] Audit structural outline summarizing Chapters 2 through 5.
  - [ ] Ensure seamless narrative bridge leading into the Chapter 2 Literature Review.

---

### 2.3 Chapter 2 (Literature Review) One-by-One Section Review Checklist
*Exhaustive review of theoretical grounding, related works, synthesis, and comparative analysis in Chapter 2:*

- [ ] **Section 2.0: Overview & Conceptual Framework**
  - [ ] Review framing of human-robot collaborative interaction as a coupled perceptual-cognitive-actuation problem.
  - [ ] Verify discussion of sensory modalities (vision, LiDAR, depth, wearable sensors).
- [ ] **Section 2.1: Theoretical Review**
  - [ ] **HRI Cognitive Models:** Audit explanation of shared mental models, anticipatory action, and intent recognition.
  - [ ] **Kinematic Motion Estimation:** Verify mathematical formulation of velocity vectors and bounding box dynamics.
  - [ ] **Multimodal Sensor Fusion:** Review discussion of complementary optical (camera) and range (LiDAR) data streams.
  - [ ] **Safety Norms & Collaborative Standards:** Verify theoretical treatment of ISO 15066:2016 speed and separation monitoring.
- [ ] **Section 2.2: Review of Related Works (Three Core Works)**
  - [ ] **Review 1 (Tsitos et al. - Upper-Limb Kinematics):**
    - [ ] Audit analysis of kinematic prediction methodology and laboratory findings.
    - [ ] Verify critique of identified limitations: heavy workstation reliance, absence of mobile base integration.
  - [ ] **Review 2 (Mahmud et al. - 3D Skeletal Tracking & Adaptive Gesture):**
    - [ ] Audit review of RGB-D camera requirements and deep neural network classification.
    - [ ] Verify critique of identified limitations: high compute overhead, lack of edge optimization, scale sensitivity.
  - [ ] **Review 3 (Li & Zhang et al. - Intention-Aware Navigation & Costmaps):**
    - [ ] Audit analysis of dynamic costmap inflation and pedestrian path forecasting.
    - [ ] Verify critique of identified limitations: simulated validation only, absence of physical gesture interlocks.
- [ ] **Section 2.3: Synthesis of Reviewed Literature & Gap Analysis**
  - [ ] Audit structured synthesis articulating the critical research gaps:
    - [ ] Gap 1: Compute disconnect (heavy deep learning models requiring discrete desktop GPUs).
    - [ ] Gap 2: Spatial ambiguity (inability of existing systems to handle multiple humans in shared workspaces).
    - [ ] Gap 3: Open-loop mobile coupling (gestures disconnected from reactive physical obstacle avoidance).
  - [ ] Confirm how the proposed thesis methodology directly bridges each identified gap.
- [ ] **Section 2.4: Comparative Summary Table (Table 2.1)**
  - [ ] Audit Table 2.1 rows across all reviewed works (Tsitos et al., Mahmud et al., Li & Zhang, Yu et al., Laplaza et al., Liang & Zheng, Muhtadin et al., This Work).
  - [ ] Check comparison dimensions: Sensing Modality, Classification Engine, Edge Feasibility, Safety Interlock, Physical Mobile Grounding.
  - [ ] Review dedicated subsection comparing camera-based non-contact tracking with wearable/sEMG sensors (Zafar et al.).
- [ ] **Citation & Bibliography Audit**
  - [ ] Verify 100% of in-text `\cite{...}` keys in Chapter 1 and Chapter 2 exist in `write_up/references.bib`.
  - [ ] Confirm IEEE citation format compliance and author name/year accuracy.

---

## 3. Preliminary Pages & Front Matter (To Be Finalized After Chapters)
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

## 5. Current Engineering Audit & Pre-Bench Status (Robot Charging Intermission)
*Verified technical status and completed preparatory work while physical robot is on balance charger:*
- [x] **Verified Ground-Truth Path Prediction Status on Physical Bot:** Confirmed `path_predictor.onnx` is present on the robot and successfully loaded into memory by ONNXRuntime in `person_detection_node.py` (`Path predictor ONNX loaded (threads=2)`). Acknowledged that runtime loop computes 1st-order linear velocity extrapolation (`predicted_x = cx + vx * 0.5`).
- [x] **Restored True 19-Feature Invariant MLP Gesture Engine:** Synchronized the balanced 6,000-sample Campaign 2 dataset (`gesture_dataset.csv`, 1,000 samples per class) and the trained 19-feature MLP weights (`gesture_model_features.pkl`, `scaler_features.pkl`, `label_encoder_features.pkl`, `gesture_model.onnx`, `path_predictor.onnx`) into `ml_models/`.
- [x] **Upgraded `gesture_node.py` Architecture:** Made the 19-feature MLP the primary classifier (Tier 1) via `hand_features.py` (99.50% holdout accuracy across all 6 classes), with the anatomical geometric engine acting as secondary fallback (Tier 2).
- [x] **Resolved Active Vision Gimbal Bugs:** Fixed FSM target loss ($z \le 0$ drops `latest_target` to trigger `MEMORY_HOLD`) and decoupled face tracking timestamp (`last_face_time`) from target timestamp, eliminating the 2 Hz artificial throttling bug.
- [x] **Enhanced Bench Monitor HUD Legend:** Updated `scripts/bench_autonomy_monitor.py` to explicitly display all 6 gestures (`STOP`, `GO`, `FOLLOW`, `LEFT`, `RIGHT`, `BACK`) and their corresponding robot reactions.
- [x] **Master Verification Suite (100% Green PASS):** Executed `scripts/run_all_local_verifications.py`, passing all 5 local unit & integration test suites in 18.10s (`test_perception_throttling`, `test_active_vision_logic`, `test_face_recognition`, `test_brain_logic`, `test_gesture_mlp`).
- [x] **Packaged One-Click Robot Sync Script:** Created and made executable `scripts/sync_to_bot.sh` for seamless container deployment once the robot completes its charging cycle.

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
