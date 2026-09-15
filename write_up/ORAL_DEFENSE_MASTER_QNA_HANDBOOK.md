# Autonomous Mobile Robot Cognition System
## Master Oral Defense Preparation & "Mastering to the Tooth" Viva Voce Handbook

**Project Title:** Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture  
**Authors:** Eleana Osei Owusu (Index: 4121230024) & Joel Nii Adjetey Ahulu (Index: 4121230020)  
**Supervisor:** Mr. Micheal Xenya  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering, Department of Computer Engineering  
**Degree:** Bachelor of Science in Computer Engineering  

---

## Purpose & How to Master This Document

This handbook is your **secret weapon** for the final project defense. It contains exhaustive, mathematically and empirically grounded answers to every question the defense panel, external examiners, or department professors can ask you. 

By reading and rehearsing these structured responses, you will be able to speak with absolute command and authority, looking directly at the examiners with poise, confidence, and fluency, without staring at the PowerPoint slides.

---

# Section 1: Mechatronic & Hardware Architecture Justifications

### Question 1: "Why did you use the Raspberry Pi 5, and why specifically the 8GB version?"

#### The Direct Answer (Say This with Confidence):
> *"We selected the Raspberry Pi 5 because our design philosophy is strictly edge-native: all perception, cognition, and spatial navigation must execute locally on the mobile robot without relying on cloud servers or external GPU workstations. The Raspberry Pi 5's Broadcom BCM2712 quad-core 64-bit Arm Cortex-A76 processor running at 2.4 GHz provides a 2.5× to 3× performance leap over the Raspberry Pi 4, enabling us to sustain an end-to-end perception cycle of 28.4 FPS on CPU alone."*

#### Deep Technical Defense (If the Panel Pushes Further):
1. **Why not an NVIDIA Jetson Nano?**  
   The Jetson Nano is based on an obsolete Maxwell GPU architecture that was officially discontinued by NVIDIA and is restricted to legacy JetPack 4.6 (Ubuntu 18.04). Ubuntu 18.04 does not natively support modern ROS 2 Humble Hawksbill (which requires Ubuntu 22.04 or 24.04). Running ROS 2 Humble on a Jetson Nano requires cumbersome, slow Docker translation layers that degrade memory bandwidth and complicate hardware GPIO/UART access. The Raspberry Pi 5 runs Ubuntu 24.04 LTS natively with Tier-1 ROS 2 Humble compatibility.
2. **Why not an Arduino, STM32, or ESP32 as the main computer?**  
   Microcontrollers possess insufficient RAM (typically kilobytes to a few megabytes) and lack memory management units (MMUs) to run full Linux operating systems, Docker containers, OpenCV, ONNX Runtime, MediaPipe, or the ROS 2 Nav2 stack. They are purely hardware controllers, not cognitive computing engines.
3. **Why did you upgrade from 2GB to 8GB RAM?**  
   During early empirical bench tests with a 2GB Raspberry Pi 5, concurrently running `slam_toolbox` (building a 5cm occupancy grid), the ROS 2 node graph, and ONNX neural network runtimes consumed ~2.1 GB of RAM. This exhausted physical memory, causing severe swap thrashing and triggering the **Linux Out-Of-Memory (OOM) Killer**, which abruptly terminated the robot's perception nodes mid-operation. Upgrading to the **8GB LPDDR4X** model provided a peak operating ceiling of 2.8 GB under full autonomous mission load, leaving over **5.2 GB of clean headroom**, completely eliminating memory faults and process termination.

---

### Question 2: "Why did you use an ESP32 microcontroller? Why couldn't the Raspberry Pi do everything?"

#### The Direct Answer:
> *"We decoupled high-level cognition from low-level actuation by introducing the Espressif ESP32-S3 microcontroller as a dedicated real-time co-processor. A standard Linux operating system on a Raspberry Pi is non-deterministic and non-real-time. Running heavy vision models causes CPU scheduling latency and microsecond jitter. If the Pi attempted to generate motor PWM signals and count high-frequency optical encoder ticks, computational spikes in the vision pipeline would cause dropped encoder ticks, erratic motor stutter, and loss of wheel odometry."*

