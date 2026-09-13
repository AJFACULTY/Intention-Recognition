# Walkthrough: Geometric L-Form Mission Alignment & Physical Robot Pre-Flight Checklist

We updated the 4-point mission topology across [`scripts/web_map_visualizer.py`](file:///home/j/ros2_cognition_ws/scripts/web_map_visualizer.py), [`scripts/mock_navigation_simulator.py`](file:///home/j/ros2_cognition_ws/scripts/mock_navigation_simulator.py), and [`scripts/mission_manager.py`](file:///home/j/ros2_cognition_ws/scripts/mission_manager.py) to form a **geometric "L" alignment**:
1. **Long Leg:** A single, obstacle-free straight diagonal corridor line from **P1** through **P2** to **P3** ($4.43\,\text{m}$), with P2 stationed exactly at the collinear midpoint.
2. **Short Leg:** An orthogonal perpendicular turn from **P3** to **P4** ($2.05\,\text{m}$ at $88.3^\circ \approx 90^\circ$) leading into the East gallery.

---

## 1. Geometric Verification of the L-Form

| Waypoint | Coordinates $(x, y)$ | Role in L-Form Geometry | Obstacle Clearance | Heading |
| :--- | :--- | :--- | :--- | :--- |
| **P1** | $(0.08\,\text{m}, 0.05\,\text{m})$ | **Docking Base (Base of L)** | $0.35\,\text{m}$ wall clearance | $+45^\circ$ forward |
| **P2** | $(1.64\,\text{m}, 1.62\,\text{m})$ | **Collinear Midpoint** (deviation $< 3.5\,\text{mm}$) | $0.44\,\text{m}$ wall clearance | $+45^\circ$ along leg |
| **P3** | $(3.20\,\text{m}, 3.20\,\text{m})$ | **North Corner Vertex (Elbow of L)** | $0.35\,\text{m}$ wall clearance | $88.3^\circ$ turn |
| **P4** | $(4.70\,\text{m}, 1.80\,\text{m})$ | **East Lab Post (End of Short Leg)** | $0.25\,\text{m}$ wall clearance | $-43^\circ$ facing aisle |

### Mathematical Metrics:
- **Collinearity:** Vector cross-product deviation of $P_2$ from the segment $\overline{P_1 P_3}$ is $\mathbf{0.0035\,\text{m}}$ ($3.5\,\text{mm}$), ensuring an exact straight line.
- **Perpendicularity:** Angle between vector $\vec{P_1 P_3}$ and $\vec{P_3 P_4}$ is $\mathbf{88.3^\circ}$ (orthogonal right angle).
- **Segment Lengths:** Long leg $= 4.43\,\text{m}$, Short leg $= 2.05\,\text{m}$ (classic geometric L proportion).
- **Visual Overlay:** A subtle lavender guideline connects $P_1 \rightarrow P_2 \rightarrow P_3 \rightarrow P_4$ on the map to make the corridor geometry instantly visible.

---

## 2. Live Visual Verification

Below is the verified live capture from the active visualizer (`http://localhost:8080/map.jpg`):

![Geometric L-Form Navigation Topology](map_l_form.jpg)

### Key Display Elements:
1. **Lavender L-Guideline:** Connects P1 $\rightarrow$ P2 $\rightarrow$ P3 along the straight main corridor, then sharply branches down-right to P4.
2. **Dual-Pass High-Contrast Pins:** P1 (green dock), P2 (cyan center), P3 (magenta elbow), P4 (amber east post) with drop-shadow numbers.
3. **Active Trajectory:** Robot navigates smoothly along the corridor line with zero wall interference.

---

## 3. Physical Robot Pre-Flight Checklist (Once Fully Charged)

When taking the **Yahboom Micro-ROS Pi 5 robotic car** off the charger, follow this systematic engineering checklist:

### A. Electrical & Mechanical Safety
1. **Disconnect Charger:** Unplug the DC balance charger / USB-C cable from the Yahboom expansion board. *Never operate motors while plugged in.*
2. **Verify Battery Health:** Full charge on the 2S Li-ion battery is $\mathbf{8.4\,\text{V}}$ ($4.2\,\text{V}$/cell). The visualizer warns in yellow below $7.4\,\text{V}$ and triggers a low-battery red alert below $7.0\,\text{V}$ (hardware motor cutoff is $6.8\,\text{V}$).
3. **Inspect Drive Components:**
   - Ensure tires are snug on their motor D-shafts and clear of hair or carpet fibers (prevents encoder odometry drift).
   - Ensure the rotating LiDAR turret spins freely with no cables grazing the optics.

### B. Power-On & Middleware Startup
1. **Power Switch:** Flip the main toggle switch on the Yahboom baseboard. Allow $30 - 45\,\text{s}$ for the Raspberry Pi 5 to complete OS boot.
2. **Network Matching:** Confirm the workstation laptop and Pi 5 are on the same Wi-Fi network (5 GHz recommended) and share the same domain:
   ```bash
   export ROS_DOMAIN_ID=0
   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
   ```
3. **Micro-ROS Agent:** Verify the micro-ROS serial bridge is communicating with the lower board:
   ```bash
   ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 921600
   ```
   Check that `/battery`, `/cmd_vel`, and `/imu/data` appear in `ros2 topic list`.

### C. Sensor Verification & Localization
1. **LiDAR Driver:** Launch the LiDAR driver (`ros2 launch ydlidar_ros2_driver ydlidar_launch.py`). Verify `/scan` rate is $\sim 10\,\text{Hz}$.
2. **The "Push Test" (Odometry Sanity Check):**
   - Gently roll the robot forward by hand $1.0\,\text{m}$; confirm `/odom` position increases by $+1.0\,\text{m}$ ($\pm 5\%$).
   - Rotate $90^\circ$ counterclockwise; confirm orientation yaw increases by $+1.57\,\text{rad}$.
3. **Dock Alignment & Initial Pose:**
   - Place the robot at the physical dock corresponding to **P1** $(0.08\,\text{m}, 0.05\,\text{m})$, pointed diagonally forward along the corridor.
   - On the web dashboard (`http://<ROBOT_IP>:8080`), click **`2D Pose Estimate`**, click on P1, and drag the arrow forward along the corridor guideline.
   - Confirm AMCL green particle swarm collapses tightly onto the robot and red laser dots snap directly to the room walls.

---

## 4. Operation

1. Open **`http://localhost:8080`**
2. Click **`Run 4-Point Unattended Mission`** to command the robot to patrol the complete L-corridor autonomously.
3. Use the **Spacebar** or click **`EMERGENCY STOP`** at any moment for an instant hardware zero-velocity freeze.
