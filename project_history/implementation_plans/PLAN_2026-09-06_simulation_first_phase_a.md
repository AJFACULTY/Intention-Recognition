# Phase A: Simulation-First Validation and Tuning (ROS 2 Jazzy / Gazebo Harmonic)

Executing Phase A of the navigation validation on the developer PC (`j-Lenovo-V15-ADA`).

## Objectives
1. Launch Gazebo Harmonic simulation and robot model (`pi5_sim.launch.py`).
2. Verify TF transform tree (`map` -> `odom_frame` -> `base_footprint` -> `base_link` -> `laser_frame`) and sensor pipeline (`/scan`, `/scan_fixed`).
3. Launch Nav2 stack with tuned `FollowPath` controller (`nav2.launch.py`).
4. Verify Nav2 lifecycle nodes transition to `active` and AMCL localized pose.
5. Send navigation goal (`/navigate_to_pose`) and verify robot drives smoothly to destination (`STATUS_SUCCEEDED`) without rotational stalling or jitter.

## Execution Steps
1. **Launch Simulation**:
   ```bash
   ros2 launch cognition_simulation pi5_sim.launch.py
   ```
2. **Verify Transforms & Topics**:
   - `ros2 topic hz /scan` & `ros2 topic hz /scan_fixed`
   - `ros2 run tf2_ros tf2_echo odom_frame base_footprint`
3. **Launch Nav2 Stack**:
   ```bash
   ros2 launch cognition_simulation nav2.launch.py
   ```
4. **Command Navigation Goal**:
   ```bash
   ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
     "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.8, y: 2.6, z: 0.0}, orientation: {w: 1.0}}}}"
   ```
5. **Verify Completion & Motion**:
   - Confirm status `STATUS_SUCCEEDED`.
   - Record `/cmd_vel` output during transit.
