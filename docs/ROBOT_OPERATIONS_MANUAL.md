# ROBOT OPERATIONS MANUAL
**Field Guide for System Bringup, Teleoperation, SLAM Mapping, Nav2 Navigation, Active Vision & Troubleshooting**
**Target Platform:** Yahboom Micro-ROS Pi 5 Mobile Robot | **Software:** ROS 2 Humble / Jazzy

---

## 1. Hardware Specifications, Power Sequence & Safety

### 1.1. System Hardware Layout
- **SBC:** Raspberry Pi 5 (8 GB RAM, 64-bit Quad-core Arm Cortex-A76 @ 2.4 GHz) with active cooler.
- **Microcontroller Baseboard:** Yahboom STM32/ESP32 motor driver board (running micro-ROS agent via USB serial on `/dev/ttyACM0`).
- **Range Sensor:** MS200 2D 360° LiDAR (USB serial, 12 Hz scan rate, 12m detection radius).
- **Vision Sensor:** USB HD RGB Camera mounted on 2-DOF Pan/Tilt Servo Gimbal.
- **Actuators:** 4x DC Geared Motors with Hall Effect wheel encoders.
- **Gimbal Servos:** 2x Digital Bus/PWM Servos (`S1`: Pan / Horizontal, `S2`: Tilt / Vertical).

```
                      [ MS200 LiDAR (Top Deck) ]
                                  │
      [ 2-DOF Camera Gimbal ] ───┼─── [ Raspberry Pi 5 SBC ]
                                  │
           [ Power Switch ] ─────┼───── [ STM32 Motor Baseboard ]
                                  │
                     [ 4x Encoder Drive Motors ]
```

### 1.2. Battery Safety & Voltage Cutoff
> [!CAUTION]
> **Battery Management Rules:**
> - The robot is powered by an 11.1V (3S Li-ion / 18650) high-drain rechargeable battery pack.
> - **Full Charge:** ~12.6V (4.2V per cell).
> - **Nominal Voltage:** 11.1V (3.7V per cell).
> - **Low Voltage Warning:** **10.2V** (Robot will emit continuous beeps on `/beep`).
> - **Emergency Cutoff Threshold:** **9.6V** (3.2V per cell). **Immediately switch off the robot and charge the battery.** Discharging below 9.0V causes irreversible cell degradation and fire hazard.

### 1.3. Power-On Sequencing
1. Place robot on a flat, unobstructed floor surface (wheels clear of wires).
2. Toggle the **Main Power Rocker Switch** on the rear battery casing to **ON**.
3. Verify that the Raspberry Pi 5 green power LED illuminates and the cooling fan spins.
4. Toggle the **Motor Power Switch** on the STM32 baseboard to **ON** (blue LEDs illuminate on the motor board).
5. Wait ~35 seconds for Debian Bookworm and the Docker containers to finish booting. When the system is ready, the onboard buzzer will emit a short double-beep.

---

## 2. Network Connectivity & Remote Access

### 2.1. Network Architecture
The robot connects to the local network via dual-band Wi-Fi (`wlan0`) or can operate as an autonomous Wi-Fi Hotspot if no external router is detected.
- **Default Robot Hostname:** `raspberrypi`
- **Known Live IPs:** `10.147.122.135` (or `10.147.122.136` / MAC: `2c:cf:67:94:29:68`)
- **Default SSH User:** `pi` | **Password:** `yahboom`

### 2.2. Establishing SSH Terminal Sessions
Open a terminal on your development workstation:
```bash
# Connect via SSH
ssh pi@10.147.122.135

# Verify host internet and container status
docker ps
```
You should see two active containers:
- `yahboom_base` (Chassis drivers, LiDAR, IMU, joystick)
- `yahboom_gesture` (ROS 2 Humble, ML perception, SLAM, Nav2)

### 2.3. Docker Container Interaction
```bash
# Enter the Base Chassis Container:
docker exec -it yahboom_base bash

# Enter the Cognition / Navigation Container:
docker exec -it yahboom_gesture bash

# Standard Environment Sourcing (Inside container):
source /opt/ros/humble/setup.bash
source /root/cognition_ws/install/setup.bash
export ROS_DOMAIN_ID=20
```

