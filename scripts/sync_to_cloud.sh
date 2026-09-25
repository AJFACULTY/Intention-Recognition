#!/usr/bin/env bash
# ==============================================================================
# Cloud Sync Helper for Co-Authors (Google Drive / Dropbox / Nextcloud)
# ==============================================================================
# Usage:
#   1. Set TARGET_DIR to your local cloud sync directory (e.g. ~/GoogleDrive/Thesis)
#   2. Run: ./scripts/sync_to_cloud.sh
# ==============================================================================

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Configure your shared local folder here:
TARGET_DIR="${1:-$HOME/GoogleDrive/Thesis_Documents}"

echo "=================================================================="
echo ">> Syncing Compiled PDFs to Shared Co-Author Folder..."
echo "   Target Directory: $TARGET_DIR"
echo "=================================================================="

mkdir -p "$TARGET_DIR"

if [ -f "$WS_DIR/write_up/thesis_final.pdf" ]; then
    cp -v "$WS_DIR/write_up/thesis_final.pdf" "$TARGET_DIR/"
fi

if [ -f "$WS_DIR/publications/conference_paper/conference_paper.pdf" ]; then
    cp -v "$WS_DIR/publications/conference_paper/conference_paper.pdf" "$TARGET_DIR/"
fi

if [ -f "$WS_DIR/publications/journal_paper/journal_paper.pdf" ]; then
    cp -v "$WS_DIR/publications/journal_paper/journal_paper.pdf" "$TARGET_DIR/"
fi

echo "=================================================================="
echo "✓ Sync complete! Co-authors can now view the latest documents."
echo "=================================================================="
