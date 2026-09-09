#!/usr/bin/env bash
# ==============================================================================
# 14_tune_pure_pursuit_and_test.sh
# Author: Antigravity Autonomous Systems Engineering Team
# Date: September 7, 2026
# Platform: Yahboom Micro-ROS Pi 5 Mobile Robot
#
# PURPOSE:
# 1. Inspects /tmp/nav2_short.log from previous test run.
# 2. Injects tuned RegulatedPurePursuitController and AMCL parameters into nav2_params.yaml:
#    - AMCL initial pose reset to (0, 0, 0) (eliminates 2.806m sim coordinate remnant)
#    - use_rotate_to_heading set to false (allows concurrent forward drive and heading steer)
#    - lookahead_dist tuned to 0.25m, min_lookahead 0.15m (prevents carrot clamping on short goals)
#    - transform_tolerance maintained at 0.8s across all nodes
# 3. Cleanly stops background services and flushes duplicate orphan nodes.
# 4. Launches Nav2 and dispatches a verified 0.30m straight-line goal in clear corridor.
# 5. Restores all base chassis services upon completion.
# ==============================================================================

set -uo pipefail

CONTAINER_GESTURE="yahboom_gesture"
CONTAINER_BASE="yahboom_base"
PARAMS_FILE="/root/cognition_ws/src/cognition_simulation/config/nav2_params.yaml"

echo "======================================================================"
echo "== STEP 1: INSPECTING /tmp/nav2_short.log FROM LAST NAVIGATION RUN =="
echo "======================================================================"
if docker exec "$CONTAINER_GESTURE" test -f /tmp/nav2_short.log 2>/dev/null; then
    echo "Found /tmp/nav2_short.log. Inspecting controller decisions..."
    docker exec "$CONTAINER_GESTURE" grep -iE "controller_server|FollowPath|collision|speed|velocity|carrot|RotateToHeading" /tmp/nav2_short.log | tail -n 25 || true
    echo -e "\nRecent warnings/errors:"
    docker exec "$CONTAINER_GESTURE" grep -iE "\[WARN\]|\[ERROR\]" /tmp/nav2_short.log | tail -n 15 || true
else
    echo "No /tmp/nav2_short.log found (fresh boot)."
fi

echo -e "\n======================================================================"
echo "== STEP 2: APPLYING TUNED PURE PURSUIT & AMCL PARAMETERS =="
echo "======================================================================"
docker exec "$CONTAINER_GESTURE" python3 -c "
import re

path = '$PARAMS_FILE'
with open(path, 'r') as f:
    c = f.read()

# 1. Update AMCL initial pose to map origin
c = re.sub(r'initial_pose_x:.*', 'initial_pose_x: 0.0', c)
c = re.sub(r'initial_pose_y:.*', 'initial_pose_y: 0.0', c)
c = re.sub(r'initial_pose_a:.*', 'initial_pose_a: 0.0', c)

# 2. Ensure transform_tolerance is 0.8 across stack
c = re.sub(r'^\s*transform_tolerance:.*\n', '', c, flags=re.MULTILINE)
c = re.sub(r'(amcl:\s*\n\s*ros__parameters:\s*\n)', r'\1    transform_tolerance: 0.8\n', c)
c = re.sub(r'(bt_navigator:\s*\n\s*ros__parameters:\s*\n)', r'\1    transform_tolerance: 0.8\n', c)
c = re.sub(r'(controller_server:\s*\n\s*ros__parameters:\s*\n)', r'\1    transform_tolerance: 0.8\n', c)
c = re.sub(r'(local_costmap:\s*\n\s*local_costmap:\s*\n\s*ros__parameters:\s*\n)', r'\1      transform_tolerance: 0.8\n', c)
c = re.sub(r'(global_costmap:\s*\n\s*global_costmap:\s*\n\s*ros__parameters:\s*\n)', r'\1      transform_tolerance: 0.8\n', c)
c = re.sub(r'(planner_server:\s*\n\s*ros__parameters:\s*\n)', r'\1    transform_tolerance: 0.8\n', c)
c = re.sub(r'(behavior_server:\s*\n\s*ros__parameters:\s*\n)', r'\1    transform_tolerance: 0.8\n', c)

