#!/usr/bin/env bash
# ==============================================================================
# download_models.sh — Automated Verification and Retrieval of Perception Weights
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "$SCRIPT_DIR")"
WEIGHTS_DIR="$WS_DIR/ml_models/weights"

mkdir -p "$WEIGHTS_DIR"

echo "=================================================================="
echo "          VERIFYING AND DOWNLOADING PERCEPTION WEIGHTS"
echo "=================================================================="

# 1. MediaPipe Pose Landmarker Lite (~5.8 MB)
POSE_MODEL="$WEIGHTS_DIR/pose_landmarker_lite.task"
POSE_URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

if [[ -f "$POSE_MODEL" && -s "$POSE_MODEL" ]]; then
    echo ">> [OK] pose_landmarker_lite.task exists ($(du -h "$POSE_MODEL" | cut -f1))"
else
    echo ">> Downloading pose_landmarker_lite.task..."
    curl -L --fail --retry 3 -o "$POSE_MODEL" "$POSE_URL"
    echo ">> [SUCCESS] Downloaded pose_landmarker_lite.task ($(du -h "$POSE_MODEL" | cut -f1))"
fi

# 2. MediaPipe Hand Landmarker (~7.8 MB)
HAND_MODEL="$WEIGHTS_DIR/hand_landmarker.task"
HAND_URL="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

if [[ -f "$HAND_MODEL" && -s "$HAND_MODEL" ]]; then
    echo ">> [OK] hand_landmarker.task exists ($(du -h "$HAND_MODEL" | cut -f1))"
else
    echo ">> Downloading hand_landmarker.task..."
    curl -L --fail --retry 3 -o "$HAND_MODEL" "$HAND_URL"
    echo ">> [SUCCESS] Downloaded hand_landmarker.task ($(du -h "$HAND_MODEL" | cut -f1))"
fi

# 3. Check gesture classifier feature weights
for pkl in gesture_model_features.pkl scaler_features.pkl label_encoder_features.pkl; do
    if [[ -f "$WEIGHTS_DIR/$pkl" ]]; then
        echo ">> [OK] $pkl exists ($(du -h "$WEIGHTS_DIR/$pkl" | cut -f1))"
    else
        echo ">> [WARNING] $pkl missing from $WEIGHTS_DIR!"
    fi
done

echo "=================================================================="
echo "          PERCEPTION WEIGHTS VERIFICATION COMPLETE"
echo "=================================================================="
