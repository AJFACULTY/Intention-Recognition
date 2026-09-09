#!/usr/bin/env python3
"""
system_preflight_diagnostics.py — Master System Pre-Flight & Operational Readiness Inspector
Cognition Robot Project — Yamaha / Yahboom Micro-ROS Pi 5 Platform

Forensic pre-flight audit tool that inspects:
1. Local Dev Machine (Jazzy, RAM, Swap, Python Venvs, Model Weights, Maps)
2. Network Connectivity to Physical Robot (10.147.122.135 / 10.147.122.136)
3. Physical Robot Containers (yahboom_base, yahboom_gesture) & Micro-ROS
4. Sensor Telemetry Pipelines (/scan, /odom_raw, /imu, /camera/image_raw/compressed)
5. Subsystem Readiness Matrix across 6 Operational Modes
6. Actionable Bringup Guidance & Exact Command-Line Instructions
"""

import os
import sys
import subprocess
import shutil
import time
import socket

# ANSI Colors for Terminal Output
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"

ROBOT_IPS = ["10.147.122.135", "10.147.122.136"]
ROBOT_USER = "pi"
WORKSPACE = "/home/j/ros2_cognition_ws"


def print_banner(title):
    print("\n" + C_BOLD + C_CYAN + "=" * 80 + C_RESET)
    print(f"  {C_BOLD}{C_WHITE}{title}{C_RESET}")
    print(C_BOLD + C_CYAN + "=" * 80 + C_RESET)


def check_file_exists(path, label):
    exists = os.path.exists(path)
    status = f"{C_GREEN}[READY]{C_RESET}" if exists else f"{C_RED}[MISSING]{C_RESET}"
    size_str = f"({os.path.getsize(path):,} bytes)" if exists else ""
    print(f"  {status:<18} {label:<35} : {path} {size_str}")
    return exists


def run_cmd(cmd, timeout=3.0):
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return res.returncode == 0, res.stdout.strip()
    except Exception as e:
        return False, str(e)


def ping_host(ip):
    ok, _ = run_cmd(f"ping -c 1 -W 1 {ip}")
    return ok


def ssh_robot(ip, cmd, timeout=4.0):
    ssh_cmd = f"ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o BatchMode=yes {ROBOT_USER}@{ip} '{cmd}'"
    return run_cmd(ssh_cmd, timeout=timeout)


def audit_local_dev_environment():
    print_banner("1. LOCAL DEV MACHINE AUDIT (j-Lenovo-V15-ADA)")
    
    # 1.1 Memory & OS
    ok, mem_out = run_cmd("free -m | grep -E 'Mem|Swap'")
    print(f"  {C_BOLD}Host Memory & Swap Allocation:{C_RESET}")
    for line in mem_out.splitlines():
        print(f"    {line}")

    # 1.2 Python Virtual Environments
    print(f"\n  {C_BOLD}Local Python Environments:{C_RESET}")
    check_file_exists("/home/j/ros2_venv/bin/python3", "ROS 2 Perception Venv")
    check_file_exists("/home/j/face_test_env/bin/python3", "InsightFace ArcFace Venv")

    # 1.3 Machine Learning Models & Weights
    print(f"\n  {C_BOLD}Embedded AI Models & Weights:{C_RESET}")
    m1 = check_file_exists(f"{WORKSPACE}/ml_models/weights/gesture_model.pkl", "Gesture MLP Weights (.pkl)")
    m2 = check_file_exists(f"{WORKSPACE}/ml_models/weights/path_predictor.pt", "Path Predictor LSTM (.pt)")
    m3 = check_file_exists("/home/j/.insightface/models/buffalo_sc/det_500m.onnx", "InsightFace Detector ONNX")
    m4 = check_file_exists("/home/j/.insightface/models/buffalo_sc/w600k_mbf.onnx", "InsightFace MobileFaceNet ONNX")
    
    # Face DB check
    db_candidates = [
        f"{WORKSPACE}/face_id_dev/face_data/known_embeddings.pkl",
        "/home/j/cognition_ws/face_id_dev/face_data/known_embeddings.pkl"
    ]
    face_db = next((p for p in db_candidates if os.path.exists(p)), None)
    if face_db:
        check_file_exists(face_db, "Enrolled Face DB (AJ, BigFisher)")
        m5 = True
    else:
        print(f"  {C_RED}[MISSING]{C_RESET}        Enrolled Face DB                   : known_embeddings.pkl not found")
        m5 = False

    # 1.4 Active Room Maps
    print(f"\n  {C_BOLD}SLAM Occupancy Grid Maps:{C_RESET}")
    map_yaml = check_file_exists(f"{WORKSPACE}/maps/room_map_20260812_0826.yaml", "Active Room Map Metadata (YAML)")
    map_png = check_file_exists(f"{WORKSPACE}/maps/room_map_20260812_0826.png", "Active Room Map Visualization")

    # 1.5 Source Nodes Integrity
    print(f"\n  {C_BOLD}ROS 2 Production Nodes:{C_RESET}")
    n1 = check_file_exists(f"{WORKSPACE}/src_nodes/active_vision_node.py", "2-DOF Active Vision Gimbal Node")
    n2 = check_file_exists(f"{WORKSPACE}/src_nodes/face_recognition_node.py", "Biometric Face Recognition Node")
    n3 = check_file_exists(f"{WORKSPACE}/src_nodes/person_detection_node.py", "Throttled YOLOv8 Person Detector")
    n4 = check_file_exists(f"{WORKSPACE}/src_nodes/gesture_node.py", "Throttled MediaPipe Gesture Node")
    n5 = check_file_exists(f"{WORKSPACE}/src_nodes/brain_node.py", "Cognition Brain Executive Node")
    n6 = check_file_exists(f"{WORKSPACE}/src_nodes/odom_imu_republisher.py", "Micro-ROS Clock Drift Restamper")

    return all([m1, m2, m3, m4, m5, map_yaml, map_png, n1, n2, n3, n4, n5, n6])


