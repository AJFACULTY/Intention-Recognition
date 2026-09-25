#!/usr/bin/env bash
# ==============================================================================
# Master Publications Builder
# Builds both IEEE Conference Paper and IEEE Journal Manuscript
# ==============================================================================
set -e

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=================================================================="
echo ">> [1/2] Building IEEE Conference Paper..."
echo "=================================================================="
"$WS_DIR/publications/conference_paper/build_conference_paper.sh"

echo ""
echo "=================================================================="
echo ">> [2/2] Building IEEE Journal Manuscript..."
echo "=================================================================="
"$WS_DIR/publications/journal_paper/build_journal_paper.sh"

echo ""
echo "=================================================================="
echo "✓ ALL PUBLICATIONS BUILT SUCCESSFULLY!"
echo "  - Conference: $WS_DIR/publications/conference_paper/conference_paper.pdf"
echo "  - Journal:    $WS_DIR/publications/journal_paper/journal_paper.pdf"
echo "=================================================================="
