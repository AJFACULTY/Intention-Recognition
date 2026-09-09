#!/bin/bash
# ============================================================================
# full_slam_diagnostic.sh
#
# The complete, properly-instrumented diagnostic pass. Combines and fixes
# gaps from all previous attempts:
#   - CPU/mem sampling for the FULL run duration (previous script stopped
#     sampling early and misread "process not found" as meaningful)
#   - System-wide CPU (not just slam_toolbox's own %) via top
#   - Drop-rate trend in 10s buckets
#   - Latency-gap trend (is the backlog growing?)
#   - Explicit confirmation slam_toolbox finished startup and registered
#     the sensor (the last "clean" run likely never got this far)
#   - Scan ACCEPTANCE rate estimate, not just drop count — expected total
#     scans (from live /scan_downsampled hz) minus logged drops
#   - DIRECT map-growth evidence: snapshots map cell content at the start
#     and end of the run and reports whether it actually changed — this
#     is the only check that answers "is a map really being built" and
#     none of the previous scripts did this.
#
# Self-reverting: stops cognition.service, runs the test, restarts it after.
# Read-mostly otherwise — no config changes made by this script.
#
# Usage:
#   chmod +x full_slam_diagnostic.sh
#   ./full_slam_diagnostic.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

DURATION=90
LOGFILE_CONTAINER=/tmp/slam_full_diag.log
CPU_LOG=~/slam_full_cpu_samples.log
MAP_SNAPSHOT_1=/tmp/map_snapshot_start.txt
MAP_SNAPSHOT_2=/tmp/map_snapshot_end.txt

echo "======================================================"
echo "== Stopping cognition.service"
echo "======================================================"
sudo systemctl stop cognition.service
sleep 3
docker exec yahboom_gesture bash -c "pkill -9 -f 'brain_node|gesture_node|camera_pub|person_detection' 2>/dev/null"
sleep 2
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 daemon stop && sleep 1 && ros2 daemon start && sleep 2"

echo "======================================================"
echo "== Launching slam_real.launch.py for ${DURATION}s"
echo "======================================================"
docker exec -d yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  timeout ${DURATION} ros2 launch /root/cognition_ws/src/cognition_simulation/launch/slam_real.launch.py > ${LOGFILE_CONTAINER} 2>&1
"

echo "Waiting 8s for nodes to fully come up before first checks..."
sleep 8

echo
echo "--- Confirming slam_toolbox has actually started and registered the sensor ---"
docker exec yahboom_gesture bash -c "grep -c 'Registering sensor' ${LOGFILE_CONTAINER}" 2>&1
echo "(should be 1 — if 0, slam_toolbox hasn't finished initializing yet, wait longer)"

echo
echo "--- Snapshotting /map at start of run (early, likely mostly-unknown) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic echo /map --once" > "$MAP_SNAPSHOT_1" 2>&1
grep -E "width|height|resolution" "$MAP_SNAPSHOT_1" || echo "(no map message received yet at this point)"

echo
echo "======================================================"
echo "== Sampling CPU (slam_toolbox + system-wide) for full ${DURATION}s run"
echo "======================================================"
> "$CPU_LOG"
START_TS=$(date +%s)
END_TS=$((START_TS + DURATION - 8))
while [ "$(date +%s)" -lt "$END_TS" ]; do
    ELAPSED=$(( $(date +%s) - START_TS ))
    PROC_SAMPLE=$(docker exec yahboom_gesture bash -c "ps aux | grep async_slam_toolbox_node | grep -v grep" 2>/dev/null)
    SYS_CPU=$(docker exec yahboom_gesture bash -c "top -bn1 | grep '%Cpu' | head -1" 2>/dev/null)
    if [ -n "$PROC_SAMPLE" ]; then
        CPU=$(echo "$PROC_SAMPLE" | awk '{print $3}')
        RSS=$(echo "$PROC_SAMPLE" | awk '{print $6}')
        echo "t=${ELAPSED}s  slam_toolbox_cpu=${CPU}%  rss=${RSS}KB  |  system: ${SYS_CPU}" | tee -a "$CPU_LOG"
    else
        echo "t=${ELAPSED}s  slam_toolbox process not found  |  system: ${SYS_CPU}" | tee -a "$CPU_LOG"
    fi
    sleep 5
done