#### Deep Technical Defense:
1. **Hard Real-Time vs. Soft Real-Time:**  
   The ESP32-S3 runs FreeRTOS with dedicated 32-bit hardware timers and high-speed interrupt service routines (ISRs). It generates steady, high-frequency Pulse Width Modulation (PWM) signals to the onboard H-bridges and counts quadrature encoder pulses with microsecond precision.
2. **The Micro-ROS Architectural Bridge:**  
   The ESP32-S3 runs a lightweight micro-ROS client firmware that communicates across a dedicated, high-speed **921,600 baud UART** serial bus with the `micro_ros_agent` hosted on the Raspberry Pi 5. This allows the ESP32 to publish raw odometry (`/odom_raw`) at 11.5 Hz and IMU telemetry (`/imu`) at 23.2 Hz, while subscribing to `/cmd_vel` velocity commands, maintaining a rock-solid, decoupled actuation loop.
3. **Electrical Noise and Brownout Isolation:**  
   The Yahboom baseboard features isolated power distribution: motors draw high transient currents from the 7.4V battery pack through dedicated buck converters, completely isolating the Raspberry Pi's sensitive 5V logic rail from back-EMF voltage spikes and brownout resets during sudden motor reversals.

---

### Question 3: "What is LiDAR? Why did you use LiDAR instead of just using cameras?"

#### The Direct Answer:
> *"LiDAR stands for **Light Detection and Ranging**. It is an active optical remote sensing technology that emits pulsed laser beams at 905 nanometers and measures the round-trip time-of-flight or triangulation phase shift to calculate precise radial distances to surrounding surfaces. We utilized the MS200 planar LiDAR spinning at 10 Hz across a full 360-degree field of view up to 12 meters with millimeter accuracy."*

#### Deep Technical Defense (Camera vs. LiDAR Trade-Off):
| Operational Parameter | Monocular / RGB-D Camera | 2D Planar LiDAR (MS200) | Robotic Engineering Advantage of LiDAR |
| :--- | :--- | :--- | :--- |
| **Field of View (FoV)** | Narrow: 60° to 80° horizontal. Blind to side/rear obstacles. | **Full 360° continuous planar sweep.** | Guarantees omnidirectional obstacle detection during in-place pivoting and reversing. |
| **Lighting Vulnerability**| Severe: Fails in dark corridors, shadows, or direct sunlight flare. | **Immune: Active infrared laser emissions.** | Operates with identical precision in broad daylight or total pitch darkness. |
| **Computational Cost** | Heavy: Stereo depth or monocular depth neural networks consume 60–80% CPU. | **Near Zero: Outputs raw distance array $(r, \theta)$ directly in C structs.** | Leaves 90% of the Raspberry Pi CPU free for AI gesture recognition and Nav2 planning. |
| **Metric Accuracy** | Degrades quadratically with distance ($>2.0\,\text{m}$, depth error exceeds 5–10%). | **Millimeter-level linear distance accuracy across entire 12-meter radius.** | Generates crisp, distortion-free 2D occupancy grid maps in `slam_toolbox`. |

---

### Question 4: "Why did you use ROS 2 and not ROS 1, MQTT, or raw Python scripts?"

#### The Direct Answer:
> *"We built the system natively on **ROS 2 Humble Hawksbill LTS** because modern collaborative robotics requires decentralized, deterministic, and modular inter-process communication. Traditional monolithic Python scripts create single points of failure where an unhandled exception in the camera loop crashes the entire robot chassis. ROS 2 provides standardized hardware abstraction, modular process isolation, and production-grade navigational frameworks."*

#### Deep Technical Defense:
1. **ROS 2 vs. ROS 1 (DDS vs. roscore):**  
   ROS 1 relied on a centralized master node (`roscore`). If `roscore` crashed or experienced network latency, the entire robotic communication network collapsed. ROS 2 is built on the Object Management Group (OMG) **Data Distribution Service (DDS)** standard (`rmw_fastrtps_cpp`). It is fully peer-to-peer and decentralized with zero single point of failure.
2. **Quality of Service (QoS) Guarantees:**  
   ROS 2 allows us to declare distinct network contracts per topic:
   - Motor control and E-Stop topics (`/cmd_vel`) use **RELIABLE** QoS (guaranteed delivery via TCP-like DDS acknowledgments).
   - High-throughput video frames (`/camera/image_raw/compressed`) use **BEST_EFFORT** QoS to prevent buffer bloat and latency buildup.
