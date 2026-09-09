#!/bin/bash
# ============================================================================
# yaw_investigation.sh
#
# Three separate, explicit checks. Read-only — no services stopped, no
# config changed, nothing restarted. Safe to run at any time.
#
# CHECK 1: Search project history for any prior mention of odom yaw, IMU
#          orientation, or related fixes — to see if disabling odom yaw
#          in EKF was a deliberate decision with a reason behind it, or
#          just inherited/copy-pasted.
#
# CHECK 2: Capture /odom_raw continuously for 20 seconds while you
#          physically rotate the robot one full 360° turn by hand (using
#          the joystick), so we see the actual curve of the yaw value
#          through the whole rotation — not just a few disconnected
#          snapshots.
#
# CHECK 3: Extract odom's own reported confidence (covariance) specifically
#          for its yaw estimate, to see if the sensor itself is flagging
#          low confidence in that value.
#
# Usage:
#   chmod +x yaw_investigation.sh
#   ./yaw_investigation.sh
# ============================================================================

set -uo pipefail
cd ~/cognition_ws || { echo "cognition_ws not found"; exit 1; }

echo "======================================================"
echo "== CHECK 1: History search — was disabling odom yaw deliberate?"
echo "======================================================"

echo
echo "--- 1a. git log: any commit mentioning yaw, odom, orientation, IMU? ---"
git log --all --oneline --grep="yaw" --grep="odom" --grep="orientation" --grep="IMU" -i 2>&1
echo "(if nothing printed above, no commit messages mention these terms —"
echo " remember this repo's history only starts from our baseline commit,"
echo " so earlier changes made before we set up git won't show here)"

echo
echo "--- 1b. bash history: any commands involving yaw/orientation config? ---"
grep -iE "yaw|orientation|odom0_config|imu0_config" ~/.bash_history 2>/dev/null | tail -30
echo "(if nothing printed above, no matching commands in shell history)"

echo
echo "--- 1c. backup files: do any OLDER versions of slam_real.launch.py or"
echo "        ekf.yaml have odom yaw ENABLED, suggesting it was turned off"
echo "        at some point rather than never set up? ---"
find ~/cognition_ws -iname "*.backup*" -o -iname "*.bak*" -o -iname "*.orig*" 2>/dev/null | \
  xargs grep -l "odom0_config\|imu0_config" 2>/dev/null

echo
echo "--- 1d. If any backup files were found above, show their odom0_config lines ---"
for f in $(find ~/cognition_ws -iname "*.backup*" -o -iname "*.bak*" -o -iname "*.orig*" 2>/dev/null); do
    if grep -q "odom0_config" "$f" 2>/dev/null; then
        echo "=== $f ==="
        grep -A2 "odom0_config" "$f"
        echo
    fi
done

echo
echo "======================================================"
echo "== CHECK 2: Live continuous odom yaw capture through a real 360° turn"
echo "======================================================"
echo
echo ">>> ACTION NEEDED: this check captures data for 20 seconds starting now."
echo ">>> Wait for the 'CAPTURING NOW' message below, then use the joystick"
echo ">>> to rotate the robot ONE FULL SLOW 360-degree turn, all in the SAME"
echo ">>> direction, trying to take close to the full 20 seconds to do it."
echo ">>> Starting in 5 seconds..."
sleep 5

echo ">>> CAPTURING NOW — ROTATE THE ROBOT ONE FULL SLOW 360 TURN <<<"
docker exec yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  timeout 20 ros2 topic echo /odom_raw
" > ~/odom_yaw_capture.log 2>&1

echo
echo ">>> Capture finished. Extracting the orientation.z and orientation.w"
echo ">>> values in the order they were received, so we can see the actual"
echo ">>> path the value took through the turn (not just start/end points):"
echo
grep -A5 "^    orientation:" ~/odom_yaw_capture.log | grep -E "z:|w:" | paste - -

echo
echo "(Read this top to bottom -- it should move smoothly through a range of"
echo " values as you turned, not jump erratically or stay flat. A real yaw"
echo " signal traces a continuous path; a broken one would look random or"
echo " frozen.)"

echo
echo "======================================================"
echo "== CHECK 3: odom's own confidence in its yaw estimate (covariance)"
echo "======================================================"
echo
echo "The pose covariance is a 6x6 grid (x,y,z,roll,pitch,yaw), flattened"
echo "into 36 numbers. The yaw confidence value is specifically the 36th"
echo "number (index 35) -- extracting that directly:"
echo
docker exec yahboom_gesture bash -c "
  source /opt/ros/humble/setup.bash &&
  timeout 5 ros2 topic echo /odom_raw --once
" 2>&1 | python3 -c "
import sys, re
text = sys.stdin.read()
match = re.search(r'pose:.*?covariance:\s*\n((?:\s*-\s*[\d.eE+-]+\s*\n?){36})', text, re.DOTALL)
if not match:
    print('Could not locate covariance block -- showing raw pose section for manual inspection:')
    idx = text.find('pose:')
    print(text[idx:idx+2000])
else:
    values = re.findall(r'-?\s*([\d.eE+-]+)', match.group(1))
    if len(values) >= 36:
        yaw_variance = float(values[35])
        print(f'Yaw variance (index 35): {yaw_variance}')
        print(f'Yaw std deviation (sqrt of variance): {yaw_variance**0.5:.4f} radians')
        if yaw_variance == 0.0:
            print('>>> Variance is exactly 0.0 -- sensor is claiming PERFECT confidence,')
            print('    which is itself a red flag (real sensors always have some noise).')
        elif yaw_variance > 10:
            print('>>> Variance is very high -- sensor itself has LOW confidence in yaw.')
        else:
            print('>>> Variance looks like a plausible, moderate confidence value.')
    else:
        print(f'Only found {len(values)} values, expected 36 -- parsing issue, showing raw:')
        print(match.group(1))
"

echo
echo "======================================================"
echo "== SUMMARY -- WHAT EACH RESULT MEANS"
echo "======================================================"
echo "CHECK 1: If backup files show odom yaw was ONCE enabled then later"
echo "  disabled, that's a strong signal it was deliberate -- look at what"
echo "  else changed around the same time for a reason why."
echo "CHECK 2: If the z/w values traced a smooth, continuous path through"
echo "  your rotation: real signal, safe to enable. If jumpy/frozen/random:"
echo "  do NOT enable it yet -- needs more investigation first."
echo "CHECK 3: A near-zero or missing (default 1.0) covariance doesn't"
echo "  necessarily mean bad data -- many low-cost robots don't populate"
echo "  this properly even when the data itself is fine. Weigh this check"
echo "  alongside Check 2's actual data trace, not in isolation."
