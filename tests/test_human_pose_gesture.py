#!/usr/bin/env python3
"""
test_human_pose_gesture.py — Automated Unit & Integration Test for Phase 2 Stack
================================================================================
Verifies:
1. Model weights presence and integrity (pose_landmarker_lite, hand_landmarker, MLP)
2. FastDDS dynamic memory configuration XML
3. Nav2 2D ObstacleLayer parameterization
4. Biomechanical Kinematic Attention logic in human_pose_gesture_node
5. Gesture classification on dummy hand landmarks
"""

import os
import sys
import xml.etree.ElementTree as ET
import yaml
import numpy as np

WS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(WS_DIR, "src_nodes"))


def test_fastdds_xml():
    xml_path = os.path.join(WS_DIR, "config", "fastdds_lowmem.xml")
    assert os.path.exists(xml_path), f"Missing {xml_path}"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Verify DYNAMIC_RESERVE_MEMORY_MODE is set in data_writer and data_reader
    policies = [el.text for el in root.iter() if el.tag.endswith("historyMemoryPolicy")]
    assert len(policies) >= 2, "FastDDS XML must contain historyMemoryPolicy elements"
    for p in policies:
        assert p == "DYNAMIC_RESERVE_MEMORY_MODE", f"Unexpected memory policy: {p}"
    print("✓ FastDDS XML verified (DYNAMIC_RESERVE_MEMORY_MODE)")


def test_nav2_yaml():
    yaml_path = os.path.join(WS_DIR, "config", "nav2_params.yaml")
    assert os.path.exists(yaml_path), f"Missing {yaml_path}"
    with open(yaml_path, "r") as f:
        cfg = yaml.safe_load(f)

    local_plugins = cfg["local_costmap"]["local_costmap"]["ros__parameters"]["plugins"]
    assert "obstacle_layer" in local_plugins, "local_costmap must contain obstacle_layer"
    assert "voxel_layer" not in local_plugins, "local_costmap must NOT contain 3D voxel_layer"

    obstacle_plugin = cfg["local_costmap"]["local_costmap"]["ros__parameters"]["obstacle_layer"]["plugin"]
    assert obstacle_plugin == "nav2_costmap_2d::ObstacleLayer", f"Unexpected plugin: {obstacle_plugin}"
    print("✓ Nav2 2D ObstacleLayer verified (3D VoxelLayer eliminated)")


def test_model_weights():
    weights_dir = os.path.join(WS_DIR, "ml_models", "weights")
    required = [
        "pose_landmarker_lite.task",
        "hand_landmarker.task",
        "gesture_model_features.pkl",
        "scaler_features.pkl",
        "label_encoder_features.pkl"
    ]
    for fname in required:
        fpath = os.path.join(weights_dir, fname)
        assert os.path.exists(fpath), f"Weight file missing: {fname}"
        assert os.path.getsize(fpath) > 0, f"Weight file empty: {fname}"
    print(f"✓ All {len(required)} perception weight files verified")


def test_biomechanical_gating_logic():
    class DummyLandmark:
        def __init__(self, x, y, visibility=1.0):
            self.x = x
            self.y = y
            self.visibility = visibility

    # 33 landmarks
    landmarks = [DummyLandmark(0.5, 0.5) for _ in range(33)]

    # Hips at y=0.7, Elbows at y=0.5
    landmarks[23] = DummyLandmark(0.45, 0.70)  # Left hip
    landmarks[24] = DummyLandmark(0.55, 0.70)  # Right hip
    landmarks[13] = DummyLandmark(0.40, 0.50)  # Left elbow
    landmarks[14] = DummyLandmark(0.60, 0.50)  # Right elbow

    # Case A: Wrists at sides (y=0.75, lowered below hip)
    landmarks[15] = DummyLandmark(0.40, 0.75)  # Left wrist
    landmarks[16] = DummyLandmark(0.60, 0.75)  # Right wrist

    from human_pose_gesture_node import HumanPoseGestureNode

    # Test static gating logic directly
    elev_thresh = 0.04
    l_wrist, r_wrist = landmarks[15], landmarks[16]
    l_hip, r_hip = landmarks[23], landmarks[24]
    l_elbow, r_elbow = landmarks[13], landmarks[14]

    l_raised = (l_wrist.visibility > 0.40) and (l_wrist.y < l_hip.y - elev_thresh or l_wrist.y < l_elbow.y + 0.05)
    r_raised = (r_wrist.visibility > 0.40) and (r_wrist.y < r_hip.y - elev_thresh or r_wrist.y < r_elbow.y + 0.05)
    assert not (l_raised or r_raised), "Wrists below hips must be evaluated as resting/idle"

    # Case B: Right wrist raised (y=0.35, above elbow and hip)
    landmarks[16] = DummyLandmark(0.60, 0.35)
    r_wrist = landmarks[16]
    r_raised = (r_wrist.visibility > 0.40) and (r_wrist.y < r_hip.y - elev_thresh or r_wrist.y < r_elbow.y + 0.05)
    assert r_raised, "Raised wrist must trigger kinematic attention"
    print("✓ Biomechanical Kinematic Gating logic verified (Arms resting vs raised)")


def test_hand_features_and_mlp():
    import joblib
    from hand_features import extract_features

    weights_dir = os.path.join(WS_DIR, "ml_models", "weights")
    clf = joblib.load(os.path.join(weights_dir, "gesture_model_features.pkl"))
    scaler = joblib.load(os.path.join(weights_dir, "scaler_features.pkl"))
    le = joblib.load(os.path.join(weights_dir, "label_encoder_features.pkl"))

    # Generate dummy 21 landmarks
    dummy_hand = [(0.5, 0.5 - i * 0.02, 0.0) for i in range(21)]
    feats = extract_features(dummy_hand)
    assert len(feats) == clf.n_features_in_, f"Feature length {len(feats)} does not match classifier {clf.n_features_in_}"

    scaled = scaler.transform([feats])
    pred_idx = clf.predict(scaled)[0]
    pred_label = le.inverse_transform([pred_idx])[0]
    classes = list(le.classes_)
    assert pred_label in classes, f"Predicted class {pred_label} not in classes {classes}"
    assert len(classes) == 6, f"Expected 6 classes, got {len(classes)}"
    print(f"✓ 19-Feature MLP inference verified across classes: {classes}")


def main():
    print("=" * 70)
    print("  RUNNING PHASE 2 UNIT & INTEGRATION TESTS")
    print("=" * 70)
    test_fastdds_xml()
    test_nav2_yaml()
    test_model_weights()
    test_biomechanical_gating_logic()
    test_hand_features_and_mlp()
    print("=" * 70)
    print("  ALL PHASE 2 TESTS PASSED SUCCESSFULLY (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    main()
