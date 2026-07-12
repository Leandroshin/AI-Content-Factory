"""Demonstration: daily YouTube discovery becomes a safe experiment proposal."""

from datetime import UTC, datetime

from core.content_factory.daily_learning_radar import DailyLearningRadar, LearningCandidate


COUNT = 0


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    print(f"  [{'PASS' if condition else 'FAIL'}] {COUNT:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    ugc = LearningCandidate(
        title="Original AI UGC workflow",
        source_url="https://www.youtube.com/watch?v=example",
        creator="example_creator",
        transcript_text=(
            "Create UGC avatar references with Sora, KIE and Nano Banana. Analyze the hook, "
            "but do not copy the creative. The presenter claims high conversion and faturar results."
        ),
        screenshot_evidence="local://youtube-home/ugc.png",
        relevance=0.95,
        novelty=0.82,
        credibility=0.72,
        actionability=0.94,
        promotional_risk=0.35,
        compliance_risk=0.20,
        tags=("ugc", "avatar", "creative"),
    )
    incomplete = LearningCandidate(
        title="Interesting title only",
        source_url="https://www.youtube.com/watch?v=incomplete",
        relevance=0.90,
        novelty=0.90,
        credibility=0.90,
        actionability=0.90,
    )
    radar = DailyLearningRadar(minimum_score=0.60, max_selected=1)
    report = radar.run((ugc, incomplete), now=datetime(2026, 7, 12, tzinfo=UTC))

    check(report.selected_count == 1, "One bounded experiment selected")
    check(report.rejected_count == 1, "Incomplete source rejected")
    check(not report.no_learning, "Daily report records useful learning")
    selected = next(item for item in report.decisions if item.status == "experiment_proposed")
    check(selected.score >= 0.60, "Selected source clears score threshold")
    check(selected.experiment is not None, "Experiment proposal created")
    experiment = selected.experiment
    assert experiment is not None
    check(experiment.owner_approval_required, "Owner approval remains mandatory")
    check(experiment.estimated_cost_usd == 0.0, "No unapproved provider spend")
    check("image_provider" in experiment.required_providers, "Image provider is a declared dependency")
    check("video_provider" in experiment.required_providers, "Video provider is a declared dependency")
    check(any("likeness" in rule for rule in experiment.guardrails), "Likeness copying is blocked")
    check(any("health" in rule for rule in experiment.guardrails), "Unsupported claims are blocked")
    check(any("measured" in rule for rule in experiment.guardrails), "Promotion requires measured success")
    check(any("marketing claims" in reason for reason in selected.reasons), "Promotional claims are flagged")
    rejected = next(item for item in report.decisions if item.status == "rejected")
    check(any("Transcript" in reason for reason in rejected.reasons), "Missing transcript is explicit")
    check(any("Visual evidence" in reason for reason in rejected.reasons), "Missing screenshot is explicit")

    duplicate = radar.run((ugc,), seen_fingerprints=report.next_seen_fingerprints)
    check(duplicate.duplicate_count == 1, "Previously evaluated source is deduplicated")
    check(duplicate.no_learning, "Duplicate-only run creates no learning")

    print(f"\nAll {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
