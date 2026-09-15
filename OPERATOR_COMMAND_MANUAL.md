# Autonomous Mobile Robot Cognition System: Operator Command Manual & Field Reference

**Project:** Development and Implementation of a Robotic Application for Human Intention Recognition Using Motion and Hand Gesture  
**Target Platform:** Yahboom 4WD Micro-ROS Mobile Robot (Raspberry Pi 5 8GB SBC, STM32 Micro-ROS Baseboard, MS200 LiDAR, 2-DOF Camera Gimbal)  
**Middleware:** ROS 2 Humble Hawksbill / FastDDS (Domain ID: 20)  
**Authors:** Eleana Osei Owusu (4121230024) & Joel Nii Adjetey Ahulu (4121230020)  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering  

---

## 1. Quick Start Guide (3-Step Turnkey Boot)

### Step 1: Connect to the Physical Robot
Ensure your laptop is on the same local Wi-Fi network as the robot, then open an SSH session:
```bash
ssh pi@10.27.122.136
```

### Step 2: Run System Pre-Flight Health Audit
Before dispatching any physical missions, verify container health, sensors, and serial bus:
```bash
python3 ~/cognition_ws/master_demo_menu.py --audit-only
```
*Look for:* `>> SYSTEM READINESS: 100% OPERATIONAL — ALL MISSIONS READY`.

### Step 3: Launch Turnkey Interactive Menu
```bash
python3 ~/cognition_ws/master_demo_menu.py
```
*(Or simply run `bash ~/menu.sh`).*

---

## 2. Master Interactive Demo Menu Matrix

When you run `master_demo_menu.py`, you are presented with eight dedicated operational options:

| Option | Mission / Utility | Description | Rosbag Output |
| :--- | :--- | :--- | :--- |
| **`[1]`** | **Pre-Flight Health Audit & Triage Matrix** | Probes Docker containers, USB camera (`/dev/video*`), STM32 UART (`/dev/ttyUSB0`), battery voltage, and AI models. | None |
| **`[2]`** | **Full 6-Gesture Evaluation & Teleoperation Suite** | Starts camera, YOLOv8, MediaPipe 19-D MLP classifier, Brain node, and Web Visualizer (`:8080`). Evaluates `GO`, `STOP`, `FOLLOW`, `LEFT`, `RIGHT`, and `BACK`. | Prompts `[y/N]` to record `gesture_follow_<timestamp>` |
| **`[3]`** | **Collaborative Follow-to-Map SLAM (Mode 1)** | Unmapped environment mode: Human leads the robot using `FOLLOW`; robot shadows footsteps and builds 2D metric SLAM map live. | Map YAML + PNG |
| **`[4]`** | **Collaborative Escort & Nav2 Patrol (Mode 2)** | Mapped environment mode: Localizes with AMCL and executes autonomous waypoint routes with touchless gesture preemption. | `patrol_<timestamp>` |
| **`[5]`** | **ISO 15066 Multimodal Safety Bubble Test** | Evaluates frontal planar LiDAR corridor (<0.35m) reactive halt and reverse acoustic beeper. | Console telemetry |
| **`[6]`** | **Export & Permanently Save Generated 2D Map** | Serializes active SLAM map to YAML and PNG formats into `~/cognition_ws/maps_new/`. | Saved Map files |
| **`[7]`** | **Emergency Chassis Halt (Instant Wheel E-Stop)** | Immediately publishes zero velocity (`0.0 m/s`) to `/cmd_vel` to halt all four motors. | None |
| **`[8]`** | **Thesis Telemetry & Trajectory Analysis Plotter** | Decodes recorded rosbag and generates publication plots (Figures 4.1 - 4.4). | Trajectory PNGs |

---

## 3. Raw Command Reference (Underlying Terminal Commands)

For oral defense or manual script execution, you can run any subsystem directly from the terminal.

### 3.1 Common ROS 2 Environment
Always prefix your commands or source this environment first:
```bash
export ROS_DOMAIN_ID=20
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
source /opt/ros/humble/setup.bash
source /root/cognition_ws/install/setup.bash 2>/dev/null || true
```

---

### 3.2 Individual Subsystem Raw Commands

#### A. Multi-Modal Gesture & Human-Following Suite (Mode 1 Bench)
```bash
# Standard interactive execution:
bash ~/start_bench_pipeline.sh

# With synchronized telemetry rosbag recording:
bash ~/start_bench_pipeline.sh --record
```
*Starts:* `camera_pub.py`, `person_detection_node.py` (with LSTM path predictor), `active_vision_node.py`, `gesture_node.py`, `brain_node.py`, `web_map_visualizer.py` (port 8080), and `bench_autonomy_monitor.py` HUD.

#### B. Live Island Minimalist Cockpit Visualizer
```bash
# Inside Docker container:
python3 -u /root/cognition_ws/web_map_visualizer.py

# Accessible on host laptop browser:
http://10.27.122.136:8080
```

#### C. Nav2 Autonomous Navigation & AMCL Localization Bringup
```bash
bash ~/start_nav2.sh
```
*Brings up:* MS200 LiDAR transform tree, EKF sensor fusion node (`odom_frame` -> `base_footprint`), `nav2_map_server` (`room_map_20260812_0826.yaml`), AMCL particle cloud filter, global costmap, local costmap, and DWB path planner.

