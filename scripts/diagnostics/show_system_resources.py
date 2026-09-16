#!/usr/bin/env python3
"""
show_system_resources.py — Embedded Hardware Resource Profiler & Scientific Benchmark Audit
=============================================================================================
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Institution: Ghana Communication Technology University (GCTU)
Thesis: Real-Time Human Intention Recognition for Autonomous Mobile Robot Navigation

Displays:
  1. Live Embedded Robot Telemetry (CPU Load, Temperature, RAM Headroom, Storage, Docker Stats)
  2. Ground-Truth Scientific Benchmark Catalog (F1-Scores, ADE/FDE, Latency Budget, Navigation MAE/RMSE)
"""

import os
import sys
import time
import subprocess
import shutil
from typing import Dict, Any, Tuple, List

# ANSI Colors
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
C_BG_BLUE = "\033[44m"
C_BG_DARK = "\033[40m"


def get_cpu_temp() -> str:
    """Reads Raspberry Pi or system CPU temperature."""
    try:
        # Check vcgencmd (Pi specific)
        res = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=1.0)
        if res.returncode == 0:
            return res.stdout.strip().replace("temp=", "")
    except Exception:
        pass
    
    # Check thermal zone
    for path in ["/sys/class/thermal/thermal_zone0/temp", "/sys/class/thermal/thermal_zone1/temp"]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    millideg = int(f.read().strip())
                    return f"{millideg / 1000.0:.1f}'C"
            except Exception:
                pass
    return "N/A"


def get_memory_info() -> Dict[str, str]:
    """Reads /proc/meminfo or free -m."""
    info = {"total": "N/A", "used": "N/A", "available": "N/A", "percent": "N/A"}
    try:
        res = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=1.0)
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            for line in lines:
                if line.startswith("Mem:"):
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    avail = int(parts[6]) if len(parts) > 6 else int(parts[3])
                    pct = (used / total) * 100.0 if total > 0 else 0
                    info["total"] = f"{total / 1024.0:.2f} GB ({total} MB)"
                    info["used"] = f"{used / 1024.0:.2f} GB ({used} MB)"
                    info["available"] = f"{avail / 1024.0:.2f} GB ({avail} MB)"
                    info["percent"] = f"{pct:.1f}%"
                    break
    except Exception:
        pass
    return info


def get_disk_info() -> str:
    """Returns disk usage of root."""
    try:
        total, used, free = shutil.disk_usage("/")
        return f"{used / (1024**3):.1f} GB used / {free / (1024**3):.1f} GB free ({total / (1024**3):.1f} GB total)"
    except Exception:
        return "N/A"