---

## 3. Operation Mode 1: Manual Teleoperation

### 3.1. Wireless Joypad (Default Mode)
The robot comes paired with a 2.4 GHz wireless USB joypad dongle plugged into the Pi 5. The joystick service runs automatically inside `yahboom_base` under supervisord.

```
       [ L1: Slow Mode ]                    [ R1: Turbo Mode ]
       [ L2: E-STOP Lock ]                  [ R2: Horn / Beep ]
             ┌───────┐                        ┌───────┐
             │   ▲   │                        │   Y   │ (Gimbal Up)
         ◄───┼───┼───┼───►                ◄───┼───┼───┼───►
             │   ▼   │                        │   A   │ (Gimbal Down)
             └───────┘                        └───────┘
          [ Left Joystick ]               [ Right Joystick ]
        Forward/Back/Rotate               Pan Left/Right Gimbal
```

- **Driving:** Push Left Stick forward/back for linear velocity ($v_x$), left/right for angular velocity ($\omega_z$).
- **Gimbal Pan/Tilt:** Push Right Stick to tilt and pan the 2-DOF camera manually.
- **Emergency Stop (L2):** Hold `L2` to lock velocity commands to zero.

### 3.2. Keyboard Teleoperation (Terminal Fallback)
If the wireless controller battery is dead, drive via keyboard over SSH:
```bash
docker exec -it yahboom_base bash -c "
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
"
```
*Keys: `i` = Forward, `,` = Reverse, `j` = Turn Left, `l` = Turn Right, `k` = Stop.*

---

## 4. Operation Mode 2: SLAM Room Mapping (Step-by-Step)

To navigate autonomously, the robot requires an occupancy grid map of the operating area. The workspace provides an automated script suite located directly in `/home/pi/`:

### Step 1: Pre-Flight Check
Ensure the robot is placed in the center of the room with at least 1.0 meter of clear space in front:
```bash
bash /home/pi/8_preflight_check.sh
```

### Step 2: Start the Mapping Session
```bash
bash /home/pi/1_start_mapping.sh
```
*What this does:*
1. Temporarily stops `cognition.service` to free CPU cycles.
2. Launches `slam_real.launch.py` inside `yahboom_gesture` (starts LiDAR restamper, ESP32 clock restamper, EKF with yaw enabled, and `slam_toolbox`).
3. Logs process IDs to `~/mapping_session_pids.txt`.

### Step 3: Drive and Map the Environment
Using the wireless joystick:
1. Drive the robot **slowly** ($<0.2\text{ m/s}$) around the perimeter of the room.
2. Make **gradual, smooth turns** at corners to allow EKF and scan-matching to register features without slipping.
3. Complete a full closed loop (return the robot to the exact starting spot).
4. Monitor mapping progress from another terminal:
   ```bash
   bash /home/pi/2_check_mapping_progress.sh
   ```

### Step 4: Save the Map and Stop SLAM
When the room is completely covered:
```bash
bash /home/pi/3_save_map_and_stop.sh
```
*What this does:*
- Saves the map as `/root/cognition_ws/maps_new/room_map_YYYYMMDD_HHMM.yaml` and `.pgm`.
- Gracefully terminates background SLAM processes using verified PID tracking.

### Step 5: Convert and Inspect Map
```bash
bash /home/pi/4_convert_map_for_viewing.sh
```
*Converts the saved `.pgm` file to `.png` so it can be viewed directly in a browser or image viewer.*

---

## 5. Operation Mode 3: Autonomous Nav2 Navigation

### Step 1: Wire Nav2 to the Latest Map
```bash
bash /home/pi/5_wire_nav2_to_new_map.sh
```
*Updates `nav2.launch.py` to automatically load the newest map generated in Step 4.*

