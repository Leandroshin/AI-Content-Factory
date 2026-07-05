"""Deterministic creative review pipeline."""

from __future__ import annotations

from enum import StrEnum

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.creative_review.models import (
    CreativeAsset,
    CreativeReviewBrief,
    CreativeReviewFinding,
    CreativeReviewReport,
)


class PipelineStage(StrEnum):
    """Stages of the creative review pipeline."""

    CREATED = "created"
    ANALYZING_BRIEF = "analyzing_brief"
    COLLECTING_ASSETS = "collecting_assets"
    SCORING_ASSETS = "scoring_assets"
    DECIDING_ACTIONS = "deciding_actions"
    HANDOFF_PLANNING = "handoff_planning"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class CreativeReviewPipeline(ProductionPipeline):
    """Rule-based state machine for creative readiness decisions."""

    def __init__(self, brief: CreativeReviewBrief) -> None:
        super().__init__()
        self._brief = brief
        self._stage: str = PipelineStage.CREATED.value
        self._assets: tuple[CreativeAsset, ...] = ()
        self._findings: tuple[CreativeReviewFinding, ...] = ()
        self._next_actions: tuple[str, ...] = ()
        self._report: CreativeReviewReport | None = None

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def progress(self) -> float:
        stages = list(PipelineStage)
        try:
            idx = stages.index(PipelineStage(self._stage))
            return round((idx / (len(stages) - 1)) * 100.0, 1)
        except (ValueError, KeyError):
            return 0.0

    def advance(self) -> StageResult:
        handlers = {
            PipelineStage.CREATED: self._stage_created,
            PipelineStage.ANALYZING_BRIEF: self._stage_analyzing_brief,
            PipelineStage.COLLECTING_ASSETS: self._stage_collecting_assets,
            PipelineStage.SCORING_ASSETS: self._stage_scoring_assets,
            PipelineStage.DECIDING_ACTIONS: self._stage_deciding_actions,
            PipelineStage.HANDOFF_PLANNING: self._stage_handoff_planning,
            PipelineStage.DELIVERING: self._stage_delivering,
        }

        try:
            current = PipelineStage(self._stage)
        except (ValueError, KeyError):
            result = StageResult(stage=self._stage, success=False, error=f"Unknown stage: {self._stage}")
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        handler = handlers.get(current)
        if handler is None:
            result = StageResult(stage=self._stage, success=False, error=f"No handler for: {self._stage}")
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        result = handler()
        self._stages_log.append(result)
        if result.next_stage:
            self._stage = result.next_stage
        elif result.success:
            self._stage = self._next_stage(current).value
        else:
            self._stage = PipelineStage.FAILED.value
        return result

    def reset(self) -> None:
        super().reset()
        self._stage = PipelineStage.CREATED.value
        self._assets = ()
        self._findings = ()
        self._next_actions = ()
        self._report = None

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Creative review task '{self._brief.title}' created",
            output={
                "task_id": str(self._brief.task_id),
                "target_platforms": list(self._brief.target_platforms),
                "ready_threshold": self._brief.ready_threshold,
            },
            next_stage=PipelineStage.ANALYZING_BRIEF.value,
        )

    def _stage_analyzing_brief(self) -> StageResult:
        if self._brief.ready_threshold <= 0:
            return StageResult(
                stage=PipelineStage.ANALYZING_BRIEF.value,
                success=False,
                error="ready_threshold must be greater than zero.",
            )
        return StageResult(
            stage=PipelineStage.ANALYZING_BRIEF.value,
            success=True,
            summary=f"Creative review brief analyzed for {len(self._brief.target_platforms)} platform(s)",
            output={
                "objective": self._brief.objective,
                "target_platforms": list(self._brief.target_platforms),
            },
            next_stage=PipelineStage.COLLECTING_ASSETS.value,
        )

    def _stage_collecting_assets(self) -> StageResult:
        assets = tuple(asset for asset in self._brief.assets if asset.title and asset.has_image_reference)
        if not assets:
            return StageResult(
                stage=PipelineStage.COLLECTING_ASSETS.value,
                success=False,
                error="At least one asset with title and image_url or file_path is required.",
            )
        self._assets = assets
        return StageResult(
            stage=PipelineStage.COLLECTING_ASSETS.value,
            success=True,
            summary=f"Collected {len(assets)} creative asset(s)",
            output={
                "assets_reviewed": len(assets),
                "asset_types": list(dict.fromkeys(asset.asset_type for asset in assets)),
                "platforms": list(dict.fromkeys(asset.platform for asset in assets if asset.platform)),
            },
            next_stage=PipelineStage.SCORING_ASSETS.value,
        )

    def _stage_scoring_assets(self) -> StageResult:
        self._findings = tuple(_score_asset(asset, self._brief.ready_threshold) for asset in self._assets)
        average = round(sum(f.score_total for f in self._findings) / len(self._findings), 2)
        return StageResult(
            stage=PipelineStage.SCORING_ASSETS.value,
            success=True,
            summary=f"Scored {len(self._findings)} creative asset(s)",
            output={
                "assets_reviewed": len(self._findings),
                "average_score": average,
                "top_score": max(f.score_total for f in self._findings),
            },
            next_stage=PipelineStage.DECIDING_ACTIONS.value,
        )

    def _stage_deciding_actions(self) -> StageResult:
        counts = _action_counts(self._findings)
        return StageResult(
            stage=PipelineStage.DECIDING_ACTIONS.value,
            success=True,
            summary=f"Creative actions decided: {counts}",
            output={
                "ready_count": counts["use_as_is"],
                "improve_count": counts["minor_cleanup"],
                "rebuild_count": counts["rebuild_creative"] + counts["find_alternative_image"],
                "human_review_count": counts["human_review"],
                "findings": [finding.to_public_dict() for finding in self._findings],
            },
            next_stage=PipelineStage.HANDOFF_PLANNING.value,
        )

    def _stage_handoff_planning(self) -> StageResult:
        actions = []
        if any(f.recommended_action == "use_as_is" for f in self._findings):
            actions.append("Send ready assets directly to AffiliateDealsEmployee or Publishing queue.")
        if any(f.recommended_action == "minor_cleanup" for f in self._findings):
            actions.append("Send cleanup tasks to ImageDesignerEmployee before publishing.")
        if any(f.recommended_action in ("rebuild_creative", "find_alternative_image") for f in self._findings):
            actions.append("Request new product image, generated creative, or marketplace alternative before video production.")
        if any(f.recommended_action == "human_review" for f in self._findings):
            actions.append("Hold risky assets for owner approval before any public use.")
        self._next_actions = tuple(dict.fromkeys(actions))
        return StageResult(
            stage=PipelineStage.HANDOFF_PLANNING.value,
            success=True,
            summary=f"Handoff planned with {len(self._next_actions)} action(s)",
            output={
                "next_actions": list(self._next_actions),
                "handoff_targets": ["affiliate_deals", "image", "video", "hitl_approval"],
            },
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        counts = _action_counts(self._findings)
        sorted_findings = tuple(sorted(self._findings, key=lambda finding: finding.score_total, reverse=True))
        self._report = CreativeReviewReport(
            title=self._brief.title,
            total_assets=len(self._findings),
            ready_count=counts["use_as_is"],
            improve_count=counts["minor_cleanup"],
            rebuild_count=counts["rebuild_creative"] + counts["find_alternative_image"],
            human_review_count=counts["human_review"],
            findings=sorted_findings,
            next_actions=self._next_actions,
            metadata={
                "target_platforms": list(self._brief.target_platforms),
                "ready_threshold": self._brief.ready_threshold,
            },
        )
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered creative review report: {len(self._findings)} asset(s)",
            output=self._report.to_public_dict(),
            next_stage=PipelineStage.COMPLETED.value,
        )

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage:
        stages = list(PipelineStage)
        idx = stages.index(current)
        if idx + 1 < len(stages):
            return stages[idx + 1]
        return PipelineStage.COMPLETED


