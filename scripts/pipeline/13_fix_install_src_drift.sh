#!/bin/bash
# ============================================================================
# 13_fix_install_src_drift.sh
#
# ROOT CAUSE of the repeated identical planner error: nav2.launch.py loads
# its config via get_package_share_directory('cognition_simulation'),
# which resolves to the INSTALLED copy
# (install/cognition_simulation/share/.../nav2_params.yaml), not the
# src/ file we've been editing and committing this whole time. Our fix
# (:: -> /) landed correctly in src/ and in git, but the running system
# never saw it -- confirmed via direct diff: src/ has the fix, install/
# still has the broken version, word-for-word matching the repeated error.
#
# This is the same install/vs/src drift flagged in the very first
# workspace scan of this project. slam_real.launch.py avoided it by
# hardcoding a direct src/ path; nav2.launch.py never was.
#
# FIX (two parts):
#   1. Point nav2.launch.py at the src/ config directly (same pattern
#      slam_real.launch.py already uses for slam_toolbox_real.yaml) --
#      permanent fix, future src/ edits will always be picked up.
#   2. Also rebuild so install/ is back in sync generally -- other
#      launch files in this project (nav2_minimal.launch.py, etc.)
#      still use get_package_share_directory and would hit the same
#      class of bug on any future config edit if we don't.
#
# Usage:
#   chmod +x 13_fix_install_src_drift.sh
#   ./13_fix_install_src_drift.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

LAUNCH_FILE=src/cognition_simulation/launch/nav2.launch.py

echo "======================================================"
echo "== PART 1: point nav2.launch.py at src/ config directly"
echo "======================================================"
grep -n "params = os.path.join(share" "$LAUNCH_FILE"

cp "$LAUNCH_FILE" /tmp/nav2_launch_before_srcfix.py
sed -i "s|params = os.path.join(share, 'config', 'nav2_params.yaml')|params = '/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml'|" "$LAUNCH_FILE"

echo
echo "--- diff ---"
diff /tmp/nav2_launch_before_srcfix.py "$LAUNCH_FILE"

echo
read -p "Apply part 1 and continue to part 2 (rebuild)? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    cp /tmp/nav2_launch_before_srcfix.py "$LAUNCH_FILE"
    echo "Reverted. No changes made."
    exit 0
fi

echo
echo "--- Verifying part 1 ---"
if grep -q "params = '/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml'" "$LAUNCH_FILE"; then
    echo "OK: nav2.launch.py now points directly at src/."
else
    echo "!!! FAILED -- check manually."
    exit 1
fi

echo
echo "======================================================"
echo "== PART 2: rebuild inside the container to resync install/"
echo "======================================================"
echo "This fixes install/ for OTHER launch files that still use"
echo "get_package_share_directory (nav2_minimal.launch.py, etc.) so they"
echo "don't hit this same bug on a future config edit."
docker exec yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  cd /root/cognition_ws &&
  colcon build --symlink-install --packages-select cognition_simulation 2>&1
"

echo
echo "--- Verifying install/ now matches src/ ---"
diff <(grep -A1 "GridBased:" src/cognition_simulation/config/nav2_params.yaml) \
     <(docker exec yahboom_gesture grep -A1 "GridBased:" /root/cognition_ws/install/cognition_simulation/share/cognition_simulation/config/nav2_params.yaml) \
     && echo "OK: install/ now matches src/." \
     || echo "!!! Still differs -- rebuild may have failed, check output above."

git add "$LAUNCH_FILE"
git commit -m "Fix install/vs/src drift: nav2.launch.py now loads config directly from src/

Root cause of the repeated identical planner FATAL error: this launch
file used get_package_share_directory(), which resolves to the
INSTALLED copy of nav2_params.yaml, not src/ -- so the :: -> / plugin
fix (already committed, already correct in src/) was never actually
picked up by the running system. Confirmed via direct diff between
src/ and install/ showing the old broken value still present in
install/.

Same class of bug flagged in the original workspace scan; same
pattern slam_real.launch.py already used to avoid it (hardcoded direct
src/ path). Also rebuilt cognition_simulation package to resync
install/ generally, so other launch files still using
get_package_share_directory (e.g. nav2_minimal.launch.py) aren't
carrying the same landmine forward."

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "Ready to re-run 9_run_navigation_test.sh -- this time the plugin fix"
echo "should actually be in effect."
