"""Run every demo with one reproducible regression report.

The project historically used different assertion-counting conventions. This
runner treats process success as the regression gate and separately reports
only assertion totals explicitly printed by each demo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ASSERTION_PATTERNS = (
    re.compile(r"All\s+(\d+)\s+assertions passed", re.IGNORECASE),
    re.compile(r"Assertions:\s*(\d+)", re.IGNORECASE),
)


def _explicit_assertions(output: str) -> int | None:
    for pattern in ASSERTION_PATTERNS:
        matches = pattern.findall(output)
        if matches:
            return sum(int(value) for value in matches)
    return None


def _safe_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key.startswith("AI_COMPANY_RUN_REAL_"):
            environment.pop(key, None)
    return environment


def run(root: Path, timeout_seconds: int, report_path: Path) -> int:
    demos = sorted(root.glob("demo_*.py"))
    results: list[dict[str, object]] = []
    environment = _safe_environment()

    for demo in demos:
        started = time.perf_counter()
        try:
            process = subprocess.run(
                [sys.executable, str(demo)],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
            output = "\n".join(part for part in (process.stdout, process.stderr) if part)
            success = process.returncode == 0
            return_code: int | None = process.returncode
            error = ""
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout
            stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else exc.stderr
            output = "\n".join(part for part in (stdout, stderr) if part)
            success = False
            return_code = None
            error = f"timeout after {timeout_seconds}s"

        explicit = _explicit_assertions(output)
        duration = round(time.perf_counter() - started, 3)
        results.append(
            {
                "demo": demo.name,
                "success": success,
                "return_code": return_code,
                "duration_seconds": duration,
                "explicit_assertions": explicit,
                "error": error,
                "failure_tail": output.splitlines()[-40:] if not success else [],
            }
        )
        assertion_label = f" assertions={explicit}" if explicit is not None else ""
        print(f"{'PASS' if success else 'FAIL'} {demo.name}{assertion_label} ({duration:.2f}s)")

    passed = sum(1 for result in results if result["success"])
    failed = len(results) - passed
    counted = [result for result in results if result["explicit_assertions"] is not None]
    explicit_total = sum(int(result["explicit_assertions"]) for result in counted)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.executable,
        "root": str(root),
        "real_execution_environment_removed": True,
        "demos_total": len(results),
        "passed": passed,
        "failed": failed,
        "explicit_assertions_total": explicit_total,
        "demos_with_explicit_assertion_summary": len(counted),
        "demos_without_explicit_assertion_summary": len(results) - len(counted),
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "SUMMARY "
        f"demos={len(results)} passed={passed} failed={failed} "
        f"explicit_assertions={explicit_total} counted_demos={len(counted)} "
        f"report={report_path}"
    )
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all AI Content Factory demos.")
    parser.add_argument("--timeout", type=int, default=300, help="Per-demo timeout in seconds.")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(".ai_company/regression/latest.json"),
        help="JSON report path relative to the repository.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report_path = args.report if args.report.is_absolute() else root / args.report
    return run(root, args.timeout, report_path)


if __name__ == "__main__":
    raise SystemExit(main())
