#!/bin/bash
# ==============================================================================
# sync_to_bot.sh — One-Click Deployment Script to Physical Robot
# Synchronizes the verified 19-Feature MLP, hand_features, active_vision_node,
# and bench monitor directly into the running 'yahboom_gesture' Docker container.
# ==============================================================================

set -e

ROBOT_HOST="${1:-raspberrypi.local}"
ROBOT_USER="pi"

echo "=================================================================="
echo "    SYNCING AUTONOMY PERCEPTION STACK TO PHYSICAL ROBOT"
echo "    Target: ${ROBOT_USER}@${ROBOT_HOST}"
echo "=================================================================="

# 1. Connectivity Check
echo "[1/4] Checking robot reachability..."
if ! ping -c 1 -W 2 "${ROBOT_HOST}" >/dev/null 2>&1; then
    echo "[ERROR] Cannot reach ${ROBOT_HOST}!"
    echo "Please ensure the robot is powered on, connected to the network, and charging is complete."
    exit 1
fi
echo ">> Robot is reachable."

# 2. Transfer files to Pi staging directory
echo "[2/4] Transferring verified files to staging area on Pi..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" "mkdir -p ~/cognition_ws/models"

scp \
    /home/j/ros2_cognition_ws/src_nodes/gesture_node.py \
    /home/j/ros2_cognition_ws/src_nodes/hand_features.py \
    /home/j/ros2_cognition_ws/src_nodes/active_vision_node.py \
    /home/j/ros2_cognition_ws/scripts/bench_autonomy_monitor.py \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/"

scp \
    /home/j/ros2_cognition_ws/ml_models/weights/gesture_model_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/scaler_features.pkl \
    /home/j/ros2_cognition_ws/ml_models/weights/label_encoder_features.pkl \
    "${ROBOT_USER}@${ROBOT_HOST}:~/cognition_ws/models/"

# 3. Inject directly into Docker container
echo "[3/4] Injecting files into 'yahboom_gesture' Docker container..."
ssh "${ROBOT_USER}@${ROBOT_HOST}" bash -c "'
    CONTAINER=yahboom_gesture
    DEST_DIR=/root/cognition_ws/src/cognition_perception/cognition_perception

    # Copy Python nodes
    docker cp ~/cognition_ws/gesture_node.py \${CONTAINER}:\${DEST_DIR}/gesture_node.py
    docker cp ~/cognition_ws/hand_features.py \${CONTAINER}:\${DEST_DIR}/hand_features.py
    docker cp ~/cognition_ws/active_vision_node.py \${CONTAINER}:\${DEST_DIR}/active_vision_node.py
    docker cp ~/cognition_ws/bench_autonomy_monitor.py \${CONTAINER}:/root/cognition_ws/bench_autonomy_monitor.py

    # Copy models into package models dir and share dir
    docker exec \${CONTAINER} mkdir -p \${DEST_DIR}/models
    docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${DEST_DIR}/models/
    docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${DEST_DIR}/models/
    docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${DEST_DIR}/models/

    # Also copy to installed share directory if present
    SHARE_DIR=/root/cognition_ws/install/cognition_perception/share/cognition_perception/models
    if docker exec \${CONTAINER} test -d \${SHARE_DIR}; then
        docker cp ~/cognition_ws/models/gesture_model_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/scaler_features.pkl \${CONTAINER}:\${SHARE_DIR}/
        docker cp ~/cognition_ws/models/label_encoder_features.pkl \${CONTAINER}:\${SHARE_DIR}/
    fi

    echo \">> Files successfully copied into Docker container.\"
'"

# 4. Success summary
echo "[4/4] Verification complete."
echo "=================================================================="
echo "  DEPLOYMENT READY!"
echo "  When ready on the robot, run:"
echo "      bash ~/start_bench_pipeline.sh"
echo "=================================================================="
