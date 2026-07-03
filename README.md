# JioPC Automated Testing Agent
An automated validation suite that verifies web apps, native apps, and desktop presence after a JioPC OS Image patch, complete with LLM-powered diagnostic reporting.

## Architecture

```text
Engineer runs command
      ↓
jiopc_agent.py (runner core)
      ↓ reads
jiopc-agent.yaml (YAML config)
      ↓ runs
┌─────────┬─────────┬─────────┐
│ Part A  │ Part B  │ Part C  │
│  Web    │ Native  │Desktop  │
│ Testing │ Health  │Presence │
└─────────┴─────────┴─────────┘
      ↓ writes
test_run_<timestamp>.log
      ↓
analyse.py → LLM API → PROMOTE / HOLD
```

## Components

| Part | File | What it does |
|------|------|--------------|
| A | `web_tester.py` | Headless Playwright tests for web apps (URL reachability and UI element verification). |
| B | `app_health.py` | Native app launch verification and process health monitoring via `psutil`. |
| C | `desktop_auditor.py` | Validates `.desktop` file presence and start menu categorizations via `PyXDG`. |
| Core | `jiopc_agent.py` | CLI entry point. Orchestrates components A/B/C and writes the structured JSONL log. |
| LLM | `analyse.py` | Reads the structured log, executes LLM analysis, and generates a PROMOTE/HOLD recommendation. |

## Quick Start

```bash
sudo apt install ./jiopc-testing-agent.deb
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml
```

## How to Configure the LLM

The LLM analysis layer uses the standard `openai` SDK but is fully decoupled from any specific provider. It requires 3 environment variables:

```bash
# Example: Using an OpenAI-compatible provider like BharatCode or Groq
export LLM_BASE_URL="https://bharatcode.ai/api/model/v1"
export LLM_MODEL="bharatcode:qwen36-35b-q6-256k-vision"
export LLM_API_KEY="your-api-key"
```

You can point this to OpenAI, Groq, Together AI, local Ollama endpoints, or any standard provider simply by changing the environment variables. The agent also natively parses a local `.env` file if one is present.

## How to Interpret the Log

The system writes logs in standard JSON Lines (JSONL) format.

### Example Entry
```json
{
  "timestamp": "2026-06-22T10:30:00Z",  
  "component": "A",                      
  "test_name": "JioSaavn",              
  "result": "BLOCKED",                  
  "duration_ms": 3421,                  
  "detail": "Bot detection page — Cloudflare challenge"
}
```

### Result Values
| Result | Component | Meaning |
|--------|-----------|---------|
| **PASS** | A, B, C | Test passed, everything as expected. |
| **FAIL** | A, B, C | Test failed (timeout, HTTP error, missing element, process crash). |
| **BLOCKED** | A only | Web page loaded but showed bot/Cloudflare challenge. |
| **DEGRADED** | B only | App launched but crashed before health check completed. |
| **MISSING** | C only | `.desktop` file not found anywhere on the system. |
| **MISPLACED** | C only | `.desktop` file exists but is in the wrong folder/category. |

> **IMPORTANT:** `BLOCKED` is **NOT** a failure. It means a Jio-protected URL triggered expected bot detection in the headless browser. The LLM is explicitly trained to understand this distinction.

## Benchmark Results

| Run | Total Time | Peak CPU% | Peak RAM | Parts Run |
|-----|------------|-----------|----------|-----------|
| 1   | (pending)  | (pending) | (pending)| (pending) |

*(To be populated post-validation benchmarking)*

## Known Limitations

1. **Bot Protection (Part A):** Jio URLs are highly protected. In a headless automated environment, they will almost always return `BLOCKED`. This is handled securely by the LLM logic.
2. **Installation Network Dependency:** Installing the `.deb` package requires internet access to download the ~300MB Chromium binaries for Playwright.
3. **No CAPTCHA Solving:** The agent enforces a strict policy against circumventing captchas. Pages requiring manual human verification will legitimately report as `BLOCKED`.
4. **Display Server Reliance (Part B):** Apps dependent on advanced GPU hardware acceleration or specific window geometry may behave unpredictably inside the headless `Xvfb` display buffer used during testing.
5. **LLM Diagnostics Requirements:** The `--analyse` reporting phase requires active internet and valid API credentials. A failure at this step will safely degrade back to the local raw log file without crashing.
