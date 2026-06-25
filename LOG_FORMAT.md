# LOG FORMAT CONTRACT

This document outlines the agreed-upon log format for the `jiopc-testing-agent`. Both Part A (Ayush) and Part B/C (Daksh) will use this exact format. Neither contributor is allowed to change this contract without notifying the other.

## Log Structure
The log file uses the JSON Lines format (JSONL).
- One JSON object per line.
- Each line is independently parseable.

## Entry Fields
Every log entry must contain exactly these fields:

- `timestamp` (string): ISO 8601 UTC string (e.g., `"2026-06-25T12:00:00Z"`)
- `component` (string): Either `"A"`, `"B"`, or `"C"`
- `test_name` (string): App name or URL being tested
- `result` (string): Exactly one of:
  - `"PASS"`
  - `"FAIL"` (Test executed but didn't pass criteria)
  - `"BLOCKED"` (Test couldn't execute, e.g., bot detection, network block)
  - `"DEGRADED"`
  - `"MISSING"`
  - `"MISPLACED"`
- `duration_ms` (integer): How long this test took in milliseconds
- `detail` (string): One-line human-readable explanation

**BLOCKED vs FAIL distinction:**
- `FAIL`: The app loaded, but an expected element wasn't there.
- `BLOCKED`: The app didn't even load, or threw a Captcha/Cloudflare error before we could test anything.

## Summary Block
The final line of the log is a summary block, which is also a JSON object:
```json
{
  "summary": true,
  "total": 10,
  "pass": 8,
  "fail": 1,
  "blocked": 1,
  "degraded": 0,
  "missing": 0,
  "misplaced": 0,
  "component_breakdown": {
    "A": {"pass": 5, "fail": 1, "blocked": 1},
    "B": {"pass": 2, "fail": 0, "degraded": 0},
    "C": {"pass": 1, "missing": 0, "misplaced": 0}
  }
}
```

## Example Log File
```json
{"timestamp": "2026-06-25T10:00:00Z", "component": "A", "test_name": "Google", "result": "PASS", "duration_ms": 1200, "detail": "All elements found."}
{"timestamp": "2026-06-25T10:00:02Z", "component": "A", "test_name": "JioSaavn", "result": "BLOCKED", "duration_ms": 8500, "detail": "Cloudflare bot detection triggered."}
{"timestamp": "2026-06-25T10:00:05Z", "component": "B", "test_name": "Calculator", "result": "PASS", "duration_ms": 300, "detail": "Process started successfully."}
{"summary": true, "total": 3, "pass": 2, "fail": 0, "blocked": 1, "degraded": 0, "missing": 0, "misplaced": 0, "component_breakdown": {"A": {"pass": 1, "fail": 0, "blocked": 1}, "B": {"pass": 1, "fail": 0, "degraded": 0}, "C": {"pass": 0, "missing": 0, "misplaced": 0}}}
```
