#!/bin/bash

# Bag recording toggle via CLI argument (--record / -r) or env variable (RECORD=1)
RECORD_BAG=false
if [ "${1:-}" = "--record" ] || [ "${1:-}" = "-r" ] || [ "${RECORD:-0}" = "1" ]; then
    RECORD_BAG=true
fi
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BAG_NAME="gesture_follow_${TIMESTAMP}"

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
        timeout 1s ros2 topic pub --once /servo_s2 std_msgs/msg/Int32 '{data: 30}' >/dev/null 2>&1 || true
        pkill -2 -f 'ros2 bag record' 2>/dev/null || true
        sleep 1
        pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|face_recognition_node|brain_node|twist_mux|bench_autonomy_monitor|web_map_visualizer|ros2 bag record' 2>/dev/null || true
        rm -f /dev/shm/sem.fastrtps_* /dev/shm/fastrtps_* 2>/dev/null || true
    "
    echo ">> Pipeline stopped cleanly."
    if [ "$RECORD_BAG" = "true" ]; then
        echo ">> Synchronized bag saved to: ~/cognition_ws/bags/${BAG_NAME}"
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "=================================================================="
echo "    STARTING COGNITION MULTI-MODAL BENCH DEMONSTRATION"
if [ "$RECORD_BAG" = "true" ]; then
    echo "    [BAG RECORDING ACTIVE]: ${BAG_NAME}"
fi
echo "=================================================================="

# Common environment for all nodes (FastDDS hardware bridge to host micro-ROS agent)
ROS_ENV="export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; export ROS_DOMAIN_ID=20; . /opt/ros/humble/setup.bash; . /root/cognition_ws/install/setup.bash 2>/dev/null || true"

# 1. Clean previous runs and purge stale FastDDS shared memory locks
echo "[1/8] Cleaning previous instances and FastDDS lockfiles..."
docker exec yahboom_gesture bash -c "
    pkill -9 -f 'camera_pub|person_detection_node|gesture_node|active_vision_node|face_recognition_node|brain_node|twist_mux|bench_autonomy_monitor|web_map_visualizer|ros2 bag record' 2>/dev/null || true
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
echo "[2/8] Starting Camera Publisher (/dev/video* -> /camera/image_raw/compressed)..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    CAM_SCRIPT=\$(test -f /root/cognition_ws/camera_pub.py && echo /root/cognition_ws/camera_pub.py || echo /root/cognition_ws/src/cognition_perception/cognition_perception/camera_pub.py)
    nohup python3 -u \"\$CAM_SCRIPT\" > /tmp/camera_pub.log 2>&1 &
"
sleep 2

echo "[3/8] Starting Throttled Person Detection (YOLOv8n 10 Hz, 2 threads)..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/person_detection_node.py > /tmp/person_detection.log 2>&1 &
"
sleep 2

echo "[4/8] Starting Active Vision Gimbal Tracking Node..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/active_vision_node.py > /tmp/active_vision.log 2>&1 &
"
sleep 1

HAS_INSIGHTFACE=$(docker exec yahboom_gesture python3 -c "import insightface; print(1)" 2>/dev/null || echo 0)
if [ "$HAS_INSIGHTFACE" = "1" ]; then
    echo "[5/8] Starting InsightFace ArcFace Biometric Face ID Node..."
    docker exec yahboom_gesture bash -c "
        $ROS_ENV
        nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/face_recognition_node.py > /tmp/face_recognition.log 2>&1 &
    "
    sleep 1
else
    echo "[5/8] ArcFace Biometric Auth: Optional / Skipped (Pure Gesture Mode Active)"
fi

echo "[6/8] Starting 19-Feature MediaPipe Gesture Classifier..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_perception/cognition_perception/gesture_node.py > /tmp/gesture.log 2>&1 &
"
sleep 2

echo "[7/8] Starting Brain Decision & Motion Arbitration Node..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    nohup python3 -u /root/cognition_ws/src/cognition_brain/cognition_brain/brain_node.py --ros-args -p cmd_vel_topic:=/cmd_vel -p require_face_auth:=false > /tmp/brain.log 2>&1 &
"
sleep 1

echo "[8/8] Starting Live Web Map & Camera Visualizer Dashboard on Port :8080..."
docker exec yahboom_gesture bash -c "
    $ROS_ENV
    VIS_SCRIPT=\$(test -f /root/cognition_ws/web_map_visualizer.py && echo /root/cognition_ws/web_map_visualizer.py || echo /root/cognition_ws/scripts/web_map_visualizer.py)
    nohup python3 -u \"\$VIS_SCRIPT\" > /tmp/web_vis.log 2>&1 &
"
sleep 1

if [ "$RECORD_BAG" = "true" ]; then
    echo "[*] Starting Synchronized Telemetry Bag Recorder..."
    echo "    Output Destination: /root/cognition_ws/bags/${BAG_NAME}"
    docker exec yahboom_gesture bash -c "
        $ROS_ENV
        mkdir -p /root/cognition_ws/bags
        nohup ros2 bag record -o /root/cognition_ws/bags/${BAG_NAME} \
            /cognition/gesture \
            /cognition/detection \
            /cmd_vel \
            /cmd_vel_gesture \
            /odom_raw \
            /imu \
            /scan \
            /tf \
            /tf_static > /tmp/bag_record.log 2>&1 &
    "
    sleep 1
fi

# Verify running processes inside container
echo ""
echo "=================================================================="
echo "  Verifying Active Autonomy Processes:"
echo "=================================================================="
docker exec yahboom_gesture ps aux | grep -E 'camera_pub|person_detection|active_vision|gesture_node|brain_node|web_map_visualizer' | grep -v grep || echo "Warning: Some nodes failed to start"
echo "  >> Live Web Visualizer is ACTIVE at: http://\$(hostname -I | awk '{print \$1}'):8080"
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

