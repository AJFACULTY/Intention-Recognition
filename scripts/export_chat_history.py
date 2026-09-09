#!/usr/bin/env python3
"""
Chat History & Reply Exporter for Antigravity IDE
-------------------------------------------------
Extracts full conversations (user prompts + agent replies + actions)
from Antigravity's internal transcript JSONL logs and converts them into
human-readable, permanent Markdown files in the workspace docs/ folder.
"""

import os
import sys
import json
import glob
from datetime import datetime

BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
WORKSPACE_DOCS = "/home/j/ros2_cognition_ws/docs"

def find_latest_conversations(limit=5):
    """List recent conversation folders sorted by modification time."""
    subdirs = [d for d in glob.glob(os.path.join(BRAIN_DIR, "*")) if os.path.isdir(d)]
    subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return subdirs[:limit]

def export_conversation(conv_id, output_path=None):
    transcript_file = os.path.join(BRAIN_DIR, conv_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found at {transcript_file}")
        return None

    if output_path is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(WORKSPACE_DOCS, f"SESSION_PROMPTS_AND_CHAT_HISTORY_{date_str}_{conv_id[:8]}.md")

    print(f"Parsing transcript: {transcript_file}")
    with open(transcript_file, "r", encoding="utf-8") as f:
        steps = [json.loads(line) for line in f if line.strip()]

    print(f"Total steps found: {len(steps)}")

    md_lines = []
    md_lines.append(f"# INTERACTIVE SESSION & CHAT REPLIES ARCHIVE")
    md_lines.append(f"**Session ID:** `{conv_id}`  ")
    md_lines.append(f"**Exported At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    md_lines.append(f"**Workspace:** `/home/j/ros2_cognition_ws`  ")
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
            # Clean up metadata wrapper if present
            if "<USER_REQUEST>" in content:
                user_req = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            else:
                user_req = content
                
            timestamp = step.get("created_at", "")
            md_lines.append(f"### Prompt {prompt_counter} ({timestamp})\n")
            md_lines.append(f"#### 👤 User Request:\n")
            md_lines.append(f"> {user_req.replace(chr(10), chr(10) + '> ')}\n\n")
            md_lines.append(f"#### 🤖 Agent Replies & Actions:\n")
            
            # Gather subsequent agent responses and actions until next user input
            i += 1
            while i < len(steps) and steps[i].get("type") != "USER_INPUT":
                s = steps[i]
                s_type = s.get("type")
                
                # Check for agent textual responses (replies)
                if s_type == "PLANNER_RESPONSE":
                    resp_content = s.get("content")
                    if resp_content and resp_content.strip():
                        md_lines.append(f"{resp_content.strip()}\n\n")
                    
                    # Also log tool calls made by the planner
                    tool_calls = s.get("tool_calls", [])
                    if tool_calls:
                        for tc in tool_calls:
                            name = tc.get("name", "")
                            args = tc.get("args", {})
                            summary = args.get("toolSummary") or args.get("Description") or name
                            md_lines.append(f"- **Executed Tool:** `{name}` — *{summary}*")
                        md_lines.append("\n")

                elif s_type == "CODE_ACTION":
                    pass # Handled in tool summaries
                    
                i += 1
            md_lines.append("\n---\n")
            continue
        i += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Successfully exported {prompt_counter} prompts and replies to:\n  {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    else:
        # Default to the crashed session
        target_id = "9109f32e-1531-414e-a1f9-70edaf7d8110"

    export_conversation(target_id)
