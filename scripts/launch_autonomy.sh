#!/bin/bash

CONTAINER=yahboom_gesture

echo "Pausing factory joystick background loop to avoid /cmd_vel contention..."
docker exec yahboom_base supervisorctl stop ChassisServer 2>/dev/null || true
sleep 1

echo "Cleaning previous autonomy nodes..."
docker exec $CONTAINER bash -c "
    pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|brain_node|web_map_visualizer' 2>/dev/null || true
    rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
"
sleep 1

echo "Starting camera_pub.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py > /tmp/camera_pub.log 2>&1
"
sleep 2

echo "Starting person_detection_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/person_detection_node.py > /tmp/person_detection.log 2>&1
"
sleep 2

echo "Starting active_vision_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py > /tmp/active_vision.log 2>&1
"
sleep 1

echo "Starting gesture_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/gesture_node.py > /tmp/gesture.log 2>&1
"
sleep 2

echo "Starting brain_node.py..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/src/cognition_brain/cognition_brain/brain_node.py --ros-args -p cmd_vel_topic:=/cmd_vel > /tmp/brain.log 2>&1
"
sleep 1

echo "Starting web_map_visualizer.py with live camera feed on port 8080..."
docker exec -d $CONTAINER bash -c "
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=20
    source /opt/ros/humble/setup.bash
    source /root/cognition_ws/install/setup.bash 2>/dev/null || true
    python3 -u /root/cognition_ws/web_map_visualizer.py > /tmp/visualizer.log 2>&1
"
sleep 1

echo ">> Checking running processes in $CONTAINER:"
docker exec $CONTAINER ps aux | grep -E 'camera_pub|person_detection|active_vision|gesture_node|brain_node|web_map_visualizer' | grep -v grep || true
echo ">> All autonomy nodes initiated successfully."
