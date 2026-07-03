from typing import Any
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Dict

class Logger:
    """Logs test results to a JSON Lines file."""

    _ALLOWED_RESULTS = {"PASS", "FAIL", "BLOCKED", "DEGRADED", "MISSING", "MISPLACED"}
    _ALLOWED_COMPONENTS = {"A", "B", "C"}

    def __init__(self, log_directory: Union[str, Path]) -> None:
        """Initializes the Logger and creates the log file.

        Args:
            log_directory: The directory where logs will be stored.
            """
        self._log_dir = Path(log_directory).expanduser()
        self._log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._log_file = self._log_dir / f"log_{timestamp}.jsonl"
        
        # Keep a persistent file handle instead of reopening on every write
        self._file = open(self._log_file, "a", encoding="utf-8")

        self._counters = {
            "PASS": 0,
            "FAIL": 0,
            "BLOCKED": 0,
            "DEGRADED": 0,
            "MISSING": 0,
            "MISPLACED": 0
        }

        self._component_breakdown: Dict[str, Dict[str, int]] = {
            "A": {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "DEGRADED": 0, "MISSING": 0, "MISPLACED": 0},
            "B": {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "DEGRADED": 0, "MISSING": 0, "MISPLACED": 0},
            "C": {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "DEGRADED": 0, "MISSING": 0, "MISPLACED": 0}
        }
    
    def __del__(self) -> None:
        """Ensures the file handle is closed."""
        self.close()
    
    def close(self) -> None:
        """Close the log file safely."""
        if hasattr(self, '_file') and not self._file.closed:
            self._file.close()

    @property
    def log_path(self) -> Path:
        """Returns the path to the current log file."""
        return self._log_file

    def _get_utc_timestamp(self) -> str:
        """Generates a UTC ISO8601 timestamp string.

        Returns:
            str: The current UTC time in ISO8601 format without microseconds.
        """
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    def _write_json(self, data: Dict[str, Any]) -> None:
        """Writes a JSON object to the log file as a new line.
        
        Args:
            data: The dictionary to write.
        """
        self._file.write(json.dumps(data) + "\n")
        self._file.flush()

    def log(self, component: str, test_name: str, result: str, duration_ms: int, detail: str) -> None:
        """Logs a test result.

        Args:
            component: The component name ('A', 'B', or 'C').
            test_name: The name of the test.
            result: The test outcome.
            duration_ms: Duration in milliseconds.
            detail: Detailed message.

        Raises:
            ValueError: If the result is not valid, component is invalid, or duration is negative.
        """
        if component not in self._ALLOWED_COMPONENTS:
            raise ValueError(f"Invalid component: {component}")
        if result not in self._ALLOWED_RESULTS:
            raise ValueError(f"Invalid result: {result}")
        if duration_ms < 0:
            raise ValueError(f"Invalid duration_ms: {duration_ms}")

        self._counters[result] += 1
        self._component_breakdown[component][result] += 1

        log_entry = {
            "timestamp": self._get_utc_timestamp(),
            "component": component,
            "test_name": test_name,
            "result": result,
            "duration_ms": duration_ms,
            "detail": detail
        }

        self._write_json(log_entry)

    def write_summary(self) -> None:
        """Writes the final test run summary to the log file."""
        total = sum(self._counters.values())

        summary_data = {
            "summary": True,
            "total": total,
            "pass": self._counters["PASS"],
            "fail": self._counters["FAIL"],
            "blocked": self._counters["BLOCKED"],
            "degraded": self._counters["DEGRADED"],
            "missing": self._counters["MISSING"],
            "misplaced": self._counters["MISPLACED"],
            "component_breakdown": {}
        }

        for comp, counts in self._component_breakdown.items():
            comp_total = sum(counts.values())
            summary_data["component_breakdown"][comp] = {
                "total": comp_total,
                "pass": counts["PASS"],
                "fail": counts["FAIL"],
                "blocked": counts["BLOCKED"],
                "degraded": counts["DEGRADED"],
                "missing": counts["MISSING"],
                "misplaced": counts["MISPLACED"]
            }

        self._write_json(summary_data)
