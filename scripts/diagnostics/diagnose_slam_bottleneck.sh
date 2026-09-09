#!/bin/bash
# ============================================================================
# diagnose_slam_bottleneck.sh
#
# Measures two things directly, instead of guessing from drop patterns:
#   1. CPU/memory usage of the slam_toolbox process over time (is the Pi's
#      processor falling behind?)
#   2. The actual latency gap for each dropped scan — the difference
#      between when a scan was timestamped and when slam_toolbox's log
#      line about dropping it was written (is the gap growing over time,
#      meaning a backlog is building up?)
#
# Self-reverting: stops cognition.service, runs the test, restarts it after.
#
# Usage:
#   chmod +x diagnose_slam_bottleneck.sh
#   ./diagnose_slam_bottleneck.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

DURATION=60
LOGFILE_CONTAINER=/tmp/slam_diag.log
CPU_LOG=~/slam_cpu_samples.log

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

sleep 5  # let the process actually start before we try to find its PID

echo "======================================================"
echo "== Sampling slam_toolbox CPU/memory every 5s for ${DURATION}s"
echo "======================================================"
> "$CPU_LOG"
SAMPLES=$((DURATION / 5))
for i in $(seq 1 $SAMPLES); do
    TS=$(date +%s)
    SAMPLE=$(docker exec yahboom_gesture bash -c "ps aux | grep async_slam_toolbox_node | grep -v grep" 2>/dev/null)
    if [ -n "$SAMPLE" ]; then
        CPU=$(echo "$SAMPLE" | awk '{print $3}')
        MEM_RSS=$(echo "$SAMPLE" | awk '{print $6}')
        echo "t=${i}x5s  cpu=${CPU}%  rss=${MEM_RSS}KB" | tee -a "$CPU_LOG"
    else
        echo "t=${i}x5s  (process not found — may have exited or not started yet)" | tee -a "$CPU_LOG"
    fi
    sleep 5
done

echo
echo "Also checking overall Pi CPU load during this window..."
docker exec yahboom_gesture bash -c "uptime" 2>&1

echo
echo "======================================================"
echo "== ANALYSIS 1: CPU/memory trend over the run"
echo "======================================================"
cat "$CPU_LOG"
echo
echo "(If RSS climbs steadily and never plateaus: backlog is accumulating in memory,"
echo " consistent with a queue that never drains. If CPU stays near 100% throughout:"
echo " the Ceres solver can't keep up in real time on this hardware.)"

echo
echo "======================================================"
echo "== ANALYSIS 2: actual latency gap per dropped scan"
echo "======================================================"
echo "Extracting: (log line time) minus (scan's own timestamp) for each drop..."
docker exec yahboom_gesture bash -c "
python3 << 'PYEOF'
import re

with open('${LOGFILE_CONTAINER}') as f:
    lines = f.readlines()

gaps = []
for line in lines:
    if 'discarding message' not in line:
        continue
    # log line timestamp, e.g. [1786283405.734904493]
    m_log = re.search(r'\[(\d+\.\d+)\]', line)
    # scan's own timestamp, e.g. 'at time 1786283405.656'
    m_scan = re.search(r'at time (\d+\.\d+)', line)
    if m_log and m_scan:
        log_t = float(m_log.group(1))
        scan_t = float(m_scan.group(1))
        gaps.append(log_t - scan_t)

if not gaps:
    print('No drop events found to analyze.')
else:
    n = len(gaps)
    avg = sum(gaps) / n
    print(f'Total drops analyzed: {n}')
    print(f'Gap  min: {min(gaps):.3f}s   max: {max(gaps):.3f}s   avg: {avg:.3f}s')
    print()
    print('Gap trend across the run (first 10 vs last 10 drops):')
    first10 = gaps[:10]
    last10 = gaps[-10:]
    print(f'  First 10 drops — avg gap: {sum(first10)/len(first10):.3f}s')
    print(f'  Last  10 drops — avg gap: {sum(last10)/len(last10):.3f}s')
    if (sum(last10)/len(last10)) > (sum(first10)/len(first10)) * 1.5:
        print('  >>> Gap is GROWING significantly — backlog is building up over time.')
    else:
        print('  >>> Gap is roughly STABLE — not a growing backlog, likely a fixed timing offset instead.')
PYEOF
" 2>&1

echo
echo "======================================================"
echo "== Restarting cognition.service"
echo "======================================================"
sudo systemctl start cognition.service
sleep 5
docker exec yahboom_gesture bash -c "source /opt/ros/humble/setup.bash && ros2 node list" 2>&1

echo
echo "======================================================"
echo "== HOW TO READ THIS"
echo "======================================================"
echo "CPU near 100% the whole time + growing gap  -> Pi is too slow for this"
echo "  workload as configured; fix = reduce load (lower scan rate further,"
echo "  reduce solver work) or accept slower/coarser mapping."
echo "CPU moderate + growing gap                   -> a genuine backlog/queue"
echo "  bug, not a hardware limit; fix = tune queue size / rates in config."
echo "CPU moderate + STABLE gap                     -> a fixed timing offset"
echo "  somewhere (e.g. transform_timeout too tight); fix = small config tweak."
