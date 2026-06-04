#!/bin/bash
# launch_dashboard.sh — Launches Web Dashboard ROS Bridge & Opens UI in Browser

echo "================================================================"
echo "    COGNITION ROBOTICS — OPERATOR WEB DASHBOARD LAUNCHER"
echo "================================================================"

# Set ROS 2 environment for laptop
export ROS_DOMAIN_ID=20
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
. /opt/ros/jazzy/setup.bash 2>/dev/null || . /opt/ros/humble/setup.bash 2>/dev/null

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting rosbridge_websocket (:9090) and web_video_server (:8080) on Domain 20..."
ros2 launch "$WS_DIR/launch/dashboard.launch.py" &
BRIDGE_PID=$!

sleep 2

DASHBOARD_URL="file://$WS_DIR/cognition_dashboard/web/index.html"
echo ">> Opening Web Dashboard in browser: $DASHBOARD_URL"

xdg-open "$DASHBOARD_URL" 2>/dev/null || firefox "$DASHBOARD_URL" 2>/dev/null || chromium-browser "$DASHBOARD_URL" 2>/dev/null || echo "Open in browser: $DASHBOARD_URL"

echo ""
echo "Press Ctrl+C to shut down dashboard server."
trap "kill -9 $BRIDGE_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait $BRIDGE_PID
