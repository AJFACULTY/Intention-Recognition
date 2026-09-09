# Implementation Plan: Active Vision Gimbal Verification (Opt 2) & Headless Simulation Hardening (Opt 4)

While the physical Yahboom robot is on the 12.6V balance charger, this plan executes **Option 2** (Milestone 3: Active 2-DOF Gimbal Tracking Logic Verification & Memory Hold Hardening) and **Option 4** (Milestone 4: Headless Simulation Launch & Pipeline Resource Optimization on the Dev Laptop).

---

## User Review Required

> [!IMPORTANT]
> **Option 2 (Active Vision Memory Hold Hardening):**
> In the current implementation of `active_vision_node.py`, when a face target is lost ($z \le 0$), the callback does not clear or invalidate `latest_target`. As a result, the controller continues to integrate the stale last known coordinate for up to 1.5 seconds, causing unwanted gimbal drift. We will update the logic so that upon target loss or inter-frame gaps, the gimbal enters **`MEMORY_HOLD`** (holding its commanded angle) before initiating the sinusoidal search sweep, matching [ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md](file:///home/j/ros2_cognition_ws/docs/ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md).

> [!NOTE]
> **Option 4 (Headless Simulation Execution):**
> Running Gazebo Harmonic with full OGRE2 GUI (`gz sim -r`) and RViz2 simultaneously overcommits the developer machine's 4-core AMD Ryzen 5 3500U and 5.7 GiB usable RAM, causing EKF update deadline misses and desktop "Wait or Force Close" dialogs. We will add headless mode support (`gui:=false`, executing `gz sim -s -r`) and create `pi5_sim_headless.launch.py`.

---

## Proposed Changes

### Component 1: Active Vision Gimbal Verification & Logic Hardening (Option 2)

#### [MODIFY] [active_vision_node.py](file:///home/j/ros2_cognition_ws/src_nodes/active_vision_node.py)
- **Target Invalidation & Memory Hold:**
  When `msg.z <= 0.0` or no fresh detection has arrived within 0.2s, freeze target integration (`delta_pan = 0.0, delta_tilt = 0.0`) and hold position during the 1.5s timeout window.
- **FSM State Reporting:**
  Explicitly report `MEMORY_HOLD` state in `/cognition/gimbal_state` when holding heading prior to `SEARCH`.
- **Integrator Bleed/Decay:**
  Gradually bleed integral terms back to zero when entering deadband or memory hold to avoid integrator windup jumps upon re-acquisition.

#### [NEW] [test_active_vision_logic.py](file:///home/j/ros2_cognition_ws/scripts/test_active_vision_logic.py)
- A standalone automated verification suite testing:
  1. **Neutral Home Pose:** Initial output is `pan=10, tilt=50`.
  2. **Deadband Suppression:** Coordinate errors $|e_x|, |e_y| \le 0.05$ output zero servo displacement.
  3. **Visual Servoing Directions:** Target at $+x$ (right of frame) decreases pan angle (pans camera right); target at $-y$ (above frame) decreases tilt angle (tilts camera up).
  4. **Slew-Rate Limiting:** Abrupt target jumps ($\Delta = 1.0$) are strictly constrained to $\le 3.0^\circ$ per 50ms tick ($60^\circ/\text{s}$).
  5. **Mechanical Safety Clamping:** Extreme commands cannot breach $0^\circ \le \theta_{\text{pan}} \le 180^\circ$ or $20^\circ \le \phi_{\text{tilt}} \le 110^\circ$.
  6. **FSM Transitions:** `IDLE` $\to$ `TRACKING` $\to$ `MEMORY_HOLD` $\to$ `SEARCH` (sinusoidal sweep at $0.3\text{ Hz}$, $40^\circ$ amp) $\to$ `REVERT` $\to$ `IDLE`.
  7. **Target Re-acquisition:** Immediately interrupts `SEARCH` and resumes `TRACKING`.

---

### Component 2: Dev Laptop Simulation Hardening (Option 4)

#### [NEW] [pi5_sim_headless.launch.py](file:///home/j/cognition_ws/src/cognition_simulation/launch/pi5_sim_headless.launch.py)
- Headless simulation launch executing Gazebo Harmonic server physics only (`gz sim -s -r empty.sdf`).
- Eliminates the heavy OGRE2 GUI rendering thread, saving ~1.5 GiB of RAM and ~1.5 CPU cores.
- Parameterizes `rviz` launch argument (default `false`) so visualizer can be launched optionally or decoupled.
- Mirrored to [launch/pi5_sim_headless.launch.py](file:///home/j/ros2_cognition_ws/launch/pi5_sim_headless.launch.py).

#### [MODIFY] [pi5_sim.launch.py](file:///home/j/cognition_ws/src/cognition_simulation/launch/pi5_sim.launch.py)
- Add `gui` launch argument (`DeclareLaunchArgument('gui', default_value='true')`).
- If `gui` is `false`, pass `-s -r` to `gz sim`; if `true`, pass `-r`.
- Mirrored to [launch/pi5_sim.launch.py](file:///home/j/ros2_cognition_ws/launch/pi5_sim.launch.py).

---

### Component 3: Documentation & Roadmap Synchronization

#### [MODIFY] [docs/MASTER_COMPLETION_ROADMAP.md](file:///home/j/ros2_cognition_ws/docs/MASTER_COMPLETION_ROADMAP.md)
- Update Milestone 3 Task 4.1 status to Verified.
- Update Milestone 4 Tasks 5.1 & 5.2 status to Completed & Verified.

#### [MODIFY] [docs/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md](file:///home/j/ros2_cognition_ws/docs/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md)
- Record the architectural analysis, test suite results, and headless simulation benchmarks.

---

## Verification Plan

### Automated Tests
1. **Active Vision Node Automated Test Suite:**
   ```bash
   source /opt/ros/jazzy/setup.bash
   python3 /home/j/ros2_cognition_ws/scripts/test_active_vision_logic.py
   # Expected Output: All 7 verification assertions PASS with zero errors.
   ```

2. **Simulation Package Build:**
   ```bash
   source /opt/ros/jazzy/setup.bash
   cd /home/j/cognition_ws && colcon build --packages-select cognition_simulation
   # Expected Output: Finished <<< cognition_simulation [clean build]
   ```

3. **Headless Gazebo Execution Benchmark:**
   ```bash
   source /opt/ros/jazzy/setup.bash
   source /home/j/cognition_ws/install/setup.bash
   ros2 launch cognition_simulation pi5_sim_headless.launch.py
   # Expected:
   # 1. Gazebo Harmonic starts in server mode (-s -r) with zero GUI windows.
   # 2. Topics /clock, /scan, /odom_raw, /tf publish continuously.
   # 3. Memory footprint < 3.8 GiB (plenty of safety margin within 5.7 GiB hardware).
   # 4. EKF runs at nominal 10.0 Hz without deadline misses.
   ```

### Manual Verification
- Verify terminal logs and resource consumption via `free -m` and `top` during simulation launch.