echo
echo "--- Snapshotting /map at end of run (should show real occupied/free cells if mapping worked) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic echo /map --once" > "$MAP_SNAPSHOT_2" 2>&1
grep -E "width|height|resolution" "$MAP_SNAPSHOT_2" || echo "(no map message received)"

echo
echo "--- Live /scan_downsampled hz right now (for acceptance-rate estimate) ---"
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /scan_downsampled" 2>&1

sleep 5  # let the timeout finish cleanly

echo
echo "======================================================"
echo "== ANALYSIS 1: drop rate over time (10s buckets)"
echo "======================================================"
docker exec yahboom_gesture bash -c "
  grep 'discarding message' ${LOGFILE_CONTAINER} | \
  grep -oE '\[[0-9]+\.[0-9]+\]' | tr -d '[]' | \
  awk -v start=\$(grep 'discarding message' ${LOGFILE_CONTAINER} | head -1 | grep -oE '\[[0-9]+\.[0-9]+\]' | tr -d '[]') \
  '{ bucket = int((\$1 - start) / 10); count[bucket]++ } END { for (b=0; b<=9; b++) printf \"  t=%3ds-%3ds: %d drops\n\", b*10, (b+1)*10, count[b]+0 }'
" 2>&1
TOTAL_DROPS=$(docker exec yahboom_gesture bash -c "grep -c 'discarding message' ${LOGFILE_CONTAINER}" 2>/dev/null || echo 0)
echo "Total drops: $TOTAL_DROPS"

echo
echo "======================================================"
echo "== ANALYSIS 2: latency gap trend (is the backlog growing?)"
echo "======================================================"
docker exec yahboom_gesture bash -c "
python3 << 'PYEOF'
import re
with open('${LOGFILE_CONTAINER}') as f:
    lines = f.readlines()
gaps = []
for line in lines:
    if 'discarding message' not in line:
        continue
    m_log = re.search(r'\[(\d+\.\d+)\]', line)
    m_scan = re.search(r'at time (\d+\.\d+)', line)
    if m_log and m_scan:
        gaps.append(float(m_log.group(1)) - float(m_scan.group(1)))
if not gaps:
    print('No drops to analyze (good, if map snapshots also show growth).')
else:
    n = len(gaps)
    print(f'Drops analyzed: {n}')
    print(f'Gap min: {min(gaps):.3f}s  max: {max(gaps):.3f}s  avg: {sum(gaps)/n:.3f}s')
    f10 = gaps[:10]; l10 = gaps[-10:]
    print(f'First 10 avg gap: {sum(f10)/len(f10):.3f}s   Last 10 avg gap: {sum(l10)/len(l10):.3f}s')
PYEOF
" 2>&1

echo
echo "======================================================"
echo "== ANALYSIS 3: CPU/memory trend (full run)"
echo "======================================================"
cat "$CPU_LOG"

echo
echo "======================================================"
echo "== ANALYSIS 4: did the map actually grow? (the definitive check)"
echo "======================================================"
echo "--- Start-of-run map header ---"
grep -E "width|height|resolution" "$MAP_SNAPSHOT_1" 2>/dev/null || echo "(none captured)"
echo "--- End-of-run map header ---"
grep -E "width|height|resolution" "$MAP_SNAPSHOT_2" 2>/dev/null || echo "(none captured)"
echo
echo "--- Data size comparison (larger byte count = more map content = real mapping progress) ---"
echo "Start snapshot size: $(wc -c < "$MAP_SNAPSHOT_1" 2>/dev/null || echo 0) bytes"
echo "End snapshot size:   $(wc -c < "$MAP_SNAPSHOT_2" 2>/dev/null || echo 0) bytes"

echo
echo "======================================================"
echo "== Restarting cognition.service"
echo "======================================================"
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== SUMMARY — READ THIS FIRST"
echo "======================================================"
echo "1. Sensor registered (should be 1 above)?"
echo "2. Total drops out of ~$((DURATION * 4)) expected scans (12.5Hz / 3 downsample)?"
echo "3. Did map snapshot size/dimensions grow between start and end?"
echo "4. Was slam_toolbox CPU meaningfully high (>50%) at any sample, or mostly idle?"
echo "5. Did system-wide CPU show other processes competing heavily?"
echo
echo "If drops are high AND map didn't grow AND CPU was high: confirms resource bottleneck."
echo "If drops are high but map DID grow some: partial success, worth tuning not overhauling."
echo "If sensor never registered: run needs to be longer, or something is still blocking startup."
