"""Deterministic scoring for affiliate deals."""

from __future__ import annotations

from core.departments.affiliate_deals.models import DealScore, ProductOffer


def score_deal(offer: ProductOffer) -> DealScore:
    """Score an offer with simple transparent rules.

    The output is intentionally explainable: every point comes from
    price drop, marketplace trust, coupon presence, urgency, margin fit,
    or a risk penalty.
    """

    reasons: list[str] = []
    discount = offer.discount_percent

    discount_score = min(40.0, round(discount * 1.35, 2))
    if discount >= 25:
        reasons.append("strong_discount")
    elif discount >= 10:
        reasons.append("moderate_discount")
    else:
        reasons.append("weak_discount")

    trust_score = round(max(0.0, min(1.0, offer.marketplace.trust_score)) * 20.0, 2)
    if offer.marketplace.allowed and offer.marketplace.supports_affiliate_links:
        reasons.append("trusted_marketplace")
    else:
        reasons.append("marketplace_needs_review")

    coupon_score = 15.0 if offer.has_coupon else 0.0
    if offer.has_coupon:
        reasons.append("coupon_available")

    urgency_score = {
        "low": 3.0,
        "medium": 7.0,
        "high": 10.0,
        "flash": 12.0,
    }.get(offer.urgency_level.lower(), 5.0)
    if urgency_score >= 10:
        reasons.append("time_sensitive")

    margin_score = _margin_score(offer.price.current_price)
    risk_penalty = min(35.0, len(offer.risk_flags) * 12.0)
    if offer.risk_flags:
        reasons.append("risk_flags_present")

    total = round(
        max(
            0.0,
            discount_score + trust_score + coupon_score + urgency_score + margin_score - risk_penalty,
        ),
        2,
    )

    if risk_penalty >= 24.0:
        recommendation = "skip"
        reasons.append("risk_too_high")
    elif total >= 76.0:
        recommendation = "post_now"
    elif total >= 52.0:
        recommendation = "needs_review"
    else:
        recommendation = "skip"

    return DealScore(
        score_total=total,
        discount_score=discount_score,
        trust_score=trust_score,
        coupon_score=coupon_score,
        urgency_score=urgency_score,
        margin_score=margin_score,
        risk_penalty=risk_penalty,
        recommendation=recommendation,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def _margin_score(price: float) -> float:
    if price <= 0:
        return 0.0
    if price <= 100:
        return 8.0
    if price <= 350:
        return 12.0
    if price <= 800:
        return 9.0
    return 5.0
