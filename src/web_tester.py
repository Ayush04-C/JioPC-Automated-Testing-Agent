#!/usr/bin/env python3
"""
Owner: Ayush — Part A (Web/URL testing)
"""
import logging
import time
import os
import re
import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

# CONFIG
DEFAULT_LOAD_TIMEOUT_MS = 8000
ELEMENT_TIMEOUT_MS = 10000
BOT_DETECTION_SIGNALS = [
    "captcha", "are you human", "verify you are human",
    "cloudflare", "bot check", "access denied", 
    "checking your browser", "ddos protection"
]
LOG_PATH = os.path.expanduser("~/.local/share/jiopc/agent/part_a.log")

# Setup logging
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger_module = logging.getLogger(__name__)

def _check_bot_detection(page: Page) -> bool:
    try:
        content = page.content().lower()
        url = page.url.lower()
        for signal in BOT_DETECTION_SIGNALS:
            if signal in content or signal in url:
                return True
        return False
    except Exception:
        return False

def _check_elements(page: Page, elements: list) -> tuple[bool, list[str]]:
    missing = []
    for el in elements:
        try:
            page.wait_for_selector(el["selector"], timeout=ELEMENT_TIMEOUT_MS)
        except Exception:
            missing.append(el["selector"])
            
    if missing:
        return False, missing
    return True, []

def _measure_load_time(page: Page, url: str, timeout_ms: int) -> tuple[int, bool, int]:
    start = time.time()
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        elapsed_ms = int((time.time() - start) * 1000)
        status_code = response.status if response else 0
        return elapsed_ms, False, status_code
    except PlaywrightTimeoutError:
        return timeout_ms, True, 0
    except Exception as e:
        raise e

def _test_single_url(page: Page, web_app: dict) -> tuple[str, str, int]:
    start_time = time.time()
    try:
        url = web_app["url"]
        load_timeout_ms = web_app.get("load_timeout_ms", DEFAULT_LOAD_TIMEOUT_MS)
        
        load_time_ms, timed_out, status_code = _measure_load_time(page, url, load_timeout_ms)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if timed_out:
            return "FAIL", f"Page timed out after {load_timeout_ms}ms", elapsed_ms
            
        if _check_bot_detection(page):
            return "BLOCKED", "Bot detection page detected", elapsed_ms
            
        if status_code in [403, 429] and web_app.get("bot_detection_expected"):
            return "BLOCKED", f"Bot protection blocked access (HTTP {status_code})", elapsed_ms
            
        if status_code >= 400:
            return "FAIL", f"HTTP Error {status_code} returned", elapsed_ms

        elements = web_app.get("elements", [])
        all_found, missing = _check_elements(page, elements)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if not all_found:
            return "FAIL", f"Missing elements: {', '.join(missing)}", elapsed_ms
            
        detail = f"All {len(elements)} elements found, load={load_time_ms}ms"
        if load_time_ms > load_timeout_ms:
            detail += " (WARNING: load time exceeded timeout)"
            
        return "PASS", detail, elapsed_ms
        
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return "FAIL", f"Unexpected error: {str(e)}", elapsed_ms

def run_web_tests(config: dict, logger) -> int:
    """
    Entry point called by Daksh's jiopc_agent.py runner core.
    
    Args:
        config: full parsed YAML config as Python dict.
                Web apps are at config["web_apps"] — list of dicts.
        logger: shared Logger instance. Call logger.log() for each result.
    
    Returns:
        int: count of FAIL results (0 = all passed or all BLOCKED)
        NOTE: BLOCKED is not counted as a failure.
    """
    web_apps = config.get("web_apps", [])
    failed_count = 0
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for web_app in web_apps:
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = context.new_page()
                    
                    try:
                        result, detail, duration_ms = _test_single_url(page, web_app)
                    except Exception as e:
                        result = "FAIL"
                        detail = f"Uncaught exception: {str(e)}"
                        duration_ms = 0
                    
                    # Call shared logger
                    logger.log(
                        component="A",
                        test_name=web_app.get("name", "Unknown"),
                        result=result,
                        duration_ms=duration_ms,
                        detail=detail
                    )
                    
                    # Print to terminal
                    print(f"[A] {web_app.get('name')}: {result} — {detail}")
                    
                    if result == "FAIL":
                        failed_count += 1
                        
                    context.close()
            finally:
                browser.close()
                
    except Exception as e:
        logger.log(
            component="A",
            test_name="Browser Launch",
            result="FAIL",
            duration_ms=0,
            detail=f"Failed to launch browser: {str(e)}"
        )
        return len(web_apps)

    return failed_count
