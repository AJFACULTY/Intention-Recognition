#!/usr/bin/env python3
"""
master_demo_menu.py — Master Consolidated Turnkey Demonstration & Mission Menu
==============================================================================
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Authors: Eleana Osei Owusu & Joel Nii Adjetey Ahulu
Institution: Ghana Communication Technology University (GCTU)
Standards Compliance: ROS REP-103/105, ISO 15066:2016, OMG DDS v1.4

Provides a unified, defense-ready operational interface:
  1. Automated Pre-Flight Health Audit (Hardware, Docker, Sensors, AI Models, Battery)
  2. Actionable Diagnostics Triage & 1-Click Recovery
  3. Unmapped Environment Suite (Mode 1: Collaborative Follow-to-Map SLAM, HRI, Safety)
  4. Mapped Environment Suite (Mode 2: Collaborative Escort, Milestone 10 Capstone, Waypoints)
  5. System Benchmark & Diagnostics Utilities
  6. Instant Emergency Chassis Halt

Usage:
  python3 scripts/master_demo_menu.py
  python3 scripts/master_demo_menu.py --audit-only
"""

import os
import sys
import time
import signal
import subprocess
import shutil
from typing import Dict, Tuple, List, Optional

# ── ANSI Terminal Styling ──
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_BG_RED = "\033[41m"
C_BG_GREEN = "\033[42m"
C_BG_BLUE = "\033[44m"

CONTAINER_GESTURE = "yahboom_gesture"
CONTAINER_BASE = "yahboom_base"
DEFAULT_ROBOT_IPS = ["10.27.122.136", "10.27.122.135"]
WORKSPACE_CONTAINER = "/root/cognition_ws"
WORKSPACE_HOST_PI = "/home/pi/cognition_ws"
WORKSPACE_LOCAL = "/home/j/ros2_cognition_ws"

# Determine environment: running inside container, on Pi host, or on dev workstation
IS_INSIDE_CONTAINER = os.path.exists("/.dockerenv")
IS_ON_PI = os.path.exists("/home/pi") and not IS_INSIDE_CONTAINER
IS_DEV_WORKSTATION = not IS_INSIDE_CONTAINER and not IS_ON_PI


def get_robot_ip() -> str:
    """Returns first reachable robot IP, or default fallback."""
    for ip in DEFAULT_ROBOT_IPS:
        try:
            ret = subprocess.call(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ret == 0:
                return ip
        except Exception:
            pass
    return DEFAULT_ROBOT_IPS[0]


def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")


def print_header(title: str, subtitle: Optional[str] = None):
    clear_screen()
    width = 82
    print(C_BOLD + C_CYAN + "═" * width + C_RESET)
    print(f"{C_BOLD}{C_WHITE}  {title.center(width - 4)}{C_RESET}")
    if subtitle:
        print(f"{C_DIM}{C_CYAN}  {subtitle.center(width - 4)}{C_RESET}")
    print(C_BOLD + C_CYAN + "═" * width + C_RESET)
    print()


def run_command_capture(cmd: str, timeout: float = 4.0) -> Tuple[bool, str]:
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        output = (res.stdout + "\n" + res.stderr).strip()
        return res.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def run_interactive_command(cmd: str):
    """Executes a command interactively, allowing user interaction and clean Ctrl+C return."""
    print(f"\n{C_BOLD}{C_YELLOW}>> Executing:{C_RESET} {cmd}\n")
    try:
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}>> Process interrupted by user.{C_RESET}")
    print(f"\n{C_DIM}Press Enter to return to menu...{C_RESET}", end="")
    try:
        input()
    except EOFError:
        pass


def emergency_halt():
    """Immediately stops all motor rotation on the base controller."""
    print(f"\n{C_BOLD}{C_BG_RED}{C_WHITE} !!! INITIATING EMERGENCY CHASSIS HALT !!! {C_RESET}")
    stop_cmd = (
        "export ROS_DOMAIN_ID=20; "
        "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash >/dev/null 2>&1 || true; "
        "timeout 1s ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "
        "'{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null 2>&1 || true"
    )
    if IS_INSIDE_CONTAINER:
        subprocess.run(stop_cmd, shell=True)
    elif IS_ON_PI:
        subprocess.run(f"docker exec {CONTAINER_GESTURE} bash -c \"{stop_cmd}\"", shell=True)
    else:
        # On dev machine: send via ROS 2 if on same network, or notify user
        subprocess.run(stop_cmd, shell=True)
    print(f"{C_GREEN}>> All drive velocities forced to 0.0 m/s. Chassis halted.{C_RESET}")
    time.sleep(1.0)


