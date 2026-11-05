#!/bin/bash
# ==============================================================================
# launch_autonomy.sh — Embedded AMR Autonomy Launch Script
# Starts perception, active vision, decision brain, and visualizer inside Docker
# Supports unified human_pose_gesture_node (default) or legacy two-node pipeline
# ==============================================================================

CONTAINER=yahboom_gesture
USE_LEGACY=false

if [[ "${1:-}" == "--legacy" ]]; then
    USE_LEGACY=true
    echo ">> Launching in LEGACY mode (Separate YOLOv8n + MediaPipe Hands)..."
else
    echo ">> Launching with Unified human_pose_gesture_node.py (Low-Memory Profile)..."
fi

echo "Pausing factory joystick background loop to avoid /cmd_vel contention..."
docker exec yahboom_base supervisorctl stop ChassisServer 2>/dev/null || true
sleep 1

echo "Cleaning previous autonomy nodes..."
docker exec $CONTAINER bash -c "
    pkill -9 -f 'camera_pub|human_pose_gesture|person_detection_node|gesture_node|active_vision_node|decision_node|brain_node|web_map_visualizer' 2>/dev/null || true
    rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
"
sleep 1

echo "Starting camera_pub.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py > /tmp/camera_pub.log 2>&1
"
sleep 2

if [ "$USE_LEGACY" = true ]; then
    echo "Starting legacy person_detection_node.py..."
    docker exec -d $CONTAINER bash -c "
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export ROS_DOMAIN_ID=20
        export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
        source /opt/ros/humble/setup.bash
        source /root/cognition_ws/install/setup.bash 2>/dev/null || true
        python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/person_detection_node.py > /tmp/person_detection.log 2>&1
    "
    sleep 2

    echo "Starting legacy gesture_node.py..."
    docker exec -d $CONTAINER bash -c "
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export ROS_DOMAIN_ID=20
        export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
        source /opt/ros/humble/setup.bash
        source /root/cognition_ws/install/setup.bash 2>/dev/null || true
        python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/gesture_node.py > /tmp/gesture.log 2>&1
    "
    sleep 2
else
    echo "Starting unified human_pose_gesture_node.py..."
    docker exec -d $CONTAINER bash -c "
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export ROS_DOMAIN_ID=20
        export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
        source /opt/ros/humble/setup.bash
        source /root/cognition_ws/install/setup.bash 2>/dev/null || true
        python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/human_pose_gesture_node.py > /tmp/human_pose_gesture.log 2>&1
    "
    sleep 2
fi

echo "Starting active_vision_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py > /tmp/active_vision.log 2>&1
"
sleep 1

echo "Starting decision_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    if [ -f /root/cognition_ws/src/cognition_brain/cognition_brain/decision_node.py ]; then
        python3 -u /root/cognition_ws/src/cognition_brain/cognition_brain/decision_node.py --ros-args -p cmd_vel_topic:=/cmd_vel > /tmp/brain.log 2>&1
    else
        python3 -u /root/cognition_ws/src/cognition_brain/cognition_brain/brain_node.py --ros-args -p cmd_vel_topic:=/cmd_vel > /tmp/brain.log 2>&1
    fi
"
sleep 1

echo "Starting web_map_visualizer.py with live camera feed on port 8080..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    export FASTRTPS_DEFAULT_PROFILES_FILE=/root/cognition_ws/config/fastdds_lowmem.xml
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/web_map_visualizer.py > /tmp/visualizer.log 2>&1
"
sleep 1

echo ">> Checking running processes in $CONTAINER:"
docker exec $CONTAINER ps aux | grep -E 'camera_pub|human_pose_gesture|person_detection|active_vision|gesture_node|decision_node|brain_node|web_map_visualizer' | grep -v grep || true
echo ">> All autonomy nodes initiated successfully."
