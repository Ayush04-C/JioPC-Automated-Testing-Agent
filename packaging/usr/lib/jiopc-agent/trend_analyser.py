#!/usr/bin/env python3
import json
import os
import logging
import datetime
import pathlib
import argparse
from typing import Dict, List, Any, Tuple, TypedDict, Optional

# ==========================================
# CONFIG
# ==========================================
HISTORY_FILE = os.path.expanduser("~/.local/share/jiopc/agent/history.json")
MAX_RUNS = 5
CONSISTENT_FAIL_THRESHOLD = 3
LOG_PATH = os.path.expanduser("~/.local/share/jiopc/agent/trend_analyser.log")

# ==========================================
# LOGGING SETUP
# ==========================================
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# TYPE DEFINITIONS
# ==========================================
class RunRecord(TypedDict):
    run_id: str
    log_file: str
    summary: Dict[str, Any]
    results: Dict[str, str]

class TrendReport(TypedDict):
    regressions: List[Dict[str, str]]
    recoveries: List[Dict[str, str]]
    new_failures: List[Dict[str, str]]
    consistent_fails: List[Dict[str, Any]]
    total_runs_analysed: int
    has_regressions: bool

# ==========================================
# PRIVATE FUNCTIONS
# ==========================================
def _load_history() -> dict:
    default_history = {"runs": [], "max_runs": MAX_RUNS, "last_updated": None}
    try:
        if not os.path.exists(HISTORY_FILE):
            return default_history
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "runs" not in data:
                logger.warning(f"Corrupt history file at {HISTORY_FILE}. Starting fresh.")
                return default_history
            return data
    except Exception as e:
        logger.warning(f"Failed to load history file: {e}. Starting fresh.")
        return default_history

def _save_history(history: dict) -> None:
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        temp_file = HISTORY_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        os.replace(temp_file, HISTORY_FILE)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")

