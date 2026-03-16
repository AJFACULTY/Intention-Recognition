# Autonomous Mobile Robot Cognition System
### Human Intention Recognition via Edge-Computed Motion & Hand Gestures

<p align="center">
  <a href="https://docs.ros.org/en/humble/"><img src="https://img.shields.io/badge/ROS_2-Humble-22314E?logo=ros&logoColor=white" alt="ROS 2 Humble" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10" /></a>
  <a href="https://www.raspberrypi.com/"><img src="https://img.shields.io/badge/Edge_Compute-Raspberry_Pi_5_(8GB)-C51A4A?logo=raspberrypi&logoColor=white" alt="Raspberry Pi 5" /></a>
  <a href="https://www.iso.org/standard/69263.html"><img src="https://img.shields.io/badge/Safety_Standard-ISO_15066-0057B8" alt="ISO 15066 Compliant" /></a>
  <a href="https://www.iso.org/standard/51528.html"><img src="https://img.shields.io/badge/Risk_Mitigation-ISO_12100-2EA44F" alt="ISO 12100 Compliant" /></a>
  <a href="#results"><img src="https://img.shields.io/badge/End--to--End_Latency-132_ms-orange" alt="Latency 132ms" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License MIT" /></a>
</p>

<p align="center">
  <img src="docs/assembled_robot_real.jpg" width="420" alt="Physical Autonomous Mobile Robot" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</p>

An end-to-end, edge-computed robotics application for real-time human intention recognition and collaborative navigation in shared human-robot workspaces. Operating entirely on an onboard edge computer without cloud reliance, external GPUs, or wearable sensors, the system achieves a verified **132 ms camera-to-motor latency** and **96.67% physical operational accuracy**.

---

## Key Highlights

- **Edge-First Neural Inference:** Fully self-contained compute pipeline on a Raspberry Pi 5 (8GB) executing 20 Hz MediaPipe hand tracking and neural classification.
- **Scale-Invariant 19-D Geometric Features:** Ratio-based geometric normalization invariant to distance, camera perspective, and hand anthropometrics (**99.38% test accuracy** across 6 gesture classes).
- **2-DOF Active Vision Platform:** Pan/tilt servo gimbal driven by visual servoing, exponential smoothing, and a memory-hold state machine for continuous human target tracking.
- **ISO 15066 Dual-Layer Safety Arbitration:** `twist_mux` priority arbitration with LiDAR-based emergency preemption and automatic active reverse braking ($<0.36\,\text{m}$).
- **Autonomous Navigation & SLAM:** Seamlessly integrates Nav2 multi-waypoint patrol, SLAM Toolbox spatial mapping, and supervisory finite-state machine (FSM) control.
- **Real-Time Telemetry Web HUD:** High-performance browser visualizer streaming 20 Hz live occupancy grids, robot pose, gesture confidence, and system health.

---

## System Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │             USB HD Camera (20 Hz)            │
                               └──────────────────────┬───────────────────────┘
                                                      │  Raw BGR Frames
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │        MediaPipe Hand Landmarker (21 × 3D)   │
                               └──────────────────────┬───────────────────────┘
                                                      │  3D Landmark Coordinates
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │   19-D Geometric Feature Extraction Engine   │
                               │  (Angles, Inter-joint Ratios, Span Metrics)  │
                               └──────────────────────┬───────────────────────┘
                                                      │  Normalized Feature Vector
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │     6-Class MLP Neural Classifier (ONNX)     │
                               │   STOP | GO | FOLLOW | LEFT | RIGHT | BACK   │
                               └──────────────────────┬───────────────────────┘
                                                      │  Raw Gesture & Confidence
                                                      ▼
 ┌─────────────────────────────┐       ┌──────────────────────────────────────┐
 │   2D ToF MS200 LiDAR Scan   │       │   Supervisory Cognition Brain FSM    │
 │ (Emergency Distance Bubble) │       │ (5-Frame Consensus + 3s Command Lock)│
 └──────────────┬──────────────┘       └──────────────────┬───────────────────┘
                │ Safety Preemption (/cmd_vel_safety)     │ Gesture Cmd (/cmd_vel_gesture)
                └──────────────────────┬──────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │     twist_mux Priority Node   │
                       │ (Safety > Joy > Gesture > Nav)│
                       └───────────────┬───────────────┘
                                       │  Arbitrated /cmd_vel
                                       ▼
                       ┌───────────────────────────────┐
                       │     micro-ROS / UART Bridge   │
                       └───────────────┬───────────────┘
                                       │  Motor PWM Signals
                                       ▼
                       ┌───────────────────────────────┐
                       │  ESP32-S3 Differential Drive  │
                       └───────────────────────────────┘
