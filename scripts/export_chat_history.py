#!/usr/bin/env python3
"""
Chat History & Reply Exporter for Antigravity IDE
-------------------------------------------------
Extracts full conversations (user prompts + agent replies + actions)
from Antigravity's internal transcript JSONL logs and saves them into
the consolidated workspace project_history/ folder.
Also backs up any associated implementation_plan.md and walkthrough.md files.
"""

import os
import sys
import json
import glob
import shutil
import subprocess
from datetime import datetime

BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
WORKSPACE_ROOT = "/home/j/ros2_cognition_ws"
HISTORY_DIR = os.path.join(WORKSPACE_ROOT, "project_history")
CHAT_SESSIONS_DIR = os.path.join(HISTORY_DIR, "chat_sessions")
PLANS_DIR = os.path.join(HISTORY_DIR, "implementation_plans")
WALKTHROUGHS_DIR = os.path.join(HISTORY_DIR, "walkthroughs")

def get_recent_conversations(limit=5):
    """List recent conversation IDs sorted by modification time."""
    subdirs = [d for d in glob.glob(os.path.join(BRAIN_DIR, "*")) if os.path.isdir(d)]
    subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return [os.path.basename(d) for d in subdirs[:limit]]

def export_conversation(conv_id=None, label=None):
    if conv_id is None:
        recent = get_recent_conversations(1)
        if not recent:
            print("Error: No conversations found in brain directory.")
            return None
        conv_id = recent[0]

    session_brain_dir = os.path.join(BRAIN_DIR, conv_id)
    transcript_file = os.path.join(session_brain_dir, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found at {transcript_file}")
        return None

    date_str = datetime.now().strftime("%Y-%m-%d")
    short_id = conv_id[:8]
    session_name = f"SESSION_{date_str}_{label or short_id}.md"
    output_path = os.path.join(CHAT_SESSIONS_DIR, session_name)

    print(f"Parsing transcript: {transcript_file}")
    with open(transcript_file, "r", encoding="utf-8") as f:
        steps = [json.loads(line) for line in f if line.strip()]

    print(f"Total steps found: {len(steps)}")

    md_lines = []
    md_lines.append(f"# INTERACTIVE SESSION & CHAT REPLIES ARCHIVE")
    md_lines.append(f"**Session ID:** `{conv_id}`  ")
    md_lines.append(f"**Exported At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    md_lines.append(f"**Workspace:** `{WORKSPACE_ROOT}`  ")
    md_lines.append(f"**Source Log:** `{transcript_file}`  \n")
    md_lines.append(f"---\n")
    md_lines.append(f"## Chronological Dialog & Engineering Record\n")

    prompt_counter = 0
    i = 0
    while i < len(steps):
        step = steps[i]
        step_type = step.get("type")

        if step_type == "USER_INPUT":
            prompt_counter += 1
            content = step.get("content", "").strip()
            if "<USER_REQUEST>" in content:
                user_req = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            else:
                user_req = content

            timestamp = step.get("created_at", "")
            md_lines.append(f"### Prompt {prompt_counter} ({timestamp})\n")
            md_lines.append(f"#### 👤 User Request:\n")
            md_lines.append(f"> {user_req.replace(chr(10), chr(10) + '> ')}\n\n")
            md_lines.append(f"#### 🤖 Agent Replies & Actions:\n")

            i += 1
            while i < len(steps) and steps[i].get("type") != "USER_INPUT":
                s = steps[i]
                s_type = s.get("type")

                if s_type == "PLANNER_RESPONSE":
                    resp_content = s.get("content")
                    if resp_content and resp_content.strip():
                        md_lines.append(f"{resp_content.strip()}\n\n")

                    tool_calls = s.get("tool_calls", [])
                    if tool_calls:
                        for tc in tool_calls:
                            name = tc.get("name", "")
                            args = tc.get("args", {})
                            summary = args.get("toolSummary") or args.get("Description") or name
                            md_lines.append(f"- **Executed Tool:** `{name}` — *{summary}*")
                        md_lines.append("\n")

                i += 1
            md_lines.append("\n---\n")
            continue
        i += 1

    os.makedirs(CHAT_SESSIONS_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Saved {prompt_counter} prompts and replies to:\n  {output_path}")

    # Check for implementation plan in this session
    plan_file = os.path.join(session_brain_dir, "implementation_plan.md")
    if os.path.exists(plan_file):
        os.makedirs(PLANS_DIR, exist_ok=True)
        dest_plan = os.path.join(PLANS_DIR, f"PLAN_{date_str}_{label or short_id}.md")
        shutil.copy2(plan_file, dest_plan)
        print(f"Backed up implementation plan to:\n  {dest_plan}")

    # Check for walkthrough in this session
    walkthrough_file = os.path.join(session_brain_dir, "walkthrough.md")
    if os.path.exists(walkthrough_file):
        os.makedirs(WALKTHROUGHS_DIR, exist_ok=True)
        dest_wt = os.path.join(WALKTHROUGHS_DIR, f"WALKTHROUGH_{date_str}_{label or short_id}.md")
        shutil.copy2(walkthrough_file, dest_wt)
        print(f"Backed up walkthrough to:\n  {dest_wt}")

    # Trigger OS desktop notification if notify-send is available
    try:
        subprocess.run([
            "notify-send",
            "-u", "normal",
            "-i", "document-save",
            "Antigravity History Archive",
            f"Successfully archived session {short_id} ({prompt_counter} prompts) to project_history!"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    return output_path

if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else None
    lbl = sys.argv[2] if len(sys.argv) > 2 else None
    export_conversation(cid, lbl)
