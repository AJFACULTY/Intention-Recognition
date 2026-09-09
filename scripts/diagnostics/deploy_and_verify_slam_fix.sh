#!/bin/bash
# ============================================================================
# deploy_and_verify_slam_fix.sh
#
# Deploys the corrected slam_real.launch.py (with slam_real.launch.py.new
# already scp'd into ~/cognition_ws) and runs a captured verification test
# identical in spirit to scan 3 — so we get a real before/after comparison
# instead of assuming the fix worked.
#
# PREREQUISITE: copy the corrected file to the Pi first, e.g.:
#   scp slam_real.launch.py pi@<pi-ip>:~/cognition_ws/slam_real.launch.py.new
#
# This script:
#   1. Shows a diff against the current committed version (review before applying)
#   2. Applies it (with git tracking the change)
#   3. Stops cognition.service, runs SLAM for 30s with captured output
#   4. Reports the scan drop rate — the actual number that matters
#   5. Restarts cognition.service
#
# Usage:
#   chmod +x deploy_and_verify_slam_fix.sh
#   ./deploy_and_verify_slam_fix.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

NEW_FILE=~/cognition_ws/slam_real.launch.py.new
TARGET=src/cognition_simulation/launch/slam_real.launch.py

if [ ! -f "$NEW_FILE" ]; then
    echo "ERROR: $NEW_FILE not found."
    echo "Copy it from your machine first:"
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

echo "======================================================"
echo "== Applying fix (git-tracked)"
echo "======================================================"
cp "$NEW_FILE" "$TARGET"
git add "$TARGET"
git commit -m "Fix SLAM scan-drop: remove conflicting odom_tf static broadcaster

EKF was already publishing odom_frame -> base_footprint dynamically
(publish_tf: True). The static_transform_publisher 'odom_tf' node
was ALSO broadcasting that same frame pair, frozen at identity.
Two broadcasters racing on one frame pair caused slam_toolbox's
message filter to unreliably resolve transforms, resulting in
100% of /scan_downsampled messages being dropped (verified via
captured launch output on 2026-08-08).

Also added a 3s startup delay before slam_toolbox so it doesn't
start before EKF publishes its first transform."

echo
echo "Copying same fix into container's mounted view (should already match, since"
echo "/home/pi/cognition_ws is bind-mounted into yahboom_gesture at /root/cognition_ws)..."
docker exec yahboom_gesture cat /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py | diff - "$TARGET" \
    && echo "Confirmed: container sees the same updated file (bind mount working as expected)." \
    || echo "WARNING: container's view differs — investigate the mount before proceeding."

echo
echo "======================================================"
echo "== VERIFICATION: captured live SLAM run (self-reverting)"
echo "======================================================"
echo "Stopping cognition.service..."
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2

echo "Restarting ROS2 daemon..."
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

echo "Launching corrected slam_real.launch.py for 30s, capturing output..."
docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  timeout 30 ros2 launch /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py > /tmp/slam_fix_test.log 2>&1
"

echo "Waiting for run to complete (32s)..."
sleep 32

echo
echo "--- Node list check ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "--- SCAN DROP RATE (the number that matters) ---"
TOTAL_LINES=$(docker exec yahboom_gesture bash -c "wc -l < /tmp/slam_fix_test.log" 2>/dev/null || echo 0)
DROPPED=$(docker exec yahboom_gesture bash -c "grep -c 'discarding message because the queue is full' /tmp/slam_fix_test.log" 2>/dev/null || echo 0)
echo "Total 'dropping message' lines: $DROPPED"
if [ "$DROPPED" -eq 0 ]; then
    echo ">>> ZERO scans dropped. Fix appears to have worked."
else
    echo ">>> Scans still being dropped. Fix did NOT fully resolve the issue — needs more investigation."
fi

echo
echo "--- Registration/matching activity (evidence SLAM is actually building a map) ---"
docker exec yahboom_gesture bash -c "grep -iE 'registering sensor|scan matching|added scan|corrupted' /tmp/slam_fix_test.log" 2>&1

echo
echo "--- Last 40 lines of captured output (full context) ---"
docker exec yahboom_gesture bash -c "tail -40 /tmp/slam_fix_test.log" 2>&1

echo
echo "Restarting cognition.service to restore normal operation..."
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "If the drop count above is 0 (or near-0), the fix worked — ready to remap."
echo "If drops are still happening, DO NOT proceed to remapping yet — send me this output."