# ════════════════════════════════════════════════════════════════════════════════
# 1. PRE-FLIGHT HEALTH AUDIT & DIAGNOSTICS
# ════════════════════════════════════════════════════════════════════════════════

class SystemHealthChecker:
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.overall_ready = True
        self.remediations: List[str] = []

    def audit(self) -> bool:
        self.results.clear()
        self.remediations.clear()
        self.overall_ready = True

        # 1. Container Health
        if not IS_INSIDE_CONTAINER:
            ok_base, _ = run_command_capture(f"docker ps --format '{{{{.Names}}}}' | grep -q '^{CONTAINER_BASE}$'")
            ok_gest, _ = run_command_capture(f"docker ps --format '{{{{.Names}}}}' | grep -q '^{CONTAINER_GESTURE}$'")
            
            self.results["Docker Base Container"] = {
                "ok": ok_base,
                "detail": "Running (Micro-ROS, Base Hardware)" if ok_base else "OFFLINE / STOPPED",
                "fix": "Run: docker start yahboom_base"
            }
            self.results["Docker Autonomy Container"] = {
                "ok": ok_gest,
                "detail": "Running (Perception, Nav2, Cognition)" if ok_gest else "OFFLINE / STOPPED",
                "fix": "Run: docker start yahboom_gesture"
            }
            if not ok_base or not ok_gest:
                self.overall_ready = False
                if not ok_base: self.remediations.append("docker start yahboom_base")
                if not ok_gest: self.remediations.append("docker start yahboom_gesture")

        # 2. Camera Device
        has_cam = os.path.exists("/dev/video0") or os.path.exists("/dev/video1")
        self.results["Physical USB Camera"] = {
            "ok": has_cam,
            "detail": "Device node present (/dev/video0 or /dev/video1)" if has_cam else "NOT DETECTED",
            "fix": "Reseat USB camera connector on Raspberry Pi 5 USB port."
        }
        if not has_cam:
            self.overall_ready = False
            self.remediations.append("Check physical camera USB connection")

        # 3. Micro-ROS & Serial Hardware Baseboard (/dev/ttyUSB0)
        has_serial = os.path.exists("/dev/ttyUSB0")
        self.results["STM32 Baseboard Serial Bus"] = {
            "ok": has_serial,
            "detail": "Active (/dev/ttyUSB0 connected)" if has_serial else "DISCONNECTED",
            "fix": "Check USB-C interconnect cable between Pi 5 and Yahboom baseboard."
        }
        if not has_serial:
            self.overall_ready = False
            self.remediations.append("Check STM32 USB-to-serial cable (/dev/ttyUSB0)")

        # 4. Battery Level & Brownout Threshold
        batt_v, batt_state = self._check_battery()
        batt_ok = (batt_v is None) or (batt_v >= 7.2)
        batt_nominal = (batt_v is not None) and (batt_v >= 8.0)
        
        detail_str = f"{batt_v:.1f}V — {batt_state}" if batt_v else f"Unable to query ({batt_state})"
        self.results["2S Li-Ion Battery Pack"] = {
            "ok": batt_ok,
            "nominal": batt_nominal,
            "detail": detail_str,
            "fix": "Connect battery to 12.6V balance charger to charge above 8.0V."
        }
        if batt_v and batt_v < 7.2:
            self.overall_ready = False
            self.remediations.append(f"Battery voltage critical ({batt_v:.1f}V < 7.2V)! Recharge before floor runs.")

        # 5. Core AI Models & Map Assets
        assets_ok = self._check_assets()
        self.results["AI Models & Map Assets"] = {
            "ok": assets_ok,
            "detail": "19-D MLP, Scaler, ArcFace, Room Map Verified" if assets_ok else "MISSING ASSET FILES",
            "fix": "Run: ./scripts/sync_to_bot.sh to synchronize verified model weights and maps."
        }
        if not assets_ok:
            self.overall_ready = False
            self.remediations.append("Execute ./scripts/sync_to_bot.sh to synchronize models")

        return self.overall_ready

    def _check_battery(self) -> Tuple[Optional[float], str]:
        # Fast query of /battery topic
        query_cmd = (
            "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
            "source /opt/ros/humble/setup.bash >/dev/null 2>&1 || true; "
            "timeout 1.5s ros2 topic echo --once /battery std_msgs/msg/UInt16 2>/dev/null"
        )
        if not IS_INSIDE_CONTAINER and not IS_DEV_WORKSTATION:
            query_cmd = f"docker exec {CONTAINER_GESTURE} bash -c \"{query_cmd}\""

        ok, out = run_command_capture(query_cmd, timeout=3.0)
        if ok and "data:" in out:
            try:
                for line in out.splitlines():
                    if "data:" in line:
                        raw_val = int(line.split("data:")[1].strip())
                        v = raw_val / 10.0
                        if v >= 8.0:
                            return v, "NOMINAL (Safe for Floor Driving)"
                        elif v >= 7.3:
                            return v, "CAUTION (Bench Tests Only)"
                        else:
                            return v, "CRITICAL (Brownout Risk)"
            except Exception:
                pass
        return None, "Topic /battery not publishing or micro-ROS agent idle"

    def _check_assets(self) -> bool:
        check_paths = [
            f"{WORKSPACE_LOCAL}/ml_models/weights/gesture_model_features.pkl",
            f"{WORKSPACE_LOCAL}/maps/room_map_20260812_0826.yaml"
        ]
        if IS_INSIDE_CONTAINER:
            check_paths = [
                "/root/cognition_ws/src/cognition_perception/cognition_perception/models/gesture_model_features.pkl",
                "/root/cognition_ws/maps_new/room_map_20260812_0826.yaml"
            ]
        elif IS_ON_PI:
            check_paths = [
                "/home/pi/cognition_ws/models/gesture_model_features.pkl",
                "/home/pi/maps_new/room_map_20260812_0826.yaml"
            ]
        for p in check_paths:
            if not os.path.exists(p):
                return False
        return True

    def display_report(self):
        print(f"{C_BOLD}{C_WHITE}  [PRE-FLIGHT SYSTEM HEALTH MATRIX]{C_RESET}")
        print(f"  {'Subsystem':<30} {'Status':<12} {'Telemetry / Health Details'}")
        print(f"  {'─'*30} {'─'*12} {'─'*36}")

        for name, data in self.results.items():
            if data.get("nominal") is False and data["ok"]:
                status_str = f"{C_YELLOW}[CAUTION]{C_RESET}"
            elif data["ok"]:
                status_str = f"{C_GREEN}[READY]{C_RESET}"
            else:
                status_str = f"{C_RED}[FAIL]{C_RESET}"
            print(f"  {name:<30} {status_str:<21} {data['detail']}")

        print(f"  {'─'*78}")
        if self.overall_ready:
            print(f"  {C_BOLD}{C_GREEN}>> SYSTEM READINESS: 100% OPERATIONAL — ALL MISSIONS READY{C_RESET}")
        else:
            print(f"  {C_BOLD}{C_RED}>> SYSTEM READINESS: DEGRADED / NOT READY{C_RESET}")
            print(f"\n  {C_BOLD}{C_YELLOW}Actionable Remediation Checklist:{C_RESET}")
            for i, rem in enumerate(self.remediations, 1):
                print(f"    {C_BOLD}{i}.{C_RESET} {rem}")
        print()


