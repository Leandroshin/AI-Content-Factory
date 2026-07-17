"""Affiliate platform evaluation for offer selection.

The factory uses this module before spending time on a product or buying
traffic. It is deliberately rule-based: screenshots and creator opinions can
suggest a direction, but the platform must still pass transparent operational
checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AffiliatePlatformProfile:
    """Operational profile for an affiliate platform or network."""

    name: str
    display_name: str
    category: str = "marketplace"
    onboarding_status: str = "unknown"
    primary_use_case: str = ""
    affiliate_link_ease: float = 0.5
    commission_potential: float = 0.5
    payout_friction: float = 0.5
    compliance_complexity: float = 0.5
    offer_evidence_strength: float = 0.5
    paid_traffic_allowed_confidence: float = 0.0
    owner_ready: bool = False
    manual_review_required: bool = True
    recommended_channels: tuple[str, ...] = field(default_factory=tuple)
    required_owner_actions: tuple[str, ...] = field(default_factory=tuple)
    evidence_requirements: tuple[str, ...] = field(default_factory=tuple)
    no_spend_allowed_actions: tuple[str, ...] = field(default_factory=tuple)
    blocked_until_budget_actions: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AffiliatePlatformEvaluation:
    """Scorecard result for a platform."""

    platform: AffiliatePlatformProfile
    score_total: float
    readiness_score: float
    economics_score: float
    friction_penalty: float
    compliance_penalty: float
    evidence_score: float
    recommendation: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class NoSpendAffiliatePlan:
    """Safe work that can continue while payments/API spend are blocked."""

    platform_name: str
    display_name: str
    status: str
    allowed_actions: tuple[str, ...] = field(default_factory=tuple)
    blocked_actions: tuple[str, ...] = field(default_factory=tuple)
    rationale: tuple[str, ...] = field(default_factory=tuple)


def evaluate_affiliate_platform(
    profile: AffiliatePlatformProfile,
    *,
    goal: str = "first_revenue",
    paid_traffic: bool = False,
) -> AffiliatePlatformEvaluation:
    """Evaluate whether the factory should work on a platform now.

    Scores intentionally privilege operational readiness and evidence over
    headline commission. This keeps the owner from chasing a platform that looks
    profitable in a video but cannot be used safely yet.
    """

    reasons: list[str] = []
    next_actions: list[str] = []

    readiness_score = 22.0 if profile.owner_ready else 6.0
    if profile.owner_ready:
        reasons.append("owner_account_ready")
    else:
        reasons.append("owner_action_required")
        next_actions.extend(profile.required_owner_actions)

    readiness_score += _bounded(profile.affiliate_link_ease) * 18.0
    if profile.affiliate_link_ease >= 0.75:
        reasons.append("affiliate_link_easy")
    elif profile.affiliate_link_ease <= 0.35:
        reasons.append("affiliate_link_friction")

    economics_score = _bounded(profile.commission_potential) * 24.0
    if profile.commission_potential >= 0.75:
        reasons.append("strong_commission_economics")
    elif profile.commission_potential <= 0.35:
        reasons.append("low_commission_economics")

    evidence_score = _bounded(profile.offer_evidence_strength) * 18.0
    if profile.offer_evidence_strength >= 0.72:
        reasons.append("offer_evidence_available")
    else:
        reasons.append("needs_offer_evidence")
        next_actions.extend(profile.evidence_requirements)

    friction_penalty = _bounded(profile.payout_friction) * 16.0
    if profile.payout_friction >= 0.65:
        reasons.append("payout_or_onboarding_friction")

    compliance_penalty = _bounded(profile.compliance_complexity) * 14.0
    if profile.compliance_complexity >= 0.65:
        reasons.append("compliance_review_needed")

    if paid_traffic and profile.paid_traffic_allowed_confidence < 0.7:
        compliance_penalty += 10.0
        reasons.append("paid_traffic_not_ready")
        next_actions.append("Confirm paid traffic rules and approved creatives before buying traffic.")

    if profile.manual_review_required:
        reasons.append("manual_review_required")

    total = round(
        max(
            0.0,
            readiness_score + economics_score + evidence_score - friction_penalty - compliance_penalty,
        ),
        2,
    )

    recommendation = _recommendation(total, profile, paid_traffic=paid_traffic)
    if recommendation == "start_now":
        next_actions.append("Select one offer and run Product Research with manual source evidence.")
    elif recommendation == "prepare_next":
        next_actions.append("Complete onboarding and collect one candidate offer before production.")
    elif recommendation == "watch_later":
        next_actions.append("Keep in the research backlog until the factory has stronger proof or credentials.")
    else:
        next_actions.append("Do not route to production until the blocking action is resolved.")

    if goal == "first_revenue" and profile.category == "physical_marketplace":
        reasons.append("useful_for_organic_testing")
    if goal == "first_revenue" and profile.category in ("digital_network", "cpa_network"):
        reasons.append("better_for_commission_testing")

    return AffiliatePlatformEvaluation(
        platform=profile,
        score_total=total,
        readiness_score=round(readiness_score, 2),
        economics_score=round(economics_score, 2),
        friction_penalty=round(friction_penalty, 2),
        compliance_penalty=round(compliance_penalty, 2),
        evidence_score=round(evidence_score, 2),
        recommendation=recommendation,
        reasons=tuple(dict.fromkeys(reasons)),
        next_actions=tuple(dict.fromkeys(action for action in next_actions if action)),
    )


def build_no_spend_affiliate_plan(
    profiles: tuple[AffiliatePlatformProfile, ...],
) -> tuple[NoSpendAffiliatePlan, ...]:
    """Create a zero-budget action plan for the affiliate portfolio.

    This is used when payment verification, paid APIs, ads or provider credits
    are temporarily unavailable. The factory keeps learning and preparing, but
    does not push the owner back into a money-dependent step.
    """

    plans: list[NoSpendAffiliatePlan] = []
    for profile in profiles:
        allowed = list(profile.no_spend_allowed_actions)
        blocked = list(profile.blocked_until_budget_actions)
        rationale = [
            "no_spend_mode_active",
            f"onboarding_status:{profile.onboarding_status}",
        ]

        if not allowed:
            allowed.extend(
                (
                    "Collect official product page and sales page URL.",
                    "Capture commission, refund, traffic rules and creative permissions.",
                    "Prepare a draft only; keep publishing and paid traffic blocked.",
                )
            )

        if profile.evidence_requirements:
            allowed.extend(profile.evidence_requirements)

        if profile.paid_traffic_allowed_confidence < 0.7:
            blocked.append("Paid traffic until platform rules and landing compliance are reviewed.")
        if profile.payout_friction >= 0.5 or "payment" in profile.onboarding_status:
            blocked.append("Payment/payout setup until owner confirms budget or account access.")

        status = "work_free_tasks"
        if not profile.owner_ready and any("official affiliate access" in action for action in profile.required_owner_actions):
            status = "research_only"
        elif profile.affiliate_link_ease >= 0.7:
            status = "manual_intake_ready"

        plans.append(
            NoSpendAffiliatePlan(
                platform_name=profile.name,
                display_name=profile.display_name,
                status=status,
                allowed_actions=tuple(dict.fromkeys(action for action in allowed if action)),
                blocked_actions=tuple(dict.fromkeys(action for action in blocked if action)),
                rationale=tuple(dict.fromkeys(rationale)),
            )
        )

    return tuple(plans)


def rank_affiliate_platforms(
    profiles: tuple[AffiliatePlatformProfile, ...],
    *,
    goal: str = "first_revenue",
    paid_traffic: bool = False,
) -> tuple[AffiliatePlatformEvaluation, ...]:
    """Evaluate and rank platforms by factory priority."""

    evaluations = tuple(
        evaluate_affiliate_platform(profile, goal=goal, paid_traffic=paid_traffic)
        for profile in profiles
    )
    return tuple(sorted(evaluations, key=lambda item: item.score_total, reverse=True))


def default_affiliate_platform_profiles() -> tuple[AffiliatePlatformProfile, ...]:
    """Current conservative platform profiles for Shin's factory."""

    return (
        AffiliatePlatformProfile(
            name="digistore24",
            display_name="Digistore24",
            category="digital_network",
            onboarding_status="next_signup",
            primary_use_case="First controlled digital offer test.",
            affiliate_link_ease=0.88,
            commission_potential=0.82,
            payout_friction=0.36,
            compliance_complexity=0.55,
            offer_evidence_strength=0.62,
            paid_traffic_allowed_confidence=0.55,
            owner_ready=False,
            manual_review_required=True,
            recommended_channels=("landing_page", "telegram", "youtube_short"),
            required_owner_actions=("Create/confirm affiliate account and payout profile.",),
            evidence_requirements=(
                "Capture product page, affiliate support page, commission, refund terms, and allowed traffic channels.",
            ),
            no_spend_allowed_actions=(
                "Browse Marketplace and shortlist products with public sales pages.",
                "Save sales page URL and promotional link when it is available without payout verification.",
                "Prepare offer dossier for later PayPal verification.",
            ),
            blocked_until_budget_actions=(
                "PayPal/payment verification that requires card balance.",
                "Paid traffic tests.",
            ),
            notes=("Best next onboarding candidate before paid traffic.",),
        ),
        AffiliatePlatformProfile(
            name="braip",
            display_name="Braip",
            category="digital_network",
            onboarding_status="api_token_saved",
            primary_use_case="Brazilian digital/physical offers after terms review.",
            affiliate_link_ease=0.72,
            commission_potential=0.74,
            payout_friction=0.42,
            compliance_complexity=0.6,
            offer_evidence_strength=0.58,
            paid_traffic_allowed_confidence=0.5,
            owner_ready=True,
            manual_review_required=True,
            recommended_channels=("landing_page", "telegram"),
            required_owner_actions=("Select one Braip offer and capture its official terms before production.",),
            evidence_requirements=("Review offer terms, checkout, refund rules, and approved promotional material.",),
            no_spend_allowed_actions=(
                "Search Braip marketplace manually and collect candidate offers.",
                "Record offer terms, checkout page and affiliate material before using the token.",
                "Use token only for future read-only smoke checks.",
            ),
            blocked_until_budget_actions=("Paid traffic tests.",),
            notes=("Account and local API token are available; no production until offer evidence is reviewed.",),
        ),
        AffiliatePlatformProfile(
            name="clickbank",
            display_name="ClickBank",
            category="digital_network",
            onboarding_status="watch_with_rules",
            primary_use_case="International marketplace after payment eligibility review.",
            affiliate_link_ease=0.78,
            commission_potential=0.8,
            payout_friction=0.68,
            compliance_complexity=0.72,
            offer_evidence_strength=0.65,
            paid_traffic_allowed_confidence=0.5,
            owner_ready=False,
            manual_review_required=True,
            recommended_channels=("landing_page", "email", "youtube_short"),
            required_owner_actions=("Accept payout eligibility constraints before investing time.",),
            evidence_requirements=("Validate customer distribution requirement, refund rate, gravity, and allowed claims.",),
            no_spend_allowed_actions=(
                "Research marketplace rules and shortlist low-risk offers.",
                "Capture payout eligibility constraints before account spend.",
            ),
            blocked_until_budget_actions=("Paid traffic tests.", "Any paid spy-tool dependency."),
            notes=("Potentially strong, but not the simplest first test.",),
        ),
        AffiliatePlatformProfile(
            name="maxweb",
            display_name="MaxWeb",
            category="cpa_network",
            onboarding_status="application_later",
            primary_use_case="CPA offers after channels and compliance profile exist.",
            affiliate_link_ease=0.45,
            commission_potential=0.86,
            payout_friction=0.72,
            compliance_complexity=0.75,
            offer_evidence_strength=0.7,
            paid_traffic_allowed_confidence=0.62,
            owner_ready=False,
            manual_review_required=True,
            recommended_channels=("landing_page", "paid_ads_after_approval"),
            required_owner_actions=("Prepare traffic method, compliance profile, and apply for approval.",),
            evidence_requirements=("Collect CPA, payout threshold, offer rules, geo, and approved creatives.",),
            no_spend_allowed_actions=(
                "Prepare application profile and compliance notes.",
                "Collect examples of allowed traffic methods from official materials.",
            ),
            blocked_until_budget_actions=("Application requiring paid traffic proof.", "Paid spy-tool dependency."),
            notes=("Promising but should wait until the factory has a clean track record.",),
        ),
        AffiliatePlatformProfile(
            name="amazon_br",
            display_name="Amazon Brasil",
            category="physical_marketplace",
            onboarding_status="manual_links_ready",
            primary_use_case="Organic deal validation and audience utility.",
            affiliate_link_ease=0.8,
            commission_potential=0.32,
            payout_friction=0.45,
            compliance_complexity=0.42,
            offer_evidence_strength=0.78,
            paid_traffic_allowed_confidence=0.25,
            owner_ready=True,
            manual_review_required=True,
            recommended_channels=("telegram", "whatsapp_manual", "instagram_organic"),
            required_owner_actions=("Finish tax/payment information before scaling.",),
            evidence_requirements=("Check price, affiliate link, stock, reviews, and product page before posting.",),
            no_spend_allowed_actions=(
                "Generate manual affiliate links for organic tests when available.",
                "Collect product URL, price evidence, reviews and stock status.",
                "Prepare Telegram/WhatsApp copy with disclosure and no paid ads.",
            ),
            blocked_until_budget_actions=("Paid traffic tests.",),
            notes=("Useful now, but not the main paid-traffic engine.",),
        ),
        AffiliatePlatformProfile(
            name="mercado_livre",
            display_name="Mercado Livre",
            category="physical_marketplace",
            onboarding_status="catalog_read_only",
            primary_use_case="Brazilian product research and organic deal validation.",
            affiliate_link_ease=0.48,
            commission_potential=0.34,
            payout_friction=0.55,
            compliance_complexity=0.45,
            offer_evidence_strength=0.74,
            paid_traffic_allowed_confidence=0.2,
            owner_ready=False,
            manual_review_required=True,
            recommended_channels=("telegram", "whatsapp_manual"),
            required_owner_actions=("Complete official affiliate access or provide an owned affiliate link manually.",),
            evidence_requirements=("Validate item page, seller reputation, price, stock, and affiliate attribution.",),
            no_spend_allowed_actions=(
                "Use catalog read-only research for product quality and price evidence.",
                "Do not publish until owned affiliate attribution exists.",
            ),
            blocked_until_budget_actions=("Paid traffic tests.", "Publication without owned affiliate attribution."),
            notes=("Adapter is read-only; it must not create links or publish listings.",),
        ),
    )


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _recommendation(
    total: float,
    profile: AffiliatePlatformProfile,
    *,
    paid_traffic: bool,
) -> str:
    if not profile.owner_ready and profile.affiliate_link_ease < 0.4:
        return "blocked"
    if paid_traffic and profile.paid_traffic_allowed_confidence < 0.7:
        return "prepare_next"
    if profile.owner_ready and profile.category == "physical_marketplace" and total >= 40.0:
        return "start_now"
    if total >= 62.0 and profile.owner_ready:
        return "start_now"
    if total >= 35.0 and not profile.owner_ready and profile.affiliate_link_ease >= 0.7:
        return "prepare_next"
    if total >= 46.0:
        return "prepare_next"
    if total >= 32.0:
        return "watch_later"
    return "blocked"
