# Disaster Prevention, Memory Hygiene & Context Recovery Guide

**Project:** Autonomous Mobile Robot with Edge-Based Human Intention Recognition  
**Workspace:** `/home/j/ros2_cognition_ws`  
**Location:** Root Project Workspace  
**Date Created:** September 9, 2026  

---

## 1. Executive Summary & Incident Postmortem

### What Happened
On September 9, 2026, at approximately 17:37–17:40 UTC, during an intensive drafting session in the `write_up/` folder, the Antigravity IDE crashed unexpectedly. The session had reached **196 agentic turns**, having completed the full initial drafting and integration of Chapters 1 through 5, generation of 9 high-resolution engineering figures, and updating `main.tex`. Immediately following Step 196 (an asynchronous directory listing command), process PID `79520` (the Antigravity IDE language server / client agent) crashed, producing crash logs in `~/.gemini/antigravity-ide/crashes/` and disconnecting the active chat window.

### Why Zero Work Was Lost
Despite the crash, **no file content or context was lost**:
1. **Physical Files Intact:** The editor had `files.autoSave` enabled, meaning all modifications to `ch1_introduction.tex`, `ch2_literature_review.tex`, `ch3_methodology.tex`, `ch4_results.tex`, `ch5_conclusion.tex`, `generate_report_figures.py`, and `references.bib` had already been written to the SSD.
2. **Conversation History Preserved:** Antigravity stores conversation state in persistent SQLite databases and append-only JSONL transcripts on disk:
   - **Transcript:** `~/.gemini/antigravity-ide/brain/9109f32e-1531-414e-a1f9-70edaf7d8110/.system_generated/logs/transcript.jsonl`
   - **Database:** `~/.gemini/antigravity-ide/conversations/9109f32e-1531-414e-a1f9-70edaf7d8110.db`
   - **Implementation Plan:** `~/.gemini/antigravity-ide/brain/9109f32e-1531-414e-a1f9-70edaf7d8110/implementation_plan.md`

### Root Cause Analysis
The crash was caused by a combination of three factors:
1. **Host Memory Headroom:** The development machine possesses **5.7 GB of usable RAM**. With desktop environments, background processes, language servers, and Node.js instances active, free RAM was constrained (~880 MB free, 834 MB swap utilized).
2. **Chromium / Electron Context Bloat:** In single chat sessions that exceed 150–200 multi-step turns with deep tool executions and code diffs, the Electron renderer's V8 heap consumes extensive memory, making it vulnerable to out-of-memory (OOM) faults or process crashes.
3. **Lack of Baseline Version Control:** The workspace was not initialized as a Git repository, meaning there were no committed snapshots or branch fallbacks in case an unsaved buffer was corrupted.

---

## 2. Precautions Taken to Prevent Future Crashes & Context Loss

To ensure this never happens again, five layers of defense have been implemented:

```
+-------------------------------------------------------------------------+
|                        5-LAYER DEFENSE ARCHITECTURE                     |
+-------------------------------------------------------------------------+
| Layer 1: Git Version Control & Automated Safety Snapshots              |
| Layer 2: Hardened IDE Auto-Save & Hot-Exit Persistence                   |
| Layer 3: Milestone-Driven Context Chunking & @ Mention Bridges           |
| Layer 4: Host Memory & Process Hygiene Monitoring                       |
| Layer 5: Disk-Level SQLite & JSONL Disaster Recovery Playbook           |
+-------------------------------------------------------------------------+
```

---

### Layer 1: Git Version Control & Safety Snapshots

The entire repository has been initialized with Git tracking and a tailored `.gitignore` to prevent repository bloat while guaranteeing that every file is version-controlled.

#### 1. `.gitignore` Configuration
A custom `.gitignore` was placed in `/home/j/ros2_cognition_ws/.gitignore` to prevent large binary files from overloading Git and memory:
- **Excluded:**
  - `archives/` (prevents tracking the 1.7 GB `cognition_ws.zip` backup).
  - `test_vids/` (prevents tracking 181 MB of raw MP4/AVI validation videos).
  - `chat_exports/` (prevents tracking 66 MB of past chat zip dumps).
  - `bags/` and `logs/` (prevents tracking volatile runtime ROS2 execution logs).
  - LaTeX intermediate files (`*.aux`, `*.log`, `*.out`, `*.toc`, `*.lof`, `*.lot`, `*.synctex.gz`).
  - Python cache (`__pycache__/`, `*.pyc`).

#### 2. Baseline Git Snapshot
All 113 essential project files—including all ROS2 nodes, launch scripts, neural network weights, figures, thesis chapters, and roadmaps—were committed on branch `main` under commit `9f1d261`:
```bash
git add .
git commit -m "feat: initial baseline snapshot of ros2_cognition_ws and complete write_up thesis (Chapters 1-5)"
```

#### How to Use Git During Work:
- **After every completed chapter or major code change:**
  ```bash
  git add .
  git commit -m "feat(write_up): complete front matter preliminary pages"
  ```
- **To see what changed since the last commit:**
  ```bash
  git status
  git diff
  ```
- **If a file is accidentally deleted or corrupted, restore it instantly:**
  ```bash
  git checkout -- <file-path>
  ```

---

### Layer 2: Hardened IDE Auto-Save & Hot-Exit Persistence

