# Installation Guide

This guide will walk you through building and installing the **JioPC Automated Testing Agent** on an Ubuntu 24.04 system.

## 1. Prerequisites

Before installing the agent, ensure your system meets the following requirements:
*   **Operating System:** Ubuntu 24.04 LTS (LxQt environment recommended but not strictly required for headless testing).
*   **Network Access:** An active internet connection (required to download the Playwright Chromium binaries).
*   **Permissions:** You must have `sudo` access to install the Debian package. Running the actual agent operates entirely in user-space without root access.

## 2. Build the Package

The testing agent is professionally packaged as a `.deb` file. To build the package from the source code, run this command from the root of the repository:

```bash
dpkg-deb --build packaging/ jiopc-testing-agent.deb
```

## 3. Install the Package

We use the `apt` package manager instead of basic `dpkg` to ensure that all required system dependencies (like `xvfb` and `python3-pip`) are automatically downloaded from Ubuntu's servers.

```bash
sudo apt --reinstall install ./jiopc-testing-agent.deb
```

**What this does:**
1. Installs all required OS packages.
2. Installs Python libraries (`playwright`, `psutil`, `PyXDG`, `openai`, `yaml`) into your user environment.
3. Downloads the Chromium headless browser engine (~300MB). *This step may take a few minutes depending on your internet connection.*
4. Exposes the `jiopc-agent` command globally to your terminal.

## 4. Verify Installation

Once the installation finishes, test that the command line tool responds:
```bash
jiopc-agent --help
```

## 5. Configure the LLM (Optional but Recommended)

The agent features an AI diagnostic layer. Before running the `--analyse` flag, you must provide API credentials. 

The easiest way to do this is to create a `.env` file in your current working directory or your home directory (`~/.env`):

```bash
# Create a .env file
nano ~/.env
```

Paste the following inside, replacing with your actual credentials:
```env
LLM_BASE_URL="https://bharatcode.ai/api/model/v1"
LLM_MODEL="bharatcode:qwen36-35b-q6-256k-vision"
LLM_API_KEY="your-api-key"

# Bonus: If you want to enable automatic SMTP emails, add your password here
SMTP_PASS="your_email_password"
```

## 6. Run the Agent

You are now ready to run tests. Choose one of the commands below depending on what you want to do:

**Test only web apps (fastest test):**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --part A
```

**Run the full test suite (A, B, and C):**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml
```

**Run the full test suite AND generate an AI report:**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --analyse
```

**Run a specific part AND generate an AI report for it:**
```bash
jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --part B --analyse
```

## 7. Finding and Interpreting Logs

Every test generates a detailed JSON Lines (`.jsonl`) log file. 
Logs are safely written in user-space to comply with system constraints:
`~/.local/share/jiopc/agent/`

To view the most recent log file:
```bash
cd ~/.local/share/jiopc/agent/
cat $(ls -t log_*.jsonl | head -n 1)
```

## 8. Run Benchmarks

To verify the agent is operating within constraints (<150MB RAM, <20% CPU), run the benchmark script directly from the source code repository:
```bash
python3 benchmarks/run_benchmark.py
```

## 9. Uninstall

If you ever need to completely remove the agent from your system, run:
```bash
sudo dpkg -r jiopc-testing-agent
```
