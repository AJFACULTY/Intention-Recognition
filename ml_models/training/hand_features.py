#!/usr/bin/env python3
"""
Hand‑agnostic feature extraction from 21 MediaPipe landmarks.
Includes thumb‑specific and relative features for better gesture disambiguation.
"""
import numpy as np

WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

FINGER_JOINTS = [
    (THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP),
    (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
]

def angle_between(v1, v2):
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)
    v2 = v2 / (np.linalg.norm(v2) + 1e-8)
    dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
    return np.degrees(np.arccos(dot))

def extract_features(landmarks):
    lm = np.array(landmarks)  # (21, 3)

    # 1. Curl angles (5)
    curls = []
    for mcp, pip, dip, tip in FINGER_JOINTS:
        v1 = lm[pip] - lm[mcp]
        v2 = lm[tip] - lm[pip]
        curls.append(angle_between(v1, v2))

    # 2. Spread angles between adjacent fingertips (3)
    spreads = []
    for i in range(3):
        tip1 = lm[FINGER_JOINTS[i][-1]]
        tip2 = lm[FINGER_JOINTS[i+1][-1]]
        v1 = tip1 - lm[WRIST]
        v2 = tip2 - lm[WRIST]
        spreads.append(angle_between(v1, v2))

    # 3. Normalized distances from wrist to fingertips (5)
    palm_width = np.linalg.norm(lm[INDEX_MCP] - lm[PINKY_MCP]) + 1e-8
    dists = []
    for mcp, pip, dip, tip in FINGER_JOINTS:
        d = np.linalg.norm(lm[tip] - lm[WRIST]) / palm_width
        dists.append(d)

    # 4. Palm orientation (angle of wrist->middle MCP relative to vertical)
    palm_vec = lm[MIDDLE_MCP] - lm[WRIST]
    vertical = np.array([0, 1, 0])
    palm_angle = angle_between(palm_vec, vertical)

    # 5. Index finger direction angle (in image plane)
    index_vec = lm[INDEX_TIP] - lm[INDEX_MCP]
    index_angle = np.degrees(np.arctan2(index_vec[1], index_vec[0]))

    # 6. Thumb direction angle (wrist to thumb tip)
    thumb_vec = lm[THUMB_TIP] - lm[WRIST]
    thumb_angle = np.degrees(np.arctan2(thumb_vec[1], thumb_vec[0]))

    # 7. Angle between index and thumb vectors (from wrist)
    index_thumb_angle = angle_between(
        lm[INDEX_TIP] - lm[WRIST],
        lm[THUMB_TIP] - lm[WRIST]
    )

    # 8. Normalized distance between thumb tip and index tip
    tip_dist = np.linalg.norm(lm[THUMB_TIP] - lm[INDEX_TIP]) / palm_width

    # 9. Thumb tip relative height (z) to distinguish up/down
    thumb_height = lm[THUMB_TIP][2] - lm[WRIST][2]  # z is depth

    # Combine all features
    features = np.concatenate([
        curls, spreads, dists,
        [palm_angle, index_angle, thumb_angle, index_thumb_angle, tip_dist, thumb_height]
    ])
    return features

def extract_features_from_row(row):
    landmarks = [(row[i], row[i+1], row[i+2]) for i in range(0, 63, 3)]
    return extract_features(landmarks)