### Step 2: Automated Safe Navigation Test (Recommended)
Use the automated, safety-gated test script:
```bash
bash /home/pi/9_run_navigation_test.sh
```
*What this does:*
1. Safely halts vision services to dedicate CPU to Nav2.
2. Launches the complete Nav2 stack and sensor chain.
3. Queries `/amcl_pose` and pauses for user confirmation: `Does that pose look sane? [y/N]`.
4. Sends a safe 1.0-meter waypoint and monitors feedback.
5. Cleans up all background processes and restores normal services upon completion.

### Step 3: Diagnostic-Only Run (If Troubleshooting Localization)
```bash
bash /home/pi/10_diagnose_amcl.sh
```
*Runs a 45-second read-only diagnostic verifying map ingestion, `/initialpose`, `/scan_downsampled`, and AMCL lifecycle `active [3]` state without moving the robot.*

### Step 2: Launch the Nav2 Stack
```bash
# On the Pi 5:
docker exec -it yahboom_gesture bash -c "
source /opt/ros/humble/setup.bash
source /root/cognition_ws/install/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch cognition_simulation nav2.launch.py
"
```

### Step 3: Provide Initial Pose Estimate (AMCL) & Physical Alignment
Before the robot can navigate, AMCL requires an initial guess of where the robot is located on the map:

> [!IMPORTANT]
> **Operational Requirements for Autonomous Navigation:**
> 1. **Physical Placement:** Always place the robot on the floor at the exact physical location and heading where the mapping session began (typically facing forward along $+X$). If placed elsewhere, AMCL particles will disperse and heading discrepancy will trap the controller in an in-place rotation loop.
> 2. **Align Before Goal:** Publish `/initialpose` matching the robot's real-world starting position:
```bash
# Terminal command to set initial pose at map origin:
docker exec yahboom_gesture bash -c "
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  '{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.07]}}'
"
```
> 3. **Check Clear Path:** Ensure a clear line of sight to the goal. In `room_map`, an obstacle wall sits at $x = +0.55\text{ m}$. For initial straight-line testing, use a waypoint at $x = 0.30\text{ m}$ to $0.40\text{ m}$ in clear space.

### Step 4: Dispatch Autonomous Navigation Goal
Command the robot to navigate to target coordinate $(x=1.5\text{m}, y=0.5\text{m})$:
```bash
docker exec yahboom_gesture bash -c "
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=20
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: map}, pose: {position: {x: 1.5, y: 0.5, z: 0.0}, orientation: {w: 1.0}}}}'
"
```
*The robot will dynamically compute an obstacle-free global path, spin to the heading, and autonomously drive to the target while avoiding dynamic obstacles.*

---

## 6. Operation Mode 4: Vision, Gestures & Active Gimbal Tracking

### 6.1. Live Bench Autonomy Demonstration Pipeline
To start the complete multi-modal bench demonstration (Camera + YOLOv8 + Active Gimbal + Face ID + Gestures + Brain + Live HUD Monitor):
```bash
# On the Raspberry Pi:
bash ~/start_bench_pipeline.sh
```

To launch the full pipeline via native ROS 2 launch file:
```bash
ros2 launch launch/cognition_autonomy.launch.py
```

### 6.2. Hardware Gimbal Servo Limit & Direction Diagnostic
To test and measure physical servo travel, direction, and mechanical limits at a safe, smooth $25^\circ/\text{s}$:
```bash
docker exec -it yahboom_gesture python3 /root/cognition_ws/probe_gimbal_limits.py
```

### 6.3. Position-Invariant Operator Gesture Controls
The robot employs an anatomical joint-vector geometric classifier, guaranteeing 100% reliable classification regardless of where the hand is in the camera frame:

