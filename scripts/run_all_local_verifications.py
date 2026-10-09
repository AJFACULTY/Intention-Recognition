#!/usr/bin/env python3
"""
run_all_local_verifications.py — Master Automated Verification Runner
Cognition Robot Project — Full Perception & Autonomy Stack

Runs all local unit & integration test suites:
1. Perception Throttling & Velocity Extrapolation (YOLOv8 + MediaPipe)
2. Active Vision Gimbal FOV Tracking & Servoing (PI, Slew, Deadband, FSM)
3. Biometric ArcFace Face Recognition (InsightFace buffalo_sc, DB AJ & BigFisher)
4. Brain Decision Node (twist_mux /cmd_vel_gesture routing, Gestures, Face ID gate)
"""

import os
import subprocess
from pathlib import Path
import os
import subprocess
import sys
import time

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = WORKSPACE_DIR / "tests"

# Detect Python interpreter with fallback to current sys.executable
PYTHON_DEFAULT = sys.executable
ros2_venv_path = os.path.expanduser("~/ros2_venv/bin/python3")
face_env_path = os.path.expanduser("~/face_test_env/bin/python3")

PYTHON_ROS = ros2_venv_path if os.path.exists(ros2_venv_path) else PYTHON_DEFAULT
PYTHON_FACE = face_env_path if os.path.exists(face_env_path) else PYTHON_ROS

SUITES = [
    {
        "name": "Perception Throttling & Extrapolation",
        "script": str(TESTS_DIR / "test_perception_throttling.py"),
        "python": PYTHON_ROS,
    },
    {
        "name": "Active Vision Gimbal Control Law & FSM",
        "script": str(TESTS_DIR / "test_active_vision_logic.py"),
        "python": PYTHON_ROS,
    },
    {
        "name": "ArcFace Biometric Recognition & DB",
        "script": str(TESTS_DIR / "test_face_recognition.py"),
        "python": PYTHON_FACE,
    },
    {
        "name": "Cognition Brain Decision & twist_mux Routing",
        "script": str(TESTS_DIR / "test_brain_logic.py"),
        "python": PYTHON_ROS,
    },
    {
        "name": "19-Feature MLP Gesture Recognition & Dataset Integrity",
        "script": str(TESTS_DIR / "test_gesture_mlp.py"),
        "python": PYTHON_ROS,
    },
    {
        "name": "Industrial Acoustic Safety Audio Node (/beep & Chimes)",
        "script": str(TESTS_DIR / "test_safety_audio.py"),
        "python": PYTHON_ROS,
    },
    {
        "name": "LiDAR Frontal Safety Preemption & Active Reverse (<0.36m)",
        "script": str(TESTS_DIR / "test_safety_reactive_reverse.py"),
        "python": PYTHON_ROS,
    },
]


def main():
    print("=" * 80)
    print("  COGNITION ROBOTICS — MASTER AUTOMATED VERIFICATION SUITE")
    print("=" * 80)

    results = []
    total_start = time.time()

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{WORKSPACE_DIR}:{env.get('PYTHONPATH', '')}"

    for suite in SUITES:
        print(f"\n[RUNNING] {suite['name']}...")
        start_t = time.time()

        cmd = [suite["python"], suite["script"]]
        proc = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        duration = time.time() - start_t
        passed = (proc.returncode == 0)

        results.append({
            "name": suite["name"],
            "passed": passed,
            "duration": duration,
            "output": proc.stdout
        })

        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] in {duration:.2f}s")
        if not passed:
            print("--- Error Output ---")
            print(proc.stdout)
            print("--------------------")

    total_duration = time.time() - total_start

    print("\n" + "=" * 80)
    print("  VERIFICATION SUMMARY REPORT")
    print("=" * 80)
    all_ok = True
    for res in results:
        status_icon = "✓ PASS" if res["passed"] else "✗ FAIL"
        if not res["passed"]:
            all_ok = False
        print(f"  {status_icon:<8} | {res['duration']:>5.2f}s | {res['name']}")

    print("-" * 80)
    print(f"Total Execution Time: {total_duration:.2f}s")
    if all_ok:
        print("RESULT: ALL 4 VERIFICATION SUITES PASSED (100% SUCCESS)")
        print("Pipeline is verified and ready for physical robot connection.")
    else:
        print("RESULT: ONE OR MORE SUITES FAILED — Review logs above.")
    print("=" * 80)

    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
