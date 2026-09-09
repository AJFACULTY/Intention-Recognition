# Implementation Plan: 0-Centric Gimbal Recalibration, Smooth Motion, and Symmetrical Sweep

## 1. Problem Diagnostic & Empirical Ground Truth

Following the live test on the physical Yahboom Raspberry Pi 5 robot (`pi@10.27.122.136`) and visual forensic inspection of [test_pics/photo_2026-09-09_10-31-48.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-09_10-31-48.jpg) and [test_vids/video_2026-09-09_10-26-04.mp4](file:///home/j/ros2_cognition_ws/test_vids/video_2026-09-09_10-26-04.mp4):

1. **Tilt Angle Too High ($100^\circ$)**:
   - Commanded tilt of $100^\circ$ aimed the camera $\approx 65^\circ$ above horizontal, directly pointing into the ceiling lights.
   - Ground truth from earlier calibrated benchmark ([photo_2026-09-08_07-24-44.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-08_07-24-44.jpg) and HUD [photo_2026-09-08_08-08-31.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-08_08-08-31.jpg)) shows that **Tilt $\approx +25^\circ \dots +30^\circ$** is the true forward-facing, slightly elevated pose that frames a standing human operator's torso, face, and hands.
2. **Right-Biased Sweep (Not a Cable Obstruction or Design Flaw)**:
   - The user noticed the camera only swept to the right side of the robot until left running.
   - Physical cable inspection confirms there is generous slack on the left hinge.
   - The mathematical cause: `pan_home` was configured to $90^\circ$ with $40^\circ$ search amplitude, causing the sinusoidal sweep formula `pan_home + amp * sin(...)` to oscillate between **$+50^\circ$ and $+130^\circ$**. On this STM32 firmware, **$0^\circ$ is dead-center forward**, so every commanded angle was far to the right!
   - By setting `pan_home = 0` with `search_amp = 30.0`, the sweep oscillates symmetrically from **$-30^\circ$ (Left)** through **$0^\circ$ (Center)** to **$+30^\circ$ (Right)**.
3. **Servo Snapping on Startup**:
   - `active_vision_node.py` executed `self.publish_servos(...)` inside `__init__()`, slamming the hardware immediately from its unenergized resting pose to the initial target with zero rate-limiting.
   - In `start_bench_pipeline.sh`, `cleanup()` previously killed processes abruptly via `pkill -9` without parking the servos, leaving them at arbitrary angles when the next test began.
4. **Kinematic Tracking Signs with 0-Centric Protocol**:
   - Target right of center ($e_x > 0$): Camera must turn RIGHT $\implies \Delta \text{pan} = +(K_p \cdot e_x + \dots)$.
   - Target high ($e_y < 0$): Camera must tilt UP $\implies \Delta \text{tilt} = -(K_p \cdot e_y + \dots)$.

---

## 2. Proposed Code Changes

### Component 1: `src_nodes/active_vision_node.py`
#### [MODIFY] [active_vision_node.py](file:///home/j/ros2_cognition_ws/src_nodes/active_vision_node.py)
- **Recalibrate Neutral & Limit Parameters**:
  - `pan_home`: `0` (range `-60` to `+60`)
  - `tilt_home`: `25` (range `10` to `55`, straight forward & slightly elevated, not facing ground or ceiling)
  - `search_amplitude`: `30.0` (sinusoidal sweep between $-30^\circ$ left and $+30^\circ$ right)
  - `search_freq`: `0.2` Hz (smooth 5-second graceful sweep cycle)
  - `max_slew_deg`: `0.8` deg/tick at 20 Hz ($16^\circ/\text{s}$ cinematic glide; eliminates all abrupt snapping)
- **Eliminate Startup Snapping**:
  - Remove immediate `publish_servos` call from `__init__()`.
  - Let the control loop smoothly ramp the servos via `max_slew_deg` limiters.
- **Visual Servoing Kinematics**:
  - Set `delta_pan = +(self.kp_pan * e_x + self.ki_pan * self.integral_pan + self.kd_pan * deriv_x)`
  - Set `delta_tilt = -(self.kp_tilt * e_y + self.ki_tilt * self.integral_tilt + self.kd_tilt * deriv_y)`
- **"GO" Gesture Forward Task Pose**:
  - When operator executes `GO` gesture (ID: 2), maintain forward task pose (`pan = 0`, `tilt = 25`) with a 3-second hold window so the robot drives forward with clear visibility of its path.

### Component 2: `scripts/bench_autonomy_monitor.py`
#### [MODIFY] [bench_autonomy_monitor.py](file:///home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py)
- Update default initial display values before first topic callback:
  - `self.current_pan = 0`
  - `self.current_tilt = 25`

### Component 3: `scripts/start_bench_pipeline.sh`
#### [MODIFY] [start_bench_pipeline.sh](file:///home/j/ros2_cognition_ws/scripts/start_bench_pipeline.sh)
- Update `cleanup()` to park servos at `Pan = 0°`, `Tilt = 25°` on exit before terminating processes, ensuring the gimbal is always neatly parked forward for the next test.

### Component 4: Companion Documentation Suite
#### [MODIFY] [CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md](file:///home/j/ros2_cognition_ws/docs/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md)
#### [MODIFY] [HISTORICAL_ERROR_POSTMORTEM_CATALOG.md](file:///home/j/ros2_cognition_ws/docs/HISTORICAL_ERROR_POSTMORTEM_CATALOG.md)
#### [MODIFY] [SESSION_PROMPTS_AND_CHAT_HISTORY_2026-09-08.md](file:///home/j/ros2_cognition_ws/docs/SESSION_PROMPTS_AND_CHAT_HISTORY_2026-09-08.md)
#### [MODIFY] [ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md](file:///home/j/ros2_cognition_ws/docs/ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md)
#### [MODIFY] [MASTER_AUDIT_AND_COMPLETION_REPORT.md](file:///home/j/ros2_cognition_ws/docs/MASTER_AUDIT_AND_COMPLETION_REPORT.md)
- Permanently record the 0-centric hardware calibration, empirical video analysis, and post-mortem resolution.

---

## 3. Verification Plan

### Automated / Local Syntax Check
- Verify all modified files compile cleanly:
  ```bash
  python3 -m py_compile src_nodes/active_vision_node.py scripts/bench_autonomy_monitor.py
  ```

### Deployment & Live Hardware Verification
1. Transfer files to Pi host:
   ```bash
   scp src_nodes/active_vision_node.py pi@10.27.122.136:~/cognition_ws/src/cognition_perception/cognition_perception/
   scp scripts/bench_autonomy_monitor.py scripts/start_bench_pipeline.sh pi@10.27.122.136:~/cognition_ws/
   ```
2. Sync to Docker container:
   ```bash
   docker cp ~/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py yahboom_gesture:/root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py
   docker cp ~/cognition_ws/bench_autonomy_monitor.py yahboom_gesture:/root/cognition_ws/bench_autonomy_monitor.py
   ```
3. Run `bash ~/start_bench_pipeline.sh` on Pi 5.
4. Verify:
   - Camera initializes gently to forward, slightly elevated pose (`Pan = 0°`, `Tilt = 25°`) with ZERO violent snapping.
   - Search sweep sweeps smoothly and symmetrically between $-30^\circ$ (Left) and $+30^\circ$ (Right).
   - Operator detection centers the gimbal smoothly onto the operator without jitter.
   - Pointing / Thumbs up (`GO`) triggers forward wheel spin ($0.25\text{ m/s}$) while camera smoothly faces forward along the drive vector.
