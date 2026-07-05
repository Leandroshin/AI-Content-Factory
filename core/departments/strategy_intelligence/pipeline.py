"""Deterministic strategy extraction pipeline."""

from __future__ import annotations

import unicodedata
from enum import StrEnum

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.strategy_intelligence.models import (
    MetricMention,
    StrategyIntelligenceReport,
    StrategyIntelligenceTask,
    StrategyPattern,
    StrategySource,
    ToolMention,
)


class PipelineStage(StrEnum):
    """Stages of the strategy intelligence pipeline."""

    CREATED = "created"
    VALIDATING_SOURCES = "validating_sources"
    DETECTING_TOOLS = "detecting_tools"
    DETECTING_METRICS = "detecting_metrics"
    EXTRACTING_PATTERNS = "extracting_patterns"
    BUILDING_GUARDRAILS = "building_guardrails"
    HANDOFF_PLANNING = "handoff_planning"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyIntelligencePipeline(ProductionPipeline):
    """Rule-based state machine for turning videos/transcripts into strategy."""

    def __init__(self, task: StrategyIntelligenceTask) -> None:
        super().__init__()
        self._task = task
        self._stage: str = PipelineStage.CREATED.value
        self._sources: tuple[StrategySource, ...] = ()
        self._tools: tuple[ToolMention, ...] = ()
        self._metrics: tuple[MetricMention, ...] = ()
        self._patterns: tuple[StrategyPattern, ...] = ()
        self._warnings: tuple[str, ...] = ()
        self._next_actions: tuple[str, ...] = ()
        self._report: StrategyIntelligenceReport | None = None

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
            PipelineStage.VALIDATING_SOURCES: self._stage_validating_sources,
            PipelineStage.DETECTING_TOOLS: self._stage_detecting_tools,
            PipelineStage.DETECTING_METRICS: self._stage_detecting_metrics,
            PipelineStage.EXTRACTING_PATTERNS: self._stage_extracting_patterns,
            PipelineStage.BUILDING_GUARDRAILS: self._stage_building_guardrails,
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
        self._sources = ()
        self._tools = ()
        self._metrics = ()
        self._patterns = ()
        self._warnings = ()
        self._next_actions = ()
        self._report = None

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Strategy task '{self._task.title}' created",
            output={
                "task_id": str(self._task.task_id),
                "focus_areas": list(self._task.focus_areas),
                "max_patterns": self._task.max_patterns,
            },
            next_stage=PipelineStage.VALIDATING_SOURCES.value,
        )

    def _stage_validating_sources(self) -> StageResult:
        if self._task.max_patterns <= 0:
            return StageResult(
                stage=PipelineStage.VALIDATING_SOURCES.value,
                success=False,
                error="max_patterns must be greater than zero.",
            )
        sources = tuple(src for src in self._task.sources if src.title and src.has_text)
        if not sources:
            return StageResult(
                stage=PipelineStage.VALIDATING_SOURCES.value,
                success=False,
                error="At least one source with title and transcript_text is required.",
            )
        self._sources = sources
        return StageResult(
            stage=PipelineStage.VALIDATING_SOURCES.value,
            success=True,
            summary=f"Validated {len(sources)} source(s)",
            output={
                "sources_analyzed": len(sources),
                "sources": [source.to_public_dict() for source in sources],
            },
            next_stage=PipelineStage.DETECTING_TOOLS.value,
        )

    def _stage_detecting_tools(self) -> StageResult:
        self._tools = _detect_tools(self._sources)
        return StageResult(
            stage=PipelineStage.DETECTING_TOOLS.value,
            success=True,
            summary=f"Detected {len(self._tools)} tool/platform mention(s)",
            output={
                "tools_detected": [tool.to_public_dict() for tool in self._tools],
            },
            next_stage=PipelineStage.DETECTING_METRICS.value,
        )

    def _stage_detecting_metrics(self) -> StageResult:
        self._metrics = _detect_metrics(self._sources)
        return StageResult(
            stage=PipelineStage.DETECTING_METRICS.value,
            success=True,
            summary=f"Detected {len(self._metrics)} metric signal(s)",
            output={
                "metrics_detected": [metric.to_public_dict() for metric in self._metrics],
            },
            next_stage=PipelineStage.EXTRACTING_PATTERNS.value,
        )

    def _stage_extracting_patterns(self) -> StageResult:
        patterns = _extract_patterns(self._sources, self._tools, self._metrics)
        self._patterns = tuple(sorted(patterns, key=lambda p: p.confidence, reverse=True)[: self._task.max_patterns])
        return StageResult(
            stage=PipelineStage.EXTRACTING_PATTERNS.value,
            success=True,
            summary=f"Extracted {len(self._patterns)} reusable strategy pattern(s)",
            output={
                "patterns": [pattern.to_public_dict() for pattern in self._patterns],
            },
            next_stage=PipelineStage.BUILDING_GUARDRAILS.value,
        )

    def _stage_building_guardrails(self) -> StageResult:
        warnings = [
            "Use videos and courses as learning inputs only; create original scripts, assets, and products.",
            "Do not publish earnings claims as guarantees; treat fast-money examples as marketing claims until verified.",
            "Prefer official APIs, affiliate terms, and human approval before public posting.",
        ]
        if _any_terms(self._sources, ("curso", "pdf", "ebook", "entregavel", "entregaveis")):
            warnings.append("When learning from courses, extract structure and checkpoints, not copied lessons or rewritten text.")
        if _any_terms(self._sources, ("whatsapp", "telegram", "instagram", "post automatico", "postagem automatica")):
            warnings.append("Automation for messaging channels must include disclosure, rate limits, and opt-in rules.")
        self._warnings = tuple(dict.fromkeys(warnings))
        return StageResult(
            stage=PipelineStage.BUILDING_GUARDRAILS.value,
            success=True,
            summary=f"Built {len(self._warnings)} guardrail(s)",
            output={
                "warnings": list(self._warnings),
            },
            next_stage=PipelineStage.HANDOFF_PLANNING.value,
        )

    def _stage_handoff_planning(self) -> StageResult:
        actions = [
            "Update ProductResearchEmployee scoring with learned metrics before collecting new candidates.",
            "Send creative rules to CreativeReviewEmployee before image or thumbnail production.",
            "Send approved offer strategy to AffiliateDealsEmployee and HITL approval before Telegram publishing.",
        ]
        if any(tool.name in ("Keepa", "Kalodata", "Divulga Ninja") for tool in self._tools):
            actions.append("Evaluate whether to integrate official APIs or use manual/exported research first.")
        if any(pattern.pattern_id == "ai_infoproduct_to_checkout" for pattern in self._patterns):
            actions.append("Use original curriculum planning for infoproducts; do not rewrite third-party course content.")
        self._next_actions = tuple(dict.fromkeys(actions))
        return StageResult(
            stage=PipelineStage.HANDOFF_PLANNING.value,
            success=True,
            summary=f"Handoff planned with {len(self._next_actions)} action(s)",
            output={
                "next_actions": list(self._next_actions),
                "handoff_targets": ["product_research", "creative_review", "affiliate_deals", "hitl_approval"],
            },
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        self._report = StrategyIntelligenceReport(
            title=self._task.title,
            sources_analyzed=len(self._sources),
            tools_detected=self._tools,
            metrics_detected=self._metrics,
            patterns=self._patterns,
            warnings=self._warnings,
            next_actions=self._next_actions,
            metadata={
                "focus_areas": list(self._task.focus_areas),
                "raw_transcripts_stored": False,
            },
        )
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered strategy report: {len(self._patterns)} pattern(s)",
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


_TOOL_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("keepa", "Keepa", "amazon_product_research", "Amazon price, BSR, variation, and Buy Box analysis."),
    ("divulga ninja", "Divulga Ninja", "affiliate_post_automation", "Affiliate post generation for social channels."),
    ("insta ninja", "Insta Ninja", "instagram_affiliate_automation", "Instagram-oriented affiliate publishing workflow."),
    ("cakto", "Cakto", "checkout_infoproduct", "Checkout and digital product delivery platform."),
    ("cacto", "Cakto", "checkout_infoproduct", "Checkout and digital product delivery platform."),
    ("tokfy", "TokFy", "tiktok_shop_ai_tooling", "AI tooling ecosystem for TikTok Shop operations."),
    ("kalodata", "Kalodata", "tiktok_shop_research", "TikTok Shop product, creator, and trend research."),
    ("caloda", "Kalodata", "tiktok_shop_research", "TikTok Shop product, creator, and trend research."),
    ("capcut", "CapCut", "video_editing", "Short-form video editing and template production."),
    ("canva", "Canva", "creative_design", "Static creative and thumbnail design."),
    ("gamma", "Gamma", "document_generation", "Fast document/course/ebook layout generation."),
    ("gama", "Gamma", "document_generation", "Fast document/course/ebook layout generation."),
    ("aliexpress api", "AliExpress API", "affiliate_api", "Official affiliate data source for AliExpress."),
    ("tiktok shop", "TikTok Shop", "marketplace", "Marketplace and affiliate content channel."),
    ("shopee", "Shopee", "marketplace", "Marketplace and affiliate content channel."),
    ("amazon", "Amazon", "marketplace", "Marketplace and affiliate content channel."),
)


