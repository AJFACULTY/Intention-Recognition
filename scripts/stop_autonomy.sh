#!/bin/bash
# stop_autonomy.sh — Stops autonomy stack and restores factory joystick control
echo "Stopping autonomy nodes in yahboom_gesture..."
docker exec yahboom_gesture pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|brain_node|web_map_visualizer' 2>/dev/null || true

echo "Restoring factory joystick (ChassisServer in yahboom_base)..."
docker exec yahboom_base supervisorctl start ChassisServer 2>/dev/null || true

echo "Factory joystick restored. Ready for manual driving with gamepad."
