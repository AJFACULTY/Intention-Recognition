import cairosvg
from PIL import Image, ImageDraw
import os

# Create figures directory
os.makedirs(os.path.expanduser("~/figs"), exist_ok=True)

# System Architecture diagram
svg_arch = '''<svg width="780" height="520" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#333"/>
    </marker>
  </defs>
  <rect width="780" height="520" fill="white"/>
  <text x="390" y="28" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle" fill="#111">Figure 3.1: System Architecture of the Intention-Aware Autonomous Robot</text>

  <!-- SENSORS BOX -->
  <rect x="20" y="55" width="160" height="110" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.5"/>
  <text x="100" y="75" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#185FA5">SENSORS</text>
  <rect x="35" y="84" width="130" height="32" rx="4" fill="#D0E8F7" stroke="#4A90D9" stroke-width="1"/>
  <text x="100" y="105" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">USB Camera</text>
  <rect x="35" y="123" width="130" height="32" rx="4" fill="#D0E8F7" stroke="#4A90D9" stroke-width="1"/>
  <text x="100" y="144" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">LiDAR Sensor</text>

  <!-- PERCEPTION LAYER -->
  <rect x="240" y="50" width="200" height="230" rx="6" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1.5"/>
  <text x="340" y="72" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#0F6E56">PERCEPTION LAYER (ROS2)</text>
  <text x="340" y="86" font-family="Arial" font-size="9" text-anchor="middle" fill="#555">Raspberry Pi 5</text>
  <rect x="255" y="95" width="170" height="50" rx="4" fill="#C6EDDA" stroke="#2EAB6A" stroke-width="1"/>
  <text x="340" y="116" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#0F6E56">gesture_node</text>
  <text x="340" y="131" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">MediaPipe Hands TFLite</text>
  <text x="340" y="143" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Geometric Feature Classifier</text>

  <rect x="255" y="160" width="170" height="50" rx="4" fill="#C6EDDA" stroke="#2EAB6A" stroke-width="1"/>
  <text x="340" y="181" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#0F6E56">person_detection_node</text>
  <text x="340" y="196" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">YOLOv8n Deep Learning</text>
  <text x="340" y="208" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Kinematic Motion Estimator</text>

  <rect x="255" y="225" width="170" height="45" rx="4" fill="#C6EDDA" stroke="#2EAB6A" stroke-width="1"/>
  <text x="340" y="246" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#0F6E56">scan_republisher_node</text>
  <text x="340" y="261" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">LiDAR data relay / filter</text>

  <!-- DECISION + NAV -->
  <rect x="500" y="50" width="185" height="160" rx="6" fill="#FEF9EC" stroke="#E8A020" stroke-width="1.5"/>
  <text x="592" y="72" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#854F0B">COGNITION LAYER</text>
  <rect x="515" y="82" width="155" height="50" rx="4" fill="#FAE4A6" stroke="#E8A020" stroke-width="1"/>
  <text x="592" y="103" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#854F0B">brain_node</text>
  <text x="592" y="118" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Priority-Based Fusion</text>
  <text x="592" y="130" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Intent → Velocity Command</text>

  <rect x="515" y="145" width="155" height="55" rx="4" fill="#FAE4A6" stroke="#E8A020" stroke-width="1"/>
  <text x="592" y="163" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#854F0B">Nav2 + SLAM Toolbox</text>
  <text x="592" y="177" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Autonomous Navigation</text>
  <text x="592" y="190" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Occupancy Map / Localisation</text>

  <!-- ACTUATION -->
  <rect x="500" y="230" width="185" height="120" rx="6" fill="#FDF0F0" stroke="#C94040" stroke-width="1.5"/>
  <text x="592" y="252" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#A32D2D">ACTUATION LAYER</text>
  <rect x="515" y="261" width="155" height="35" rx="4" fill="#F5C6C6" stroke="#C94040" stroke-width="1"/>
  <text x="592" y="279" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#A32D2D">ESP32 (micro-ROS)</text>
  <text x="592" y="291" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">UART bridge / PI velocity ctrl</text>
  <rect x="515" y="305" width="155" height="35" rx="4" fill="#F5C6C6" stroke="#C94040" stroke-width="1"/>
  <text x="592" y="324" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#A32D2D">L298N + DC Motors</text>
  <text x="592" y="336" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Differential drive platform</text>

  <!-- ARROWS: Camera → gesture_node -->
  <line x1="180" y1="100" x2="238" y2="115" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <line x1="180" y1="110" x2="238" y2="178" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <line x1="180" y1="150" x2="238" y2="242" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <line x1="440" y1="118" x2="498" y2="105" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="465" y="110" font-family="Arial" font-size="8" fill="#555">/cognition/gesture</text>
  <line x1="440" y1="182" x2="498" y2="120" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="445" y="163" font-family="Arial" font-size="8" fill="#555">/cognition/detection</text>
  <line x1="440" y1="247" x2="498" y2="190" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="435" y="230" font-family="Arial" font-size="8" fill="#555">/scan</text>

  <line x1="592" y1="210" x2="592" y2="258" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="596" y="238" font-family="Arial" font-size="8" fill="#555">/cmd_vel</text>
  <line x1="575" y1="210" x2="565" y2="258" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <line x1="592" y1="296" x2="592" y2="303" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <text x="390" y="475" font-family="Arial" font-size="10" text-anchor="middle" fill="#444">
    All inter-node communication uses ROS2 DDS publish-subscribe middleware on Raspberry Pi 5
  </text>
  <text x="390" y="493" font-family="Arial" font-size="10" text-anchor="middle" fill="#444">
    ESP32 interfaces via micro-ROS UART serial transport at 921600 baud
  </text>

  <rect x="30" y="430" width="12" height="12" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1"/>
  <text x="48" y="441" font-family="Arial" font-size="10" fill="#333">Sensing</text>
  <rect x="100" y="430" width="12" height="12" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1"/>
  <text x="118" y="441" font-family="Arial" font-size="10" fill="#333">Perception</text>
  <rect x="185" y="430" width="12" height="12" fill="#FEF9EC" stroke="#E8A020" stroke-width="1"/>
  <text x="203" y="441" font-family="Arial" font-size="10" fill="#333">Cognition</text>
  <rect x="268" y="430" width="12" height="12" fill="#FDF0F0" stroke="#C94040" stroke-width="1"/>
  <text x="286" y="441" font-family="Arial" font-size="10" fill="#333">Actuation</text>
</svg>'''

