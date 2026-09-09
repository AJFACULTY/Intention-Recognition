#!/bin/bash
# ============================================================================
# 5_wire_nav2_to_new_map.sh  (v2 -- fixes a real bug in v1)
#
# BUG IN v1: it searched for the literal placeholder text 'sim_room.yaml'.
# That text only existed the FIRST time this script ran; every run after
# that, the files already pointed at a real (but possibly outdated) map
# name, so the literal search matched nothing and silently did nothing --
# no error, no commit, files left pointing at whatever they had before.
# This is exactly why last night's "successful-looking" run actually left
# both files pointing at the OLD drifted map (room_map_20260810_0452)
# instead of the new clean one (room_map_20260812_0826).
#
# FIX: use a regex that matches ANY current room_map_*.yaml reference,
# not a one-time-only literal. Safe to re-run any number of times,
# always updates to whatever the newest saved map actually is.
#
# Usage:
#   chmod +x 5_wire_nav2_to_new_map.sh
#   ./5_wire_nav2_to_new_map.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

LATEST_YAML=$(ls -t ~/maps_new/*.yaml 2>/dev/null | head -1)
if [ -z "$LATEST_YAML" ]; then
    LATEST_YAML=$(ls -t ~/cognition_ws/maps_new/*.yaml 2>/dev/null | head -1)
fi
if [ -z "$LATEST_YAML" ]; then
    echo "ERROR: no saved map .yaml found in ~/maps_new/. Run 3_save_map_and_stop.sh first."
    exit 1
fi

MAP_BASENAME=$(basename "$LATEST_YAML" .yaml)
echo "Newest available map: ${MAP_BASENAME}"

echo
echo "======================================================"
echo "== Copying map into ~/maps/ (alongside existing ones)"
echo "======================================================"
mkdir -p ~/maps
cp "$LATEST_YAML" ~/maps/
cp "$(dirname "$LATEST_YAML")/${MAP_BASENAME}.pgm" ~/maps/ 2>/dev/null || \
  cp "$(dirname "$LATEST_YAML")/${MAP_BASENAME}.png" ~/maps/ 2>/dev/null
ls -la ~/maps/${MAP_BASENAME}.*

echo
echo "======================================================"
echo "== CURRENT vs PROPOSED -- what each file actually says right now"
echo "======================================================"
CHANGED=0
for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
    CURRENT=$(grep -oE "room_map_[0-9_]+\.yaml|sim_room\.yaml" "$f" | head -1)
    echo "--- $f ---"
    echo "  currently points at: ${CURRENT:-<not found -- unexpected, check file manually>}"
    if [ "$CURRENT" == "${MAP_BASENAME}.yaml" ]; then
        echo "  already correct -- no change needed"
    else
        echo "  will change to:      ${MAP_BASENAME}.yaml"
        CHANGED=1
    fi
done

if [ "$CHANGED" -eq 0 ]; then
    echo
    echo "Both files already point at the newest map. Nothing to do."
    exit 0
fi

echo
read -p "Apply this change to both launch files? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted. Map was copied to ~/maps/ but launch files unchanged."
    exit 0
fi

echo
echo "======================================================"
echo "== Applying (git-tracked)"
echo "======================================================"
for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
    # Matches whichever is currently there -- an old room_map_*.yaml OR
    # the original sim_room.yaml placeholder. Two separate substitutions
    # so it works regardless of which one is present.
    sed -i "s|room_map_[0-9_]*\.yaml|${MAP_BASENAME}.yaml|" "$f"
    sed -i "s|sim_room\.yaml|${MAP_BASENAME}.yaml|" "$f"
    echo "Updated: $f"
    grep "map_yaml = " "$f"
done

echo
echo "--- Verifying the change actually took effect ---"
ALL_OK=1
for f in src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py; do
    if grep -q "${MAP_BASENAME}.yaml" "$f"; then
        echo "  OK: $f now points at ${MAP_BASENAME}.yaml"
    else
        echo "  !!! FAILED: $f does NOT contain ${MAP_BASENAME}.yaml -- manual fix needed"
        ALL_OK=0
    fi
done

if [ "$ALL_OK" -eq 0 ]; then
    echo
    echo "ABORTING commit -- at least one file failed verification. Fix manually before committing."
    exit 1
fi

git add src/cognition_simulation/launch/nav2.launch.py src/cognition_simulation/launch/nav2_minimal.launch.py
git commit -m "Point Nav2 launch files at real map (${MAP_BASENAME})

Supersedes an earlier attempt (v1 of this script) that used a
one-time-only literal search for 'sim_room.yaml' -- that placeholder
no longer existed after the first run, so subsequent runs silently
did nothing, leaving both files pointing at an outdated (and in this
case, drift-affected) map. This version matches any current
room_map_*.yaml reference so it works correctly on every run, and
verifies the substitution actually took effect before committing."

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
echo "Nav2 is now configured to use: ~/maps/${MAP_BASENAME}.yaml"
echo "Verify any time with:"
echo "  grep map_yaml ~/cognition_ws/src/cognition_simulation/launch/nav2.launch.py"