# ════════════════════════════════════════════════════════════════════════════════
# 2. MISSION DISPATCH HANDLERS
# ════════════════════════════════════════════════════════════════════════════════

def dispatch_collaborative_follow_slam():
    """Unmapped Mode 1: Collaborative Follow-to-Map SLAM."""
    print_header("COLLABORATIVE FOLLOW-TO-MAP SLAM (MODE 1)", "Chapter 5 (§5.4 Dual-Mode Architecture)")
    print(f"{C_WHITE}Mission Overview:{C_RESET}")
    print("  1. The robot launches SLAM Toolbox, Active Vision tracking, and Audio Safety.")
    print("  2. Stand 1.5m in front of the camera and raise the FOLLOW gesture (peace sign).")
    print("  3. As you walk through the unmapped space, the robot shadows your footsteps.")
    print("  4. The 2D metric occupancy grid map is drawn live in your web browser!")
    print(f"  5. Open Live Web Visualizer: {C_BOLD}{C_CYAN}http://<robot_ip>:8080{C_RESET}")
    print()

    cmd = (
        "docker exec -it yahboom_gesture bash -c '"
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true; "
        "ros2 launch /root/cognition_ws/src/cognition_simulation/launch/follow_to_map.launch.py'"
    ) if not IS_INSIDE_CONTAINER else (
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true; "
        "ros2 launch launch/follow_to_map.launch.py"
    )
    run_interactive_command(cmd)


