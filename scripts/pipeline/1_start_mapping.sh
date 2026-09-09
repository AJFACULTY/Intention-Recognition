#!/bin/bash
# ============================================================================
# 1_start_mapping.sh  (v2 — records exact PIDs for reliable cleanup)
#
# Fixes the recurring cleanup bug: two previous sessions left laser_tf,
# scan_republisher, odom_imu_republisher, and ekf_node running after
# "cleanup" because pattern-matching pkill didn't match their real names.
# This version captures the ACTUAL PIDs right after launch and saves them
# to ~/mapping_session_pids.txt, so 3_save_map_and_stop.sh can kill those
# exact processes by PID — no guessing.
#
# Usage:
#   chmod +x 1_start_mapping.sh
#   ./1_start_mapping.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

PID_FILE=~/mapping_session_pids.txt

echo "======================================================"
echo "== Stopping cognition.service (gesture control)"
echo "======================================================"
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2

docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

echo
echo "======================================================"
echo "== Launching slam_real.launch.py — PERSISTENT, no timeout"
echo "======================================================"
docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  ros2 launch /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py > /tmp/mapping_session.log 2>&1
"

echo "Waiting 10s for all nodes to fully come up..."
sleep 10

echo
echo "--- Capturing exact PIDs of each SLAM-session process ---"
> "$PID_FILE"
for pattern in "static_transform_publisher.*laser_tf" "cognition_simulation/scan_republisher" "cognition_simulation/odom_imu_republisher" "robot_localization/ekf_node" "async_slam_toolbox_node"; do
    PID=$(docker exec yahboom_gesture bash -c "ps aux | grep -E '${pattern}' | grep -v grep | awk '{print \$2}'" 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "$PID" >> "$PID_FILE"
        echo "  Found: $pattern -> PID $PID"
    else
        echo "  WARNING: no PID found for pattern: $pattern"
    fi
done

echo
echo "Saved PIDs to $PID_FILE:"
cat "$PID_FILE"

echo
echo "--- Confirming SLAM nodes are running ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "--- Confirming sensor registered ---"
docker exec yahboom_gesture bash -c "grep -c 'Registering sensor' /tmp/mapping_session.log" 2>&1

echo
echo "======================================================"
echo "== READY TO DRIVE"
echo "======================================================"
echo "SLAM is running and will keep running until you run 3_save_map_and_stop.sh."
echo
echo "Now: drive the robot around the room using the joystick."
echo "  - Cover the whole room, loop back through areas you've already"
echo "    covered every minute or two (helps correct any drift)."
echo "  - Drive slowly and smoothly, especially through turns."
echo "  - Pause briefly after each turn before continuing straight."
echo "  - You can run 2_check_mapping_progress.sh at any time to peek at"
echo "    progress without stopping anything."
echo
echo "When you're satisfied with coverage, run 3_save_map_and_stop.sh."
