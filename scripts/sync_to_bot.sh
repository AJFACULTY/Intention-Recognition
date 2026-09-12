#!/bin/bash
# ==============================================================================
# sync_to_bot.sh — One-Click Deployment Script to Physical Robot
# Synchronizes the verified 19-Feature MLP, hand_features, active_vision_node,
# and bench monitor directly into the running 'yahboom_gesture' Docker container.
# ==============================================================================

set -e

ROBOT_HOST="${1:-10.27.122.135}"
ROBOT_USER="pi"

# Auto-detect robot host IP if not explicitly provided
if [ -n "$1" ]; then
    ROBOT_HOST="$1"
else
    if ping -c 1 -W 1 10.27.122.136 >/dev/null 2>&1; then
        ROBOT_HOST="10.27.122.136"
    elif ping -c 1 -W 1 10.27.122.135 >/dev/null 2>&1; then
        ROBOT_HOST="10.27.122.135"
    else
        ROBOT_HOST="10.27.122.136"
    fi
fi

echo "=================================================================="
echo "    SYNCING AUTONOMY PERCEPTION STACK TO PHYSICAL ROBOT"
echo "    Target: ${ROBOT_USER}@${ROBOT_HOST}"
echo "=================================================================="

# 1. Connectivity Check
echo "[1/4] Checking robot reachability..."
if ! ping -c 1 -W 2 "${ROBOT_HOST}" >/dev/null 2>&1; then
    echo "[ERROR] Cannot reach ${ROBOT_HOST}!"
    echo "Please ensure the robot is powered on and connected to the network."
    exit 1
fi
echo ">> Robot is reachable at ${ROBOT_HOST}."

# 2. Transfer files to Pi staging directory
echo "[2/4] Transferring verified files to staging area on Pi..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" "mkdir -p ~/cognition_ws/models ~/cognition_ws/src/cognition_perception/cognition_perception ~/cognition_ws/src/cognition_brain/cognition_brain"

scp \
    /home/j/ros2_cognition_ws/src_nodes/gesture_node.py \
    /home/j/ros2_cognition_ws/src_nodes/hand_features.py \
    /home/j/ros2_cognition_ws/src_nodes/active_vision_node.py \
    /home/j/ros2_cognition_ws/src_nodes/person_detection_node.py \
    /home/j/ros2_cognition_ws/src_nodes/camera_pub.py \
    /home/j/ros2_cognition_ws/src_nodes/face_recognition_node.py \
    /home/j/ros2_cognition_ws/src_nodes/face_id_lib.py \
    /home/j/ros2_cognition_ws/src_nodes/brain_node.py \
    /home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py \
    /home/j/ros2_cognition_ws/scripts/mission_manager.py \
    /home/j/ros2_cognition_ws/scripts/web_map_visualizer.py \
    /home/j/ros2_cognition_ws/scripts/navigate_waypoints.py \
    /home/j/ros2_cognition_ws/launch/nav2.launch.py \
    /home/j/ros2_cognition_ws/launch/demo_system.launch.py \
    /home/j/ros2_cognition_ws/launch/cognition_autonomy.launch.py \
    /home/j/ros2_cognition_ws/config/nav2_params.yaml \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/"

scp \
    /home/j/ros2_cognition_ws/scripts/start_nav2.sh \
    /home/j/ros2_cognition_ws/scripts/start_bench_pipeline.sh \
    /home/j/ros2_cognition_ws/scripts/run_nav2_patrol.sh \
    /home/j/ros2_cognition_ws/scripts/run_mission.sh \
    /home/j/ros2_cognition_ws/src_nodes/brain_node.py \
    "${ROBOT_USER}@${ROBOT_HOST}:~/"

ssh "${ROBOT_USER}@${ROBOT_HOST}" "chmod +x ~/start_nav2.sh ~/start_bench_pipeline.sh ~/run_nav2_patrol.sh ~/run_mission.sh ~/cognition_ws/navigate_waypoints.py ~/cognition_ws/mission_manager.py"

scp \
    /home/j/ros2_cognition_ws/ml_models/weights/gesture_model_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/scaler_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/label_encoder_features.pkl \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/models/"

