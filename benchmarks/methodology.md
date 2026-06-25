# Benchmarking Methodology

## What we measure
- CPU% utilization during test execution.
- RAM usage by the validation agent.
- Total run time of the suite.
- Part B overhead per native application.

## How we measure it
- `ps` for process snapshots.
- `/proc` filesystem metrics for real-time memory stats.
- `time` command for total execution duration.

## Results table

| Metric | Run 1 | Run 2 | Run 3 | p50 | p95 |
|---|---|---|---|---|---|
| CPU% | - | - | - | - | - |
| RAM (MB) | - | - | - | - | - |
| Total Time (s) | - | - | - | - | - |
| Part B Overhead (ms) | - | - | - | - | - |

## Part B overhead calculation methodology
Total execution time of Part B minus the baseline process launch time of the underlying native applications.