#### D. Multi-Waypoint Autonomous Facility Patrol
```bash
bash ~/run_nav2_patrol.sh
```
*Executes:* Autonomous action navigation across inspection route ($P_1 \to P_2 \to P_3 \to P_4 \to P_1$) while recording non-saturating scalar telemetry to `~/cognition_ws/bags/patrol_<timestamp>`.

#### E. Single Named Waypoint Mission Dispatcher
```bash
docker exec -it yahboom_gesture bash -c "
    export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp;
    source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true;
    python3 /root/cognition_ws/mission_manager.py --mission CENTRAL_HUB_INSPECTION
"
```
*Available Missions:* `HOME_DOCK`, `CENTRAL_HUB_INSPECTION`, `NORTH_GALLERY_PATROL`, `EAST_LAB_TRANSIT`, `UNATTENDED_FACILITY_PATROL`.

#### F. Unified Autonomy & Preemption Master Launch
```bash
docker exec -it yahboom_gesture bash -c "
    export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp;
    source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true;
    ros2 launch /root/cognition_ws/src/cognition_simulation/launch/master_robot.launch.py
"
```

#### G. Collaborative Follow-to-Map SLAM Master Launch
```bash
docker exec -it yahboom_gesture bash -c "
    export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp;
    source /opt/ros/humble/setup.bash; source /root/cognition_ws/install/setup.bash 2>/dev/null || true;
    ros2 launch /root/cognition_ws/src/cognition_simulation/launch/follow_to_map.launch.py
"
```

#### H. Immediate Emergency Motor Halt (Instant E-Stop)
```bash
docker exec yahboom_gesture bash -c "
    export ROS_DOMAIN_ID=20; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp;
    source /opt/ros/humble/setup.bash >/dev/null 2>&1;
    ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}'
"
```

#### I. Manual Wireless Gamepad Teleoperation Service
```bash
# Check status of background joystick service:
bash ~/setup_joystick_service.sh status

# Restart joystick service if controller disconnects:
bash ~/setup_joystick_service.sh restart
```

---

## 4. LSTM Human Path Prediction Model

### How It Operates in the Stack
1. **Model Architecture:** 2-layer stacked LSTM (`hidden=64`, `layers=2`, dropout=0.2) taking the last 10 2D coordinates $(cx, cy)$ of the tracked operator and predicting the future trajectory coordinates 5 steps ahead.
2. **ONNX Acceleration:** Exported to `path_predictor.onnx` and executed by ONNX Runtime on the Pi 5 CPU using 2 dedicated intra-op threads (<3 ms latency).
3. **Anticipatory Gimbal Tracking:** In `active_vision_node.py`, the predicted horizontal position `det_msg.predicted_x` is blended ($70\%$ current center, $30\%$ predicted center) so the camera leads the walking human rather than lagging behind.
4. **Relevant ROS 2 Topics:**
   - Input: `/camera/image_raw/compressed`
   - Output: `/cognition/detection` (`Detection.msg` containing `center_x`, `center_y`, `velocity_x`, `velocity_y`, `direction`, and `predicted_x`).

---

## 5. Telemetry Rosbag Recording & Thesis Plot Generation

### Recording Lightweight Bags
When running `~/start_bench_pipeline.sh --record` or `~/run_nav2_patrol.sh`, the system records lightweight scalar topics:
- `/cognition/gesture` (gesture classification tokens and confidences)
- `/cognition/detection` (human bounding box and prediction coordinates)
- `/cmd_vel` & `/cmd_vel_gesture` (motor drive speeds)
- `/odom_raw` (wheel encoder ticks)
- `/scan` (LiDAR distance sweeps)
- `/tf` & `/tf_static` (coordinate transform frames)

### Generating Publication Trajectory Figures (Figs 4.1 – 4.4)
On the robot or workstation:
```bash
python3 scripts/plot_multi_waypoint_trajectory.py $(ls -td bags/*/ | head -1)
```
Generates:
- Trajectory path tracking plot
- Linear & angular velocity profiles over time
- Cross-track error (MAE / RMSE) metrics
- LiDAR obstacle distance clearance curve

---

## 6. Fault Triage & Recovery Matrix

| Observed Symptom | Probable Cause | Immediate Remediation Command |
| :--- | :--- | :--- |
| **`Cannot reach 10.27.122.136`** | Wi-Fi network switch or DHCP refresh | Check IP on local subnet: `nmap -sn 10.27.122.0/24`. If IP changed to `.135`, run `./scripts/sync_to_bot.sh 10.27.122.135`. |
| **Camera not opening in container** | USB disconnect / stale device node | Reseat USB cable on Pi 5 blue port, then run: `docker restart yahboom_gesture`. |
| **Motors not spinning on commands** | Micro-ROS serial link idle | Check host serial agent: `ps aux \| grep MicroXRCEAgent`. If dead, run: `sudo systemctl restart microros_agent.service`. |
| **Web visualizer blank map** | Map server not yet publishing `/map` | The Island Minimalist Cockpit automatically displays the offline preview. Launch `bash ~/start_nav2.sh` to stream live occupancy grid. |
| **FastDDS shared memory deadlock** | Stale POSIX lockfiles from killed process | Run: `rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_*` inside container. |
