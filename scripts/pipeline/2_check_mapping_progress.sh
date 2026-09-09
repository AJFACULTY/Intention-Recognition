#!/bin/bash
# ============================================================================
# 2_check_mapping_progress.sh
#
# Read-only. Safe to run as many times as you want WHILE driving — doesn't
# stop or touch anything. Shows current map size and how much of it has
# actually been explored (occupied/free cells), not just dimensions.
#
# Usage:
#   chmod +x 2_check_mapping_progress.sh
#   ./2_check_mapping_progress.sh
# ============================================================================

set -uo pipefail

echo "--- Current map snapshot ---"
docker exec yahboom_gesture bash -c "
source /opt/ros/humble/setup.bash
python3 << 'PYEOF'
import subprocess, re

result = subprocess.run(
    ['ros2', 'topic', 'echo', '/map', '--once', '--full-length'],
    capture_output=True, text=True, timeout=8
)
out = result.stdout

w = re.search(r'width:\s*(\d+)', out)
h = re.search(r'height:\s*(\d+)', out)
res = re.search(r'resolution:\s*([\d.]+)', out)

if not (w and h):
    print('No map message received yet — still very early, or SLAM not running.')
else:
    width, height = int(w.group(1)), int(h.group(1))
    resolution = float(res.group(1)) if res else 0.05
    print(f'Map size: {width} x {height} cells  (~{width*resolution:.1f}m x {height*resolution:.1f}m)')

    # Parse the data array to count occupied/free/unknown
    data_match = re.search(r'data:\s*\[([^\]]*)\]', out, re.DOTALL)
    if data_match:
        vals = [int(v.strip()) for v in data_match.group(1).split(',') if v.strip()]
        unknown = sum(1 for v in vals if v == -1)
        free = sum(1 for v in vals if v == 0)
        occupied = sum(1 for v in vals if v > 0)
        total = len(vals)
        explored = free + occupied
        print(f'Cells explored so far: {explored}/{total} ({100*explored/total:.1f}%)')
        print(f'  free: {free}   occupied: {occupied}   still unknown: {unknown}')
    else:
        print('(could not parse cell data — map header only)')
PYEOF
" 2>&1

echo
echo "--- SLAM still running? ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list 2>/dev/null | grep slam_toolbox" \
  && echo "Yes, slam_toolbox is active." \
  || echo "WARNING: slam_toolbox not found in node list — check 1_start_mapping.sh ran and hasn't crashed."
