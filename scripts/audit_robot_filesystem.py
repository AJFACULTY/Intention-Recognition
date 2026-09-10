#!/usr/bin/env python3
"""
High-Speed Comprehensive Robot Filesystem & Architecture Auditor (v2 - High Performance)
Executes localized container Python workers to scan host and container filesystems in seconds.
Captures:
- Host metadata & hardware devices (USB, serial, video, disk, memory, network).
- Complete file trees & SHA256 checksums of /home/pi.
- Full code/text contents of all scripts, launch files, configs (.py, .sh, .yaml, etc.).
- Inside containers ('yahboom_gesture', 'yahboom_base'): scans all src packages, models, launch files.
- Generates:
  1. /home/pi/bot_full_audit.txt  (Human-readable comprehensive audit report)
  2. /home/pi/bot_full_audit.json (Structured JSON inventory)
"""

import os
import sys
import json
import hashlib
import subprocess
import datetime
from pathlib import Path

TEXT_EXTENSIONS = {
    '.py', '.sh', '.bash', '.yaml', '.yml', '.json', '.xml', '.txt',
    '.md', '.launch', '.launch.py', '.service', '.conf', '.cfg', '.ini',
    '.env', '.urdf', '.xacro', '.csv', '.sub', '.bashrc', '.profile'
}

EXCLUDE_DIRS = {
    '.cache', '.local', '__pycache__', '.git', '.vscode', '.npm',
    'dist-packages', 'site-packages', 'build', 'install', 'log'
}

def run_cmd(cmd, timeout=30):
    """Run shell command safely and return stdout string."""
    try:
        res = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=timeout
        )
        return res.stdout.strip()
    except Exception as e:
        return f"[ERROR executing '{cmd}']: {e}"

def compute_sha256(filepath):
    """Compute SHA256 checksum of a file."""
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def is_text_file(filepath):
    """Determine if a file is plain text / code."""
    path = Path(filepath)
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS or path.name in {'.bashrc', '.profile', 'start_bench_pipeline.sh'}:
        return True
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(512)
            if b'\x00' in chunk:
                return False
            chunk.decode('utf-8')
            return True
    except Exception:
        return False

def scan_directory(base_dir, max_file_size_mb=5):
    """Recursively scan directory and capture metadata and contents of text files."""
    inventory = []
    base_path = Path(base_dir)
    if not base_path.exists():
        return inventory

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        
        for file in files:
            full_path = Path(root) / file
            if full_path.is_symlink():
                try:
                    target = os.readlink(full_path)
                    inventory.append({
                        "path": str(full_path),
                        "relative_path": str(full_path.relative_to(base_path)),
                        "type": "symlink",
                        "target": target
                    })
                except Exception:
                    pass
                continue

            try:
                stat = full_path.stat()
                size_bytes = stat.st_size
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat()
                sha256 = compute_sha256(full_path) if size_bytes < 25 * 1024 * 1024 else "SKIPPED_TOO_LARGE"
                
                is_text = is_text_file(full_path) and (size_bytes < max_file_size_mb * 1024 * 1024)
                content = None
                if is_text:
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                    except Exception as e:
                        content = f"[ERROR reading content]: {e}"

                inventory.append({
                    "path": str(full_path),
                    "relative_path": str(full_path.relative_to(base_path)),
                    "type": "file",
                    "size_bytes": size_bytes,
                    "mtime_utc": mtime,
                    "sha256": sha256,
                    "is_text": is_text,
                    "content": content
                })
            except Exception as e:
                inventory.append({
                    "path": str(full_path),
                    "error": str(e)
                })

    return inventory

