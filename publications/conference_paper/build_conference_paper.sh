#!/usr/bin/env bash
# ==============================================================================
# IEEE Conference Paper Builder (Tectonic Standalone)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$PATH"

echo "=================================================================="
echo ">> Compiling IEEE Conference Paper (conference_paper.tex)..."
echo "=================================================================="

tectonic -X compile conference_paper.tex

echo "=================================================================="
echo "✓ IEEE Conference Paper Built Successfully!"
echo "  Output: $SCRIPT_DIR/conference_paper.pdf"
echo "  Pages:  $(pdfinfo conference_paper.pdf | grep 'Pages:' | awk '{print $2}')"
echo "=================================================================="
