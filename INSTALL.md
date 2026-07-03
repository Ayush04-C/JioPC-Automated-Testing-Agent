# Installation Guide

This guide will walk you through installing the **JioPC Automated Testing Agent** on a fresh Linux virtual machine. Every command is written out explicitly for ease of use.

## 1. Prerequisites

Before installing the agent, ensure your system meets the following requirements:
* **Operating System:** Ubuntu 24.04 LTS equipped with the LxQt desktop environment.
* **Network Access:** An active internet connection (required to download the headless Playwright browser during setup).
* **Permissions:** You must have `sudo` (administrator) access to install the package. You will not need `sudo` after installation is complete.

## 2. Installation

We will use the `apt` package manager instead of basic `dpkg`. This ensures that all required system dependencies (like `xvfb`) are automatically downloaded from Ubuntu's servers.

Run this exact command in your terminal:
```bash
sudo apt install ./jiopc-testing-agent.deb
```

**What this does:**
1. Installs all required OS packages (like `xvfb` and `python3-pip`).
2. Installs Python libraries into your user environment.
3. Downloads the Chromium headless browser engine (~300MB). *This step may take a few minutes depending on your internet connection.*
4. Exposes the `jiopc-agent` command to your terminal.

## 3. Verify Installation

Once the installation finishes, you can confirm it worked by running these three commands:

Check if the package manager registered it:
```bash
dpkg -l | grep jiopc
```

Check if the files were successfully placed on your system:
```bash
ls /usr/lib/jiopc-agent/
```

Test that the command line tool responds:
```bash
jiopc-agent --help
```

## 4. Configure LLM

The agent features an AI diagnostic layer. Before running the analysis, you must provide API credentials. 

Run these exact commands in your terminal (replacing `your-openai-api-key-here` with your actual key):
```bash
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL=gpt-4o
export LLM_API_KEY=your-openai-api-key-here
```
*(You can get an API key from the OpenAI Developer Platform. Note: you will need to re-run these `export` commands every time you open a new terminal window, unless you save them permanently in your `.bashrc` or a local `.env` file).*

## 5. Run the Agent

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

## 6. Find the Log File

Every test generates a detailed JSON Lines log file. You can find all your past runs stored safely in your user directory:
```bash
ls ~/.local/share/jiopc/agent/
```
To view the most recent log file:
```bash
cat ~/.local/share/jiopc/agent/test_run_<latest-timestamp>.log
```

## 7. Uninstall

If you ever need to completely remove the agent from your system, simply run:
```bash
sudo dpkg -r jiopc-testing-agent
```

## 8. Troubleshooting

* **`command not found: jiopc-agent`**
  Your terminal might need to be refreshed to see the new command. Simply close the terminal window and open a new one.

* **`ModuleNotFoundError: playwright`**
  Your Python environment may have been modified. Run `pip3 install playwright --break-system-packages` to manually force a reinstall.

* **`LLM_API_KEY not set`**
  You forgot to run the `export` commands from Step 4. Run them in your current terminal window and try again.

* **`Playwright Chromium not found`**
  Your internet connection may have dropped during installation. Run `python3 -m playwright install chromium` to retry the download manually.

* **Part A all results are `BLOCKED`**
  This is 100% expected! Jio domains have advanced bot protection. The headless browser triggers this intentionally. The AI diagnostic layer is specifically programmed to recognize this as a `PASS` for infrastructure health.