def _parse_log_file(log_path: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    summary_dict = {}
    results_dict = {}
    summary_found = False
    
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                if obj.get("summary"):
                    summary_dict = obj
                    summary_found = True
                else:
                    test_name = obj.get("test_name")
                    result = obj.get("result")
                    if test_name and result:
                        results_dict[test_name] = result
            except Exception:
                pass
                
    if not summary_found:
        raise ValueError(f"No summary block found in {log_path}")
        
    return summary_dict, results_dict

def _add_run_to_history(history: dict, log_path: str) -> dict:
    summary, results = _parse_log_file(log_path)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    run_record: RunRecord = {
        "run_id": now,
        "log_file": log_path,
        "summary": summary,
        "results": results
    }
    
    runs = history.get("runs", [])
    runs.insert(0, run_record)
    
    if len(runs) > MAX_RUNS:
        runs = runs[:MAX_RUNS]
        
    history["runs"] = runs
    history["last_updated"] = now
    
    return history

def _detect_regressions(current: Dict[str, str], previous: Dict[str, str]) -> List[Dict[str, str]]:
    regressions = []
    for test_name, curr_res in current.items():
        prev_res = previous.get(test_name)
        if curr_res == "FAIL" and prev_res == "PASS":
            regressions.append({
                "test_name": test_name,
                "previous": "PASS",
                "current": "FAIL"
            })
    return regressions

def _detect_recoveries(current: Dict[str, str], previous: Dict[str, str]) -> List[Dict[str, str]]:
    recoveries = []
    for test_name, curr_res in current.items():
        prev_res = previous.get(test_name)
        if curr_res == "PASS" and prev_res in ("FAIL", "DEGRADED", "MISSING", "MISPLACED"):
            recoveries.append({
                "test_name": test_name,
                "previous": prev_res,
                "current": "PASS"
            })
    return recoveries

def _detect_new_failures(current: Dict[str, str], previous: Dict[str, str]) -> List[Dict[str, str]]:
    new_fails = []
    for test_name, curr_res in current.items():
        if curr_res == "FAIL" and test_name not in previous:
            new_fails.append({
                "test_name": test_name,
                "result": "FAIL"
            })
    return new_fails

def _detect_consistent_fails(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(runs) < CONSISTENT_FAIL_THRESHOLD:
        return []
        
    recent_runs = runs[:CONSISTENT_FAIL_THRESHOLD]
    all_tests = set(recent_runs[0].get("results", {}).keys())
    
    consistent_fails = []
    for test_name in all_tests:
        appears_in_all = all(test_name in r.get("results", {}) for r in recent_runs)
        if appears_in_all:
            fails_in_all = all(r.get("results", {}).get(test_name) == "FAIL" for r in recent_runs)
            if fails_in_all:
                # Find oldest run where it failed
                oldest_run_id = recent_runs[-1].get("run_id")
                consistent_fails.append({
                    "test_name": test_name,
                    "consecutive_fails": len(recent_runs),
                    "first_seen": oldest_run_id
                })
                
    return consistent_fails

# ==========================================
# PUBLIC FUNCTIONS
# ==========================================
def run_trend_analysis(log_path: str) -> TrendReport:
    """
    Process a new test run log, update history, and detect trends.
    """
    try:
        log_path_str = str(log_path)
        history = _load_history()
        history = _add_run_to_history(history, log_path_str)
        _save_history(history)
        
        runs = history.get("runs", [])
        total_runs = len(runs)
        
        report: TrendReport = {
            "regressions": [],
            "recoveries": [],
            "new_failures": [],
            "consistent_fails": [],
            "total_runs_analysed": total_runs,
            "has_regressions": False
        }
        
        if total_runs <= 1:
            logger.info("First run recorded. Baseline established.")
            return report
            
        current_results = runs[0].get("results", {})
        previous_results = runs[1].get("results", {})
        
        regressions = _detect_regressions(current_results, previous_results)
        recoveries = _detect_recoveries(current_results, previous_results)
        new_failures = _detect_new_failures(current_results, previous_results)
        consistent_fails = _detect_consistent_fails(runs)
        
        report["regressions"] = regressions
        report["recoveries"] = recoveries
        report["new_failures"] = new_failures
        report["consistent_fails"] = consistent_fails
        report["has_regressions"] = len(regressions) > 0
        
        logger.info(f"{len(regressions)} regressions, {len(recoveries)} recoveries, {len(consistent_fails)} consistent fails")
        return report
        
    except Exception as e:
        logger.error(f"Failed to run trend analysis: {e}")
        return {
            "regressions": [],
            "recoveries": [],
            "new_failures": [],
            "consistent_fails": [],
            "total_runs_analysed": 0,
            "has_regressions": False
        }

def format_trend_report(report: TrendReport) -> str:
    """
    Format a TrendReport as a human-readable string for printing.
    """
    total = report.get("total_runs_analysed", 0)
    
    header = (
        "============================================================\n"
        "TREND ANALYSIS REPORT\n"
        f"Runs analysed: {total} (max history: {MAX_RUNS})\n"
        "============================================================"
    )
    
    if total <= 1:
        return f"{header}\n\nFirst run recorded. Baseline established. No trend data yet.\n"
        
    lines = [header, ""]
    
    regressions = report.get("regressions", [])
    if regressions:
        lines.append(f"🔴 REGRESSIONS ({len(regressions)}) — Tests that were PASS and are now FAIL:")
        for r in regressions:
            lines.append(f"  - {r['test_name']}: PASS → FAIL")
        lines.append("")
        
    recoveries = report.get("recoveries", [])
    if recoveries:
        lines.append(f"🟢 RECOVERIES ({len(recoveries)}) — Tests that were failing and now PASS:")
        for r in recoveries:
            lines.append(f"  - {r['test_name']}: {r['previous']} → PASS")
        lines.append("")
        
    new_fails = report.get("new_failures", [])
    if new_fails:
        lines.append(f"🆕 NEW FAILURES ({len(new_fails)}) — FAIL tests not seen in previous run:")
        for r in new_fails:
            lines.append(f"  - {r['test_name']}")
        lines.append("")
        
    consistent = report.get("consistent_fails", [])
    if consistent:
        lines.append(f"⚠️  CONSISTENT FAILURES ({len(consistent)}) — FAIL for {CONSISTENT_FAIL_THRESHOLD}+ runs:")
        for c in consistent:
            lines.append(f"  - {c['test_name']}: failed {c['consecutive_fails']} consecutive runs")
            lines.append(f"    (first seen failing: {c['first_seen']})")
        lines.append("")
        
    lines.append("VERDICT:")
    if regressions:
        lines.append(f"ACTION REQUIRED: {len(regressions)} regression(s) detected")
    elif not regressions and not consistent:
        lines.append("No regressions. System stable.")
    elif not regressions and consistent:
        lines.append(f"No new regressions. {len(consistent)} known persistent failure(s).")
        
    lines.append("")
    lines.append("============================================================")
    
    return "\n".join(lines)

# ==========================================
# CLI ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse trends across JioPC test agent runs")
    parser.add_argument("--log", required=True, help="Path to the current run log file to process")
    parser.add_argument("--history", default=HISTORY_FILE, help=f"Path to history file (default: {HISTORY_FILE})")
    args = parser.parse_args()
    
    HISTORY_FILE = args.history
    
    report = run_trend_analysis(args.log)
    print(format_trend_report(report))
