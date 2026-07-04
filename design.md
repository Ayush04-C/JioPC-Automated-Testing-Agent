# System Architecture & Design Document

## 1. Problem Statement

JioPC provides a powerful Desktop-as-a-Service (DaaS) infrastructure built on Ubuntu 24.04 LTS and the LxQt environment. As the operating system receives frequent image patches, manual validation of core components (such as pre-installed native applications, web app shortcuts, and desktop menu integrity) becomes extremely time-consuming and prone to human error. A broken application shortcut or a crashing background service can severely degrade the end-user experience, but these issues are notoriously difficult to catch programmatically across a full graphical environment.

The `jiopc-testing-agent` solves this by providing a unified, automated validation suite. By packaging Web (Part A), Native Process (Part B), and XDG Desktop (Part C) validation logic into a single modular framework, engineers can instantly verify the structural integrity of a new OS patch. Furthermore, by passing the highly structured JSONL logs through an LLM analysis layer, the system removes the burden of manually parsing logs, instantly providing a human-readable `PROMOTE` or `HOLD` recommendation for production deployment.

## 2. Architecture Diagram

```text
[ ENGINEER TERMINAL OR CI/CD PIPELINE ]
         │
         ▼  (jiopc-agent --config jiopc-agent.yaml --analyse)
┌────────────────────────────────────────────────────────┐
│               jiopc_agent.py (Runner Core)             │
│                                                        │
│   Reads → config/jiopc-agent.yaml                      │
└──────┬────────────────────┬────────────────────┬───────┘
       │                    │                    │
┌──────▼─────┐       ┌──────▼─────┐       ┌──────▼─────┐
│   Part A   │       │   Part B   │       │   Part C   │
│ web_tester │       │ app_health │       │desktop_aud │
│(Playwright)│       │  (psutil)  │       │  (PyXDG)   │
└──────┬─────┘       └──────┬─────┘       └──────┬─────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  JSONL File Logger                     │
│  Writes → ~/.local/share/jiopc/agent/test_run_*.log    │
└───────────────────────────┬────────────────────────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ analyse.py (LLM Layer)  │   │ trend_analyser.py (Hist) │
│ Reads JSONL + Prompt    │   │ Reads history.json       │
│ Returns PROMOTE/HOLD    │   │ Detects Regressions      │
└────────────┬────────────┘   └────────────┬─────────────┘
             │                             │
             └──────────────┬──────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│               mailer.py (SMTP Dispatcher)              │
│       Emails the combined analysis to Admins           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
           [ TERMINAL OUTPUT OR GITHUB PR COMMENT ]
```

## 3. Component Design

### Part A: Web Application Testing (`web_tester.py`)
* **What it does:** Uses a headless Chromium browser to navigate to Jio web application URLs, verifying HTTP status codes and ensuring the correct visual elements (nav bars, logos) render in the DOM. Handles bot-detection interceptions securely.
* **Key design decision:** We use Playwright over Selenium because Playwright handles JavaScript-heavy Single Page Applications (SPAs) dynamically, preventing false-negative "missing element" errors caused by race conditions.
* **Input/Output:** Reads `web_apps` from the YAML config. Outputs JSON lines containing `PASS`, `FAIL`, or `BLOCKED`.
* **Bot Protection Handling:** Cloudflare and WAF protections on Jio domains actively block headless browsers. The agent elegantly detects `403`/`429` or challenge pages and flags them as `BLOCKED` rather than `FAIL`, preventing false-positive regressions in headless CI pipelines.

### Part B: Native App Health (`app_health.py`)
* **What it does:** Launches native desktop applications inside an isolated `Xvfb` display server. Monitors the process tree for crashes, timeouts, or unexpected terminations.
* **Key design decision:** We chose `psutil` because it can track entire process hierarchies. Many Linux GUI apps spawn worker children; `psutil` ensures we cleanly kill the entire tree, preventing orphan processes from leaking RAM.
* **Input/Output:** Reads `native_apps` from the YAML config. Outputs JSON lines containing `PASS`, `FAIL`, or `DEGRADED`.

### Part C: Desktop Presence (`desktop_auditor.py`)
* **What it does:** Scans standard XDG directories (like `/usr/share/applications`) for `.desktop` files. Validates that the file exists, has correct execution permissions, and is categorized into the right start menu folder.
* **Key design decision:** Directly parsing standard desktop spec files using `PyXDG` avoids brittle Regex matching, fully complying with Linux Desktop spec standards.
* **Input/Output:** Reads `desktop_presence` from YAML. Outputs JSON lines containing `PASS`, `MISSING`, or `MISPLACED`.

### Runner Core (`jiopc_agent.py`)
* **What it does:** Provides the CLI interface, parses arguments, acts as the central orchestrator for A, B, and C, and manages safe file I/O for the logs.
* **Key design decision:** Separating the orchestration from the execution means developers can work on Part A, B, and C independently without merge conflicts.
* **Input/Output:** Accepts CLI args (`--part`, `--analyse`). Outputs the final JSONL summary block.

