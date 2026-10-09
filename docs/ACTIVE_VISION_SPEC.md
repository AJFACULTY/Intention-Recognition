# ACTIVE VISION GIMBAL & FACIAL RECOGNITION TECHNICAL SPECIFICATION
**Dynamic Field of View (FOV) Adaptation, 2-DOF Pan/Tilt Servoing, Active Search State Machine & ArcFace Identity Verification**
**Platform:** Mobile Robot (Raspberry Pi 5) | **Subsystem:** Active Vision & Biometric Cognition

---

## 1. Problem Statement & Operational Rationale

In conventional mobile robot setups, the onboard camera is rigidly mounted to the chassis at a fixed tilt angle. This static Field of View (FOV) creates severe operational blind spots in human-robot interaction (HRI):
1. **Vertical Elevation Blind Spot (Standing vs. Seated):** The robot chassis height is ~15 cm. A human operator standing 1–2 meters away has their face elevated at 1.5–1.8 m, well above the camera's upper vertical FOV limit.
2. **Gesture Blind Spot (Hands Outside Frame):** When an operator raises their hand to signal a "Stop" or "Turn" command, the hand frequently exits the top or side margins of the camera frame.
3. **Lateral Movement Blind Spot:** If the operator walks around the robot, a fixed camera loses track unless the entire robot rotates its chassis, consuming excessive battery power and inducing wheel slippage.

### The Solution: Active Dynamic FOV Adaptation
By leveraging the Yahboom car's integrated **2-DOF camera gimbal** (pan on horizontal servo `S1`, tilt on vertical servo `S2`), the robot dynamically re-centers the operator's face or gesturing hand in the frame. When the target exits the frame entirely, an **Active FOV Recovery Search** routine sweeps the environment to re-acquire the operator without needing to move the wheels.

---

## 2. Hardware Actuation & Servo Kinematics

```
                  [ USB RGB Camera ]
                          ▲
                          │ Tilt (Pitch) Axis: 0° - 180°
                          ▼ [ Servo S2: Tilt ]
                          │
                   [ Pan (Yaw) Axis ] ◄──► [ Servo S1: Pan: 0° - 180° ]
                          │
                [ Robot Front Chassis ]
```

### Table 2.1: Servo Actuator Parameters (Empirically Calibrated 0-Centric Protocol)

| Servo Channel | ROS 2 Topic | Message Type | Angle Range | Neutral / Default | Directionality |
|---|---|---|:---:|:---:|---|
| **Horizontal (Pan)** | `/servo_s1` | `std_msgs/msg/Int32` | $-60^\circ \le \theta \le +60^\circ$ | **$0^\circ$** (Straight Forward) | Negative ($<0^\circ$): Turn Left<br>Positive ($>0^\circ$): Turn Right |
| **Vertical (Tilt)** | `/servo_s2` | `std_msgs/msg/Int32` | $-15^\circ \le \phi \le +48^\circ$ | **$+30^\circ$** (Forward Level + Slight Elevation) | Decreasing ($<30^\circ$): Tilt Down<br>Increasing ($>30^\circ$): Tilt Up |

*Hardware Controller:* Servos are driven by dedicated PWM timer channels on the Yahboom STM32 baseboard, communicating with the Raspberry Pi 5 via micro-ROS UART serial (`/dev/ttyACM0`) on FastDDS `ROS_DOMAIN_ID=20`. The firmware protocol is centered at $0^\circ$ for pan, with $+25^\circ \dots +30^\circ$ corresponding to horizontal eye-level framing. Continuous $16^\circ/\text{s}$ slew-rate limiting eliminates sudden current inrush spikes and mechanical snapping.

---

## 3. Closed-Loop PID Visual Servoing (Target Centering)

When a face or hand is detected within the camera frame ($W \times H = 640 \times 480$), the tracking algorithm calculates the pixel error vector between the target bounding box centroid $(x_{t}, y_{t})$ and the optical center $(x_{c}, y_{c}) = (W/2, H/2)$:

$$\Delta x = x_{t} - \frac{W}{2}, \quad \Delta y = y_{t} - \frac{H}{2}$$

### Error Normalization:
$$e_x = \frac{\Delta x}{W/2} \in [-1.0, 1.0], \quad e_y = \frac{\Delta y}{H/2} \in [-1.0, 1.0]$$

### Proportional-Derivative (PD) Servo Update Equations:
To ensure smooth camera tracking without high-frequency oscillation or mechanical servo jitter:

$$\theta_{\text{pan}}(t) = \theta_{\text{pan}}(t-1) - \left( K_{p,x} \cdot e_x(t) + K_{d,x} \cdot \frac{e_x(t) - e_x(t-1)}{\Delta t} \right)$$

