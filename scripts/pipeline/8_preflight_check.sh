#!/bin/bash
# ============================================================================
# 8_preflight_check.sh
#
# Quick, read-only checks before actually launching nav2.launch.py for the
# first time with the new sensor-chain additions:
#   1. Is the new launch file syntactically valid Python?
#   2. Does the container see the same updated files as the host?
#   3. Does the map file it references actually exist on disk?
#
# Usage:
#   chmod +x 8_preflight_check.sh
#   ./8_preflight_check.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

LAUNCH_FILE=src/cognition_simulation/launch/nav2.launch.py
PARAMS_FILE=src/cognition_simulation/config/nav2_params.yaml

echo "======================================================"
echo "== 1. Python syntax check on nav2.launch.py"
echo "======================================================"
python3 -c "
import ast
try:
    with open('${LAUNCH_FILE}') as f:
        ast.parse(f.read())
    print('OK: file parses as valid Python.')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit(1)
"

echo
echo "======================================================"
echo "== 2. Container sees the same files as host?"
echo "======================================================"
docker exec yahboom_gesture cat /root/cognition_ws/${LAUNCH_FILE} | diff - "$LAUNCH_FILE" \
    && echo "OK: nav2.launch.py matches in container." \
    || echo "MISMATCH -- investigate before launching."
docker exec yahboom_gesture cat /root/cognition_ws/${PARAMS_FILE} | diff - "$PARAMS_FILE" \
    && echo "OK: nav2_params.yaml matches in container." \
    || echo "MISMATCH -- investigate before launching."

echo
echo "======================================================"
echo "== 3. Does the referenced map file actually exist?"
echo "======================================================"
grep "map_yaml = " "$LAUNCH_FILE"
MAP_PATH=$(grep "map_yaml = " "$LAUNCH_FILE" | grep -oE "~/maps/[a-zA-Z0-9_.]+\.yaml")
EXPANDED_PATH="${MAP_PATH/#\~/$HOME}"
if [ -f "$EXPANDED_PATH" ]; then
    echo "OK: $EXPANDED_PATH exists."
    ls -la "$EXPANDED_PATH" "${EXPANDED_PATH%.yaml}.pgm" 2>/dev/null
else
    echo "!!! MISSING: $EXPANDED_PATH does not exist -- map_server will fail to start."
fi

echo
echo "======================================================"
echo "== SUMMARY"
echo "======================================================"
echo "If all three checks above show OK, we're ready to launch the actual"
echo "navigation test."
echo
echo "REMINDER (not a script check -- a physical one): place the robot at"
echo "roughly the same position and facing direction it was in when"
echo "1_start_mapping.sh was run for room_map_20260812_0826, since"
echo "initial_pose_cmd assumes the robot starts at map origin (0,0,0)."
