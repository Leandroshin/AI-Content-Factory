"""Compliance checks for affiliate deals and growth funnels."""

from __future__ import annotations

from core.departments.affiliate_deals.models import (
    AffiliateDealTask,
    ComplianceCheck,
    OfferMessage,
    ProductOffer,
)


_MISLEADING_TERMS = (
    "bug da amazon",
    "preço errado garantido",
    "quase de graça",
    "compra antes que apaguem",
    "segredo vazou",
)


def review_compliance(
    task: AffiliateDealTask,
    offer: ProductOffer,
    message: OfferMessage,
) -> ComplianceCheck:
    """Validate a prepared offer before any publication step."""

    issues: list[str] = []
    warnings: list[str] = []
    disclosure = task.disclosure_text or task.campaign.disclosure_text

    if not offer.marketplace.allowed:
        issues.append("Marketplace is not allowed for this campaign.")
    if not offer.marketplace.supports_affiliate_links:
        issues.append("Marketplace does not support affiliate links in this configuration.")
    if not offer.affiliate.has_affiliate_target:
        issues.append("Affiliate URL is missing.")
    if offer.price.current_price <= 0:
        issues.append("Current price must be greater than zero.")
    if offer.price.old_price is not None and offer.price.old_price < offer.price.current_price:
        issues.append("Old price cannot be lower than current price.")
    if disclosure and disclosure not in message.body:
        issues.append("Affiliate disclosure is missing from the message.")

    body_lower = message.body.lower()
    for term in _MISLEADING_TERMS:
        if term in body_lower:
            issues.append(f"Misleading term is not allowed: {term}")

    if task.preferred_channel.lower() in ("whatsapp", "whatsapp_auto"):
        warnings.append("WhatsApp automatic publishing is blocked in this phase.")
    if not task.require_human_approval:
        warnings.append("Human approval is recommended while this vertical is being calibrated.")
    if task.auto_publish_allowed and task.preferred_channel.lower().startswith("whatsapp"):
        issues.append("Automatic WhatsApp publishing is not enabled in this phase.")

    return ComplianceCheck(
        passed=len(issues) == 0,
        issues=tuple(issues),
        warnings=tuple(warnings),
        disclosure_text=disclosure,
        requires_human_approval=True,
        automatic_whatsapp_blocked=True,
        metadata={
            "channel": task.preferred_channel,
            "marketplace": offer.marketplace.name,
        },
    )