We updated [.vscode/settings.json](file:///home/j/ros2_cognition_ws/.vscode/settings.json) with robust editor persistence parameters:

```json
{
    "editor.fontSize": 15,
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    "files.hotExit": "onExitAndWindowClose",
    "workbench.editor.restoreWindows": "all"
}
```

#### Explanation of Settings:
- `"files.autoSave": "afterDelay"`: Automatically writes dirty buffers to disk without waiting for a manual `Ctrl+S`.
- `"files.autoSaveDelay": 1000`: Reduces the delay to **1 second** (1000 ms). Within one second of you or the agent stopping typing, all changes are written directly to the SSD.
- `"files.hotExit": "onExitAndWindowClose"`: Ensures that even if the window closes abruptly or the IDE crashes, unsaved editor tabs are saved into an emergency backup cache and restored when the window reopens.
- `"workbench.editor.restoreWindows": "all"`: Guarantees that all active tabs (such as `main.tex`, `references.bib`, and chapter files) are immediately re-opened in their exact positions after an IDE restart.

---

### Layer 3: Milestone-Driven Context Chunking & Session Management

Running an AI chat session for 150+ turns creates huge DOM trees and consumes gigabytes of Chromium renderer memory. The correct engineering practice is **Milestone-Driven Chunking**:

1. **Use Persistent Roadmap Files as the Single Source of Truth:**
   - The roadmap file [write_up/TODO_AND_ROADMAP.md](file:///home/j/ros2_cognition_ws/write_up/TODO_AND_ROADMAP.md) acts as the bridge between sessions.
   - All completed milestones are checked off (`[x]`), and upcoming tasks are outlined with concrete acceptance criteria.
2. **Starting Fresh Chat Sessions at Logical Milestones:**
   - When a major milestone is finished (e.g., finishing all 5 chapters), start a fresh chat session for the next phase (e.g., Preliminary Pages & PDF compilation).
   - This resets the agent's context window to zero token overhead and frees all cached V8 renderer RAM.
3. **Re-linking Context Seamlessly with `@` Mentions:**
   - When opening a new chat, you never need to re-explain the project from scratch. Simply type:
     - `@TODO_AND_ROADMAP.md` to feed the agent the exact status and next steps.
     - Or open the mention menu with `@` and select **Previous Conversations** (`9109f32e-1531-414e-a1f9-70edaf7d8110`) to pull in context from the earlier session.

---

### Layer 4: Host Memory & Process Hygiene

Because the machine has 5.7 GB of physical RAM, keeping memory usage healthy prevents Linux OOM (Out Of Memory) killer interventions:

1. **Quick Health Check Command:**
   Before launching heavy simulations or extensive builds, check available RAM:
   ```bash
   free -h
   ```
   *Rule of thumb:* Ensure `available` memory is at least **1.5 GB** before running deep AI agent tasks.
2. **Manage Background Docker Containers:**
   If hardware testing containers (`yahboom_base`, `micro_ros_agent`, `yahboom_gesture`) are not actively in use, stop them to release host RAM:
   ```bash
   docker stop $(docker ps -q)
   ```
3. **Clear Stale Node/Language Server Instances:**
   If the IDE ever feels sluggish, closing and re-opening the IDE clears orphaned language server threads and garbage-collects unused RAM.

---

### Layer 5: Disaster Recovery Playbook (Instant Context Recovery)

If a crash ever happens in any conversation, here is the exact procedure to recover everything:

#### Step 1: Locate the Conversation ID
All Antigravity conversations are stored under `~/.gemini/antigravity-ide/brain/` and `~/.gemini/antigravity-ide/conversations/`.
Run this command to find the most recently active sessions sorted by time:
```bash
ls -lt ~/.gemini/antigravity-ide/brain/
```
The top entries correspond to your latest sessions.

#### Step 2: Read the Implementation Plan & Artifacts
Each session directory contains the full implementation plan and scratch files generated during that chat:
```bash
cat ~/.gemini/antigravity-ide/brain/<CONVERSATION_ID>/implementation_plan.md
```

#### Step 3: Inspect the Exact Last Prompts and Agent Responses
The complete step-by-step history is recorded in `transcript.jsonl`. You can extract the user prompts or the last actions using Python or `jq`:

```bash
# View the last 5 user messages in that conversation:
grep '"type":"USER_INPUT"' ~/.gemini/antigravity-ide/brain/<CONVERSATION_ID>/.system_generated/logs/transcript.jsonl | jq -r '.content' | tail -n 5

# View the last 5 tool calls and status:
tail -n 15 ~/.gemini/antigravity-ide/brain/<CONVERSATION_ID>/.system_generated/logs/transcript.jsonl | jq -c '{step_index, type, status}'
```

#### Step 4: Resume in a New Chat
Open a new chat window and tell the agent:
> *"Resume work from conversation `<CONVERSATION_ID>`. Check `TODO_AND_ROADMAP.md` and proceed with the next task."*

The agent will inspect the transcript and roadmap, and continue seamlessly without any context loss.

---

## 3. Current System State & Readiness

As of this moment:
- [x] **Git Version Control:** Initialized, clean `.gitignore`, initial baseline commit `9f1d261` recorded.
- [x] **Auto-Save & Hot Exit:** Hardened to 1000 ms flush with full window restoration enabled.
- [x] **Chapters 1–5:** 100% written, peer-reviewed against GCTU standards, non-indented 3+ sentence paragraphs, with ERQs and real hardware results integrated.
- [x] **Figures:** 9 high-resolution engineering schematics and data plots saved in `write_up/figures/`.
- [x] **Bibliography:** `references.bib` updated with IEEE-standard citations.
- [x] **Master Roadmap:** [write_up/TODO_AND_ROADMAP.md](file:///home/j/ros2_cognition_ws/write_up/TODO_AND_ROADMAP.md) synchronized and ready for the next milestone: **Preliminary Pages & Front Matter**.
