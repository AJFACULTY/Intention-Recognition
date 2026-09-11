#!/bin/bash
# ==============================================================================
# start_nav2.sh — Clean Nav2 Autonomous Bringup on Physical Robot
# Author: Antigravity Autonomous Systems Engineering Team
# ==============================================================================

set -uo pipefail

CONTAINER="yahboom_gesture"

echo "=================================================================="
echo "    STARTING NAV2 AUTONOMOUS NAVIGATION STACK"
echo "=================================================================="

# 1. Always flush old navigation processes to ensure clean costmaps and uncorrupted particle filters
echo "[1/3] Flushing old navigation processes..."
docker exec "$CONTAINER" bash -c "
    pkill -9 -f 'web_map_visualizer|laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl|map_server|planner_server|controller_server|behavior_server|bt_navigator|waypoint_follower|lifecycle_manager' 2>/dev/null || true
"
sleep 2

echo "[2/3] Launching nav2.launch.py and Web Visualizer in background..."
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash
    ros2 launch /root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py > /tmp/nav2_run.log 2>&1
"

# Launch lightweight crash-free web visualizer
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash
    python3 /root/cognition_ws/web_map_visualizer.py > /tmp/web_vis.log 2>&1
"

echo "Waiting 18s for full lifecycle initialization..."
for i in $(seq 18 -1 1); do
    printf "\r  Initialization: %2d s remaining..." "$i"
    sleep 1
done
echo ""

# 2. Publish initial pose to align AMCL
echo "[3/3] Aligning AMCL localization to map origin..."
docker exec "$CONTAINER" bash -c '
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    python3 - << "PYEOF"
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
import time

rclpy.init()
node = Node("initial_pose_pub")
pub = node.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)
time.sleep(1.0)

msg = PoseWithCovarianceStamped()
msg.header.frame_id = "map"
msg.header.stamp = node.get_clock().now().to_msg()
msg.pose.pose.position.x = 0.0
msg.pose.pose.position.y = 0.0
msg.pose.pose.orientation.w = 1.0
msg.pose.covariance[0] = 0.25
msg.pose.covariance[7] = 0.25
msg.pose.covariance[35] = 0.15

pub.publish(msg)
print(">> Initial pose broadcast to /initialpose at origin (0, 0).")
node.destroy_node()
rclpy.shutdown()
PYEOF
'

echo "Waiting 5s for scan matching convergence..."
sleep 5

ROBOT_IP=$(hostname -I | awk '{print $1}')
echo "=================================================================="
echo "  NAV2 STACK & WEB MONITOR ARE READY!"
echo "  Open live map in your browser: http://${ROBOT_IP}:8080"
echo "  Then run your mission in terminal:"
echo "      bash ~/run_mission.sh"
echo "=================================================================="
