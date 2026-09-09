#!/bin/bash
# ============================================================================
# 10_diagnose_amcl.sh
#
# Focused diagnostic on why /amcl_pose never published in the last test.
# Instead of one all-or-nothing check, this verifies each link in the
# chain separately: did /initialpose actually get delivered, is scan
# data reaching AMCL at all, what does AMCL's OWN log say (never checked
# before), whether AMCL's lifecycle state is actually "active" (a
# lifecycle node can exist as a process while stuck unconfigured/inactive
# -- which would fully explain silent output with no crash), and gives
# it a longer window (45s, not 16s) before declaring anything broken.
#
# Does NOT send any navigation goal -- diagnosis only, no movement.
#
# Usage:
#   chmod +x 10_diagnose_amcl.sh
#   ./10_diagnose_amcl.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

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
  ros2 launch /root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py > /tmp/amcl_diag.log 2>&1
"

echo "Waiting 45s -- long enough for everything to fully settle, including"
echo "the internal 10s delay before /initialpose is published..."
sleep 45

echo
echo "======================================================"
echo "== CHECK 1: did /initialpose actually get published?"
echo "======================================================"
docker exec yahboom_gesture bash -c "cat /tmp/amcl_diag.log" | grep -i "initialpose" 2>&1
echo "(if nothing printed above, no mention of initialpose in the log at all)"

echo
echo "======================================================"
echo "== CHECK 2: is scan data actually reaching AMCL?"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /scan_downsampled" 2>&1
echo
echo "--- Who is subscribed to /scan_downsampled? (should include amcl) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic info /scan_downsampled -v" 2>&1

echo
echo "======================================================"
echo "== CHECK 3: AMCL's own log output (never checked before)"
echo "======================================================"
docker exec yahboom_gesture bash -c "cat /tmp/amcl_diag.log" | grep -i "amcl" | head -50

echo
echo "======================================================"
echo "== CHECK 4: /amcl_pose now, after the longer wait"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic echo /amcl_pose --once" 2>&1

echo
echo "======================================================"
echo "== CHECK 5: lifecycle state -- did AMCL actually activate?"
echo "======================================================"
echo "Nav2 nodes are lifecycle nodes -- a lifecycle node can exist as a"
echo "running process while stuck in an 'unconfigured' or 'inactive' state,"
echo "which would explain silent output with no crash or visible error."
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 lifecycle get /amcl" 2>&1

echo
echo "======================================================"
echo "== CHECK 6: any errors/warnings anywhere in the full log?"
echo "======================================================"
docker exec yahboom_gesture bash -c "cat /tmp/amcl_diag.log" | grep -iE "error|fail|exception|could not|unable" | head -30
echo "(if nothing printed above, no errors/warnings found anywhere in the log)"

echo
echo "======================================================"
echo "== Cleanup"
echo "======================================================"
PIDS=$(docker exec yahboom_gesture bash -c "ps aux | grep -E 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|/amcl ' | grep -v grep | awk '{print \$2}'" | tr '\n' ' ')
echo "Killing PIDs: $PIDS"
docker exec yahboom_gesture bash -c "kill -9 $PIDS 2>/dev/null"
sleep 3

echo "--- Verification ---"
STRAY=$(docker exec yahboom_gesture bash -c "ps aux | grep -E 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|/amcl ' | grep -v grep | grep -v defunct")
if [ -n "$STRAY" ]; then
    echo "!!! Still running: !!!"
    echo "$STRAY"
else
    echo "Confirmed clean."
fi

sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2 && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== WHAT TO LOOK FOR"
echo "======================================================"
echo "CHECK 1: nothing found -> the ExecuteProcess step in the launch file"
echo "  itself failed to run -- a launch-file bug."
echo "CHECK 2: /scan_downsampled not publishing, or 'amcl' not listed as a"
echo "  subscriber -> AMCL has no sensor data, can't localize regardless"
echo "  of initial pose."
echo "CHECK 5: lifecycle state anything other than 'active' -> AMCL exists"
echo "  as a process but was never actually activated by the lifecycle"
echo "  manager -- this would fully explain silent /amcl_pose with no"
echo "  crash or error. THIS IS THE MOST LIKELY CULPRIT to check first."
echo "CHECK 6: any explicit errors -> read these first if present."
