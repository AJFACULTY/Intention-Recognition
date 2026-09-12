#!/bin/bash
# ==============================================================================
# run_nav2_patrol.sh — Physical Waypoint Patrol with Synchronized Bag Recording
# Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
# Authors: Eleana Osei Owusu & Joel Nii Adjetey Ahulu
# Institution: Ghana Communication Technology University (GCTU)
# ==============================================================================

set -e

CONTAINER="yahboom_gesture"
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BAG_NAME="patrol_${TIMESTAMP}"
BAG_CONTAINER_DIR="/root/cognition_ws/bags/${BAG_NAME}"
BAG_HOST_DIR="/home/pi/cognition_ws/bags/${BAG_NAME}"

mkdir -p /home/pi/cognition_ws/bags

echo "=================================================================="
echo "    AUTONOMOUS COGNITION — NAV2 WAYPOINT PATROL RUNNER"
echo "    Robot: Yahboom (Raspberry Pi 5)"
echo "    Container: ${CONTAINER}"
echo "    Session Timestamp: ${TIMESTAMP}"
echo "=================================================================="

# Check container running state
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "[ERROR] Docker container '${CONTAINER}' is not running!"
    exit 1
fi

# Execute patrol inside container with ROS 2 environment
docker exec -it "${CONTAINER}" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true

    echo '[1/4] Checking Nav2 action server availability...'
    if ! ros2 action list | grep -q '/navigate_through_poses'; then
        echo '[!] Nav2 action server /navigate_through_poses not yet ready.'
        echo '    Please ensure Nav2 is running (bash ~/start_nav2.sh).'
        exit 1
    fi
    echo '>> Nav2 action server verified ACTIVE.'

    echo '[2/4] Starting synchronized telemetry bag recording...'
    echo '      Bag destination: ${BAG_CONTAINER_DIR}'
    ros2 bag record -o '${BAG_CONTAINER_DIR}' /odom_raw /scan /cmd_vel /tf /tf_static > /tmp/bag_rec_${TIMESTAMP}.log 2>&1 &
    BAG_PID=\$!
    sleep 2

    # Clean shutdown trap
    cleanup() {
        echo ''
        echo '[CLEANUP] Stopping bag recording...'
        kill -2 \"\$BAG_PID\" 2>/dev/null || true
        wait \"\$BAG_PID\" 2>/dev/null || true
        echo '[CLEANUP] Halting chassis...'
        timeout 1s ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null 2>&1 || true
    }
    trap cleanup EXIT INT TERM

    echo '[3/4] Dispatching 3-Waypoint Corridor Patrol...'
    if python3 /root/cognition_ws/navigate_waypoints.py "\$@"; then
        echo '[4/4] Patrol successfully traversed all legs. Finalizing bag...'
        PATROL_SUCCESS=true
    else
        echo '[!] Patrol aborted or incomplete. Finalizing diagnostic bag...'
        PATROL_SUCCESS=false
    fi
    sleep 2
"

echo "=================================================================="
if [ -d "${BAG_HOST_DIR}" ]; then
    echo "  Telemetry bag recorded at: ${BAG_HOST_DIR}"
fi
echo "=================================================================="
