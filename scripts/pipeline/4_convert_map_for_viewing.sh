#!/bin/bash
# ============================================================================
# 4_convert_map_for_viewing.sh
#
# .pgm files aren't viewable by most image viewers directly. This converts
# the most recent saved map to .png using cv2 (already installed in the
# yahboom_gesture container for gesture recognition — no new install needed).
# Since ~/cognition_ws is bind-mounted into the container, the .png lands
# on the host automatically too.
#
# Usage:
#   chmod +x 4_convert_map_for_viewing.sh
#   ./4_convert_map_for_viewing.sh
# ============================================================================

set -uo pipefail

LATEST_PGM=$(ls -t ~/cognition_ws/maps_new/*.pgm 2>/dev/null | head -1)

if [ -z "$LATEST_PGM" ]; then
    echo "No .pgm files found in ~/cognition_ws/maps_new/"
    echo "Checking ~/maps_new/ instead (host copy from the save script)..."
    LATEST_PGM=$(ls -t ~/maps_new/*.pgm 2>/dev/null | head -1)
fi

if [ -z "$LATEST_PGM" ]; then
    echo "ERROR: no .pgm map found anywhere. Did the save script run successfully?"
    exit 1
fi

echo "Found: $LATEST_PGM"
BASENAME=$(basename "$LATEST_PGM" .pgm)

# Convert via the container, since it already has cv2 installed.
# Path translation: host ~/cognition_ws/X == container /root/cognition_ws/X
CONTAINER_PGM="/root/cognition_ws/maps_new/${BASENAME}.pgm"
CONTAINER_PNG="/root/cognition_ws/maps_new/${BASENAME}.png"

echo "Converting via container (cv2)..."
docker exec yahboom_gesture python3 -c "
import cv2
img = cv2.imread('${CONTAINER_PGM}', cv2.IMREAD_UNCHANGED)
if img is None:
    print('ERROR: cv2 could not read the pgm file')
else:
    cv2.imwrite('${CONTAINER_PNG}', img)
    print(f'Converted: {img.shape[1]}x{img.shape[0]} pixels -> ${BASENAME}.png')
"

# If the container path didn't resolve (e.g. file was only in ~/maps_new/,
# not the bind-mounted cognition_ws), copy it in first and retry.
if [ ! -f ~/cognition_ws/maps_new/${BASENAME}.png ]; then
    echo "Not found via bind mount — copying into container directly and retrying..."
    docker cp "$LATEST_PGM" yahboom_gesture:/tmp/${BASENAME}.pgm
    docker exec yahboom_gesture python3 -c "
import cv2
img = cv2.imread('/tmp/${BASENAME}.pgm', cv2.IMREAD_UNCHANGED)
cv2.imwrite('/tmp/${BASENAME}.png', img)
print('Converted via /tmp fallback')
"
    docker cp yahboom_gesture:/tmp/${BASENAME}.png ~/maps_new/${BASENAME}.png
fi

echo
echo "======================================================"
echo "== DONE"
echo "======================================================"
find ~ -name "${BASENAME}.png" 2>/dev/null

echo
echo "To view it, from your LAPTOP terminal (not this SSH session):"
echo "  scp pi@<this-pi-ip>:~/cognition_ws/maps_new/${BASENAME}.png ~/Downloads/"
echo "  (or, if that path doesn't exist:)"
echo "  scp pi@<this-pi-ip>:~/maps_new/${BASENAME}.png ~/Downloads/"
echo
echo "Then open it with your normal image viewer, or upload it into the chat"
echo "with Claude so it can be looked at directly."