_METRIC_RULES: tuple[tuple[tuple[str, ...], str, str, str], ...] = (
    (("crescimento", "grafico"), "trend_growth_graph", "Avoid products with declining demand; prefer rising trend curves.", "growth graph"),
    (("queda", "grafico"), "decline_risk", "Reject products whose revenue or trend graph is falling.", "decline graph"),
    (("receita",), "revenue_signal", "Use revenue as a demand signal, not as the only decision rule.", "revenue"),
    (("ticket medio",), "average_ticket", "Estimate price band, commission potential, and impulse-buy fit.", "ticket medio"),
    (("comissao",), "commission_rate", "Prioritize offers with enough margin to justify creative work.", "commission"),
    (("ranking",), "ranking_bsr", "Use category rank/BSR as demand context, especially on Amazon.", "ranking"),
    (("bsr",), "ranking_bsr", "Use category rank/BSR as demand context, especially on Amazon.", "BSR"),
    (("buy box",), "buy_box_share", "Check whether the seller can actually win sales on Amazon.", "Buy Box"),
    (("variacao",), "variation_share", "Find the variation that actually drives sales before producing creative.", "variation share"),
    (("avaliacao",), "reviews_rating", "Use rating and review count to assess trust.", "reviews"),
    (("reviews",), "reviews_rating", "Use rating and review count to assess trust.", "reviews"),
    (("preco historico",), "historical_price", "Avoid fake discounts by checking historical price.", "historical price"),
    (("constancia",), "posting_consistency", "Content distribution needs repeated posting, not one isolated creative.", "posting consistency"),
)


