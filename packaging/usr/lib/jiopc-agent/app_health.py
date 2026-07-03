#!/usr/bin/env python3
import subprocess
import time
from typing import Dict, Any, Tuple
import psutil

def _launch_application(binary: str, arguments: list) -> subprocess.Popen:
    """Launches the application and returns the Popen process object."""
    cmd = [binary] + arguments
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # We start a new session so child processes are cleanly isolated
        start_new_session=True
    )

def _wait_for_application(process: subprocess.Popen, timeout_ms: int) -> Tuple[str, str]:
    """Waits for the application to confirm it is running.
    
    Checks the process state every ~100ms.
    """
    start_time = time.perf_counter()
    timeout_sec = timeout_ms / 1000.0
    
    try:
        ps_proc = psutil.Process(process.pid)
    except psutil.NoSuchProcess:
        return "FAIL", "Immediate crash."

    while (time.perf_counter() - start_time) < timeout_sec:
        if process.poll() is not None:
            return "FAIL", "Application exited during startup."
            
        try:
            if ps_proc.is_running():
                return "PASS", "Application launched successfully."
        except psutil.NoSuchProcess:
            return "FAIL", "Application exited during startup."
            
        time.sleep(0.1)
        
    return "FAIL", "Startup timeout exceeded."

def _cleanup_process(process: subprocess.Popen) -> None:
    """Terminates the process and its children cleanly to avoid orphans."""
    children = []
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
    except Exception:
        pass

    # Ensure no background processes are left running (e.g., wrapper scripts spawning main apps)
    # Terminate children first to avoid them being orphaned when parent dies
    for child in children:
        try:
            if child.is_running():
                child.terminate()
                child.wait(timeout=1.0)
        except psutil.TimeoutExpired:
            try:
                child.kill()
                child.wait(timeout=1.0)
            except Exception:
                pass
        except Exception:
            pass

    if process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2.0)
        except Exception:
            pass

def run_app_health(config: Dict[str, Any], logger: Any) -> int:
    """Runs health checks on configured native applications.
    
    Returns:
        int: The total number of failed health checks.
    """
    failures = 0
    apps = config.get("native_apps") or []
    
    for app in apps:
        start_time = time.perf_counter()
        name = app.get("name", "Unknown")
        binary = app.get("binary", "")
        
        arguments = app.get("arguments", [])
        if not isinstance(arguments, list):
            arguments = []
            
        timeout_ms = app.get("startup_timeout_ms", 5000)
        if not isinstance(timeout_ms, int) or timeout_ms < 0:
            timeout_ms = 5000
        
        result = "PASS"
        detail = ""
        process = None
        
        try:
            process = _launch_application(binary, arguments)
            result, detail = _wait_for_application(process, timeout_ms)
        except FileNotFoundError:
            result = "FAIL"
            detail = "Executable not found."
        except PermissionError:
            result = "FAIL"
            detail = "Permission denied."
        except Exception as e:
            result = "FAIL"
            detail = f"Unexpected exception: {e}"
            
        if process is not None:
            _cleanup_process(process)
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        if result == "FAIL":
            failures += 1
            
        logger.log(
            component="B",
            test_name=name,
            result=result,
            duration_ms=duration_ms,
            detail=detail
        )
        
        print(f"[B] {name}: {result} — {detail}")
        
    return failures
