#!/bin/bash

# Cleanup handler on Ctrl+C (SIGINT) or SIGTERM
cleanup() {
    echo ""
    echo "================================================================"
    echo "  Shutting down demo pipeline & halting chassis..."
    echo "================================================================"
    docker exec yahboom_gesture bash -c "
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export ROS_DOMAIN_ID=20
        . /opt/ros/humble/setup.bash >/dev/null 2>&1
        timeout 1s ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null 2>&1 || true
        timeout 1s ros2 topic pub --once /servo_s1 std_msgs/msg/Int32 '{data: 0}' >/dev/null 2>&1 || true
        timeout 1s ros2 topic pub --once /servo_s2 std_msgs/msg/Int32 '{data: 25}' >/dev/null 2>&1 || true
        pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|face_recognition_node|brain_node|twist_mux|bench_autonomy_monitor' 2>/dev/null || true
        rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
    "
    echo ">> Pipeline stopped cleanly."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "=================================================================="
echo "    STARTING COGNITION MULTI-MODAL BENCH DEMONSTRATION"
echo "=================================================================="

# Common environment for all nodes (FastDDS hardware bridge to host micro-ROS agent)
ROS_ENV="export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; export ROS_DOMAIN_ID=20; . /opt/ros/humble/setup.bash; . /root/cognition_ws/install/setup.bash 2>/dev/null || true"

# 1. Clean previous runs and purge stale FastDDS shared memory locks
echo "[1/7] Cleaning previous instances and FastDDS lockfiles..."
docker exec yahboom_gesture bash -c "
    pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|face_recognition_node|brain_node|twist_mux|bench_autonomy_monitor' 2>/dev/null || true
    rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
"
sleep 1

# Hardware Safety Check: Verify physical USB camera device presence on host
if [ ! -e /dev/video0 ] && [ ! -e /dev/video1 ]; then
    echo ""
    echo "=================================================================="
    echo "  [ERROR] USB CAMERA DISCONNECTED! (No /dev/video0 or /dev/video1 found on host)"
    echo "=================================================================="
    echo "  The camera USB cable has come unplugged from the Raspberry Pi."
    echo "  Please plug the USB camera into a USB port on the Pi and re-run:"
    echo "      bash ~/start_bench_pipeline.sh"
    echo "=================================================================="
    echo ""
    exit 1
fi

# Verify container has working access to camera device; restart container if device node is stale from USB disconnect
CAM_TEST=$(docker exec yahboom_gesture python3 -c "import cv2; c=cv2.VideoCapture(0); ret=c.isOpened(); c.release(); print(1 if ret else 0)" 2>/dev/null || echo 0)
if [ "$CAM_TEST" != "1" ]; then
    echo "[!] Camera not opening in container (stale device node from USB reconnect). Refreshing container..."
    docker restart yahboom_gesture >/dev/null 2>&1
    sleep 2
fi

# 2. Launch Background Pipeline Nodes inside container
echo "[2/7] Starting Camera Publisher (/dev/video0 -> /camera/image_raw/compressed)..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py > /tmp/camera_pub.log 2>&1 &
"
sleep 2

echo "[3/7] Starting Throttled Person Detection (YOLOv8n 10 Hz, 2 threads)..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/person_detection_node.py > /tmp/person_detection.log 2>&1 &
"
sleep 2

echo "[4/7] Starting Active Vision Gimbal Tracking Node..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py > /tmp/active_vision.log 2>&1 &
"
sleep 1

echo "[5/7] Starting InsightFace ArcFace Biometric Face ID Node..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/face_recognition_node.py > /tmp/face_recognition.log 2>&1 &
"
sleep 1

echo "[6/7] Starting MediaPipe Gesture Classifier..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/gesture_node.py > /tmp/gesture.log 2>&1 &
"
sleep 2

echo "[7/7] Starting Brain Decision & Motion Arbitration Node..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_brain/cognition_brain/brain_node.py --ros-args -p cmd_vel_topic:=/cmd_vel > /tmp/brain.log 2>&1 &
"
sleep 1

# Verify running processes inside container
echo ""
echo "=================================================================="
echo "  Verifying Active Autonomy Processes:"
echo "=================================================================="
docker exec yahboom_gesture ps aux | grep -E 'camera_pub|person_detection|active_vision|face_recognition|gesture_node|brain_node' | grep -v grep || echo "Warning: Some nodes failed to start"
echo "=================================================================="
echo ""

# 3. Launch live interactive HUD monitor in foreground
echo ">> Priming neural perception models (3s)..."
sleep 3
echo ">> Launching Live Autonomous Dashboard Monitor (Press Ctrl+C to exit)..."
docker exec -i yahboom_gesture bash -c "
    $ROS_ENV
    python3 -u /root/cognition_ws/bench_autonomy_monitor.py
"
cleanup

