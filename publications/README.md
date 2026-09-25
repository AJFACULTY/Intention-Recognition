# Academic Publications Suite — Autonomous Mobile Robot Cognition

This directory contains publication-ready manuscripts derived from the GCTU undergraduate engineering research project, organized into dual-track academic formats:
1. **IEEE Conference Paper (6 Pages):** Target venues include IEEE ICRA, IROS, RO-MAN, or IEEE AFRICON.
2. **IEEE Journal Manuscript (10–12 Pages):** Target venues include *IEEE Transactions on Human-Machine Systems*, *IEEE Robotics and Automation Letters (RA-L)*, or *Journal of Intelligent & Robotic Systems (Springer)*.

---

## Directory Organization

```
publications/
├── README.md                      # Academic publication and submission guide
├── build_all_papers.sh            # Automated master build script (builds both PDFs)
├── conference_paper/              # 6-page IEEE conference manuscript
│   ├── conference_paper.tex       # Conference LaTeX source (\documentclass[conference]{IEEEtran})
│   ├── conference_paper.pdf       # Compiled conference PDF
│   ├── build_conference_paper.sh  # Standalone fast builder
│   ├── figures/ -> ../../write_up/figures/  # Shared empirical figures symlink
│   └── references.bib -> ../../write_up/references.bib # 30 IEEE citations symlink
└── journal_paper/                 # 10-12 page IEEE journal manuscript
    ├── journal_paper.tex          # Journal LaTeX source (\documentclass[journal]{IEEEtran})
    ├── journal_paper.pdf          # Compiled journal PDF
    ├── build_journal_paper.sh     # Standalone fast builder
    ├── figures/ -> ../../write_up/figures/  # Shared empirical figures symlink
    └── references.bib -> ../../write_up/references.bib # 30 IEEE citations symlink
```

---

## Strategy for "Not Ready to Present Yet"

If you are not yet ready or able to present a paper in person at an international conference, the dual-track strategy provides two immediate solutions:

### Option A: The Journal Route (Zero Presentation Required)
- **No in-person attendance or oral presentation:** Journals operate **100% online**. You submit the PDF via the journal's peer-review portal (e.g. IEEE Author Portal / ScholarOne).
- **Written peer review:** Expert reviewers evaluate the manuscript over 2–4 months and return written comments. You respond with written revisions.
- **Publication:** Once accepted, the paper is assigned a DOI and published online directly in IEEE Xplore. You never have to travel or stand in front of an audience.

### Option B: The Conference Route (Proxy or Virtual Presentation)
- **Virtual / Hybrid Tracks:** Many contemporary IEEE conferences offer hybrid or pre-recorded video presentation tracks.
- **Co-Author / Supervisor Presentation:** Under IEEE conference policy, **any co-author or the research supervisor** can register and present the paper at the conference on behalf of the team. The student remains the **First Author**.
- **Cycle Timing:** Conferences have submission deadlines 4–6 months before the physical event, providing ample time to prepare a 10-minute slide deck.

---

## Zero-Plagiarism Assurance & Turnitin Pre-Check Protocol

To guarantee that neither the thesis nor the publication manuscripts trigger plagiarism flags:

1. **Empirical Grounding (100% Original Data):**
   All numerical data (Table 4.3 velocity measurements, Table 4.4 LiDAR scans, Table 4.5 132\,ms latency budget, Figure 4.10 confusion matrix) are physical hardware measurements generated on the Raspberry Pi 5 testbed. Empirical experimental data cannot be plagiarized.
2. **The "Triad Synthesis" Paraphrasing Formula:**
   All literature review text follows the strict three-part formula:
   - **Step 1 (Scope):** What the reviewed authors investigated in your own phrasing.
   - **Step 2 (Empirical Finding):** Their specific benchmark or experimental result with formal citation (`\cite{...}`).
   - **Step 3 (Critical Gap):** Exactly how their system differs from our edge-deployed mobile robot.
3. **Turnitin Configuration Guidelines:**
   - **Threshold:** University standard requires $< 15\%$ aggregate similarity and $< 1\%$ from any single source.
   - **Mandatory Filter Settings:** In the Turnitin/iThenticate interface, ensure that **"Exclude Bibliography / References"** and **"Exclude Matches $< 10$ Words"** are checked. Standard technical phrases like *"autonomous mobile robot"* or *"Human-Robot Interaction"* trigger false positives if short matches are not excluded.
4. **Self-Citation / Prior Thesis Disclosure:**
   Both manuscripts include the formal IEEE disclosure footnote on Page 1:
   > *"This work is based upon and extends the undergraduate thesis conducted at the Department of Computer Engineering, Ghana Communication Technology University (GCTU)."*
   This explicitly prevents self-plagiarism flags between the published paper and the university library thesis repository.

---

## Building the Publications

To compile both manuscripts in seconds using the local offline Tectonic compiler:

```bash
# Build both conference and journal manuscripts:
./publications/build_all_papers.sh

# Or build individually:
./publications/conference_paper/build_conference_paper.sh
./publications/journal_paper/build_journal_paper.sh
```
