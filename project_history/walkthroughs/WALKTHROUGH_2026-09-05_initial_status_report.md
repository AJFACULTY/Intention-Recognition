# Robot Navigation Project — Complete Analysis & Status Report

## Project Overview

**Thesis:** "Cognition" — A gesture-controlled autonomous mobile robot that recognizes human intent through hand gestures and body motion, combined with autonomous navigation.

**Hardware:** Yahboom MicroROS-Pi5 (Raspberry Pi 5 + ESP32 co-processor)  
**Software Stack:** ROS2 Humble (Robot/Docker), ROS2 Jazzy (Dev machine)  
**Core Components:** SLAM Toolbox, Nav2, YOLOv8n, MediaPipe, MLP classifier, LSTM path predictor

---

## Complete Bug History & Fix Chain

The following documents every root cause found and fixed, in chronological order. Each fix was evidence-based and verified before moving to the next.

---

### Fix 1: Transform Conflict (TF Broadcaster Collision)

| | |
|---|---|
| **Symptom** | Robot jitters, SLAM drops 100% of scans |
| **Root Cause** | Two competing TF broadcasters for `odom_frame → base_footprint`: a static identity publisher (`odom_tf` node) AND the dynamic EKF publisher |
| **Fix** | Removed the `odom_tf` static broadcaster node from `slam_real.launch.py` |
| **Verification** | Scan drop rate went from 100% → ~12-68% (variable run-to-run). Transforms showed real nonzero motion values. |
| **Git Commit** | `aa299c3` |

---

### Fix 2: Rotational Drift (Missing Odom Yaw in EKF)

| | |
|---|---|
| **Symptom** | Maps showed "hourglass" shape with starburst artifacts — two disconnected, rotated room halves |
| **Root Cause** | EKF's `odom0_config` had yaw set to `False`. IMU orientation was dead (`0,0,0,1` identity on all reads). Robot's heading came entirely from integrated gyro rate — pure dead reckoning with zero absolute correction |
| **Evidence** | `/odom_raw` orientation: smooth, correct quaternion values across 200+ continuous readings through multiple full rotations. `/imu` orientation: identical `(0,0,0,1)` on all reads — confirmed dead. |
| **Fix** | Flipped `odom0_config` yaw field from `False` to `True` in `slam_real.launch.py` |
| **Verification** | Fused EKF output tracked real continuous rotation through multiple full turns with correct ±180° wraparound. Third mapping attempt produced a coherent single-room shape with no drift artifacts. |
| **Git Commit** | Committed alongside the verified mapping session |

---

### Fix 3: Nav2 Topic Mismatch (`/scan_fixed`)

| | |
|---|---|
| **Symptom** | Config audit pre-Nav2 test |
| **Root Cause** | `nav2_params.yaml` referenced `/scan_fixed` (3 occurrences) — a topic that doesn't exist on real hardware. Real topics: `/scan` (raw) and `/scan_downsampled` (restamped by `scan_republisher`) |
| **Fix** | Changed all 3 references to `/scan_downsampled` |
| **Additional** | Also changed `bt_navigator`'s `odom_topic` from raw `/odom_raw` to fused `/odometry/filtered` |

---

### Fix 4: Missing Sensor Chain in Nav2 Launch

| | |
|---|---|
| **Symptom** | Config audit |
| **Root Cause** | `nav2.launch.py` only started Nav2's own nodes — didn't start `laser_tf`, `scan_republisher`, `odom_imu_republisher`, or EKF, which produce the transform chain and fixed-timing scan data Nav2 depends on |
| **Fix** | Rewrote `nav2.launch.py` to include the full sensor/transform chain (same nodes as `slam_real.launch.py` minus `slam_toolbox`) with timer-delayed Nav2 nodes |

---

### Fix 5: Map Path Unreachable in Container

| | |
|---|---|
| **Symptom** | Nav2 test: `/amcl_pose` never published, AMCL stayed `unconfigured` |
| **Root Cause** | `os.path.expanduser('~/maps/...')` resolved to `/root/maps/` inside the container — but only `/root/cognition_ws/` is bind-mounted. The map file existed on the host at `/home/pi/maps/` but was invisible to the container. |
| **Evidence** | Log showed: `[ERROR] [map_io]: Failed processing YAML file /root/maps/room_map_20260812_0826.yaml` → `lifecycle_manager` aborted all node bringup |
| **Fix** | Changed `map_yaml` path to `/root/cognition_ws/maps_new/room_map_20260812_0826.yaml` (accessible via bind mount) |
| **Verification** | Next run's log confirmed: `[INFO] [map_io]: Loading yaml file: ... Loading image_file: ... Read map: 185 X 195 map @ 0.05 m/cell` — full success |
| **Git Commit** | `2a7697c` |

---

### Fix 6: Planner Plugin Name Format