def _detect_tools(sources: tuple[StrategySource, ...]) -> tuple[ToolMention, ...]:
    found: dict[str, ToolMention] = {}
    for source in sources:
        text = _normalize(source.transcript_text)
        for needle, name, category, note in _TOOL_RULES:
            if needle in text:
                previous = found.get(name)
                sources_seen = tuple(dict.fromkeys((*(previous.sources if previous else ()), source.title)))
                notes = tuple(dict.fromkeys((*(previous.notes if previous else ()), note)))
                confidence = min(0.98, (previous.confidence if previous else 0.62) + 0.08)
                found[name] = ToolMention(name=name, category=category, confidence=round(confidence, 2), sources=sources_seen, notes=notes)
    return tuple(sorted(found.values(), key=lambda t: (t.category, t.name)))


def _detect_metrics(sources: tuple[StrategySource, ...]) -> tuple[MetricMention, ...]:
    found: dict[str, MetricMention] = {}
    for source in sources:
        text = _normalize(source.transcript_text)
        for terms, name, use_case, note in _METRIC_RULES:
            if all(term in text for term in terms):
                previous = found.get(name)
                sources_seen = tuple(dict.fromkeys((*(previous.sources if previous else ()), source.title)))
                notes = tuple(dict.fromkeys((*(previous.notes if previous else ()), note)))
                confidence = min(0.98, (previous.confidence if previous else 0.62) + 0.08)
                found[name] = MetricMention(name=name, use_case=use_case, confidence=round(confidence, 2), sources=sources_seen, notes=notes)
    return tuple(sorted(found.values(), key=lambda m: (m.name, m.confidence)))


