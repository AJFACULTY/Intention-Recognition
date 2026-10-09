# Automated Verification & Test Suite

This directory contains standalone unit, integration, and compliance validation suites for the Autonomous Mobile Robot Cognition System.

---

## Test Inventory

| Test Script | Target Subsystem | Execution Environment | Validation Criteria |
| :--- | :--- | :--- | :--- |
| `test_perception_throttling.py` | Camera & YOLOv8/MediaPipe | `ros2_venv` | 20 Hz frame throttle; deadband & linear velocity extrapolation. |
| `test_active_vision_logic.py` | 2-DOF Pan/Tilt Camera Gimbal | `ros2_venv` | PI control law, pan/tilt slew bounds, angular deadbands, FSM search sweep. |
| `test_face_recognition.py` | Biometric ArcFace (InsightFace) | `face_test_env` | Feature embedding extraction, cosine similarity matching, database lookup. |
| `test_brain_logic.py` | Supervisory Brain Node | `ros2_venv` | Twist multiplexer priority switching, FSM command locks, gesture routing. |
| `test_gesture_mlp.py` | 19-D Geometric Feature MLP | `ros2_venv` | Invariant angle/distance feature pipeline, label encoding, classification accuracy. |
| `test_safety_audio.py` | Industrial Acoustic Safety | `ros2_venv` | Wave generation, /beep topic subscription, distinct obstacle & mode chimes. |
| `test_safety_reactive_reverse.py` | LiDAR Emergency Halt & Reverse | Python 3 (ROS 2) | ISO 15066 safety zone preemption (<0.36m trigger, reactive backward escape). |

---

## Execution Instructions

Run all suites sequentially using the master automated runner:
```bash
python3 scripts/run_all_local_verifications.py
```

Run an individual test suite:
```bash
python3 tests/test_brain_logic.py
```
