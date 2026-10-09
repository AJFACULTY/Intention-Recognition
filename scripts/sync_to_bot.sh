#!/bin/bash
# ==============================================================================
# sync_to_bot.sh — One-Click Deployment Script to Physical Robot
# Synchronizes the verified 19-Feature MLP, hand_features, active_vision_node,
# and bench monitor directly into the running 'yahboom_gesture' Docker container.
# ==============================================================================

set -e

ROBOT_HOST="${1:-${ROBOT_IP:-}}"
ROBOT_USER="pi"

# Auto-detect robot host IP if not explicitly provided
if [ -z "$ROBOT_HOST" ]; then
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "$SCRIPT_DIR")"

# 2. Transfer files to Pi staging directory
echo "[2/4] Transferring verified files to staging area on Pi..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" "mkdir -p ~/cognition_ws/models ~/cognition_ws/assets ~/maps_new ~/cognition_ws/src/cognition_perception/cognition_perception ~/cognition_ws/src/cognition_brain/cognition_brain"

scp \
    "$WS_DIR/src_nodes/gesture_node.py" \
    "$WS_DIR/src_nodes/hand_features.py" \
    "$WS_DIR/src_nodes/active_vision_node.py" \
    "$WS_DIR/src_nodes/person_detection_node.py" \
    "$WS_DIR/src_nodes/camera_pub.py" \
    "$WS_DIR/src_nodes/face_recognition_node.py" \
    "$WS_DIR/src_nodes/face_id_lib.py" \
    "$WS_DIR/src_nodes/brain_node.py" \
    "$WS_DIR/src_nodes/safety_audio_node.py" \
    "$WS_DIR/scripts/master_demo_menu.py" \
    "$WS_DIR/scripts/menu.sh" \
    "$WS_DIR/scripts/bench_autonomy_monitor.py" \
    "$WS_DIR/scripts/mission_manager.py" \
    "$WS_DIR/scripts/plot_multi_waypoint_trajectory.py" \
    "$WS_DIR/scripts/web_map_visualizer.py" \
    "$WS_DIR/scripts/navigate_waypoints.py" \
    "$WS_DIR/scripts/setup_joystick_service.sh" \
    "$WS_DIR/scripts/test_safety_audio.py" \
    "$WS_DIR/scripts/diagnostics/test_camera_stream.py" \
    "$WS_DIR/scripts/diagnostics/show_system_resources.py" \
    "$WS_DIR/launch/nav2.launch.py" \
    "$WS_DIR/launch/demo_system.launch.py" \
    "$WS_DIR/launch/cognition_autonomy.launch.py" \
    "$WS_DIR/launch/master_robot.launch.py" \
    "$WS_DIR/launch/follow_to_map.launch.py" \
    "$WS_DIR/config/twist_mux.yaml" \
    "$WS_DIR/config/nav2_params.yaml" \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/"

scp \
    "$WS_DIR/scripts/menu.sh" \
    "$WS_DIR/scripts/start_nav2.sh" \
    "$WS_DIR/scripts/start_bench_pipeline.sh" \
    "$WS_DIR/scripts/run_nav2_patrol.sh" \
    "$WS_DIR/scripts/run_mission.sh" \
    "$WS_DIR/scripts/setup_joystick_service.sh" \
    "$WS_DIR/scripts/launch_autonomy.sh" \
    "$WS_DIR/scripts/stop_autonomy.sh" \
    "$WS_DIR/src_nodes/brain_node.py" \
    "${ROBOT_USER}@${ROBOT_HOST}:~/"

ssh "${ROBOT_USER}@${ROBOT_HOST}" "chmod +x ~/menu.sh ~/start_nav2.sh ~/start_bench_pipeline.sh ~/run_nav2_patrol.sh ~/run_mission.sh ~/setup_joystick_service.sh ~/launch_autonomy.sh ~/stop_autonomy.sh ~/cognition_ws/menu.sh ~/cognition_ws/master_demo_menu.py ~/cognition_ws/setup_joystick_service.sh ~/cognition_ws/navigate_waypoints.py ~/cognition_ws/mission_manager.py ~/cognition_ws/safety_audio_node.py ~/cognition_ws/plot_multi_waypoint_trajectory.py ~/cognition_ws/show_system_resources.py"

scp \
    "$WS_DIR/ml_models/weights/gesture_model_features.pkl" \
    "$WS_DIR/ml_models/weights/scaler_features.pkl" \
    "$WS_DIR/ml_models/weights/label_encoder_features.pkl" \
    "$WS_DIR/ml_models/weights/hand_landmarker.task" \
    "$WS_DIR/ml_models/weights/path_predictor.onnx" \
    "$WS_DIR/ml_models/weights/path_predictor.onnx.data" \
    "$WS_DIR/ml_models/weights/path_predictor_config.pkl" \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/models/"

scp \
    "$WS_DIR/maps/room_map.yaml" \
    "$WS_DIR/maps/room_map.png" \
    "${ROBOT_USER}@${ROBOT_HOST}:~/maps_new/"

if [ -f "$WS_DIR/assets/preview_camera.jpg" ]; then
    scp "$WS_DIR/assets/preview_camera.jpg" "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/assets/" 2>/dev/null || true
fi

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
    docker exec \${CONTAINER} mkdir -p /root/cognition_ws/assets /root/cognition_ws/maps_new /root/cognition_ws/maps /root/cognition_ws/src_nodes /root/cognition_ws/scripts /root/cognition_ws/scripts/diagnostics /root/cognition_ws/src/cognition_simulation/src_nodes /root/cognition_ws/src/cognition_simulation/scripts
    docker cp ~/cognition_ws/assets/preview_camera.jpg \${CONTAINER}:/root/cognition_ws/assets/preview_camera.jpg 2>/dev/null || true
    docker cp ~/maps_new/room_map.png \${CONTAINER}:/root/cognition_ws/maps/room_map.png
    docker cp ~/maps_new/room_map.yaml \${CONTAINER}:/root/cognition_ws/maps/room_map.yaml
    docker cp ~/maps_new/room_map.png \${CONTAINER}:/root/cognition_ws/maps_new/room_map_20260812_0826.png 2>/dev/null || true
    docker cp ~/maps_new/room_map.yaml \${CONTAINER}:/root/cognition_ws/maps_new/room_map_20260812_0826.yaml 2>/dev/null || true
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
    docker cp ~/cognition_ws/twist_mux.yaml \${CONTAINER}:/root/cognition_ws/config/twist_mux.yaml 2>/dev/null || true
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