```

---

## Hardware Specification

| Component | Engineering Specification | Role |
| :--- | :--- | :--- |
| **Edge Compute SBC** | Raspberry Pi 5 (Quad-Core Cortex-A76 @ 2.4 GHz, 8GB LPDDR4X) | ROS 2 middleware, perception, neural inference |
| **Microcontroller** | ESP32-S3 Dual-Core Xtensa LX7 | Low-level motor control, micro-ROS agent |
| **LiDAR Sensor** | MS200 2D Time-of-Flight (ToF) LiDAR (360°, 12m range, 10 Hz) | Obstacle avoidance, SLAM, safety envelope |
| **Active Vision Gimbal** | 2-DOF Pan/Tilt platform (Bus Servos, 20 ms update rate) | Dynamic human operator tracking |
| **Optical Perception** | Wide-angle USB Camera (640×480 @ 20 FPS) | Hand landmarking, facial ID, gesture capture |
| **Acoustic Warning** | Industrial Safety Horn & Chime Module | ISO 15066 acoustic proximity hazard alert |
| **Chassis** | 4WD Differential Mobile Robot Chassis | Physical locomotion and payload transport |

---

## Core Node Inventory

| ROS 2 Node | Script / Source | Primary Topic(s) | Function |
| :--- | :--- | :--- | :--- |
| `camera_pub` | `src_nodes/camera_pub.py` | `/camera/image_raw` | High-throughput 20 Hz low-latency camera capture |
| `gesture_node` | `src_nodes/gesture_node.py` | `/gesture/intent` | MediaPipe extraction + 19-D invariant MLP classification |
| `brain_node` | `src_nodes/brain_node.py` | `/cmd_vel_gesture`, `/brain/state` | Consensus filtering, state transitions, mission lock |
| `active_vision_node` | `src_nodes/active_vision_node.py` | `/gimbal/cmd`, `/camera/target_error` | Proportional pan/tilt visual servoing & memory hold |
| `safety_audio_node` | `src_nodes/safety_audio_node.py` | `/beep`, `/safety/audio_alert` | Acoustic state chimes & ISO 15066 safety alarms |
| `person_detection_node` | `src_nodes/person_detection_node.py` | `/human/bbox`, `/human/detected` | Bounding box localization for visual following |
| `face_recognition_node` | `src_nodes/face_recognition_node.py` | `/face/operator_id` | Operator biometric identification & spatial gating |
| `odom_imu_republisher` | `src_nodes/odom_imu_republisher.py` | `/odom`, `/imu/data` | Clean TF odometry republishing with covariance tuning |

---

## Empirical Benchmark Results

| Metric | Target / Benchmark Standard | Physical Empirical Result | Status |
| :--- | :--- | :--- | :--- |
| **End-to-End Latency** | $< 150\,\text{ms}$ total | **132 ms** (Camera: 49ms, MLP: 12ms, DDS: 4ms, Motor: 67ms) | ✅ Exceeded |
| **Gesture Holdout Accuracy** | $> 95.0\%$ | **99.38%** (Holdout test dataset across 6 classes) | ✅ Exceeded |
| **Physical Trial Accuracy** | $> 90.0\%$ | **96.67%** (180 physical trials in shared testbed) | ✅ Exceeded |
| **Multi-Waypoint Patrol** | $100\%$ waypoint legs | **15.89 m traversed**, $0.155\,\text{m}$ Mean Absolute Error | ✅ Exceeded |
| **Emergency Braking Distance** | $< 0.50\,\text{m}$ | **$< 0.36\,\text{m}$** (Immediate LiDAR preemption) | ✅ Exceeded |
| **Edge Compute Load** | Thermal stability on SBC | **311% CPU across 4 cores**, 2.1 GB RAM utilization | ✅ Stable |

---

## Quick Start Guide

### 1. Launch Master Interactive Menu
The master menu automatically detects robot connectivity, checks ROS 2 node status, and provides one-key execution:
```bash
./scripts/menu.sh
```

### 2. Deploy Full Robot Stack
To launch the entire cognitive architecture, active vision tracking, LiDAR safety preemption, and motor drivers in a single command:
```bash
ros2 launch launch/master_robot.launch.py
```

### 3. Launch Real-Time Web Cockpit HUD
Launch the dual-mode telemetry server to stream robot telemetry, occupancy grid maps, and gesture states:
```bash
python3 scripts/web_map_visualizer.py
```
*Open `http://localhost:8080` in any browser on your network.*

### 4. Run Automated Verification Suite
Run the 7-tier test suite to qualify all ROS 2 nodes, neural models, safety reverse behaviors, and audio chimes locally:
```bash
python3 scripts/run_all_local_verifications.py
```

---

## Documentation

For full step-by-step assembly, micro-ROS network configuration, SLAM calibration, Nav2 multi-waypoint patrol parameters, and operational runbooks:

- 📖 **[Robot Operations Manual](docs/ROBOT_OPERATIONS_MANUAL.md)**
- 📐 **[Active Vision Gimbal & Biometric Tracking Spec](docs/ACTIVE_VISION_SPEC.md)**

---

## Repository Structure

```
├── cognition_dashboard/     # Web-based real-time telemetry HUD
├── config/                  # Nav2, twist multiplexer, and system configuration YAMLs
├── docs/                    # Architecture specifications, manuals, and empirical trajectories
├── launch/                  # Full-stack and modular ROS 2 launch files
├── maps/                    # Calibrated 2D SLAM occupancy grid maps
├── ml_models/
│   ├── training/            # Scale-invariant feature extraction & training scripts
│   └── weights/             # Production ONNX & serialized neural network models
├── scripts/                 # Operations, dispatchers, telemetry, and deployment tooling
├── src_nodes/               # Core ROS 2 perception, cognition, safety, and vision nodes
└── tests/                   # Automated verification test suites
```

---

## License & Citation

This project is licensed under the **MIT License**. Compliant with ISO 15066:2016, ISO 12100:2010, ROS REP-103, and REP-105 standards.