3. **Battle-Tested Industrial Navigation Ecosystem:**  
   ROS 2 gives us native access to the **Nav2** architecture (costmap inflation layers, DWB local trajectory planners, AMCL probabilistic particle filters) and **SLAM Toolbox**. Developing these algorithms from scratch in raw Python would have taken years and lacked the real-time reliability required for physical human safety.

---

# Section 2: Literature Review, Theoretical Gaps & Problem Statement

### Question 5: "What did the authors in your literature review achieve, and what are their specific gaps?"

#### Benchmark 1: Tsitos et al. (2022) — *Real-Time Feasibility of a Human Intention Method Evaluated Through a Competitive Human-Robot Reaching Game* (IEEE RAL)
- **What they achieved:** Tracked upper-limb kinematics using an RGB-D camera and OpenPose. Extracted wrist joint velocity profiles to predict reach targets, controlling an industrial Universal Robots UR3 robotic arm in real time during a competitive game.
- **Their Gaps & Limitations:**
  1. *Stationary Workstation:* Their system was deployed on a static tabletop manipulator connected to an external high-power computer; it had no mobile base.
  2. *No Mobile Navigation:* The human and robot never shared physical floor space; dynamic collision avoidance while traversing an environment was never investigated.
  3. *Implicit Only:* The operator could not issue deliberate, explicit supervisory commands (e.g., STOP, GO, FOLLOW); the robot only reacted implicitly to reach motions.

#### Benchmark 2: Mahmud et al. (2022) — *3D Gesture Recognition and Adaptation for Human-Robot Interaction*
- **What they achieved:** Used a Microsoft Kinect depth sensor to capture 3D skeletal joints from 24 participants, classifying dynamic and pointing gestures using HMMs, SVMs, and CNNs. Proposed a semi-supervised gesture adaptation framework.
- **Their Gaps & Limitations:**
  1. *Proprietary Heavy Hardware:* Bound strictly to the high-power Microsoft Kinect sensor, incompatible with lightweight low-cost mobile robots.
  2. *Simulation Only:* Navigation was evaluated solely inside a computer simulation; physical real-world floor issues (wheel slippage, ambient lighting shifts, embedded compute latency) were completely unaddressed.
  3. *Unimanual Limitation:* Interaction was restricted exclusively to right-hand joint models.

#### Benchmark 3: Li et al. (2023) — *Safe and Efficient Motion Planning for Material Transportation Robots Considering Intention Prediction of Obstacles*
- **What they achieved:** Combined 2D LiDAR and camera CNN detection to predict whether construction workers would yield to a material transport robot, dynamically updating ROS 2 Nav2 global and local costmaps.
- **Their Gaps & Limitations:**
  1. *Virtual Environment:* Entirely implemented and evaluated in NVIDIA Isaac Sim; no physical hardware validation on real embedded microprocessors.
  2. *No Command Channel:* The robot had no mechanism to receive intentional human guidance or touchless gestures; workers were treated merely as dynamic obstacle obstacles.

#### Non-Visual Alternatives: Zafar et al. (2023) — Surface Electromyography (sEMG)
- **What they achieved:** Captured forearm muscle electrical impulses via wearable skin electrodes to classify hand gestures without optical cameras, eliminating visual occlusion and lighting issues.
- **Their Gaps & Limitations:**
  1. *Operator Burden:* Requires human personnel to wear sticky, bulky electrode sleeves and battery packs on their arms.
  2. *Unhygienic & Impractical:* Totally unsuitable for sterile healthcare environments, food processing, or hot industrial warehouses where sweat degrades electrode conductivity.

---

### Question 6: "What is the ONE common gap among all prior works, and does your project solve all of them?"

#### The Direct Answer:
> *"The single common gap linking all prior research is **The Disconnect Between Perception and Grounded Mobile Action**. Prior researchers treated gesture recognition as an isolated classification task evaluated on offline datasets or stationary workstation GPUs, completely decoupled from real-time edge processing on a mobile robot navigating dynamic, mapped physical environments."*

