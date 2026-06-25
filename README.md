# jiopc-testing-agent

An automated scripted validation agent that tests a freshly patched JioPC OS Image (Ubuntu 24.04 LTS + LxQt desktop). It verifies web applications, native applications, and desktop presence, outputting a consolidated log for LLM analysis.

## Architecture

```text
YAML Config
    │
    ▼
Runner Core (jiopc_agent.py)
    │
    ├──► Part A (Web/URL testing)
    ├──► Part B (Native App Health)
    └──► Part C (Desktop Presence)
    │
    ▼
Log File (JSON Lines format)
    │
    ▼
LLM Analysis (analyse.py)
    │
    ▼
PROMOTE / HOLD Recommendation
```

## Components

| Part | Owner | File | Description |
|---|---|---|---|
| Part A | Ayush | `src/web_tester.py` | Web and URL testing via Playwright headless Chromium |
| Part B | Daksh | `src/app_health.py` | Native app health checks |
| Part C | Daksh | `src/desktop_auditor.py` | Desktop presence checks |
| LLM | Ayush | `src/analyse.py` | LLM analysis layer |
| Runner | Daksh | `src/jiopc_agent.py` | Main orchestrator |

## Quick Start

Run the validation agent:
```bash
jiopc-agent --config config/jiopc-agent.yaml
```

Run LLM analysis:
```bash
python3 src/analyse.py --log ~/.local/share/jiopc/agent/run.log
```

## LLM Configuration

The LLM analysis requires the following environment variables to be set:

- `LLM_BASE_URL`: The base URL for the OpenAI-compatible endpoint.
- `LLM_MODEL`: The model name to use.
- `LLM_API_KEY`: Your API key.

Example:
```bash
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o"
export LLM_API_KEY="sk-..."
```

## Interpreting Logs

Logs are stored in `~/.local/share/jiopc/agent/` in JSON Lines format. Each line represents a test result. Refer to `LOG_FORMAT.md` for the detailed structure.

## Known Limitations

- Runs as standard user; requires no runtime root privileges.
- Assumes a network connection is available for Part A web testing.
