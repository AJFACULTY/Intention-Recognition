#!/usr/bin/env bash
# setup_joystick_service.sh — Installs turnkey background joystick service on Yahboom Pi 5
# Routes joystick velocity to /cmd_vel_joy for twist_mux Priority 100 arbitration.

set -euo pipefail

SERVICE_FILE="/etc/systemd/system/yahboom-joystick.service"

echo "=================================================================="
echo "    INSTALLING TURNKEY JOYSTICK SERVICE (yahboom-joystick.service)"
echo "=================================================================="

cat << 'EOF' | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Yahboom Wireless Joypad Teleoperation Service (twist_mux /cmd_vel_joy)
After=docker.service yahboom_base.service
Wants=docker.service

[Service]
Type=simple
User=pi
Restart=always
RestartSec=5
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/docker exec yahboom_base bash -c "source /opt/ros/humble/setup.bash && source /root/yahboomcar_ws/install/setup.bash && ros2 launch yahboomcar_ctrl yahboomcar_joy_launch.py --ros-args -r /cmd_vel:=/cmd_vel_joy"

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable yahboom-joystick.service
sudo systemctl restart yahboom-joystick.service || true

echo "✓ yahboom-joystick.service successfully installed and enabled."
echo "  Joystick teleoperation will now start automatically on boot"
echo "  and route directly to twist_mux (/cmd_vel_joy)."
echo "=================================================================="
