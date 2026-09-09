# Walkthrough: Organization of `ros2_cognition_ws`

The flat directory structure of `/home/j/ros2_cognition_ws` (previously containing 60 files intermixed at the root) has been reorganized into categorized, dedicated subdirectories.

## Directory Structure

```
ros2_cognition_ws/
├── scripts/
│   ├── pipeline/               # 13 sequential mapping and Nav2 deployment scripts (1_* to 13_*)
│   └── diagnostics/            # 7 SLAM, sensor, and hardware diagnostic scripts
├── src_nodes/                  # 6 ROS 2 Python nodes (brain_node, person_detection_node, odom_imu_republisher, etc.)
├── launch/                     # 2 ROS 2 launch files (nav2.launch.py, slam_real.launch.py)
├── ml_models/
│   ├── datasets/               # 2 datasets (gesture_dataset.csv, trajectory_dataset.csv)
│   ├── weights/                # 4 model weights & configs (.pt, .pkl)
│   └── training/               # 5 training and evaluation scripts
├── maps/                       # 1 clean map artifact (room_map_20260812_0826.png)
├── docs_and_figures/           # 2 documentation and architecture diagram tools
├── logs/                       # 5 Gazebo simulation launch logs
├── archives/                   # 2 archives (cognition_ws.zip, src_10_fixes.zip)
└── chat_exports/               # 11 Claude & DeepSeek chat archives and manifests
```

## Inventory Breakdown

| Directory | Count | Key Contents |
| :--- | :--- | :--- |
| [`scripts/pipeline/`](file:///home/j/ros2_cognition_ws/scripts/pipeline/) | 13 | [1_start_mapping.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/1_start_mapping.sh) through [13_fix_install_src_drift.sh](file:///home/j/ros2_cognition_ws/scripts/pipeline/13_fix_install_src_drift.sh) |
| [`scripts/diagnostics/`](file:///home/j/ros2_cognition_ws/scripts/diagnostics/) | 7 | [full_slam_diagnostic.sh](file:///home/j/ros2_cognition_ws/scripts/diagnostics/full_slam_diagnostic.sh), [deploy_and_verify_yaw_fix.sh](file:///home/j/ros2_cognition_ws/scripts/diagnostics/deploy_and_verify_yaw_fix.sh), etc. |
| [`src_nodes/`](file:///home/j/ros2_cognition_ws/src_nodes/) | 6 | [brain_node.py](file:///home/j/ros2_cognition_ws/src_nodes/brain_node.py), [person_detection_node.py](file:///home/j/ros2_cognition_ws/src_nodes/person_detection_node.py), [odom_imu_republisher.py](file:///home/j/ros2_cognition_ws/src_nodes/odom_imu_republisher.py), `FIXED_*.py` |
| [`launch/`](file:///home/j/ros2_cognition_ws/launch/) | 2 | [nav2.launch.py](file:///home/j/ros2_cognition_ws/launch/nav2.launch.py), [slam_real.launch.py](file:///home/j/ros2_cognition_ws/launch/slam_real.launch.py) |
| [`ml_models/datasets/`](file:///home/j/ros2_cognition_ws/ml_models/datasets/) | 2 | [gesture_dataset.csv](file:///home/j/ros2_cognition_ws/ml_models/datasets/gesture_dataset.csv), [trajectory_dataset.csv](file:///home/j/ros2_cognition_ws/ml_models/datasets/trajectory_dataset.csv) |
| [`ml_models/weights/`](file:///home/j/ros2_cognition_ws/ml_models/weights/) | 4 | [gesture_model.pkl](file:///home/j/ros2_cognition_ws/ml_models/weights/gesture_model.pkl), [label_encoder.pkl](file:///home/j/ros2_cognition_ws/ml_models/weights/label_encoder.pkl), [path_predictor.pt](file:///home/j/ros2_cognition_ws/ml_models/weights/path_predictor.pt), [path_predictor_config.pkl](file:///home/j/ros2_cognition_ws/ml_models/weights/path_predictor_config.pkl) |
| [`ml_models/training/`](file:///home/j/ros2_cognition_ws/ml_models/training/) | 5 | [train_mlp.py](file:///home/j/ros2_cognition_ws/ml_models/training/train_mlp.py), [train_path_predictor.py](file:///home/j/ros2_cognition_ws/ml_models/training/train_path_predictor.py), [visualize_predictions.py](file:///home/j/ros2_cognition_ws/ml_models/training/visualize_predictions.py), etc. |
| [`maps/`](file:///home/j/ros2_cognition_ws/maps/) | 1 | [room_map_20260812_0826.png](file:///home/j/ros2_cognition_ws/maps/room_map_20260812_0826.png) |
| [`docs_and_figures/`](file:///home/j/ros2_cognition_ws/docs_and_figures/) | 2 | [gen_images.py](file:///home/j/ros2_cognition_ws/docs_and_figures/gen_images.py), [path_predictor_loss.png](file:///home/j/ros2_cognition_ws/docs_and_figures/path_predictor_loss.png) |
| [`logs/`](file:///home/j/ros2_cognition_ws/logs/) | 5 | [sim_launch_log.txt](file:///home/j/ros2_cognition_ws/logs/sim_launch_log.txt) through `sim_launch_log5.txt` |
| [`archives/`](file:///home/j/ros2_cognition_ws/archives/) | 2 | [cognition_ws.zip](file:///home/j/ros2_cognition_ws/archives/cognition_ws.zip) (1.7 GB), [src_10_fixes.zip](file:///home/j/ros2_cognition_ws/archives/src_10_fixes.zip) |
| [`chat_exports/`](file:///home/j/ros2_cognition_ws/chat_exports/) | 11 | Claude batch zips, manifests, and DeepSeek chat exports |

## Verification Results

* **Root Directory**: Clean (only the 9 category directories).
* **Total File Count**: Exactly 60 files preserved.
* **Script Permissions**: Executable permissions (`+x`) applied to all scripts in `scripts/pipeline/` and `scripts/diagnostics/`.