cairosvg.svg2png(bytestring=svg_arch.encode(), write_to=os.path.expanduser("~/figs/fig_arch.png"), output_width=780, output_height=520)
print("Architecture PNG done")

# Operational Workflow Flowchart
svg_flow = '''<svg width="680" height="780" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#333"/>
    </marker>
  </defs>
  <rect width="680" height="780" fill="white"/>
  <text x="340" y="25" font-family="Arial" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">Figure 3.2: Operational Workflow of the Intention-Aware Robot</text>

  <ellipse cx="340" cy="55" rx="75" ry="22" fill="#C6EDDA" stroke="#0F6E56" stroke-width="1.5"/>
  <text x="340" y="60" font-family="Arial" font-size="11" text-anchor="middle" fill="#0F6E56">SYSTEM START</text>
  <line x1="340" y1="77" x2="340" y2="97" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="240" y="97" width="200" height="38" rx="5" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <text x="340" y="116" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">Launch ROS2 nodes, SLAM,</text>
  <text x="340" y="128" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">Nav2, micro-ROS agent</text>
  <line x1="340" y1="135" x2="340" y2="155" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="220" y="155" width="240" height="36" rx="5" fill="#FEF9EC" stroke="#E8A020" stroke-width="1.3"/>
  <text x="340" y="173" font-family="Arial" font-size="10" text-anchor="middle" fill="#854F0B">Robot navigates autonomously</text>
  <text x="340" y="185" font-family="Arial" font-size="10" text-anchor="middle" fill="#854F0B">(Nav2 + m-explore-ros2)</text>
  <line x1="340" y1="191" x2="340" y2="211" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="230" y="211" width="220" height="34" rx="5" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <text x="340" y="231" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">Acquire camera frame</text>
  <text x="340" y="243" font-family="Arial" font-size="10" text-anchor="middle" fill="#185FA5">Run MediaPipe + YOLOv8</text>
  <line x1="340" y1="245" x2="340" y2="265" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <polygon points="340,265 460,305 340,345 220,305" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1.3"/>
  <text x="340" y="301" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">Human</text>
  <text x="340" y="315" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">detected?</text>
  <line x1="460" y1="305" x2="570" y2="305" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="505" y="299" font-family="Arial" font-size="9" fill="#555">No</text>
  <rect x="570" y="287" width="95" height="36" rx="5" fill="#F1EFE8" stroke="#888" stroke-width="1"/>
  <text x="617" y="307" font-family="Arial" font-size="9" text-anchor="middle" fill="#444">Continue</text>
  <text x="617" y="319" font-family="Arial" font-size="9" text-anchor="middle" fill="#444">autonomous nav</text>
  <line x1="617" y1="323" x2="617" y2="173" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="617" y1="173" x2="460" y2="173" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arr)"/>

  <line x1="340" y1="345" x2="340" y2="365" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="352" y="360" font-family="Arial" font-size="9" fill="#555">Yes</text>

  <polygon points="340,365 460,405 340,445 220,405" fill="#FEF9EC" stroke="#E8A020" stroke-width="1.3"/>
  <text x="340" y="401" font-family="Arial" font-size="10" text-anchor="middle" fill="#854F0B">Valid gesture</text>
  <text x="340" y="415" font-family="Arial" font-size="10" text-anchor="middle" fill="#854F0B">detected?</text>
  <line x1="460" y1="405" x2="530" y2="405" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="487" y="399" font-family="Arial" font-size="9" fill="#555">Yes</text>
  <rect x="530" y="385" width="125" height="40" rx="5" fill="#FAE4A6" stroke="#E8A020" stroke-width="1"/>
  <text x="592" y="405" font-family="Arial" font-size="9" text-anchor="middle" fill="#854F0B">Execute gesture</text>
  <text x="592" y="418" font-family="Arial" font-size="9" text-anchor="middle" fill="#854F0B">command (priority)</text>
  <line x1="617" y1="425" x2="617" y2="450" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3"/>

  <line x1="340" y1="445" x2="340" y2="465" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>
  <text x="352" y="460" font-family="Arial" font-size="9" fill="#555">No</text>

  <rect x="220" y="465" width="240" height="40" rx="5" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1.3"/>
  <text x="340" y="485" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">Classify human motion state</text>
  <text x="340" y="498" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">(Approaching/Receding/Lateral)</text>
  <line x1="340" y1="505" x2="340" y2="525" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="205" y="525" width="270" height="55" rx="5" fill="#FDF0F0" stroke="#C94040" stroke-width="1.3"/>
  <text x="340" y="545" font-family="Arial" font-size="10" font-weight="bold" text-anchor="middle" fill="#A32D2D">Brain Node Decision</text>
  <text x="340" y="560" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Approaching → stop and yield</text>
  <text x="340" y="573" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Lateral → adjust heading</text>
  <line x1="340" y1="580" x2="340" y2="600" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="230" y="600" width="220" height="34" rx="5" fill="#FDF0F0" stroke="#C94040" stroke-width="1.3"/>
  <text x="340" y="621" font-family="Arial" font-size="10" text-anchor="middle" fill="#A32D2D">Publish /cmd_vel → ESP32</text>
  <text x="340" y="633" font-family="Arial" font-size="10" text-anchor="middle" fill="#A32D2D">Motor response via micro-ROS</text>
  <line x1="340" y1="634" x2="340" y2="654" stroke="#333" stroke-width="1.3" marker-end="url(#arr)"/>

  <rect x="260" y="654" width="160" height="28" rx="14" fill="#C6EDDA" stroke="#0F6E56" stroke-width="1.3"/>
  <text x="340" y="673" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">Next frame (continuous)</text>
  <line x1="260" y1="668" x2="160" y2="668" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="160" y1="668" x2="160" y2="228" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="160" y1="228" x2="228" y2="228" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arr)"/>
  <line x1="617" y1="450" x2="617" y2="668" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="617" y1="668" x2="420" y2="668" stroke="#888" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arr)"/>
</svg>'''

