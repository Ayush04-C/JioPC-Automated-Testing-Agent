#!/usr/bin/env python3
import argparse
import sys
import traceback
import yaml
from pathlib import Path
from typing import Dict, Any, Callable

from analyse import run_analysis
from app_health import run_app_health
from desktop_auditor import run_desktop_audit
from logger import Logger
from web_tester import run_web_tests

def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="JioPC Validation Agent Runner")
    parser.add_argument("--config", type=str, default="config/jiopc-agent.yaml", help="Path to YAML config file")
    parser.add_argument("--part", type=str, choices=["A", "B", "C"], help="Specific part to run (A, B, or C)")
    parser.add_argument("--analyse", action="store_true", help="Run LLM analysis on log")
    return parser.parse_args()

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    path = Path(config_path)
    if not path.is_file():
        print(f"Error: Configuration file not found at '{config_path}'.")
        sys.exit(1)
        
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    
    logger = Logger(config["agent"]["log_dir"])
    
    dispatch_map: Dict[str, Callable[[Dict[str, Any], Logger], int]] = {
        "A": run_web_tests,
        "B": run_app_health,
        "C": run_desktop_audit
    }
    
    parts_to_run = [args.part] if args.part else config["agent"]["parts_order"]
    total_failures = 0
    
    for part in parts_to_run:
        if part not in dispatch_map:
            print(f"Warning: Unknown part '{part}' specified. Skipping.")
            continue
            
        runner_func = dispatch_map[part]
        
        try:
            failures = runner_func(config, logger)
            total_failures += failures
        except Exception as e:
            detail_msg = f"{type(e).__name__}: {e}"
            logger.log(
                component=part,
                test_name="UnexpectedError",
                result="FAIL",
                duration_ms=0,
                detail=detail_msg
            )
            total_failures += 1

    logger.write_summary()
    
    if args.analyse:
        run_analysis(logger.log_path)
        
    sys.exit(0 if total_failures == 0 else 1)

if __name__ == "__main__":
    main()
