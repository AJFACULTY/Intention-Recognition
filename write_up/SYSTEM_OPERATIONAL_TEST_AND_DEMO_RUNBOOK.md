# Autonomous Mobile Robot Cognition System
## Live Defense Demonstration & Full System Operational Runbook

**Mission Title:** Capstone Operational Demonstration — Multi-Waypoint Patrol $\to$ Human Approach $\to$ LSTM Motion Prediction $\to$ LiDAR Corridor Halt $\to$ Dynamic Gesture Interaction  
**Platform:** Yahboom 4WD Micro-ROS Mobile Robot (Raspberry Pi 5 8GB SBC, ESP32-S3 Baseboard, MS200 LiDAR, 2-DOF Camera Gimbal)  
**Authors:** Eleana Osei Owusu (4121230024) & Joel Nii Adjetey Ahulu (4121230020)  
**Supervisor:** Mr. Micheal Xenya  
**Institution:** Ghana Communication Technology University (GCTU), Faculty of Engineering  

---

## 1. Executive Demonstration Scenario & Narrative

When presenting the live hardware demonstration to the defense examination panel, this is the exact **4-Stage Narrative Arc** to execute:

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                LIVE DEMONSTRATION TIMELINE                                │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                           │
│   STAGE 1: Mapped Autonomous Waypoint Patrol                                              │
│   • Robot starts at Home Base (0.08m, 0.05m).                                            │
│   • Mission Manager dispatches Nav2 goal to Waypoint P2 (Central Hub).                     │
│   • Robot navigates smoothly down the corridor, avoiding static wall boundaries.          │
│                                                                                           │
│   STAGE 2: Human Approaches & Trajectory Prediction                                       │
│   • An operator walks toward the patrolling robot down the corridor.                      │
│   • Camera captures human silhouette; YOLOv8n extracts bounding box.                     │
│   • LSTM path predictor ingests 10-frame sliding window of centroid coordinates.          │
│   • Live Web Visualizer (port :8080) renders trajectory arrow & status: "APPROACHING".    │
│                                                                                           │
│   STAGE 3: Corridor Blockage & ISO 15066 LiDAR Reactive Halt                             │
│   • The operator intentionally steps directly into the robot's travel path (<0.36m).      │
│   • MS200 LiDAR frontal safety corridor triggers instant emergency stop.                  │
│   • Brain node preempts Nav2 on twist_mux (priority 40 > 20); cmd_vel zeroes immediately. │
│   • Safety audio node plays acoustic chime; robot stops dead without physical contact.    │
│                                                                                           │
│   STAGE 4: Touchless Hand Gesture Preemption & Resumption                                 │
│   • While the robot is halted, the operator raises a clear gesture to the camera:         │
│       - Option A: "GO" (Thumbs Up) -> Robot clears the halt and resumes patrol.           │
│       - Option B: "FOLLOW" (Peace Sign) -> Robot switches to person tracking mode.       │
│       - Option C: "STOP" (Open Palm) -> Robot permanently cancels the patrol mission.     │
│   • Rolling 5-frame consensus confirms gesture (1.2 ms inference); robot reacts.          │
│                                                                                           │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. "No Bluff" Readiness Punch List: What is Left to Do While Charging?

To execute this demonstration with **zero failure**, here is the unvarnished engineering checklist:

| # | Subsystem / Task | Current Status | Action Required While Bot is Charging | Exact Command / Test |
| :-: | :--- | :---: | :--- | :--- |
| **1** | **Battery Pack (2S Li-Ion)** | **CHARGING** | **DO NOT DISCONNECT EARLY.** Must reach **$\ge 8.0\,\text{V}$** (ideal: $8.3\,\text{V} \to 8.4\,\text{V}$). At $<7.2\,\text{V}$, baseboard H-bridges brown out during sudden motor torque reversals. | Check charger LED (Green = Full) or verify on startup. |
| **2** | **Code & Models Sync** | **READY** | All latest nodes, models, and `hand_landmarker.task` are staged. As soon as the Pi boots on Wi-Fi, run the synchronization script from your laptop. | `./scripts/sync_to_bot.sh 10.27.122.136` |
| **3** | **Hardware Cabling** | **PHYSICAL** | Inspect mechatronic interconnects before putting the robot on the floor: <br>• USB Camera cable securely plugged into Pi 5 USB 3.0 port.<br>• USB-C data cable between Pi 5 and Yahboom baseboard firmly seated.<br>• MS200 LiDAR spinning freely without cable snags. | Hand check cable tension and motor wheel nuts. |
| **4** | **Initial Robot Pose** | **SPATIAL** | Place the robot at the physical origin marked on your floor corresponding to **Home Base** $(x=0.08\,\text{m}, y=0.05\,\text{m}, \theta=0^\circ)$ facing along the positive X-axis. | Align wheels with marked floor tape. |
| **5** | **Lighting Environment** | **OPTICAL** | Ensure the demonstration corridor has uniform overhead ambient lighting. Avoid standing directly in front of a blinding window (backlighting silhouetting hand landmarks). | Turn on room fluorescent lights; avoid direct backlights. |

---

## 3. Step-by-Step Live Execution Procedure (Turnkey Method)

Once the battery reaches $\ge 8.0\,\text{V}$ and the robot is powered on:

### Step 1: Verify Network Connectivity from Development Laptop
Open a terminal on your host workstation:
```bash
cd /home/j/ros2_cognition_ws
ping -c 2 10.27.122.136
```
*(If the robot was assigned a different IP, check your router or hotspot: e.g., `10.27.122.135`).*

### Step 2: Push Latest Source Code & Models
Execute the updated deployment script:
```bash
./scripts/sync_to_bot.sh
```
*Wait for output:* `>> All autonomy, mission, waypoint, and model files successfully injected into Docker container.`

