# Autonomous Mobile Robot Cognition System
## Human Intention Recognition Using Motion and Hand Gesture

[![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E.svg)](https://docs.ros.org/en/humble/)
[![Platform](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%20(8GB)-C51A4A.svg)](https://www.raspberrypi.com/)
[![Micro-ROS](https://img.shields.io/badge/Micro--ROS-ESP32--S3-E7352C.svg)](https://micro.ros.org/)
[![Safety](https://img.shields.io/badge/Compliance-ISO%2015066%3A2016-blue.svg)](https://www.iso.org/standard/69263.html)

---

## 1. Executive Summary

This repository contains the complete robotics codebase, edge AI perception stack, simulation environments, academic write-up, and oral defense artifacts for the undergraduate engineering thesis:

* **Title:** Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture
* **Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering, Department of Computer Engineering
* **Authors:** Eleana Osei Owusu (Index: `4121230024`), Joel Nii Adjetey Ahulu (Index: `4121230020`)
* **Supervisor:** Mr. Micheal Xenya

---

## 2. Hardware Architecture & Testbed

The system operates across a dual-tier distributed compute topology:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Physical Mobile Robot Platform                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Raspberry Pi 5 (8GB RAM)]  ─── High-Level Cognition & Perception          │
│    • Ubuntu 22.04 LTS + ROS 2 Humble                                        │
│    • MediaPipe Hand Landmark Extractor (21 3D Landmarks)                    │
│    • 19-D Position-Invariant Geometric MLP Gesture Classifier (99.38% Acc)  │
│    • Supervisory Brain Finite State Machine (FSM) Node                      │
│    • Active Vision 2-DOF Gimbal Pan/Tilt Servoing Node                      │
│    • twist_mux Velocity Priority Arbitrator & Emergency Brake Preemption    │
│    • Nav2 Navigation Stack & SLAM Toolbox                                   │
├───────────────────────────────────┬─────────────────────────────────────────┤
│          Hardware UART Bus        │             USB 2.0 / 3.0 Bus           │
│         (/dev/ttyAMA0 @ 115.2k)   │                                         │
▼                                   ▼                                         ▼
[Yahboom micro-ROS ESP32-S3]     [MS200 2D ToF LiDAR]             [2-DOF Gimbal + USB Cam]
 • 4-Wheel Differential Drive     • 12.5 Hz Scan Rate              • Pan (-90° to +90°)
 • Real-time Closed-Loop PID      • 12 m Detection Range           • Tilt (-45° to +45°)
 • Odometry Publisher             • ISO 15066 <0.36m Safety Bubble • 640×480 @ 20 FPS Stream
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Layout

The workspace is organized into modular engineering domains:

```
ros2_cognition_ws/
├── README.md                      # Canonical project documentation (this file)
├── AGENTS.md                      # Mandatory AI agent operating rules & turn safety budgets
├── MASTER_WRITEUP_ROADMAP.md      # Symlink to active roadmap (write_up/TODO_AND_ROADMAP.md)
├── OPERATOR_COMMAND_MANUAL.md     # Turnkey field commands and cheat-sheet for robot operators
├── PROJECT_EXPLAINER_AND_DEFENSE_HANDBOOK.md # Deep-dive Q&A handbook for academic defense
├── CRASH_PREVENTION_AND_RECOVERY_GUIDE.md   # System recovery and environment stability guide
│
├── src_nodes/                     # Production ROS 2 Python nodes (Active perception & brain)
│   ├── active_vision_node.py      # Closed-loop 2-DOF camera gimbal visual servoing
│   ├── brain_node.py              # Central supervisory FSM (gesture command arbitration)
│   ├── camera_pub.py              # Throttled 20 Hz low-latency camera publisher
│   ├── face_recognition_node.py   # InsightFace ArcFace biometric authentication
│   ├── gesture_node.py            # Real-time 19-D geometric invariant feature extraction & MLP
│   ├── hand_features.py           # Shared 19-D geometric vector feature extractor
│   ├── person_detection_node.py   # YOLOv8-based spatial person localization
│   ├── safety_audio_node.py       # Acoustic safety horn (/beep) and state transition chimes
│   └── odom_imu_republisher.py    # Odometry & IMU message republisher
│
├── launch/                        # ROS 2 launch orchestrations
│   ├── cognition_autonomy.launch.py # Full autonomy stack bringup
│   ├── demo_system.launch.py        # Complete live demonstration orchestration
│   ├── master_robot.launch.py       # Master system launch on physical robot
│   ├── nav2.launch.py               # Nav2 navigation stack launcher
│   ├── slam_real.launch.py          # Real-time SLAM Toolbox bringup
│   └── twist_mux.yaml               # Safety velocity multiplexer priority rules
│
├── config/                        # Configuration parameters
│   └── nav2_params.yaml           # Nav2 planner, controller, and costmap configurations
│
├── ml_models/                     # Machine learning pipelines & trained weights
│   ├── datasets/                  # Gesture & trajectory training CSVs
│   ├── training/                  # Model training, feature engineering, and evaluation scripts
│   └── weights/                   # Production models (gesture_model_features.pkl, yolov8n.pt, ONNX)
│
├── scripts/                       # Operational, deployment, and diagnostic utilities
│   ├── menu.sh                    # Turnkey visual menu launcher (Workstation & Robot)
│   ├── master_demo_menu.py        # Interactive CLI operations dashboard
│   ├── sync_to_bot.sh             # One-click SSH/SCP deployment to physical Raspberry Pi 5
│   ├── bench_autonomy_monitor.py  # Real-time terminal telemetry monitor
│   ├── mission_manager.py         # Autonomous multi-waypoint patrol dispatcher
│   ├── web_map_visualizer.py      # Real-time browser-based map & robot trajectory visualizer
│   ├── slides/                    # Python-pptx individual slide generation scripts
│   └── diagnostics/               # Diagnostic shell scripts and sensor profilers
│
├── tests/                         # Master automated test and verification suite
│   ├── README.md                  # Test suite inventory and execution guide
│   ├── test_active_vision_logic.py # Gimbal control law and search state machine tests
│   ├── test_brain_logic.py        # Supervisory brain state transitions and command lock tests
│   ├── test_face_recognition.py   # ArcFace embedding extraction & matching tests
│   ├── test_gesture_mlp.py        # 19-D feature extraction and classification tests
│   ├── test_perception_throttling.py # Camera throttling and FPS stability tests
│   ├── test_safety_audio.py       # Acoustic horn generation and audio topic tests
│   ├── test_safety_reactive_reverse.py # LiDAR safety zone preemption (<0.36m) tests
│   └── verify_writeup.py          # Academic LaTeX formatting compliance linter
│
├── write_up/                      # Academic thesis and oral defense package
│   ├── main.tex                   # Master LaTeX document (GCTU handbook compliant)
│   ├── chapters/                  # Chapters 1 through 5 (TeX sources)
│   ├── figures/                   # High-resolution architectural schematics & empirical plots
│   ├── references.bib             # IEEE-formatted bibliography
│   ├── TODO_AND_ROADMAP.md        # Chapter-by-chapter completion checklist
│   └── Project Final Defense Slides_FINAL.pptx # Authoritative defense presentation deck
│
├── project_history/               # Canonical historical persistence (Never lose a decision)
│   ├── chat_sessions/             # Chronological transcripts of engineering sessions
│   ├── implementation_plans/      # Architectural designs and engineering plans
│   ├── walkthroughs/              # Verified test benchmarks and hardware bringup notes
│   ├── robot_audits/              # Physical robot filesystem audits and sensor dumps
│   └── technical_evolution/       # Error catalogs, historical retrospectives, and legacy nodes
│
├── maps/                          # Metric occupancy grid maps (YAML + PNG)
├── bags/                          # Empirical physical robot test datasets (rosbag2)
├── cognition_dashboard/           # Lightweight web-based status and control dashboard
└── archives/                      # Cold backups and legacy compressed releases
```

---

## 4. Quickstart Guide

### 4.1. Turnkey Operational Menu
To interact with the robot, run health diagnostics, or start autonomous missions:
```bash
./scripts/menu.sh
```
* Automatically detects whether the physical robot is reachable on the local network (`10.27.122.136` / `10.27.122.135`).
* If reachable, allows 1-click SSH connection straight into the live interactive robot dashboard.
* If offline, launches local workstation simulation and diagnostic mode.

### 4.2. Run Master Automated Verification Suite
Verify all core modules (Perception, Gimbal, MLP, Brain, Safety Audio, and LiDAR Preemption):
```bash
python3 scripts/run_all_local_verifications.py
```

### 4.3. One-Click Synchronization to Physical Robot
To synchronize verified nodes, models, and configs to the Raspberry Pi 5 (`yahboom_gesture` container):
```bash
./scripts/sync_to_bot.sh
```

### 4.4. Verify Thesis LaTeX Formatting
Validate that all body paragraphs satisfy GCTU formatting standards (minimum 3 sentences, zero indentation, no commercial brand names):
```bash
python3 tests/verify_writeup.py
```

---

## 5. Engineering Standards Compliance

The system is rigorously engineered to comply with international robotics and software standards:
* **ISO 15066:2016 (Collaborative Robots):** Strict power, force, and speed limiting; dynamic speed reduction in transient contact zones; immediate preemption and emergency reverse within 0.36 m obstacle proximity.
* **ISO 12100:2010 (Safety of Machinery):** Risk assessment and layered redundancy (hardware multiplexer `twist_mux` priority over software commands).
* **ROS REP-103 & REP-105:** Standard coordinate frames (`base_link`, `odom`, `map`, `laser`), SI units (m/s, rad/s), and right-hand orientation conventions.
* **OMG DDS v1.4 QoS:** Transient local durability for metric occupancy maps, Best-Effort QoS for high-rate LiDAR scans (`/scan`), and Reliable QoS for safety control topics.