def audit_robot_network_and_hardware():
    print_banner("2. PHYSICAL ROBOT HARDWARE & NETWORK AUDIT")

    active_ip = None
    for ip in ROBOT_IPS:
        print(f"  Pinging robot network address {ip}...", end=" ", flush=True)
        if ping_host(ip):
            print(f"{C_GREEN}[ONLINE]{C_RESET}")
            active_ip = ip
            break
        else:
            print(f"{C_YELLOW}[NO RESPONSE]{C_RESET}")

    if not active_ip:
        print(f"\n  {C_BOLD}{C_RED}>> VERDICT: PHYSICAL ROBOT IS CURRENTLY OFFLINE / DISCONNECTED.{C_RESET}")
        print(f"     Reason: Battery was placed on balance charger (or power switch is OFF).")
        print(f"     Action: Turn on physical robot power switch and ensure Pi 5 joins Wi-Fi network.")
        return None, {}

    print(f"\n  {C_BOLD}{C_GREEN}>> CONNECTED TO ROBOT AT {active_ip}!{C_RESET}")
    robot_data = {"ip": active_ip}

    # 2.1 Check Docker Containers
    ok, containers = ssh_robot(active_ip, "docker ps --format '{{.Names}} ({{.Status}})'")
    print(f"\n  {C_BOLD}Docker Container Status:{C_RESET}")
    if ok:
        for c in containers.splitlines():
            print(f"    • {c}")
        robot_data["base_container"] = "yahboom_base" in containers
        robot_data["gesture_container"] = "yahboom_gesture" in containers
    else:
        print(f"    {C_RED}Failed to query docker containers via SSH.{C_RESET}")
        robot_data["base_container"] = False
        robot_data["gesture_container"] = False

    # 2.2 Micro-ROS STM32 Baseboard check
    ok, tty = ssh_robot(active_ip, "ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null")
    print(f"\n  {C_BOLD}Hardware Serial Ports:{C_RESET}")
    if ok and tty:
        for line in tty.splitlines():
            print(f"    {line}")
        robot_data["stm32_serial"] = "/dev/ttyACM0" in tty
    else:
        print(f"    {C_YELLOW}No serial ports found. Micro-ROS baseboard may be unpowered.{C_RESET}")
        robot_data["stm32_serial"] = False

    # 2.3 Check System Thermals & Voltage
    ok, temp = ssh_robot(active_ip, "vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp")
    if ok:
        print(f"    Pi 5 CPU Temperature: {temp}")

    # 2.4 Active ROS 2 Topics
    ok, topics = ssh_robot(active_ip, "docker exec yahboom_base bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list' 2>/dev/null")
    if ok and topics:
        topic_list = topics.splitlines()
        robot_data["has_scan"] = "/scan" in topic_list
        robot_data["has_odom"] = "/odom_raw" in topic_list
        robot_data["has_imu"] = "/imu" in topic_list
        robot_data["has_camera"] = "/camera/image_raw/compressed" in topic_list
        robot_data["has_servos"] = "/servo_s1" in topic_list and "/servo_s2" in topic_list
    else:
        robot_data["has_scan"] = False
        robot_data["has_odom"] = False
        robot_data["has_imu"] = False
        robot_data["has_camera"] = False
        robot_data["has_servos"] = False

    return active_ip, robot_data