#### Are we solving ALL the gaps? (Give this balanced, scientific answer):
> *"We do not claim to solve every conceivable robotics challenge, but we solve the foundational engineering bottleneck:*
> 1. *We eliminate high-power workstation and cloud dependency by running the full perception pipeline on an embedded **Raspberry Pi 5 in under 75 ms**.*
> 2. *We eliminate distance domain shift through our **19-D scale-invariant geometric feature vector**.*
> 3. *We bridge perception to mobile action by integrating the MLP classifier and LSTM motion predictor directly into **ROS 2 Nav2 costmaps and a supervisory Brain state machine**.*
> 4. *We enforce physical collaborative safety using **MS200 LiDAR in accordance with ISO 15066**.*
> 
> *What we delimit as future extensions are dense crowd social navigation, operations in unlit darkness for the RGB camera, and 3D terrain navigation."*

---

### Question 7: "What backs up or proves your Problem Statement? What standards or citations can you reference?"

#### Reference 1: Cloud Robotics Failure Rates & Network Latency
- Citing **Tsitos et al. (2022)** and **Chinchali et al. (2021)**: Offboard cloud inference introduces round-trip network latencies of $150\,\text{ms} \to 350\,\text{ms}$ and random packet dropouts over Wi-Fi. In an industrial facility where a mobile robot travels at $0.5\,\text{m/s}$, a $300\,\text{ms}$ network drop means the robot travels $15\,\text{cm}$ blind before braking can begin, violating real-time human safety thresholds.

#### Reference 2: Distance Domain Shift in Optical Landmark Tracking
- Citing **Sunderhauf et al. (2018)**: Feeding raw pixel coordinates $(u, v)$ to neural networks results in classification collapse when the human moves between $1.0\,\text{m}$ and $2.5\,\text{m}$ from the lens. At $2.5\,\text{m}$, the hand occupies $4\times$ fewer pixels than at $1.0\,\text{m}$, distorting unnormalized feature distributions.

#### Reference 3: Collaborative Safety Standards (ISO 15066:2016)
- **ISO 15066:2016 (Clause 5.5.4 — Speed and Separation Monitoring):** Mandates that the protective separation distance ($S$) between a human worker and an autonomous mobile vehicle must satisfy:
  $$S \ge (v_r \cdot T_r) + (v_h \cdot T_h) + B_r + C$$
  Our system physically proves this compliance: with an end-to-end perception latency of $T_r = 74.2\,\text{ms}$, robot speed $v_r = 0.25\,\text{m/s}$, and braking deceleration $a = 0.8\,\text{m/s}^2$, our physical stopping distance is **0.42 m**, safely within our configured **0.45 m** LiDAR clearance threshold.

---

# Section 3: Research Questions & Empirical Answers

### Question 8: "What research questions did you formulate from your specific objectives, and have they been answered?"

#### The 4 Core Engineering Research Questions (ERQs):

| Research Question | Formulated Technical Inquiry | Empirical Answer & Chapter 4 Evidence |
| :--- | :--- | :--- |
| **ERQ 1 (Edge Feasibility & Latency Budget)** | Can a multi-stage visual perception pipeline execute natively on a low-cost edge processor (Raspberry Pi 5) without GPU acceleration while keeping end-to-end latency below 150 ms? | **YES.** Proven empirically in Table 4.1. Total end-to-end sensing-to-actuation latency is **74.2 ms** (Camera capture 50 ms + MediaPipe landmarks 16 ms + MLP inference 1.2 ms + DDS dispatch 3 ms + ESP32 motor ramp 4 ms), leaving a **50.5% margin below the 150 ms threshold**. |
| **ERQ 2 (Mathematical Feature Invariance)** | To what extent does converting raw landmark coordinates into 19 scale-invariant geometric features eliminate distance domain shift compared to unnormalized pixel baselines? | **YES.** Proven in Section 4.2. Raw pixel coordinates degraded to 68.4% accuracy at 2.5m distance. Our 19-D geometric feature vector maintained **99.38% test accuracy** and **96.67% physical trial accuracy** across all distances from 1.0m to 2.5m. |
| **ERQ 3 (Multi-Person Disambiguation)** | How effectively can a central spatial-zone filter coupled with rolling majority-vote temporal buffering isolate a primary operator and prevent bystander interference? | **YES.** Proven in Section 4.4. A 5-frame rolling consensus window ($N=5$) and a centered 45% $\times$ 65% interaction zone achieved **100% false-positive rejection** of background pedestrians walking across the camera FoV. |
| **ERQ 4 (Middleware Coupling & Safety)** | Can discrete hand gestures and continuous motion predictions be integrated within ROS 2 middleware to govern mobile robot velocities in compliance with ISO 15066 safety limits? | **YES.** Proven in Section 4.5 & Table 4.4. LiDAR frontal corridor safety (<0.36m) executed emergency halts in **0.42 m**, satisfying ISO 15066 separation requirements while enabling seamless touchless preemption via `twist_mux`. |

