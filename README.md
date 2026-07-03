# JioPC Automated Testing Agent

An automated validation suite that verifies web apps, native apps, and desktop presence after a JioPC OS Image patch, complete with LLM-powered diagnostic reporting.

## Dependencies & Setup

The agent is designed to run on **Ubuntu 24.04** (or any Debian-based system) and uses standard Linux utilities.

**Core Dependencies:**
*   **Python 3.11+**
*   **Playwright** (`playwright-python` + Chromium) for headless web testing.
*   **psutil** for tracking child process CPU/RAM and window health.
*   **PyXDG** for parsing Linux `.desktop` files.
*   **openai** for communicating with LLMs.
*   **xvfb** (X Virtual Framebuffer) for launching native apps headlessly.

**Installation (Debian Package):**
We have fully packaged the agent into a `.deb` file so all dependencies (including system-level ones like `xvfb`) are automatically installed.

1. **Build the package:**
   ```bash
   dpkg-deb --build packaging/ jiopc-testing-agent.deb
   ```
2. **Install the package:**
   ```bash
   sudo apt --reinstall install ./jiopc-testing-agent.deb
   ```

## How to Run

Once installed, the agent registers a global command on your system (`jiopc-agent`).

**Run the full test suite and LLM analysis in one step:**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --analyse
```

**Run only a specific part (e.g., Part B - Native Apps):**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --part B
```

**Run a specific part AND generate an AI report for it:**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --part B --analyse
```

## How to Configure the LLM Analysis

The LLM analysis layer uses the standard `openai` SDK but is completely decoupled from any specific provider (OpenAI, Groq, BharatCode, Ollama, etc.).

**Configuration via `.env` file (Recommended):**
The agent will automatically hunt for a `.env` file in your current working directory or your home directory (`~/.env`). Create a `.env` file and add the following 3 variables:

```env
# Example: Using an OpenAI-compatible provider like BharatCode
LLM_BASE_URL="https://bharatcode.ai/api/model/v1"
LLM_MODEL="bharatcode:qwen36-35b-q6-256k-vision"
LLM_API_KEY="your-api-key"
```

If you prefer not to use a `.env` file, you can `export` these variables directly into your bash terminal before running the agent.

## Email Summary (Bonus Feature)

The agent can automatically email the final LLM report (Executive Summary and PROMOTE/HOLD recommendation) to administrators using SMTP.

1. **Configure YAML:** Open `config/jiopc-agent.yaml` and set your sender/receiver email addresses in the `agent.email` block.
2. **Set Password:** Add your SMTP password (e.g. Gmail App Password) to your `.env` file:
```env
SMTP_PASS="your_16_char_app_password"
```
When you run with `--analyse`, the email will automatically be dispatched upon completion.

**Testing Email Configuration Locally:**
If you want to quickly test your email configuration without rebuilding the `.deb` package, you can instruct the globally installed agent to read your local config file instead of the system default:
```bash
jiopc-agent --config config/jiopc-agent.yaml --part B --analyse
```

## Logging & How to Interpret Results

### Log Location
All logs are safely written in user-space to comply with system constraints. They are written to:
`~/.local/share/jiopc/agent/`

*(Note: On your VM, if you are logged in as the user `user`, this perfectly expands to `/home/user/.local/share/jiopc/agent/`)*.

### Log Format
The logs are written in **JSON Lines (JSONL)** format, making them highly machine-readable.
*   **Individual Tests:** Each line represents a test execution with `timestamp`, `component`, `test_name`, `result`, and `duration_ms`.
*   **Summary Block:** The absolute last line of the file is always a massive JSON object (`{"summary": true, ...}`) that contains the aggregated totals and a per-component breakdown for Parts A, B, and C.

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

## Benchmarking

To prove that the agent complies with the strict hackathon resource constraints (< 150MB RAM, < 20% CPU), run the included benchmark script:
```bash
python3 benchmarks/run_benchmark.py
```
*(See `benchmarks/METHODOLOGY.md` for full methodology details).*