### LLM Analysis Layer (`analyse.py`)
* **What it does:** Reads the raw JSONL log and feeds it into an LLM via a structured prompt to generate a non-technical summary and a release recommendation.
* **Key design decision:** Uses environment variables (`LLM_BASE_URL`) to allow seamless hot-swapping between different AI providers (OpenAI, Groq, local Ollama) without changing code, ensuring zero vendor lock-in.
* **Input/Output:** Takes a log file path. Outputs a Markdown-formatted diagnostic report.

### Trend Analyser (`trend_analyser.py`) (Bonus)
* **What it does:** Maintains a rolling history of the last 5 test runs in `history.json`. Compares the current run against the previous run to explicitly identify regressions (e.g. PASS → FAIL), recoveries, and consistent failures.
* **Key design decision:** Trend data survives across VM reassignments because it is written to the user's NFS-mounted `~/.local/share/jiopc/agent/` directory, directly supporting JioPC's floating VM architecture.

### SMTP Mailer (`mailer.py`) (Bonus)
* **What it does:** Dispatches the final LLM report directly to designated administrator emails using SMTP.
* **Key design decision:** Highly configurable via the YAML configuration file and `.env` password integration to prevent credential leakage.

## 4. YAML Schema

All test rules are governed by a central, zero-code YAML file. 

* **`agent` fields:** Core configurations (e.g., `log_retention_days`).
* **`email` fields:** Target addresses and SMTP routing details for the notification dispatcher.
* **`web_apps` fields (Part A):**
  * `name`: Display name of the web application.
  * `url`: The target URL to test.
  * `load_timeout_ms`: Maximum time allowed before aborting.
  * `bot_detection_expected`: Boolean flag for expected cloudflare/WAF walls.
  * `elements`: A list of CSS selectors (e.g. `img[alt*='logo']`) the browser must find in the DOM.
* **`native_apps` fields (Part B):**
  * *(Placeholder for Daksh)* Contains execution paths, timeout requirements, and expected process names.
* **`desktop_presence` fields (Part C):**
  * *(Placeholder for Daksh)* Contains expected XDG categories and absolute paths to standard `.desktop` files.

## 5. Technology Choices

* **Python 3.11+:** Natively available on Ubuntu 24.04 LTS. Provides a rich, unified ecosystem for system automation, HTTP requests, and text parsing.
* **Playwright + Chromium:** Headless by default, offers incredibly stable auto-waiting element selectors, precise load-timing APIs, and handles modern JS-heavy web apps far better than traditional scrapers.
* **psutil:** Provides cross-platform OS visibility, allowing us to accurately track process tree CPU/RAM (VmRSS) and send clean termination signals.
* **PyXDG:** Safely parses `.desktop` files according to the strict Freedesktop.org specifications, specifically handling multi-language `Categories=` fields reliably.
* **OpenAI SDK with base_url:** Ensures the LLM analysis component is model-agnostic. We can point it to any provider serving an OpenAI-compatible spec (which is currently the industry standard).
* **JSON Lines (JSONL) Log Format:** Each line is independently parseable. This allows streaming, prevents catastrophic log corruption if a test crashes mid-write, and is extremely easy for LLMs to read.
* **YAML Config:** Highly human-readable, allows for inline comments, and supports multi-document files. It centralizes test parameters so that QA testers can add tests without touching Python code.
* **GitHub Actions (CI/CD Bonus):** Provides seamless, event-driven CI/CD integration. We trigger the full agent automatically on PRs, catching broken code and bot-protection blocks before they hit `main`.

## 6. Constraints

The system was architected strictly around the following hackathon requirements:
* **No root at runtime:** The agent is packaged as root, but `jiopc-agent` is executed exclusively in user space.
* **No system file modifications:** Tests only read data; nothing is mutated.
* **User space output:** All test artifacts strictly output to `~/.local/share/jiopc/agent/`.
* **Headless execution:** Part A runs in an invisible Chromium instance.
* **No CAPTCHA solving:** Captchas are detected and elegantly flagged as `BLOCKED`.
* **Process hygiene:** Part B implements graceful SIGTERM/SIGKILL cleanup via psutil.
* **Performance caps:** Total run time constrained to < 5 minutes; agent processes are throttled to ensure CPU < 20% sustained and RAM < 150MB.

## 7. Known Limitations

1. **Jio URLs:** The advanced bot protection on Jio domains means Part A will likely always report `BLOCKED` in a headless environment. The LLM has been explicitly instructed to expect this, but it limits deep-page validation.
2. **Network Dependency at Install:** Installing the `.deb` file requires internet access to download Playwright's ~300MB Chromium binaries. An entirely offline air-gapped installation is not currently supported.
3. **Unsolvable Captchas:** Part A cannot (and explicitly will not) attempt to solve CAPTCHAs. Tests end instantly at the challenge wall.
4. **Xvfb Display Quirks (Part B):** Native apps that depend heavily on window manager geometries or hardware GPU acceleration may crash or behave unpredictably when trapped inside the virtual `Xvfb` display buffer used during testing. 
5. **LLM Diagnostics Requirements:** The `--analyse` reporting phase requires active internet access and valid API credentials. A failure at this stage will safely degrade back to the raw log file without crashing the main application.
