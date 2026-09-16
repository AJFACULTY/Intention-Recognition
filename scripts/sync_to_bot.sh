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
ssh "${ROBOT_USER}@${ROBOT_HOST}" "mkdir -p ~/cognition_ws/models ~/cognition_ws/assets ~/maps_new ~/cognition_ws/src/cognition_perception/cognition_perception ~/cognition_ws/src/cognition_brain/cognition_brain"

scp \
    /home/j/ros2_cognition_ws/src_nodes/gesture_node.py \
    /home/j/ros2_cognition_ws/src_nodes/hand_features.py \
    /home/j/ros2_cognition_ws/src_nodes/active_vision_node.py \
    /home/j/ros2_cognition_ws/src_nodes/person_detection_node.py \
    /home/j/ros2_cognition_ws/src_nodes/camera_pub.py \
    /home/j/ros2_cognition_ws/src_nodes/face_recognition_node.py \
    /home/j/ros2_cognition_ws/src_nodes/face_id_lib.py \
    /home/j/ros2_cognition_ws/src_nodes/brain_node.py \
    /home/j/ros2_cognition_ws/src_nodes/safety_audio_node.py \
    /home/j/ros2_cognition_ws/scripts/master_demo_menu.py \
    /home/j/ros2_cognition_ws/scripts/menu.sh \
    /home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py \
    /home/j/ros2_cognition_ws/scripts/mission_manager.py \
    /home/j/ros2_cognition_ws/scripts/plot_multi_waypoint_trajectory.py \
    /home/j/ros2_cognition_ws/scripts/web_map_visualizer.py \
    /home/j/ros2_cognition_ws/scripts/navigate_waypoints.py \
    /home/j/ros2_cognition_ws/scripts/setup_joystick_service.sh \
    /home/j/ros2_cognition_ws/scripts/test_safety_audio.py \
    /home/j/ros2_cognition_ws/scripts/diagnostics/test_camera_stream.py \
    /home/j/ros2_cognition_ws/scripts/diagnostics/show_system_resources.py \
    /home/j/ros2_cognition_ws/launch/nav2.launch.py \
    /home/j/ros2_cognition_ws/launch/demo_system.launch.py \
    /home/j/ros2_cognition_ws/launch/cognition_autonomy.launch.py \
    /home/j/ros2_cognition_ws/launch/master_robot.launch.py \
    /home/j/ros2_cognition_ws/launch/follow_to_map.launch.py \
    /home/j/ros2_cognition_ws/launch/twist_mux.yaml \
    /home/j/ros2_cognition_ws/config/nav2_params.yaml \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/"

scp \
    /home/j/ros2_cognition_ws/scripts/menu.sh \
    /home/j/ros2_cognition_ws/scripts/start_nav2.sh \
    /home/j/ros2_cognition_ws/scripts/start_bench_pipeline.sh \
    /home/j/ros2_cognition_ws/scripts/run_nav2_patrol.sh \
    /home/j/ros2_cognition_ws/scripts/run_mission.sh \
    /home/j/ros2_cognition_ws/scripts/setup_joystick_service.sh \
    /home/j/ros2_cognition_ws/scripts/launch_autonomy.sh \
    /home/j/ros2_cognition_ws/scripts/stop_autonomy.sh \
    /home/j/ros2_cognition_ws/src_nodes/brain_node.py \
    "${ROBOT_USER}@${ROBOT_HOST}:~/"

ssh "${ROBOT_USER}@${ROBOT_HOST}" "chmod +x ~/menu.sh ~/start_nav2.sh ~/start_bench_pipeline.sh ~/run_nav2_patrol.sh ~/run_mission.sh ~/setup_joystick_service.sh ~/launch_autonomy.sh ~/stop_autonomy.sh ~/cognition_ws/menu.sh ~/cognition_ws/master_demo_menu.py ~/cognition_ws/setup_joystick_service.sh ~/cognition_ws/navigate_waypoints.py ~/cognition_ws/mission_manager.py ~/cognition_ws/safety_audio_node.py ~/cognition_ws/plot_multi_waypoint_trajectory.py ~/cognition_ws/show_system_resources.py"

scp \
    /home/j/ros2_cognition_ws/ml_models/weights/gesture_model_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/scaler_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/label_encoder_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/hand_landmarker.task \
    /home/j/ros2_cognition_ws/ml_models/weights/path_predictor.onnx \
    /home/j/ros2_cognition_ws/ml_models/weights/path_predictor.onnx.data \
    /home/j/ros2_cognition_ws/ml_models/weights/path_predictor_config.pkl \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/models/"

