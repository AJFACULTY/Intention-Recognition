#!/bin/bash
# ============================================================================
# 9_run_navigation_test.sh
#
# The actual autonomous navigation test. Launches nav2.launch.py (sensor
# chain + full Nav2 stack), verifies AMCL's pose estimate looks sane
# BEFORE trusting it, sends one modest (1m) navigation goal, monitors
# execution, then cleans up with the same mandatory-verification pattern
# that worked reliably for mapping sessions.
#
# SAFETY: this makes the robot move on its own. Know your physical stop
# method (power switch is more reliable than hoping a command interrupts
# it in time) before running this. Stay close and watch it.
#
# Usage:
#   chmod +x 9_run_navigation_test.sh
#   ./9_run_navigation_test.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

echo "======================================================"
echo "== SAFETY CHECK"
echo "======================================================"
echo "This will make the robot move autonomously in a moment."
read -p "Robot positioned at mapping start point, area clear, you're ready to physically stop it if needed? [y/N] " ready
if [[ "$ready" != "y" && "$ready" != "Y" ]]; then
    echo "Aborted -- nothing started."
    exit 0
fi

echo
echo "======================================================"
echo "== Stopping cognition.service, launching nav2.launch.py"
echo "======================================================"
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  ros2 launch /root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py > /tmp/nav2_test.log 2>&1
"

echo "Waiting 16s for the full stack to come up (Nav2 nodes are timer-delayed"
echo "up to 10s internally, plus startup time)..."
sleep 16

echo
echo "--- Node list ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== CHECKPOINT: is AMCL's pose estimate sane before we trust it?"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic echo /amcl_pose --once" 2>&1

echo
echo ">>> Look at the position above. It should be reasonably close to"
echo ">>> (0, 0) -- a few meters off at most, not wildly different -- since"
echo ">>> the robot was placed at roughly the mapping start point."
echo
read -p "Does that pose look sane? Proceed with the navigation goal? [y/N] " sane
if [[ "$sane" != "y" && "$sane" != "Y" ]]; then
    echo "Stopping here -- AMCL pose looked wrong. Not sending a goal."
    echo "(Cleanup will still run below.)"
    SKIP_GOAL=1
else
    SKIP_GOAL=0
fi

if [ "$SKIP_GOAL" -eq 0 ]; then
    echo
    echo "======================================================"
    echo "== Sending a modest goal: 1.0m forward in +x, same orientation"
    echo "======================================================"
    echo ">>> WATCH THE ROBOT NOW. Be ready to physically stop it."
    sleep 3

    docker exec yahboom_gesture bash -c "
      source /opt/ros/humble/setup.bash &&
      timeout 40 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
        '{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}' \
        --feedback
    " 2>&1 | tee ~/nav_goal_result.log

    echo
    echo "--- Result summary ---"
    grep -iE "result:|status|SUCCEEDED|ABORTED|CANCELED" ~/nav_goal_result.log | tail -10
fi

echo
echo "======================================================"
echo "== Stopping test, restoring normal operation"
echo "======================================================"
docker exec yahboom_gesture bash -c "
  pkill -9 -f 'ros2 launch.*nav2.launch.py' 2>/dev/null
  pkill -9 -f 'static_transform_publisher.*laser_tf' 2>/dev/null
  pkill -9 -f 'cognition_simulation/scan_republisher' 2>/dev/null
  pkill -9 -f 'cognition_simulation/odom_imu_republisher' 2>/dev/null
  pkill -9 -f 'ekf_node' 2>/dev/null
  pkill -9 -f 'nav2_map_server' 2>/dev/null
  pkill -9 -f 'nav2_amcl' 2>/dev/null
  pkill -9 -f 'nav2_planner' 2>/dev/null
  pkill -9 -f 'nav2_controller' 2>/dev/null
  pkill -9 -f 'nav2_behaviors' 2>/dev/null
  pkill -9 -f 'nav2_bt_navigator' 2>/dev/null
  pkill -9 -f 'nav2_waypoint_follower' 2>/dev/null
  pkill -9 -f 'nav2_lifecycle_manager' 2>/dev/null
"
sleep 3

echo
echo "--- MANDATORY VERIFICATION ---"
STRAY=$(docker exec yahboom_gesture bash -c "ps aux | grep -E 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl' | grep -v grep | grep -v defunct")
if [ -n "$STRAY" ]; then
    echo "!!! CLEANUP FAILED -- still running: !!!"
    echo "$STRAY"
    echo "Manual kill needed: docker exec yahboom_gesture bash -c \"kill -9 <PIDs from 2nd column above>\""
else
    echo "Confirmed clean -- no nav2-session processes remain."
fi

echo
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2 && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
if [ "$SKIP_GOAL" -eq 1 ]; then
    echo "Goal was skipped (AMCL pose didn't look sane). Check /tmp/nav2_test.log"
    echo "on the Pi for AMCL/localization details before retrying."
else
    echo "Check the result summary above -- SUCCEEDED means it planned and"
    echo "drove to the goal autonomously. Any other status: send me the full"
    echo "~/nav_goal_result.log output."
fi
