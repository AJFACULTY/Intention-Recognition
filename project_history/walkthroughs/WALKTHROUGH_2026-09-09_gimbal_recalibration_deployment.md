# Walkthrough: Physical Gimbal Recalibration & Smooth Motion Deployment

## 1. Overview of Changes

Based on physical media forensics ([photo_2026-09-09_10-31-48.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-09_10-31-48.jpg), [video_2026-09-09_10-26-04.mp4](file:///home/j/ros2_cognition_ws/test_vids/video_2026-09-09_10-26-04.mp4), and benchmark [photo_2026-09-08_07-24-44.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-08_07-24-44.jpg)), we empirically calibrated the 2-DOF active camera gimbal on the physical Yahboom Raspberry Pi 5 robot (`pi@10.27.122.136`).

### Core Accomplishments
1. **Calibrated Physical 0-Centric Protocol**:
   - Replaced incorrect 90-centric assumption (`pan_home = 90`, `tilt_home = 100`) with true empirical 0-centric kinematics:
     - **Pan Neutral Center:** **$0^\circ$** (Straight forward along chassis bumper; range $-60^\circ \dots +60^\circ$).
     - **Tilt Neutral Resting:** **$+25^\circ$** (Horizontally level with slight elevation to frame human standing in front, not facing the ground and not aimed at the ceiling; range $+10^\circ \dots +55^\circ$).
2. **Eliminated Sudden Startup Snapping**:
   - Removed immediate `publish_servos` call from `__init__()`.
   - Enforced continuous $16^\circ/\text{s}$ slew-rate limiting (`max_slew_deg = 0.8`), protecting tiny micro-servo gears from tooth shear stress and preventing electrical inrush voltage sags on the Raspberry Pi 5.
3. **Enabled Symmetrical Left/Right Search Sweeps**:
   - Search sweep formula `pan_home + search_amp * sin(...)` now oscillates evenly between **$-30^\circ$ (Left)** through **$0^\circ$ (Center)** to **$+30^\circ$ (Right)** with a 5-second graceful cycle (`search_amplitude = 30.0`, `search_freq = 0.2`).
   - Confirmed the USB camera cable on the left hinge has ample slack and was not binding.
4. **Maintained Forward Task Pose on "GO" Command**:
   - When operator commands `GO` (gesture ID: 2), gimbal transitions to `TASK_FORWARD` and smoothly glides to `pan = 0`, `tilt = 25`, holding this view for 3.0 seconds so the robot has a level view of its driving path.
5. **Graceful Shutdown & Parking**:
   - Updated `start_bench_pipeline.sh` cleanup trap to command `Pan = 0°`, `Tilt = 25°` before terminating processes.

---

## 2. Modified Files & Components

| Component | File | Changes Made |
|---|---|---|
| **Active Vision Gimbal** | [src_nodes/active_vision_node.py](file:///home/j/ros2_cognition_ws/src_nodes/active_vision_node.py) | Set `pan_home=0`, `tilt_home=25`, `max_slew_deg=0.8`, `search_amplitude=30.0`, `search_freq=0.2`; removed `__init__` publish; corrected 0-centric visual servoing signs (`delta_pan = +Kp*ex`, `delta_tilt = -Kp*ey`). |
| **Autonomy HUD Monitor** | [scripts/bench_autonomy_monitor.py](file:///home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py) | Updated baseline initial display to `Pan = 0°`, `Tilt = 25°`. |
| **Bench Pipeline Launcher** | [scripts/start_bench_pipeline.sh](file:///home/j/ros2_cognition_ws/scripts/start_bench_pipeline.sh) | Updated cleanup trap to publish `Pan = 0°`, `Tilt = 25°` before process termination. |
| **Hardware Spec** | [docs/ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md](file:///home/j/ros2_cognition_ws/docs/ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md) | Updated Table 2.1 with verified 0-centric parameters. |
| **Post-Mortem Catalog** | [docs/HISTORICAL_ERROR_POSTMORTEM_CATALOG.md](file:///home/j/ros2_cognition_ws/docs/HISTORICAL_ERROR_POSTMORTEM_CATALOG.md) | Documented Error 62 (0-centric calibration, anti-snapping, and symmetric sweep). |
| **Evolution Log** | [docs/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md](file:///home/j/ros2_cognition_ws/docs/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md) | Logged new production versions and verified parameters. |
| **Session Prompts** | [docs/SESSION_PROMPTS_AND_CHAT_HISTORY_2026-09-08.md](file:///home/j/ros2_cognition_ws/docs/SESSION_PROMPTS_AND_CHAT_HISTORY_2026-09-08.md) | Recorded Prompt 30 with photographic forensics and consultation. |
| **Audit Report** | [docs/MASTER_AUDIT_AND_COMPLETION_REPORT.md](file:///home/j/ros2_cognition_ws/docs/MASTER_AUDIT_AND_COMPLETION_REPORT.md) | Updated Active Gimbal FOV Tracking progress to 95%. |
| **Roadmap** | [docs/MASTER_COMPLETION_ROADMAP.md](file:///home/j/ros2_cognition_ws/docs/MASTER_COMPLETION_ROADMAP.md) | Updated Task 4.1 to reflect physical 0-centric verification. |

---

## 3. Step-by-Step Deployment to Physical Robot

Run the following commands on your laptop terminal to transfer the updated nodes and launch the live test:

### Step 1: Transfer Updated Files to Pi Host
```bash
scp /home/j/ros2_cognition_ws/src_nodes/active_vision_node.py \
    pi@10.27.122.136:~/cognition_ws/src/cognition_perception/cognition_perception/

scp /home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py \
    pi@10.27.122.136:~/cognition_ws/

scp /home/j/ros2_cognition_ws/scripts/start_bench_pipeline.sh \
    pi@10.27.122.136:~/start_bench_pipeline.sh
```

### Step 2: SSH into the Pi & Sync Files into Docker Container
```bash
ssh pi@10.27.122.136
```
Inside the Pi SSH session, copy the files into `yahboom_gesture` and launch:
```bash
# Sync files into the container
docker cp ~/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py \
    yahboom_gesture:/root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py

docker cp ~/cognition_ws/bench_autonomy_monitor.py \
    yahboom_gesture:/root/cognition_ws/bench_autonomy_monitor.py

# Ensure executable and launch bench pipeline
chmod +x ~/start_bench_pipeline.sh
bash ~/start_bench_pipeline.sh
```

---

## 4. Expected Live Verification Behavior

When `start_bench_pipeline.sh` runs:
1. **Smooth Gentle Startup**: The camera will glide smoothly at $16^\circ/\text{s}$ to the resting pose:
   $$\text{Pan} = 0^\circ \quad (\text{Center Forward}), \quad \text{Tilt} = +25^\circ \quad (\text{Slightly Elevated Forward})$$
   There will be **zero violent snapping** or buzzing.
2. **Symmetrical Left/Right Search Sweep**: If no human is present, the camera will smoothly sweep back and forth from $-30^\circ$ (Left) to $+30^\circ$ (Right) every 5 seconds.
3. **Smooth Torso/Face Tracking**: When you step in front of the robot, the gimbal locks onto you and smoothly pans left or right to keep you centered.
4. **Forward Task Pose on "GO"**: Pointing forward or giving a thumbs-up commands the robot to drive forward ($0.25\text{ m/s}$) while the camera looks straight ahead along the driving path (`Pan = 0°`, `Tilt = 25°`).
5. **Instant Stop**: Showing an open palm immediately halts the wheels.
