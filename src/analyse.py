#!/usr/bin/env python3
"""
Owner: Ayush — LLM analysis script
"""
import argparse
import os

# CONFIG
PROMPT_FILE_PATH = "/usr/lib/jiopc-agent/prompts/analyse_log.txt"
DEV_PROMPT_PATH = "../prompts/analyse_log.txt"
LOG_PLACEHOLDER = "{{LOG_CONTENT}}"
ENV_BASE_URL = "LLM_BASE_URL"
ENV_MODEL = "LLM_MODEL"
ENV_API_KEY = "LLM_API_KEY"

def _load_prompt_template(prompt_path: str) -> str:
    pass

def _inject_log(template: str, log_content: str) -> str:
    pass

def _call_llm(prompt: str) -> str:
    pass

def run_analysis(log_path: str) -> str:
    """
    Read log file, inject into prompt template, call LLM API,
    return the LLM response as a string.
    Reads LLM config from environment variables:
        LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
    Uses openai Python SDK with configurable base_url so it works
    with any OpenAI-compatible endpoint.
    """
    # TODO: Ayush implements
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze jiopc-agent logs with LLM.")
    parser.add_argument("--log", required=True, help="Path to the log file to analyze")
    args = parser.parse_args()
    
    result = run_analysis(args.log)
    print(result)