---

# Section 4: Methodology & Software Pipeline

### Question 9: "Explain your methodology. What engineering steps did you follow, and is a bullet list on a slide the best way to represent it?"

#### The Direct Answer:
> *"No, a bare bullet list is insufficient to represent an engineering methodology. Our methodology followed a disciplined, 6-Phase Engineering Pipeline moving from sensor calibration up to closed-loop physical validation:"*

#### The 6-Phase Methodology Workflow:
1. **Phase 1: Mechatronic Hardware Integration & Embedded Bridge:**  
   Assembled the 4WD mobile base, mounted the Raspberry Pi 5, MS200 LiDAR, and 2-DOF camera gimbal. Established high-speed 921,600 baud UART micro-ROS communication with the ESP32-S3 co-processor.
2. **Phase 2: Custom Dataset Construction & Sensor Calibration:**  
   Collected 6,000 balanced image samples (1,000 per class across 6 gestures: STOP, GO, FOLLOW, LEFT, RIGHT, BACK) directly through the onboard robot camera under varying lighting conditions to eradicate domain shift.
3. **Phase 3: Mathematical Feature Extraction & Neural Network Training:**  
   Engineered the 19-D scale-invariant feature vector (palm-normalized Euclidean distances and joint curl angles). Trained a lightweight 3-layer MLP classifier in PyTorch, exported to ONNX (46 KB, 1.2 ms inference). Trained an LSTM recurrent network on 10-frame sliding pose sequences to predict future human trajectories.
4. **Phase 4: Cognitive State Machine (`brain_node`) & Priority Arbitration:**  
   Constructed a centralized ROS 2 supervisory node implementing a rolling 5-frame consensus buffer, subject-locking FSM, active visual servoing, and multi-tier priority velocity routing via `twist_mux`.
5. **Phase 5: Metric SLAM Mapping & Nav2 Navigation Stack Tuning:**  
   Configured `slam_toolbox` to generate a 5cm 2D occupancy grid of the test facility. Integrated AMCL particle filter localization and tuned Nav2 costmap inflation buffers (0.25m inflation radius) for collision-free autonomous transit.
6. **Phase 6: Empirical Experimental Benchmarking & ISO 15066 Validation:**  
   Executed 180 physical gesture trials, measured end-to-end component latency budgets, evaluated LiDAR safety stopping distances, and recorded synchronized telemetry rosbags.

---

### Question 10: "Explain all ROS concepts used in this project, giving exact examples of where they were used."

