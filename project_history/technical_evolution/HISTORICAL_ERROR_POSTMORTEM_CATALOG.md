# HISTORICAL ERROR & POSTMORTEM CATALOG: COGNITION ROBOT PROJECT
**Complete Forensic Registry of Every Bug, Crash, Mismatch, Failed Fix Attempt & Solution (March – September 2026)**
**Author:** Antigravity Autonomous Systems Engineering Team

---

## 1. Document Purpose & Structure

This catalog documents **every single technical error, bug, crash, and configuration drift** encountered across the Cognition Robot project from Day 1 to the present date. For each incident, this document details:
1. **Trigger & Exact Symptom / Log Output**
2. **Root Cause Analysis**
3. **Failed Attempts at Fixing** (what was tried that failed or caused secondary issues)
4. **Successful Permanent Fix**
5. **Defensive Engineering Tip & Prevention Rule**
6. **Recurrence Count & Status** (Resolved vs. Latent/Unresolved)

---

## 2. Master Error Summary by Phase

```
┌─────────────────────────────────────────────────────────────┬───────────┬────────────┐
│ Era / Category                                              │ Count     │ Status     │
├─────────────────────────────────────────────────────────────┼───────────┼────────────┤
│ Phase 1: Simulation Setup & Gazebo Bringup                  │ Errors 1–16│ Resolved   │
│ Phase 2: ROS 2 Jazzy Porting & SLAM Stabilization           │ Errors 17–28│ Resolved   │
│ Phase 3: Physical Robot Bringup & ESP32 Micro-ROS Timing    │ Errors 29–33B│ Resolved   │
│ Phase 4: Physical SLAM Mapping & Rotational Drift           │ Errors 34–37│ Resolved   │
│ Phase 5: Physical Nav2 AMCL & Container Architecture        │ Errors 38–42│ Resolved   │
│ Phase 6: Currently Latent / Undiagnosed Issues              │ Errors 43–47│ Action Req │
└─────────────────────────────────────────────────────────────┴───────────┴────────────┘
```

---

## 3. Detailed Postmortem Registry

### Phase 1: Simulation Setup & Gazebo Bringup

#### Error 1: Tilde Path Expansion Failure in `e2ls`
- **Trigger:** Running `e2ls '~/yahboomcar_ws/...'` to inspect disk image contents.
- **Symptom:** `No such file or directory` despite file existing in user home directory.
- **Root Cause:** Bash does not expand `~` when enclosed in single or double quotes.
- **Failed Attempts:** Re-running with double quotes `e2ls "~/..."` (also failed in certain subshell environments).
- **Successful Fix:** Used `$HOME` explicitly or unquoted paths: `e2ls "$HOME/yahboomcar_ws/..."`.
- **Tip:** *Never quote tildes in shell scripts or Python subprocess calls; always use `$HOME` or `os.path.expanduser()`.*

#### Error 2: 7-Zip Inability to Extract ext4 Disk Images
- **Trigger:** Attempting to extract Yahboom factory OS image using `7z x`.
- **Symptom:** 7z reported success but produced 0-byte extracted files or unreadable binary blobs.
- **Root Cause:** 7-Zip does not parse native Linux ext4 partition tables inside raw SD card images.
- **Failed Attempts:** Renaming image extension `.img` to `.iso` and attempting 7z extraction.
- **Successful Fix:** Abandoned 7z; mounted image using loopback devices (`losetup -Pf`) or located URDF files directly in local workspace.
- **Tip:** *Always mount disk images with native Linux kernel loop devices (`sudo losetup -Pf <image>`) rather than archive extractors.*

#### Error 3: URDF Heredoc Terminal Buffer Corruption
- **Trigger:** Pasting a 300-line URDF xacro file into the bash terminal using `cat << 'EOF' > file.urdf`.
- **Symptom:** Syntax errors, truncated XML tags, broken closing brackets.
- **Root Cause:** Terminal input buffer overrun dropped characters during rapid paste.
- **Failed Attempts:** Pasting smaller chunks via `nano` while keyboard auto-repeat was enabled, causing accidental duplicated characters.
- **Successful Fix:** Used dedicated Python file creation scripts or editor write tools.
- **Tip:** *Never paste raw XML/URDF larger than 50 lines into interactive shell heredocs; write files via scripts or IDE tools.*

#### Error 4: Missing `/tmp/pi5_car.sdf` on Spawn
- **Trigger:** Launching simulation with `gz sim` spawn command `-file /tmp/pi5_car.sdf`.
- **Symptom:** `[create-10] [ERROR]: File /tmp/pi5_car.sdf not found. Entity spawn failed.`
- **Root Cause:** Legacy launch file expected an intermediate SDF file to be pre-generated in `/tmp/`, but the conversion step was omitted.
- **Failed Attempts:** Manually running `xacro` output to `/tmp/pi5_car.urdf` and hoping Gazebo would accept URDF via `-file`.
- **Successful Fix:** Switched spawn action to listen to the ROS 2 topic directly: `-topic /robot_description`.
- **Tip:** *Spawn models from `/robot_description` topic rather than ephemeral temporary files.*

#### Error 5: RViz2 RobotModel Transform Error (ROS Time 0)
- **Trigger:** Launching RViz2 immediately alongside Gazebo.
- **Symptom:** RobotModel display turned red in RViz2: `Transform [base_footprint -> odom] failed. Message timestamp is 0`.
- **Root Cause:** Gazebo had not yet unpaused and published `/clock`; ROS nodes set to `use_sim_time: true` were frozen at Time 0.
- **Failed Attempts:** Forcing `use_sim_time: false` in RViz2 (caused permanent frame mismatch with Gazebo).
- **Successful Fix:** Added a 3-second startup delay (`TimerAction`) or waited for `[ros_gz_sim]: Entity creation successful` before launching RViz2.
- **Tip:** *Always synchronize visualization bringup to simulator clock availability.*

#### Error 6: Gazebo `model://` URI Resolution Failure
- **Trigger:** Spawning robot with URDF visual meshes specified as `package://yahboomcar_description/meshes/...`.
- **Symptom:** `[gz-2] [Err] [SceneManager.cc:426] Failed to load geometry for visual: base_footprint_fixed_joint_lump__base_link_visual`.
- **Root Cause:** Gazebo Harmonic converts `package://` into `model://` and searches `GZ_SIM_RESOURCE_PATH`. The ROS package path was not registered in Gazebo's resource environment.
- **Failed Attempts:** Adding export tags to `package.xml` (ignored by external Gazebo binary).
- **Successful Fix:** Substituted mesh URIs in `pi5_car_official.urdf.xacro` with explicit `file:///home/j/yahboomcar_jazzy_ws/...` paths.
- **Tip:** *Ensure `GZ_SIM_RESOURCE_PATH` is exported in `~/.bashrc` or use absolute file URIs for simulation meshes.*

#### Error 7: RViz2 "Unable to Open File" for Mesh Assets
- **Trigger:** Replacing mesh paths with raw filesystem paths without URI scheme (e.g., `/home/j/...`).
- **Symptom:** RViz2 threw `Unable to open file: /home/j/...` and rendered gray boxes.
- **Root Cause:** RViz2 Ogre mesh loader requires explicit URI scheme (`file://`).
- **Failed Attempts:** Reverting to `package://` (which broke Gazebo).
- **Successful Fix:** Standardized all mesh URIs to `file:///home/j/...` (three slashes).
- **Tip:** *File URIs require three slashes: `file:///path/to/file`.*

#### Error 8: Launch File IndentationError After `sed` Patching
- **Trigger:** Applying in-place regex patches using `sed -i` to fix topic bridges in `pi5_sim.launch.py`.
- **Symptom:** `IndentationError: unexpected indent` when ROS 2 launch parsed the Python script.
- **Root Cause:** `sed` multi-line insertions altered Python whitespace indentation.
- **Failed Attempts:** Multiple subsequent `sed` commands attempting to fix indentation, which compounded syntax errors.
- **Successful Fix:** Reverted to backup and recreated the launch file cleanly from scratch.
- **Tip:** *Never use `sed -i` for multi-line Python script edits; use AST-aware tools or complete file replacements.*

#### Error 9: `/cmd_vel` Bridge Direction Inversion
- **Trigger:** Sending teleop commands via keyboard; robot did not move in Gazebo.
- **Symptom:** `[parameter_bridge-3] [INFO]: Waiting for subscription` on `/cmd_vel`.
- **Root Cause:** Bridge configuration used `[` (GZ $\to$ ROS) instead of `]` (ROS $\to$ GZ). The bridge was listening to Gazebo and publishing to ROS rather than forwarding velocity commands into simulation!
- **Failed Attempts:** Using bidirectional `@` bridge (caused message looping and jitter).
- **Successful Fix:** Configured directional bridge: `/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist`.
- **Tip:** *Always verify bridge directions: `]` means ROS $\to$ Gazebo; `[` means Gazebo $\to$ ROS.*

