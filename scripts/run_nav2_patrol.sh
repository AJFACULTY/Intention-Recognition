#!/bin/bash
# ==============================================================================
# run_nav2_patrol.sh — Autonomous Waypoint Patrol with Synchronized Bag Recording
# Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
# Institution: Ghana Communication Technology University (GCTU)
# ==============================================================================

set -uo pipefail

CONTAINER="yahboom_gesture"
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BAG_NAME="patrol_${TIMESTAMP}"
BAG_CONTAINER_DIR="/root/cognition_ws/bags/${BAG_NAME}"
BAG_HOST_DIR="/home/pi/cognition_ws/bags/${BAG_NAME}"

MISSION_NAME="${1:-UNATTENDED_FACILITY_PATROL}"

mkdir -p /home/pi/cognition_ws/bags

echo "=================================================================="
echo "    AUTONOMOUS COGNITION — NAV2 WAYPOINT PATROL RUNNER"
echo "    Robot: Yahboom (Raspberry Pi 5) | ROS 2 Humble"
echo "    Mission: ${MISSION_NAME}"
echo "    Synchronized Bag: ${BAG_NAME}"
echo "=================================================================="

# Check container running state
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "[ERROR] Docker container '${CONTAINER}' is not running!"
    echo "Please ensure container is running before launching patrol."
    exit 1
fi

# Execute patrol inside container with ROS 2 environment
docker exec -it "${CONTAINER}" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true

    echo '[1/4] Checking Nav2 action server availability...'
    if ! ros2 action list | grep -q '/navigate_to_pose'; then
        echo '[!] Nav2 action server /navigate_to_pose not yet ready.'
        echo '    Please ensure Nav2 is running (bash ~/start_nav2.sh).'
        exit 1
    fi
    echo '>> Nav2 action server verified ACTIVE.'

    echo '[2/4] Starting synchronized telemetry bag recording...'
    echo '      Destination: ${BAG_CONTAINER_DIR}'
    # Record non-saturating scalar telemetry topics (<150 KB/s write rate)
    ros2 bag record -o '${BAG_CONTAINER_DIR}' \
        /odom_raw \
        /odometry/filtered \
        /scan \
        /cmd_vel \
        /cmd_vel_nav \
        /cmd_vel_joy \
        /tf \
        /tf_static \
        /amcl_pose \
        /plan \
        /battery \
        /safety/chime > /tmp/bag_rec_${TIMESTAMP}.log 2>&1 &
    BAG_PID=\$!
    sleep 2

    # Clean shutdown trap
    cleanup() {
        echo ''
        echo '[CLEANUP] Stopping bag recording (flushing buffers)...'
        kill -2 \"\$BAG_PID\" 2>/dev/null || true
        wait \"\$BAG_PID\" 2>/dev/null || true
        echo '[CLEANUP] Zeroing chassis velocity...'
        timeout 1s ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null 2>&1 || true
    }
    trap cleanup EXIT INT TERM

    echo '[3/4] Dispatching Mission: ${MISSION_NAME}...'
    if python3 /root/cognition_ws/mission_manager.py --mission '${MISSION_NAME}'; then
        echo '[4/4] Mission successfully completed! Finalizing bag...'
    else
        echo '[!] Mission aborted or incomplete. Finalizing diagnostic bag...'
    fi
    sleep 2
"

echo "=================================================================="
echo "  PATROL & TELEMETRY SESSION CONCLUDED"
echo "  Bag location on Pi: ${BAG_HOST_DIR}"
echo "  To decode & plot on workstation:"
echo "    scp -r pi@\$(hostname -I | awk '{print \$1}'):${BAG_HOST_DIR} ~/ros2_cognition_ws/bags/"
echo "    python3 scripts/plot_multi_waypoint_trajectory.py ~/ros2_cognition_ws/bags/${BAG_NAME}"
echo "=================================================================="