| | |
|---|---|
| **Symptom** | Nav2 test: `planner_server` FATAL error, lifecycle bringup aborted again |
| **Root Cause** | `nav2_params.yaml` specified `nav2_navfn_planner::NavfnPlanner` (C++ namespace `::` style) instead of `nav2_navfn_planner/NavfnPlanner` (slash format the plugin loader requires) |
| **Evidence** | Error message itself listed the correct declared types |
| **Fix** | Changed `::` to `/` in `nav2_params.yaml` |
| **Git Commit** | `56730f7` |

---

### Fix 7 (PENDING): `install/` vs `src/` Drift

| | |
|---|---|
| **Symptom** | After Fix 6, the exact same planner plugin error appeared word-for-word |
| **Root Cause** | `nav2.launch.py` loads `nav2_params.yaml` via `get_package_share_directory()`, which resolves to the **installed** copy (`install/cognition_simulation/share/.../nav2_params.yaml`), not the `src/` file being edited. The `install/` copy was never rebuilt after edits. |
| **Evidence** | Direct diff confirmed: `src/` has the fix (`/`), `install/` still has the broken version (`::`) |
| **Proposed Fix** | Two-part: (1) Point `nav2.launch.py` at `src/` config directly (same pattern `slam_real.launch.py` uses), (2) Rebuild `cognition_simulation` package to resync `install/` |
| **Status** | ⚠️ **Script `13_fix_install_src_drift.sh` was created but NOT YET RUN on the robot** |

---

## Current Map Status

| Map File | Date | Dimensions | Quality |
|---|---|---|---|
| `room_map_v1` | Pre-project (July) | Unknown | Stale — room arrangement changed |
| `room_map_20260810_0452` | Aug 10 | 314×206 cells (~15.7m × 10.3m) | ❌ Severe drift (hourglass shape, starburst artifacts) |
| `room_map_20260810_0938` | Aug 10 | Unknown | ❌ Also drifted |
| `room_map_20260812_0826` | Aug 12 | 185×195 cells (~9.25m × 9.75m) | ✅ **Good** — coherent room, no drift, usable for Nav2 |

---

## Current State Summary

### What's Working
- ✅ Gesture control (`cognition.service`) — stable throughout
- ✅ Joystick control — always available
- ✅ LiDAR sensor chain (`/scan` @ ~12.5Hz, `/odom_raw` @ ~10.8Hz, `/imu` @ ~23Hz)
- ✅ SLAM mapping with corrected EKF — produces drift-free maps
- ✅ Git tracking — all changes committed and reversible

### What's Blocking Nav2
- ⚠️ **Fix 7 not applied yet** — `install/` vs `src/` drift means the planner plugin fix hasn't actually taken effect at runtime
- The script (`13_fix_install_src_drift.sh`) exists but has not been run

### Known Recurring Issues
- **Process cleanup scripts**: `pkill` pattern-matching has failed consistently. PID-based cleanup (capturing PIDs at launch, killing by exact PID) works reliably.
- **ROS2 daemon cache staleness**: Frequently shows stale node lists. Fixed by `ros2 daemon stop && ros2 daemon start`.
- **Disk usage**: 79% utilized. ~55GB reclaimable from redundant Docker image tags.

---

## Exact Next Steps to Resume

### Step 1: Apply Fix 7 (install/src drift)
```bash
# Transfer and run the fix script
scp ~/Downloads/13_fix_install_src_drift.sh pi@<robot-ip>:~
ssh pi@<robot-ip>
chmod +x 13_fix_install_src_drift.sh
./13_fix_install_src_drift.sh
```

### Step 2: Retry Navigation Test
```bash
# Position robot at mapping start point, same direction
./9_run_navigation_test.sh
```

### Step 3: If Successful
- Nav2 should localize (AMCL pose near 0,0) and accept a 1m forward goal
- Monitor for clean path planning and actual autonomous movement

### Step 4: If More Plugin Errors
- Same pattern: read the `FATAL` error's "declared types" list, fix that one line, retest
- After each fix, rebuild or point at `src/` directly to avoid the install/src drift trap

---

## Key Configuration Files

| File | Purpose | Location |
|---|---|---|
| `slam_real.launch.py` | SLAM + sensor chain launch | `~/cognition_ws/src/cognition_simulation/launch/` |
| `nav2.launch.py` | Nav2 + sensor chain launch | `~/cognition_ws/src/cognition_simulation/launch/` |
| `nav2_params.yaml` | Nav2 parameter config | `~/cognition_ws/src/cognition_simulation/config/` |
| `scan_republisher.py` | Scan timestamp fix + downsampling | `~/cognition_ws/src/cognition_simulation/...` |
| `odom_imu_republisher.py` | Odom/IMU timestamp fix | Same package |

## Architecture Notes

- **Dual Docker containers**: `yahboom_base` (micro-ROS agent), `yahboom_gesture` (ROS2 stack)
- **Bind mount**: `/home/pi/cognition_ws` → `/root/cognition_ws` in container
- **ROS_DOMAIN_ID**: 20
- **Frame names**: `odom_frame`, `base_footprint`, `laser_frame`, `map` (non-standard but consistent)
- **Middleware**: FastDDS (hardware), CycloneDDS (simulation)
