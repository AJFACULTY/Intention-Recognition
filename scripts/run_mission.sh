#!/bin/bash
# ==============================================================================
# run_mission.sh — Turnkey Terminal Mission Dispatcher for Autonomous AMR
# Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
# ==============================================================================

set -uo pipefail

CONTAINER="yahboom_gesture"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "[ERROR] Docker container '${CONTAINER}' is not running!"
    echo "Please launch the autonomy container first."
    exit 1
fi

MISSION_NAME="${1:-}"

# If no mission provided on CLI, present interactive mission pool selector
if [ -z "$MISSION_NAME" ]; then
    echo "=================================================================="
    echo "    AUTONOMOUS COGNITION — MISSION POOL SELECTOR"
    echo "    Robot: Yahboom (Raspberry Pi 5) | ROS 2 Humble"
    echo "=================================================================="
    echo "  [1] RETURN_HOME               (Autonomous Return to Home Base: 0.08m, 0.05m)"
    echo "  [2] CENTRAL_INSPECTION        (Corridor Midpoint Inspection: Home -> P2 -> Home)"
    echo "  [3] NORTH_GALLERY_PATROL      (Long Leg Corridor Patrol: Home -> P2 -> P3 -> Home)"
    echo "  [4] UNATTENDED_FACILITY_PATROL(Complete L-Form Sweep: Home -> P2 -> P3 -> P4 -> Home)"
    echo "  [5] EMERGENCY_STOP            (Halt all chassis motion immediately)"
    echo "=================================================================="
    read -rp "Select Mission [1-5] (default 1): " CHOICE
    CHOICE="${CHOICE:-1}"

    case "$CHOICE" in
        1) MISSION_NAME="RETURN_HOME" ;;
        2) MISSION_NAME="CENTRAL_INSPECTION" ;;
        3) MISSION_NAME="NORTH_GALLERY_PATROL" ;;
        4) MISSION_NAME="UNATTENDED_FACILITY_PATROL" ;;
        5)
            echo "[!] COMMANDING EMERGENCY STOP..."
            docker exec "${CONTAINER}" bash -c "
                export ROS_DOMAIN_ID=20
                export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
                source /opt/ros/humble/setup.bash
                ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null 2>&1
            "
            echo ">> Chassis halted."
            exit 0
            ;;
        *)
            echo "[!] Invalid selection. Defaulting to RETURN_HOME."
            MISSION_NAME="RETURN_HOME"
            ;;
    esac
fi

echo "=================================================================="
echo "    DISPATCHING AUTONOMOUS MISSION: ${MISSION_NAME}"
echo "=================================================================="

docker exec -it "${CONTAINER}" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true

    python3 /root/cognition_ws/mission_manager.py --mission '${MISSION_NAME}'
"
