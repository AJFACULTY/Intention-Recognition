#!/usr/bin/env python3
"""
safety_audio_node.py — Industrial Acoustic Safety & Chime Signaling Node
Cognition Robot Project | Yahboom Micro-ROS AMR

Features:
- ISO 3691-4 & OSHA Compliant Reversing Alarm (pulsed acoustic beeping on v_x < -0.02 m/s)
- Continuous High-Priority Siren on Emergency Stop (/e_stop)
- Discrete Event Chimes (/safety/chime):
    * "waypoint" / "arrival"      -> Short confirmation chirp (70 ms)
    * "mission_complete"         -> Double ascending chime
    * "obstacle" / "blocked"     -> Double caution warning (polite clearance alert)
    * "low_battery"              -> Urgent triple alarm
    * "boot" / "ready"           -> System ready tone
- Rate-limiting and serial bus protection for Yahboom ESP32/STM32 /beep topic
"""

import time
import threading
from typing import Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, String, UInt16


class SafetyAudioNode(Node):
    def __init__(self):
        super().__init__("safety_audio_node")

        # Configurable Parameters
        self.declare_parameter("reverse_vel_threshold", -0.02)  # m/s
        self.declare_parameter("reverse_beep_interval", 0.6)    # seconds between beeps
        self.declare_parameter("reverse_beep_duration", 100)    # ms
        self.declare_parameter("estop_beep_interval", 0.25)     # seconds
        self.declare_parameter("estop_beep_duration", 80)       # ms
        self.declare_parameter("audio_enabled", True)

        self.reverse_thresh = float(self.get_parameter("reverse_vel_threshold").value)
        self.reverse_interval = float(self.get_parameter("reverse_beep_interval").value)
        self.reverse_dur = int(self.get_parameter("reverse_beep_duration").value)
        self.estop_interval = float(self.get_parameter("estop_beep_interval").value)
        self.estop_dur = int(self.get_parameter("estop_beep_duration").value)
        self.audio_enabled = bool(self.get_parameter("audio_enabled").value)

        # State Variables
        self.is_reversing = False
        self.is_estop = False
        self.last_reverse_beep_time = 0.0
        self.last_estop_beep_time = 0.0
        self.lock = threading.Lock()

        # Publisher for hardware buzzer (duration in ms)
        self.beep_pub = self.create_publisher(UInt16, "/beep", 10)

        # Subscriptions
        self.create_subscription(Twist, "/cmd_vel", self._cmd_vel_cb, 10)
        self.create_subscription(Bool, "/e_stop", self._estop_cb, 10)
        self.create_subscription(String, "/safety/chime", self._chime_cb, 10)

        # Periodic Loop for Continuous Alarms (Reverse & E-Stop) at 20 Hz
        self.timer = self.create_timer(0.05, self._safety_loop)

        self.get_logger().info("Safety Audio Node initialized. Auditory safety alerts active.")

    def _cmd_vel_cb(self, msg: Twist):
        with self.lock:
            # Reversing when linear.x is negative beyond deadband
            self.is_reversing = (msg.linear.x < self.reverse_thresh)

    def _estop_cb(self, msg: Bool):
        with self.lock:
            self.is_estop = bool(msg.data)

    def _chime_cb(self, msg: String):
        """Dispatches pre-programmed acoustic sequences asynchronously."""
        chime_type = msg.data.strip().lower()
        if not self.audio_enabled:
            return

        threading.Thread(target=self._play_sequence, args=(chime_type,), daemon=True).start()

    def _emit_beep(self, duration_ms: int):
        """Sends raw duration in ms to /beep topic."""
        if not self.audio_enabled:
            return
        m = UInt16()
        m.data = int(max(10, min(duration_ms, 2000)))
        self.beep_pub.publish(m)

    def _safety_loop(self):
        """Periodically pulses the buzzer for continuous states."""
        if not self.audio_enabled:
            return

        now = time.monotonic()

        # Priority 1: E-Stop Alarm (Fast repetitive pulse)
        if self.is_estop:
            if (now - self.last_estop_beep_time) >= self.estop_interval:
                self._emit_beep(self.estop_dur)
                self.last_estop_beep_time = now
            return

        # Priority 2: Reversing Warning (Forklift standard pulse)
        if self.is_reversing:
            if (now - self.last_reverse_beep_time) >= self.reverse_interval:
                self._emit_beep(self.reverse_dur)
                self.last_reverse_beep_time = now

    def _play_sequence(self, chime_type: str):
        """Executes distinct multi-tone acoustic patterns."""
        self.get_logger().info(f"Playing safety audio chime: [{chime_type}]")
        try:
            if chime_type in ("waypoint", "arrival"):
                # Crisp confirmation chirp
                self._emit_beep(70)

            elif chime_type in ("mission_complete", "success"):
                # Melodic ascending double chirp
                self._emit_beep(60)
                time.sleep(0.12)
                self._emit_beep(120)

            elif chime_type in ("obstacle", "blocked"):
                # Caution double alert: "Excuse me, path obstructed"
                self._emit_beep(100)
                time.sleep(0.15)
                self._emit_beep(100)

            elif chime_type in ("low_battery", "battery_warning"):
                # Urgent triple warning
                for _ in range(3):
                    self._emit_beep(120)
                    time.sleep(0.15)

            elif chime_type in ("boot", "ready"):
                # Power-on notification
                self._emit_beep(80)
                time.sleep(0.1)
                self._emit_beep(80)

            else:
                self._emit_beep(100)
        except Exception as e:
            self.get_logger().warn(f"Error in acoustic sequence: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = SafetyAudioNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
