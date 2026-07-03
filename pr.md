# 🚀 Feature: Automated Web Testing & LLM Diagnostics (Hackathon Release)

## 📋 Overview
This Pull Request introduces the completed **Part A (Web Testing)** logic alongside a fully functional **LLM Analysis Engine** and an automated `.deb` deployment package. This satisfies all requirements for the JioPC Automated Testing Agent hackathon project, seamlessly orchestrating testing and providing a human-readable `PROMOTE` or `HOLD` recommendation.

## 🛠️ Key Technical Deliverables

### 1. LLM Analysis Engine (`analyse.py` & Prompts)
- **Zero-Dependency Dotenv:** Implemented a native `.env` parser to load `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` without requiring `python-dotenv`.
- **Reasoning Model Support:** Re-architected the OpenAI SDK wrapper to natively support advanced "reasoning" models (like BharatCode/Qwen and DeepSeek R1). The script now gracefully extracts the `reasoning` payload when the standard `content` block is empty.
- **Dynamic Token Boundaries:** Removed artificial `max_tokens` constraints, allowing deep-thinking models enough space to process output before writing the final Markdown report.
- **Structured Prompts:** Finalized `prompts/analyse_log.txt` to strictly enforce a 4-section output rubric (`Executive Summary`, `Failures`, `Patterns`, `Recommendation`) while intelligently recognizing Jio Cloudflare/Bot-walls as an expected `BLOCKED` status rather than a failure.

### 2. Automated `.deb` Packaging (`packaging/`)
- **PEP 668 Compliance:** Hardened the `postinst` script to safely use `--break-system-packages` during the initial setup, ensuring Ubuntu 24.04 environments process the dependencies without throwing externally managed errors.
- **Dynamic User Resolution:** Engineered the `postinst` script to aggressively sniff `$SUDO_USER` and `getent passwd`, guaranteeing that Python dependencies (like Playwright Chromium) and log directories are installed securely into the actual invoking user's home folder, rather than `/root`.
- **Clean Uninstallation:** Added a `prerm` hook to properly remove the global CLI wrapper (`/usr/bin/jiopc-agent`) without destroying the user's localized test logs.
- **Permissions:** Git executable bits (`chmod +x`) are now permanently tracked for the Debian maintainer scripts so that `dpkg-deb --build` succeeds out-of-the-box on fresh clones.

### 3. Comprehensive Documentation (`docs/` -> Root)
- **`README.md`**: Outlined the ASCII data-flow architecture, component ownership, LLM configuration, and benchmark placeholders.
- **`INSTALL.md`**: Created explicit, non-technical instructions for installing the `.deb` package using `apt` (to dynamically resolve `xvfb`) and troubleshooting common missing-dependency edge cases.
- **`design.md`**: Consolidated the overarching technical specifications, justifying technology choices (Playwright, psutil, JSONL) and clearly documenting hackathon constraints (e.g. headless boundaries, memory caps, captcha rules).

## 🧪 Testing Performed
- ✅ Simulated a `PASS` json payload into `/tmp/test.log` and confirmed the LLM engine successfully outputs a highly formatted `PROMOTE` recommendation.
- ✅ Successfully compiled the package (`dpkg-deb --build`) and deployed it using `sudo apt install ./jiopc-testing-agent.deb` on a pristine Ubuntu 24.04 LxQt VM.
- ✅ Verified `jiopc-agent` fires cleanly from the global terminal without triggering Python `ModuleNotFoundError` for `playwright`.

## 🚀 Next Steps (For Daksh)
- Merge this branch into `main`.
- Plug in the Part B and Part C logic into the `jiopc_agent.py` orchestrator's `main()` block!
