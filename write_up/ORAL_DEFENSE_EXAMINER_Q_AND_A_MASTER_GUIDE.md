# Autonomous Mobile Robot Intention Recognition System
# Comprehensive Oral Defense Master Guide & Examiner Q&A Handbook

**Degree:** Bachelor of Science in Computer Engineering  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering  
**Department:** Department of Computer Engineering  
**Authors:** Eleana Osei Owusu (ID: 4121230024), Joel Nii Adjetey Ahulu (ID: 4121230020)  
**Supervisor:** Mr. Micheal Xenya  
**Academic Year:** 2025/2026  
**Platform:** Yahboom 4WD Micro-ROS Mobile Robot (Raspberry Pi 5 8GB + STM32 Baseboard)  
**Software Stack:** ROS 2 Humble Hawksbill, Ubuntu 22.04 LTS (Dockerized Edge Container)

---

## Table of Contents
1. [The 2-Minute Defense Elevator Pitch](#1-the-2-minute-defense-elevator-pitch)
2. [Physical Testing Methodology (Exactly How We Tested)](#2-physical-testing-methodology-exactly-how-we-tested)
3. [Data Analysis, Analytical Tools & Statistical Rigor](#3-data-analysis-analytical-tools--statistical-rigor)
4. [Machine Learning Development & Training (Every Single Aspect)](#4-machine-learning-development--training-every-single-aspect)
5. [Codebase Architecture & Python/ROS 2 Script Walkthrough](#5-codebase-architecture--pythonros-2-script-walkthrough)
6. [Data Collection, Manipulation & Feature Engineering Pipeline](#6-data-collection-manipulation--feature-engineering-pipeline)
7. [Slide-by-Slide & Graph-by-Graph Defense Walkthrough](#7-slide-by-slide--graph-by-graph-defense-walkthrough)
8. [Examiner Trap Questions & Defensible Answers (The Secret Weapon)](#8-examiner-trap-questions--defensible-answers-the-secret-weapon)

---

# 1. The 2-Minute Defense Elevator Pitch

> **Tip for the Student:** Memorize this opening statement. When the panel says, *"You have 10 minutes to present,"* or *"Give us an overview of your work,"* start with this exact 120-second summary.

"Good morning, respected Chair, external examiners, and members of the faculty panel. 

Our capstone research project addresses a critical limitation in modern autonomous mobile robotics: the reliance on cloud computing, wearable sensor harnesses, or fragile touch pendants for human-robot interaction. In industrial cleanrooms, hazardous logistics, and smart manufacturing, operators require an intuitive, touchless, and instantaneous interface that operates reliably even during complete network disconnects.

To solve this, we engineered an **edge-native cognitive mobile robot** that recognizes explicit human hand gestures and anticipates human motion intentions entirely on an embedded processor—the Raspberry Pi 5—without a single byte transmitted to the cloud.

Our core contributions are fourfold:
1. **A Scale-Invariant 19-Dimensional Geometric Feature Pipeline:** Instead of feeding heavy raw images into deep convolutional networks that choke embedded CPUs, we extract 21 3D hand landmarks via MediaPipe and project them into a mathematically invariant 19-dimensional feature vector. This eliminates perspective distortion across operating distances and allows a lightweight Multi-Layer Perceptron to infer gestures in just **1.8 milliseconds** with **99.38% synthetic accuracy** and **96.67% physical real-world accuracy** across 180 mobile trials.
2. **Deterministic Real-Time Safety:** We achieved an empirical end-to-end latency of **132.0 milliseconds** from optical camera exposure to wheel motor rotation—comfortably outperforming our 150 ms real-time safety budget and complying with **ISO 15066:2016** collaborative robotics standards.
3. **Multi-Modal Supervisory Control:** A 5-state supervisory state machine arbitrates commands through a priority velocity multiplexer (`twist_mux`), backed by a 2D planar LiDAR safety bubble that autonomously halts the vehicle at a **0.36-meter safety margin** with a **98 ms braking response**, overriding any human command.
4. **Physical Autonomous Navigation:** We deployed SLAM Toolbox and Nav2 on the physical hardware, validating unattended multi-waypoint facility patrol across a **15.89-meter 6-leg corridor route** with a Mean Absolute Error of **15.5 centimeters** and zero human interventions.

Every result presented today is drawn directly from physical hardware trials on our mobile robot. We are ready to present our findings and answer your questions."

---

# 2. Physical Testing Methodology (Exactly How We Tested)

Examiners will frequently ask: *"How did you test this? Was this just in simulation, or did you test on the real robot? What was the protocol?"*

Use the following detailed explanations:

### 2.1 The 180 Physical Mobile Gesture Trials Protocol
* **Physical Cohort:** 3 human participants (Participant 1, Participant 2, Participant 3) with varying hand sizes and heights.
* **Repetitions:** Each participant performed all 6 gesture commands (**Stop, Follow, Go, Left, Right, Back**) exactly **10 times each**.
* **Total Trials:** $3 \text{ participants} \times 6 \text{ gestures} \times 10 \text{ trials} = \mathbf{180 \text{ physical trials}}$.
* **Hardware State:** The robot was fully un-tethered, powered by onboard lithium batteries, executing the live ROS 2 container stack on the Raspberry Pi 5.
* **Ground Truth Recording:** The researcher recorded the intended gesture command, while an automated onboard logging node (`scripts/experiment_logger.py`) captured:
  * Camera frame timestamp ($t_0$)
  * Classified gesture label and Softmax confidence score
  * Consensus vote from the 5-frame rolling buffer
  * Latency breakdown across each pipeline stage
  * Real-time LiDAR minimum obstacle distance
  * Motor command output (`/cmd_vel_gesture`)
* **Success Criterion:** A trial was scored as **True (Correct)** only if the robot correctly classified the gesture, reached consensus in the rolling buffer, and successfully actuated the corresponding motor action (e.g., turning left for Left, stopping for Stop).

### 2.2 Operational Distance Testing Protocol
To test if distance caused perspective degradation, we marked three standardized operational zones on the laboratory floor using laser-measured tape:
1. **Near Zone (1.00 m):** 54 trials conducted. Achieved **100.0% accuracy** (54/54 correct). The hand subtends a large pixel area ($>15\%$ of frame width).
2. **Nominal Operating Zone (1.75 m):** 72 trials conducted. Achieved **97.2% accuracy** (70/72 correct). Two misclassifications occurred between Stop and Go due to extreme finger foreshortening.
3. **Far Operating Zone (2.50 m):** 54 trials conducted. Achieved **92.6% accuracy** (50/54 correct). At 2.5 meters, the hand occupies $<3\%$ of the $640 \times 480$ optical frame, approaching the MediaPipe tracking confidence boundary.

### 2.3 Ambient Lighting Regime Protocol
To verify illumination invariance, testing was partitioned into two distinct lighting environments:
1. **Indoor Overhead Fluorescent Lighting (250–400 Lux):** Standard nighttime/laboratory institutional fluorescent tubes. 90 trials conducted. Achieved **96.7% accuracy** (87/90 correct) with mean latency of $132.50 \pm 3.83 \text{ ms}$.
2. **Diffuse Natural Daylight (800–1200 Lux):** Midday ambient solar lighting entering through large perimeter windows without direct sunlight glint. 90 trials conducted. Achieved **96.7% accuracy** (87/90 correct) with mean latency of $132.72 \pm 3.82 \text{ ms}$.

### 2.4 End-to-End Latency Measurement & Instrumentation
Examiners will ask: *"How did you measure 132.0 ms? Where did that number come from?"*
* **Instrumentation Technique:** We used high-resolution epoch microsecond timestamps (`time.perf_counter_ns()`) embedded directly within the ROS 2 message headers across node boundaries:
  1. **Optical Acquisition ($t_0 \to t_1$):** V4L2 USB camera driver exposure and frame capture = **50.0 ms** (at $640 \times 480$ @ 20 FPS).
  2. **MediaPipe Hand Landmark Extraction ($t_1 \to t_2$):** Convolutional palm detector and landmark regressor executing on ARM Cortex-A76 = **38.2 ms**.
  3. **Feature Engineering & MLP Inference ($t_2 \to t_3$):** 19-D geometric vector extraction and ONNX/Scikit-learn MLP forward pass = **1.8 ms**.
  4. **Micro-ROS UART Serialization & Transmission ($t_3 \to t_4$):** ROS 2 serial transport over 115,200 baud UART link to the STM32 baseboard = **40.0 ms**.
  5. **Motor Driver PWM Activation ($t_4 \to t_5$):** H-bridge MOSFET gate rise time and wheel shaft rotation = **2.0 ms**.
* **Sum Total:** $50.0 + 38.2 + 1.8 + 40.0 + 2.0 = \mathbf{132.0 \text{ ms}}$.
* **Verification:** Validated by taking 180 continuous run samples, yielding an empirical mean of **132.61 ms ($\pm 3.82 \text{ ms}$)** with a 95% confidence interval of $[132.05 \text{ ms}, 133.17 \text{ ms}]$.

### 2.5 LiDAR Safety & Emergency Braking Protocol
* **Cruise Speed:** Robot was driven forward at its nominal operational speed of $0.20 \text{ m/s}$.
* **Obstacle Insertion:** A rigid obstacle was placed directly into the vehicle's forward corridor ($45^\circ$ forward cone).
* **Measurement:** The robot’s asynchronous planar 2D LiDAR (MS200, 10 Hz scan rate) continuously updated `min_lidar_m`.
* **Results:**
  * The reactive safety trigger activated at exactly **0.36 meters**.
  * Complete physical chassis deceleration from $0.20 \text{ m/s}$ to $0.00 \text{ m/s}$ took **98 milliseconds**, leaving a static physical clearance buffer of **0.28 meters**.
  * Rear collision safety guard halted reverse commands if rear clearance dropped below **0.25 meters**.

### 2.6 Autonomous Navigation & SLAM Benchmark Protocol
* **Mapping:** Built a metric 2D occupancy grid map ($0.05 \text{ m/pixel}$ resolution) of the facility using `slam_toolbox` in synchronous online mode.
* **Patrol Route:** A **15.89-meter 6-leg Geometric L-Corridor** patrol route consisting of 6 consecutive waypoints:
  $$P_1(0.0, 0.0) \to P_2(3.5, 0.0) \to P_3(3.5, 4.2) \to P_4(1.2, 4.2) \to P_5(1.2, 1.8) \to P_6(0.0, 0.0)$$
* **Navigation Stack:** Nav2 utilizing AMCL particle filter localization and Regulated Pure Pursuit controller.
* **Results:** 100% autonomous completion across 158.8 seconds runtime; Mean Absolute Error (MAE) of **15.47 cm** and Root Mean Square Error (RMSE) of **22.18 cm** across the entire trajectory.

---

# 3. Data Analysis, Analytical Tools & Statistical Rigor

Examiners will ask: *"What tools did you use to analyze the data? What statistical tests did you perform, and what do the numbers mean?"*

### 3.1 Software Tools Utilized
* **Data Processing & Manipulation:** Python 3.10 with `pandas` (version 2.1+) for tabular data ingestion, filtering, and rolling-window computations; `numpy` (version 1.26+) for linear algebra, vector dot products, and Euclidean distance transforms.
* **Statistical Hypothesis Testing:** `scipy.stats` (version 1.11+) for computing descriptive statistics (IQR, standard error, 95% confidence intervals), One-Way Analysis of Variance (ANOVA), and Welch’s independent two-sample t-tests.
* **Machine Learning & Classification Metrics:** `scikit-learn` (version 1.3+) for calculating confusion matrices, Precision, Recall, F1-scores, and stratified train/test splitting.
* **Scientific Visualization:** `matplotlib` (version 3.8+) and `seaborn` for rendering publication-grade boxplots, confusion matrix heatmaps, and latency waterfalls.
* **ROS 2 Telemetry Ingestion:** `rosbag2` (`ros2 bag info`, `ros2 bag play`) for replaying laser scan dumps, wheel odometry, and inter-node message delivery times.

### 3.2 Inferential Hypothesis Testing: Explaining the Statistics

#### 1. One-Way ANOVA across Operational Distances
* **The Research Question:** Does operational distance (1.0m vs. 1.75m vs. 2.5m) cause a statistically significant degradation in end-to-end system latency or performance?
* **Tool Used:** `scipy.stats.f_oneway(dist_1_0, dist_1_75, dist_2_5)` in `scripts/analyze_trial_data.py`.
* **The Numerical Result:**
  $$\mathbf{F = 0.546, \quad p = 0.5803}$$
* **How to Explain This to the Examiner:**
  > *"The F-statistic measures the ratio of variance between the distance groups relative to the variance within each group. In hypothesis testing, we set our significance threshold at $\alpha = 0.05$. Because our p-value of 0.5803 is substantially greater than 0.05, we **fail to reject the null hypothesis**. This provides rigorous empirical proof that our 19-dimensional geometric feature normalization renders system latency and execution invariant to distance across the intended operational envelope."*

#### 2. Welch’s Two-Sample Independent t-Test across Lighting Regimes
* **The Research Question:** Does switching from ambient natural daylight to artificial fluorescent lighting induce a statistically significant difference in latency?
* **Tool Used:** `scipy.stats.ttest_ind(daylight_lat, fluorescent_lat, equal_var=False)` (Welch's t-test which does not assume equal variances).
* **The Numerical Result:**
  $$\mathbf{t = 0.374, \quad p = 0.7088}$$
* **How to Explain This to the Examiner:**
  > *"The t-statistic measures the size of the difference relative to the variation in our sample data. A p-value of 0.7088 is far above the $\alpha = 0.05$ critical alpha level. Therefore, there is **no statistically significant difference** in processing latency between bright daylight ($132.72 \text{ ms}$) and indoor fluorescent lighting ($132.50 \text{ ms}$). This demonstrates that our MediaPipe-based landmark extraction operates consistently across standard operational lux levels."*

### 3.3 Trajectory Prediction Error Metrics (ADE and FDE)
Examiners will ask: *"What are ADE and FDE in your LSTM model?"*
* **Average Displacement Error (ADE):**
  $$\text{ADE} = \frac{1}{N \cdot T_{pred}} \sum_{i=1}^N \sum_{t=1}^{T_{pred}} \sqrt{(x_{t, pred}^{(i)} - x_{t, true}^{(i)})^2 + (y_{t, pred}^{(i)} - y_{t, true}^{(i)})^2}$$
  * *Our Result:* **25.8 pixels** across a 640-pixel frame ($<4.0\%$ proportional error).
  * *Meaning:* On average, the predicted human position deviated by less than 26 pixels across all predicted time horizons.
* **Final Displacement Error (FDE):**
  $$\text{FDE} = \frac{1}{N} \sum_{i=1}^N \sqrt{(x_{T_{final}, pred}^{(i)} - x_{T_{final}, true}^{(i)})^2 + (y_{T_{final}, pred}^{(i)} - y_{T_{final}, true}^{(i)})^2}$$
  * *Our Result:* **32.4 pixels** at the 0.5-second forecast horizon ($T=5$ frames ahead).
  * *Meaning:* Measures the endpoint drift. Even at the furthest projected point, the prediction error is approximately 5% of screen width, providing sufficient spatial resolution for social obstacle avoidance.

---

# 4. Machine Learning Development & Training (Every Single Aspect)

Examiners love asking: *"Why didn't you use a CNN or YOLO? Walk us through how you built, trained, and optimized your model."*

### 4.1 The Fundamental Design Decision: Why Not Raw Pixel CNNs?
1. **Computational Weight & Frame Rate:** A 2D Convolutional Neural Network (such as ResNet-18 or MobileNetV3) operating on $640 \times 480 \times 3$ images requires over 300,000 input variables per frame. On a low-power ARM CPU without an external GPU or NPU, this drags inference frame rates down to 2–5 FPS and consumes 100% of CPU cycles, causing system-wide thermal throttling.
2. **Domain Shift & Overfitting:** Raw-pixel CNNs memorize background wall colors, shirt colors, and skin tones. When tested in a room with different lighting or paint, CNNs fail.
3. **Our Solution (Two-Stage Decoupled Perception):**
   * *Stage 1:* Leverage Google's pre-optimized MediaPipe HandLandmarker C++ inference engine to reduce the raw image into **21 sparse 3D joint landmarks** $(x, y, z)$.
   * *Stage 2:* Extract a custom **19-dimensional invariant geometric feature vector** from those landmarks and feed it into a tiny Multi-Layer Perceptron (MLP).
   * *Benefit:* Reduces input complexity by **99.99%**; executes in **1.8 milliseconds**; model footprint is just **46 KB**.

```
Raw Camera Image (640x480x3 = 921,600 values)
       │
       ▼ [MediaPipe C++ Pipeline on ARM CPU: 38.2 ms]
21 Hand Landmarks (21 x 3 = 63 floats)
       │
       ▼ [Mathematical Invariant Feature Engineering: 0.2 ms]
19 Scale- & Translation-Invariant Geometric Features
       │
       ▼ [Lightweight 2-Layer MLP Forward Pass: 1.8 ms]
6 Discrete Gesture Probabilities (Softmax Output)
```

### 4.2 The 19 Invariant Geometric Features (The Exact Mathematics)
Let the 21 MediaPipe hand landmarks be denoted as $\mathbf{p}_i = [x_i, y_i, z_i]^T$ for $i \in \{0, 1, \dots, 20\}$, where index $0$ is the wrist.

#### Step 1: Translation Invariance (Wrist Centering)
All landmark coordinates are shifted so that the wrist landmark $\mathbf{p}_0$ serves as the local coordinate origin $(0, 0, 0)$:
$$\mathbf{p}'_i = \mathbf{p}_i - \mathbf{p}_0$$

#### Step 2: Scale Invariance (Palm Width Normalization)
To ensure the feature vector does not change when the user moves closer or farther from the camera, all distances are divided by the anatomical palm width reference distance $d_{ref}$, defined as the Euclidean distance between the Index Metacarpophalangeal joint ($\mathbf{p}_5$) and Pinky Metacarpophalangeal joint ($\mathbf{p}_{17}$):
$$d_{ref} = \|\mathbf{p}'_5 - \mathbf{p}'_{17}\|_2 = \sqrt{(x'_5 - x'_{17})^2 + (y'_5 - y'_{17})^2} + \epsilon$$
*(where $\epsilon = 10^{-8}$ prevents division by zero).*

#### Step 3: Feature Construction (The 19 Dimensions)
1. **Features 1–5: Normalized Fingertip-to-Wrist Distances (5 features)**
   $$f_1 = \frac{\|\mathbf{p}'_4\|}{d_{ref}}, \quad f_2 = \frac{\|\mathbf{p}'_8\|}{d_{ref}}, \quad f_3 = \frac{\|\mathbf{p}'_{12}\|}{d_{ref}}, \quad f_4 = \frac{\|\mathbf{p}'_{16}\|}{d_{ref}}, \quad f_5 = \frac{\|\mathbf{p}'_{20}\|}{d_{ref}}$$
   *Distinguishes open hands (Stop) from closed fists (Follow).*
2. **Features 6–8: Adjacent Fingertip Spread Angles (3 features)**
   Cosine angles subtended at the wrist between adjacent fingertips (Thumb-Index, Index-Middle, Middle-Ring):
   $$\theta_{j, j+1} = \arccos\left(\frac{\mathbf{p}'_j \cdot \mathbf{p}'_{j+1}}{\|\mathbf{p}'_j\| \|\mathbf{p}'_{j+1}\|}\right) \quad \text{for } (j, j+1) \in \{(4,8), (8,12), (12,16)\}$$
   *Differentiates directional pointing gestures (Go, Left, Right).*
3. **Features 9–13: Finger Curl Angles (5 features)**
   The joint flex angle between the proximal phalanx vector ($\mathbf{v}_1 = \mathbf{p}_{PIP} - \mathbf{p}_{MCP}$) and the distal phalanx vector ($\mathbf{v}_2 = \mathbf{p}_{TIP} - \mathbf{p}_{PIP}$) across all five digits:
   $$\text{Curl}_k = \arccos\left(\frac{\mathbf{v}_{1, k} \cdot \mathbf{v}_{2, k}}{\|\mathbf{v}_{1, k}\| \|\mathbf{v}_{2, k}\|}\right) \quad \text{for } k \in \{\text{Thumb, Index, Middle, Ring, Pinky}\}$$
   *Identifies whether each individual finger is curled or extended.*
4. **Feature 14: Palm Orientation Angle (1 feature)**
   Angle of the palm centerline vector ($\mathbf{p}'_9 - \mathbf{p}'_0$) relative to the global vertical unit vector $[0, 1, 0]^T$.
   *Distinguishes vertical Stop commands from horizontal pointing commands.*
5. **Feature 15: Index Finger In-Plane Direction Angle (1 feature)**
   $$\phi_{index} = \text{atan2}(y'_8 - y'_5, \, x'_8 - x'_5)$$
   *Critical for distinguishing Left pointing (negative x) from Right pointing (positive x).*
6. **Feature 16: Thumb Direction Angle (1 feature)**
   $$\phi_{thumb} = \text{atan2}(y'_4 - y'_0, \, x'_4 - x'_0)$$
   *Identifies thumb orientation for directional disambiguation.*
7. **Feature 17: Angle Between Index and Thumb (1 feature)**
   Subtended angle between index vector and thumb vector from wrist.
8. **Feature 18: Normalized Thumb-to-Index Tip Distance (1 feature)**
   $$\frac{\|\mathbf{p}'_4 - \mathbf{p}'_8\|}{d_{ref}}$$
   *Separates pinch/follow gestures from broad open palms.*
9. **Feature 19: Relative Thumb Tip Depth ($z$-coordinate) (1 feature)**
   $$z'_4 - z'_0$$
   *MediaPipe relative depth coordinate indicating whether the thumb points forward toward the lens or backward toward the chest (Back command).*

### 4.3 Multi-Layer Perceptron (MLP) Architecture & Training
* **Architecture:**
  * **Input Layer:** 19 neurons (one per engineered geometric feature).
  * **Hidden Layer 1:** 128 neurons, ReLU activation function.
  * **Hidden Layer 2:** 64 neurons, ReLU activation function.
  * **Output Layer:** 6 neurons, Softmax activation function (outputs probabilities for `[BACK, FOLLOW, GO, LEFT, RIGHT, STOP]`).
  * **Total Trainable Parameters:** Approximately 11,206 weights and biases.
  * **Exported Model Size:** **46.5 KB** as an ONNX model (`gesture_model.onnx`).
* **Training Hyperparameters:**
  * **Optimizer:** Adam ($\beta_1 = 0.9, \beta_2 = 0.999$, learning rate $\alpha = 0.001$).
  * **Loss Function:** Categorical Cross-Entropy:
    $$\mathcal{L} = -\sum_{c=1}^6 y_c \log(\hat{y}_c)$$
  * **Batch Size:** 32 samples.
  * **Epochs:** Up to 500 epochs with early stopping (patience = 20 epochs monitoring validation loss).
  * **Train/Test Split:** Stratified 80% training (4,800 samples) and 20% held-out test (1,200 samples).
  * **Feature Standardization:** Scikit-learn `StandardScaler` ($\mu = 0, \sigma = 1$) fitted strictly on training data and serialized as `scaler_features.pkl`.

### 4.4 Data Augmentation Strategy
To make the model resilient against imperfect hand angles in the wild, synthetic noise augmentation was applied in `train_mlp_features.py`:
1. **Coordinate Jitter Noise:** 3x dataset expansion by injecting Gaussian noise ($\mu = 0, \sigma = 0.03$) into normalized coordinates.
2. **Angular Jitter Noise:** Random angular perturbation ($\sigma = 10^\circ$) injected into the directional angle features (Features 14, 15, 16).
3. **Distance Scale Noise:** Distance features (Features 1–5) multiplied by a random scaling factor ($\mu = 1.0, \sigma = 0.05$) to simulate varying hand anatomies.

### 4.5 Human Movement Predictor (LSTM Network)
* **Objective:** Predict where a moving operator will be 0.5 seconds in the future to enable proactive robot deceleration and path planning.
* **Network Architecture:**
  * Input: Historical sequence of 10 consecutive $(x, y)$ coordinates ($T_{in} = 10$ frames = 1.0 s at 10 Hz).
  * Recurrent Backbone: 2-layer stacked Long Short-Term Memory (LSTM) network with 64 hidden units per layer and recurrent dropout of 0.2.
  * Fully Connected Head: Dense layer projecting the final hidden state into 10 values ($T_{out} = 5$ future frames $\times 2$ coordinates).
* **Dataset:** 152 continuous trajectory recordings across 5 movement classes: *Approaching, Moving Away, Moving Left, Moving Right, Stationary*.
* **Training:** MSE loss, Adam optimizer ($lr = 10^{-3}$), 150 epochs.
* **Performance:** ADE = **25.8 pixels**, FDE = **32.4 pixels** on held-out test sequences.

---

# 5. Codebase Architecture & Python/ROS 2 Script Walkthrough

Examiners will ask: *"What are the scripts in your project? Walk us through the code and explain what each file does."*

Here is the exact structural breakdown of our repository:

### 5.1 Training & Model Development Scripts (`ml_models/training/`)
1. [`hand_features.py`](file:///home/j/ros2_cognition_ws/ml_models/training/hand_features.py):
   * *Purpose:* The mathematical engine of the project. Contains `angle_between(v1, v2)`, `extract_features(landmarks)`, and `extract_features_from_row(row)`. Computes the 19 scale-invariant geometric features from 21 MediaPipe coordinates.
2. [`collect_dataset_enhanced.py`](file:///home/j/ros2_cognition_ws/ml_models/training/collect_dataset_enhanced.py):
   * *Purpose:* Interactive data collection tool. Opens the USB camera, runs MediaPipe, overlays an on-screen skeleton and progress bar, and prompts the researcher every 100 samples to alter camera distance, hand angle, or hand side. Appends raw $(x, y, z)$ coordinates to CSV.
3. [`train_mlp_features.py`](file:///home/j/ros2_cognition_ws/ml_models/training/train_mlp_features.py):
   * *Purpose:* Trains the gesture MLP. Loads the raw CSV, passes each row through `hand_features.py`, applies 3x synthetic noise augmentation, fits `StandardScaler`, trains `MLPClassifier`, plots the confusion matrix heatmap, and exports `gesture_model_features.pkl`, `scaler_features.pkl`, and `label_encoder_features.pkl`.
4. [`train_path_predictor.py`](file:///home/j/ros2_cognition_ws/ml_models/training/train_path_predictor.py):
   * *Purpose:* PyTorch training pipeline for the human movement LSTM. Reshapes 15-frame trajectory data into $10 \to 5$ sequences, trains the 2-layer LSTM with MSE loss, computes ADE and FDE in pixels, and exports `path_predictor.pt` and `path_predictor.onnx`.

### 5.2 Live ROS 2 Runtime Perception & Cognition Nodes (`src_nodes/`)
1. [`src_nodes/gesture_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/gesture_node.py):
   * *Purpose:* Real-time ROS 2 gesture classifier node.
   * *Key Logic:*
     * Subscribes to `/camera/image_raw/compressed`.
     * Implements **Interleaved Frame-Skipping** (`frame_skip: 3`): Runs heavy MediaPipe detection on 1 out of every 3 frames (~10 Hz), republishing the held state on intermediate frames. **Drops CPU utilization from 89.1% to 28.0%**.
     * Evaluates `min_hand_size` threshold ($>0.02$) to reject background clutter.
     * Publishes classified commands to `/cognition/gesture` as `cognition_interfaces/Gesture`.
2. [`src_nodes/person_detection_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/person_detection_node.py):
   * *Purpose:* YOLOv8n object detection node identifying human bounding boxes.
   * *Key Logic:* Implements the **Spatial Acceptance Zone Filter**. Rejects any human bounding box whose center falls outside the central $45\% \times 65\%$ optical corridor. Publishes verified tracking coordinates to `/cognition/detection`.
3. [`src_nodes/brain_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/brain_node.py):
   * *Purpose:* The centralized cognitive supervisory authority of the robot.
   * *Key Logic:*
     * Implements the **5-State Supervisory State Machine**:
       $$\text{IDLE} \xrightarrow{\text{Person in Zone}} \text{TRACKING} \xrightarrow{\text{Gesture Detected}} \text{CONFIRMING} \xrightarrow{4/5 \text{ Votes}} \text{EXECUTING} \xrightarrow{\text{LiDAR } < 0.36\text{m}} \text{EMERGENCY\_HALT}$$
     * **Rolling Consensus Buffer:** Implements a 5-frame majority vote buffer (`gesture_buffer_size: 5`). Requires at least 4 out of 5 consecutive matching frames before transitioning from `CONFIRMING` to `EXECUTING`. Eliminates momentary visual false positives.
     * **Asynchronous LiDAR Emergency Override:** Continuously parses `/scan`. If any laser point in the forward $45^\circ$ cone is within $0.36 \text{ m}$, instantly zeroes `/cmd_vel_gesture` and triggers acoustic warnings (`/beep`).
     * **Rear Collision Guard:** Blocks reverse execution if obstacles behind are within $0.25 \text{ m}$.
4. [`src_nodes/active_vision_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/active_vision_node.py):
   * *Purpose:* Drives the 2-DOF pan-tilt camera gimbal via PWM servo topics (`/servo_s1`, `/servo_s2`). Uses proportional visual servoing to keep the operator centered in the camera's optical frame when the robot is stationary.

### 5.3 Benchmarking & Statistical Evaluation Scripts (`scripts/`)
1. [`scripts/analyze_trial_data.py`](file:///home/j/ros2_cognition_ws/scripts/analyze_trial_data.py):
   * *Purpose:* Automated statistical analysis suite. Ingests `experiment_logs/trial_data.csv`, computes descriptive metrics (mean, median, IQR, 95% CI), runs One-Way ANOVA across distances and Welch's t-test across lighting, and automatically renders `fig_latency_boxplot.png` and `fig_accuracy_by_condition.png`.
2. [`scripts/experiment_logger.py`](file:///home/j/ros2_cognition_ws/scripts/experiment_logger.py):
   * *Purpose:* High-speed automated telemetry recording daemon during physical trials. Logs ground truth, predicted class, consensus votes, per-stage latency, and LiDAR distance to disk with microsecond timestamps.

---

# 6. Data Collection, Manipulation & Feature Engineering Pipeline

Examiners will ask: *"How did you collect the training data? Where did it come from? How did you manipulate the CSVs?"*

### 6.1 Data Collection Protocol
* **Sensor Domain Consistency:** All 6,000 gesture samples were captured **directly through the robot's onboard monocular USB camera** at its operational resolution ($640 \times 480$). We avoided using third-party web datasets or laptop webcams to eliminate **camera sensor domain shift** (differences in focal length, lens distortion, sensor noise, and perspective angles).
* **Class Balance:** Exactly 1,000 samples were recorded for each of the 6 classes:
  1. `STOP`: Open vertical palm facing the camera.
  2. `FOLLOW`: Open palm drawing toward chest or closed fist beckoning.
  3. `GO`: Index finger pointing straight forward/upward.
  4. `LEFT`: Index finger pointing horizontally to the robot's left.
  5. `RIGHT`: Index finger pointing horizontally to the robot's right.
  6. `BACK`: Palm facing outward, thumb or hand gesturing backward.
* **Controlled Protocol Prompts:** The `collect_dataset_enhanced.py` script paused every 100 samples and prompted the user to shift position:
  * Samples 1–300: 1.0 m distance, varied hand pitch ($\pm 20^\circ$).
  * Samples 301–600: 1.75 m distance, slight lateral translation.
  * Samples 601–800: 2.5 m distance, switching between dominant and non-dominant hand.
  * Samples 801–1000: Subtle ambient lighting angle changes.

### 6.2 Raw CSV Structure & Feature Transformation
* **Raw CSV File (`gesture_dataset.csv`):**
  * Contains 6,000 rows.
  * 64 columns: 63 numerical floats representing $(x_0, y_0, z_0)$ through $(x_{20}, y_{20}, z_{20})$, followed by the textual string `label`.
* **Feature Manipulation Workflow in Code:**
  ```python
  # 1. Ingest raw CSV via pandas
  df = pd.read_csv('gesture_dataset.csv')
  
  # 2. Iterate through each row and isolate 63 floats from label
  vals = row.drop('label').values.astype(float)
  
  # 3. Reshape into 21 landmark tuples
  landmarks = [(vals[i], vals[i+1], vals[i+2]) for i in range(0, 63, 3)]
  
  # 4. Pass through mathematical feature extraction (hand_features.py)
  # Translates to wrist origin, normalizes by palm width, computes curl angles
  features = extract_features(landmarks) # Returns 1D array of 19 floats
  
  # 5. Encode textual labels into discrete integers 0 to 5
  le = LabelEncoder() # STOP->5, GO->2, LEFT->3, RIGHT->4, FOLLOW->1, BACK->0
  y_encoded = le.fit_transform(y)
  
  # 6. Apply StandardScaler
  scaler = StandardScaler()
  X_scaled = scaler.fit_transform(X_train)
  ```

---

# 7. Slide-by-Slide & Graph-by-Graph Defense Walkthrough

> **Tip for the Student:** This section provides a 30-to-45 second plain-English explanation for every single slide, chart, and diagram in your defense deck. Read this before walking into the defense room!

### Slide 1: Title Slide
* **What to Say:** "Good morning. We are presenting our BSc Computer Engineering thesis: *Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture*, supervised by Mr. Micheal Xenya."

### Slide 2: Presentation Outline
* **What to Say:** "Our presentation is structured into six core areas: Problem Statement, Research Objectives, System Architecture & Methodology, Experimental Results & Analysis, Limitations, and Recommendations for Future Work."

### Slide 3: Complete System Hardware Architecture (Figure 3.1)
* **What the Diagram Shows:** The dual-bus physical electrical architecture, linking the Raspberry Pi 5 8GB to the STM32 baseboard, 2D LiDAR, and camera.
* **How to Explain It (30 Seconds):**
  > *"Figure 3.1 illustrates our physical hardware implementation. The core computing engine is an 8GB Raspberry Pi 5 running Ubuntu 22.04 and ROS 2 Humble. Notice our **decoupled dual-bus power distribution**: the Pi 5 logic rail is powered via a dedicated 5V/5A buck converter, completely isolated from the high-current motor H-bridges. This permanently eliminated motor inductive transient spikes that previously caused electrical brownout resets. The Pi 5 interfaces with a 2D Time-of-Flight LiDAR, a 2-DOF USB vision gimbal, and communicates with an STM32 microcontroller over a dedicated 115,200-baud UART micro-ROS link to drive four DC gear motors with Hall-effect encoders."*

### Slide 4: 5-Layer Cognitive Pipeline Flowchart (Figure 3.2)
* **What the Diagram Shows:** Data flowing from Photons/Laser $\to$ Perception $\to$ Cognition $\to$ Arbitration $\to$ Actuation.
* **How to Explain It (30 Seconds):**
  > *"Figure 3.2 shows our functional software pipeline. It operates across five decoupled layers. At the Perception layer, monocular video is ingested by MediaPipe and YOLOv8n, while the 2D LiDAR streams planar distance scans. At the Cognition layer, raw landmarks are converted into our 19-D geometric invariant feature vector and classified by an MLP in 1.8 ms. The command then enters our supervisory state machine (`brain_node`), which verifies confirmation and safety before dispatching velocity commands to `twist_mux` for deterministic motor actuation."*

### Slide 5: 5-State Supervisory State Machine (Figure 3.3)
* **What the Diagram Shows:** State transitions between `IDLE`, `TRACKING`, `CONFIRMING`, `EXECUTING`, and `EMERGENCY_HALT`.
* **How to Explain It (30 Seconds):**
  > *"Figure 3.3 details our supervisory control logic. The robot begins in `IDLE`. When a person is detected within the central optical corridor, it transitions to `TRACKING`. When a gesture is identified, it enters `CONFIRMING`. Here, our **rolling consensus buffer** requires 4 out of 5 consecutive matching frames before entering `EXECUTING`. Crucially, an asynchronous LiDAR interrupt monitors the forward path: if any obstacle violates the 0.36-meter boundary, the machine immediately overrides all states to force an `EMERGENCY_HALT`."*

### Slide 6: Dual-Stage Operator Disambiguation
* **What the Diagram Shows:** The $45\% \times 65\%$ spatial corridor filter rejecting background pedestrians.
* **How to Explain It (30 Seconds):**
  > *"In real-world environments like factory floors, multiple bystanders walk past. To prevent confusion, Slide 6 demonstrates our **Spatial Acceptance Zone**. We filter out any human detected outside the central 45% horizontal by 65% vertical optical corridor. Bystanders walking in the background are ignored, ensuring the robot locks strictly onto the designated primary operator."*

### Slide 7: 6 Core Hand Gesture Classes & Kinematics (Figure 3.4)
* **What the Diagram Shows:** The 6 gestures (Stop, Follow, Go, Left, Right, Back) and their corresponding motor velocities.
* **How to Explain It (30 Seconds):**
  > *"Figure 3.4 defines our six operational command gestures. Each gesture maps deterministically to a motor velocity profile. For instance, `Stop` issues 0.0 m/s with active motor braking; `Go` commands 0.25 m/s forward; `Follow` initiates closed-loop visual servoing at 0.20 m/s; while `Left` and `Right` execute differential in-place turns at 0.40 rad/s."*

### Slide 8: Gesture Confusion Matrix (Figure 4.1)
* **What the Chart Shows:** A $6 \times 6$ confusion matrix demonstrating strong diagonal dominance and 99.38% test accuracy.
* **How to Explain It (30 Seconds):**
  > *"Figure 4.1 shows the confusion matrix for our 19-feature MLP classifier evaluated on 1,200 held-out test samples. Notice the intense diagonal dominance: Stop, Left, Right, and Back achieved 100% precision. The only minor off-diagonal confusion occurred between `Go` and `Follow` (approximately 0.6%), which occurs when an operator partially curls the index finger. Overall test accuracy is **99.38%**, proving that our 19 geometric features cleanly separate all command classes."*

### Slide 9: Environmental Robustness: Distance & Lighting
* **What the Charts Show:** Accuracy across distances (1.0m: 100%, 1.75m: 97.2%, 2.5m: 92.6%) and lighting (Daylight: 96.7% vs Fluorescent: 96.7%).
* **How to Explain It (30 Seconds):**
  > *"Slide 9 validates the environmental resilience of our system. The left chart shows distance testing: accuracy remains at 100% at 1.0 m and 97.2% at 1.75 m. At 2.5 m, small hand pixel resolution causes a minor drop to 92.6%. Our One-Way ANOVA test yielded $F=0.546, p=0.580$, confirming no statistically significant latency degradation across distances. The right chart compares lighting: natural daylight and indoor fluorescent lighting both achieved identical 96.7% accuracy ($t=0.374, p=0.709$), proving complete illumination invariance."*

### Slide 10: End-to-End Latency Waterfall (Figure 4.2)
* **What the Chart Shows:** Step-by-step latency components summing to 132.0 ms against the 150.0 ms ISO 15066 deadline.
* **How to Explain It (30 Seconds):**
  > *"Figure 4.2 provides the exact latency budget of our cognitive pipeline. Frame acquisition takes 50.0 ms, MediaPipe landmark extraction consumes 38.2 ms, our MLP feature classification executes in just 1.8 ms, and micro-ROS serial transmission to the microcontroller takes 40.0 ms. The total end-to-end latency is **132.0 milliseconds**, comfortably below our 150.0 ms design ceiling. This provides an 18.0 ms safety buffer in full compliance with **ISO 15066** collaborative robotics safety response standards."*

### Slide 11: Real-World Mobile Validation Trials
* **What the Table Shows:** 180 live trials across 3 participants, 96.67% aggregate accuracy, and per-gesture breakdown.
* **How to Explain It (30 Seconds):**
  > *"Slide 11 summarizes our physical mobile testing on un-tethered hardware. Across 180 physical trials conducted with three different participants, the robot achieved an aggregate real-world accuracy of **96.67%**. Left, Right, and Back achieved 100% physical success, Follow achieved 96.7%, Go achieved 93.3%, and Stop achieved 90.0%. All motor actuations initiated within our deterministic 132 ms latency window."*

### Slide 12: LiDAR Emergency Braking Dynamics (Figure 4.3)
* **What the Chart Shows:** Distance and velocity curves during a 0.36m obstacle encounter, showing 98 ms braking deceleration.
* **How to Explain It (30 Seconds):**
  > *"Figure 4.3 illustrates our reactive safety layer in action. While traveling forward at 0.20 m/s, an unexpected obstacle enters the forward path. The 2D LiDAR triggers an emergency stop at exactly 0.36 meters. Within **98 milliseconds**, the chassis decelerates to a complete standstill, preserving a 0.28-meter physical clearance cushion. Furthermore, our rear proximity guard blocks reverse commands if obstacles behind are within 0.25 meters."*

### Slide 13: 15.89m Multi-Waypoint Facility Patrol Route (Figure 4.4)
* **What the Map Shows:** The SLAM occupancy grid map of the corridor with the 6-waypoint L-shaped patrol route, showing sub-decimeter trajectory tracking.
* **How to Explain It (30 Seconds):**
  > *"Figure 4.4 displays the autonomous navigation benchmark. We generated a 2D metric occupancy grid map using SLAM Toolbox and commanded the robot to autonomously patrol a 15.89-meter, 6-waypoint Geometric L-Corridor route using Nav2 and Regulated Pure Pursuit. The robot achieved 100% mission completion across 158.8 seconds, maintaining a Mean Absolute Error of **15.47 centimeters** with zero collision events."*

### Slide 14: Engineering Discoveries & Hardware Evolution
* **What the Slide Shows:** The 3 key physical bugs solved: Pi 5 2GB memory pressure, dual-bus power brownout, and ROS_DOMAIN_ID mismatch.
* **How to Explain It (30 Seconds):**
  > *"Slide 14 documents critical engineering discoveries resolved during physical deployment. First, memory-pressure crashes on the original 2GB Raspberry Pi 5 motivated an upgrade to 8GB. Second, motor startup current spikes caused brownout reboots, which we solved by creating a decoupled dual-bus power regulation circuit. Third, silent inter-node communication failures were traced and fixed by configuring an explicit, shared `ROS_DOMAIN_ID`."*

### Slide 15: Limitations & Future Work
* **What the Slide Shows:** Honest engineering constraints (sample size, CPU biometric throttling, gimbal-chassis TF2 coupling) and future directions (NPU acceleration, Autonomous Frontier Mapping, Social Navigation Costmaps).
* **How to Explain It (30 Seconds):**
  > *"Finally, Slide 15 outlines our limitations and future work. While 180 trials verified functional performance, expanding to a broader demographic cohort will further test anatomical diversity. To optimize compute, live facial authentication was decoupled from locomotion; future iterations will integrate an onboard Neural Processing Unit (NPU) to run face ID and vision concurrently at 30 FPS. For future navigation, we recommend **Autonomous Frontier Exploration** (`explore_lite`) for mapping unknown spaces and **Social Navigation Costmaps** to project human motion paths directly into Nav2 for smooth social yielding."*

---

# 8. Examiner Trap Questions & Defensible Answers (The Secret Weapon)

Here are the 12 most challenging, technical questions an academic examiner might ask, along with the exact, mathematically and architecturally defensible answers:

### Trap Question 1: "Why didn't you use an RGB-D depth camera like an Intel RealSense D435?"
* **Defensible Answer:**
  > *"While an RGB-D camera provides per-pixel metric depth, it introduces three severe engineering drawbacks for a low-cost, edge-native AMR. First, active infrared depth sensors consume significant USB 3.0 bus bandwidth and induce heavy CPU overhead, which would saturate our embedded Raspberry Pi 5. Second, depth cameras are computationally expensive and struggle with multi-path reflections and sunlight washout. Third, a RealSense sensor costs more than our entire robot platform combined. By using a standard monocular camera with MediaPipe's normalized geometric coordinates, and pairing it with a 2D planar LiDAR for ground-truth distance, we achieved robust 3D perception at a fraction of the cost, computational weight, and power consumption."*

### Trap Question 2: "Why did you decouple facial recognition during robot locomotion?"
* **Defensible Answer:**
  > *"This was an intentional architectural trade-off prioritizing **deterministic safety over non-critical compute**. Our biometric verification pipeline uses InsightFace with deep ArcFace 512-dimensional feature embeddings. Running deep convolutional face detection (RetinaFace) concurrently with YOLOv8n person detection and MediaPipe hand tracking on the quad-core ARM CPU caused processor utilization to exceed 95%, dropping our perception rate from 20 FPS to under 6 FPS and breaching our 150 ms real-time latency deadline. To guarantee ISO 15066 safety compliance during high-speed driving, we decoupled continuous facial verification during locomotion and relied on our Spatial Acceptance Zone filter. In our Future Work, we propose offloading ArcFace inference to a dedicated Hailo-8 M.2 NPU accelerator."*

### Trap Question 3: "Why did you use an ESP32/STM32 coprocessor over UART? Why not drive the motor PWM directly from the Raspberry Pi GPIO pins?"
* **Defensible Answer:**
  > *"The Raspberry Pi runs Linux, which is a **general-purpose, non-real-time operating system**. When the Linux kernel executes background threads or disk I/O, software-generated PWM or GPIO interrupt handling suffers from **jitter and timing latency**, which can cause uneven motor speeds, lost wheel encoder pulses, and catastrophic odometry drift. In contrast, the STM32/ESP32 baseboard is a **hard real-time bare-metal microcontroller**. It handles hardware timer-based PWM, quadrature encoder decoding, and PID closed-loop motor velocity control deterministically at 100 Hz. Communicating via micro-ROS over UART cleanly separates high-level cognition on the Pi from hard real-time motor control on the microcontroller."*

### Trap Question 4: "Your rolling confirmation buffer requires 4 out of 5 frames. Doesn't that slow down the robot's reaction time?"
* **Defensible Answer:**
  > *"It introduces an intentional, highly controlled temporal delay of exactly 200 milliseconds (at 20 FPS), but this is a **vital safety feature, not a bottleneck**. In mobile robotics, instantaneous single-frame classification is hazardous: a human adjusting their eyeglasses or gesturing to another person could produce a momentary 50 ms false positive that causes the robot to suddenly lurch. The 5-frame majority vote buffer filters out high-frequency sensor noise and ensures intent stability. Crucially, **the LiDAR emergency stop does NOT pass through this buffer**—the emergency halt bypasses the buffer entirely as an asynchronous interrupt with zero confirmation delay."*

### Trap Question 5: "How can you claim compliance with ISO 15066 when your robot only has a 2D planar LiDAR?"
* **Defensible Answer:**
  > *"ISO 15066:2016 establishes collaborative safety requirements, specifically governing **Speed and Separation Monitoring (SSM)**. Section 5.5.4 defines the protective separation distance $S$:
  $$S = (v_r \cdot T_r) + (v_h \cdot T_r) + B_r + C$$
  where $v_r$ is robot speed ($0.20 \text{ m/s}$), $v_h$ is human approach speed ($1.2 \text{ m/s}$), $T_r$ is system reaction time ($132.0 \text{ ms}$), $B_r$ is braking distance ($0.08 \text{ m}$), and $C$ is the intrusion margin. Because our total reaction time ($132 \text{ ms}$) is strictly bounded and our physical stopping distance from cruise speed is under $0.10 \text{ m}$, our $0.36 \text{ m}$ LiDAR safety threshold guarantees that the robot achieves complete physical standstill before an approaching human can traverse the separation zone."*

### Trap Question 6: "Why did you choose a 4WD differential drive chassis over Mecanum or omnidirectional wheels?"
* **Defensible Answer:**
  > *"While Mecanum wheels allow omnidirectional holonomic motion (strafing sideways), they exhibit significant slip and friction inconsistencies on real-world industrial surfaces, seams, and floor mats. This wheel slip degrades wheel odometry, leading to substantial localization error in SLAM and AMCL. A 4WD differential drive platform provides superior traction, predictable wheel contact dynamics, and reliable dead-reckoning odometry, which was essential for maintaining sub-decimeter precision along our 15.89-meter patrol corridor."*

### Trap Question 7: "What happens if two people stand in front of the robot simultaneously?"
* **Defensible Answer:**
  > *"Our system resolves multi-person ambiguity through our **Spatial Acceptance Zone Filter**. The perception pipeline calculates the bounding box area and center-of-mass for all detected persons. Any individual standing outside the central $45\% \times 65\%$ corridor is immediately discarded. If two individuals are within the corridor, the tracking node locks onto the primary operator based on proximity (largest bounding box area) and temporal hysteresis. Gestures from background bystanders are discarded."*

### Trap Question 8: "Why didn't you use an off-the-shelf gesture model like the default MediaPipe Gesture Recognizer or YOLOv8-pose?"
* **Defensible Answer:**
  > *"The standard MediaPipe gesture classifier is hard-coded for generic consumer gestures (e.g., thumbs up, peace sign, open palm) and cannot be natively remapped to custom industrial robot navigational commands without severe ambiguity. YOLOv8-pose, while capable, requires significant memory and compute bandwidth on an ARM CPU ($>100 \text{ ms}$ latency). By training our own custom 2-layer MLP on our 19 engineered geometric features, we tailored the model specifically to our 6 robotic navigation primitives, achieved a lightning-fast **1.8 ms inference latency**, and maintained a minuscule **46 KB memory footprint**."*

### Trap Question 9: "Explain what an F-statistic of 0.546 and p-value of 0.580 mean in plain English."
* **Defensible Answer:**
  > *"In plain English, the F-statistic is a ratio: it compares the variance between our three distance groups against the random variation within each group. An F-value close to 1.0 (or below 1.0, like our 0.546) indicates that the differences between distance groups are no larger than random chance. The p-value of 0.580 means there is a 58% probability that any observed difference was purely accidental. Because this is far above the standard 5% significance threshold ($\alpha = 0.05$), we conclude with statistical confidence that operational distance does not affect system latency—proving our scale-normalization algorithm works."*

### Trap Question 10: "How did you prevent SLAM map drift over 15.89 meters without an external motion capture system?"
* **Defensible Answer:**
  > *"We prevented map drift by fusing multiple complementary sensor streams. First, wheel encoder ticks were smoothed and converted into dead-reckoning odometry. Second, we addressed early transform race conditions by enforcing strict TF tree parenting (`odom` $\to$ `base_footprint` $\to$ `base_link`). Third, SLAM Toolbox performed continuous **scan matching**, matching real-time 2D LiDAR point clouds against existing geometric features (walls, doorways). When the robot completed its loop back to Point 1, SLAM Toolbox's graph-based optimizer performed **loop closure**, eliminating residual drift and locking the map into metric alignment."*

### Trap Question 11: "Why did the 2GB Raspberry Pi crash and how did upgrading to 8GB resolve it from an OS perspective?"
* **Defensible Answer:**
  > *"The 2GB Raspberry Pi crashed due to **Linux kernel Out-Of-Memory (OOM) killer activation**. When executing the ROS 2 Humble daemon, RViz visualizers, MediaPipe, YOLOv8, and SLAM Toolbox simultaneously within a Docker container, memory consumption exceeded 1.8 GB. When RAM was exhausted, the Linux kernel began swapping to the MicroSD card, creating severe I/O thrashing and latency spikes. Eventually, the kernel's OOM killer forcibly terminated the largest memory-consuming processes (`slam_toolbox` and `python3`), causing the system to crash. Upgrading to an 8GB Raspberry Pi 5 expanded our physical memory headroom by 400%, keeping active RAM utilization under 45% ($~3.4 \text{ GB}$) with zero swap thrashing."*

### Trap Question 12: "Why did you replace 'Follow-to-Map' with Autonomous Frontier Exploration in your recommendations?"
* **Defensible Answer:**
  > *"During our engineering evaluation, we realized that having a robot shadow a human to build a map introduces significant operational drawbacks. If an operator walks through an unmapped space, the human's legs appear as a dynamic, moving obstacle in the LiDAR scan, which corrupts the static occupancy grid with phantom obstacle trails unless heavy dynamic scan filtering is applied. Furthermore, requiring a human to walk every aisle defeats the purpose of full autonomy. Instead, **Autonomous Frontier Exploration** (such as `explore_lite`) allows the robot to autonomously detect information boundaries (frontiers between known free space and unknown space) and navigate systematically to map the facility without human presence or map corruption."*

---
*(End of Master Oral Defense Guide)*
