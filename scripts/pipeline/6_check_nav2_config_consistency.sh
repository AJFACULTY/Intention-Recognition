#!/bin/bash
# ============================================================================
# 6_check_nav2_config_consistency.sh
#
# Read-only. Cross-checks every topic and frame name referenced in Nav2's
# config against the KNOWN GOOD set actually produced by slam_real.launch.py
# and the sensor chain -- so we catch every mismatch (not just /scan_fixed)
# before wiring anything together.
#
# Known-good reference (from slam_real.launch.py, verified working):
#   Frames: map, odom_frame, base_footprint, laser_frame
#   Topics: /scan_downsampled (fixed-timing scan)
#           /odom_raw_restamped, /imu_restamped (fixed-timing, feed EKF)
#           /odometry/filtered (EKF's FUSED output -- default topic name)
#
# Usage:
#   chmod +x 6_check_nav2_config_consistency.sh
#   ./6_check_nav2_config_consistency.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

ISSUES=0

echo "======================================================"
echo "== 1. Scan topic references in nav2_params.yaml"
echo "======================================================"
grep -n "scan_topic:\|topic: /scan" src/cognition_simulation/config/nav2_params.yaml
BAD=$(grep -c "scan_fixed" src/cognition_simulation/config/nav2_params.yaml || true)
if [ "$BAD" -gt 0 ]; then
    echo ">>> ISSUE: $BAD reference(s) to /scan_fixed, which does not exist."
    echo ">>>        Real topic is /scan_downsampled."
    ISSUES=$((ISSUES + BAD))
fi

echo
echo "======================================================"
echo "== 2. Odometry topic references"
echo "======================================================"
grep -n "odom_topic:\|odom0:" src/cognition_simulation/config/nav2_params.yaml src/cognition_simulation/launch/slam_real.launch.py 2>/dev/null
ODOM_REF=$(grep "odom_topic:" src/cognition_simulation/config/nav2_params.yaml | grep -o "/[a-zA-Z_/]*" || true)
if [ "$ODOM_REF" == "/odom_raw" ]; then
    echo ">>> NOTE: bt_navigator's odom_topic is /odom_raw -- this is the RAW,"
    echo ">>>       unfused odometry (also has the known ESP32 clock-drift"
    echo ">>>       timestamps before restamping). The corrected, fused output"
    echo ">>>       is /odometry/filtered (EKF's output). Worth considering"
    echo ">>>       whether bt_navigator should use the fused topic instead --"
    echo ">>>       this affects recovery-behavior stuck-detection accuracy,"
    echo ">>>       not core localization (AMCL doesn't use this directly)."
    ISSUES=$((ISSUES + 1))
fi

echo
echo "======================================================"
echo "== 3. Frame name consistency (map / odom / base frames)"
echo "======================================================"
echo "--- What slam_real.launch.py / EKF actually uses ---"
grep -E "'odom_frame'|'base_link_frame'|'world_frame'" src/cognition_simulation/launch/slam_real.launch.py
grep -E "map_frame:|odom_frame:|base_frame:" src/cognition_simulation/config/slam_toolbox_real.yaml

echo
echo "--- What nav2_params.yaml uses ---"
grep -E "global_frame:|robot_base_frame:|odom_frame_id:|global_frame_id:|base_frame_id:" src/cognition_simulation/config/nav2_params.yaml

echo
echo "--- Checking for mismatches ---"
WRONG_ODOM_FRAME=$(grep -cE "'odom'$|: odom$|frame_id: odom$" src/cognition_simulation/config/nav2_params.yaml || true)
WRONG_BASE_FRAME=$(grep -c "base_link" src/cognition_simulation/config/nav2_params.yaml || true)
if [ "$WRONG_ODOM_FRAME" -gt 0 ]; then
    echo ">>> ISSUE: found bare 'odom' frame reference(s) -- this project uses"
    echo ">>>        'odom_frame' (with suffix) everywhere else. Check these lines:"
    grep -nE "'odom'$|: odom$|frame_id: odom$" src/cognition_simulation/config/nav2_params.yaml
    ISSUES=$((ISSUES + WRONG_ODOM_FRAME))
fi
if [ "$WRONG_BASE_FRAME" -gt 0 ]; then
    echo ">>> ISSUE: found 'base_link' reference(s) -- this project uses"
    echo ">>>        'base_footprint' everywhere else. Check these lines:"
    grep -n "base_link" src/cognition_simulation/config/nav2_params.yaml
    ISSUES=$((ISSUES + WRONG_BASE_FRAME))
fi
if [ "$WRONG_ODOM_FRAME" -eq 0 ] && [ "$WRONG_BASE_FRAME" -eq 0 ]; then
    echo "No frame name mismatches found -- frame naming looks consistent."
fi

echo
echo "======================================================"
echo "== 4. Does nav2.launch.py itself start the sensor/transform chain?"
echo "======================================================"
NODES_STARTED=$(grep -c "package=" src/cognition_simulation/launch/nav2.launch.py)
HAS_EKF=$(grep -c "robot_localization\|ekf_node" src/cognition_simulation/launch/nav2.launch.py || true)
HAS_SCAN_REPUB=$(grep -c "scan_republisher" src/cognition_simulation/launch/nav2.launch.py || true)
HAS_LASER_TF=$(grep -c "laser_tf\|static_transform_publisher" src/cognition_simulation/launch/nav2.launch.py || true)
echo "Nodes launched directly by nav2.launch.py: $NODES_STARTED"
echo "  Includes EKF?            $([ "$HAS_EKF" -gt 0 ] && echo yes || echo NO)"
echo "  Includes scan_republisher? $([ "$HAS_SCAN_REPUB" -gt 0 ] && echo yes || echo NO)"
echo "  Includes laser_tf?       $([ "$HAS_LASER_TF" -gt 0 ] && echo yes || echo NO)"
if [ "$HAS_EKF" -eq 0 ] || [ "$HAS_SCAN_REPUB" -eq 0 ] || [ "$HAS_LASER_TF" -eq 0 ]; then
    echo ">>> ISSUE: nav2.launch.py does NOT start the sensor/transform chain."
    echo ">>>        Launched alone, it would have no scan data or transforms"
    echo ">>>        to localize against. Needs to run ALONGSIDE the same chain"
    echo ">>>        slam_real.launch.py uses (minus slam_toolbox itself, since"
    echo ">>>        AMCL replaces that role), not instead of it."
    ISSUES=$((ISSUES + 1))
fi

echo
echo "======================================================"
echo "== 5. map_saver_cli thresholds vs current map's saved yaml"
echo "======================================================"
echo "--- Current map's saved thresholds ---"
grep -E "occupied_thresh|free_thresh" ~/maps/room_map_20260812_0826.yaml 2>/dev/null
echo "--- nav2_params.yaml's own threshold assumptions (if any) ---"
grep -n "occupied_thresh\|free_thresh" src/cognition_simulation/config/nav2_params.yaml || echo "(none referenced -- map_server reads thresholds from the map's own yaml, this is fine)"

echo
echo "======================================================"
echo "== SUMMARY"
echo "======================================================"
echo "Total issues found: $ISSUES"
if [ "$ISSUES" -eq 0 ]; then
    echo "Config is internally consistent -- safe to proceed with just the"
    echo "combined-launch work, no further config edits needed."
else
    echo "Fix all of the above together in one pass before testing navigation,"
    echo "rather than discovering them one at a time during a live test."
fi