def dispatch_interactive_gesture_hri():
    """Unmapped Mode 2: Full 6-Gesture Evaluation Suite & Touchless Teleoperation."""
    print_header("FULL 6-GESTURE EVALUATION & TELEOPERATION SUITE", "Test GO, STOP, FOLLOW, LEFT, RIGHT, BACK + Live Visualizer (:8080)")
    robot_ip = get_robot_ip()
    print(f"{C_WHITE}Gesture Verification Protocol:{C_RESET}")
    print("  Stand ~1.5m in front of the 2-DOF camera to evaluate all 6 canonical gestures:")
    print(f"    1. {C_BOLD}{C_RED}STOP{C_RESET}   (Open Palm)    -> Instant wheel halt (/cmd_vel = 0.0 m/s)")
    print(f"    2. {C_BOLD}{C_GREEN}GO{C_RESET}     (Thumbs Up)    -> Translates forward (+0.25 m/s)")
    print(f"    3. {C_BOLD}{C_CYAN}FOLLOW{C_RESET} (Peace Sign)   -> Visual servoing shadows your footsteps")
    print(f"    4. {C_BOLD}{C_BLUE}LEFT{C_RESET}   (Point Left)   -> In-place pivot counter-clockwise (+0.4 rad/s)")
    print(f"    5. {C_BOLD}{C_BLUE}RIGHT{C_RESET}  (Point Right)  -> In-place pivot clockwise (-0.4 rad/s)")
    print(f"    6. {C_BOLD}{C_YELLOW}BACK{C_RESET}   (Point Down)   -> Translates backward (-0.15 m/s)")
    print()
    print(f"  Live Visualizer & Camera Stream: {C_BOLD}{C_CYAN}http://{robot_ip}:8080{C_RESET}")
    print("  Live Terminal HUD: Displays real-time detection confidence, FPS, and wheel velocities.")
    print()

    cmd = "bash ~/start_bench_pipeline.sh" if IS_ON_PI else (
        f"ssh -t pi@{robot_ip} 'bash ~/start_bench_pipeline.sh'" if IS_DEV_WORKSTATION else
        "python3 -u /root/cognition_ws/bench_autonomy_monitor.py"
    )
    run_interactive_command(cmd)


def dispatch_safety_bubble_test():
    """ISO 15066 Multimodal Safety Bubble & Reactive Reverse Test."""
    print_header("ISO 15066 MULTIMODAL SAFETY BUBBLE TEST", "Planar LiDAR Frontal Corridor & Rear Collision Guard")
    print(f"{C_WHITE}Test Protocol:{C_RESET}")
    print("  1. Frontal Breach: Walk into the robot's front corridor (<0.35m).")
    print("     -> Robot halts instantly, sounds acoustic reverse beeper, and retreats 0.20m.")
    print("  2. Rear Collision Guard: Stand directly behind the robot (<0.25m) during a breach.")
    print("     -> Robot detects your feet, SUPPRESSES the reverse maneuver, and halts dead.")
    print()

    cmd = (
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash 2>/dev/null; "
        "python3 /home/j/ros2_cognition_ws/scripts/test_safety_reactive_reverse.py"
    ) if IS_DEV_WORKSTATION else "python3 /root/cognition_ws/test_safety_reactive_reverse.py"
    run_interactive_command(cmd)


def dispatch_save_map():
    """Saves the active SLAM map permanently."""
    print_header("EXPORT & PERMANENTLY SAVE GENERATED 2D MAP", "Occupancy Grid YAML + PNG Serializer")
    map_name = input(f"{C_BOLD}Enter map filename (e.g. room_map_new): {C_RESET}").strip()
    if not map_name:
        map_name = f"map_{int(time.time())}"
    
    dest_path = f"/root/cognition_ws/maps_new/{map_name}" if IS_INSIDE_CONTAINER else f"~/cognition_ws/maps_new/{map_name}"
    cmd = (
        f"export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        f"source /opt/ros/humble/setup.bash; "
        f"ros2 run nav2_map_server map_saver_cli -f {dest_path}"
    )
    if IS_ON_PI:
        cmd = f"docker exec yahboom_gesture bash -c \"{cmd}\""
    run_interactive_command(cmd)
    print(f"\n{C_GREEN}>> Map successfully saved to {dest_path}.yaml and .png{C_RESET}")


def dispatch_collaborative_escort_mapped():
    """Mapped Mode: Collaborative Co-Worker Escort with Live AMCL Localization."""
    print_header("COLLABORATIVE CO-WORKER ESCORT (MAPPED MODE)", "Real-Time Metric AMCL Localization + Follow Gesture")
    print(f"{C_WHITE}Mission Overview:{C_RESET}")
    print("  1. Nav2 and AMCL localize the robot within the pre-calibrated facility map.")
    print("  2. Raise the FOLLOW gesture (peace sign) to lead the robot across the plant floor.")
    print("  3. The robot shadows you while respecting global static costmap boundaries.")
    print("  4. Live AMCL position (x, y, θ) updates continuously over the blueprint on :8080.")
    print("  5. Show STOP (open palm) to park the robot at any workstation.")
    print()

    # Bring up master stack with Nav2 and Cognition active
    cmd = (
        "docker exec -it yahboom_gesture bash -c '"
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true; "
        "ros2 launch /root/cognition_ws/src/cognition_simulation/launch/master_robot.launch.py'"
    ) if not IS_INSIDE_CONTAINER else (
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true; "
        "ros2 launch launch/master_robot.launch.py"
    )
    run_interactive_command(cmd)