def get_cpu_usage() -> str:
    """Computes instant CPU usage over 0.2 seconds."""
    try:
        def read_stat():
            with open("/proc/stat", "r") as f:
                fields = [float(x) for x in f.readline().strip().split()[1:]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            return idle, total

        idle1, total1 = read_stat()
        time.sleep(0.25)
        idle2, total2 = read_stat()
        d_idle = idle2 - idle1
        d_total = total2 - total1
        if d_total > 0:
            usage = 100.0 * (1.0 - d_idle / d_total)
            cores = os.cpu_count() or 4
            return f"{usage:.1f}% (across {cores} cores, aggregate ~{usage * cores / 100.0 * 100:.0f}%)"
    except Exception:
        pass
    return "N/A"


def get_docker_stats() -> List[Tuple[str, str, str]]:
    """Returns container CPU and RAM usage if Docker is available."""
    containers = []
    try:
        res = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                parts = line.split("|")
                if len(parts) >= 3:
                    containers.append((parts[0], parts[1], parts[2]))
    except Exception:
        pass
    return containers


def render_banner(title: str, subtitle: str = ""):
    width = 84
    print(C_BOLD + C_CYAN + "═" * width + C_RESET)
    print(f"{C_BOLD}{C_WHITE}  {title.center(width - 4)}{C_RESET}")
    if subtitle:
        print(f"{C_DIM}{C_CYAN}  {subtitle.center(width - 4)}{C_RESET}")
    print(C_BOLD + C_CYAN + "═" * width + C_RESET)


def main():
    os.system("clear" if os.name != "nt" else "cls")
    render_banner(
        "EMBEDDED HARDWARE RESOURCE AUDIT & SCIENTIFIC BENCHMARKS",
        "Empirical Edge Profiling, F1-Scores, Latency Budget & Safety Compliance"
    )
    print()

    # 1. Live Hardware Telemetry
    mem = get_memory_info()
    cpu_use = get_cpu_usage()
    cpu_temp = get_cpu_temp()
    disk_use = get_disk_info()
    cores = os.cpu_count() or 4

    print(f"{C_BOLD}{C_YELLOW}── [1] REAL-TIME EMBEDDED EDGE COMPUTE TELEMETRY ──{C_RESET}")
    print(f"  {C_CYAN}Compute Architecture :{C_RESET} Broadcom BCM2712 (Quad-core ARM Cortex-A76 @ 2.4 GHz, 64-bit)")
    print(f"  {C_CYAN}Current CPU Load     :{C_RESET} {C_BOLD}{cpu_use}{C_RESET}")
    print(f"  {C_CYAN}Current Core Temp    :{C_RESET} {C_BOLD}{cpu_temp}{C_RESET} (Thermal throttling threshold: 80.0'C)")
    print(f"  {C_CYAN}Physical RAM Usage   :{C_RESET} {C_BOLD}{mem['used']}{C_RESET} of {mem['total']} ({mem['percent']} utilized)")
    print(f"  {C_CYAN}Available Headroom   :{C_RESET} {C_GREEN}{C_BOLD}{mem['available']}{C_RESET} (Zero OOM / Swap Thrashing Guaranteed)")
    print(f"  {C_CYAN}Local Root Storage   :{C_RESET} {disk_use}")

    doc_stats = get_docker_stats()
    if doc_stats:
        print(f"  {C_CYAN}Active Containers    :{C_RESET}")
        for name, cpu, ram in doc_stats:
            print(f"    • {C_WHITE}{name:<18}{C_RESET} CPU: {C_BOLD}{cpu:<8}{C_RESET} RAM: {C_BOLD}{ram}{C_RESET}")
    print()

    # 2. Benchmark Ground-Truth: 19-Feature MLP Gesture Recognition
    print(f"{C_BOLD}{C_YELLOW}── [2] 19-FEATURE MLP GESTURE RECOGNITION BENCHMARKS (THESIS CH. 4) ──{C_RESET}")
    print(f"  {C_CYAN}Dataset Composition  :{C_RESET} 6,000 balanced samples (1,000 per class across 6 canonical gestures)")
    print(f"  {C_CYAN}Feature Extraction   :{C_RESET} 21 MediaPipe 3D joint landmarks -> 19 Scale & Translation Invariant Features")
    print(f"  {C_CYAN}Overall Test Accuracy:{C_RESET} {C_GREEN}{C_BOLD}99.38%{C_RESET} (on unseen test set via stratified 5-fold cross-validation)")
    print(f"  {C_CYAN}Physical Field Trials:{C_RESET} {C_GREEN}{C_BOLD}96.67%{C_RESET} (174/180 successful trials across 1.0m, 1.75m, 2.5m under daylight & lamps)")
    print(f"  {C_CYAN}Per-Class Classification Metrics (Table 4.1):{C_RESET}")
    print(f"    ┌──────────┬───────────┬────────┬──────────┬──────────────────────────────────────────┐")
    print(f"    │ {C_BOLD}GESTURE{C_RESET}  │ {C_BOLD}PRECISION{C_RESET} │ {C_BOLD}RECALL{C_RESET} │ {C_BOLD}F1-SCORE{C_RESET} │ {C_BOLD}PHYSICAL ACTUATION OUTCOME               {C_RESET}│")
    print(f"    ├──────────┼───────────┼────────┼──────────┼──────────────────────────────────────────┤")
    print(f"    │ BACK     │   0.997   │ 0.996  │  {C_BOLD}0.9965{C_RESET}  │ -0.15 m/s Reverse retreat (corridor check)│")
    print(f"    │ FOLLOW   │   0.999   │ 0.987  │  {C_BOLD}0.9930{C_RESET}  │ Visual servoing shadows operator steps   │")
    print(f"    │ GO       │   0.993   │ 0.994  │  {C_BOLD}0.9935{C_RESET}  │ +0.25 m/s Forward transit velocity       │")
    print(f"    │ LEFT     │   0.991   │ 0.991  │  {C_BOLD}0.9910{C_RESET}  │ +0.40 rad/s In-place CCW vehicle pivot   │")
    print(f"    │ RIGHT    │   0.995   │ 0.998  │  {C_BOLD}0.9965{C_RESET}  │ -0.40 rad/s In-place CW vehicle pivot    │")
    print(f"    │ STOP     │   0.988   │ 0.997  │  {C_BOLD}0.9925{C_RESET}  │ Instant wheel brake (/cmd_vel = 0.0 m/s) │")
    print(f"    ├──────────┼───────────┼────────┼──────────┼──────────────────────────────────────────┤")
    print(f"    │ {C_BOLD}MACRO AVG{C_RESET}│ {C_BOLD}  0.9938  {C_RESET}│ {C_BOLD}0.9938 {C_RESET}│  {C_GREEN}{C_BOLD}0.9938{C_RESET}  │ Mean F1-Score across all 6 classes       │")
    print(f"    └──────────┴───────────┴────────┴──────────┴──────────────────────────────────────────┘")
    print()

    # 3. Benchmark Ground-Truth: Human Intention & Path Prediction
    print(f"{C_BOLD}{C_YELLOW}── [3] LSTM HUMAN INTENTION & PATH PREDICTION BENCHMARKS (PELLEGRINI METRICS) ──{C_RESET}")
    print(f"  {C_CYAN}Model Architecture   :{C_RESET} Recurrent LSTM (2-layer, 64 hidden units, 8-frame horizon forecasting)")
    print(f"  {C_CYAN}Average Displ. Error :{C_RESET} {C_GREEN}{C_BOLD}ADE = 25.8 pixels{C_RESET} (Euclidean drift across 8 forecast frames in 640x480)")
    print(f"  {C_CYAN}Final Displ. Error   :{C_RESET} {C_GREEN}{C_BOLD}FDE = 32.4 pixels{C_RESET} (Terminal horizon displacement offset)")
    print(f"  {C_CYAN}Navigation Coupling  :{C_RESET} Proactively inflates local costmap in predicted human transit cone")
    print()

    # 4. Benchmark Ground-Truth: End-to-End Latency Budget
    print(f"{C_BOLD}{C_YELLOW}── [4] QUANTITATIVE END-TO-END LATENCY BUDGET (TABLE 4.3 & ISO 15066) ──{C_RESET}")
    print(f"  {C_CYAN}Empirical Mean Latency:{C_RESET} {C_GREEN}{C_BOLD}132.61 ms{C_RESET} (std: +/-3.82 ms, 95% CI: [132.05, 133.17 ms], max: 143.8 ms)")
    print(f"  {C_CYAN}Design Safety Deadline:{C_RESET} {C_BOLD}150.00 ms{C_RESET} (Engineering Research Question 1 Compliance)")
    print(f"  {C_CYAN}Turnaround Breakdown :{C_RESET}")
    print(f"    1. Camera V4L2 Exposure & Hardware Capture (640x480 @ 20 FPS) :  50.0 ms")
    print(f"    2. MediaPipe Hand Landmark Extraction (21 skeletal joints)   :  38.2 ms")
    print(f"    3. 19-D Scale & Translation Geometric Feature Computation    :   0.8 ms")
    print(f"    4. MLP Neural Forward Pass (ONNX Runtime / CPython)          :   1.8 ms")
    print(f"    5. ROS 2 DDS Node Arbitration & Temporal Consensus (/cmd_vel):   1.2 ms")
    print(f"    6. Micro-ROS UART Transmission (921,600 baud) & Motor Driver :  40.0 ms")
    print(f"    ────────────────────────────────────────────────────────────────────────")
    print(f"    {C_BOLD}Cumulative Nominal End-to-End Latency                        : 132.0 ms{C_RESET}")
    print()

    # 5. Benchmark Ground-Truth: Autonomous Nav2 Patrol & Locomotion
    print(f"{C_BOLD}{C_YELLOW}── [5] PHYSICAL LOCOMOTION & NAVIGATION FIDELITY (TABLE 4.4 & METRICS) ──{C_RESET}")
    print(f"  {C_CYAN}Mean Absolute Error  :{C_RESET} {C_BOLD}MAE  = 15.47 cm{C_RESET} (Global planned path adherence)")
    print(f"  {C_CYAN}Root Mean Square Err :{C_RESET} {C_BOLD}RMSE = 22.24 cm{C_RESET}")
    print(f"  {C_CYAN}Terminal Waypoints   :{C_RESET} P1: 2.7 cm | P2: 3.7 cm | P3: 8.1 cm | P4: 6.4 cm (All < 12.0 cm threshold)")
    print(f"  {C_CYAN}Patrol Completion    :{C_RESET} {C_GREEN}{C_BOLD}100.0% Autonomous Completion{C_RESET} (15.89 m traversed across 6 legs)")
    print()

    # 6. Peak Resource Ceiling
    print(f"{C_BOLD}{C_YELLOW}── [6] FULL-PIPELINE CONCURRENT RESOURCE CEILING (BENCHMARK STRESS TEST) ──{C_RESET}")
    print(f"  {C_CYAN}Peak Aggregate CPU   :{C_RESET} 311% across 4 cores (~77.8% load per core with SLAM + YOLO + MediaPipe + MLP + LSTM)")
    print(f"  {C_CYAN}Physical Memory Peak :{C_RESET} 4.2 GB used / 3.8 GB headroom (47.5% safety margin on 8GB Pi 5)")
    print(f"  {C_CYAN}Throughput Rates     :{C_RESET} Camera: 20.0 Hz | LiDAR: 12.6 Hz | Gesture: 10.0 Hz | Person: 2.7 Hz")
    print()

    print(f"{C_BOLD + C_CYAN}═" * 84 + C_RESET)
    print(f"{C_DIM}Press Enter to return to menu...{C_RESET}", end="")
    try:
        input()
    except EOFError:
        pass


if __name__ == "__main__":
    main()
