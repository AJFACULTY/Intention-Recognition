#!/usr/bin/env bash
# ==============================================================================
# Desktop & Terminal Notification Utility for Antigravity Milestones
# ==============================================================================
# Usage:
#   ./scripts/notify_milestone.sh milestone "Milestone 6: Preliminary Pages"
#   ./scripts/notify_milestone.sh limit 45
#   ./scripts/notify_milestone.sh general "Title" "Message body"
# ==============================================================================

EVENT_TYPE="${1:-milestone}"
PARAM="${2:-Milestone Completed}"

case "$EVENT_TYPE" in
  milestone)
    TITLE="🏆 Antigravity Milestone Completed!"
    BODY="Completed: $PARAM\nAll changes committed to Git. Please open a fresh chat for the next milestone."
    URGENCY="critical"
    ICON="emblem-default"
    ;;
  limit)
    TITLE="⚠️ Antigravity Chat Health Check"
    BODY="Turn count reached ~$PARAM. To prevent IDE lag and memory pressure, export history and start a fresh chat."
    URGENCY="normal"
    ICON="dialog-warning"
    ;;
  general)
    TITLE="${2:-Antigravity Notification}"
    BODY="${3:-Operation completed successfully.}"
    URGENCY="normal"
    ICON="dialog-information"
    ;;
  *)
    TITLE="Antigravity Alert"
    BODY="$PARAM"
    URGENCY="normal"
    ICON="dialog-information"
    ;;
esac

# Send desktop notification if GUI is available
if command -v notify-send >/dev/null 2>&1; then
    notify-send -u "$URGENCY" -i "$ICON" "$TITLE" "$BODY" 2>/dev/null || true
fi

# Also print to terminal with ANSI colors
echo -e "\n\033[1;32m======================================================================\033[0m"
echo -e "\033[1;33m$TITLE\033[0m"
echo -e "$BODY"
echo -e "\033[1;32m======================================================================\033[0m\n"