cairosvg.svg2png(bytestring=svg_flow.encode(), write_to=os.path.expanduser("~/figs/fig_workflow.png"), output_width=680, output_height=780)
print("Workflow PNG done")

# Gesture diagram
svg_gestures = '''<svg width="700" height="320" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="320" fill="white"/>
  <text x="350" y="22" font-family="Arial" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">Figure 3.3: Gesture Classes and Corresponding Robot Commands</text>

  <rect x="20" y="38" width="130" height="260" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <rect x="162" y="38" width="130" height="260" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <rect x="304" y="38" width="130" height="260" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <rect x="446" y="38" width="130" height="260" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>
  <rect x="550" y="38" width="130" height="260" rx="6" fill="#EEF4FB" stroke="#4A90D9" stroke-width="1.3"/>

  <text x="85" y="58" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#185FA5">STOP</text>
  <text x="85" y="105" font-family="Arial" font-size="40" text-anchor="middle">🖐</text>
  <text x="85" y="165" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">All 5 fingers</text>
  <text x="85" y="178" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">fully extended</text>
  <rect x="35" y="235" width="100" height="24" rx="4" fill="#FDF0F0" stroke="#C94040" stroke-width="1"/>
  <text x="85" y="252" font-family="Arial" font-size="10" text-anchor="middle" fill="#A32D2D">Robot halts</text>

  <text x="227" y="58" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#185FA5">GO (FORWARD)</text>
  <text x="227" y="105" font-family="Arial" font-size="40" text-anchor="middle">👍</text>
  <text x="227" y="165" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Thumb extended</text>
  <text x="227" y="178" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">others curled</text>
  <rect x="177" y="235" width="100" height="24" rx="4" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1"/>
  <text x="227" y="252" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">Move forward</text>

  <text x="369" y="58" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#185FA5">LEFT / RIGHT</text>
  <text x="369" y="105" font-family="Arial" font-size="40" text-anchor="middle">☝</text>
  <text x="369" y="165" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Index finger pointing</text>
  <text x="369" y="178" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">horizontally L or R</text>
  <rect x="319" y="235" width="100" height="24" rx="4" fill="#FEF9EC" stroke="#E8A020" stroke-width="1"/>
  <text x="369" y="252" font-family="Arial" font-size="10" text-anchor="middle" fill="#854F0B">Turn left/right</text>

  <text x="511" y="58" font-family="Arial" font-size="11" font-weight="bold" text-anchor="middle" fill="#185FA5">FOLLOW</text>
  <text x="511" y="105" font-family="Arial" font-size="40" text-anchor="middle">✌</text>
  <text x="511" y="165" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">Index + middle</text>
  <text x="511" y="178" font-family="Arial" font-size="9" text-anchor="middle" fill="#333">fingers extended</text>
  <rect x="461" y="235" width="100" height="24" rx="4" fill="#F0FBF4" stroke="#2EAB6A" stroke-width="1"/>
  <text x="511" y="252" font-family="Arial" font-size="10" text-anchor="middle" fill="#0F6E56">Track person</text>

  <text x="350" y="300" font-family="Arial" font-size="9" text-anchor="middle" fill="#666">
    Classification uses geometric feature analysis on 21 MediaPipe Hands landmarks. Confidence threshold: 0.70.
  </text>
</svg>'''

