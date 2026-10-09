#!/bin/bash
# ==============================================================================
# launch_offline_visualizer.sh — Real-Time Offline Nav2 & Visualizer Testbed
# Runs 100% locally on workstation without physical robot powered on.
# ==============================================================================

# Flush any existing visualizer or mock nodes
pkill -f 'web_map_visualizer.py' 2>/dev/null || true
pkill -f 'mock_navigation_simulator.py' 2>/dev/null || true
sleep 1

# Source ROS 2 environment (without set -e)
set +e
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
elif [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

echo "=================================================================="
echo "    LAUNCHING OFFLINE RVIZ-EQUIVALENT WEB NAVIGATION TESTBED"
echo "=================================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Start Mock Navigation Simulator
echo "[1/2] Starting Mock Navigation Simulator (Map, Costmap, AMCL, LiDAR, Paths)..."
python3 "$SCRIPT_DIR/mock_navigation_simulator.py" > /tmp/mock_nav.log 2>&1 &
MOCK_PID=$!

sleep 1

# 2. Start Upgraded Web Map Visualizer
echo "[2/2] Starting RViz-Equivalent Web Visualizer on port 8080..."
python3 "$SCRIPT_DIR/web_map_visualizer.py" > /tmp/web_vis.log 2>&1 &
VIS_PID=$!

sleep 2

echo ""
echo "=================================================================="
echo "  >> SUCCESS! LIVE DASHBOARD READY AT:"
echo "     http://localhost:8080"
echo "     http://127.0.0.1:8080"
echo "=================================================================="
echo "Press Ctrl+C to terminate the offline simulation at any time."

trap "echo 'Stopping offline simulation...'; kill $MOCK_PID $VIS_PID 2>/dev/null || true; exit 0" INT TERM

wait $VIS_PID