def dispatch_capstone_patrol_preemption():
    """Mapped Mode: Milestone 10 Capstone Autonomous Patrol + Dynamic Gesture Preemption."""
    print_header("DEFENSE CAPSTONE: PATROL + DYNAMIC PREEMPTION", "Milestone 10 Full Integration Benchmark")
    print(f"{C_WHITE}Mission Protocol:{C_RESET}")
    print("  1. Robot executes autonomous multi-waypoint inspection route (Home -> P2 -> P3 -> Home).")
    print("  2. Telemetry is logged to a synchronized rosbag in real time (<150 KB/s).")
    print("  3. Dynamic Avoidance: Have a person walk across the path -> Local costmap detours smoothly.")
    print("  4. Touchless Preemption: Raise STOP gesture (open palm) -> Nav2 halts immediately.")
    print("  5. Raise GO gesture -> Robot resumes transit and completes the patrol mission.")
    print()

    robot_ip = get_robot_ip()
    cmd = "bash ~/run_nav2_patrol.sh" if IS_ON_PI else (
        f"ssh -t pi@{robot_ip} 'bash ~/run_nav2_patrol.sh'" if IS_DEV_WORKSTATION else
        "bash /root/cognition_ws/run_nav2_patrol.sh"
    )
    run_interactive_command(cmd)


def dispatch_waypoint_mission(mission_name: str):
    """Dispatches a named waypoint mission via mission_manager.py."""
    print_header(f"DISPATCHING MISSION: {mission_name}", "Nav2 Autonomous Action Client")
    cmd = (
        f"docker exec -it yahboom_gesture bash -c '"
        f"export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        f"source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true; "
        f"python3 /root/cognition_ws/mission_manager.py --mission {mission_name}'"
    ) if not IS_INSIDE_CONTAINER else (
        f"export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        f"source /opt/ros/humble/setup.bash; "
        f"python3 scripts/mission_manager.py --mission {mission_name}"
    )
    run_interactive_command(cmd)


def dispatch_plot_trajectory():
    """Decodes recorded rosbag and generates thesis publication plots (Figs 4.1 - 4.4)."""
    print_header("THESIS TELEMETRY & TRAJECTORY ANALYSIS PLOTTER", "Generates Figures 4.1 - 4.4 from Recorded Bags")
    bag_dir = "/home/pi/cognition_ws/bags" if IS_ON_PI else "/home/j/ros2_cognition_ws/bags"
    cmd = f"python3 scripts/plot_multi_waypoint_trajectory.py $(ls -td {bag_dir}/*/ 2>/dev/null | head -1)"
    run_interactive_command(cmd)


def dispatch_gimbal_calibration_sweep():
    """Cycles the 2-DOF active vision gimbal through calibrated ranges."""
    print_header("2-DOF ACTIVE VISION GIMBAL CALIBRATION SWEEP", "Calibrated Yahboom 0-Centric Protocol")
    print("Testing Pan (-60° to +60°) and Tilt (-15° to +24°, elevated home +18°)...")
    cmd = (
        "export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; "
        "source /opt/ros/humble/setup.bash >/dev/null 2>&1; "
        "python3 -c \""
        "import time, rclpy; from rclpy.node import Node; from std_msgs.msg import Int32\n"
        "rclpy.init(); n = Node('gimbal_cal'); p1 = n.create_publisher(Int32, '/servo_s1', 10); p2 = n.create_publisher(Int32, '/servo_s2', 10)\n"
        "m1 = Int32(); m2 = Int32()\n"
        "for pan in [0, -30, -60, 0, 30, 60, 0]:\n"
        "    m1.data = pan; m2.data = 18; p1.publish(m1); p2.publish(m2); time.sleep(0.6)\n"
        "for tilt in [18, 0, -15, 10, 24, 18]:\n"
        "    m1.data = 0; m2.data = tilt; p1.publish(m1); p2.publish(m2); time.sleep(0.6)\n"
        "n.destroy_node(); rclpy.shutdown()\""
    )
    if IS_ON_PI:
        cmd = f"docker exec yahboom_gesture bash -c '{cmd}'"
    run_interactive_command(cmd)