$$\phi_{\text{tilt}}(t) = \phi_{\text{tilt}}(t-1) + \left( K_{p,y} \cdot e_y(t) + K_{d,y} \cdot \frac{e_y(t) - e_y(t-1)}{\Delta t} \right)$$

### Deadband Threshold:
To protect servo gear trains from micro-wear, updates are suppressed if the centroid lies within a deadband margin:
$$\text{If } |e_x| < 0.08 \text{ and } |e_y| < 0.08 \implies \text{No servo motion (Error = 0)}$$

### Tuned Gain Parameters:
- $K_{p,x} = 6.0^\circ$, $K_{d,x} = 1.2^\circ$
- $K_{p,y} = 5.0^\circ$, $K_{d,y} = 1.0^\circ$
- Maximum slew rate limit: $15^\circ$ per second (prevents abrupt video blurring).

---

## 4. Multi-Target Dynamic Priority Arbitration

The camera must track both **faces** (for identification) and **hands** (for gesture recognition). The active vision controller implements a dynamic focus arbitrator:

```
                  ┌───────────────────────────────┐
                  │ Target Detection State Stream │
                  └───────────────┬───────────────┘
                                  │
                 Is Hand Detected in Gesture Pose?
                                  │
                 ┌────────────────┴────────────────┐
                 │ YES                             │ NO
                 ▼                                 ▼
      [ Priority 1: Hand FOV ]          Is Face Detected in Frame?
      Target Centroid = Hand BBox                  │
      Tilt down slightly to capture       ┌────────┴────────┐
      wrist & finger landmarks            │ YES             │ NO
                                          ▼                 ▼
                               [ Priority 2: Face FOV ]  [ Priority 3: FOV Lost ]
                               Target Centroid = Face    Trigger Active Search
                               Tilt up to keep face      State Machine
                               in upper third of image
```

---

## 5. Active FOV Search & Recovery State Machine

When an operator steps outside the camera's visual cone, the tracking node transitions into the **Active FOV Recovery State Machine**:

```
      ┌────────────────────────┐
      │   STATE 1: TRACKING    │◄─────────────────────────────┐
      └───────────┬────────────┘                              │
                  │ Target Lost (Frames > 3)                  │
                  ▼                                           │
      ┌────────────────────────┐                              │
      │  STATE 2: MEMORY HOLD  │                              │
      │ (Maintain last heading │                              │
      │  for 1.5 seconds)      │                              │
      └───────────┬────────────┘                              │
                  │ Timeout Exceeded                          │ Target Re-acquired
                  ▼                                           │
      ┌────────────────────────┐                              │
      │  STATE 3: LOCAL SCAN   │                              │
      │ (Sweep ±25° pan around │──────────────────────────────┤
      │  last known position)  │                              │
      └───────────┬────────────┘                              │
                  │ 2 Cycles Complete                         │
                  ▼                                           │
      ┌────────────────────────┐                              │
      │ STATE 4: WIDE SWEEP    │                              │
      │ (Pan 45° to 135°,      │──────────────────────────────┤
      │  Tilt: 60°, 90°, 120°) │                              │
      └───────────┬────────────┘                              │
                  │ Full Sweep Complete                       │
                  ▼                                           │
      ┌────────────────────────┐                              │
      │ STATE 5: BODY ROTATION │                              │
      │ (Command chassis       │──────────────────────────────┘
      │  /cmd_vel rotation)    │
      └────────────────────────┘
```

### State Definitions:
1. **TRACKING:** Target detected. Closed-loop PD servoing centers the target.
2. **TASK_FORWARD:** Operator commands "GO" (`gesture_id == 2`). The controller overrides person tracking and smoothly returns the gimbal to the forward-facing task pose ($\theta_{\text{pan}} = 90^\circ, \phi_{\text{tilt}} = 100^\circ$), looking ahead along the path of travel.
3. **MEMORY HOLD:** Target temporarily occluded. The gimbal holds its last commanded angles for 1.5 seconds, avoiding erratic swings if a hand briefly drops.
4. **LOCAL SCAN:** Oscillates pan servo $\pm 25^\circ$ around the last known azimuth at $30^\circ/\text{s}$. Recovers ~80% of lost targets.
5. **WIDE SWEEP:** Systematically sweeps azimuth from $45^\circ$ to $135^\circ$ across three elevation planes ($\phi = 70^\circ$ [seated], $90^\circ$ [level], $120^\circ$ [standing]).
6. **BODY ROTATION:** If the gimbal reaches its hardware travel limits ($0^\circ$ or $180^\circ$) without re-acquiring the operator, the node commands a slow body rotation via `/cmd_vel` ($\omega_z = 0.3 \text{ rad/s}$) to turn the robot chassis toward the operator.

---

## 6. Biometric Facial Recognition Subsystem (InsightFace ArcFace)

To prevent unauthorized bystanders from commanding the robot via gestures, a facial recognition pipeline is integrated into the decision loop.