cairosvg.svg2png(bytestring=svg_gestures.encode(), write_to=os.path.expanduser("~/figs/fig_gestures.png"), output_width=700, output_height=320)
print("Gestures PNG done")

# Placeholder images using Pillow
def make_placeholder(filename, label, w=500, h=350):
    img = Image.new('RGB', (w, h), color='#F5F5F5')
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, w-3, h-3], outline='#AAAAAA', width=2)
    for i in range(0, w, 20):
        draw.line([(i, 0), (min(i+10, w), 0)], fill='#AAAAAA', width=2)
        draw.line([(i, h-1), (min(i+10, w), h-1)], fill='#AAAAAA', width=2)
    for i in range(0, h, 20):
        draw.line([(0, i), (0, min(i+10, h))], fill='#AAAAAA', width=2)
        draw.line([(w-1, i), (w-1, min(i+10, h))], fill='#AAAAAA', width=2)
    cx, cy = w//2, h//2 - 20
    draw.rectangle([cx-30, cy-20, cx+30, cy+20], outline='#AAAAAA', width=2)
    draw.ellipse([cx-15, cy-12, cx+15, cy+12], outline='#AAAAAA', width=2)
    draw.rectangle([cx-38, cy-10, cx-31, cy-5], outline='#AAAAAA', width=1)
    draw.rectangle([20, h//2+20, w-20, h//2+65], fill='#E8E8E8', outline='#AAAAAA', width=1)
    # Simulate text lines with rectangles (PIL doesn't have simple text scaling)
    lines = label.split('\n')
    for i, line in enumerate(lines):
        y_pos = h//2 + 30 + i*18
        text_w = len(line) * 7
        draw.rectangle([w//2 - text_w//2, y_pos, w//2 + text_w//2, y_pos + 14], fill='#999999')
    img.save(os.path.expanduser(f"~/figs/{filename}"))

make_placeholder('fig_pi5.png', '[Insert photograph of Raspberry Pi 5 board]', 460, 300)
make_placeholder('fig_lidar.png', '[Insert photograph of LiDAR sensor module]', 460, 300)
make_placeholder('fig_camera.png', '[Insert photograph of USB camera module]', 460, 300)
make_placeholder('fig_esp32.png', '[Insert photograph of ESP32 microcontroller]', 460, 300)
make_placeholder('fig_hardware_assembled.png', '[Insert photograph of fully assembled robot]', 560, 380)
make_placeholder('fig_rviz_slam.png', '[Insert screenshot of RViz2 showing SLAM map generation]', 560, 380)
make_placeholder('fig_gazebo.png', '[Insert screenshot of Gazebo simulation environment]', 560, 380)
make_placeholder('fig_dashboard.png', '[Insert screenshot of ROS2 web dashboard]', 560, 380)

print("All placeholder PNGs created in ~/figs/")
