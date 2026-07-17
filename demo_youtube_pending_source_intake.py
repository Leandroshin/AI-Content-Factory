"""Regression proof for zero-cost YouTube learning-source intake."""

from dataclasses import FrozenInstanceError

from core.intelligence import SourceIntakeStatus, YouTubePendingSourceIntake


def run_demo() -> int:
    assertions = 0
    intake = YouTubePendingSourceIntake()
    urls = (
        "https://www.youtube.com/watch?v=o9L5ihc1jyY&utm_source=test",
        "https://youtu.be/o9L5ihc1jyY",
        "https://m.youtube.com/shorts/o9L5ihc1jyY",
        "https://youtube.com/live/o9L5ihc1jyY",
    )
    sources = tuple(intake.register(url, submitted_at=1_784_244_000.0) for url in urls)
    for source in sources:
        assert source.source_uri == "https://www.youtube.com/watch?v=o9L5ihc1jyY"
        assertions += 1
        assert source.external_id == "o9L5ihc1jyY"
        assertions += 1
        assert source.status == SourceIntakeStatus.PENDING_TRANSCRIPT
        assertions += 1
        assert source.audit_allowed is False and source.learning_allowed is False
        assertions += 2
        assert source.provider_called is False and source.estimated_cost == 0.0
        assertions += 2
        assert len(source.blockers) == 5
        assertions += 1
    assert len({source.fingerprint for source in sources}) == 1
    assertions += 1
    assert len({source.intake_id for source in sources}) == 1
    assertions += 1

    invalid = (
        "http://www.youtube.com/watch?v=o9L5ihc1jyY",
        "https://youtube.example/watch?v=o9L5ihc1jyY",
        "https://www.youtube.com/playlist?list=PL123",
        "https://www.youtube.com/watch?v=o9L5ihc1jyY&list=PL123",
        "https://www.youtube.com/@channel",
        "https://user:pass@youtube.com/watch?v=o9L5ihc1jyY",
    )
    for url in invalid:
        try:
            intake.register(url)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError(f"unsafe URL accepted: {url}")

    try:
        sources[0].source_uri = "https://example.com"  # type: ignore[misc]
    except FrozenInstanceError:
        assertions += 1
    else:
        raise AssertionError("PendingLearningSource must be frozen")

    print(f"YouTube pending source intake demo passed: {assertions} assertions")
    return assertions


if __name__ == "__main__":
    run_demo()