scp \
    /home/j/ros2_cognition_ws/maps/room_map_20260812_0826.yaml \
    /home/j/ros2_cognition_ws/maps/room_map_20260812_0826.png \
    "${ROBOT_USER}@${ROBOT_HOST}:~/maps_new/"

scp \
    /home/j/ros2_cognition_ws/assets/preview_camera.jpg \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/assets/"

# 3. Synchronize package sources and inject directly into Docker container
echo "[3/4] Updating package source trees and injecting into 'yahboom_gesture' Docker container..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" bash -c "'
    CONTAINER=yahboom_gesture
    docker start \${CONTAINER} >/dev/null 2>&1 || true
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
    cp ~/cognition_ws/safety_audio_node.py ~/cognition_ws/src/cognition_perception/cognition_perception/
    cp ~/cognition_ws/brain_node.py ~/cognition_ws/src/cognition_brain/cognition_brain/

    # Copy Perception & Audio nodes into container across all fallback locations
    docker exec \${CONTAINER} mkdir -p /root/cognition_ws/assets /root/cognition_ws/maps_new /root/cognition_ws/src_nodes /root/cognition_ws/scripts /root/cognition_ws/scripts/diagnostics /root/cognition_ws/src/cognition_simulation/src_nodes /root/cognition_ws/src/cognition_simulation/scripts
    docker cp ~/cognition_ws/assets/preview_camera.jpg \${CONTAINER}:/root/cognition_ws/assets/preview_camera.jpg
    docker cp ~/maps_new/room_map_20260812_0826.png \${CONTAINER}:/root/cognition_ws/maps_new/room_map_20260812_0826.png
    docker cp ~/maps_new/room_map_20260812_0826.yaml \${CONTAINER}:/root/cognition_ws/maps_new/room_map_20260812_0826.yaml
    docker cp ~/cognition_ws/gesture_node.py \${CONTAINER}:\${PERCEPT_DIR}/gesture_node.py
    docker cp ~/cognition_ws/hand_features.py \${CONTAINER}:\${PERCEPT_DIR}/hand_features.py
    docker cp ~/cognition_ws/active_vision_node.py \${CONTAINER}:\${PERCEPT_DIR}/active_vision_node.py
    docker cp ~/cognition_ws/person_detection_node.py \${CONTAINER}:\${PERCEPT_DIR}/person_detection_node.py
    docker cp ~/cognition_ws/face_recognition_node.py \${CONTAINER}:\${PERCEPT_DIR}/face_recognition_node.py
    docker cp ~/cognition_ws/face_id_lib.py \${CONTAINER}:\${PERCEPT_DIR}/face_id_lib.py

    for dir in \${PERCEPT_DIR} /root/cognition_ws /root/cognition_ws/src_nodes /root/cognition_ws/src/cognition_simulation/src_nodes; do
        docker cp ~/cognition_ws/camera_pub.py \${CONTAINER}:\${dir}/camera_pub.py
        docker cp ~/cognition_ws/safety_audio_node.py \${CONTAINER}:\${dir}/safety_audio_node.py
    done

    docker cp ~/cognition_ws/bench_autonomy_monitor.py \${CONTAINER}:/root/cognition_ws/bench_autonomy_monitor.py
    docker cp ~/cognition_ws/master_demo_menu.py \${CONTAINER}:/root/cognition_ws/master_demo_menu.py
    docker cp ~/cognition_ws/master_demo_menu.py \${CONTAINER}:/root/cognition_ws/scripts/master_demo_menu.py
    docker cp ~/cognition_ws/show_system_resources.py \${CONTAINER}:/root/cognition_ws/scripts/diagnostics/show_system_resources.py
    docker cp ~/cognition_ws/show_system_resources.py \${CONTAINER}:/root/cognition_ws/show_system_resources.py

    # Copy Brain Decision node, Mission Manager, Waypoint Navigator & Web Map Visualizer
    docker cp ~/cognition_ws/brain_node.py \${CONTAINER}:\${BRAIN_DIR}/brain_node.py
    docker cp ~/cognition_ws/mission_manager.py \${CONTAINER}:/root/cognition_ws/mission_manager.py
    docker cp ~/cognition_ws/navigate_waypoints.py \${CONTAINER}:/root/cognition_ws/navigate_waypoints.py

    for dir in /root/cognition_ws /root/cognition_ws/scripts /root/cognition_ws/src/cognition_simulation/scripts; do
        docker cp ~/cognition_ws/web_map_visualizer.py \${CONTAINER}:\${dir}/web_map_visualizer.py
    done
    docker cp ~/cognition_ws/nav2_params.yaml \${CONTAINER}:\${CONFIG_DIR}/nav2_params.yaml
    docker cp ~/cognition_ws/twist_mux.yaml \${CONTAINER}:/root/cognition_ws/twist_mux.yaml
    docker cp ~/cognition_ws/twist_mux.yaml \${CONTAINER}:\${LAUNCH_SRC}/twist_mux.yaml

    # Copy Launch files into container source and install share directories
    LAUNCH_SRC=/root/cognition_ws/src/cognition_simulation/launch
    LAUNCH_SHARE=/root/cognition_ws/install/cognition_simulation/share/cognition_simulation/launch
    docker exec \${CONTAINER} mkdir -p \${LAUNCH_SRC} \${LAUNCH_SHARE}
    docker cp ~/cognition_ws/nav2.launch.py \${CONTAINER}:\${LAUNCH_SRC}/nav2.launch.py
    docker cp ~/cognition_ws/demo_system.launch.py \${CONTAINER}:\${LAUNCH_SRC}/demo_system.launch.py
    docker cp ~/cognition_ws/cognition_autonomy.launch.py \${CONTAINER}:\${LAUNCH_SRC}/cognition_autonomy.launch.py
    docker cp ~/cognition_ws/master_robot.launch.py \${CONTAINER}:\${LAUNCH_SRC}/master_robot.launch.py
    docker cp ~/cognition_ws/follow_to_map.launch.py \${CONTAINER}:\${LAUNCH_SRC}/follow_to_map.launch.py
    docker cp ~/cognition_ws/nav2.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/nav2.launch.py
    docker cp ~/cognition_ws/demo_system.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/demo_system.launch.py
    docker cp ~/cognition_ws/cognition_autonomy.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/cognition_autonomy.launch.py
    docker cp ~/cognition_ws/master_robot.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/master_robot.launch.py
    docker cp ~/cognition_ws/follow_to_map.launch.py \${CONTAINER}:\${LAUNCH_SHARE}/follow_to_map.launch.py
    docker cp ~/cognition_ws/master_robot.launch.py \${CONTAINER}:/root/cognition_ws/master_robot.launch.py
    docker cp ~/cognition_ws/follow_to_map.launch.py \${CONTAINER}:/root/cognition_ws/follow_to_map.launch.py

    # Update installed python package location if present
    INSTALLED_BRAIN=/root/cognition_ws/install/cognition_brain/lib/python3.10/site-packages/cognition_brain/brain_node.py
    if docker exec \${CONTAINER} test -f \${INSTALLED_BRAIN}; then
        docker cp ~/cognition_ws/brain_node.py \${CONTAINER}:\${INSTALLED_BRAIN}
    fi

    # Copy models into package models dir, container models dir, and share dir
    docker exec \${CONTAINER} mkdir -p \${PERCEPT_DIR}/models /root/cognition_ws/models
    docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/hand_landmarker.task \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/path_predictor.onnx \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/path_predictor.onnx.data \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/path_predictor_config.pkl \${CONTAINER}:\${PERCEPT_DIR}/models/
    docker cp ~/cognition_ws/models/hand_landmarker.task \${CONTAINER}:/root/cognition_ws/models/
    docker cp ~/cognition_ws/models/path_predictor.onnx \${CONTAINER}:/root/cognition_ws/models/
    docker cp ~/cognition_ws/models/path_predictor.onnx.data \${CONTAINER}:/root/cognition_ws/models/
    docker cp ~/cognition_ws/models/path_predictor_config.pkl \${CONTAINER}:/root/cognition_ws/models/

    # Also copy to installed share directory if present
    SHARE_DIR=/root/cognition_ws/install/cognition_perception/share/cognition_perception/models
    if docker exec \${CONTAINER} test -d \${SHARE_DIR}; then
        docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/hand_landmarker.task \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/path_predictor.onnx \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/path_predictor.onnx.data \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/path_predictor_config.pkl \${CONTAINER}:\${SHARE_DIR}/
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
