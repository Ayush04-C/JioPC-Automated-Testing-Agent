# JioPC Testing Agent - System Architecture

## 1. Overview

The JioPC Testing Agent is a modular validation framework designed to automate quality assurance for JioPC operating system images. Instead of relying on manual verification after every image update, the agent executes a configurable suite of validation tests covering web applications, native desktop applications, and desktop launcher integrity.

The entire system is configuration-driven through a YAML file, allowing new applications or validation rules to be added without modifying the source code. Every execution generates a structured JSON Lines (JSONL) log that serves as the single source of truth for analysis, historical tracking, and automated reporting.

The architecture follows a modular pipeline where each validation component is isolated, making the system easy to maintain, test, and extend.

---

# 2. High-Level Architecture

The system consists of six primary layers:

```
                User / CI Pipeline
                        │
                        ▼
                Runner (CLI Entry)
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Web Tests      Native Tests     Desktop Audit
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 Shared JSON Logger
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
    Trend Analysis              LLM Analysis
          │                           │
          └─────────────┬─────────────┘
                        ▼
                 Email Notification
                        │
                        ▼
                  Final Validation Report
```

---

# 3. Architectural Principles

The project was designed around several guiding principles.

### Modular Components

Each validation domain is implemented independently.

- Part A validates web applications.
- Part B validates native applications.
- Part C validates desktop launcher integrity.

Each module exposes exactly one public entry point, allowing the Runner Core to orchestrate execution without knowing the implementation details.

---

### Configuration Driven

Application definitions are never hardcoded.

Instead, every validation target is described inside a YAML configuration file.

This allows QA engineers to:

- add new applications
- change timeouts
- update selectors
- modify launch commands

without editing Python source code.

---

### Shared Logging Pipeline

Rather than allowing every module to write its own logs, all components communicate through a shared Logger.

This guarantees:

- consistent log format
- unified timestamps
- centralized summaries
- easy downstream processing

The generated JSONL file becomes the single source of truth for the remainder of the pipeline.

---

### Post-Processing Layer

Once testing finishes, additional processing modules consume the generated log.

These modules include:

- Trend Analyzer
- LLM Analyzer
- SMTP Mailer

Since they operate on the log instead of the testing modules directly, new analysis features can be added without changing the validation code.

---

# 4. Component Responsibilities

## Runner Core

Responsible for:

- CLI argument parsing
- configuration loading
- module orchestration
- failure aggregation
- summary generation
- optional analysis execution

The Runner never performs validation itself. Its responsibility is orchestration.

---

## Part A — Web Validation

Uses Playwright with a headless Chromium browser to validate:

- page availability
- HTTP status
- page loading
- expected DOM elements
- bot-detection pages

Results are recorded as:

- PASS
- FAIL
- BLOCKED

---

## Part B — Native Application Validation

Launches native desktop applications and monitors their health using psutil.

Validation includes:

- executable availability
- successful startup
- unexpected crashes
- startup timeout
- graceful cleanup

Results are recorded as:

- PASS
- FAIL

---

## Part C — Desktop Presence Validation

Audits Linux desktop launcher metadata.

Checks include:

- launcher existence
- desktop file parsing
- application type
- category validation

Results are recorded as:

- PASS
- MISSING
- MISPLACED

---

## Shared Logger

Provides a unified logging interface used by every validation component.

Responsibilities include:

- writing JSONL records
- maintaining counters
- component statistics
- execution summary generation

The logger is intentionally isolated so future modules can consume a standardized log format.

---

## Trend Analyzer

Compares the current execution against previous runs stored inside the history database.

It detects:

- regressions
- recoveries
- recurring failures
- execution trends

This enables engineers to identify problems introduced by recent image changes.

---

## LLM Analysis

Reads the completed JSONL log together with a structured prompt.

The language model converts raw validation output into:

- human-readable summaries
- likely root causes
- deployment recommendation
- production readiness assessment

---

## SMTP Mailer

Distributes the generated validation report to configured recipients.

Separating notification logic from validation logic keeps the testing pipeline independent of delivery mechanisms.

---

# 5. Data Storage

The agent stores all execution artifacts inside the user's local data directory.

```
~/.local/share/jiopc/agent/
```

Typical contents include:

- JSONL execution logs
- historical execution database
- generated reports
- archived results

This satisfies the hackathon requirement that no system files are modified during execution.

---

# 6. Configuration Architecture

The YAML configuration file defines every validation target.

Major sections include:

- agent
- web_apps
- native_apps
- desktop_presence
- email

This design keeps the validation engine generic while allowing project-specific behavior to remain inside configuration.

---

# 7. Extensibility

The architecture was intentionally designed for future expansion.

New validation modules can be introduced by:

1. implementing a new runner function
2. registering it inside the Runner dispatch table
3. extending the YAML configuration

No existing validation modules require modification.

This minimizes merge conflicts and encourages independent development.

---

# 8. Design Decisions

Several architectural decisions were made to improve maintainability.

- Modular execution instead of one monolithic script.
- Configuration-driven validation instead of hardcoded logic.
- Shared logger instead of independent log files.
- JSONL storage for easy machine parsing.
- Post-processing architecture separating testing from reporting.
- Provider-independent LLM integration using OpenAI-compatible APIs.

Together, these decisions produce a validation framework that is portable, maintainable, and suitable for continuous integration workflows.