#!/usr/bin/env bash
# ==============================================================================
# IEEE Journal Paper Builder (Tectonic Standalone)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$PATH"

echo "=================================================================="
echo ">> Compiling IEEE Journal Manuscript (journal_paper.tex)..."
echo "=================================================================="

tectonic -X compile journal_paper.tex

echo "=================================================================="
echo "✓ IEEE Journal Manuscript Built Successfully!"
echo "  Output: $SCRIPT_DIR/journal_paper.pdf"
echo "  Pages:  $(pdfinfo journal_paper.pdf | grep 'Pages:' | awk '{print $2}')"
echo "=================================================================="