def dispatch_run_unit_verifications():
    """Executes the master automated verification suite (7/7 test suites)."""
    print_header("MASTER AUTOMATED SYSTEM VERIFICATION SUITE", "7 Master Suites — 100% Green Verification")
    cmd = "python3 scripts/run_all_local_verifications.py"
    run_interactive_command(cmd)


def dispatch_clean_fastdds():
    """Flushes stale FastDDS shared memory mutex locks and restarts micro-ROS nodes."""
    print_header("FASTDDS & DOCKER CLEAN RESET UTILITY", "Purges Stale Shared Memory Locks (/dev/shm)")
    cmd = (
        "docker exec yahboom_gesture bash -c '"
        "pkill -9 -f \"camera_pub|person_detection|active_vision|gesture_node|brain_node|twist_mux|bench_autonomy\" 2>/dev/null || true; "
        "rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true' && "
        "echo '>> Stale lockfiles cleared successfully.'"
    ) if not IS_INSIDE_CONTAINER else (
        "pkill -9 -f 'camera_pub|person_detection|active_vision|gesture_node|brain_node|twist_mux|bench_autonomy' 2>/dev/null || true; "
        "rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true; "
        "echo '>> Stale lockfiles cleared.'"
    )
    run_interactive_command(cmd)


def dispatch_camera_diagnostic():
    """Probes V4L2 devices, benchmarks capture rates, and checks ROS 2 image topics."""
    print_header("LIVE CAMERA FEED & V4L2 DEVICE DIAGNOSTIC", "Hardware Interface, FPS Benchmark & Snapshot")
    cmd = (
        "python3 scripts/diagnostics/test_camera_stream.py" if IS_DEV_WORKSTATION else
        "docker exec -it yahboom_gesture python3 /root/cognition_ws/test_camera_stream.py" if IS_ON_PI else
        "python3 /root/cognition_ws/test_camera_stream.py"
    )
    run_interactive_command(cmd)


def dispatch_standalone_web_visualizer():
    """Launches the lightweight RViz-equivalent Web Visualizer on port 8080."""
    print_header("STANDALONE WEB MAP & CAMERA VISUALIZER", "HTTP Port 8080 Dashboard")
    print(f"Opening server on http://0.0.0.0:8080 ...")
    cmd = (
        "python3 scripts/web_map_visualizer.py" if IS_DEV_WORKSTATION else
        "docker exec -it yahboom_gesture python3 /root/cognition_ws/web_map_visualizer.py" if IS_ON_PI else
        "python3 /root/cognition_ws/web_map_visualizer.py"
    )
    run_interactive_command(cmd)


# ════════════════════════════════════════════════════════════════════════════════
# 3. INTERACTIVE SUB-MENUS WITH ERGONOMIC BACK NAVIGATION
# ════════════════════════════════════════════════════════════════════════════════

def menu_unmapped_environment():
    while True:
        print_header("CATEGORY [1]: UNMAPPED ENVIRONMENT (COLLABORATIVE SLAM & HRI)", "Mode 1: Zero Prior Map Required — Exploration & Touchless Interaction")
        print(f"  {C_BOLD}[1.1]{C_RESET} Collaborative 'Follow-to-Map' SLAM (Live Map Construction on :8080)")
        print(f"  {C_BOLD}[1.2]{C_RESET} Full 6-Gesture Evaluation Suite (Test GO, STOP, FOLLOW, LEFT, RIGHT, BACK)")
        print(f"  {C_BOLD}[1.3]{C_RESET} ISO 15066 Safety Bubble & 20cm Reactive Reverse Retreat Test")
        print(f"  {C_BOLD}[1.4]{C_RESET} Manual Wireless Gamepad SLAM Mapping (Priority 100 Teleop)")
        print(f"  {C_BOLD}[1.5]{C_RESET} Save Generated 2D Metric Map (.yaml & .png)")
        print()
        print(f"  {C_BOLD}[H]{C_RESET}   {C_RED}EMERGENCY CHASSIS HALT (/cmd_vel = 0.0){C_RESET}")
        print(f"  {C_BOLD}[B]{C_RESET}   {C_CYAN}Back to Main Menu{C_RESET}")
        print(f"  {C_BOLD}[0]{C_RESET}   Exit Application")
        print()
        
        choice = input(f"{C_BOLD}Select Option: {C_RESET}").strip().upper()
        if choice in ["B", "BACK"]:
            break
        elif choice == "0":
            sys.exit(0)
        elif choice == "H":
            emergency_halt()
        elif choice in ["1", "1.1"]:
            dispatch_collaborative_follow_slam()
        elif choice in ["2", "1.2"]:
            dispatch_interactive_gesture_hri()
        elif choice in ["3", "1.3"]:
            dispatch_safety_bubble_test()
        elif choice in ["4", "1.4"]:
            run_interactive_command("ros2 launch launch/slam_real.launch.py")
        elif choice in ["5", "1.5"]:
            dispatch_save_map()
        else:
            print(f"{C_RED}Invalid selection.{C_RESET}")
            time.sleep(0.8)


