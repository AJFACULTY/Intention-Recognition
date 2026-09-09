#!/bin/bash
# ============================================================================
# check_scan_data_flow.sh
#
# Read-only. Checks whether /scan (the raw laser topic from the ESP32 via
# micro-ROS) is actually publishing right now, and looks at the micro-ROS
# agent's own log for any disconnects/errors around the last test window.
# Does NOT stop or restart any services — /scan comes from micro_ros_agent
# .service, which runs independently of cognition.service.
#
# Usage:
#   chmod +x check_scan_data_flow.sh
#   ./check_scan_data_flow.sh
# ============================================================================

set -uo pipefail

echo "======================================================"
echo "== 1. micro_ros_agent.service status (is it even up?)"
echo "======================================================"
sudo systemctl status micro_ros_agent --no-pager | head -10

echo
echo "======================================================"
echo "== 2. Serial device present?"
echo "======================================================"
ls -la /dev/ttyUSB0 2>&1

echo
echo "======================================================"
echo "== 3. Is /scan publishing RIGHT NOW? (10s live check)"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 10 ros2 topic hz /scan" 2>&1

echo
echo "======================================================"
echo "== 4. micro_ros_agent log — last 15 minutes (errors/disconnects?)"
echo "======================================================"
sudo journalctl -u micro_ros_agent --since "15 minutes ago" --no-pager | grep -iE "error|disconnect|timeout|fail|reconnect|lost" | tail -40
echo "(if nothing printed above, no errors/disconnects found in that window)"

echo
echo "======================================================"
echo "== 5. micro_ros_agent log — last 30 lines regardless (general health)"
echo "======================================================"
sudo journalctl -u micro_ros_agent --no-pager | tail -30

echo
echo "======================================================"
echo "== 6. Raw /odom_raw and /imu — also from the ESP32, same path as /scan"
echo "======================================================"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /odom_raw" 2>&1
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /imu" 2>&1

echo
echo "======================================================"
echo "== HOW TO READ THIS"
echo "======================================================"
echo "If /scan, /odom_raw, /imu ALL show a live hz rate right now: the ESP32"
echo "  link is healthy. The zero-drop run was probably a real, if fragile,"
echo "  success — worth re-testing to confirm it repeats."
echo "If /scan shows 'does not appear to be published' or times out: there's"
echo "  a real ESP32/serial connectivity issue, separate from the SLAM"
echo "  transform bug — the zero-drop run was a silent data outage, not a fix."
echo "If micro_ros_agent log shows errors/disconnects: that confirms it and"
echo "  tells us roughly when it happened."
