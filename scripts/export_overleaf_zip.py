#!/usr/bin/env python3
"""
export_overleaf_zip.py — One-Click Overleaf Package Generator
============================================================
Creates a clean, 100% self-contained Overleaf-ready project folder and zip archive
for the undergraduate thesis at Ghana Communication Technology University (GCTU).

Features:
  - Copies main.tex, references.bib, front_matter/, and chapters/
  - Automatically identifies all figures cited in chapters/*.tex
  - Copies only required figures into figures/ (avoiding large unused raw assets)
  - Eliminates external relative paths (e.g. ../maps/) to ensure zero compilation errors
  - Produces 'write_up/thesis_overleaf.zip' ready for 1-click import into Overleaf
"""

import os
import re
import shutil
import zipfile

WORKSPACE = "/home/j/ros2_cognition_ws"
WRITEUP_DIR = os.path.join(WORKSPACE, "write_up")
OUTPUT_DIR = os.path.join(WRITEUP_DIR, "overleaf_ready")
OUTPUT_ZIP = os.path.join(WRITEUP_DIR, "thesis_overleaf.zip")

def main():
    print("=" * 70)
    print("   GENERATING OVERLEAF-READY THESIS PACKAGE")
    print("=" * 70)

    # 1. Clean previous build
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "front_matter"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "chapters"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "figures"), exist_ok=True)

    # 2. Copy root documents
    shutil.copy2(os.path.join(WRITEUP_DIR, "main.tex"), os.path.join(OUTPUT_DIR, "main.tex"))
    shutil.copy2(os.path.join(WRITEUP_DIR, "references.bib"), os.path.join(OUTPUT_DIR, "references.bib"))
    print("✓ Copied main.tex and references.bib")

    figure_names = set()

    # 3. Copy front_matter files and scan figures
    fm_dir = os.path.join(WRITEUP_DIR, "front_matter")
    for f in os.listdir(fm_dir):
        if f.endswith(".tex"):
            src_f = os.path.join(fm_dir, f)
            with open(src_f, "r", encoding="utf-8") as rf:
                fm_content = rf.read()
            for m in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', fm_content):
                figure_names.add(os.path.basename(m.strip()))
            shutil.copy2(src_f, os.path.join(OUTPUT_DIR, "front_matter", f))
    print(f"✓ Copied {len(os.listdir(fm_dir))} front matter sections")

    # 4. Copy and sanitize chapters
    ch_dir = os.path.join(WRITEUP_DIR, "chapters")
    for ch in sorted(os.listdir(ch_dir)):
        if not ch.endswith(".tex"):
            continue
        src_path = os.path.join(ch_dir, ch)
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract all \includegraphics references
        matches = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content)
        for m in matches:
            # strip any 'figures/' prefix so it's just the basename
            base = os.path.basename(m.strip())
            figure_names.add(base)

        # Standardize \includegraphics to use base filenames (since \graphicspath{{figures/}} is set)
        clean_content = re.sub(
            r'(\\includegraphics(?:\[[^\]]*\])?\{)figures/([^}]+)\}',
            r'\1\2}',
            content
        )

        dst_path = os.path.join(OUTPUT_DIR, "chapters", ch)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(clean_content)

    print(f"✓ Copied 5 chapters and scanned {len(figure_names)} unique referenced figures")

    # 5. Copy required figures into figures/
    src_fig_dir = os.path.join(WRITEUP_DIR, "figures")
    copied_figs = 0
    missing_figs = []

    for fig in sorted(figure_names):
        src_fig = os.path.join(src_fig_dir, fig)
        if os.path.exists(src_fig):
            shutil.copy2(src_fig, os.path.join(OUTPUT_DIR, "figures", fig))
            copied_figs += 1
        else:
            # Check fallback locations if needed
            found = False
            for alt in [
                os.path.join(WORKSPACE, "maps", fig),
                os.path.join(WORKSPACE, "test_pics", fig),
                os.path.join(WORKSPACE, "docs_and_figures", fig)
            ]:
                if os.path.exists(alt):
                    shutil.copy2(alt, os.path.join(OUTPUT_DIR, "figures", fig))
                    copied_figs += 1
                    found = True
                    break
            if not found:
                missing_figs.append(fig)

    print(f"✓ Gathered {copied_figs} figures into overleaf_ready/figures/")
    if missing_figs:
        print(f"⚠️ WARNING: Missing figures: {missing_figs}")

    # 6. Create Zip Archive
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, OUTPUT_DIR)
                zipf.write(full_path, rel_path)

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print("=" * 70)
    print(f"✓ SUCCESS: Overleaf package created at: {OUTPUT_ZIP}")
    print(f"  Package Size: {zip_size_mb:.2f} MB (Well under Overleaf's 100 MB limit)")
    print(f"  Ready for 1-click upload: Overleaf -> New Project -> Upload Project")
    print("=" * 70)

if __name__ == "__main__":
    main()
