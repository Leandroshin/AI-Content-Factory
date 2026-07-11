"""Editorial quality contract for agent-authored short and long-form video."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EditorialBeat:
    """One narration beat mapped to a deliberate visual treatment."""

    start_time: float
    end_time: float
    narration: str
    visual_kind: str
    visual_source: str = ""
    source_verified: bool = False
    camera_change: str = "none"


@dataclass(frozen=True, slots=True)
class EditorialCaptionCue:
    """Caption cue with safe-zone and emphasis metadata."""

    start_time: float
    end_time: float
    text: str
    keywords: tuple[str, ...] = field(default_factory=tuple)
    safe_zone: bool = True
    occludes_subject: bool = False


@dataclass(frozen=True, slots=True)
class EditorialEditingProfile:
    """Reusable quality target derived from a proven editing workflow."""

    name: str = "hyperframes_editorial_v1"
    max_uninterrupted_visual_seconds: float = 6.0
    minimum_broll_beats: int = 3
    maximum_asset_reuse: int = 2
    word_level_captions: bool = True
    keyword_emphasis: bool = True
    require_source_provenance: bool = True
    require_contact_sheet: bool = True
    require_overflow_check: bool = True
    require_occlusion_check: bool = True
    require_preview_review: bool = True
    require_clean_audio_priority: bool = True


@dataclass(frozen=True, slots=True)
class EditorialVideoPlan:
    """Evidence consumed by the editorial quality validator."""

    duration_seconds: float
    beats: tuple[EditorialBeat, ...] = field(default_factory=tuple)
    captions: tuple[EditorialCaptionCue, ...] = field(default_factory=tuple)
    asset_usage: tuple[str, ...] = field(default_factory=tuple)
    narration_is_primary: bool = True
    background_audio_gain_db: float = -24.0
    contact_sheet_reviewed: bool = False
    overflow_checked: bool = False
    occlusion_checked: bool = False
    preview_reviewed: bool = False
    output_variants: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EditorialQualityResult:
    """Auditable pass/fail result with direct corrections."""

    passed: bool
    score: float
    issues: tuple[str, ...]
    corrections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EditorialChapter:
    """Auditable chapter boundary in a long-form factual master."""

    title: str
    start_time: float
    end_time: float
    source_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ShortExtractionCandidate:
    """Self-contained short candidate tied to exact master timestamps."""

    title: str
    source_chapter: str
    start_time: float
    end_time: float
    hook: str
    payoff: str
    score: float


@dataclass(frozen=True, slots=True)
class LongFormRepurposingPlan:
    """Chapter map and ranked short candidates for a long-form master."""

    master_duration_seconds: float
    chapters: tuple[EditorialChapter, ...] = field(default_factory=tuple)
    short_candidates: tuple[ShortExtractionCandidate, ...] = field(default_factory=tuple)


class EditorialQualityValidator:
    """Validate pacing, captions, provenance, audio and visual QA evidence."""

    def __init__(self, profile: EditorialEditingProfile | None = None) -> None:
        self._profile = profile or EditorialEditingProfile()

    def validate(self, plan: EditorialVideoPlan) -> EditorialQualityResult:
        issues: list[str] = []
        corrections: list[str] = []

        if plan.duration_seconds <= 0:
            self._add(issues, corrections, "invalid_duration", "Set a positive duration.")
        if not plan.beats:
            self._add(issues, corrections, "missing_beat_map", "Map narration to timed visual beats.")
        else:
            self._validate_beats(plan, issues, corrections)
        self._validate_captions(plan, issues, corrections)
        self._validate_assets(plan, issues, corrections)
        self._validate_audio(plan, issues, corrections)
        self._validate_review_evidence(plan, issues, corrections)

        score = max(0.0, round(100.0 - len(issues) * 8.0, 1))
        return EditorialQualityResult(
            passed=not issues,
            score=score,
            issues=tuple(issues),
            corrections=tuple(corrections),
        )

    def _validate_beats(
        self,
        plan: EditorialVideoPlan,
        issues: list[str],
        corrections: list[str],
    ) -> None:
        sorted_beats = sorted(plan.beats, key=lambda item: item.start_time)
        broll_count = 0
        for beat in sorted_beats:
            if beat.end_time <= beat.start_time:
                self._add(issues, corrections, "invalid_beat_timing", "Fix overlapping or empty beat timing.")
            if beat.end_time - beat.start_time > self._profile.max_uninterrupted_visual_seconds:
                self._add(issues, corrections, "visual_hold_too_long", "Add a purposeful visual change within six seconds.")
            if beat.visual_kind in {"broll", "source_card", "split_screen", "motion_graphic"}:
                broll_count += 1
            if (
                self._profile.require_source_provenance
                and beat.visual_kind in {"source_card", "news_screenshot"}
                and (not beat.visual_source or not beat.source_verified)
            ):
                self._add(issues, corrections, "unverified_source_visual", "Attach and verify the original source URL.")
        if broll_count < self._profile.minimum_broll_beats:
            self._add(issues, corrections, "insufficient_visual_context", "Add at least three contextual visual beats.")

    def _validate_captions(
        self,
        plan: EditorialVideoPlan,
        issues: list[str],
        corrections: list[str],
    ) -> None:
        if not plan.captions:
            self._add(issues, corrections, "missing_captions", "Generate synchronized captions from the final narration.")
            return
        for cue in plan.captions:
            if cue.end_time <= cue.start_time or not cue.text.strip():
                self._add(issues, corrections, "invalid_caption", "Repair empty caption text or timing.")
            if not cue.safe_zone:
                self._add(issues, corrections, "caption_outside_safe_zone", "Move captions into the platform-safe area.")
            if cue.occludes_subject:
                self._add(issues, corrections, "caption_occlusion", "Reposition captions away from faces and evidence.")
            if self._profile.keyword_emphasis and not cue.keywords:
                self._add(issues, corrections, "missing_keyword_emphasis", "Select only meaningful words for emphasis.")

    def _validate_assets(
        self,
        plan: EditorialVideoPlan,
        issues: list[str],
        corrections: list[str],
    ) -> None:
        counts = {asset: plan.asset_usage.count(asset) for asset in set(plan.asset_usage) if asset}
        if any(count > self._profile.maximum_asset_reuse for count in counts.values()):
            self._add(issues, corrections, "asset_overused", "Replace repeated B-roll with a new contextual asset.")

    def _validate_audio(
        self,
        plan: EditorialVideoPlan,
        issues: list[str],
        corrections: list[str],
    ) -> None:
        if self._profile.require_clean_audio_priority and not plan.narration_is_primary:
            self._add(issues, corrections, "narration_not_primary", "Keep narration above music and source audio.")
        if plan.background_audio_gain_db > -12.0:
            self._add(issues, corrections, "background_audio_too_loud", "Lower music/source audio below narration.")

    def _validate_review_evidence(
        self,
        plan: EditorialVideoPlan,
        issues: list[str],
        corrections: list[str],
    ) -> None:
        checks = (
            (self._profile.require_contact_sheet, plan.contact_sheet_reviewed, "contact_sheet_missing", "Review a contact sheet across the full timeline."),
            (self._profile.require_overflow_check, plan.overflow_checked, "overflow_not_checked", "Run text overflow checks."),
            (self._profile.require_occlusion_check, plan.occlusion_checked, "occlusion_not_checked", "Run subject and caption occlusion checks."),
            (self._profile.require_preview_review, plan.preview_reviewed, "preview_not_reviewed", "Watch the rendered preview before delivery."),
        )
        for required, completed, issue, correction in checks:
            if required and not completed:
                self._add(issues, corrections, issue, correction)

    @staticmethod
    def _add(issues: list[str], corrections: list[str], issue: str, correction: str) -> None:
        if issue not in issues:
            issues.append(issue)
            corrections.append(correction)


class LongFormRepurposingValidator:
    """Reject arbitrary crops and preserve context from long master to short."""

    def validate(self, plan: LongFormRepurposingPlan) -> EditorialQualityResult:
        issues: list[str] = []
        corrections: list[str] = []
        if plan.master_duration_seconds <= 0:
            self._add(issues, corrections, "invalid_master_duration", "Set the verified long-form duration.")
        if not plan.chapters:
            self._add(issues, corrections, "missing_chapters", "Divide the master into factual chapters.")

        chapter_names = {chapter.title for chapter in plan.chapters}
        previous_end = 0.0
        for chapter in sorted(plan.chapters, key=lambda item: item.start_time):
            if not chapter.title.strip() or chapter.end_time <= chapter.start_time:
                self._add(issues, corrections, "invalid_chapter", "Repair chapter title and timestamp boundaries.")
            if chapter.start_time < previous_end:
                self._add(issues, corrections, "overlapping_chapters", "Remove chapter timestamp overlap.")
            if chapter.end_time > plan.master_duration_seconds:
                self._add(issues, corrections, "chapter_outside_master", "Keep chapter timestamps inside the master.")
            if not chapter.source_ids:
                self._add(issues, corrections, "chapter_without_sources", "Attach source evidence to each factual chapter.")
            previous_end = max(previous_end, chapter.end_time)

        if not plan.short_candidates:
            self._add(issues, corrections, "missing_short_candidates", "Score self-contained moments for Shorts.")
        for candidate in plan.short_candidates:
            duration = candidate.end_time - candidate.start_time
            if duration < 15 or duration > 60:
                self._add(issues, corrections, "invalid_short_duration", "Keep each short between 15 and 60 seconds.")
            if candidate.start_time < 0 or candidate.end_time > plan.master_duration_seconds:
                self._add(issues, corrections, "short_outside_master", "Use exact timestamps from the long master.")
            if candidate.source_chapter not in chapter_names:
                self._add(issues, corrections, "unknown_source_chapter", "Link each short to a verified chapter.")
            if not candidate.hook.strip() or not candidate.payoff.strip():
                self._add(issues, corrections, "short_without_arc", "Give each short a hook and standalone payoff.")
            if not 0 <= candidate.score <= 100:
                self._add(issues, corrections, "invalid_candidate_score", "Score short candidates from 0 to 100.")

        score = max(0.0, round(100.0 - len(issues) * 10.0, 1))
        return EditorialQualityResult(not issues, score, tuple(issues), tuple(corrections))

    @staticmethod
    def _add(issues: list[str], corrections: list[str], issue: str, correction: str) -> None:
        if issue not in issues:
            issues.append(issue)
            corrections.append(correction)