def _extract_patterns(
    sources: tuple[StrategySource, ...],
    tools: tuple[ToolMention, ...],
    metrics: tuple[MetricMention, ...],
) -> tuple[StrategyPattern, ...]:
    text = _normalize(" ".join(source.transcript_text for source in sources))
    patterns: list[StrategyPattern] = []
    tool_names = {tool.name for tool in tools}
    metric_names = {metric.name for metric in metrics}

    if "tiktok shop" in text and ("pov" in text or "video de pov" in text) and ("ia" in text or "inteligencia artificial" in text):
        patterns.append(StrategyPattern(
            pattern_id="tiktok_shop_pov_ai_video",
            title="TikTok Shop POV video from winning product signals",
            category="commerce_content",
            confidence=0.9,
            routes_to=("product_research", "script", "image", "video", "affiliate_deals"),
            evidence_points=(
                "Find products already selling on TikTok Shop.",
                "Use POV-style creatives and product images as input for short videos.",
                "Route winners into script, visual, and affiliate offer production.",
            ),
            guardrails=("Verify product rights, affiliate terms, and claim accuracy before publishing.",),
        ))

    if {"trend_growth_graph", "decline_risk"} & metric_names:
        patterns.append(StrategyPattern(
            pattern_id="product_trend_graph_selection",
            title="Select products by trend direction, not only top revenue",
            category="product_research",
            confidence=0.88,
            routes_to=("product_research", "affiliate_deals"),
            evidence_points=(
                "Revenue alone can hide products already declining.",
                "Positive growth curve increases odds that content still has demand.",
            ),
            guardrails=("Treat graphs as signals; verify availability, margin, and competition.",),
        ))

    if "Keepa" in tool_names or {"ranking_bsr", "buy_box_share", "variation_share"} & metric_names:
        patterns.append(StrategyPattern(
            pattern_id="amazon_keepa_product_analysis",
            title="Amazon product validation with Keepa-style metrics",
            category="marketplace_research",
            confidence=0.87,
            routes_to=("product_research", "affiliate_deals"),
            evidence_points=(
                "Review BSR/ranking windows, historical price, reviews, and variation share.",
                "Check Buy Box behavior before assuming a product can convert.",
            ),
            guardrails=("Do not assume estimated sales are exact; use them as directional evidence.",),
        ))

    if {"Divulga Ninja", "Insta Ninja", "AliExpress API"} & tool_names:
        patterns.append(StrategyPattern(
            pattern_id="affiliate_post_automation",
            title="Affiliate post automation with controlled approval",
            category="publishing",
            confidence=0.84,
            routes_to=("affiliate_deals", "hitl_approval", "publishing"),
            evidence_points=(
                "Collect product data from affiliate sources.",
                "Generate compact posts for Telegram, WhatsApp manual flow, or Instagram.",
            ),
            guardrails=("Require disclosure, rate limits, official APIs, and human approval before sending.",),
        ))

    if "Cakto" in tool_names and ("claude" in text or "ia" in text) and ("produto" in text or "infoproduto" in text):
        patterns.append(StrategyPattern(
            pattern_id="ai_infoproduct_to_checkout",
            title="Original infoproduct planning to checkout",
            category="digital_product",
            confidence=0.82,
            routes_to=("strategy_intelligence", "script", "image", "publishing"),
            evidence_points=(
                "Use AI to plan product promise, modules, delivery assets, cover, and checkout.",
                "Publish through a checkout platform only after original content is created.",
            ),
            guardrails=("Never rewrite or repackage copied courses; build original curriculum and examples.",),
        ))

    if ("thumbnail" in text or "thumb" in text or "sacar" in text) and ("tiktok" in text or "shop" in text):
        patterns.append(StrategyPattern(
            pattern_id="thumbnail_money_proof_pattern",
            title="High-contrast thumbnail with platform, face, proof card, and giant text",
            category="creative",
            confidence=0.8,
            routes_to=("creative_review", "image", "script"),
            evidence_points=(
                "Strong thumbnails combine expressive face, platform logo, proof card, action button, and short text.",
                "This is a reusable style formula, not an asset to copy.",
            ),
            guardrails=("Use original faces/assets and avoid fake earnings proof.",),
        ))

    if "TokFy" in tool_names or "Kalodata" in tool_names:
        patterns.append(StrategyPattern(
            pattern_id="tiktok_shop_tool_stack_mapping",
            title="Map external TikTok Shop tools before building our own",
            category="tool_strategy",
            confidence=0.78,
            routes_to=("product_research", "provider_control", "external_llm_inbox"),
            evidence_points=(
                "Some paid tools already bundle product, creator, and video research.",
                "The factory should test/manual-import first, then build adapters only for proven value.",
            ),
            guardrails=("Avoid cloning proprietary products; implement our own workflow around public data and user-provided exports.",),
        ))

    return tuple(patterns)


def _any_terms(sources: tuple[StrategySource, ...], terms: tuple[str, ...]) -> bool:
    text = _normalize(" ".join(source.transcript_text for source in sources))
    return any(term in text for term in terms)


def _normalize(text: str) -> str:
    clean = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in clean if not unicodedata.combining(ch))
    return ascii_text.lower()