| Gesture | Hand Pose | Commanded Action | Safety Behavior |
|---|---|---|---|
| **STOP** | Open Palm (all fingers extended) | Chassis Wheels Halted ($0.0\text{ m/s}$) | Instant preemption over all active motions |
| **GO** | Thumbs Up (thumb extended, fingers curled) | Translate Forward ($0.25\text{ m/s}$) | Drives straight forward |
| **FOLLOW** | Peace / V-Sign (index + middle extended) | Steer & Maintain Distance ($0.20\text{ m/s}$) | Halts forward drive if closer than $1.2\text{ m}$ |
| **LEFT** | Index Finger pointing left | Turn Left ($+0.40\text{ rad/s}$) | Pivots chassis counter-clockwise |
| **RIGHT** | Index Finger pointing right | Turn Right ($-0.40\text{ rad/s}$) | Pivots chassis clockwise |
| **BACK** | Closed Fist or Thumb Down | Translate Backward ($-0.15\text{ m/s}$) | Reverses chassis slowly |

### 6.4. Enrolling an Authorized Operator (Facial Recognition)
To enroll your face into the robot's biometric authorization database:
```bash
cd ~/cognition_ws/src/cognition_perception/cognition_perception
python3 face_id_lib.py --enroll "Operator_Name"
```
*Look directly at the camera for 3 seconds. The script extracts clean 512-d ArcFace embeddings and saves them to `authorized_faces.json`.*

### 6.5. Live Autonomy Dashboards & Telemetry Recording

#### A. Interactive Curses Terminal HUD Monitor
Monitor real-time vision bounding boxes, pan/tilt servo angles, gesture confidence, and velocity commands directly in your terminal:
```bash
python3 scripts/bench_autonomy_monitor.py
```

#### B. Full Web Operations Dashboard
Launch the unified ROS bridge and web video server to open the interactive operator dashboard:
```bash
bash scripts/launch_dashboard.sh
```
- Browser opens: `cognition_dashboard/web/index.html`
- Direct MJPEG stream: `http://<robot-ip>:8080/stream?topic=/camera/image_raw/compressed`

#### C. Lightweight Hardware Telemetry Recording (Rosbag2)
Record numerical topics without saturating the MicroSD card:
```bash
bash scripts/record_autonomy_bag.sh
```
*Captures `/cognition/gesture`, `/cmd_vel`, `/odom_raw`, `/scan`, and `/tf` into timestamped bag archives for verification analysis.*


---

## 7. Operation Mode 5: Gazebo Simulation (Dev Machine)

To test algorithms without the physical robot, run the optimized simulation on your development machine:

```bash
# Terminal 1: Launch Gazebo Headless Server
source /opt/ros/jazzy/setup.bash
source ~/yahboomcar_jazzy_ws/install/setup.bash
source ~/cognition_ws/install/setup.bash
export ROS_DOMAIN_ID=20
ros2 launch launch/pi5_sim_headless.launch.py

# Terminal 2: Launch Throttled RViz2 Visualizer
source /opt/ros/jazzy/setup.bash
source ~/cognition_ws/install/setup.bash
export ROS_DOMAIN_ID=20
rviz2 -d config/cognition.rviz --ros-args -p use_sim_time:=true
```

---

## 8. Quick-Reference Field Troubleshooting Checklist

| Symptom / Failure | Immediate Cause | Rapid Resolution Procedure |
|---|---|---|
| **Motors do not spin on teleop** | Motor switch on baseboard is OFF or battery $<9.8$V | 1. Toggle motor board power switch.<br>2. Check voltage on `/battery`: `ros2 topic echo /battery --once`. |
| **LiDAR topic `/scan` has 0 Hz** | USB device permissions or baud rate error | Run `ls -l /dev/rplidar` or restart `yahboom_base`: `docker restart yahboom_base`. |
| **AMCL `/amcl_pose` never publishes** | `use_sim_time` set to True on real bot | Open `launch/nav2.launch.py`; verify `'use_sim_time': False`. |
| **Map rotates 45° during turns** | EKF yaw disabled in `odom0_config` | In `slam_real.launch.py`, ensure yaw (index 5) is set to `True` in `odom0_config`. |
| **Camera video feed is black / frozen** | USB camera claimed by dead process | Restart container camera node: `docker exec yahboom_base pkill -9 -f camera_pub`. |
| **Emergency Stop Needed Immediately** | Uncontrolled motor motion | **Press the red Main Power Rocker Switch on the battery rear casing immediately.** |