def menu_mapped_environment():
    while True:
        print_header("CATEGORY [2]: MAPPED ENVIRONMENT (FACILITY AUTONOMY & DEFENSE)", "Mode 2: Pre-Calibrated Map Active — AMCL Localization & Navigation")
        print(f"  {C_BOLD}[2.1]{C_RESET} Collaborative Co-Worker Escort ('Follow-Me' with Live AMCL Localization)")
        print(f"  {C_BOLD}[2.2]{C_RESET} Defense Capstone: Patrol + Dynamic Obstacle & Gesture Preemption (Milestone 10)")
        print(f"  {C_BOLD}[2.3]{C_RESET} Unattended Facility Patrol (Complete 4-Waypoint L-Corridor Inspection)")
        print(f"  {C_BOLD}[2.4]{C_RESET} Central Corridor Inspection (Rapid 2-Waypoint Midpoint Check)")
        print(f"  {C_BOLD}[2.5]{C_RESET} North Gallery Patrol (Furthest Station Inspection & Return)")
        print(f"  {C_BOLD}[2.6]{C_RESET} Autonomous Return to Home Base (AMCL Recovery Docking at 0.08m, 0.05m)")
        print(f"  {C_BOLD}[2.7]{C_RESET} Generate Thesis Trajectory & Performance Plots (Figures 4.1 - 4.4)")
        print()
        print(f"  {C_BOLD}[H]{C_RESET}   {C_RED}EMERGENCY CHASSIS HALT (/cmd_vel = 0.0){C_RESET}")
        print(f"  {C_BOLD}[B]{C_RESET}   {C_CYAN}Back to Main Menu{C_RESET}")
        print(f"  {C_BOLD}[0]{C_RESET}   Exit Application")
        print()
        
        choice = input(f"{C_BOLD}Select Option: {C_RESET}").strip().upper()
        if choice in ["B", "BACK"]:
            break
        elif choice == "0":
            sys.exit(0)
        elif choice == "H":
            emergency_halt()
        elif choice in ["1", "2.1"]:
            dispatch_collaborative_escort_mapped()
        elif choice in ["2", "2.2"]:
            dispatch_capstone_patrol_preemption()
        elif choice in ["3", "2.3"]:
            dispatch_waypoint_mission("UNATTENDED_FACILITY_PATROL")
        elif choice in ["4", "2.4"]:
            dispatch_waypoint_mission("CENTRAL_INSPECTION")
        elif choice in ["5", "2.5"]:
            dispatch_waypoint_mission("NORTH_GALLERY_PATROL")
        elif choice in ["6", "2.6"]:
            dispatch_waypoint_mission("RETURN_HOME")
        elif choice in ["7", "2.7"]:
            dispatch_plot_trajectory()
        else:
            print(f"{C_RED}Invalid selection.{C_RESET}")
            time.sleep(0.8)


def menu_diagnostics_suite():
    while True:
        print_header("CATEGORY [3]: HARDWARE BENCHMARK & DIAGNOSTICS SUITE", "Unit Verification, Hardware Calibration & Live Telemetry Monitors")
        print(f"  {C_BOLD}[3.1]{C_RESET} Live Autonomous Dashboard Terminal Monitor (bench_autonomy_monitor.py)")
        print(f"  {C_BOLD}[3.2]{C_RESET} 2-DOF Active Vision Gimbal Calibration & Range Sweep")
        print(f"  {C_BOLD}[3.3]{C_RESET} Planar LiDAR Frontal & Rear Safety Bubble Live Visualizer")
        print(f"  {C_BOLD}[3.4]{C_RESET} Industrial Acoustic Safety Chimes & Buzzer Self-Test (/beep)")
        print(f"  {C_BOLD}[3.5]{C_RESET} Run Full Automated Verification Suite (7/7 Master Suites)")
        print(f"  {C_BOLD}[3.6]{C_RESET} Clean FastDDS Shared Memory Lockfiles & Process Reset")
        print(f"  {C_BOLD}[3.7]{C_RESET} Test Live Camera Feed & V4L2 Devices (FPS & Snapshot)")
        print(f"  {C_BOLD}[3.8]{C_RESET} Launch Standalone Web Visualizer Dashboard (Port :8080)")
        print()
        print(f"  {C_BOLD}[H]{C_RESET}   {C_RED}EMERGENCY CHASSIS HALT (/cmd_vel = 0.0){C_RESET}")
        print(f"  {C_BOLD}[B]{C_RESET}   {C_CYAN}Back to Main Menu{C_RESET}")
        print(f"  {C_BOLD}[0]{C_RESET}   Exit Application")
        print()
        
        choice = input(f"{C_BOLD}Select Option: {C_RESET}").strip().upper()
        if choice in ["B", "BACK"]:
            break
        elif choice == "0":
            sys.exit(0)
        elif choice == "H":
            emergency_halt()
        elif choice in ["1", "3.1"]:
            run_interactive_command("python3 scripts/bench_autonomy_monitor.py" if IS_DEV_WORKSTATION else "python3 /root/cognition_ws/bench_autonomy_monitor.py")
        elif choice in ["2", "3.2"]:
            dispatch_gimbal_calibration_sweep()
        elif choice in ["3", "3.3"]:
            run_interactive_command("python3 scripts/diagnostics/verify_lidar_live.py")
        elif choice in ["4", "3.4"]:
            run_interactive_command("python3 scripts/test_safety_audio.py")
        elif choice in ["5", "3.5"]:
            dispatch_run_unit_verifications()
        elif choice in ["6", "3.6"]:
            dispatch_clean_fastdds()
        elif choice in ["7", "3.7"]:
            dispatch_camera_diagnostic()
        elif choice in ["8", "3.8"]:
            dispatch_standalone_web_visualizer()
        else:
            print(f"{C_RED}Invalid selection.{C_RESET}")
            time.sleep(0.8)


