# Implementation Plan: Simulation-First Validation and Tuning (ROS 2 Jazzy / Gazebo Harmonic)

Validate autonomous navigation in Gazebo simulation on the dev machine while the physical robot is powered off and charging. Specifically, eliminate controller rotation stall, verify TF and laser scan pipeline, test full path navigation, and prepare configurations to deploy to the physical robot once charged.

## User Review Required

> [!IMPORTANT]
> The physical robot is currently charging and powered off. All actions in this phase run strictly on the local developer machine (`j-Lenovo-V15-ADA`, Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Sim 8.11.0).

> [!NOTE]
> ROS 2 Distro conventions:
> - **Dev Machine (Simulation)**: ROS 2 Jazzy. Uses C++ namespace `::` plugin definitions (`nav2_navfn_planner::NavfnPlanner`, `nav2_behaviors::Spin`, etc.) and `use_sim_time: true`.
> - **Physical Robot (Pi 5)**: ROS 2 Humble in Docker. Uses slash format `/` for planner/behavior plugins (`nav2_navfn_planner/NavfnPlanner`, `nav2_behaviors/Spin`, etc.) and `use_sim_time: false`.

---

## Proposed Plan of Action

### 1. Tune `FollowPath` Controller in Simulation
In `/home/j/cognition_ws/src/cognition_simulation/config/nav2_params.yaml`:
- Configure `FollowPath` (`RegulatedPurePursuitController`):
  - Set `use_rotate_to_heading: false` to allow the robot to steer along an arc toward path goals without locking `linear.x = 0.0`.
  - Set `rotate_to_heading_min_angular_vel: 0.4` and `rotate_to_heading_angular_vel: 0.8` (or max_angular_vel: 1.0, min_angular_vel: 0.1) to ensure in-place rotations have sufficient velocity.
  - Re-install/build the config (`colcon build --packages-select cognition_simulation`).

### 2. Verify and Align Simulation TF / Scan Pipeline
- Inspect frame IDs published by `ros_gz_bridge` on `/scan` and `scan_republisher` on `/scan_fixed`.
- Verify the full TF tree: `map` -> `odom_frame` -> `base_footprint` -> `base_link` -> `radar_Link` -> `laser_frame`.
- Correct any dangling static transform in `pi5_sim.launch.py` so RViz and costmaps receive laser scans with 0 discarded messages.

### 3. Launch Simulation & Nav2 Stack
- Launch Gazebo simulation:
  ```bash
  ros2 launch cognition_simulation pi5_sim.launch.py
  ```
- Launch Nav2 stack:
  ```bash
  ros2 launch cognition_simulation nav2.launch.py
  ```
- Verify all 7 Nav2 lifecycle nodes transition to `active`.
- Verify AMCL particle cloud initializes at `(2.806, 2.624, 0.0)` matching the Gazebo spawn pose `(-2.8, -2.6)`.

### 4. Send Navigation Goal & Validate Motion
- Send an action goal via `ros2 action send_goal /navigate_to_pose`:
  - Verify `/cmd_vel` outputs `linear.x > 0` and smooth curvature steering.
  - Verify the simulated robot drives smoothly to the goal.
  - Verify `navigation_time` and `distance_remaining` decrease monotonically until `succeeded`.

### 5. Package Validated Fix for Physical Robot
- Format the exact parameter update for the Pi's `/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml`.
- Update `9_run_navigation_test.sh` on the Pi workspace with aggressive process cleanup (`pkill -9 -f 'nav2_'`) so testing runs cleanly once the robot is turned back on.

---

## Verification Plan

### Automated / Command Verification
1. **Colcon Build**:
   ```bash
   bash -c "source /opt/ros/jazzy/setup.bash && cd /home/j/cognition_ws && colcon build --packages-select cognition_simulation"
   ```
2. **TF Tree Verification**:
   ```bash
   ros2 run tf2_ros tf2_echo map base_footprint
   ros2 run tf2_ros tf2_echo base_footprint laser_frame
   ```
3. **Scan Topic Check**:
   ```bash
   ros2 topic hz /scan
   ros2 topic hz /scan_fixed
   ```
4. **Nav2 Goal Execution**:
   ```bash
   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
     "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.8, y: 2.6, z: 0.0}, orientation: {w: 1.0}}}}"
   ```
   Confirm goal completion with status `STATUS_SUCCEEDED`.