def evaluate_operational_readiness(local_ok, robot_ip, robot_data):
    print_banner("3. SYSTEM READINESS MATRIX ACROSS OPERATIONAL MODES")

    modes = [
        {
            "mode": "MODE 1: Wireless Joypad Teleoperation",
            "condition": robot_ip and robot_data.get("base_container") and robot_data.get("stm32_serial"),
            "description": "Direct manual control of differential chassis motors via wireless handheld remote.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'docker exec -it yahboom_base ros2 run yahboomcar_joy joy_teleop'"
        },
        {
            "mode": "MODE 2: Real-World LiDAR SLAM Room Mapping",
            "condition": robot_ip and robot_data.get("has_scan") and robot_data.get("has_odom"),
            "description": "Real-time occupancy grid mapping via MS200 LiDAR & EKF yaw restamped odometry.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'bash /home/pi/1_start_mapping.sh'"
        },
        {
            "mode": "MODE 3: Nav2 Autonomous Navigation & Obstacle Avoidance",
            "condition": robot_ip and robot_data.get("has_scan") and local_ok,
            "description": "Full AMCL particle filter localization, global Navfn planning & Regulated Pure Pursuit.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'bash /home/pi/7_fix_and_deploy_nav2.sh'"
        },
        {
            "mode": "MODE 4: Active Vision 2-DOF Gimbal FOV Tracking",
            "condition": robot_ip and robot_data.get("has_camera") and robot_data.get("has_servos"),
            "description": "Smooth decoupled PID visual servoing centering human face/body dynamically in FOV.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'python3 /root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py'"
        },
        {
            "mode": "MODE 5: Biometric Face ID & Hand Gesture Cognition",
            "condition": robot_ip and robot_data.get("has_camera") and local_ok,
            "description": "InsightFace ArcFace 512-d operator authorization + MediaPipe 6-class gesture classification.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'bash /home/pi/start_bench_pipeline.sh'"
        },
        {
            "mode": "MODE 6: Full Multi-Modal Integrated Autonomy",
            "condition": robot_ip and robot_data.get("has_scan") and robot_data.get("has_camera") and robot_data.get("has_servos"),
            "description": "End-to-end mission: Face authorization -> Gesture driving -> Social distance hold -> Nav2 avoidance.",
            "bringup_cmd": f"ssh {ROBOT_USER}@{robot_ip or '10.147.122.135'} 'bash /home/pi/start_full_autonomy.sh'"
        },
    ]

    for m in modes:
        status = f"{C_GREEN}[READY]{C_RESET}" if m["condition"] else f"{C_YELLOW}[NOT READY (STANDBY)]{C_RESET}" if not robot_ip else f"{C_RED}[BLOCKED]{C_RESET}"
        print(f"\n  {status} {C_BOLD}{m['mode']}{C_RESET}")
        print(f"     Capability: {m['description']}")
        print(f"     Bringup CLI: {C_CYAN}{m['bringup_cmd']}{C_RESET}")

    print_banner("4. OPERATOR ACTIONABLE GUIDANCE & NEXT STEPS")
    if not robot_ip:
        print(f"  {C_BOLD}1. POWER SEQUENCE:{C_RESET}")
        print(f"     • Disconnect robot from 12.6V balance charger.")
        print(f"     • Flip physical toggle power switch on robot base.")
        print(f"     • Wait 30 seconds for Raspberry Pi 5 to boot and establish Wi-Fi connection.")
        print(f"     • Re-run this diagnostics tool: {C_CYAN}python3 scripts/system_preflight_diagnostics.py{C_RESET}")
    else:
        print(f"  {C_BOLD}1. DEPLOY UPDATED PERCEPTION NODES:{C_RESET}")
        print(f"     • Sync the smoothed active vision & person detection nodes to the robot:")
        print(f"       {C_CYAN}rsync -avz src_nodes/*.py {ROBOT_USER}@{robot_ip}:/root/cognition_ws/src/cognition_perception/cognition_perception/{C_RESET}")
        print(f"\n  {C_BOLD}2. BENCH QUALIFICATION:{C_RESET}")
        print(f"     • Keep robot on workbench and launch bench demo HUD:")
        print(f"       {C_CYAN}ssh -t {ROBOT_USER}@{robot_ip} 'bash /home/pi/start_bench_pipeline.sh'{C_RESET}")
        print(f"     • Verify smooth bidirectional tracking (both robot-left and robot-right).")
        print(f"\n  {C_BOLD}3. FLOOR AUTONOMY RUN:{C_RESET}")
        print(f"     • Place robot on floor tile grid and test autonomous human following.")

    print(C_BOLD + C_CYAN + "=" * 80 + C_RESET + "\n")


def main():
    local_ok = audit_local_dev_environment()
    robot_ip, robot_data = audit_robot_network_and_hardware()
    evaluate_operational_readiness(local_ok, robot_ip, robot_data)


if __name__ == "__main__":
    main()
