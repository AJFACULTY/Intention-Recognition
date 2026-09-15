#!/bin/bash
# ==============================================================================
# menu.sh — Turnkey Launcher for AMR Cognition Master Demonstration Menu
# Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check if running directly on the Raspberry Pi
if [ -f "/etc/rpi-issue" ] || [ -d "/home/pi" ]; then
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash >/dev/null 2>&1 || true
    
    # Try container location first, then host location
    if [ -f "/root/cognition_ws/scripts/master_demo_menu.py" ]; then
        exec python3 /root/cognition_ws/scripts/master_demo_menu.py "$@"
    elif [ -f "/home/pi/cognition_ws/master_demo_menu.py" ]; then
        exec python3 /home/pi/cognition_ws/master_demo_menu.py "$@"
    elif [ -f "${SCRIPT_DIR}/master_demo_menu.py" ]; then
        exec python3 "${SCRIPT_DIR}/master_demo_menu.py" "$@"
    fi
fi

# If running on the development workstation:
echo "=================================================================="
echo "    AMR COGNITION — MASTER CONSOLIDATED DEMO LAUNCHER"
echo "=================================================================="

ROBOT_IP=""
if ping -c 1 -W 1 10.27.122.136 >/dev/null 2>&1; then
    ROBOT_IP="10.27.122.136"
elif ping -c 1 -W 1 10.27.122.135 >/dev/null 2>&1; then
    ROBOT_IP="10.27.122.135"
fi

if [ -n "$ROBOT_IP" ]; then
    echo ">> Detected physical robot online at: ${ROBOT_IP}"
    echo "  [1] Connect & Launch Live Menu on Physical Robot (SSH)"
    echo "  [2] Run Local Workstation Diagnostic & Pre-Flight Menu"
    read -rp "Select Option [1-2] (default 1): " CHOICE
    CHOICE="${CHOICE:-1}"
    
    if [ "$CHOICE" = "1" ]; then
        echo ">> Connecting to pi@${ROBOT_IP}..."
        ssh -t "pi@${ROBOT_IP}" "python3 ~/cognition_ws/master_demo_menu.py"
        exit $?
    fi
else
    echo ">> Physical robot is currently offline or recharging."
    echo ">> Launching local workstation inspection mode..."
    sleep 1
fi

python3 "${SCRIPT_DIR}/master_demo_menu.py" "$@"