| ROS 2 Architectural Concept | Engineering Definition | Exact Instance & Implementation in This Project |
| :--- | :--- | :--- |
| **Node** | An independent executable process that performs computation, designed to be modular and decoupled. | `gesture_node.py` (extracts landmarks & runs MLP), `person_detection_node.py` (runs YOLOv8 & LSTM), `brain_node.py` (supervisory state machine), `slam_toolbox` (mapping). |
| **Topic** | A unidirectional, asynchronous named communication bus over which nodes exchange messages via publish/subscribe. | `/camera/image_raw/compressed` (raw video stream), `/cognition/gesture` (classified hand gestures), `/scan` (LiDAR ranges), `/cmd_vel` (final chassis velocity). |
| **Message** | A strictly typed data structure defining the fields and data types transmitted over a topic. | `geometry_msgs/msg/Twist` (linear and angular velocities), `sensor_msgs/msg/LaserScan` (360° laser ranges), `cognition_interfaces/msg/Gesture` (gesture ID & confidence). |
| **Service** | A synchronous request/response communication pair between a client node and a server node for on-demand tasks. | `std_srvs/srv/SetBool` used by `brain_node` to toggle active tracking or reset odometry on demand. |
| **Action** | An asynchronous, non-blocking goal-oriented communication pattern supporting goal dispatch, continuous feedback, and preemption/cancellation. | `nav2_msgs/action/NavigateToPose` used by `mission_manager.py` to dispatch multi-waypoint patrol goals to Nav2 and monitor remaining distance live. |
| **Parameter** | Configuration values stored dynamically within individual nodes, modifiable at startup or runtime via YAML. | `linear_speed: 0.25`, `lidar_safety_distance: 0.36`, `gesture_buffer_size: 5` declared in `brain_node.py`. |
| **TF2 Transform Tree** | The coordinate transform framework that tracks time-synchronized spatial relationships between physical frames. | Maintains transformations between `map` (global floor) $\to$ `odom` (integrated wheel odometry) $\to$ `base_footprint` (chassis ground projection) $\to$ `laser_frame` (LiDAR). |
| **QoS Profile** | Quality of Service contracts governing network reliability and packet durability in DDS. | **RELIABLE + TRANSIENT_LOCAL** on `/cmd_vel` and `/amcl_pose` (safety-critical); **BEST_EFFORT + VOLATILE** on `/camera` and `/scan` (high-bandwidth sensor streams). |
| **Micro-ROS Bridge** | Middleware extension linking resource-constrained microcontrollers to the ROS 2 DDS graph over serial UART. | `micro_ros_agent` on Raspberry Pi 5 bridging the ESP32-S3 FreeRTOS client at 921,600 baud. |

---

# Section 5: Presentation Delivery Mastery & Viva Voce Psychology

### 1. How to Present Without Looking at the Slides ("The Anchor Method")
- **Never Read Sentences:** Slides exist for the *audience* to see diagrams and numbers; they do not exist for the *speaker* to read.
- **Use Slide Titles as Mental Anchors:** When you transition to a slide, glance at the title for half a second, take one breath, look straight into the eyes of the center examiner, and deliver the 3 key takeaways from memory.
- **The "Rule of Three":** On every slide, deliver exactly three crisp sentences:
  1. *Sentence 1 (What):* State what the slide depicts (e.g., *"This slide presents our mechatronic architecture..."*).
  2. *Sentence 2 (Why):* Explain why it was designed this way (e.g., *"We offloaded real-time motor control to an ESP32-S3 to prevent Linux CPU spikes from causing wheel jitter..."*).
  3. *Sentence 3 (The Empirical Proof):* Quote the hard metric (e.g., *"This sustained a steady 11.5 Hz odometry stream across a 921,600 baud serial bus."*).

### 2. The "Story Arc" Structure
Every great engineering defense follows a classic 5-act narrative arc:
1. **The Hook & Problem:** Robots must work with humans touchlessly, but current systems rely on bulky cloud GPUs, break down when users move farther away, and bump into obstacles.
2. **The Engineering Insight:** We can replace heavy pixel networks with 19 scale-invariant geometric features and offload motor timing to a micro-ROS co-processor.
3. **The Architecture:** How Pi 5, ESP32-S3, MS200 LiDAR, and ROS 2 work together in harmony.
4. **The Hard Evidence:** 99.38% accuracy, 74.2 ms latency, 0.42 m stopping distance.
5. **The Real-World Impact:** Touchless, safe collaborative logistics ready for sterile hospitals and industrial factories.

### 3. De-Escalating Tough or Aggressive Panel Questions
- **Rule 1: Never Argue or Get Defensive.** If an examiner points out a limitation, acknowledge it with respect:  
  *"Thank you for that insightful observation, Professor. You are completely correct that in dense crowds, occlusion becomes a significant challenge. Within our defined undergraduate scope, we bounded our filter to a primary operator in a central spatial zone, but integrating 3D point-cloud tracking is indeed the exact direction we recommend for future work."*
- **Rule 2: Don't Bluff.** If you don't know an obscure theoretical formula, pivot to what you physically measured:  
  *"I do not have the exact theoretical constant at hand, Professor, but during our empirical physical bench trials, we observed that..."*
- **Rule 3: Use the Word "Empirical".** Engineering panels love empirical validation. Whenever possible, ground your answer in physical robot data: *"During physical testing on the Yahboom testbed...", "Our recorded rosbag telemetry verified that..."*.