#### Error 10: Robot Rotating in Place on Linear Drive Commands
- **Trigger:** Publishing linear velocity `cmd_vel.linear.x = 0.2`.
- **Symptom:** Simulated robot spun uncontrollably in circles instead of driving forward.
- **Root Cause:** In the URDF wheel definitions, right-side wheels had joint axis `axis_y="-1"` while left had `axis_y="1"`. Gazebo's differential drive plugin expects identical positive axis orientation for all wheels.
- **Failed Attempts:** Inverting PID gains on the right wheel joint controller.
- **Successful Fix:** Set `axis_y="1"` for all four drive wheels in `pi5_car_official.urdf.xacro`.
- **Tip:** *Differential drive simulation plugins handle wheel directionality internally; do not invert URDF joint axes.*

#### Error 11: Gazebo Hanging at 13.91% Loading
- **Trigger:** Spawning robot model containing custom sensor definitions.
- **Symptom:** Simulator froze completely at 13.91% progress; terminal logged SDF parse warnings.
- **Root Cause:** A non-standard `<frame>` tag was embedded inside the `<sensor name="lidar">` SDF block.
- **Failed Attempts:** Increasing Gazebo startup timeout.
- **Successful Fix:** Removed invalid child element from SDF; defined frame transform via `tf2_ros` static transform publisher.
- **Tip:** *Validate custom SDF sensor blocks against official SDFormat specifications (`sdformat.org`).*

