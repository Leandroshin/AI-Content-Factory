"""Proof of HyperFrames editorial quality gates and adapter behavior."""

from __future__ import annotations

from uuid import uuid4

from core.departments.video.editorial_quality import (
    EditorialBeat,
    EditorialCaptionCue,
    EditorialChapter,
    EditorialQualityValidator,
    EditorialVideoPlan,
    LongFormRepurposingPlan,
    LongFormRepurposingValidator,
    ShortExtractionCandidate,
)
from core.tools.adapters import HyperFramesRenderAdapter
from core.tools.adapters.models import ToolRequest


def main() -> None:
    validator = EditorialQualityValidator()
    weak = EditorialVideoPlan(duration_seconds=40)
    weak_result = validator.validate(weak)
    assert weak_result.passed is False
    assert "missing_beat_map" in weak_result.issues
    assert "missing_captions" in weak_result.issues
    assert "contact_sheet_missing" in weak_result.issues
    assert weak_result.score < 100

    beats = (
        EditorialBeat(0, 4, "Hook", "motion_graphic", camera_change="zoom_20"),
        EditorialBeat(4, 9, "Source", "source_card", "https://example.com/news", True, "split_screen"),
        EditorialBeat(9, 14, "Context", "broll", camera_change="reset"),
        EditorialBeat(14, 19, "Detail", "motion_graphic", camera_change="zoom_35"),
    )
    captions = (
        EditorialCaptionCue(0, 4, "Saiu uma atualizacao", ("ATUALIZACAO",)),
        EditorialCaptionCue(4, 9, "A fonte oficial confirmou", ("OFICIAL",)),
    )
    strong = EditorialVideoPlan(
        duration_seconds=19,
        beats=beats,
        captions=captions,
        asset_usage=("source", "broll-a", "broll-b", "source"),
        narration_is_primary=True,
        background_audio_gain_db=-24,
        contact_sheet_reviewed=True,
        overflow_checked=True,
        occlusion_checked=True,
        preview_reviewed=True,
        output_variants=("tiktok_9x16", "youtube_shorts_9x16"),
    )
    strong_result = validator.validate(strong)
    assert strong_result.passed is True
    assert strong_result.score == 100.0
    assert strong_result.issues == ()
    assert strong_result.corrections == ()

    adapter = HyperFramesRenderAdapter()
    request = ToolRequest(
        tool_id=uuid4(),
        capability="video_rendering",
        params={
            "action": "render",
            "task_id": "editorial-demo",
            "composition_file_path": "composition.html",
            "quality_standard": "hyperframes_editorial_v1",
        },
    )
    rendered = adapter.execute(request)
    assert rendered.success is True
    assert rendered.output["renderer"] == "hyperframes"
    assert rendered.output["mode"] == "mock"
    assert rendered.output["quality_standard"] == "hyperframes_editorial_v1"
    assert rendered.output["file_path"].endswith("editorial-demo.mp4")
    assert adapter.check_availability() is True
    assert adapter.validate_credentials() is True
    assert adapter.owner_guidance().docs_url == "https://hyperframes.video/docs"

    repurposing = LongFormRepurposingPlan(
        master_duration_seconds=600,
        chapters=(
            EditorialChapter("Update 2.6", 0, 210, ("steam-update-2.6",)),
            EditorialChapter("What changed", 210, 600, ("steam-update-2.6", "developer-notes")),
        ),
        short_candidates=(
            ShortExtractionCandidate(
                title="The biggest change",
                source_chapter="Update 2.6",
                start_time=32,
                end_time=77,
                hook="The update changed the game overnight.",
                payoff="Here is the verified feature that matters.",
                score=91,
            ),
        ),
    )
    repurposing_result = LongFormRepurposingValidator().validate(repurposing)
    assert repurposing_result.passed is True
    assert repurposing_result.score == 100
    assert repurposing_result.issues == ()
    assert len(repurposing.chapters) == 2
    assert len(repurposing.short_candidates) == 1

    arbitrary_crop = LongFormRepurposingPlan(
        master_duration_seconds=600,
        chapters=repurposing.chapters,
        short_candidates=(ShortExtractionCandidate("Crop", "Unknown", 5, 10, "", "", 110),),
    )
    rejected_crop = LongFormRepurposingValidator().validate(arbitrary_crop)
    assert rejected_crop.passed is False
    assert "invalid_short_duration" in rejected_crop.issues
    assert "unknown_source_chapter" in rejected_crop.issues
    assert "short_without_arc" in rejected_crop.issues
    assert "invalid_candidate_score" in rejected_crop.issues
    print("All 28 assertions passed.")


if __name__ == "__main__":
    main()