### 6.1. Architecture & Model Pack
- **Library:** InsightFace (`insightface==0.7.3`, ONNX Runtime execution provider).
- **Model Pack:** **`buffalo_sc`** (Lightweight mobile-optimized pack, ~16 MB total weight):
  - *Detector:* **RetinaFace-500MF** (detects faces, facial bounding box, 5 key landmarks: eyes, nose, mouth corners). Input resolution: $320 \times 320$.
  - *Recognizer:* **MobileFaceNet (MBF@WebFace600K)** (generates a compact **512-dimensional normalized embedding vector** $\mathbf{v} \in \mathbb{R}^{512}$).

### 6.2. Identity Database & Enrollment Pipeline
- Implemented in `src_nodes/face_recognition_node.py`.
- An operator enrolls by looking at the camera for 3 seconds. The enrollment script extracts 10 clean embeddings, calculates the mean identity centroid $\mathbf{\mu}_i$, and stores it in `face_data/faces_db.pkl`:

$$\mathbf{\mu}_i = \frac{1}{N} \sum_{k=1}^N \mathbf{v}_k, \quad \mathbf{\hat{\mu}}_i = \frac{\mathbf{\mu}_i}{\|\mathbf{\mu}_i\|_2}$$

### 6.3. Real-Time Verification & Cosine Matching
For an observed face with embedding $\mathbf{v}_{\text{obs}}$, cosine similarity against enrolled identities is computed:

$$S(\mathbf{v}_{\text{obs}}, \mathbf{\hat{\mu}}_i) = \mathbf{v}_{\text{obs}} \cdot \mathbf{\hat{\mu}}_i = \cos(\alpha)$$

- **Decision Boundary:**
  - If $S \ge 0.45$: Identified as authorized operator $i$. Identity published on `/cognition/face_identity`.
  - If $S < 0.45$: Classified as `"Unknown / Unauthorized"`. Gesture commands are rejected.

---

## 7. ROS 2 Node Architecture: `active_vision_node.py`

Below is the design specification for the unified active tracking and face recognition ROS 2 node:

```python
#!/usr/bin/env python3
"""
active_vision_node.py -- Unified Pan/Tilt Gimbal Tracking & Face ID Node
Subscriptions:
  /camera/image_raw/compressed (sensor_msgs/CompressedImage)
  /cognition/detection         (cognition_interfaces/Detection)
Publications:
  /servo_s1                    (std_msgs/Int32 - Pan angle)
  /servo_s2                    (std_msgs/Int32 - Tilt angle)
  /cognition/face_identity     (std_msgs/String - Operator name)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Int32, String
from cv_bridge import CvBridge
import cv2
import numpy as np

class ActiveVisionNode(Node):
    def __init__(self):
        super().__init__('active_vision_node')
        
        # Publishers for 2-DOF Gimbal
        self.pub_pan = self.create_publisher(Int32, 'servo_s1', 10)
        self.pub_tilt = self.create_publisher(Int32, 'servo_s2', 10)
        self.pub_identity = self.create_publisher(String, '/cognition/face_identity', 10)
        
        # Subscribers
        self.sub_cam = self.create_subscription(
            CompressedImage, '/camera/image_raw/compressed', self.camera_callback, 1)
            
        # State variables
        self.pan_angle = 90
        self.tilt_angle = 90
        self.state = "TRACKING" # TRACKING, HOLD, LOCAL_SCAN, WIDE_SWEEP
        self.frames_since_detect = 0
        
        # Controller gains
        self.kp_x = 6.0
        self.kp_y = 5.0
        
    def execute_pd_centering(self, norm_err_x, norm_err_y):
        if abs(norm_err_x) > 0.08:
            self.pan_angle = int(np.clip(self.pan_angle - self.kp_x * norm_err_x, 10, 170))
            self.pub_pan.publish(Int32(data=self.pan_angle))
            
        if abs(norm_err_y) > 0.08:
            self.tilt_angle = int(np.clip(self.tilt_angle + self.kp_y * norm_err_y, 45, 140))
            self.pub_tilt.publish(Int32(data=self.tilt_angle))
```

---

## 8. Integration with the Executive Brain

In `src_nodes/brain_node.py`, the robot's high-level state machine incorporates the active vision system:
1. **Idle State:** Gimbal performs periodic slow sweeps (`WIDE_SWEEP`) searching for an operator.
2. **Operator Detected:** When a face is spotted, gimbal centers the face. `face_recognition_node` verifies authorization.
3. **Authorization Confirmed:** Robot beeps twice (`/beep`), enters `ATTENTIVE` state, and adjusts tilt downward toward the operator's chest/hand height to anticipate gesture commands.
4. **Gesture Command Executed:** When a gesture is verified (e.g. "Forward"), the robot dispatches a Nav2 goal, centers the path forward, and periodically checks back to verify the operator is still following.
