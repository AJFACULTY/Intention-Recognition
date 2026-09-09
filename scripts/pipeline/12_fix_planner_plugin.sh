#!/bin/bash
# ============================================================================
# 12_fix_planner_plugin.sh
#
# Fixes ONE confirmed bug: planner_server's GridBased plugin was specified
# as 'nav2_navfn_planner::NavfnPlanner' (C++ namespace style), but
# pluginlib's own error message showed the actual registered name is
# 'nav2_navfn_planner/NavfnPlanner' (slash style) -- not a guess, it's
# literally what the FATAL error printed as a declared/valid type.
#
# Deliberately NOT touching other '::' plugin references elsewhere in
# nav2_params.yaml (controller, costmap layers, behaviors) -- those may
# or may not have the same issue depending on how each package exports
# its plugins, and we don't have confirmed evidence for those yet. If
# any of them are also wrong, Nav2 will fail the same clear way and tell
# us the correct name, same as it just did here -- better to fix
# confirmed bugs one at a time than guess broadly.
#
# Usage:
#   chmod +x 12_fix_planner_plugin.sh
#   ./12_fix_planner_plugin.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

PARAMS_FILE=src/cognition_simulation/config/nav2_params.yaml

echo "======================================================"
echo "== Current line"
echo "======================================================"
grep -n "nav2_navfn_planner" "$PARAMS_FILE"

echo
echo "======================================================"
echo "== DIFF"
echo "======================================================"
cp "$PARAMS_FILE" /tmp/nav2_params_before_planner_fix.yaml
sed -i 's|plugin: nav2_navfn_planner::NavfnPlanner|plugin: nav2_navfn_planner/NavfnPlanner|' "$PARAMS_FILE"
diff /tmp/nav2_params_before_planner_fix.yaml "$PARAMS_FILE"

echo
read -p "Apply this fix and commit? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    cp /tmp/nav2_params_before_planner_fix.yaml "$PARAMS_FILE"
    echo "Reverted. No changes made."
    exit 0
fi

echo
echo "--- Verifying ---"
if grep -q "plugin: nav2_navfn_planner/NavfnPlanner" "$PARAMS_FILE"; then
    echo "OK: fix applied."
else
    echo "!!! FAILED: substitution didn't match -- check manually."
    exit 1
fi

git add "$PARAMS_FILE"
git commit -m "Fix planner_server plugin name: :: -> / (nav2_navfn_planner/NavfnPlanner)

pluginlib failed to load the GridBased planner with a FATAL error,
whose own message showed the correct declared type is
nav2_navfn_planner/NavfnPlanner (slash), not the C++ namespace-style
nav2_navfn_planner::NavfnPlanner that was configured. This one
failure aborted the entire lifecycle_manager bringup, which is also
why map_server successfully configuring (confirmed via log, this
session) still didn't get AMCL to activate -- one failed node blocks
the whole managed set.

Only this ONE confirmed instance fixed -- other :: plugin references
elsewhere in this file (controller, costmap layers, behaviors) were
deliberately left untouched pending their own confirmed errors, since
correctness depends on how each package exports its plugins, not a
single project-wide convention."

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "Ready to re-run 9_run_navigation_test.sh. If another plugin name is"
echo "also wrong, Nav2 will fail the same clear way and name the correct"
echo "value -- send me that error and we'll fix it the same way."
