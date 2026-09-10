#!/usr/bin/env bash
# ==============================================================================
# record_autonomy_bag.sh — Lightweight ROS 2 Telemetry Bag Recorder
# ==============================================================================
# Records essential navigation, perception, and control telemetry while
# strictly excluding uncompressed camera video frames to prevent MicroSD
# I/O saturation and thermal throttling on the Raspberry Pi 5.
# ==============================================================================

set -eo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BAG_BASE="${BAG_OUTPUT_DIR:-$HOME/bags}"
BAG_DIR="${BAG_BASE}/telemetry_${TIMESTAMP}"

mkdir -p "${BAG_BASE}"

echo "======================================================================"
echo "    COGNITION ROBOTICS — TELEMETRY BAG RECORDER"
echo "======================================================================"
echo ">> Target Output Directory: ${BAG_DIR}"
echo ">> Selected Telemetry Channels:"
echo "   - /cognition/gesture       (Hand gesture classification tokens)"
echo "   - /cognition/detection     (Operator bounding box & tracking state)"
echo "   - /cmd_vel                 (Arbiter output velocity to wheels)"
echo "   - /cmd_vel_gesture         (Brain node gesture velocity)"
echo "   - /cmd_vel_nav             (Nav2 autonomous navigation velocity)"
echo "   - /cmd_vel_joy             (Manual joystick override velocity)"
echo "   - /odom_raw                (Wheel encoder ticks & dead-reckoning)"
echo "   - /imu                     (6-axis IMU angular velocity / accel)"
echo "   - /scan                    (Planar MS200 LiDAR distance sweeps)"
echo "   - /tf                      (Dynamic coordinate transform tree)"
echo "   - /tf_static               (Static coordinate transform tree)"
echo "======================================================================"
echo ">> NOTE: High-bandwidth raw camera images are deliberately EXCLUDED"
echo "   to preserve MicroSD bus bandwidth (<150 KB/s disk write rate)."
echo ">> Press Ctrl+C at any time to stop recording and close the bag."
echo "======================================================================"

export ROS_DOMAIN_ID=20
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

TOPICS="/cognition/gesture /cognition/detection /cmd_vel /cmd_vel_gesture /cmd_vel_nav /cmd_vel_joy /odom_raw /imu /scan /tf /tf_static"

# Check if native ros2 exists, otherwise invoke inside yahboom_base container
if command -v ros2 &> /dev/null || [ -f "/opt/ros/humble/setup.bash" ] || [ -f "/opt/ros/jazzy/setup.bash" ]; then
    . /opt/ros/humble/setup.bash 2>/dev/null || . /opt/ros/jazzy/setup.bash 2>/dev/null
    ros2 bag record -o "${BAG_DIR}" $TOPICS
elif docker ps --format '{{.Names}}' | grep -q 'yahboom_base'; then
    echo ">> Native ros2 not found on host. Executing inside yahboom_base container..."
    docker exec -it yahboom_base bash -c "
        export ROS_DOMAIN_ID=20
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        . /opt/ros/humble/setup.bash
        ros2 bag record -o '${BAG_DIR}' $TOPICS
    "
else
    echo "[ERROR] Neither native ROS 2 nor yahboom_base container found!"
    exit 1
fi

echo ""
echo ">> Bag recording successfully finalized at: ${BAG_DIR}"

