#!/usr/bin/env python3
"""
Benchmark script for JioPC Testing Agent.
Methodology: 
- Executes jiopc-agent via subprocess.
- Uses psutil to sample the orchestrator process CPU % and RAM (RSS) every 100ms.
- Calculates p50 (median) and p95 resource metrics.
- Parses the newly generated JSONL log to extract Part B overhead timing per app.
- No root access required.
"""
import subprocess
import psutil
import time
import os
import glob
import json
import statistics
import sys

def main():
    print("==========================================================")
    print(" JioPC Agent - Official Benchmark Tool ")
    print("==========================================================\n")
    print("Methodology: psutil polling at 100ms intervals. No root access required.")
    
    cmd = ["jiopc-agent", "--config", "/usr/lib/jiopc-agent/config/jiopc-agent.yaml"]
    
    print("Executing agent...\n")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        agent_proc = psutil.Process(process.pid)
    except FileNotFoundError:
        print("Error: jiopc-agent not found. Have you installed the .deb package?")
        sys.exit(1)
    
    cpu_samples = []
    ram_samples = []
    
    start_time = time.time()
    
    while process.poll() is None:
        try:
            # CPU% across the interval. RAM RSS in MB.
            cpu_samples.append(agent_proc.cpu_percent(interval=0.1))
            ram_samples.append(agent_proc.memory_info().rss / (1024 * 1024))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
            
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Calculate percentiles
    if cpu_samples:
        cpu_samples.sort()
        cpu_p50 = statistics.median(cpu_samples)
        idx_p95 = int(len(cpu_samples) * 0.95)
        cpu_p95 = cpu_samples[idx_p95] if idx_p95 < len(cpu_samples) else max(cpu_samples)
    else:
        cpu_p50 = cpu_p95 = 0.0
        
    if ram_samples:
        ram_samples.sort()
        ram_p50 = statistics.median(ram_samples)
        idx_p95 = int(len(ram_samples) * 0.95)
        ram_p95 = ram_samples[idx_p95] if idx_p95 < len(ram_samples) else max(ram_samples)
        ram_max = max(ram_samples)
    else:
        ram_p50 = ram_p95 = ram_max = 0.0

    print(f"\n--- Resource Usage Report ---")
    print(f"Full Run Duration : {total_duration:.2f} seconds")
    print(f"Agent CPU (p50)   : {cpu_p50:.2f}%")
    print(f"Agent CPU (p95)   : {cpu_p95:.2f}%")
    print(f"Agent RAM (p50)   : {ram_p50:.2f} MB")
    print(f"Agent RAM (p95)   : {ram_p95:.2f} MB")
    print(f"Agent RAM (Max)   : {ram_max:.2f} MB")
    
    print("\n--- Part B Overhead Per App ---")
    log_dir = os.path.expanduser("~/.local/share/jiopc/agent/")
    list_of_files = glob.glob(f"{log_dir}/log_*.jsonl")
    
    if list_of_files:
        latest_log = max(list_of_files, key=os.path.getctime)
        print(f"Extracted from log: {latest_log}\n")
        
        with open(latest_log, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                if data.get("component") == "B":
                    # Overhead is the duration tracked by the orchestrator for this check
                    print(f"  - {data['test_name']:<20}: {data['duration_ms']} ms overhead")
    else:
        print("No log files found in ~/.local/share/jiopc/agent/")
        
    print("\nBenchmark complete.")

if __name__ == "__main__":
    main()
