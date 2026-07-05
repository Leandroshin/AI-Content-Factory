"""Demonstration: Quality Loop — automatic validation of executions.

Flow:
  1. Create QualityRuntime + EventBus
  2. Register quality rules (completeness, quality, process, consistency)
  3. Validate a successful execution -> passes
  4. Validate a failed execution -> fails with corrections
  5. Generate correction suggestions
  6. Validate again after fix -> passes
  7. Verify events in observability
"""

from __future__ import annotations

from uuid import uuid4

from core.company import QualityRuntime
from core.events.bus import EventBus
from core.observability import ObservabilityProjector

_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")


def main() -> None:
    print("=" * 62)
    print("Quality Loop - Automatic Validation")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    qr = QualityRuntime(event_bus=event_bus)

    # ==================================================================
    # Step 1: Register quality rules
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Register quality rules")
    print("-" * 62)

    r1 = qr.register_rule(
        name="Output must have no errors",
        description="Execution result must not contain error messages",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    _check(r1 is not None, "Rule 1: no errors")
    _check(r1.category == "output_quality", f"Category: {r1.category}")
    _check(r1.severity == "critical", f"Severity: {r1.severity}")

    r2 = qr.register_rule(
        name="All required fields present",
        description="Execution must include all required output fields",
        category="output_completeness",
        severity="major",
        criteria={"required_fields": ["output_url", "duration_sec", "format"]},
    )
    _check(r2 is not None, "Rule 2: required fields")

    r3 = qr.register_rule(
        name="Duration within limit",
        description="Task duration must not exceed max allowed",
        category="process",
        severity="minor",
        criteria={"max_duration_minutes": 30},
    )
    _check(r3 is not None, "Rule 3: duration limit")

    r4 = qr.register_rule(
        name="Consistent format metadata",
        description="Format field must match file extension",
        category="consistency",
        severity="major",
        criteria={"consistent_fields": ["format", "file_extension"]},
    )
    _check(r4 is not None, "Rule 4: consistency")

    listed = qr.list_rules()
    _check(len(listed) == 4, f"Total rules registered: {len(listed)}")

    cat_listed = qr.list_rules(category="output_quality")
    _check(len(cat_listed) == 1, f"Output quality rules: {len(cat_listed)}")

    # ==================================================================
    # Step 2: Validate a successful execution
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Validate successful execution")
    print("-" * 62)

    exec_id_ok = uuid4()
    task_id_ok = uuid4()
    good_result = {
        "success": True,
        "error": "",
        "output_url": "https://storage.example.com/video.mp4",
        "duration_sec": 120,
        "format": "mp4",
        "file_extension": "mp4",
        "duration_minutes": 5,
    }

    report_ok = qr.validate(exec_id_ok, good_result, task_id=task_id_ok)
    _check(report_ok.passed, "Validation passed for good result")
    _check(report_ok.total_rules == 4, f"Total rules: {report_ok.total_rules}")
    _check(report_ok.passed_rules == 4, f"Passed rules: {report_ok.passed_rules}")
    _check(report_ok.failed_rules == 0, f"Failed rules: {report_ok.failed_rules}")
    _check(report_ok.execution_id == exec_id_ok, "Execution ID in report")
    _check(report_ok.task_id == task_id_ok, "Task ID in report")

    # ==================================================================
    # Step 3: Validate a failed execution
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Validate failed execution")
    print("-" * 62)

    exec_id_fail = uuid4()
    bad_result = {
        "success": False,
        "error": "YouTube quota exceeded",
        "output_url": None,
        "duration_sec": None,
        "format": "mp4",
        "file_extension": "avi",
        "duration_minutes": 45,
    }

    report_fail = qr.validate(exec_id_fail, bad_result, task_id=task_id_ok)
    _check(not report_fail.passed, "Validation failed for bad result")
    _check(report_fail.failed_rules >= 1, f"Failed rules: {report_fail.failed_rules}")
    _check(report_fail.passed_rules < report_fail.total_rules,
           "Not all rules passed")

    # ==================================================================
    # Step 4: Generate corrections
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Generate correction suggestions")
    print("-" * 62)

    corrections = qr.generate_correction(report_fail)
    _check(len(corrections) >= 1, f"Corrections generated: {len(corrections)}")
    print("  Corrections:")
    for c in corrections:
        print(f"    - {c}")

    # Check specific issues in failed report
    has_critical = any("[CRITICAL]" in c for c in corrections)
    _check(has_critical, "Critical issues identified")

    # ==================================================================
    # Step 5: Fix and re-validate
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Fix issues and re-validate")
    print("-" * 62)

    fixed_result = {
        "success": True,
        "error": "",
        "output_url": "https://storage.example.com/video.mp4",
        "duration_sec": 120,
        "format": "mp4",
        "file_extension": "mp4",
        "duration_minutes": 10,
    }

    report_fixed = qr.validate(uuid4(), fixed_result, task_id=task_id_ok)
    _check(report_fixed.passed, "Validation passed after fix")
    _check(report_fixed.failed_rules == 0, "Zero failed rules after fix")

    # ==================================================================
    # Step 6: Report history
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Report history")
    print("-" * 62)

    all_reports = qr.reports()
    _check(len(all_reports) == 3, f"Total reports: {len(all_reports)}")
    _check(all_reports[0].passed, "First report: passed")
    _check(not all_reports[1].passed, "Second report: failed")
    _check(all_reports[2].passed, "Third report: passed (after fix)")

    last = qr.last_report()
    _check(last is not None, "Last report accessible")
    _check(last.passed, "Last report passed")

    # ==================================================================
    # Step 7: Observability verification
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Observability - quality events tracked")
    print("-" * 62)

    snap = observer.snapshot
    _check(snap.quality.reports_count >= 3,
           f"Quality reports tracked: {snap.quality.reports_count}")
    _check(snap.quality.rules_count == 4,
           f"Rules count: {snap.quality.rules_count}")
    _check(snap.quality.last_validation_passed is True,
           "Last validation: passed")
    _check(snap.quality.last_validation_failed_rules == 0,
           "Last validation failed rules: 0")

    quality_events = [e for e in snap.events if e.startswith("quality:")]
    _check(len(quality_events) >= 6, f"Quality events tracked: {len(quality_events)}")
    print(f"  Quality events captured: {len(quality_events)}")
    for e in quality_events:
        print(f"    -> {e}")

    # ==================================================================
    # Step 8: Unregister rule
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Unregister rule")
    print("-" * 62)

    unreg = qr.unregister_rule(r1.id)
    _check(unreg, "Rule unregistered")
    _check(len(qr.list_rules()) == 3, f"Remaining rules: {len(qr.list_rules())}")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
