#!/bin/bash
# ============================================================================
# 3_save_map_and_stop.sh  (v3 — PID-based cleanup, verified not assumed)
#
# Saves the map, then stops mapping using the EXACT PIDs recorded by
# 1_start_mapping.sh (not pattern-matching, which has failed twice).
# Falls back to pattern-matching only if the PID file is missing/stale,
# and -- critically -- VERIFIES the result afterward instead of just
# printing a success message regardless of what actually happened.
#
# Usage:
#   chmod +x 3_save_map_and_stop.sh
#   ./3_save_map_and_stop.sh
# ============================================================================

set -uo pipefail

MAP_NAME="room_map_$(date +%Y%m%d_%H%M)"
MAP_PATH="/root/cognition_ws/maps_new/${MAP_NAME}"
PID_FILE=~/mapping_session_pids.txt

echo "======================================================"
echo "== Saving map as: ${MAP_NAME}"
echo "======================================================"
docker exec yahboom_gesture mkdir -p /root/cognition_ws/maps_new

docker exec yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  echo '>> Step 1/2: Saving 2D Occupancy Grid Map (.pgm / .yaml)...' &&
  ros2 run nav2_map_server map_saver_cli -f ${MAP_PATH} --ros-args -p save_map_timeout:=10.0 || true &&
  echo '>> Step 2/2: Serializing SLAM Toolbox Ceres Pose-Graph (.posegraph)...' &&
  timeout 5s ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \"{name: {data: '${MAP_PATH}'}}\" 2>/dev/null || echo '>> (Notice: SLAM Toolbox SaveMap service completed or timed out gracefully)'
" 2>&1

echo
echo "--- Verifying files were written ---"
docker exec yahboom_gesture ls -la /root/cognition_ws/maps_new/ 2>&1

echo
echo "--- Copying to host (~/maps_new/) ---"
mkdir -p ~/maps_new
docker cp yahboom_gesture:/root/cognition_ws/maps_new/. ~/maps_new/ 2>&1
ls -la ~/maps_new/

echo
echo "======================================================"
echo "== Stopping the mapping SLAM launch (PID-based)"
echo "======================================================"
if [ -f "$PID_FILE" ] && [ -s "$PID_FILE" ]; then
    echo "Using recorded PIDs from $PID_FILE:"
    cat "$PID_FILE"
    PIDS=$(cat "$PID_FILE" | tr '\n' ' ')
    docker exec yahboom_gesture bash -c "kill -9 $PIDS 2>/dev/null"
else
    echo "WARNING: no PID file found -- falling back to pattern-matching (less reliable)"
    docker exec yahboom_gesture bash -c "
      pkill -9 -f 'ros2 launch.*slam_real.launch.py' 2>/dev/null
      pkill -9 -f 'static_transform_publisher.*laser_tf' 2>/dev/null
      pkill -9 -f 'cognition_simulation/scan_republisher' 2>/dev/null
      pkill -9 -f 'cognition_simulation/odom_imu_republisher' 2>/dev/null
      pkill -9 -f 'ekf_node' 2>/dev/null
      pkill -9 -f 'async_slam_toolbox_node' 2>/dev/null
    "
fi
sleep 3

echo
echo "--- MANDATORY VERIFICATION: checking what's actually still running ---"
STRAY=$(docker exec yahboom_gesture bash -c "ps aux | grep -E 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|slam_toolbox' | grep -v grep | grep -v defunct")
if [ -n "$STRAY" ]; then
    echo "!!! CLEANUP FAILED -- these processes are still running: !!!"
    echo "$STRAY"
    echo
    echo "Manual kill needed. Copy the PIDs (2nd column) from above and run:"
    echo "  docker exec yahboom_gesture bash -c \"kill -9 <PID1> <PID2> ...\""
else
    echo "Confirmed clean -- no mapping-session processes remain."
fi
rm -f "$PID_FILE"

echo
echo "======================================================"
echo "== Restarting cognition.service"
echo "======================================================"
sudo systemctl start cognition.service
sleep 5

echo
echo "--- Refreshing ROS2 daemon (clears stale discovery cache) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2 && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== FINAL STATUS"
echo "======================================================"
if [ -f ~/maps_new/${MAP_NAME}.pgm ] || [ -f ~/maps_new/${MAP_NAME}.png ]; then
    echo "Map saved: ~/maps_new/${MAP_NAME}.*"
else
    echo "WARNING: map file not found -- save may have failed, check output above."
fi
if [ -n "$STRAY" ]; then
    echo "CLEANUP: FAILED -- see warning above, manual action needed."
else
    echo "CLEANUP: confirmed successful."
fi
echo "Node list above should show ONLY: /brain_node /camera_pub /gesture_node /person_detection_node"
