# JioPC Testing Agent - Workflow

## 1. Workflow Overview

The JioPC Testing Agent follows a sequential execution pipeline beginning with user invocation and ending with automated reporting. Each stage of the workflow has a clearly defined responsibility and communicates with the next stage through structured data rather than direct coupling.

The workflow is designed to ensure that every execution follows the same predictable lifecycle regardless of which validation modules are enabled.

---

# 2. End-to-End Execution Flow

```
User / CI Pipeline
        │
        ▼
Execute jiopc-agent
        │
        ▼
Parse CLI Arguments
        │
        ▼
Load YAML Configuration
        │
        ▼
Initialize Logger
        │
        ▼
Determine Validation Parts
        │
        ▼
Execute Validation Modules
(A / B / C)
        │
        ▼
Collect Results
        │
        ▼
Write Execution Summary
        │
        ▼
(Optional)
Run Trend Analysis
        │
        ▼
(Optional)
Run LLM Analysis
        │
        ▼
(Optional)
Send Email Report
        │
        ▼
Exit
```

---

# 3. Detailed Workflow

## Step 1 — User Invocation

Execution begins when the user launches the testing agent from the terminal.

Example:

```bash
jiopc-agent --config jiopc-agent.yaml --analyse
```

The command-line interface allows the user to:

- specify a custom configuration file
- execute only selected validation modules
- enable or disable LLM analysis

At this point no validation has started.

---

## Step 2 — Configuration Loading

The Runner Core loads the YAML configuration file.

The configuration defines:

- agent settings
- web applications
- native applications
- desktop launchers
- notification settings

If the configuration cannot be loaded or parsed, execution stops immediately.

---

## Step 3 — Logger Initialization

A shared Logger instance is created before any validation begins.

The logger:

- creates a new JSONL log file
- initializes execution counters
- prepares component statistics
- timestamps every future event

All validation modules receive this same logger instance.

---

## Step 4 — Validation Scheduling

The Runner determines which validation modules should execute.

This depends on:

- the `parts_order` defined in the YAML configuration
- optional `--part` command-line arguments

Each selected module is executed independently while sharing the same configuration and logger.

---

## Step 5 — Web Application Validation (Part A)

The Web Tester validates every configured web application.

For each application it performs:

1. Launch headless Chromium
2. Navigate to target URL
3. Wait for page load
4. Detect bot-protection pages
5. Verify required DOM elements
6. Record the result

Possible outcomes include:

- PASS
- FAIL
- BLOCKED

Each result is immediately written to the JSONL log.

---

## Step 6 — Native Application Validation (Part B)

The Native App Health module validates installed desktop applications.

For every configured application it:

1. launches the executable
2. monitors process startup
3. waits for successful initialization
4. detects crashes or startup failures
5. terminates all spawned processes

Possible outcomes include:

- PASS
- FAIL

Each result is recorded through the shared logger.

---

## Step 7 — Desktop Presence Validation (Part C)

The Desktop Auditor verifies Linux desktop integration.

For every configured launcher it:

1. searches standard application directories
2. locates the corresponding `.desktop` file
3. parses launcher metadata
4. validates application type
5. validates menu category

Possible outcomes include:

- PASS
- MISSING
- MISPLACED

Results are appended to the execution log.

---

## Step 8 — Summary Generation

Once all validation modules finish execution, the Logger writes a final summary.

The summary contains:

- total validations
- overall pass count
- failure count
- blocked count
- missing launchers
- misplaced launchers
- component-wise statistics

This marks the completion of the validation phase.

---

## Step 9 — Trend Analysis (Optional)

If enabled, the Trend Analyzer compares the current execution against historical validation data.

It identifies:

- newly introduced failures
- recovered applications
- recurring failures
- long-term execution trends

This information provides additional context beyond the current execution.

---

## Step 10 — LLM Analysis (Optional)

When the `--analyse` flag is provided, the completed JSONL log is processed by the LLM Analysis module.

The module:

1. loads the prompt template
2. reads the execution log
3. injects the log into the prompt
4. calls the configured language model
5. generates a human-readable report

The report summarizes:

- detected issues
- likely causes
- deployment recommendation
- production readiness

---

## Step 11 — Email Notification (Optional)

If email notifications are configured, the generated report is delivered to the configured recipients.

This enables automated reporting after every execution without requiring manual log inspection.

---

## Step 12 — Program Termination

The application exits after all requested stages have completed.

Exit codes follow standard UNIX conventions:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Validation completed successfully |
| 1 | One or more validation failures occurred |

---

# 4. Information Flow

Throughout execution, information flows in one direction.

```
Configuration
      │
      ▼
Runner Core
      │
      ▼
Validation Modules
      │
      ▼
Shared Logger
      │
      ▼
JSONL Log
      │
      ├────────► Trend Analysis
      │
      ├────────► LLM Analysis
      │
      └────────► Email Notification
```

This unidirectional flow minimizes coupling between modules and makes the system easier to maintain and extend.

---

# 5. Workflow Characteristics

The execution workflow was designed around several key principles.

- **Sequential orchestration** ensures deterministic execution.
- **Independent validation modules** prevent failures in one component from affecting others.
- **Centralized logging** provides a single source of truth.
- **Configuration-driven execution** enables flexible test selection.
- **Optional post-processing** keeps validation independent from reporting.
- **Graceful error handling** allows execution to continue whenever possible, ensuring maximum diagnostic information is collected during each run.