def scan_container_fast(container_name, target_dirs):
    """Executes a single in-container Python worker script to scan files at native speed."""
    status = run_cmd(f"docker inspect -f '{{{{.State.Running}}}}' {container_name}")
    if status != "true":
        return [{"error": f"Container {container_name} is not running"}]

    dirs_arg = " ".join([f"'{d}'" for d in target_dirs])
    
    worker_script = f'''python3 -c "
import os, sys, json, hashlib

TEXT_EXTS = {{'.py', '.sh', '.bash', '.yaml', '.yml', '.json', '.xml', '.txt', '.md', '.launch.py', '.urdf', '.xacro', '.sub'}}
EXCLUDES = {{'.git', '__pycache__', 'build', 'install', 'log'}}

dirs = [{", ".join([repr(d) for d in target_dirs])}]
results = []

for base_dir in dirs:
    if not os.path.exists(base_dir):
        continue
    for root, d_list, files in os.walk(base_dir):
        d_list[:] = [d for d in d_list if d not in EXCLUDES and not d.startswith('.')]
        for f in files:
            p = os.path.join(root, f)
            try:
                sz = os.path.getsize(p)
                ext = os.path.splitext(f)[1].lower()
                is_text = ext in TEXT_EXTS and sz < 200 * 1024
                content = None
                if is_text:
                    try:
                        with open(p, 'r', encoding='utf-8', errors='replace') as fp:
                            content = fp.read()
                    except Exception:
                        content = '[ERROR reading text]'
                
                md5 = 'N/A'
                if sz < 20 * 1024 * 1024:
                    h = hashlib.md5()
                    with open(p, 'rb') as fp:
                        while chunk := fp.read(65536):
                            h.update(chunk)
                    md5 = h.hexdigest()
                else:
                    md5 = 'SKIPPED_LARGE'
                
                results.append({{
                    'path': p,
                    'size_bytes': sz,
                    'md5': md5,
                    'is_code': is_text,
                    'content': content
                }})
            except Exception as e:
                results.append({{'path': p, 'error': str(e)}})

print(json.dumps(results))
"'''

    raw_output = run_cmd(f"docker exec {container_name} {worker_script}", timeout=60)
    try:
        return json.loads(raw_output)
    except Exception as e:
        return [{"error": f"Failed to parse container output: {e}", "raw": raw_output[:500]}]

