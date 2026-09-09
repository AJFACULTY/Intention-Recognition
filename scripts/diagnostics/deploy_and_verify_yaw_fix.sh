#!/bin/bash
# ============================================================================
# deploy_and_verify_yaw_fix.sh
#
# Deploys the corrected slam_real.launch.py (odom yaw now enabled in EKF)
# and verifies it by watching EKF's FUSED orientation output (/odometry/
# filtered) through a real rotation -- not just the raw /odom_raw input
# we already confirmed was good, but the actual thing SLAM will use.
#
# PREREQUISITE: copy the corrected file to the Pi first:
#   scp slam_real.launch.py pi@<pi-ip>:~/cognition_ws/slam_real.launch.py.new
#
# Usage:
#   chmod +x deploy_and_verify_yaw_fix.sh
#   ./deploy_and_verify_yaw_fix.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

NEW_FILE=~/cognition_ws/slam_real.launch.py.new
TARGET=src/cognition_simulation/launch/slam_real.launch.py

if [ ! -f "$NEW_FILE" ]; then
    echo "ERROR: $NEW_FILE not found."
    echo "Copy it from your laptop first:"
    echo "  scp slam_real.launch.py pi@<pi-ip>:~/cognition_ws/slam_real.launch.py.new"
    exit 1
fi

echo "======================================================"
echo "== DIFF: current committed version vs corrected version"
echo "======================================================"
diff "$TARGET" "$NEW_FILE" && echo "(no differences — nothing to apply)"

echo
read -p "Apply this change and run the verification test? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted. No changes made."
    exit 0
fi

echo
echo "======================================================"
echo "== Applying fix (git-tracked)"
echo "======================================================"
cp "$NEW_FILE" "$TARGET"
git add "$TARGET"
git commit -m "Fix rotational drift: enable odom yaw in EKF

Evidence gathered before this change (yaw_investigation.sh, 2026-08-10):
- History: backup files show odom yaw enabled as the standard pattern
  elsewhere in this project; no record of it being deliberately
  disabled for real hardware.
- Live data: /odom_raw orientation traced a smooth, continuous,
  correctly-behaving path through a real ~720 degree hand rotation.
- Covariance: yaw variance reports 0.0, read as a firmware reporting
  gap given the clean data trace, not a data-quality problem.

Previously EKF had NO absolute heading reference, only integrated
gyro rate -- classic dead-reckoning drift, worst during turns. This
matches the hourglass/rotated-segment pattern seen in both prior
mapping attempts. odom0_config yaw flipped False -> True; IMU angular
velocity remains enabled alongside it (standard dual-source fusion)."

echo
echo "--- Confirming container sees the updated file (bind mount check) ---"
docker exec yahboom_gesture cat /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py | diff - "$TARGET" \
    && echo "Confirmed: container sees the same updated file." \
    || echo "WARNING: container's view differs — investigate before proceeding."

echo
echo "======================================================"
echo "== LIVE VERIFICATION: watching FUSED EKF output through a rotation"
echo "======================================================"
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

echo "Launching corrected slam_real.launch.py persistently..."
docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  ros2 launch /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py > /tmp/yaw_fix_verify.log 2>&1
"
echo "Waiting 10s for nodes to come up..."
sleep 10

echo
echo "--- Confirming EKF is publishing its fused output ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /odometry/filtered" 2>&1

echo
echo ">>> ACTION NEEDED: this next check captures data for 20 seconds."
echo ">>> Wait for 'CAPTURING NOW' below, then rotate the robot ONE FULL"
echo ">>> SLOW 360-degree turn using the joystick, same as before."
echo ">>> Starting in 5 seconds..."
sleep 5

echo ">>> CAPTURING NOW — ROTATE THE ROBOT ONE FULL SLOW 360 TURN <<<"
docker exec yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  timeout 20 ros2 topic echo /odometry/filtered
" > ~/ekf_fused_yaw_capture.log 2>&1

echo
echo ">>> Capture finished. Extracting fused orientation.z / .w values,"
echo ">>> in order received:"
echo
grep -A5 "^    orientation:" ~/ekf_fused_yaw_capture.log | grep -E "z:|w:" | paste - -

echo
echo "(Compare this by eye against the earlier raw /odom_raw capture — it"
echo " should trace a similarly smooth path. If it does, EKF is genuinely"
echo " using the yaw data now, not ignoring it.)"

echo
echo "--- Also checking scan-drop rate hasn't regressed (log so far) ---"
docker exec yahboom_gesture bash -c "grep -c 'discarding message' /tmp/yaw_fix_verify.log" 2>&1

echo
echo "======================================================"
echo "== Stopping test, restoring normal operation"
echo "======================================================"
docker exec yahboom_gesture bash -c "
  pkill -9 -f 'ros2 launch.*slam_real.launch.py' 2>/dev/null
  pkill -9 -f 'static_transform_publisher.*laser_tf' 2>/dev/null
  pkill -9 -f 'cognition_simulation/scan_republisher' 2>/dev/null
  pkill -9 -f 'cognition_simulation/odom_imu_republisher' 2>/dev/null
  pkill -9 -f 'ekf_node' 2>/dev/null
  pkill -9 -f 'async_slam_toolbox_node' 2>/dev/null
"
sleep 3
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2 && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "If the fused orientation values above traced a smooth path AND node"
echo "list is back to just: /brain_node /camera_pub /gesture_node /person_detection_node"
echo "then we're ready for a third mapping drive."
