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
    pkill -9 -f 'twist_mux|safety_audio_node|web_map_visualizer|laser_tf|scan_republisher|odom_imu_republisher|ekf_node|nav2_|amcl|map_server|planner_server|controller_server|behavior_server|bt_navigator|waypoint_follower|lifecycle_manager' 2>/dev/null || true
"
sleep 2

echo "[2/3] Launching nav2.launch.py, Web Visualizer, Safety Audio Node, and Twist Mux..."
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash
    ros2 launch /root/cognition_ws/src/cognition_simulation/launch/nav2.launch.py > /tmp/nav2_run.log 2>&1
"

# Launch ROS 2 twist_mux priority velocity arbiter (Joystick=100, Nav2=50, Gesture=40, E-Stop=255)
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash
    ros2 run twist_mux twist_mux --ros-args --params-file /root/cognition_ws/twist_mux.yaml -r cmd_vel_out:=/cmd_vel > /tmp/twist_mux.log 2>&1
"

# Launch lightweight crash-free web visualizer
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash
    python3 /root/cognition_ws/web_map_visualizer.py > /tmp/web_vis.log 2>&1
"

# Launch industrial acoustic safety audio node (/beep)
docker exec -d "$CONTAINER" bash -c "
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    python3 /root/cognition_ws/safety_audio_node.py > /tmp/safety_audio.log 2>&1
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
msg.pose.pose.position.x = 0.08
msg.pose.pose.position.y = 0.05
msg.pose.pose.orientation.z = 0.3826834
msg.pose.pose.orientation.w = 0.9238795
msg.pose.covariance[0] = 0.25
msg.pose.covariance[7] = 0.25
msg.pose.covariance[35] = 0.15

for _ in range(5):
    pub.publish(msg)
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.05)
    time.sleep(0.1)

print(">> Initial pose broadcast to /initialpose at Home Base (0.08, 0.05).")
node.destroy_node()
rclpy.shutdown()
PYEOF
'

# 3. Assert camera gimbal eye level
echo "[Extra] Aligning 2-DOF camera gimbal to level horizon (+30°)..."
docker exec "$CONTAINER" bash -c '
    export ROS_DOMAIN_ID=20
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    source /opt/ros/humble/setup.bash
    python3 -c "
import time, rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
rclpy.init()
n = Node(\"gimbal_aligner\")
p1 = n.create_publisher(Int32, \"/servo_s1\", 10)
p2 = n.create_publisher(Int32, \"/servo_s2\", 10)
time.sleep(0.2)
m1 = Int32(); m1.data = 0
m2 = Int32(); m2.data = 30
for _ in range(5):
    p1.publish(m1); p2.publish(m2)
    rclpy.spin_once(n, timeout_sec=0.05); time.sleep(0.05)
n.destroy_node(); rclpy.shutdown()
" >/dev/null 2>&1 || true
'

ROBOT_IP=$(hostname -I | awk '{print $1}')
echo "=================================================================="
echo "  NAV2 STACK & WEB MONITOR ARE READY!"
echo "  Open live map in your browser: http://${ROBOT_IP}:8080"
echo "  Then run your mission in terminal:"
echo "      bash ~/run_mission.sh"
echo "=================================================================="
