#!/usr/bin/env python3
"""
record_map_video.py — Live Navigation & Mission Trajectory Video Recorder
Platform: Autonomous Mobile Robot Cognition System (ROS 2 Humble / Pi 5)
Authors: Eleana Osei Owusu & Joel Nii Adjetey Ahulu
Institution: Ghana Communication Technology University (GCTU)

Streams real-time rendered map frames from http://<ROBOT_IP>:8080/map.jpg
and compiles a high-definition H.264 MP4 video and animated GIF
documenting the robot's real-time trajectory execution on the map.
"""

import os
import sys
import time
import urllib.request
import argparse
import subprocess
import cv2
import numpy as np


def record_navigation_video(robot_ip: str, output_path: str, duration_sec: float = 60.0, fps: int = 5):
    map_url = f"http://{robot_ip}:8080/map.jpg"
    telemetry_url = f"http://{robot_ip}:8080/telemetry"
    
    print("=" * 65)
    print("    NAV2 LIVE MISSION TRAJECTORY RECORDER")
    print(f"    Source URL: {map_url}")
    print(f"    Target Duration: {duration_sec:.1f}s @ {fps} FPS")
    print(f"    Output Video: {output_path}")
    print("=" * 65)

    # Test stream connectivity
    try:
        req = urllib.request.urlopen(map_url, timeout=3.0)
        img_data = req.read()
        frame = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            print(f"[ERROR] Failed to decode initial frame from {map_url}!")
            return False
        h, w, _ = frame.shape
        print(f">> Connected successfully! Map stream resolution: {w}x{h}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to {map_url}: {e}")
        print("Please ensure web_map_visualizer is running (bash ~/sync_to_bot.sh).")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    temp_raw_avi = output_path + ".temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(temp_raw_avi, fourcc, fps, (w, h))

    frames_captured = 0
    start_time = time.time()
    last_frame_bytes = None
    frame_interval = 1.0 / fps

    print("\n[REC] Recording map trajectory stream... (Press Ctrl+C to conclude)")
    try:
        while time.time() - start_time < duration_sec:
            cycle_start = time.time()
            try:
                req = urllib.request.urlopen(map_url, timeout=1.5)
                img_data = req.read()
                frame = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    # Timestamp watermark overlay
                    elapsed = time.time() - start_time
                    time_str = f"T+{elapsed:05.1f}s | REC [{frames_captured:04d}]"
                    cv2.putText(frame, time_str, (w - 190, h - 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
                    writer.write(frame)
                    frames_captured += 1
            except Exception as e:
                pass

            elapsed = time.time() - start_time
            sys.stdout.write(f"\r  Recording... Elapsed: {elapsed:5.1f}s / {duration_sec:5.1f}s | Captured: {frames_captured:4d} frames")
            sys.stdout.flush()

            sleep_dur = frame_interval - (time.time() - cycle_start)
            if sleep_dur > 0:
                time.sleep(sleep_dur)

    except KeyboardInterrupt:
        print("\n\n[REC] Recording stopped by operator (Ctrl+C).")
    finally:
        writer.release()

    total_time = time.time() - start_time
    print(f"\n>> Captured {frames_captured} frames in {total_time:.1f}s ({frames_captured/max(0.1, total_time):.1f} effective FPS)")

    if frames_captured == 0:
        print("[ERROR] No frames were captured.")
        if os.path.exists(temp_raw_avi):
            os.remove(temp_raw_avi)
        return False

    # Convert to browser-compatible H.264 MP4 via ffmpeg
    print(f">> Encoding to H.264 MP4: {output_path}...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", temp_raw_avi,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "22",
        output_path
    ]
    res = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if os.path.exists(temp_raw_avi):
        os.remove(temp_raw_avi)

    if res.returncode == 0 and os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024.0
        print(f"✓ Video successfully generated: {output_path} ({size_kb:.1f} KB)")
        
        # Also create a lightweight animated GIF version
        gif_path = os.path.splitext(output_path)[0] + ".gif"
        print(f">> Generating animated GIF preview: {gif_path}...")
        gif_cmd = [
            "ffmpeg", "-y", "-i", output_path,
            "-vf", "fps=4,scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            gif_path
        ]
        subprocess.run(gif_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(gif_path):
            print(f"✓ GIF preview generated: {gif_path} ({os.path.getsize(gif_path)/1024.0:.1f} KB)")

        return True
    else:
        print(f"[ERROR] ffmpeg encoding failed: {res.stderr.decode('utf-8', errors='ignore')}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Record live Nav2 navigation video from web_map_visualizer")
    parser.add_argument('--ip', type=str, default="10.27.122.136", help="Robot IP address (default: 10.27.122.136)")
    parser.add_argument('--duration', type=float, default=60.0, help="Recording duration in seconds (default: 60.0)")
    parser.add_argument('--fps', type=int, default=5, help="Frame rate (default: 5)")
    parser.add_argument('--out', type=str, default="project_history/robot_audits/nav2_mission_recording.mp4",
                        help="Output MP4 file path")
    args = parser.parse_args()

    record_navigation_video(
        robot_ip=args.ip,
        output_path=args.out,
        duration_sec=args.duration,
        fps=args.fps
    )


if __name__ == '__main__':
    main()
