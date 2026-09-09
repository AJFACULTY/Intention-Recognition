#!/usr/bin/env python3
"""
collect_dataset.py
------------------
Collects hand gesture landmark data using MediaPipe and saves to CSV.
Run once per gesture label.

Usage:
    python3 collect_dataset.py --label STOP   --samples 300
    python3 collect_dataset.py --label GO     --samples 300
    python3 collect_dataset.py --label LEFT   --samples 300
    python3 collect_dataset.py --label RIGHT  --samples 300
    python3 collect_dataset.py --label FOLLOW --samples 300

Valid labels: STOP, GO, LEFT, RIGHT, FOLLOW
All runs append to the same gesture_dataset.csv file.
"""

import argparse
import csv
import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ── Configuration ─────────────────────────────────────────────────────────────

MODEL_PATH = os.path.expanduser(
    '~/cognition_ws/src/cognition_perception/cognition_perception/models/hand_landmarker.task'
)

VALID_LABELS = ['STOP', 'GO', 'LEFT', 'RIGHT', 'FOLLOW', 'BACK']

# Lowered from 0.7 to handle natural poses where back of palm faces camera
# (thumb up, index pointing down/sideways, etc.)
MIN_HAND_DETECTION_CONFIDENCE = 0.5
MIN_HAND_PRESENCE_CONFIDENCE  = 0.5
MIN_TRACKING_CONFIDENCE       = 0.5

# Match gesture_node.py hand size filter
MIN_HAND_SIZE = 0.08

# ── Argument parsing ───────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description='Collect gesture landmark dataset.')
parser.add_argument('--label',   required=True, choices=VALID_LABELS,
                    help='Gesture label to collect')
parser.add_argument('--samples', type=int, default=300,
                    help='Number of samples to collect (default: 300)')
parser.add_argument('--output',  default='gesture_dataset.csv',
                    help='Output CSV file (default: gesture_dataset.csv)')
parser.add_argument('--camera',  type=int, default=0,
                    help='Camera device index (default: 0)')
args = parser.parse_args()

# ── MediaPipe setup (identical to gesture_node.py) ────────────────────────────

if not os.path.isfile(MODEL_PATH):
    print(f'\n[ERROR] hand_landmarker.task not found at:\n  {MODEL_PATH}')
    print('Check the MODEL_PATH variable at the top of this script.')
    exit(1)

base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=MIN_HAND_DETECTION_CONFIDENCE,
    min_hand_presence_confidence=MIN_HAND_PRESENCE_CONFIDENCE,
    min_tracking_confidence=MIN_TRACKING_CONFIDENCE
)
detector = mp_vision.HandLandmarker.create_from_options(options)
print(f'[OK] MediaPipe model loaded from {MODEL_PATH}')

# ── Camera setup ──────────────────────────────────────────────────────────────

cap = cv2.VideoCapture(args.camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print(f'[ERROR] Cannot open camera {args.camera}. Try --camera 1 or --camera 2.')
    exit(1)
print(f'[OK] Camera {args.camera} opened.')

# ── CSV setup — append mode so all labels go into one file ───────────────────

file_exists = os.path.isfile(args.output)
csvfile = open(args.output, 'a', newline='')
writer  = csv.writer(csvfile)

if not file_exists:
    # Write header only once
    header = []
    for i in range(21):
        header += [f'x{i}', f'y{i}', f'z{i}']
    header.append('label')
    writer.writerow(header)
    print(f'[OK] Created new dataset file: {args.output}')
else:
    print(f'[OK] Appending to existing dataset file: {args.output}')

# ── Collection loop ───────────────────────────────────────────────────────────

collected = 0

print(f'\n{"="*55}')
print(f'  Collecting {args.samples} samples for: [{args.label}]')
print(f'{"="*55}')
print('  Tips:')
print('  - Vary distance: 0.5 m close  →  1.5 m far')
print('  - Vary height: waist / chest / head level')
print('  - Slight tilts: left, right, forward')
print('  - Green skeleton = sample captured')
print('  - Press Q to quit early')
print(f'{"="*55}\n')

while collected < args.samples:
    ret, frame = cap.read()
    if not ret:
        print('[WARN] Frame grab failed, retrying...')
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    display = frame.copy()
    h, w, _ = display.shape

    if result.hand_landmarks:
        landmarks = result.hand_landmarks[0]

        # Apply the same hand-size filter as gesture_node.py
        x_coords  = [lm.x for lm in landmarks]
        y_coords  = [lm.y for lm in landmarks]
        hand_size = max(max(x_coords) - min(x_coords),
                        max(y_coords) - min(y_coords))

        if hand_size < MIN_HAND_SIZE:
            cv2.putText(display, 'TOO FAR — move closer',
                        (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
        else:
            # Build the 63-float feature row (same order as gesture_node.py)
            row = []
            for lm in landmarks:
                row.extend([lm.x, lm.y, lm.z])
            row.append(args.label)

            writer.writerow(row)
            csvfile.flush()
            collected += 1

            # Draw skeleton (same connections as gesture_node.py)
            connections = [
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),
                (0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20)
            ]
            for a, b in connections:
                pt1 = (int(landmarks[a].x * w), int(landmarks[a].y * h))
                pt2 = (int(landmarks[b].x * w), int(landmarks[b].y * h))
                cv2.line(display, pt1, pt2, (0, 255, 0), 2)
            for lm in landmarks:
                cv2.circle(display, (int(lm.x * w), int(lm.y * h)), 5, (255, 0, 0), -1)

            # Progress bar
            progress = int((collected / args.samples) * (w - 20))
            cv2.rectangle(display, (10, h - 30), (w - 10, h - 10), (50, 50, 50), -1)
            cv2.rectangle(display, (10, h - 30), (10 + progress, h - 10), (0, 200, 0), -1)

        cv2.putText(display, f'{args.label}: {collected}/{args.samples}',
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
    else:
        cv2.putText(display, 'NO HAND DETECTED',
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 2)

    cv2.imshow('Gesture Data Collection', display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('\n[INFO] Stopped early by user.')
        break

# ── Cleanup ───────────────────────────────────────────────────────────────────

csvfile.close()
cap.release()
cv2.destroyAllWindows()

print(f'\n[DONE] Collected {collected} samples for [{args.label}]')
print(f'[DONE] Saved to: {os.path.abspath(args.output)}')

if collected < args.samples:
    print(f'[WARN] Only {collected}/{args.samples} collected. Run again to add more.')

# Quick CSV verification
with open(args.output, 'r') as f:
    total_lines = sum(1 for _ in f) - 1  # subtract header
print(f'[INFO] Total samples in dataset so far: {total_lines}')
