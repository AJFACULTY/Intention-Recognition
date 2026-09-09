#!/bin/bash
# ============================================================================
# verify_slam_fix_extended.sh
#
# Longer (100s) captured SLAM run to see whether the scan-drop rate
# converges to zero over time, or plateaus at some nonzero rate.
# Fixes two issues from the first verification pass:
#   1. Judges by TREND (bucketed over time), not a single total count.
#   2. Checks node list WHILE SLAM is running, not after it's exited.
#
# Self-reverting: stops cognition.service, runs the test, restarts it
# automatically at the end regardless of outcome.
#
# Usage:
#   chmod +x verify_slam_fix_extended.sh
#   ./verify_slam_fix_extended.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

DURATION=100
LOGFILE_CONTAINER=/tmp/slam_fix_extended.log

echo "======================================================"
echo "== Stopping cognition.service"
echo "======================================================"
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2

echo "======================================================"
echo "== Restarting ROS2 daemon"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

echo "======================================================"
echo "== Launching slam_real.launch.py for ${DURATION}s"
echo "======================================================"
docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  timeout ${DURATION} ros2 launch /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py > ${LOGFILE_CONTAINER} 2>&1
"

echo "Waiting 15s for nodes to come up..."
sleep 15

echo
echo "--- Node list AT 15s (SLAM should still be running now) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "--- Live /map hz check (5s sample, taken mid-run) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /map" 2>&1

echo
echo "--- Live transform check, odom_frame -> base_footprint (mid-run) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 run tf2_ros tf2_echo odom_frame base_footprint" 2>&1 | head -6

echo
echo "Waiting for remaining run time to finish..."
sleep $((DURATION - 15 + 3))

echo
echo "======================================================"
echo "== ANALYSIS: drop rate over time (10-second buckets)"
echo "======================================================"
docker exec yahboom_gesture bash -c "
  grep 'discarding message' ${LOGFILE_CONTAINER} | \
  grep -oE '\[[0-9]+\.[0-9]+\]' | tr -d '[]' | \
  awk -v start=\$(grep 'discarding message' ${LOGFILE_CONTAINER} | head -1 | grep -oE '\[[0-9]+\.[0-9]+\]' | tr -d '[]') \
  '{ bucket = int((\$1 - start) / 10); count[bucket]++ } END { for (b=0; b<=10; b++) printf \"  t=%3ds-%3ds: %d drops\n\", b*10, (b+1)*10, count[b]+0 }'
" 2>&1

echo
echo "--- Total drops over full ${DURATION}s run ---"
TOTAL_DROPS=$(docker exec yahboom_gesture bash -c "grep -c 'discarding message' ${LOGFILE_CONTAINER}" 2>/dev/null || echo 0)
echo "Total: $TOTAL_DROPS"

echo
echo "--- odom_imu_republisher relay counts (confirms data actually flowing throughout) ---"
docker exec yahboom_gesture bash -c "grep 'relayed' ${LOGFILE_CONTAINER}" 2>&1

echo
echo "--- Any scan-matching / registration activity beyond initial sensor registration? ---"
docker exec yahboom_gesture bash -c "grep -iE 'registering sensor|scan matching|laser scan' ${LOGFILE_CONTAINER}" 2>&1

echo
echo "--- Last 30 lines (final state of the run) ---"
docker exec yahboom_gesture bash -c "tail -30 ${LOGFILE_CONTAINER}" 2>&1

echo
echo "======================================================"
echo "== Restarting cognition.service"
echo "======================================================"
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== HOW TO READ THE BUCKET TABLE ABOVE"
echo "======================================================"
echo "If drop counts trend DOWN toward 0 across the buckets: fix is working,"
echo "  just needed settle time — safe to proceed to remapping."
echo "If drop counts stay roughly FLAT/nonzero across all buckets: there's a"
echo "  smaller secondary issue (e.g. message_filter_queue_size tuning) —"
echo "  send this output back before remapping."
echo "If /map hz check above showed a rate AND tf2_echo showed live nonzero"
echo "  values (not stuck at translation [0,0,0]): strong sign it's working."
