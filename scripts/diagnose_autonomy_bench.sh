#!/bin/bash
# ==============================================================================
# diagnose_autonomy_bench.sh — Deep Ground-Truth Fact Collector
# Runs on Raspberry Pi host to audit container processes, logs, topic traffic,
# and hardware health across all 6 autonomy subsystems.
# ==============================================================================

echo "=================================================================="
echo "    AUTONOMY BENCH DEEP DIAGNOSTIC AUDIT (GROUND TRUTH)"
echo "    Host Timestamp: $(date)"
echo "=================================================================="
echo ""

echo "--- [1/8] DOCKER CONTAINER & PROCESS AUDIT ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""
echo "Active perception/autonomy processes inside 'yahboom_gesture':"
docker exec yahboom_gesture ps aux | grep -E 'camera_pub|person_detection|active_vision|face_recognition|gesture_node|brain_node|bench_autonomy_monitor' | grep -v grep || echo ">> NO AUTONOMY PROCESSES RUNNING!"
echo ""

echo "--- [2/8] HARDWARE, USB & THERMAL HEALTH ---"
if command -v vcgencmd >/dev/null 2>&1; then
    echo -n "Throttled State: "; vcgencmd get_throttled
    echo -n "Core Temp:       "; vcgencmd measure_temp
    echo -n "ARM Clock:       "; vcgencmd measure_clock arm
fi
echo "Host Video Nodes: $(ls -d /dev/video* 2>/dev/null | tr '\n' ' ')"
echo "Host USB Devices:"
lsusb 2>/dev/null
echo ""
echo "Recent Kernel USB / UVC Events:"
dmesg | grep -iE 'usb|uvc' | tail -n 12
echo ""

echo "--- [3/8] CAMERA PUBLISHER DIAGNOSTIC (/tmp/camera_pub.log) ---"
docker exec yahboom_gesture tail -n 20 /tmp/camera_pub.log 2>/dev/null || echo ">> No /tmp/camera_pub.log found!"
echo ""

echo "--- [4/8] PERSON DETECTION LOG (/tmp/person_detection.log) ---"
docker exec yahboom_gesture tail -n 25 /tmp/person_detection.log 2>/dev/null || echo ">> No /tmp/person_detection.log found!"
echo ""

echo "--- [5/8] ACTIVE VISION GIMBAL LOG (/tmp/active_vision.log) ---"
docker exec yahboom_gesture tail -n 25 /tmp/active_vision.log 2>/dev/null || echo ">> No /tmp/active_vision.log found!"
echo ""

echo "--- [6/8] MEDIAPIPE GESTURE LOG (/tmp/gesture.log) ---"
docker exec yahboom_gesture tail -n 20 /tmp/gesture.log 2>/dev/null || echo ">> No /tmp/gesture.log found!"
echo ""

echo "--- [7/8] BRAIN DECISION LOG (/tmp/brain.log) ---"
docker exec yahboom_gesture tail -n 20 /tmp/brain.log 2>/dev/null || echo ">> No /tmp/brain.log found!"
echo ""

echo "--- [8/8] FACIAL RECOGNITION LOG (/tmp/face_recognition.log) ---"
docker exec yahboom_gesture tail -n 15 /tmp/face_recognition.log 2>/dev/null || echo ">> No /tmp/face_recognition.log found!"
echo ""

echo "=================================================================="
echo "    DIAGNOSTIC AUDIT COMPLETE"
echo "=================================================================="