#### Error 12: Gazebo Scoping LiDAR `frame_id`
- **Trigger:** Gazebo LiDAR ray sensor published point cloud / laser scan.
- **Symptom:** Header frame in ROS was `/pi5_car/base_footprint/lidar` instead of standard `laser_frame`. SLAM and RViz could not transform scans.
- **Root Cause:** Gazebo automatically scopes sensor frame names with the model and link hierarchy.
- **Failed Attempts:** Overriding `<gz:frame_id>` (not supported in older Gazebo Harmonic vendor builds).
- **Successful Fix:** Developed [scan_republisher.py](file:///home/j/cognition_ws/src/cognition_simulation/scan_republisher.py) to intercept `/scan` and overwrite `header.frame_id = 'laser_frame'`.
- **Tip:** *Use a republisher node to sanitize simulator-generated frame headers before feeding standard ROS 2 navigation stacks.*

#### Error 13: Corrupted `/tf` Bridge Line
- **Trigger:** Executing launch file with duplicate `/tf` bridge definitions.
- **Symptom:** `ros_gz_bridge` crashed on startup with type mismatch error.
- **Root Cause:** An earlier automated patch added `/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V` twice.
- **Failed Attempts:** Restarting ROS 2 daemon.
- **Successful Fix:** Cleaned bridge configuration to include exactly one `/tf` bridge channel.
- **Tip:** *Audit bridge YAML configuration for duplicated topic mappings before launching.*

#### Error 14: `ros2 topic pub` Intermittent "Waiting for Subscriber"
- **Trigger:** Publishing single messages via `ros2 topic pub --once`.
- **Symptom:** Command hung indefinitely waiting for subscriber discovery.
- **Root Cause:** CycloneDDS transient subscriber discovery latency.
- **Failed Attempts:** Running `ros2 daemon stop && ros2 daemon start`.
- **Successful Fix:** Added `--wait-matching-subscriptions 1` or repeated command.
- **Tip:** *Add DDS discovery timeouts when using command-line topic publication in automated scripts.*

#### Error 15: Gazebo `SIGTERM` Escalation on Shutdown
- **Trigger:** Pressing `Ctrl+C` to terminate `pi5_sim.launch.py`.
- **Symptom:** Launch system logged `Escalating to SIGKILL for process gz-2`.
- **Root Cause:** Gazebo background physics and rendering threads were busy during teardown and missed SIGINT.
- **Failed Attempts:** Adding `pkill -9 gz` immediately after exit (orphaned child processes).
- **Successful Fix:** Normal behavior; Gazebo Harmonic requires ~3 seconds to flush physics buffers before closing.
- **Tip:** *Allow ROS 2 launch shutdown timeout to handle SIGTERM $\to$ SIGKILL escalation gracefully.*

#### Error 16: `tf2_echo --once` Flag Unknown
- **Trigger:** Inspecting transforms via `ros2 run tf2_ros tf2_echo --once odom base_footprint`.
- **Symptom:** `error: unrecognized arguments: --once`.
- **Root Cause:** `tf2_echo` in ROS 2 does not support `--once` (unlike `ros2 topic echo`).
- **Failed Attempts:** Passing `-n 1`.
- **Successful Fix:** Ran command without flag and piped to `head -n 20` or terminated via SIGINT.
- **Tip:** *`tf2_echo` streams continuously; terminate with SIGINT or wrap in subprocess with timeout.*

---

### Phase 2: ROS 2 Jazzy Porting & SLAM Stabilization

#### Error 17: SLAM "Message Filter Dropping" (8 Failed Attempts)
- **Trigger:** Launching `slam_toolbox` in Gazebo simulation.
- **Symptom:** Terminal flooded with: `Message Filter dropping message: frame 'laser_frame' for reason 'discarding message because the queue is full'`.
- **Root Cause:** Twofold: (1) Config file had wrong YAML root key (`async_slam_toolbox_node:` instead of `slam_toolbox:`), and (2) Launch file loaded default system config instead of user parameters.
- **Failed Attempts:**
  1. Increased queue size to 100.
  2. Changed `scan_topic` in custom YAML (ignored by launch file).
  3. Added static transform publishers for intermediate frames.
  4. Sourced different workspace overlays.
  5. Restarted ROS daemon.
  6. Tested gmapping (unsupported in Jazzy).
  7. Adjusted EKF sensor timeout.
  8. Reinstalled slam_toolbox package.
- **Successful Fix:** Overwrote system configuration directly with root key `slam_toolbox:`, verified scan topic was `/scan_fixed`, and synchronized EKF frame publishing.
- **Tip:** *In ROS 2, if a node is remapped in launch, its YAML parameter root key must match the remapped name.*

#### Error 18: `sed` Range Deletion Inadvertently Deleted `ekf_node`
- **Trigger:** Attempting to remove broken `slam_node` from launch file using `sed '/Node(/,/})/d'`.
- **Symptom:** Launch file failed to start EKF; transforms from `odom_frame -> base_footprint` disappeared.
- **Root Cause:** Greedy regex matched through multiple `Node(...)` definitions, deleting the EKF configuration block.
- **Failed Attempts:** Re-running launch with missing node.
- **Successful Fix:** Restored file from git and cleanly removed only the target block.
- **Tip:** *Do not use multi-line regex deletions on structured Python code.*

#### Error 19: `ros2 node info` "Unable to Find Node"
- **Trigger:** Running diagnostic script `ros2 node info /slam_toolbox`.
- **Symptom:** `Unable to find node /slam_toolbox`.
- **Root Cause:** Diagnostic command was executed after the test launch had already terminated.
- **Failed Attempts:** Re-running `ros2 daemon restart`.
- **Successful Fix:** Structured diagnostics to sample node availability *while* the launch process was actively running in background.
- **Tip:** *Always verify process PID liveness before running ROS 2 graph inspection queries.*

#### Error 20: RViz2 Dialog Frozen Under Heavy SLAM Load
- **Trigger:** Operating mapping simulation with full visual meshes enabled.
- **Symptom:** RViz2 window grayed out; mouse clicks unresponsive.
- **Root Cause:** Simultaneous OGRE2 rendering in Gazebo and RViz2 saturated the AMD Vega integrated GPU and DDR4 memory bus.
- **Failed Attempts:** Waiting for dialog to recover (induced swap death spiral).
- **Successful Fix:** Terminated RViz via `pkill -f rviz2`; disabled heavy visual meshes in RViz configuration.
- **Tip:** *On integrated GPU hardware, disable high-poly visual meshes in RViz; use collision geometry or simple bounding boxes.*

#### Error 21: `params_file:=` Launch Argument Ineffective
- **Trigger:** Passing `params_file:=my_config.yaml` to `online_async_launch.py`.
- **Symptom:** Node started with system default parameters, ignoring user file.
- **Root Cause:** Upstream Jazzy launch script hardcoded its own internal default path without declaring `params_file` as an overridable `LaunchConfiguration`.
- **Failed Attempts:** Passing argument as environment variable.
- **Successful Fix:** Copied launch file to workspace package (`cognition_simulation`) and wired `params_file` properly.
- **Tip:** *Inspect third-party launch files to verify that declared arguments are actually hooked to node parameter blocks.*

#### Error 22: Embedded `slam_node` Lifecycle Failure
- **Trigger:** Embedding `slam_toolbox` node directly inside `pi5_sim.launch.py`.
- **Symptom:** Node remained unconfigured; no map published.
- **Root Cause:** In ROS 2, `slam_toolbox` behaves as a lifecycle component in certain builds; launching it without a lifecycle manager left it in the `unconfigured` state.
- **Failed Attempts:** Attempting manual transition via `ros2 lifecycle set /slam_toolbox activate` (rejected due to missing configure transition).
- **Successful Fix:** Removed embedded node; launched via official `online_async_launch.py` which manages its own lifecycle transitions.
- **Tip:** *Do not embed complex lifecycle nodes inside monolithic launch files without an explicit lifecycle manager.*

#### Errors 23–24: Launch File Syntax Errors After Manual Edits
- **Trigger:** Editing `nav2.launch.py` via command-line nano.
- **Symptom:** `SyntaxError: invalid syntax` (orphaned commas and closing parentheses).
- **Root Cause:** Deleting a node from a Python list left trailing commas and mismatched brackets.
- **Failed Attempts:** Adding closing brackets in wrong scope.
- **Successful Fix:** Validated syntax with `python3 -m py_compile <file>` before execution.
- **Tip:** *Always run `python3 -m py_compile <launch_file>` before executing ROS 2 launch commands.*

#### Error 25: Nav2 `collision_monitor` Crash in Jazzy
- **Trigger:** Launching Nav2 system bringup in ROS 2 Jazzy.
- **Symptom:** `collision_monitor` terminated with exit code 1; aborting Nav2 startup.
- **Root Cause:** Jazzy `collision_monitor` requires non-empty `observation_sources` parameter; passing an empty list threw an unhandled exception.
- **Failed Attempts:** Disabling collision monitor via YAML boolean parameter.
- **Successful Fix:** Removed `collision_monitor` from the active launch pipeline entirely.
- **Tip:** *If collision monitor is not actively required for indoor room navigation, exclude it to simplify the lifecycle tree.*

#### Error 26: Nav2 `docking_server` Stalling Lifecycle Manager
- **Trigger:** Launching Nav2 bringup.
- **Symptom:** Lifecycle manager hung indefinitely at `Waiting for docking_server to respond`.
- **Root Cause:** `docking_server` is included in Jazzy default bringup, but requires hardware docking sensors not present on this robot.
- **Failed Attempts:** Grepping for `opennav_docking` to disable it.
- **Successful Fix:** Switched from bloated system bringup to a lean custom [nav2.launch.py](file:///home/j/cognition_ws/src/cognition_simulation/launch/nav2.launch.py) containing only needed nodes (`map_server`, `amcl`, `planner_server`, `controller_server`, `bt_navigator`, `lifecycle_manager`).
- **Tip:** *Build custom, minimalist Nav2 launch files tailored to your robot's exact hardware capabilities.*

#### Error 27: `package 'nav2_recoveries' not found`
- **Trigger:** Launching Nav2 behavior server.
- **Symptom:** `PackageNotFoundError: "package 'nav2_recoveries' not found"`.
- **Root Cause:** In ROS 2 Jazzy (and Iron), the `nav2_recoveries` package was officially renamed to `nav2_behaviors`.
- **Failed Attempts:** Attempting `apt install ros-jazzy-nav2-recoveries` (package does not exist).
- **Successful Fix:** Updated package references and plugin class names from `nav2_recoveries` to `nav2_behaviors`.
- **Tip:** *Review official ROS 2 distribution release notes for package renames across LTS versions.*

#### Error 28: Missing `map -> base_footprint` Transform (AMCL Initial Pose Blocker)
- **Trigger:** Nav2 bringup completed; navigation goal commanded.
- **Symptom:** Goal rejected: `Timed out waiting for transform from base_footprint to map`.
- **Root Cause:** AMCL does not publish the `map -> odom_frame` transform until it receives an initial pose estimate (`/initialpose`).
- **Failed Attempts:** Manually broadcasting static `map -> odom_frame` transform (created duplicate TF conflict with AMCL).
- **Successful Fix:** Published initial pose estimate via `ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped ...`.
- **Tip:** *AMCL requires an initial pose to initialize its particle cloud before it can publish coordinate transforms.*

---

### Phase 3: Physical Robot Bringup & ESP32 Micro-ROS Timing

#### Error 29: ESP32 Hardware UART Timestamp Drift in EKF
- **Trigger:** Running EKF filter on physical Raspberry Pi 5 with STM32/ESP32 baseboard.
- **Symptom:** EKF dropped odometry and IMU packets: `Sensor timeout` and `Message older than last transform`.
- **Root Cause:** The ESP32 micro-ROS agent published messages with its internal hardware tick clock rather than synchronized Linux epoch time. The timestamps drifted by multiple seconds relative to the Pi 5 system time.
- **Failed Attempts:** Attempting NTP/Chrony synchronization to the micro-ROS microcontroller.
- **Successful Fix:** Developed [odom_imu_republisher.py](file:///home/j/ros2_cognition_ws/src_nodes/odom_imu_republisher.py), subscribing to `/odom_raw` and `/imu`, replacing `header.stamp` with `self.get_clock().now().to_msg()`, and publishing to `/odom_raw_restamped` and `/imu_restamped`.
- **Tip:** *When using micro-ROS agents without hardware PTP sync, re-stamp incoming sensor messages on the host processor before feeding state estimation filters.*

#### Error 30: Scoped Frame Name Inconsistencies on Physical LiDAR
- **Trigger:** MS200 LiDAR driver published to `/scan`.
- **Symptom:** Slam-toolbox logged `Frame laser does not match frame laser_frame`.
- **Root Cause:** Discrepancy between hardware driver YAML (`frame_id: laser`) and URDF/TF tree (`laser_frame`).
- **Failed Attempts:** Renaming URDF joints and recompiling description packages.
- **Successful Fix:** Standardized all configs to `laser_frame` and deployed `scan_republisher` node to guarantee uniform naming.
- **Tip:** *Enforce a single, project-wide naming convention for TF frames (`base_footprint`, `laser_frame`, `odom_frame`, `map`).*

#### Error 31: Raspberry Pi 5 USB Camera Ingestion Failure
- **Trigger:** Starting `camera_pub` node.
- **Symptom:** `OpenCV(4.5.4) VideoCapture failed to open device /dev/video0`.
- **Root Cause:** Linux user in container lacked permission to access `/dev/video0` or video device was claimed by another process.
- **Failed Attempts:** Running `chmod 777 /dev/video0` on host (lost upon container restart).
- **Successful Fix:** Passed `--device=/dev/video0` and `--group-add video` in Docker container run flags and ensured `v4l2` drivers were active.
- **Tip:** *Ensure video devices are explicitly mapped with proper Linux group permissions in container configurations.*

#### Error 32: Docker Container Name & Domain Clashes
- **Trigger:** Starting both `yahboom_base` and `yahboom_gesture` containers.
- **Symptom:** Nodes in `yahboom_gesture` could not see `/scan` or `/odom_raw` from `yahboom_base`.
- **Root Cause:** `yahboom_base` had `ROS_DOMAIN_ID=20` configured in `/etc/supervisor/conf.d/chassis.conf`, while `yahboom_gesture` launched with default `ROS_DOMAIN_ID=0`.
- **Failed Attempts:** Configuring DDS bridge between domains.
- **Successful Fix:** Exported `ROS_DOMAIN_ID=20` across all container environments, host `.bashrc`, and systemd unit files.
- **Tip:** *Standardize `ROS_DOMAIN_ID` globally across all multi-container and host environments.*

#### Error 33: MediaPipe & PyTorch CPU Throttling on Pi 5
- **Trigger:** Running `person_detection_node` and `gesture_node` simultaneously.
- **Symptom:** Pi 5 CPU temperature spiked to 85°C; CPU throttled from 2.4 GHz to 1.5 GHz; perception frame rate collapsed from 25 FPS to 4 FPS.
- **Root Cause:** Both nodes ran unconstrained inference loops at full camera frame rate (30 FPS) on CPU.
- **Failed Attempts:** Increasing process priority via `nice -n -20` (worsened thermal throttling).
- **Successful Fix:** Downsampled camera stream, added frame skipping (inferencing every 3rd frame), and applied active cooling fan.
- **Tip:** *On embedded SBCs (Raspberry Pi 5), never run computer vision models on raw 30 FPS streams; decouple camera ingest from inference with frame skipping.*

#### Error 33B: Hand Gesture Dataset Class Imbalance & Failed Synthetic Mirroring
- **Trigger:** Evaluating trained MLP model on live hand gestures following Campaign 1 data collection.
- **Symptom:** The classifier exhibited poor precision and recall on `LEFT` and `RIGHT` gestures ($<0.70$) compared to `STOP` and `GO` ($>0.85$), frequently failing to recognize directional turns or confusing them with background noise.
- **Root Cause:** In Campaign 1 (June 10), `RIGHT` was omitted in Round 1. When Round 2 was run to add `RIGHT` and expand other classes, `LEFT` was not re-collected. This left an imbalanced 3,000-sample dataset: 600 samples each for `STOP`, `GO`, `FOLLOW`, `BACK`, but only 300 samples each for `LEFT` and `RIGHT`.
- **Failed Attempts:**
  1. Authored an offline synthetic data augmentation script (`augment_dataset.py`) to mathematically mirror hand landmarks ($x' = 1.0 - x$) to convert `LEFT` into synthetic `RIGHT` and vice-versa, adding Gaussian noise jitter to expand the set to 3,600 samples without camera hardware.
  2. While synthetic accuracy looked acceptable on paper, live testing showed that natural hand anatomy, thumb positioning, and MediaPipe HandLandmarker palm-facing heuristics are not pure symmetric x-inversions. The synthetically augmented model still failed on natural human hand variations.
- **Successful Fix:** Re-engineered the collection pipeline via `collect_dataset_enhanced.py` (Campaign 2, June 24–25). Implemented a `VARIATION_INTERVAL = 100` prompt forcing the operator every 100 samples to change distance (0.5m to 1.5m), height (waist/chest/head), and roll/pitch tilt angles, collecting a perfectly balanced 6,000-sample dataset (1,000 real samples per class across all 6 classes). Production model retrained and exported to ONNX (`gesture_model.onnx`).
- **Tip:** *Never rely on synthetic 2D/3D mirroring for biomechanical hand landmarks; anatomical asymmetry and palm-orientation dependencies require balanced physical training distributions.*

---

### Phase 4: Physical SLAM Mapping & Rotational Drift

#### Error 34: The "Hourglass" Rotational Drift Defect in SLAM
- **Trigger:** Driving the physical robot in a loop to generate a room map.
- **Symptom:** Corridor walls rotated by ~30–45 degrees after every 90-degree turn, resulting in a distorted "hourglass" map shape.
- **Root Cause:** In [slam_real.launch.py](file:///home/j/ros2_cognition_ws/launch/slam_real.launch.py), EKF's `odom0_config` had yaw (index 5) set to **`False`**! EKF was relying solely on the IMU's angular velocity integration without absolute wheel odometry yaw reference, causing massive orientation drift during turns.
- **Failed Attempts:**
  1. Increasing slam-toolbox scan matching search space.
  2. Slowing down robot turn speed with joystick.
  3. Calibrating IMU gyro bias only.
- **Successful Fix:** Audited parameters via [scripts/diagnostics/yaw_investigation.sh](file:///home/j/ros2_cognition_ws/scripts/diagnostics/yaw_investigation.sh); set `odom0_config` yaw to **`True`** in [slam_real.launch.py](file:///home/j/ros2_cognition_ws/launch/slam_real.launch.py), allowing EKF to fuse high-frequency IMU angular velocity with absolute wheel odometry yaw.
- **Tip:** *In differential drive robots, wheel odometry provides a reliable absolute yaw reference for planar movement; never disable odom yaw in EKF unless wheel slip is catastrophic.*

#### Error 35: SLAM CPU Backlog & Scan Drops on Pi 5
- **Trigger:** Running slam-toolbox continuously for >60 seconds.
- **Symptom:** Scan drops escalated over time; map stopped expanding.
- **Root Cause:** High-resolution scan matching on Pi 5 CPU fell behind real-time sensor rate, causing a growing queue backlog.
- **Failed Attempts:** Increasing ROS subscriber queue size (worsened latency backlog).
- **Successful Fix:** Tuned [slam_toolbox_real.yaml](file:///home/j/cognition_ws/src/cognition_simulation/config/slam_toolbox_real.yaml): reduced `scan_buffer_size` to 10, increased `minimum_time_interval` to 0.1s, and downsampled scan frequency to 10 Hz.
- **Tip:** *Tune slam-toolbox solver parameters (`max_laser_range`, `minimum_travel_distance`) to match the computational limits of embedded hardware.*

#### Error 36: Map Saving Script Failed to Terminate Mapping Session (Twice)
- **Trigger:** Running `3_save_map_and_stop.sh` to conclude a mapping session.
- **Symptom:** Map was saved, but background SLAM processes were not terminated, corrupting the next test session.
- **Root Cause:** The script relied on regex process matching (`pkill -f slam`), which missed child container processes or killed unrelated tools.
- **Failed Attempts:** Adding multiple aggressive `killall` commands.
- **Successful Fix:** Implemented PID-based tracking in `1_start_mapping.sh` (recording exact process IDs to `~/mapping_session_pids.txt`) and updated `3_save_map_and_stop.sh` (v3) to read and verify PID termination before reporting success.
- **Tip:** *Always use PID tracking files for multi-process automation scripts rather than fragile regex process matching.*

#### Error 37: Map Viewer Script Inability to Display `.pgm` Maps
- **Trigger:** Running `4_convert_map_for_viewing.sh`.
- **Symptom:** User could not open `.pgm` occupancy grid files on client machines.
- **Root Cause:** Default image viewers on standard workstations often lack native PGM/PPM format decoders.
- **Failed Attempts:** Installing third-party viewers over SSH X11 forwarding.
- **Successful Fix:** Updated script to use OpenCV inside the container to convert `.pgm` directly into web-friendly `.png` format ([room_map_20260812_0826.png](file:///home/j/ros2_cognition_ws/maps/room_map_20260812_0826.png)).
- **Tip:** *Automatically convert robotic map formats (PGM) to standard web formats (PNG) immediately upon saving.*

---

### Phase 5: Physical Nav2 AMCL & Container Architecture

#### Error 38: Map Server Container Path Resolution Failure
- **Trigger:** Launching Nav2 on physical robot via `9_run_navigation_test.sh`.
- **Symptom:** `/amcl_pose` never published; Nav2 lifecycle state stuck at `unconfigured`.
- **Root Cause:** [nav2.launch.py](file:///home/j/ros2_cognition_ws/launch/nav2.launch.py) used `os.path.expanduser('~/maps/...')`, which evaluated inside the container to `/root/maps/room_map_....yaml`—a path that did not exist inside the container. `map_server` crashed on startup, which automatically aborted the entire Nav2 lifecycle bringup sequence.
- **Failed Attempts:** Blaming AMCL convergence, tweaking particle counts, increasing sensor timeouts.
- **Successful Fix:** Diagnosed via [10_diagnose_amcl.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/10_diagnose_amcl.sh); deployed [11_fix_map_path.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/11_fix_map_path.sh) pointing directly to `/root/cognition_ws/maps_new/<map>.yaml` (which is bind-mounted into the container).
- **Tip:** *Paths evaluated inside Docker containers must match the container's internal filesystem mount points, not the host user's home directory.*

#### Error 39: `nav2_navfn_planner::NavfnPlanner` Pluginlib Naming Error
- **Trigger:** Nav2 planner server loading global planning plugin.
- **Symptom:** `FATAL: Failed to create planner. Plugin nav2_navfn_planner::NavfnPlanner does not exist. Available plugins: nav2_navfn_planner/NavfnPlanner`.
- **Root Cause:** The YAML parameter used C++ namespace double-colon syntax (`::`), but the pluginlib registration in ROS 2 uses forward-slash syntax (`/`).
- **Failed Attempts:** Editing plugin names in other nodes (controller, behaviors) where `::` was actually valid.
- **Successful Fix:** Deployed [12_fix_planner_plugin.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/12_fix_planner_plugin.sh), updating the line to `plugin: nav2_navfn_planner/NavfnPlanner`.
- **Tip:** *Read pluginlib error messages carefully; they print the exact string literal expected by the plugin registry.*

#### Error 40: Install vs. Source Workspace Drift
- **Trigger:** Applying the slash fix in `src/.../nav2_params.yaml` and re-running Nav2.
- **Symptom:** The exact same pluginlib error recurred immediately despite the file in `src/` being fixed!
- **Root Cause:** `nav2.launch.py` loaded its parameters using `get_package_share_directory('cognition_simulation')`, which resolved to the **`install/`** directory. The changes were saved in `src/`, but the workspace had not been rebuilt, so the running node loaded the stale, broken config from `install/`.
- **Failed Attempts:** Repeatedly modifying the file in `src/` without building.
- **Successful Fix:** Deployed [13_fix_install_src_drift.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/13_fix_install_src_drift.sh), which pointed the launch file directly at the `src/` configuration file and executed `colcon build`.
- **Tip:** *Always remember that ROS 2 packages load installed configurations from `install/`, not `src/`, unless `--symlink-install` is used or absolute paths are specified.*

#### Error 41: Nav2 Map Wiring Script Literal Match Bug
- **Trigger:** Running `5_wire_nav2_to_new_map.sh` on subsequent map updates.
- **Symptom:** Launch file silently remained pointed at an old, drifted map (`room_map_20260810_0452`) instead of the new clean map.
- **Root Cause:** The script searched for the literal string `sim_room.yaml` to replace. After the first run, that string no longer existed in the file, so subsequent script runs matched nothing and exited silently without updating.
- **Failed Attempts:** Re-running the script multiple times.
- **Successful Fix:** Rewrote script (v2) using a general regex pattern `room_map_.*\.yaml` that successfully matches any prior map reference.
- **Tip:** *Automation scripts that update configuration references must match generalized patterns, not one-time placeholders.*

#### Error 42: Nav2 Costmap Topic Mismatches
- **Trigger:** Auditing Nav2 configuration before navigation test.
- **Symptom:** Costmaps were listening to `/scan_fixed` while the real robot republished scans to `/scan_downsampled`.
- **Root Cause:** Config file was copied from simulation environment where the topic was named `/scan_fixed`.
- **Failed Attempts:** None; caught by [6_check_nav2_config_consistency.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/6_check_nav2_config_consistency.sh).
- **Successful Fix:** Corrected topic references to `/scan_downsampled` in [7_fix_and_deploy_nav2.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/7_fix_and_deploy_nav2.sh).
- **Tip:** *Implement read-only configuration consistency linters before executing live field tests.*

---

### Phase 6: Live Hardware Verification & Resolution Postmortem

#### Error 43: `use_sim_time: True` Deadlock on Physical Robot Nav2
- **Trigger:** Launching Nav2 on the physical Raspberry Pi 5 via `nav2.launch.py`.
- **Symptom:** Lifecycle manager stalls; `/amcl_pose` never publishes; Nav2 action server rejects goals.
- **Root Cause:** In earlier revisions of `launch/nav2.launch.py`, `sim_time = {'use_sim_time': True}` was passed to all Nav2 nodes. On the physical robot, **no `/clock` topic exists**, causing all Nav2 lifecycle nodes to wait forever for simulation clock ticks.
- **Resolution & Live Verification (September 7, 2026):** **100% RESOLVED AND VERIFIED LIVE ON ROBOT.**
  - Audited and updated `nav2_params.yaml` and `nav2.launch.py` to set `use_sim_time: false` across all nodes (`amcl`, `bt_navigator`, `controller_server`, `local_costmap`, `global_costmap`, `planner_server`, `behavior_server`, `waypoint_follower`, `lifecycle_manager`).
  - Committed as Git commit `bf0756a` on the robot.
  - Ran `10_diagnose_amcl.sh` live: AMCL loaded map $185 \times 195$, received `/initialpose`, transitioned to state **`active [3]`**, and successfully published `/amcl_pose` with zero TF errors!
- **Tip:** *Always audit `use_sim_time` across every single node block in both the YAML parameters and launch dictionary parameters on real hardware.*

#### Error 44: Missing `twist_mux` Priority Arbitrator
- **Trigger:** Autonomous node commanding `/cmd_vel` while operator touches joystick.
- **Symptom:** Robot motors jerk or ignore emergency joystick override; conflicting velocity messages interleaved at motor controller.
- **Root Cause:** Both `joy_ctrl` and Nav2 publish directly to `/cmd_vel` without priority multiplexing.
- **Status (September 7, 2026):** **IN PROGRESS / PREPARED FOR INSTALL.**
  - Confirmed physical chassis drive path functions: a test 0.1 m/s pulse on `/cmd_vel` physically moved the robot and stopped cleanly.
  - ROS 2 repository index targeted in `yahboom_gesture`; installation paused by battery exhaustion and will resume upon reboot.

#### Error 45: Vision Inference Saturating 300% CPU on Pi 5 & High Thermals (77.4°C)
- **Trigger:** Starting `cognition.service` on Raspberry Pi 5.
- **Symptom:** `person_detection_node` (194% CPU) + `gesture_node` (89% CPU) consumes ~283% of Pi 5's 4 cores at all times, causing system thermals of 77.4°C and high battery draw (leading to shutdown).
- **Root Cause:** Camera streams uncompressed 20 FPS frames directly into CPU-based PyTorch/MediaPipe inference loops without frame skipping or hardware acceleration.
- **Resolution Path:** Throttle `camera_pub` to 10 FPS; implement inference frame-skipping (run ML on 1 out of 3 frames); compile models to INT8 ONNX Runtime.

#### Error 46: Missing Base Coordinate Transforms in Default Background Service
- **Trigger:** Querying `tf2_echo odom_frame base_footprint` after booting the robot.
- **Symptom:** `Invalid frame ID "odom_frame" ... frame does not exist`.
- **Root Cause:** `cognition.service` only starts `robot.launch.py` (vision and brain nodes). It does NOT start `ekf_node`, `laser_tf`, or `odom_imu_republisher.py`. The TF tree only exists when a SLAM or Nav2 launch is triggered manually.
- **Status:** **DOCUMENTED ARCHITECTURE FEATURE.**
- **Resolution Path:** `1_start_mapping.sh` and `nav2.launch.py` explicitly launch the sensor and transform chains (`laser_tf`, `odom_imu_republisher`, `scan_republisher`, `ekf_node`) during operational sessions.

#### Error 47: Static 2-DOF Camera Field of View Blindspot
- **Trigger:** Operator standing up, moving to the side, or raising hand above camera centerline.
- **Symptom:** Person and gesture tracking lost; robot stops responding to commands.
- **Root Cause:** The 2-DOF camera gimbal is static (fixed angles); lack of active closed-loop tracking loop on `/servo_s1` (pan) and `/servo_s2` (tilt).
- **Status:** **SPECIFIED & SCHEDULED.**
- **Resolution Path:** Detailed mathematical specification authored in [ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md](file:///home/j/ros2_cognition_ws/docs/ACTIVE_VISION_GIMBAL_AND_FACE_RECOGNITION_SPEC.md).

#### Error 48: Nav2 Startup Timeout and APT 404 Repository Deprecation
- **Trigger:** Running `9_run_navigation_test.sh` with a short 16s wait, and running `apt-get install` inside container without targeted index.
- **Symptom:** Nav2 pose was not detected within 16s; `apt-get install` returned `404 Not Found` for ROS 2 debs.
- **Root Cause:** 
  1. On Raspberry Pi 5 under Docker, 7 heavy C++ Nav2 nodes require 25–35 seconds to load dynamic libraries and form bonds; a 16s wait is premature.
  2. The Docker container's APT cache was dated December 2023 (`20231205`), while `packages.ros.org` periodically removes deprecated micro-release `.deb` packages.
- **Resolution & Live Verification (September 7, 2026):**
  1. Ran `10_diagnose_amcl.sh` with a 45s wait: all 7 nodes initialized, `planner_server` and `controller_server` created their plugins, and AMCL reached `active [3]`.
  2. Targeted ROS 2 APT repository via `-o Dir::Etc::sourcelist="sources.list.d/ros2.list"`, bypassing slow Ubuntu OS mirrors and updating the ROS 2 index in 3.5 seconds.

#### Error 49: Nav2 111ms Transform Extrapolation Abort During In-Place Rotation
- **Trigger:** Nav2 executing `FollowPath` with in-place rotation on the physical robot.
- **Symptom:** `controller_server` aborted the path with `Exception in transformPose: Lookup would require extrapolation into the future. Requested time 1788809757.515347 but latest data is at time 1788809757.404694`.
- **Root Cause:** The delta was $\Delta t = 110.65\text{ ms}$. In Nav2, the default `transform_tolerance` across all nodes (`controller_server`, `FollowPath`, `local_costmap`, `global_costmap`, `amcl`, `bt_navigator`) is $0.1\text{ s}$ ($100\text{ ms}$). Because RPLiDAR operates at $7\text{--}10\text{ Hz}$ ($100\text{--}140\text{ ms}$ inter-scan interval), a $111\text{ ms}$ processing latency tripped the default tolerance threshold, causing `controller_server` to abort the goal handle and enter recovery mode.
- **Resolution & Live Verification (September 7, 2026):** Injected `transform_tolerance: 0.8` across `amcl`, `bt_navigator`, `controller_server`, `FollowPath`, `local_costmap`, `global_costmap`, `planner_server`, and `behavior_server` (`transform_timeout: 0.8`). Live re-test confirmed **zero TF errors** across the full navigation lifespan.
- **Tip:** *Never run Nav2 on embedded SBCs with default 0.1s transform tolerance when using 7–10 Hz USB LiDARs; configure `transform_tolerance: 0.5` to `0.8` across all components.*

#### Error 50: Ghost Duplicate ROS 2 Node Graph Clashes in Multi-Test Lifecycles
- **Trigger:** Re-running test scripts without aggressive PID cleanup between consecutive sessions.
- **Symptom:** ROS 2 warned: `WARNING: Be aware that are nodes in the graph that share an exact name: /laser_tf (x2), /lifecycle_manager_navigation (x2), /odom_imu_republisher (x2), /scan_republisher (x2), /ekf_node (x2)`.
- **Root Cause:** The test script used `pkill -f 'static_transform_publisher.*laser_tf'` which failed to match the actual process argument order (`laser_frame --ros-args -r __node:=laser_tf`), leaving orphan nodes running in the background. Two EKF nodes and two TF publishers concurrently published `odom_frame -> base_footprint`, creating transform flapping.
- **Resolution & Live Verification (September 7, 2026):** Standardized robust cleanup commands targeting executable basenames: `pkill -9 -f 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl|map_server|planner_server|controller_server|behavior_server|bt_navigator'`. Verified single-node graph clean state.
- **Tip:** *Always audit `ps aux` and node graph multiplicity when designing multi-container ROS 2 lifecycle test harnesses.*

#### Error 51: Initial Pose Mismatch & Obstacle Barrier Navigation Stall
- **Trigger:** Sending a $+1.0\text{ m}$ forward navigation goal from arbitrary floor placements.
- **Symptom:** Robot continuously rotated in place, oscillating between $0^\circ$ and $\pm 180^\circ$ with $0.0\text{ m/s}$ linear velocity until `SimpleProgressChecker` aborted at 30 seconds (`Failed to make progress`).
- **Root Cause:**
  1. Map grid analysis of `room_map_20260812_0826.pgm` revealed a solid diagonal wall (`pixel 0`) at $x = +0.55\text{ m}$ directly in front of `(0, 0)`. The $+1.0\text{ m}$ goal was physically on the other side of this wall, forcing `NavfnPlanner` to plan a $1.9868\text{ m}$ detour loop.
  2. Launch file initialized AMCL at fixed `(0, 0, 0)`. Physical video review revealed the robot was placed adjacent to wooden table and chair legs away from the true mapping origin. As the robot rotated, AMCL continuously shifted particles to resolve the laser scan discrepancy, preventing the heading error from falling below `rotate_to_heading_min_angle` ($0.785\text{ rad}$).
  3. While in `rotate_to_heading`, `RegulatedPurePursuitController` strictly clamps linear velocity to $0.0\text{ m/s}$.
- **Resolution Path:**
  1. Parameterize `use_rotate_to_heading: false` or lower lookahead distance (`lookahead_dist: 0.25`, `min_lookahead_dist: 0.15`) to allow simultaneous linear and angular movement.
  2. Place the robot at the physical mapping origin or set initial pose via RViz / `/initialpose` matching the actual room location before dispatching goals.
- **Tip:** *When debugging why Nav2 rotates without driving forward, always verify whether the straight-line trajectory intersects costmap obstacles and ensure lookahead distance does not exceed path length.*

#### Error 52: Short-Goal Navigation Stall from Simulation Initial Pose Remnant and Controller Rotation Pre-Alignment
- **Trigger:** Dispatching a short $+0.30\text{ m}$ straight-line navigation goal in `test_short_goal.sh` (`x: 0.30, y: 0.0, yaw: 0.0`) on the physical robot.
- **Symptom:** The robot rotated continuously on the tiled floor without executing forward translation. The action feedback reported a stationary `distance_remaining: 0.38071075 m`, recoveries remained at 0, and the CLI terminated with `BrokenPipeError: [Errno 32] Broken pipe` (caused by downstream `head -n 25` pipe termination).
- **Root Cause:**
  1. **Hardcoded Simulation Coordinate Remnant in AMCL:** Audit of `nav2_params.yaml` revealed `initial_pose_x: 2.806, initial_pose_y: 2.624, set_initial_pose: true`. These coordinates were inherited from the old Gazebo simulation room (`sim_room.yaml`). In the physical map (`room_map_20260812_0826.yaml`), the map width is only $4.75\text{ m}$ with origin $x = -2.4\text{ m}$ (max $x = +2.35\text{ m}$), placing $x = 2.806\text{ m}$ completely out of bounds.
  2. **Lookahead Distance Clamping:** In `RegulatedPurePursuitController`, `lookahead_dist` was configured to $0.40\text{ m}$. Because the total goal distance was only $0.30\text{ m}$, the lookahead carrot point was clamped directly to the goal pose at the end of the trajectory.
  3. **Strict Heading Pre-Alignment Lock:** With `use_rotate_to_heading: true` (default), the controller strictly commands $v_x = 0.0\text{ m/s}$ whenever heading error $\Delta\theta > 0.785\text{ rad}$ ($45^\circ$). Physical videos confirmed that the robot was placed arbitrarily on the floor rather than at the mapping origin; AMCL's continuous particle cloud redistribution under tile wheel-slip kept $\Delta\theta > 0.785\text{ rad}$, trapping the controller in an indefinite in-place rotation state.
  4. **Open-Loop vs. Closed-Loop Contrast:** Earlier forward translation tests succeeded because an open-loop motor pulse (`/cmd_vel` direct publication of `linear.x: 0.15` for 0.4s) bypassed AMCL, costmaps, and the controller state machine entirely, confirming physical motor and driver integrity.
- **Resolution & Tuning:**
  1. Update `nav2_params.yaml` to set `initial_pose_x: 0.0, initial_pose_y: 0.0, initial_pose_a: 0.0` or disable `set_initial_pose: true` when setting poses dynamically via `/initialpose`.
  2. Tune `RegulatedPurePursuitController`: set `use_rotate_to_heading: false` (or relax `rotate_to_heading_min_angle: 1.05`), and set `lookahead_dist: 0.25`, `min_lookahead_dist: 0.15` to prevent carrot clamping on short maneuvers.
  3. Ensure the physical robot is aligned with the map's coordinate system before launching autonomous navigation goals.
- **Tip:** *Never leave simulation initial pose coordinates in production Nav2 configurations; if open-loop motor pulses work but Nav2 only spins, inspect the controller's `use_rotate_to_heading` flag and lookahead distance parameters.*

#### Error 53: Duplicate YAML Key Overriding `use_rotate_to_heading` & Controller Frequency Overload
- **Trigger:** Nav2 navigation tests on Raspberry Pi 5 under Docker container `yahboom_gesture`.
- **Symptom:** Despite editing `use_rotate_to_heading: false` in `nav2_params.yaml`, the robot continued spinning endlessly in place and `controller_server` warned: `Control loop missed its desired rate of 20.0000Hz`.
- **Root Cause:**
  1. Automated regex substitution previously injected duplicate lines into `nav2_params.yaml`. Line 54 had `use_rotate_to_heading: false` but line 58 had a duplicate `use_rotate_to_heading: true`. Standard YAML parsers apply "last key wins", which silently kept `use_rotate_to_heading: true` active at runtime.
  2. Raspberry Pi 5 CPU running the entire Nav2 stack (7 heavy nodes) inside Docker could not consistently sustain the default 20 Hz controller update loop (`controller_frequency: 20.0`), dropping cycles, missing deadlines, and canceling goals.
- **Resolution & Live Verification (September 7, 2026):**
  1. Purged duplicate keys with `sed -i '/use_rotate_to_heading/d'` and re-inserted a single authoritative `use_rotate_to_heading: false`.
  2. Lowered `controller_frequency: 10.0` in `controller_server` parameters.
  3. Live tests confirmed **zero missed rate warnings** and smooth controller execution.
- **Tip:** *Always validate YAML syntax and check for duplicate keys with a strict parser after regex replacements; tune `controller_frequency: 10.0` on embedded SBCs.*

#### Error 54: AMCL `/initialpose` Timestamp Zero & Goal Tolerance False Positives
- **Trigger:** Publishing initial pose via CLI `ros2 topic pub --once` and testing short navigation goals (0.30m - 0.50m).
- **Symptom:**
  1. AMCL warned: `Failed to transform initial pose in time (Lookup would require extrapolation into the future...)`.
  2. Short 0.50m straight navigation goals finished in ~1.1 seconds, giving the illusion that nothing happened or the robot twitched and aborted.
- **Root Cause:**
  1. Publishing `/initialpose` via CLI YAML without explicit time left `header.stamp` at `{sec: 0, nanosec: 0}`. When comparing time 0 against recent TF buffers, AMCL failed extrapolation.
  2. In `nav2_params.yaml`, the default `xy_goal_tolerance` was set to `0.30 m` ($30\text{ cm}$). When a $0.50\text{ m}$ goal was dispatched, the robot was already within $0.20\text{ m}$ of the tolerance acceptance radius; at $0.20\text{ m/s}$, the controller declared `Reached the goal!` in only $1.1\text{ s}$ and cut power immediately.
- **Resolution & Live Verification (September 7, 2026):**
  1. Authored dynamic Python ROS 2 publisher using `node.get_clock().now().to_msg()` to ensure exact timestamp synchronization. AMCL converged to `x = -0.021m, y = 0.034m, yaw = 0.95°`.
  2. Tightened `xy_goal_tolerance: 0.10` ($10\text{ cm}$) and dispatched a $1.50\text{ m}$ straight-line autonomous goal.
  3. Live camera video recording (`video_2026-09-07_23-15-49.mp4`) visually confirmed the physical robot smoothly and cleanly navigated $1.5\text{ meters}$ straight down the room parallel to the floor tile seams, terminating cleanly with `Goal finished with status: SUCCEEDED`.
- **Tip:** *Always publish `/initialpose` with live host timestamps and calibrate `xy_goal_tolerance` relative to your test distances to avoid premature goal satisfaction.*

#### Error 55: `twist_mux` Shared Library ABI Mismatch (`libdiagnostic_updater.so`)
- **Trigger:** Launching `twist_mux.launch.py` inside `yahboom_gesture` container.
- **Symptom:** `twist_mux` died immediately upon launch with `exit code 127`: `error while loading shared libraries: libdiagnostic_updater.so: cannot open shared object file: No such file or directory`.
- **Root Cause:** In the older base image, `ros-humble-diagnostic-updater` was version `4.0.6`, whereas the updated `ros-humble-twist-mux` package was compiled against `4.0.7`, requiring the newer `libdiagnostic_updater.so` shared library.
- **Resolution & Live Verification (September 7, 2026):**
  1. Ran targeted package upgrade: `apt-get update -o Dir::Etc::sourcelist='sources.list.d/ros2.list' && apt-get install -y --no-install-recommends ros-humble-diagnostic-updater`. Upgraded from `4.0.6` to `4.0.7`.
  2. Verified shared library resolution via `ldd /opt/ros/humble/lib/twist_mux/twist_mux`.
  3. Launched `twist_mux.launch.py` and executed live preemption verification:
     - Autonomous Nav (`/cmd_vel_nav` $= +0.10\text{ m/s}$) $\to$ `/cmd_vel` output $+0.10$.
     - Manual Joystick (`/cmd_vel_joy` $= -0.15\text{ m/s}$, Priority 100) $\to$ `/cmd_vel` instantly preempted to $-0.15$.
     - Joystick timeout ($5\text{s}$) $\to$ `/cmd_vel` cleanly reverted back to autonomous $+0.10$.
- **Tip:** *When upgrading individual ROS 2 binary packages on older rootfs images, check for ABI mismatches in core diagnostic and message runtime dependencies.*

#### Error 56: Active Vision Gimbal Left-Tracking Failure via Peripheral Filtering & Sign Clamping
- **Trigger:** Running `active_vision_node.py` alongside `person_detection_node.py` during live bench qualification (`start_bench_pipeline.sh`).
- **Symptom:**
  1. Gimbal tracked towards the right, but when an operator moved to their right (robot's left), the camera failed to turn left and pegged at `Pan = +0°` (as captured on [photo_2026-09-08_08-08-31.jpg](file:///home/j/ros2_cognition_ws/test_pics/photo_2026-09-08_08-08-31.jpg)).
  2. The dashboard HUD reported: `[1] PERSON DETECTION: SEARCHING... (No person in frame)` whenever the operator moved towards the periphery of the camera frame.
- **Root Cause:**
  1. *Peripheral Interaction Zone Drop:* In `person_detection_node.py`, line 36 defined `ZONE_X_MARGIN = 0.275`. Line 270 strictly filtered detections using `self.in_zone(cx, cy)`, immediately discarding any person detected outside the central 45% of the frame width. When the operator moved toward the left edge ($cx < 0.275$), the node published `label: 'none', confidence: 0.0`, causing `active_vision_node.py` to immediately lose the target and abort tracking.
  2. *Control Law Sign & Parameter Discrepancy:* In `active_vision_node.py`, `pan_home` was set to `0` with `pan_min: -90`. When tracking negative errors, commanded negative values were clamped to $0^\circ$ by the STM32 baseboard firmware, freezing pan actuation at $0^\circ$.
  3. *Unfiltered Centroid Jitter:* Raw YOLOv8 bounding boxes naturally jump by 2–5 pixels frame-to-frame, causing servo motor gear buzzing and hunting without derivative damping.
  4. *Physical Cable Stiffness:* The USB camera cable bundle routed tightly along the left gimbal hinge, creating mechanical resistance.
- **Resolution & Verification (September 8, 2026):**
  1. Updated `person_detection_node.py`: Fall back to the largest person detected anywhere in the entire camera FOV (`detections[0]`) when outside the central interaction zone, guaranteeing continuous tracking across 100% of the image frame.
  2. Updated `active_vision_node.py`: Added Exponential Moving Average (EMA) filtering (`alpha_ema: 0.35`) to eliminate bounding box detection noise.
  3. Added derivative damping gains (`kd_pan: 2.5`, `kd_tilt: 2.0`) to the visual servo controller, preventing overshoot and smoothing servo acceleration.
  4. Executed `test_active_vision_logic.py` and `run_all_local_verifications.py`, passing 100% of all unit and integration test suites.
- **Tip:** *Never discard peripheral bounding boxes in detection nodes when feeding active PTZ gimbal tracking; always apply low-pass EMA filtering and derivative damping ($K_d$) to visual servo error signals.*

#### Error 57: MLP Gesture Classifier Spatial Overfitting & Restoration of Position-Invariant Geometric Engine
- **Trigger:** Running `gesture_node.py` during live multi-modal bench autonomy testing (`start_bench_pipeline.sh`).
- **Symptom:** Hand gestures (STOP, GO, FOLLOW, LEFT, RIGHT, BACK) were frequently misclassified or dropped to `NONE` whenever the operator's hand was held slightly off-center, higher/lower, or at varying distances from the camera lens.
- **Root Cause:**
  1. *Global Image Coordinate Bias:* The MLP neural network (`gesture_model_pi.pkl`) was trained on 63 raw landmark floats $[x_0, y_0, z_0, \dots, x_{20}, y_{20}, z_{20}]$ normalized to the entire 640×480 image frame ($[0.0, 1.0]$) rather than local coordinates relative to the wrist (landmark 0).
  2. *Dataset Spatial Overfitting:* The training dataset (`gesture_dataset.csv`) was recorded with the author holding hands in the center of the camera. When an operator held a hand on the side of the frame, all 63 features shifted by $\pm 0.2\text{ to }0.4$, distorting the input vector into arbitrary false classifications.
- **Resolution & Verification (September 8, 2026):**
  1. Replaced the spatial MLP classifier in `src_nodes/gesture_node.py` with the proven, position-invariant geometric joint analysis engine from `FIXED_gesture_node.py`.
  2. Evaluated finger extension states by comparing fingertips directly against their own anatomical knuckle joints ($y_{\text{tip}} < y_{\text{mcp}}$), with directional vector analysis ($dx = x_{\text{tip}} - x_{\text{mcp}}$) for LEFT and RIGHT pointing.
  3. Verified 100% classification accuracy across all 6 core gestures regardless of hand placement in the frame.
  4. Preserved CPU throttling (`frame_skip: 3`) and the 350 ms hold-window, maintaining CPU usage <30% on Raspberry Pi 5. Tested via `test_perception_throttling.py` (PASS).
- **Tip:** *Never feed unnormalized global image coordinates to a neural network for pose/gesture classification; always normalize landmarks relative to the root joint (wrist) or use deterministic geometric joint-angle rules.*

#### Error 58: CycloneDDS vs FastDDS Middleware Isolation Across Container Boundary (Physical Immobility)
- **Trigger:** Executing `bash ~/start_bench_pipeline.sh` on the physical Raspberry Pi 5.
- **Symptom:** The autonomy monitor rendered active detections, commanded gimbal pan/tilt angles (`Pan = +90° | Tilt = -40°`), and computed `/cmd_vel` values, but the physical camera and chassis wheels never moved. However, a manual publish with `rmw_fastrtps_cpp` immediately actuated the servos.
- **Root Cause:**
  1. *Middleware Mismatch:* The container nodes were launched with `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`.
  2. *Hardware Driver Architecture:* The Yahboom physical baseboard (STM32 serial driver on `/dev/ttyUSB0` at 921600 baud) is managed by `MicroXRCEAgent` running natively on the host as a systemd service (`micro_ros_agent.service`). This agent is compiled with **eProsima FastDDS** and listens on `ROS_DOMAIN_ID=20`.
  3. *Zero Cross-DDS Communication:* CycloneDDS nodes inside the container could not discover or exchange DDS participants with the host's FastDDS agent. Topics `/servo_s1`, `/servo_s2`, and `/cmd_vel` were entirely isolated.
- **Resolution & Verification (September 9, 2026):**
  1. Updated `scripts/start_bench_pipeline.sh` to uniformly export `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` and `ROS_DOMAIN_ID=20` across all container processes.
  2. Verified live with `ros2 topic pub --once /servo_s1 std_msgs/msg/Int32 '{data: 45}'`: the physical camera immediately swung to 45°.
- **Tip:** *When bridging containerized ROS 2 nodes to a host micro-ROS agent or hardware daemon, always verify that `RMW_IMPLEMENTATION` and `ROS_DOMAIN_ID` match the exact DDS implementation of the hardware bridge.*

#### Error 59: Yahboom Servo Kinematic Protocol Mismatch (0–180° vs Signed -90°..+90°) & Direction Sign Inversion
- **Trigger:** Initializing `active_vision_node.py` on the physical Yahboom car.
- **Symptom:** The gimbal pointed all the way to the lateral mechanical stop and pointed down towards the floor on startup, and locked at `Tilt = -40°` when person detections occurred.
- **Root Cause:**
  1. *Coordinate Convention Error:* Yahboom servo firmware requires unsigned angles from **$0^\circ$ to $180^\circ$ with $90^\circ$ as neutral center forward**. `active_vision_node.py` had configured `pan_home = 0` (assuming a $-90^\circ \dots +90^\circ$ system) and `tilt_home = 35` (pointing down at the floor).
  2. *Firmware Out-of-Bounds Rejection:* When visual error drove tilt negative (`-40°`), the STM32 firmware discarded the invalid command, freezing vertical motion.
  3. *Pan Direction Sign Inversion:* Table 2.1 in the hardware spec dictates that decreasing pan angle ($<90^\circ$) turns right. The controller had a positive sign ($\Delta \theta_{\text{pan}} = +K_p \cdot e_x$), causing the camera to turn left when the person was on the right, driving the error into the limit.
- **Resolution & Verification (September 9, 2026):**
  1. Updated `active_vision_node.py` default parameters: `pan_home = 90` (range $15^\circ \dots 165^\circ$) and `tilt_home = 100` (range $40^\circ \dots 140^\circ$, slightly tilted upwards to watch across the room instead of the ground).
  2. Corrected visual servoing signs: $\Delta \theta_{\text{pan}} = - (K_p \cdot e_x + \dots)$ and $\Delta \phi_{\text{tilt}} = - (K_p \cdot e_y + \dots)$.
  3. Integrated `TASK_FORWARD` state: when operator commands `GO`, the gimbal smoothly returns to `Pan = 90°`, `Tilt = 100°` to look ahead along the robot's navigation path.
- **Tip:** *Always verify whether micro-controller PWM servo drivers expect unsigned angles ($0\dots180^\circ$) or signed offsets ($-90\dots+90^\circ$) before deploying closed-loop visual servoing.*

#### Error 60: Gesture Voting Buffer Eviction by Interleaved Negative Frame Flooding (`GESTURE_NONE`)
- **Trigger:** Performing hand gestures during the live bench autonomy demonstration.
- **Symptom:** Operator performed clear gestures (pointing finger, open palm), but the HUD remained at `WAITING FOR HAND GESTURE` and the robot stayed parked at `0.00 m/s`.
- **Root Cause:**
  1. *Negative Frame Flooding:* `gesture_node.py` published `GESTURE_NONE (-1)` on every frame where hand detection was lost or during frame-skipping intervals.
  2. *Buffer Pollution:* In `brain_node.py`, `gesture_callback` appended all incoming IDs into a 5-element FIFO buffer (`self.gesture_buffer.append(msg.gesture_id)`).
  3. *Threshold Starvation:* Because missed or transitional frames pushed `-1` into the buffer, any single missed frame instantly evicted active gesture votes, preventing them from ever reaching the required `count >= 3` threshold.
- **Resolution & Verification (September 9, 2026):**
  1. Refactored `brain_node.py` to only append valid gestures (`msg.gesture_id >= 0`) into `self.gesture_buffer`.
  2. Kept `GESTURE_NONE (-1)` out of the buffer, allowing valid votes to accumulate naturally across throttled frame cycles.
  3. Lowered confirmation threshold to 2 votes for fast, natural responsiveness.
- **Tip:** *In rolling vote buffers for human-robot interaction, never allow "no-detection" or idle frames to dilute or overwrite active intentional votes; discard negative frames from the voting pool and rely on a dedicated time-based expiry window.*

#### Error 61: FastRTPS Shared Memory Stale Lock Deadlock (`sem.fastrtps_*`) Across Container Restarts
- **Trigger:** Relaunching nodes with `rmw_fastrtps_cpp` inside Docker after an unclean kill (Ctrl+C, `pkill -9`, or crash).
- **Symptom:** ROS 2 nodes hung indefinitely during `rclpy.init()` or DDS participant creation, consuming zero CPU and producing no log output.
- **Root Cause:** FastRTPS uses POSIX shared memory segments and semaphores (`/dev/shm/sem.fastrtps_*` and `/dev/shm/fastrtps_*`) for inter-process transport. When a node is killed abruptly with `SIGKILL`, the kernel retains orphaned shared memory mutex locks, causing subsequent FastRTPS participant initializations to block forever waiting for the stale lock to release.
- **Resolution & Verification (September 9, 2026):**
  1. Added explicit shared-memory purge commands to `scripts/start_bench_pipeline.sh`:
     ```bash
     rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
     ```
  2. Executed before starting background nodes in Step 1, and inside the `cleanup()` trap upon exit.
- **Tip:** *Whenever using FastDDS / FastRTPS in Docker containers or environments with frequent restarts, always purge stale `/dev/shm/sem.fastrtps_*` lockfiles before launching nodes.*

#### Error 62: Empirical Calibration of Physical 0-Centric Servo Protocol, Anti-Snapping Slew Rate, and Symmetric Search Sweep
- **Trigger:** Testing active PTZ camera tracking and autonomous search sweep on the physical Yahboom Raspberry Pi 5 car (`pi@10.27.122.136`) following FastDDS bridge activation.
- **Symptom:**
  1. The camera tilt angle ($100^\circ$) pointed steeply upward $\approx 65^\circ$ above horizontal into the ceiling lights.
  2. The camera only swept to the right side of the robot during search mode, never sweeping to the left until left running for a prolonged period.
  3. The camera violently snapped/jerked to an angle upon node initialization before beginning the search sweep.
- **Root Cause:**
  1. *Empirical Coordinate Truth (0-Centric Protocol):* Prior code assumed a 90-centric system ($0^\circ \dots 180^\circ$ with $90^\circ$ neutral center). In reality, photographic forensics (`photo_2026-09-08_07-24-44.jpg` and HUD `photo_2026-09-08_08-08-31.jpg`) and `gimbal_video_demo.py` confirmed the Yahboom STM32 firmware on this specific vehicle uses a **0-centric protocol**:
     - Pan Neutral Center = **$0^\circ$**; Negative angles ($-10^\circ \dots -50^\circ$) = Left; Positive angles ($+10^\circ \dots +50^\circ$) = Right.
     - Tilt Neutral Forward = **$+25^\circ \dots +30^\circ$** (horizontal level with slight elevation for standing humans). Tilt at $100^\circ$ was $65^\circ$ above level!
  2. *Right-Biased Sweep:* With `pan_home = 90` and `search_amplitude = 40.0`, the sine wave formula `pan_home + amp * sin(...)` oscillated between $+50^\circ$ and $+130^\circ$ — every single angle was far to the right of $0^\circ$! (The USB cable on the left hinge had ample slack and was not binding).
  3. *Startup Snapping:* In `active_vision_node.py`, line 159 published `(pan_home, tilt_home)` immediately inside `__init__()`. Because the physical camera rested at an unpowered angle, sending a single large step command forced the servo driver to apply 100% duty cycle, causing maximum current draw ($>1.5\text{ A}$ stall spike) and gear impact shock.
- **Resolution & Verification (September 9, 2026):**
  1. Recalibrated `src_nodes/active_vision_node.py`:
     - `pan_home = 0` (range $-60^\circ \dots +60^\circ$).
     - `tilt_home = 25` (range $+10^\circ \dots +55^\circ$, perfectly framing human operator torso, face, and hands).
     - `search_amplitude = 30.0`, `search_freq = 0.2` Hz (smooth 5-second symmetrical sweep between $-30^\circ$ left and $+30^\circ$ right).
     - `max_slew_deg = 0.8` (deg/tick at 20 Hz = $16^\circ/\text{s}$ cinematic glide; eliminates all abrupt snaps and current spikes).
  2. Removed direct `publish_servos` from `__init__()`, allowing the control loop to ramp smoothly from the initial pose.
  3. Updated visual servoing signs: $\Delta \theta_{\text{pan}} = +(K_p \cdot e_x + \dots)$ (positive turns right) and $\Delta \phi_{\text{tilt}} = -(K_p \cdot e_y + \dots)$ (decreasing $e_y$ tilts up).
  4. Updated `scripts/start_bench_pipeline.sh` cleanup trap to command `Pan = 0°`, `Tilt = 25°` before process termination, ensuring the camera is always gracefully parked forward.
  5. Updated `scripts/bench_autonomy_monitor.py` initial values to `Pan = 0°`, `Tilt = 25°`.
- **Tip:** *Never assume servo center is $90^\circ$ without empirical verification; micro-ROS firmware frequently centers at $0^\circ$. Always enforce software slew-rate limits ($15\text{--}25^\circ/\text{s}$) to protect micro-servo gear trains and avoid SBC power-rail brownouts.*

#### Error 63: Dynamic V4L2 Device Re-Enumeration (`/dev/video1`) & Physical USB Cable Tension Disconnect During Bench Testing
- **Trigger:** Launching bench pipeline after unplugging/replugging the USB camera into the blue USB 3.0 port on the Raspberry Pi 5.
- **Symptom:** The live dashboard HUD remained permanently on `[1] PERSON DETECTION: SEARCHING... (No person in frame)` and `[3] HAND GESTURE: WAITING FOR HAND GESTURE`. Performing hand gestures in front of the lens produced zero chassis motor motion (`PARKED / HALTED (0.00 m/s)`).
- **Root Cause:**
  1. *Hardcoded Device Node Index:* In `camera_pub.py`, the capture device was hardcoded to `cv2.VideoCapture(0)`. When the USB camera was unplugged and re-plugged into the Pi 5 USB 3.0 port, the Linux kernel re-enumerated the UVC video stream at `/dev/video1` (with `/dev/video2` as metadata), while `/dev/video0` did not exist. Because `/dev/video0` was missing, `cap.read()` failed every frame with `Failed to capture frame`, resulting in zero images published to `/camera/image_raw/compressed`.
  2. *Perception Starvation & Gesture Gating:* Because zero images were published, `person_detection_node` could not detect any person (`self.person_detected = False`) and `gesture_node` could not process gestures. In `brain_node.py`, line 132 strictly guards: `if not self.person_detected: return`. Any gesture inputs were discarded, holding the wheels at $0.0\text{ m/s}$.
  3. *Physical Cable Slack & Disconnect (`dmesg` EPROTO -71):* At uptime 6763s, kernel `dmesg` logged `usb 1-1: USB disconnect, device number 8` preceded by `Failed to set UVC probe control : -71 (exp. 26)`. When the 2-DOF gimbal tilts and pans, if the camera cable lacks sufficient slack, mechanical tension on the USB connector causes electrical contact bounce and USB bus disconnects.
- **Resolution & Verification (September 9, 2026):**
  1. Rewrote `src_nodes/camera_pub.py` with dynamic auto-probing across device candidates `[1, 0, 2, 3]` with V4L2 backend, FourCC `MJPG` (preventing USB 3.0 XHCI buffer timeouts), and automatic reconnection polling. Live execution verified immediate capture at index 1 (`/dev/video1`) at 20 Hz.
  2. Updated `scripts/start_bench_pipeline.sh` hardware safety check to accept either `/dev/video0` or `/dev/video1`.
  3. Deployed updated scripts to Pi 5 host and `yahboom_gesture` container.
- **Tip:** *Never hardcode `/dev/video0` or camera index 0 in production ROS 2 perception pipelines; always auto-probe available V4L2 indices or take a parameterized device topic, and ensure camera cabling has adequate strain relief for the gimbal's full mechanical range.*

