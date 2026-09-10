#!/usr/bin/env python3
"""
Enhanced gesture data collection with variation prompts every 100 samples.
"""
import argparse
import csv
import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import time

# Configuration
MODEL_PATH = os.path.expanduser(
    '~/cognition_ws/src/cognition_perception/cognition_perception/models/hand_landmarker.task'
)
VALID_LABELS = ['STOP', 'GO', 'LEFT', 'RIGHT', 'FOLLOW', 'BACK']
MIN_HAND_DETECTION_CONFIDENCE = 0.5
MIN_HAND_PRESENCE_CONFIDENCE  = 0.5
MIN_TRACKING_CONFIDENCE       = 0.5
MIN_HAND_SIZE = 0.08
VARIATION_INTERVAL = 100  # prompt every 100 samples

parser = argparse.ArgumentParser(description='Collect enhanced gesture dataset.')
parser.add_argument('--label', required=True, choices=VALID_LABELS)
parser.add_argument('--samples', type=int, default=1000, help='Total samples per gesture')
parser.add_argument('--output', default='gesture_dataset_enhanced.csv')
parser.add_argument('--camera', type=int, default=2)  # default to USB camera
args = parser.parse_args()

# MediaPipe setup
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=MIN_HAND_DETECTION_CONFIDENCE,
    min_hand_presence_confidence=MIN_HAND_PRESENCE_CONFIDENCE,
    min_tracking_confidence=MIN_TRACKING_CONFIDENCE
)
detector = mp_vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(args.camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cap.isOpened():
    print(f'[ERROR] Cannot open camera {args.camera}. Try --camera 0, 1, or 2.')
    exit(1)

# CSV
file_exists = os.path.isfile(args.output)
csvfile = open(args.output, 'a', newline='')
writer = csv.writer(csvfile)
if not file_exists:
    header = [f'{c}{i}' for i in range(21) for c in ('x','y','z')] + ['label']
    writer.writerow(header)
    csvfile.flush()

print(f'\n{"="*60}')
print(f'Collecting {args.samples} samples for: [{args.label}]')
print('You will be prompted every 100 samples to change conditions.')
print('Variations: distance, angle, hand side (use both hands for LEFT/RIGHT).')
print('Press Q to quit early.')
print(f'{"="*60}\n')

collected = 0
sample_since_last_prompt = 0

while collected < args.samples:
    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    display = frame.copy()
    h, w, _ = display.shape

    if result.hand_landmarks:
        landmarks = result.hand_landmarks[0]
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        hand_size = max(max(x_coords)-min(x_coords), max(y_coords)-min(y_coords))

        if hand_size < MIN_HAND_SIZE:
            cv2.putText(display, 'TOO FAR – move closer', (10,45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,165,255), 2)
        else:
            row = []
            for lm in landmarks:
                row.extend([lm.x, lm.y, lm.z])
            row.append(args.label)
            writer.writerow(row)
            csvfile.flush()
            collected += 1
            sample_since_last_prompt += 1

            # Draw skeleton
            connections = [(0,1),(1,2),(2,3),(3,4),
                           (0,5),(5,6),(6,7),(7,8),
                           (0,9),(9,10),(10,11),(11,12),
                           (0,13),(13,14),(14,15),(15,16),
                           (0,17),(17,18),(18,19),(19,20)]
            for a,b in connections:
                pt1 = (int(landmarks[a].x*w), int(landmarks[a].y*h))
                pt2 = (int(landmarks[b].x*w), int(landmarks[b].y*h))
                cv2.line(display, pt1, pt2, (0,255,0), 2)
            for lm in landmarks:
                cv2.circle(display, (int(lm.x*w), int(lm.y*h)), 5, (255,0,0), -1)

            # Progress bar
            progress = int((collected / args.samples) * (w - 20))
            cv2.rectangle(display, (10, h-30), (w-10, h-10), (50,50,50), -1)
            cv2.rectangle(display, (10, h-30), (10+progress, h-10), (0,200,0), -1)

            # Prompt to change conditions every 100 samples
            if sample_since_last_prompt >= VARIATION_INTERVAL and collected < args.samples:
                cv2.putText(display, 'CHANGE CONDITION: distance, angle, or hand side!',
                            (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                cv2.imshow('Gesture Collection', display)
                cv2.waitKey(2000)  # 2-second pause
                sample_since_last_prompt = 0

        cv2.putText(display, f'{args.label}: {collected}/{args.samples}',
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,0), 2)
    else:
        cv2.putText(display, 'NO HAND', (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,255), 2)

    cv2.imshow('Gesture Collection', display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

csvfile.close()
cap.release()
cv2.destroyAllWindows()
print(f'\n[DONE] Collected {collected} samples for [{args.label}]')
print(f'Appended to: {os.path.abspath(args.output)}')
