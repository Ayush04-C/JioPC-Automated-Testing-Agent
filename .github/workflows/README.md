# JioPC Testing Agent CI/CD Pipeline

## What This Pipeline Does

The GitHub Actions pipeline automatically triggers on every Pull Request to the repository. It spins up a clean, ephemeral Ubuntu 24.04 environment and installs the JioPC testing agent dependencies. The pipeline then runs the web validation suite (Part A), securely calls the OpenAI API to analyze the JSON Lines log file via the agent's internal LLM module, and automatically extracts and posts the test counts and the LLM recommendation directly as a comment on the Pull Request. This gives engineers immediate AI-powered feedback on whether the OS patch is safe to promote.

## Trigger Conditions

The CI/CD pipeline is designed to execute automatically on:
- **Pull Requests:** Whenever a PR is opened, reopened, or when new commits are synchronized to an open PR targeting `main`.
- **Manual Trigger:** The workflow supports `workflow_dispatch`, allowing developers to manually run the pipeline from the GitHub Actions UI for testing or demonstration purposes.

## Pipeline Steps

| Step | Name | What it does |
|------|------|--------------|
| 1 | Checkout | Clones the repository code into the runner |
| 2 | Python setup | Installs Python 3.11 |
| 3 | System deps | Installs underlying system requirements (`xvfb`, `xdg-utils`, `wmctrl`) |
| 4 | Python deps | Installs all required pip packages including `playwright` and `openai` |
| 5 | Playwright | Downloads headless Chromium and its OS-level dependencies (`--with-deps`) |
| 6 | Log dir | Creates `~/.local/share/jiopc/agent/` to safely capture test logs |
| 7 | Run agent | Executes the testing agent (Part A) and captures the standard output |
| 8 | Find log | Automatically locates the latest JSONL generated log file by timestamp |
| 9 | LLM analysis | Runs `analyse.py` against the log file with the OpenAI API |
| 10 | Extract summary | Uses Python to safely parse the `summary: true` block for pass/fail counts |
| 11 | PR comment | Uses `actions/github-script` to post the extracted metrics and LLM report to the PR |
| 12 | Check result | Forcefully fails the pipeline if any `FAIL` results are detected |

## Required GitHub Secrets

To allow the pipeline to securely communicate with the LLM without exposing credentials in the public codebase, the following repository secret must be configured:

| Secret name | What it is | Where to set it |
|-------------|------------|-----------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM analysis | GitHub repo → Settings → Secrets and variables → Actions → New repository secret |

## How to Read the PR Comment

When the pipeline posts the automated PR comment, it provides a comprehensive overview:
- ✅ **Green (PASS):** Indicates that all executed tests passed successfully (or were safely blocked).
- ❌ **Red (FAIL):** Indicates that at least one functional failure was detected during the run.
- **BLOCKED Results:** These are explicitly expected for Jio URLs (like JioSaavn, JioCloud) that sit behind Cloudflare/Bot protection when accessed via headless Chromium. They **do not** indicate failures.
- **LLM Analysis:** This section contains the deep-dive diagnostic report and states the clear **PROMOTE** or **HOLD** recommendation from the AI.

## What `GITHUB_TOKEN` is

The `GITHUB_TOKEN` is a special authentication token automatically provided by GitHub Actions at runtime. No manual setup is needed. It is strictly used in Step 11 (`actions/github-script`) to authenticate the bot to post the PR comment on your behalf. Because the workflow file explicitly sets `permissions: pull-requests: write`, the token operates securely and with least-privilege.

## Running Manually

If you need to trigger a test run without opening a Pull Request:
1. Go to your GitHub repository and click the **Actions** tab.
2. Select **JioPC Testing Agent** from the left-hand sidebar.
3. Click the **Run workflow** dropdown on the right side.
4. Select your target branch and click the green **Run workflow** button.

---

> **Note on Scope:**
> The CI pipeline runs Part A (web testing) only. Parts B and C require the JioPC Gold Image environment with pre-installed native applications and desktop folder structure. To run the full agent including all three components, use a JioPC VM or an Ubuntu 24.04 + LxQt environment with the Gold Image installed.
> 
> Full run command (on JioPC VM):
> `jiopc-agent --config /usr/lib/jiopc-agent/config/jiopc-agent.yaml --analyse`