# 3. Synchronize package sources and inject directly into Docker container
echo "[3/4] Updating package source trees and injecting into 'yahboom_gesture' Docker container..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" bash -c "'
    CONTAINER=yahboom_gesture
    PERCEPT_DIR=/root/cognition_ws/src/cognition_perception/cognition_perception
    BRAIN_DIR=/root/cognition_ws/src/cognition_brain/cognition_brain
    CONFIG_DIR=/root/cognition_ws/src/cognition_simulation/config

    # Synchronize host source tree
    cp ~/cognition_ws/gesture_node.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/hand_features.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/active_vision_node.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/person_detection_node.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/camera_pub.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/face_recognition_node.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/face_id_lib.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/brain_node.py ~/cognition_ws/src/cognition_brain/cognition_brain/

    # Copy Perception nodes into container
    docker cp ~/cognition_ws/gesture_node.py \${CONTAINER}:\${PERCEPT_DIR}/gesture_node.py
    docker cp ~/cognition_ws/hand_features.py \${CONTAINER}:\${PERCEPT_DIR}/hand_features.py
    docker cp ~/cognition_ws/active_vision_node.py \${CONTAINER}:\${PERCEPT_DIR}/active_vision_node.py
    docker cp ~/cognition_ws/person_detection_node.py \${CONTAINER}:\${PERCEPT_DIR}/person_detection_node.py
    docker cp ~/cognition_ws/camera_pub.py \${CONTAINER}:\${PERCEPT_DIR}/camera_pub.py
    docker cp ~/cognition_ws/face_recognition_node.py \${CONTAINER}:\${PERCEPT_DIR}/face_recognition_node.py
    docker cp ~/cognition_ws/face_id_lib.py \${CONTAINER}:\${PERCEPT_DIR}/face_id_lib.py
    docker cp ~/cognition_ws/bench_autonomy_monitor.py \${CONTAINER}:/root/cognition_ws/bench_autonomy_monitor.py

    # Copy Brain Decision node, Mission Manager, Waypoint Navigator & Web Map Visualizer
    docker cp ~/cognition_ws/brain_node.py \${CONTAINER}:\${BRAIN_DIR}/brain_node.py
    docker cp ~/cognition_ws/mission_manager.py \${CONTAINER}:/root/cognition_ws/mission_manager.py
    docker cp ~/cognition_ws/navigate_waypoints.py \${CONTAINER}:/root/cognition_ws/navigate_waypoints.py
    docker cp ~/cognition_ws/web_map_visualizer.py \${CONTAINER}:/root/cognition_ws/web_map_visualizer.py
    docker cp ~/cognition_ws/nav2_params.yaml \${CONTAINER}:\${CONFIG_DIR}/nav2_params.yaml

    # Copy Launch files into container source and install share directories
    LAUNCH_SRC=/root/cognition_ws/src/cognition_simulation/launch
    LAUNCH_SHARE=/root/cognition_ws/install/cognition_simulation/share/cognition_simulation/launch
    docker exec \${CONTAINER} mkdir -p \${LAUNCH_SRC} \${LAUNCH_SHARE}
    docker cp ~/cognition_ws/nav2.launch.py \${CONTAINER}:\${LAUNCH_SRC}/nav2.launch.py
    docker cp ~/cognition_ws/demo_system.launch.py \${CONTAINER}:\${LAUNCH_SRC}/demo_system.launch.py
    docker cp ~/cognition_ws/cognition_autonomy.launch.py \${CONTAINER}:\${LAUNCH_SRC}/cognition_autonomy.launch.py
    docker cp ~/cognition_ws/nav2.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/nav2.launch.py
    docker cp ~/cognition_ws/demo_system.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/demo_system.launch.py
    docker cp ~/cognition_ws/cognition_autonomy.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/cognition_autonomy.launch.py

    # Update installed python package location if present
    INSTALLED_BRAIN=/root/cognition_ws/install/cognition_brain/lib/python3.10/site-packages/cognition_brain/brain_node.py
    if docker exec \${CONTAINER} test -f \${INSTALLED_BRAIN}; then
        docker cp ~/cognition_ws/brain_node.py \${CONTAINER}:\${INSTALLED_BRAIN}
    fi

    # Copy models into package models dir and share dir
    docker exec \${CONTAINER} mkdir -p \${PERCEPT_DIR}/models
    docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/

    # Also copy to installed share directory if present
    SHARE_DIR=/root/cognition_ws/install/cognition_perception/share/cognition_perception/models
    if docker exec \${CONTAINER} test -d \${SHARE_DIR}; then
        docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${SHARE_DIR}/
    fi

    echo \">> All autonomy, mission, waypoint, and model files successfully injected into Docker container.\"
'"

# 4. Success summary
echo "[4/4] Verification complete."
echo "=================================================================="
echo "  DEPLOYMENT READY ON ${ROBOT_HOST}!"
echo "  When ready on the robot, run:"
echo "      bash ~/start_bench_pipeline.sh"
echo "  Or for autonomous waypoint patrol:"
echo "      bash ~/run_nav2_patrol.sh"
echo "=================================================================="