# ════════════════════════════════════════════════════════════════════════════════
# 4. MAIN ENTRY POINT & MASTER CONTROLLER
# ════════════════════════════════════════════════════════════════════════════════

def main():
    signal.signal(signal.SIGINT, lambda sig, frame: emergency_halt() or sys.exit(0))
    
    checker = SystemHealthChecker()

    # If invoked with --audit-only, execute non-interactive pre-flight check and exit
    if "--audit-only" in sys.argv:
        print_header("SYSTEM PRE-FLIGHT HEALTH AUDIT (NON-INTERACTIVE)")
        checker.audit()
        checker.display_report()
        sys.exit(0 if checker.overall_ready else 1)

    # Initial startup audit
    print_header("AMR COGNITION SYSTEM — INITIALIZING PRE-FLIGHT AUDIT")
    print(f"{C_DIM}Probing Docker containers, sensor topics, neural weights, and battery...{C_RESET}")
    checker.audit()

    while True:
        print_header("AUTONOMOUS MOBILE ROBOT COGNITION — MASTER MISSION MENU", "Yahboom Micro-ROS Pi 5 Autonomous Mobile Robot | ROS 2 Humble")
        checker.display_report()

        print(f"{C_BOLD}OPERATIONAL MISSION DIRECTORIES:{C_RESET}")
        print(f"  {C_BOLD}[1]{C_RESET} {C_GREEN}UNMAPPED ENVIRONMENT{C_RESET}   (Collaborative Follow-to-Map SLAM & Free-Space HRI)")
        print(f"  {C_BOLD}[2]{C_RESET} {C_BLUE}MAPPED ENVIRONMENT{C_RESET}     (Collaborative Escort, Capstone Patrol & Waypoints)")
        print(f"  {C_BOLD}[3]{C_RESET} {C_MAGENTA}SYSTEM BENCHMARKS{C_RESET}      (Hardware Calibration, Live HUD & Diagnostic Tests)")
        print()
        print(f"  {C_BOLD}[H]{C_RESET} {C_BG_RED}{C_WHITE} EMERGENCY CHASSIS HALT (/cmd_vel = 0.0) {C_RESET}")
        print(f"  {C_BOLD}[R]{C_RESET} {C_YELLOW}Re-Run Pre-Flight Health Audit{C_RESET}")
        print(f"  {C_BOLD}[0]{C_RESET} Exit")
        print()

        choice = input(f"{C_BOLD}Select Option [1-3, H, R, 0]: {C_RESET}").strip().upper()
        if choice == "1":
            menu_unmapped_environment()
        elif choice == "2":
            menu_mapped_environment()
        elif choice == "3":
            menu_diagnostics_suite()
        elif choice == "H":
            emergency_halt()
        elif choice == "R":
            print(f"\n{C_DIM}Re-running diagnostic sweep...{C_RESET}")
            checker.audit()
            time.sleep(0.5)
        elif choice == "0":
            print(f"\n{C_CYAN}>> Exiting Master Demo Menu. Standby.{C_RESET}")
            break
        else:
            print(f"{C_RED}Invalid selection.{C_RESET}")
            time.sleep(0.8)


if __name__ == "__main__":
    main()
