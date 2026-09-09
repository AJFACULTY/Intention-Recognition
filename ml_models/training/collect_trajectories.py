import cv2, csv, os, argparse
from ultralytics import YOLO

parser = argparse.ArgumentParser()
parser.add_argument('--sequences', type=int, default=100)
parser.add_argument('--seq_len',   type=int, default=15)
parser.add_argument('--output',    default='trajectory_dataset.csv')
parser.add_argument('--camera',    type=int, default=0)
args = parser.parse_args()

model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture(args.camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

file_exists = os.path.isfile(args.output)
csvfile = open(args.output, 'a', newline='')
writer  = csv.writer(csvfile)
if not file_exists:
    header = []
    for i in range(args.seq_len):
        header += [f'x{i}', f'y{i}']
    writer.writerow(header)
    csvfile.flush()

sequences_saved = 0
position_buffer = []

print(f'\nCollecting {args.sequences} trajectory sequences.')
print('Walk back and forth in front of the camera.')
print('Script captures automatically when a person is detected.')
print('Press Q to quit.\n')

while sequences_saved < args.sequences:
    ret, frame = cap.read()
    if not ret:
        continue

    H, W = frame.shape[:2]
    results = model(frame, classes=[0], verbose=False)

    display = frame.copy()
    person_detected = False

    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.5:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cx = (x1 + x2) / 2 / W
                cy = (y1 + y2) / 2 / H
                position_buffer.append((cx, cy))
                person_detected = True

                cv2.rectangle(display,
                    (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
                for px, py in position_buffer[-10:]:
                    cv2.circle(display,
                        (int(px*W), int(py*H)), 3, (0,165,255), -1)
                break

    if not person_detected:
        if len(position_buffer) >= args.seq_len:
            for start in range(0, len(position_buffer) - args.seq_len + 1, 3):
                seq = position_buffer[start : start + args.seq_len]
                row = []
                for (x, y) in seq:
                    row += [round(x, 5), round(y, 5)]
                writer.writerow(row)
                csvfile.flush()
                sequences_saved += 1
                if sequences_saved >= args.sequences:
                    break
            print(f'Sequences saved: {sequences_saved}/{args.sequences}')
        position_buffer = []

    cv2.putText(display,
        f'Sequences: {sequences_saved}/{args.sequences}',
        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    cv2.imshow('Trajectory Collection', display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

csvfile.close()
cap.release()
cv2.destroyAllWindows()
print(f'\nDone. {sequences_saved} sequences saved to {args.output}')
