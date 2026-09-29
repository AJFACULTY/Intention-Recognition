# Autonomous Mobile Robot Cognition System
### Human Intention Recognition Using Motion and Hand Gesture

[![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E.svg)](https://docs.ros.org/en/humble/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205%20(8GB)-C51A4A.svg)](https://www.raspberrypi.com/)
[![Safety](https://img.shields.io/badge/Compliance-ISO%2015066%3A2016-0057B8.svg)](https://www.iso.org/standard/69263.html)
[![Accuracy](https://img.shields.io/badge/Gesture%20Accuracy-99.38%25-brightgreen.svg)]()
[![Latency](https://img.shields.io/badge/End--to--End%20Latency-132%20ms-orange.svg)]()

---

## Overview

This repository contains the complete source code, trained models, configuration files, empirical test data, and academic write-up for an undergraduate engineering thesis project at the **Ghana Communication Technology University (GCTU)**.

The system implements a **real-time human intention recognition pipeline** on a physical mobile robot, enabling a person to control the robot entirely through hand gestures — with no physical contact, wearable devices, or cloud connectivity required.

> **Authors:** Eleana & Joel  
> **Supervisor:** Mr. Michael Xenya  
> **Institution:** GCTU, Faculty of Engineering — Department of Computer Engineering

---

## Key Capabilities

| Feature | Detail |
|---|---|
| 🤚 **Gesture Recognition** | 6 gestures (`STOP`, `GO`, `FOLLOW`, `LEFT`, `RIGHT`, `BACK`) using a 19-D geometric MLP |
| 🎯 **Position-Invariant** | Scale-invariant features work at 1.0 m, 1.75 m, and 2.5 m operator distances |
| 👁️ **Active Vision** | 2-DOF pan/tilt camera gimbal with closed-loop visual servoing |
| 🧠 **Supervisory Brain FSM** | 5-frame rolling consensus + 3.0 s command lock + emergency LiDAR preemption |
| 🗺️ **Autonomous Navigation** | Nav2 stack with SLAM Toolbox; multi-waypoint room patrol (15.89 m, 100% success) |
| 🔒 **Safety Compliance** | ISO 15066:2016 — reactive obstacle stop within 0.36 m at all times |
| ⚡ **Edge-Only Inference** | Runs fully on Raspberry Pi 5 (8 GB) — no GPU, no cloud |

---

## Hardware Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Physical Robot Platform                       │
├─────────────────────────────────────────────────────────────────┤
│  Raspberry Pi 5 (8 GB RAM) — Ubuntu 22.04 + ROS 2 Humble        │
│  ├── MediaPipe Hand Landmark Extractor (21 3D landmarks)         │
│  ├── 19-D Geometric Invariant MLP Gesture Classifier (99.38%)   │
│  ├── Supervisory Brain FSM Node (command arbitration)            │
│  ├── Active Vision 2-DOF Gimbal Servoing Node                    │
│  ├── twist_mux Velocity Priority Arbitrator                      │
│  └── Nav2 Navigation Stack + SLAM Toolbox                        │
├────────────────────┬────────────────────────────────────────────┤
│  UART /dev/ttyAMA0 │  USB Bus                                    │
▼                    ▼                                             ▼
Yahboom ESP32-S3    MS200 2D ToF LiDAR          2-DOF Gimbal + USB Cam
(Differential Drive) (12.5 Hz, 12 m range)     (640×480 @ 20 FPS)
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
Intention-Recognition/
│
├── src_nodes/                  # Core ROS 2 perception and brain nodes
│   ├── gesture_node.py         # 19-D MLP gesture classifier (primary)
│   ├── hand_features.py        # Geometric invariant feature extractor
│   ├── brain_node.py           # Supervisory FSM — command arbitration
│   ├── active_vision_node.py   # 2-DOF gimbal closed-loop visual servoing
│   ├── person_detection_node.py# YOLOv8 + LSTM trajectory prediction
│   ├── camera_pub.py           # 20 Hz throttled camera publisher
│   ├── face_recognition_node.py# ArcFace biometric authentication
│   ├── safety_audio_node.py    # Acoustic safety horn node
│   └── odom_imu_republisher.py # Odometry republisher
│
├── launch/                     # ROS 2 launch orchestrations
│   ├── master_robot.launch.py  # Full system bringup (recommended)
│   ├── cognition_autonomy.launch.py
│   ├── demo_system.launch.py
│   ├── nav2.launch.py
│   ├── slam_real.launch.py
│   ├── follow_to_map.launch.py
│   └── twist_mux.yaml
│
├── config/
│   └── nav2_params.yaml        # Nav2 planner, controller, and costmap config
│
├── ml_models/
│   ├── datasets/               # Training CSVs (gesture + trajectory)
│   ├── training/               # Training and evaluation scripts
│   └── weights/                # Production ONNX + pickle model files
│       ├── gesture_model_features.pkl   # Primary 19-D MLP
│       ├── gesture_model.onnx           # Portable ONNX format
│       ├── scaler_features.pkl
│       ├── label_encoder_features.pkl
│       ├── path_predictor.onnx          # LSTM trajectory predictor
│       ├── path_predictor.onnx.data
│       └── path_predictor_config.pkl
│
├── maps/                       # SLAM occupancy grid maps (YAML + PNG)
│
├── scripts/                    # Operational and deployment scripts
│   ├── sync_to_bot.sh          # One-click deploy to robot (SSH + Docker)
│   ├── start_bench_pipeline.sh # Launch full autonomy stack on robot
│   ├── menu.sh                 # Interactive launcher menu
│   ├── master_demo_menu.py     # CLI operations dashboard
│   ├── bench_autonomy_monitor.py # Real-time terminal HUD
│   ├── mission_manager.py      # Multi-waypoint patrol dispatcher
│   ├── navigate_waypoints.py   # Nav2 waypoint navigation client
│   ├── web_map_visualizer.py   # Browser-based live map viewer
│   ├── run_nav2_patrol.sh      # Autonomous patrol runner
│   ├── experiment_logger.py    # Live ROS 2 trial data recorder
│   ├── analyze_trial_data.py   # Statistical analysis of trial CSVs
│   ├── plot_multi_waypoint_trajectory.py
│   ├── run_all_local_verifications.py
│   ├── system_preflight_diagnostics.py
│   └── diagnostics/            # Sensor and SLAM health check scripts
│
├── tests/                      # Automated unit and integration test suite
│   ├── test_gesture_mlp.py
│   ├── test_brain_logic.py
│   ├── test_active_vision_logic.py
│   ├── test_perception_throttling.py
│   ├── test_safety_audio.py
│   ├── test_safety_reactive_reverse.py
│   ├── test_face_recognition.py
│   └── verify_writeup.py
│
├── write_up/                   # Undergraduate thesis (LaTeX source)
│   ├── main.tex                # Master document
│   ├── chapters/               # ch1 – ch5 (TeX source files)
│   ├── figures/                # All publication figures (PNG/JPG)
│   └── references.bib          # IEEE-formatted bibliography (30 works)
│
├── publications/               # IEEE dual-track manuscripts
│   ├── conference_paper/       # 6-page IEEEtran conference format
│   └── journal_paper/          # 10-page IEEEtran journal format
│
├── experiment_logs/
│   └── trial_data.csv          # Empirical trial data (180 physical trials)
│
├── docs/                       # Technical reference documents
│   ├── ROBOT_OPERATIONS_MANUAL_AND_USER_GUIDE.md
│   ├── ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md
│   └── *.png                   # Empirical navigation trajectory plots
│
├── assets/                     # Demo media
├── cognition_dashboard/        # Web-based robot status dashboard
├── OPERATOR_COMMAND_MANUAL.md  # Quick-reference command cheat sheet
└── .gitignore
```

---

## Quickstart

### 1. Deploy to Physical Robot
Synchronize all nodes, models, and configs into the running Docker container on the Raspberry Pi 5:
```bash
./scripts/sync_to_bot.sh
```

### 2. Launch Full Autonomy Stack (on robot)
```bash
bash ~/start_bench_pipeline.sh
```

### 3. Run Automated Test Suite (on workstation)
```bash
python3 scripts/run_all_local_verifications.py
```
Expected output: **5/5 PASS** — Perception, Gimbal, MLP, Brain, Safety Audio.

### 4. Multi-Waypoint Autonomous Patrol
```bash
bash scripts/run_nav2_patrol.sh
python3 scripts/navigate_waypoints.py
```

### 5. Compile Thesis (requires [Tectonic](https://tectonic-typesetting.github.io/))
```bash
cd write_up && tectonic main.tex
```

---

## Results Summary

| Metric | Result |
|---|---|
| MLP Test Accuracy (6-class) | **99.38%** |
| Physical Trial Accuracy (180 trials) | **96.67%** |
| End-to-End Pipeline Latency | **132 ms** (Camera → Motor) |
| Multi-Waypoint Patrol Distance | **15.89 m**, 100% legs completed |
| Cross-Track Error (MAE) | **15.5 cm** |
| Emergency Stop Distance | **< 0.36 m** (ISO 15066 compliant) |
| CPU Utilization (4 cores) | **311%** — no thermal throttling |

---

## Engineering Standards Compliance

| Standard | Application |
|---|---|
| **ISO 15066:2016** | Collaborative robot safety — reactive stop within 0.36 m |
| **ISO 12100:2010** | Risk mitigation — hardware `twist_mux` priority over software |
| **ROS REP-103** | SI units (m/s, rad/s), right-hand coordinate frames |
| **ROS REP-105** | Standard TF frames: `base_link`, `odom`, `map`, `laser` |
| **OMG DDS v1.4** | QoS profiles — Reliable for safety topics, Best-Effort for `/scan` |