def _score_asset(asset: CreativeAsset, ready_threshold: float) -> CreativeReviewFinding:
    reasons: list[str] = []
    tasks: list[str] = []
    handoff: list[str] = []

    positive = (
        _clamp(asset.visual_quality) * 2.2
        + _clamp(asset.product_visibility) * 2.2
        + _clamp(asset.resolution_score) * 1.5
        + _clamp(asset.brand_safety) * 1.4
        + _context_bonus(asset)
    )
    penalty = _clamp(asset.text_clutter) * 1.7 + _clamp(asset.watermark_risk) * 2.5 + len(asset.risk_flags) * 7.0
    score = round(max(0.0, min(100.0, positive - penalty)), 2)

    if asset.visual_quality >= 7 and asset.product_visibility >= 7:
        reasons.append("clear_product_visual")
    if asset.text_clutter >= 7:
        reasons.append("too_much_text_or_visual_noise")
        tasks.append("Remove noisy text overlays or rebuild layout.")
    if asset.watermark_risk >= 5:
        reasons.append("watermark_or_third_party_asset_risk")
        tasks.append("Find a clean marketplace image or create an original asset.")
    if "third_party_thumbnail_reference" in asset.risk_flags:
        reasons.append("reference_only_do_not_reuse")
        tasks.append("Use as style reference only; create original face, layout, and proof card.")
    if "earnings_claim" in asset.risk_flags:
        reasons.append("earnings_claim_requires_verification")
        tasks.append("Replace fake proof with verified dashboard data or remove claim.")
    if asset.face_emotion >= 7 or asset.proof_element >= 7:
        reasons.append("strong_thumbnail_formula")
    if asset.brand_safety < 5:
        reasons.append("brand_safety_risk")
        tasks.append("Owner must approve before publishing.")

    if score >= ready_threshold and not _has_hard_risk(asset):
        readiness = "ready"
        action = "use_as_is"
        handoff.append("affiliate_deals")
    elif score >= 62 and not _has_hard_risk(asset):
        readiness = "needs_light_improvement"
        action = "minor_cleanup"
        tasks.append("Apply small cleanup before publishing.")
        handoff.append("image")
    elif score >= 45 and not _has_hard_risk(asset):
        readiness = "needs_rebuild"
        action = "rebuild_creative"
        tasks.append("Rebuild creative using product, benefit, proof, and CTA structure.")
        handoff.extend(("image", "script"))
    elif _has_hard_risk(asset):
        readiness = "blocked_for_review"
        action = "human_review"
        tasks.append("Do not publish until owner approves rights, claims, and source.")
        handoff.append("hitl_approval")
    else:
        readiness = "needs_alternative"
        action = "find_alternative_image"
        tasks.append("Search for a cleaner product image before creative production.")
        handoff.extend(("product_research", "image"))

    if not reasons:
        reasons.append("manual_review_needed")

    return CreativeReviewFinding(
        asset=asset,
        score_total=score,
        readiness=readiness,
        recommended_action=action,
        reasons=tuple(dict.fromkeys(reasons)),
        improvement_tasks=tuple(dict.fromkeys(tasks)),
        handoff_targets=tuple(dict.fromkeys(handoff)),
    )


def _context_bonus(asset: CreativeAsset) -> float:
    bonus = 0.0
    if asset.use_case in ("youtube_thumbnail", "short_thumbnail"):
        bonus += _clamp(asset.face_emotion) * 0.9
        bonus += _clamp(asset.proof_element) * 0.8
    if asset.use_case in ("affiliate_post", "product_card"):
        bonus += _clamp(asset.product_visibility) * 0.8
    return bonus


def _has_hard_risk(asset: CreativeAsset) -> bool:
    hard = {"third_party_thumbnail_reference", "copyright_risk", "earnings_claim", "unsafe_claim"}
    return asset.brand_safety < 4 or any(flag in hard for flag in asset.risk_flags)


def _action_counts(findings: tuple[CreativeReviewFinding, ...]) -> dict[str, int]:
    counts = {
        "use_as_is": 0,
        "minor_cleanup": 0,
        "rebuild_creative": 0,
        "find_alternative_image": 0,
        "human_review": 0,
    }
    for finding in findings:
        if finding.recommended_action in counts:
            counts[finding.recommended_action] += 1
    return counts


def _clamp(value: float) -> float:
    return max(0.0, min(10.0, float(value or 0.0)))