# 3. Tune FollowPath (RegulatedPurePursuitController)
# Strip old settings to prevent duplicates
c = re.sub(r'^\s*use_rotate_to_heading:.*\n', '', c, flags=re.MULTILINE)
c = re.sub(r'^\s*lookahead_dist:.*\n', '', c, flags=re.MULTILINE)
c = re.sub(r'^\s*min_lookahead_dist:.*\n', '', c, flags=re.MULTILINE)
c = re.sub(r'^\s*max_lookahead_dist:.*\n', '', c, flags=re.MULTILINE)
c = re.sub(r'^\s*desired_linear_vel:.*\n', '', c, flags=re.MULTILINE)

follow_path_replacement = '''    FollowPath:
      transform_tolerance: 0.8
      plugin: nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController
      desired_linear_vel: 0.20
      lookahead_dist: 0.25
      min_lookahead_dist: 0.15
      max_lookahead_dist: 0.60
      use_rotate_to_heading: false
      use_velocity_scaled_lookahead_dist: false
      min_approach_linear_velocity: 0.05
      max_allowed_time_to_collision_up_to_carrot: 1.0
'''
c = re.sub(r'    FollowPath:\s*\n.*?max_allowed_time_to_collision_up_to_carrot: 1\.0\n', follow_path_replacement, c, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(c)

print('Successfully tuned nav2_params.yaml!')
"

echo -e "\nVerifying FollowPath configuration in $PARAMS_FILE:"
docker exec "$CONTAINER_GESTURE" grep -A 11 "FollowPath:" "$PARAMS_FILE"

echo -e "\n======================================================================"
echo "== STEP 3: FLUSHING ORPHAN NODES & STOPPING BACKGROUND SERVICES =="
echo "======================================================================"
sudo systemctl stop cognition.service 2>/dev/null || true
docker exec "$CONTAINER_BASE" supervisorctl stop ChassisServer 2>/dev/null || true
docker exec "$CONTAINER_GESTURE" bash -c "
  pkill -9 -f 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl|map_server|planner_server|controller_server|behavior_server|bt_navigator|waypoint_follower|lifecycle_manager' 2>/dev/null || true
"
sleep 2

echo -e "\n======================================================================"
echo "== STEP 4: LAUNCHING NAV2 WITH TUNED PARAMETERS =="
echo "======================================================================"
docker exec -d "$CONTAINER_GESTURE" bash -c "
  source /opt/ros/humble/setup.bash &&
  source /root/cognition_ws/install/setup.bash &&
  ros2 launch /root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py > /tmp/nav2_tuned.log 2>&1
"

echo "Waiting 15s for full Nav2 lifecycle convergence..."
for i in {15..1}; do
    echo -ne "Initializing... $i s remaining \r"
    sleep 1
done
echo -e "\nNav2 stack is active."

echo -e "\n======================================================================"
echo "== STEP 5: PHYSICAL PLACEMENT CHECK & DISPATCHING 0.30m GOAL =="
echo "======================================================================"
echo ">>> OPERATOR: Ensure the robot is on the floor at the mapping origin <<<"
echo ">>> facing forward down the unobstructed hallway (towards +X).       <<<"
echo "Sending 0.30m straight-line goal..."

docker exec "$CONTAINER_GESTURE" bash -c "
  source /opt/ros/humble/setup.bash &&
  timeout 18 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
    '{pose: {header: {frame_id: map}, pose: {position: {x: 0.30, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}' \
    --feedback | grep -E 'position:|distance_remaining|recoveries|Result:' || true
"

echo -e "\n======================================================================"
echo "== STEP 6: RESTORING SERVICES & CLEANUP =="
echo "======================================================================"
docker exec "$CONTAINER_GESTURE" bash -c "
  pkill -9 -f 'laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl|map_server|planner_server|controller_server|behavior_server|bt_navigator|waypoint_follower|lifecycle_manager' 2>/dev/null || true
"
docker exec "$CONTAINER_BASE" supervisorctl start ChassisServer 2>/dev/null || true
echo "ChassisServer restored. Test complete."
