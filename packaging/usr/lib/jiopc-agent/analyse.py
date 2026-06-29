#!/usr/bin/env python3
"""
Owner: Ayush — LLM Analysis Layer
"""
import openai
import os
import sys
import argparse
import logging
import pathlib

PROMPT_FILE_PATH = "/usr/lib/jiopc-agent/prompts/analyse_log.txt"
DEV_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../prompts/analyse_log.txt")
LOG_PLACEHOLDER = "{{LOG_CONTENT}}"
ENV_BASE_URL = "LLM_BASE_URL"
ENV_MODEL = "LLM_MODEL"
ENV_API_KEY = "LLM_API_KEY"
DEFAULT_MAX_TOKENS = 2000

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def _load_prompt_template() -> str:
    if os.path.exists(PROMPT_FILE_PATH):
        path = PROMPT_FILE_PATH
    elif os.path.exists(DEV_PROMPT_PATH):
        path = DEV_PROMPT_PATH
    else:
        raise FileNotFoundError(f"Prompt template not found at {PROMPT_FILE_PATH} or {DEV_PROMPT_PATH}")
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _load_log_file(log_path: str) -> str:
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    if not content:
        raise ValueError("Log file is empty")
        
    return content

def _inject_log(template: str, log_content: str) -> str:
    if LOG_PLACEHOLDER not in template:
        raise ValueError(f"Placeholder {LOG_PLACEHOLDER} not found in prompt template.")
    return template.replace(LOG_PLACEHOLDER, log_content)

def _get_llm_config() -> tuple[str, str, str]:
    # Attempt to load from .env file
    env_path = os.path.join(os.path.dirname(__file__), "../.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
                    
    base_url = os.environ.get(ENV_BASE_URL)
    model = os.environ.get(ENV_MODEL)
    api_key = os.environ.get(ENV_API_KEY)
    
    missing = []
    if not base_url: missing.append(ENV_BASE_URL)
    if not model: missing.append(ENV_MODEL)
    if not api_key: missing.append(ENV_API_KEY)
    
    if missing:
        print(f"ERROR: Missing required environment variables for LLM configuration: {', '.join(missing)}")
        sys.exit(1)
        
    return base_url, model, api_key

def _call_llm(prompt: str, base_url: str, model: str, api_key: str) -> str:
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=DEFAULT_MAX_TOKENS
        )
        msg = response.choices[0].message
        content = msg.content
        
        # Fallback for alternative providers (e.g., BharatCode reasoning models)
        if not content:
            reasoning = getattr(msg, "reasoning", None)
            if reasoning:
                content = f"[Reasoning Process]\n{reasoning}"
            else:
                content = str(msg)
                
        return content
    except Exception as e:
        raise e

def run_analysis(log_path: str) -> str:
    """
    Read a jiopc-agent log file, inject it into the prompt template,
    call the configured LLM, and return the analysis as a string.
    
    Called two ways:
    1. Directly by CLI: run_analysis(args.log)
    2. By Daksh's runner: from analyse import run_analysis
    
    Args:
        log_path: absolute or relative path to the log file
    
    Returns:
        str: the LLM's analysis response
    
    Raises:
        FileNotFoundError: if log file or prompt file missing
        SystemExit: if LLM env vars not set
    """
    template = _load_prompt_template()
    log_content = _load_log_file(log_path)
    prompt = _inject_log(template, log_content)
    base_url, model, api_key = _get_llm_config()
    
    print(f"Analysing log with {model}...")
    response = _call_llm(prompt, base_url, model, api_key)
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyse a jiopc-agent log file using an LLM"
    )
    parser.add_argument("--log", required=True, 
                        help="Path to the log file to analyse")
    args = parser.parse_args()
    
    result = run_analysis(args.log)
    print("\n" + "="*60)
    print("LLM ANALYSIS RESULT")
    print("="*60)
    print(result)
