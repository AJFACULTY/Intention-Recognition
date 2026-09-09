# Autonomous Mobile Robot Cognition Project — Agent Operating Rules

Welcome to the **ros2_cognition_ws** workspace. These mandatory rules are permanently active for all agent sessions operating within this directory and its subdirectories.

---

## 1. Single Source of Truth & Milestone Discipline
1. **Always Check the Roadmap First:** At the beginning of every session, consult the Master Roadmap:
   👉 [MASTER_WRITEUP_ROADMAP.md](file:///home/j/ros2_cognition_ws/MASTER_WRITEUP_ROADMAP.md) (or [write_up/TODO_AND_ROADMAP.md](file:///home/j/ros2_cognition_ws/write_up/TODO_AND_ROADMAP.md)).
2. **One Milestone at a Time:** Work strictly within the currently active milestone. Never begin a subsequent milestone until the current milestone's checklist items are verified and marked `[x]`.
3. **Update on Completion:** When a milestone finishes, update the roadmap, notify the user, and commit all changes to Git.

---

## 2. Crash Prevention, Turn Limits & Desktop Notifications
1. **Turn Budget & Health Check:** To prevent Chromium/Electron renderer memory exhaustion (which previously caused an IDE crash at turn 196), keep chat sessions focused.
   - When a chat approaches **turn 40–45**, proactively warn the user:
     > ⚠️ **Chat Limit Health Check:** *We are approaching turn 45. To keep the IDE fast and crash-free, let us conclude this immediate task, export our history, and transition to a fresh chat.*
2. **Milestone Completion Protocol:** Whenever a milestone is achieved:
   - Display a prominent Milestone Completion Box in your response.
   - Run the desktop notification utility:
     ```bash
     ./scripts/notify_milestone.sh milestone "<Milestone Name>"
     ```
   - Automatically export the session history, replies, and implementation plan:
     ```bash
     python3 scripts/export_chat_history.py
     ```
   - Stage and commit the workspace:
     ```bash
     git add . && git commit -m "feat: complete <Milestone Name>"
     ```

---

## 3. History, Plans & Decisions Persistence
1. **Single History Repository:** All historical context, user prompts, agent replies, implementation plans, and walkthroughs are stored in:
   👉 [project_history/](file:///home/j/ros2_cognition_ws/project_history/) (Master Index: [project_history/README.md](file:///home/j/ros2_cognition_ws/project_history/README.md)).
2. **Never Lose a Decision:** If the user asks about past decisions, bug postmortems, or hardware setups, inspect:
   - `project_history/chat_sessions/` for past prompt/reply dialogs.
   - `project_history/implementation_plans/` for design reviews.
   - `project_history/walkthroughs/` for verified benchmark tests.
   - `project_history/technical_evolution/` for error catalogues.

---

## 4. Academic Writing & Engineering Standards
When writing, revising, or compiling the undergraduate thesis in `write_up/`:
1. **GCTU Handbook Formatting Rules:**
   - Margins: Top = 2.5 cm, Bottom = 2.5 cm, Left = 4.0 cm (for binding), Right = 2.5 cm.
   - Line Spacing: 1.5 spacing (`\onehalfspacing`).
   - Paragraphing: First line must **NOT** be indented (`\setlength{\parindent}{0pt}`); paragraphs must be separated by space (`\setlength{\parskip}{1em}`).
   - Paragraph Rule: Every paragraph must contain **at least three sentences**.
2. **Prohibited Branding:**
   - Never mention retail laptop brands (e.g. "Lenovo", "Lenovo V15 ADA").
   - Always use formal engineering specification nomenclature: `x86_64 Host Workstation (AMD Ryzen 5, 8GB DDR4 RAM)`.
3. **Engineering Grounding:**
   - Ground all results in real physical robot data (Table 4.3 velocity tests, Table 4.4 LiDAR costmaps, 132 ms latency budget).
   - Ensure compliance with ISO 15066:2016 (collaborative safety), ISO 12100:2010 (risk mitigation), ROS REP-103/105, and OMG DDS v1.4 QoS.