### Step 3: Run Pre-Flight Health Audit (Terminal 1)
SSH into the robot:
```bash
ssh pi@10.27.122.136
python3 ~/cognition_ws/master_demo_menu.py --audit-only
```
**Verify:**
- Docker Container `yahboom_gesture`: `RUNNING`
- USB Camera `/dev/video*`: `DETECTED`
- STM32/ESP32 Baseboard `/dev/ttyUSB0`: `CONNECTED`
- Battery Voltage: `NOMINAL (>= 8.0V)`
- Core AI Models: `VERIFIED`

---

### Step 4: Launch the Live Autonomous Patrol & Cognition Stack

You can launch this using the **Interactive Master Menu** or directly via dedicated terminal commands:

#### Option A: Via Master Menu (Recommended for Defense)
On the robot SSH session:
```bash
python3 ~/cognition_ws/master_demo_menu.py
```
1. Select **`[4]` — Collaborative Escort & Nav2 Patrol (Mode 2)**.
2. Select Mission: `UNATTENDED_FACILITY_PATROL` (or `CENTRAL_INSPECTION` for a shorter runway).
3. The robot initializes AMCL localization, sounds an initial chime, and begins driving toward Waypoint P2.

#### Option B: Direct Shell Commands (For Split-Screen Terminal Projection)
**Terminal 1 (Base Navigation & SLAM Map Localization):**
```bash
ssh pi@10.27.122.136
bash ~/start_nav2.sh
```
*(Wait 10 seconds until Nav2 lifecycle nodes report `active`).*

**Terminal 2 (Cognition, Vision & LSTM Trajectory Predictor):**
```bash
ssh pi@10.27.122.136
bash ~/start_bench_pipeline.sh --record
```

**Terminal 3 (Dispatch Autonomous Waypoint Patrol):**
```bash
ssh pi@10.27.122.136
python3 ~/cognition_ws/mission_manager.py --mission CENTRAL_INSPECTION
```

**Host Workstation Browser (Project on Classroom Screen / Projector):**
Open Google Chrome on your laptop:
```
http://10.27.122.136:8080
```
This displays:
- Live front camera video stream with YOLOv8 bounding boxes and 21 MediaPipe hand landmarks.
- Active human motion classification (`APPROACHING`, `STATIONARY`, `MOVING_LEFT`).
- Real-time 2D occupancy grid map with live AMCL robot pose $(x, y, \theta)$ and planned global trajectory.

---

## 4. Executing the Physical Human-Robot Interaction (The "Showstopper")

While the robot is driving autonomously toward Waypoint P2:

1. **The Human Approach:**
   - Stand approximately $2.5\,\text{m}$ down the corridor in the robot's field of view.
   - Begin walking toward the robot at a normal pace (~$0.8\,\text{m/s}$).
   - **What happens:** The Web HUD highlights your bounding box in green, and the status bar displays: `Behavior: APPROACHING | Conf: 0.92`.
2. **The Path Blockage & Safety Halt:**
   - Stop walking and stand directly in the center of the corridor, about $0.30\,\text{m} \to 0.35\,\text{m}$ in front of the robot.
   - **What happens:** 
     - The MS200 LiDAR detects obstacles inside the $0.36\,\text{m} \times 0.36\,\text{m}$ frontal corridor.
     - `brain_node` publishes zero velocity on `/cmd_vel_gesture`.
     - `twist_mux` suppresses Nav2's `/cmd_vel_nav` (priority 40 overrides priority 20).
     - The chassis halts smoothly without jerking or bumping your feet.
     - An acoustic alert tone sounds from the robot.
3. **The Touchless Hand Gesture:**
   - Stand in front of the camera and raise your hand clearly:
     - **Show `GO` (Thumbs Up):** Hold for 1.5 seconds. The robot registers 5 consecutive `GO` frames, clears the halt, and resumes autonomous transit to complete the patrol route.
     - **Show `FOLLOW` (Peace Sign):** The robot switches from Nav2 patrol to visual servoing, pivoting its chassis to shadow your movement as you guide it to another location.
     - **Show `STOP` (Open Palm):** The robot locks into emergency halt, disengaging motors and terminating the mission.

---

## 5. Live Demonstration Troubleshooting & Triage Matrix

| Symptom During Live Demo | Immediate Root Cause | 5-Second Rapid Fix |
| :--- | :--- | :--- |
| **Robot doesn't move when mission is dispatched.** | Nav2 lifecycle nodes or `/navigate_to_pose` action server not fully active. | In terminal: check `ros2 node list \| grep nav2`. If missing, re-run `bash ~/start_nav2.sh`. |
| **AMCL robot position jumps wildly on the map.** | Initial robot pose not aligned with the true floor coordinates, causing particle filter ambiguity. | In Master Menu, select `[6]` to reset pose to Home Base, or manually rotate the robot in place $360^\circ$ to let LiDAR scan-matching converge. |
| **Hand gesture not detected (camera ignores hand).** | Hand is held too close to the lens ($<0.4\,\text{m}$) or backlit by strong window glare. | Step back to **$1.0\,\text{m} \to 1.5\,\text{m}$** from the lens. Ensure the hand is held in the center of the frame with fingers clearly spread. |
| **Robot stops prematurely before the human blocks it.** | LiDAR detection threshold triggered by loose floor clutter, cables, or chair legs. | Ensure the test corridor is clear of floor cables within a $0.5\,\text{m}$ corridor width. |
| **Motors suddenly lose power or Pi reboots during turn.** | Battery voltage dropped below brownout threshold ($<7.2\,\text{V}$). | Immediately attach charger. Run bench demonstration on test stand while charging. |
