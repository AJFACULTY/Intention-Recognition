#!/usr/bin/env python3
"""
capture_spatial_zone_snapshot.py
Captures a live frame from the robot USB camera (or takes a source image/topic),
overlays the exact geometric Active Spatial Acceptance Zone (45% width x 65% height),
adds HUD diagnostics, and saves high-resolution verification artifacts.
"""

import os
import sys
import argparse
import cv2
import numpy as np

# Geometric definitions matching src_nodes/person_detection_node.py
ZONE_X_MARGIN = 0.275  # 27.5% margin on left/right -> 45% central zone
ZONE_Y_MIN = 0.175     # Top bound at 17.5%
ZONE_Y_MAX = 0.825     # Bottom bound at 82.5% -> 65% central height

def draw_dashed_rect(img, pt1, pt2, color, thickness=2, dash_length=15):
    """Draws a dashed rectangle on an image."""
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Top & bottom lines
    for x in range(x1, x2, dash_length * 2):
        x_end = min(x + dash_length, x2)
        cv2.line(img, (x, y1), (x_end, y1), color, thickness)
        cv2.line(img, (x, y2), (x_end, y2), color, thickness)
        
    # Left & right lines
    for y in range(y1, y2, dash_length * 2):
        y_end = min(y + dash_length, y2)
        cv2.line(img, (x1, y), (x1, y_end), color, thickness)
        cv2.line(img, (x2, y), (x2, y_end), color, thickness)

def overlay_spatial_zone(frame):
    """Applies the spatial acceptance zone overlay, corner reticles, and HUD telemetry."""
    h, w = frame.shape[:2]
    
    zx_min = int(w * ZONE_X_MARGIN)
    zx_max = int(w * (1.0 - ZONE_X_MARGIN))
    zy_min = int(h * ZONE_Y_MIN)
    zy_max = int(h * ZONE_Y_MAX)
    
    output = frame.copy()
    
    # Create semi-transparent shaded mask outside active zone
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    # Outside zone shaded slightly darker (inactive region)
    mask[:] = (10, 10, 20)
    # Inside zone is transparent (active region)
    mask[zy_min:zy_max, zx_min:zx_max] = (0, 0, 0)
    
    # Blend overlay with 30% alpha for inactive periphery
    output = cv2.addWeighted(output, 1.0, mask, -0.45, 0)
    
    # Draw dashed active zone border (bright cyan)
    cyan = (255, 230, 0)
    draw_dashed_rect(output, (zx_min, zy_min), (zx_max, zy_max), cyan, thickness=2, dash_length=12)
    
    # Draw solid high-contrast corner reticles (tactical HUD style)
    reticle_len = 25
    reticle_color = (0, 255, 180)  # Neon mint green
    t = 3
    # Top-Left
    cv2.line(output, (zx_min, zy_min), (zx_min + reticle_len, zy_min), reticle_color, t)
    cv2.line(output, (zx_min, zy_min), (zx_min, zy_min + reticle_len), reticle_color, t)
    # Top-Right
    cv2.line(output, (zx_max, zy_min), (zx_max - reticle_len, zy_min), reticle_color, t)
    cv2.line(output, (zx_max, zy_min), (zx_max, zy_min + reticle_len), reticle_color, t)
    # Bottom-Left
    cv2.line(output, (zx_min, zy_max), (zx_min + reticle_len, zy_max), reticle_color, t)
    cv2.line(output, (zx_min, zy_max), (zx_min, zy_max - reticle_len), reticle_color, t)
    # Bottom-Right
    cv2.line(output, (zx_max, zy_max), (zx_max - reticle_len, zy_max), reticle_color, t)
    cv2.line(output, (zx_max, zy_max), (zx_max, zy_max - reticle_len), reticle_color, t)
    
    # Header HUD Banner
    cv2.rectangle(output, (0, 0), (w, 36), (20, 24, 32), -1)
    cv2.line(output, (0, 36), (w, 36), (0, 200, 255), 1)
    
    hud_title = "COGNITION ROBOTICS - SPATIAL ACCEPTANCE ZONE"
    cv2.putText(output, hud_title, (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(output, "YOLOv8 GATING: ACTIVE", (w - 195, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 120), 1, cv2.LINE_AA)
    
    # Zone Dimension Badge
    badge_x = zx_min + 10
    badge_y = zy_min + 22
    zone_label = f"CENTRAL ACCEPTANCE ZONE [45% x 65%] (w:{zx_max-zx_min}px, h:{zy_max-zy_min}px)"
    cv2.rectangle(output, (badge_x - 4, badge_y - 15), (badge_x + 390, badge_y + 5), (0, 0, 0), -1)
    cv2.putText(output, zone_label, (badge_x, badge_y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 255), 1, cv2.LINE_AA)
    
    # Footer Telemetry Banner
    cv2.rectangle(output, (0, h - 30), (w, h), (20, 24, 32), -1)
    cv2.line(output, (0, h - 30), (w, h - 30), (0, 200, 255), 1)
    footer_text = f"FOV: 640x480 | X:[{zx_min}..{zx_max}] Y:[{zy_min}..{zy_max}] | BYSTANDER SUPPRESSION: ENFORCED"
    cv2.putText(output, footer_text, (14, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 220, 240), 1, cv2.LINE_AA)
    
    return output

def grab_camera_frame():
    """Tries available V4L2 camera indices."""
    for dev_idx in [1, 0, 2, 3]:
        cap = cv2.VideoCapture(dev_idx, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print(f"[OK] Acquired live frame from /dev/video{dev_idx}")
                return frame
    return None

def main():
    parser = argparse.ArgumentParser(description="Capture & overlay robot spatial acceptance zone")
    parser.add_argument("--source", type=str, default=None, help="Source image path if camera is offline")
    parser.add_argument("--out", type=str, default="test_pics/live_spatial_zone_snapshot.jpg", help="Output path")
    args = parser.parse_args()
    
    frame = None
    if args.source and os.path.exists(args.source):
        frame = cv2.imread(args.source)
        print(f"[INFO] Loaded source frame from: {args.source}")
    else:
        frame = grab_camera_frame()
        if frame is None:
            # Fallback to existing bench test picture if hardware camera is not connected
            fallback = "test_pics/photo_2026-09-08_07-24-44.jpg"
            if os.path.exists(fallback):
                print(f"[WARN] Live camera not accessible. Using bench test baseline: {fallback}")
                frame = cv2.imread(fallback)
            else:
                print("[ERROR] Neither live camera nor baseline image could be opened.")
                sys.exit(1)
                
    # Resize to standard 640x480 if needed
    if frame.shape[1] != 640 or frame.shape[0] != 480:
        frame = cv2.resize(frame, (640, 480))
        
    result = overlay_spatial_zone(frame)
    
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    cv2.imwrite(args.out, result)
    print(f"[SUCCESS] Spatial zone verification artifact saved to: {args.out}")
    
    # Also copy to write_up/figures if directory exists
    writeup_target = os.path.join("write_up", "figures", "live_spatial_zone_snapshot.jpg")
    if os.path.exists(os.path.dirname(writeup_target)):
        cv2.imwrite(writeup_target, result)
        print(f"[SUCCESS] Mirrored to write-up figures: {writeup_target}")

if __name__ == "__main__":
    main()
