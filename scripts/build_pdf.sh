#!/bin/bash
# ==============================================================================
# build_pdf.sh — Offline Turnkey LaTeX Compiler (Overleaf Experience Locally)
# Uses standalone Tectonic engine: 100% offline, zero-root, single-pass build
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${WORKSPACE}/write_up/overleaf_ready"
OUTPUT_PDF="${WORKSPACE}/write_up/thesis_final.pdf"

TECTONIC_BIN="${HOME}/.local/bin/tectonic"
if [ ! -x "${TECTONIC_BIN}" ]; then
    if which tectonic >/dev/null 2>&1; then
        TECTONIC_BIN="$(which tectonic)"
    else
        echo "[ERROR] Tectonic compiler not found in ~/.local/bin/tectonic or PATH!"
        exit 1
    fi
fi

echo "=================================================================="
echo "    COMPILING GCTU THESIS MONOGRAPH (OFFLINE LATEX ENGINE)"
echo "=================================================================="
echo ">> Target Directory: ${TARGET_DIR}"
echo ">> Engine: ${TECTONIC_BIN}"

# 1. Update overleaf_ready package from master write_up sources
echo "[1/3] Refreshing overleaf_ready package..."
python3 "${WORKSPACE}/scripts/export_overleaf_zip.py" >/dev/null 2>&1 || true

# 2. Compile LaTeX
echo "[2/3] Compiling document (main.tex + front_matter + chapters + references)..."
cd "${TARGET_DIR}"
"${TECTONIC_BIN}" main.tex

# 3. Copy final PDF to write_up/
if [ -f "${TARGET_DIR}/main.pdf" ]; then
    cp "${TARGET_DIR}/main.pdf" "${OUTPUT_PDF}"
    echo "[3/3] Output generated successfully!"
    echo "=================================================================="
    echo "✓ PDF BUILT: ${OUTPUT_PDF}"
    echo "  File Size: $(du -h "${OUTPUT_PDF}" | cut -f1)"
    echo "=================================================================="
else
    echo "[ERROR] Compilation finished without producing main.pdf!"
    exit 1
fi
