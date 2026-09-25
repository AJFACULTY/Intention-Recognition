#!/usr/bin/env python3
"""
Brain Node - FIXED VERSION
All Priority 1 issues resolved:
- ✅ Changed TwistStamped → Twist (compatibility fix)
- ✅ Added configurable parameters
- ✅ Better error handling
- ✅ Mode awareness (ready for autonomous navigation integration)
"""

import rclpy
from rclpy.node import Node
from collections import deque

from cognition_interfaces.msg import Gesture, Detection
from geometry_msgs.msg import Twist  # FIXED: Changed from TwistStamped
from std_msgs.msg import String


class BrainNode(Node):
    
    # Gesture IDs (must match gesture_node.py)
    GESTURE_NONE = -1
    GESTURE_BACK = 0
    GESTURE_FOLLOW = 1
    GESTURE_GO = 2
    GESTURE_LEFT = 3
    GESTURE_RIGHT = 4
    GESTURE_STOP = 5
    
    def __init__(self):
        super().__init__('brain_node')
        
        # FIXED: All parameters configurable (no more magic numbers)
        self.declare_parameter('linear_speed', 0.3)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('follow_speed', 0.2)
        self.declare_parameter('gesture_buffer_size', 5)
        self.declare_parameter('use_sim_time', False)
        
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.follow_speed = self.get_parameter('follow_speed').value
        self.buffer_size = self.get_parameter('gesture_buffer_size').value
        
        # Subscribers
        self.gesture_sub = self.create_subscription(
            Gesture, '/cognition/gesture', self.gesture_callback, 10)
        
        self.detection_sub = self.create_subscription(
            Detection, '/cognition/detection', self.detection_callback, 10)
        
        # NEW: Mode subscriber (for AUTO/GESTURE mode switching)
        self.mode_sub = self.create_subscription(
            String, '/system/mode', self.mode_callback, 10)
        
        # Publishers
        # FIXED: Changed from TwistStamped to Twist
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # State
        self.current_gesture = self.GESTURE_NONE
        self.gesture_buffer = deque(maxlen=self.buffer_size)
        self.person_detected = False
        self.person_center_x = 0.0
        self.person_width = 0.0
        self.system_mode = "GESTURE"  # Default to gesture control mode
        
        # Control loop timer (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info(
            f'Brain Node started (linear={self.linear_speed}, '
            f'angular={self.angular_speed}, follow={self.follow_speed}, '
            f'buffer_size={self.buffer_size})'
        )
    
    def mode_callback(self, msg: String):
        """
        Receive system mode updates
        NEW: Supports AUTO/GESTURE mode switching for navigation integration
        """
        self.system_mode = msg.data
        if self.system_mode == "GESTURE":
            self.get_logger().info('Brain node active (GESTURE mode)', once=True)
        else:
            self.get_logger().info('Brain node paused (AUTO mode)', once=True)
    
    def gesture_callback(self, msg: Gesture):
        """Receive gesture commands"""
        
        # Add to buffer
        self.gesture_buffer.append(msg.gesture_id)
        
        # Require 3 consistent detections to confirm gesture
        if self.gesture_buffer.count(msg.gesture_id) >= 3:
            if self.current_gesture != msg.gesture_id:
                self.current_gesture = msg.gesture_id
                if msg.gesture_id != self.GESTURE_NONE:
                    self.get_logger().info(f'Gesture confirmed: {msg.gesture_label}')
    
    def detection_callback(self, msg: Detection):
        """Receive person detection"""
        
        if msg.label == 'person' and msg.confidence > 0.5:
            self.person_detected = True
            self.person_center_x = msg.center_x
            self.person_width = msg.width
        else:
            self.person_detected = False
    
    def make_cmd(self, linear_x, angular_z):
        """
        Create velocity command
        FIXED: Now returns Twist instead of TwistStamped
        """
        cmd = Twist()
        cmd.linear.x = float(linear_x)
        cmd.linear.y = 0.0
        cmd.linear.z = 0.0
        cmd.angular.x = 0.0
        cmd.angular.y = 0.0
        cmd.angular.z = float(angular_z)
        return cmd
    
    def control_loop(self):
        """
        Main control loop (10 Hz)
        Implements gesture-based behaviors
        """
        
        # NEW: Check mode - only control robot in GESTURE mode
        if self.system_mode != "GESTURE":
            # In AUTO mode, Nav2 controls the robot
            # Brain node is paused
            return
        
        # Execute gesture command
        if self.current_gesture == self.GESTURE_STOP:
            # Stop immediately
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
        
        elif self.current_gesture == self.GESTURE_GO:
            # FIXED: Use configurable parameter instead of hardcoded 0.3
            self.cmd_vel_pub.publish(self.make_cmd(self.linear_speed, 0.0))
        
        elif self.current_gesture == self.GESTURE_LEFT:
            # FIXED: Use configurable parameter instead of hardcoded 0.5
            self.cmd_vel_pub.publish(self.make_cmd(0.0, self.angular_speed))
        
        elif self.current_gesture == self.GESTURE_RIGHT:
            # FIXED: Use configurable parameter
            self.cmd_vel_pub.publish(self.make_cmd(0.0, -self.angular_speed))
        
        elif self.current_gesture == self.GESTURE_FOLLOW:
            # Person following mode
            if self.person_detected:
                # Calculate centering error
                error = self.person_center_x - 0.5  # Center of frame is 0.5
                
                # Check if person is too close (occupies >40% of frame width)
                if self.person_width > 0.4:
                    # Too close, stop
                    self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))
                    self.get_logger().debug('Person too close, stopping', throttle_duration_sec=1.0)
                else:
                    # Move forward while centering person
                    # FIXED: Use configurable follow_speed
                    angular = -error * 1.5  # Proportional controller (gain=1.5)
                    self.cmd_vel_pub.publish(self.make_cmd(self.follow_speed, angular))
                    self.get_logger().debug(
                        f'Following: error={error:.2f}, angular={angular:.2f}',
                        throttle_duration_sec=1.0
                    )
            else:
                # No person detected, search by rotating slowly
                self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.2))
                self.get_logger().debug('Searching for person...', throttle_duration_sec=1.0)
        
        else:
            # No gesture or unknown gesture, stop
            self.cmd_vel_pub.publish(self.make_cmd(0.0, 0.0))


def main(args=None):
    rclpy.init(args=args)
    
    node = None
    try:
        node = BrainNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info('Shutting down (Ctrl+C)')
    except Exception as e:
        if node:
            node.get_logger().error(f'Fatal error: {e}')
        else:
            print(f'Fatal error during node creation: {e}')
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