def main():
    start_time = datetime.datetime.now(datetime.timezone.utc)
    print("==================================================================")
    print("      ROBOT COMPREHENSIVE FILESYSTEM AUDIT (V2 HIGH SPEED)")
    print(f"      Timestamp: {start_time.isoformat()}")
    print("==================================================================")

    audit_data = {
        "metadata": {
            "timestamp_utc": start_time.isoformat(),
            "hostname": run_cmd("hostname"),
            "kernel": run_cmd("uname -a"),
            "os_release": run_cmd("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"),
            "cpu_info": run_cmd("lscpu | grep 'Model name' || uname -m"),
            "memory": run_cmd("free -h"),
            "disk_usage": run_cmd("df -h /"),
            "ip_addresses": run_cmd("hostname -I"),
            "usb_devices": run_cmd("lsusb"),
            "video_devices": run_cmd("ls -l /dev/video* 2>/dev/null || echo 'None'"),
            "serial_devices": run_cmd("ls -l /dev/ttyUSB* /dev/ttyACM* /dev/myserial* 2>/dev/null || echo 'None'"),
            "docker_containers": run_cmd("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'")
        },
        "host_home_pi": [],
        "container_yahboom_gesture": [],
        "container_yahboom_base": [],
        "all_model_files": []
    }

    # 1. Scan Host /home/pi
    print("[1/4] Scanning Host filesystem in /home/pi (excluding build/install caches)...")
    audit_data["host_home_pi"] = scan_directory("/home/pi")
    print(f"      >> Found {len(audit_data['host_home_pi'])} relevant files in /home/pi.")

    # 2. Fast Scan yahboom_gesture container
    print("[2/4] Scanning container 'yahboom_gesture' at native speed...")
    audit_data["container_yahboom_gesture"] = scan_container_fast(
        "yahboom_gesture", 
        ["/root/cognition_ws/src", "/root/cognition_ws/models", "/root"]
    )
    print(f"      >> Found {len(audit_data['container_yahboom_gesture'])} items in yahboom_gesture.")

    # 3. Fast Scan yahboom_base container
    print("[3/4] Scanning container 'yahboom_base' at native speed...")
    audit_data["container_yahboom_base"] = scan_container_fast(
        "yahboom_base", 
        ["/root/yahboomcar_ws/src", "/root/yahboomcar_ws/param", "/root"]
    )
    print(f"      >> Found {len(audit_data['container_yahboom_base'])} items in yahboom_base.")

    # 4. Identify all model files across host & containers
    print("[4/4] Locating all ML model weights across host and containers...")
    find_models_host = run_cmd("find /home/pi -type f \\( -name '*.pkl' -o -name '*.onnx' -o -name '*.pt' -o -name '*.tflite' \\) -exec ls -lh {} + 2>/dev/null").splitlines()
    find_models_gesture = run_cmd("docker exec yahboom_gesture find /root -type f \\( -name '*.pkl' -o -name '*.onnx' -o -name '*.pt' -o -name '*.tflite' \\) -exec ls -lh {} + 2>/dev/null").splitlines()
    audit_data["all_model_files"] = {
        "host_models": find_models_host,
        "yahboom_gesture_models": find_models_gesture
    }

    # Save JSON output
    json_path = "/home/pi/bot_full_audit.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"\n>> JSON report written to: {json_path} ({os.path.getsize(json_path) / 1024:.1f} KB)")

    # Generate Human-Readable Text Report
    txt_path = "/home/pi/bot_full_audit.txt"
    with open(txt_path, "w", encoding="utf-8") as out:
        out.write("================================================================================\n")
        out.write("                  PHYSICAL ROBOT COMPREHENSIVE AUDIT REPORT\n")
        out.write("================================================================================\n")
        out.write(f"Generated at: {audit_data['metadata']['timestamp_utc']}\n")
        out.write(f"Hostname    : {audit_data['metadata']['hostname']}\n")
        out.write(f"Kernel      : {audit_data['metadata']['kernel']}\n")
        out.write(f"OS Release  : {audit_data['metadata']['os_release']}\n")
        out.write(f"IPs         : {audit_data['metadata']['ip_addresses']}\n\n")

        out.write("--- DISK & HARDWARE PERIPHERALS ---\n")
        out.write(f"Disk Usage:\n{audit_data['metadata']['disk_usage']}\n\n")
        out.write(f"Memory:\n{audit_data['metadata']['memory']}\n\n")
        out.write(f"USB Devices:\n{audit_data['metadata']['usb_devices']}\n\n")
        out.write(f"Video Devices:\n{audit_data['metadata']['video_devices']}\n\n")
        out.write(f"Serial Ports:\n{audit_data['metadata']['serial_devices']}\n\n")
        out.write(f"Docker Containers:\n{audit_data['metadata']['docker_containers']}\n\n")

        out.write("================================================================================\n")
        out.write("SECTION 1: ALL MACHINE LEARNING MODEL WEIGHTS ON ROBOT\n")
        out.write("================================================================================\n")
        out.write("[HOST MODELS (/home/pi)]:\n")
        for m in audit_data["all_model_files"]["host_models"]:
            out.write(f"  {m}\n")
        out.write("\n[CONTAINER MODELS (yahboom_gesture)]:\n")
        for m in audit_data["all_model_files"]["yahboom_gesture_models"]:
            out.write(f"  {m}\n")
        out.write("\n")

        out.write("================================================================================\n")
        out.write("SECTION 2: HOST FILES IN /home/pi (SCRIPTS & PACKAGES)\n")
        out.write("================================================================================\n")
        for item in audit_data["host_home_pi"]:
            if item.get("type") == "symlink":
                out.write(f"LINK: {item['relative_path']} -> {item['target']}\n")
            elif item.get("type") == "file":
                out.write(f"\nFILE: {item['path']} ({item.get('size_bytes', 0)} bytes | SHA256: {item.get('sha256', 'N/A')})\n")
                if item.get("content"):
                    out.write("----------------------------------------\n")
                    out.write(item["content"])
                    if not item["content"].endswith("\n"):
                        out.write("\n")
                    out.write("----------------------------------------\n")

        out.write("================================================================================\n")
        out.write("SECTION 3: CONTAINER 'yahboom_gesture' (/root/cognition_ws)\n")
        out.write("================================================================================\n")
        for item in audit_data["container_yahboom_gesture"]:
            out.write(f"\nCONTAINER FILE: {item.get('path', 'N/A')} ({item.get('size_bytes', 0)} bytes | MD5: {item.get('md5', 'N/A')})\n")
            if item.get("content"):
                out.write("----------------------------------------\n")
                out.write(item["content"])
                if not item["content"].endswith("\n"):
                    out.write("\n")
                out.write("----------------------------------------\n")

        out.write("================================================================================\n")
        out.write("SECTION 4: CONTAINER 'yahboom_base' (/root/yahboomcar_ws)\n")
        out.write("================================================================================\n")
        for item in audit_data["container_yahboom_base"]:
            out.write(f"\nCONTAINER FILE: {item.get('path', 'N/A')} ({item.get('size_bytes', 0)} bytes | MD5: {item.get('md5', 'N/A')})\n")
            if item.get("content"):
                out.write("----------------------------------------\n")
                out.write(item["content"])
                if not item["content"].endswith("\n"):
                    out.write("\n")
                out.write("----------------------------------------\n")

    print(f">> Human-readable text report written to: {txt_path} ({os.path.getsize(txt_path) / 1024:.1f} KB)")
    print("==================================================================")
    print("AUDIT COMPLETE! Run on your laptop:")
    print("    scp pi@10.27.122.136:~/bot_full_audit.txt docs/")
    print("    scp pi@10.27.122.136:~/bot_full_audit.json docs/")
    print("==================================================================")

if __name__ == "__main__":
    main()
