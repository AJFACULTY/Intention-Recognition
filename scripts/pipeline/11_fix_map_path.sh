#!/bin/bash
# ============================================================================
# 11_fix_map_path.sh
#
# ROOT CAUSE of the failed nav2 test (found via 10_diagnose_amcl.sh):
# nav2.launch.py used os.path.expanduser('~/maps/...'), which evaluates
# INSIDE the container -- where home is /root, not /home/pi. That
# resolved to /root/maps/room_map_....yaml, a path that was never
# created or mounted in the container. map_server failed to load it,
# which aborted the ENTIRE lifecycle bringup, which is why AMCL stayed
# permanently "unconfigured" and /amcl_pose never published -- nothing
# to do with AMCL itself, timing, or localization quality.
#
# FIX: point at /root/cognition_ws/maps_new/<map>.yaml instead -- this
# path IS genuinely accessible from the container, because cognition_ws
# is actually bind-mounted (confirmed: the mapping session already wrote
# the map files there directly). Same pattern already used elsewhere in
# this project (e.g. slam_real.launch.py hardcodes an absolute
# /root/cognition_ws/... path for slam_toolbox_real.yaml).
#
# Usage:
#   chmod +x 11_fix_map_path.sh
#   ./11_fix_map_path.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

MAP_NAME="room_map_20260812_0826"
CONTAINER_MAP_PATH="/root/cognition_ws/maps_new/${MAP_NAME}.yaml"

echo "======================================================"
echo "== Confirming the map actually exists at the container path"
echo "======================================================"
docker exec yahboom_gesture ls -la "$CONTAINER_MAP_PATH" 2>&1
if ! docker exec yahboom_gesture test -f "$CONTAINER_MAP_PATH"; then
    echo "ERROR: map not found at $CONTAINER_MAP_PATH -- cannot proceed."
    echo "Check ~/cognition_ws/maps_new/ on the host for the actual filename."
    exit 1
fi
echo "Confirmed: file exists and is reachable from inside the container."

echo
echo "======================================================"
echo "== DIFF: fixing map_yaml in both launch files"
echo "======================================================"
for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
    cp "$f" "/tmp/$(basename "$f").before"
    sed -i "s|map_yaml = os.path.expanduser('~/maps/${MAP_NAME}.yaml')|map_yaml = '${CONTAINER_MAP_PATH}'|" "$f"
    echo "--- $f ---"
    diff "/tmp/$(basename "$f").before" "$f" || true
done

echo
read -p "Apply this fix and commit? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Reverting..."
    for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
        cp "/tmp/$(basename "$f").before" "$f"
    done
    echo "Reverted. No changes made."
    exit 0
fi

echo
echo "--- Verifying the change took effect ---"
ALL_OK=1
for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
    if grep -q "map_yaml = '${CONTAINER_MAP_PATH}'" "$f"; then
        echo "OK: $f"
    else
        echo "!!! FAILED: $f -- sed substitution didn't match, check manually"
        ALL_OK=0
    fi
done

if [ "$ALL_OK" -eq 0 ]; then
    echo "Aborting commit -- fix verification failed."
    exit 1
fi

git add src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py
git commit -m "Fix root cause of failed nav2 test: map_yaml path unreachable in container

Diagnosed via 10_diagnose_amcl.sh, 2026-08-14. The actual failure had
nothing to do with AMCL, localization timing, or the odom yaw fix --
map_server itself failed with 'bad file' because os.path.expanduser
('~/maps/...') evaluates inside the container, where home is /root,
not /home/pi. That path was never created/mounted, so map_server's
lifecycle transition failed, which aborted bringup of EVERY managed
node -- explaining why AMCL stayed permanently 'unconfigured' with
zero topic subscriptions, and why /amcl_pose never published, despite
no direct AMCL error.

Fixed by pointing at /root/cognition_ws/maps_new/${MAP_NAME}.yaml
instead -- genuinely reachable, since cognition_ws is bind-mounted and
the mapping session already wrote the map files there directly."

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "Ready to re-run 9_run_navigation_test.sh. This time map_server"
echo "should configure successfully, which should let the whole lifecycle"
echo "chain (including AMCL) actually activate."
