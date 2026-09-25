# Legacy Archived Nodes (Historical Reference)

This directory contains historical hardening snapshots created during early development and rapid bench bringup (May – September 2026).

---

## Catalog of Preserved Nodes

| Filename | Creation / Hardening Date | Purpose & Role in Evolution | Canonical Successor |
| :--- | :--- | :--- | :--- |
| `FIXED_person_detection_node.py` | May 16, 2026 | Early robust exception handling around empty frames and disconnected camera exceptions. | [`src_nodes/person_detection_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/person_detection_node.py) |
| `FIXED_brain_node.py` | September 9, 2026 | Benchmark state machine snapshot used during physical obstacle & linear navigation trials. | [`src_nodes/brain_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/brain_node.py) |
| `FIXED_gesture_node.py` | September 9, 2026 | Geometric finger state rule engine (`get_finger_states()`) used to unblock bench testing before 19-D MLP weights were fully aligned. | [`src_nodes/gesture_node.py`](file:///home/j/ros2_cognition_ws/src_nodes/gesture_node.py) |

These files are preserved here to maintain historical integrity and verify the development milestones documented in [CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md](file:///home/j/ros2_cognition_ws/project_history/technical_evolution/CHRONOLOGICAL_HISTORY_AND_CODE_EVOLUTION.md).
