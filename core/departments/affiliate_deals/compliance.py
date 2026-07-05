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

_DIGITAL_PRODUCT_MARKETPLACES = (
    "hotmart",
    "kiwify",
)

_REGULATED_VERTICAL_MARKERS = (
    "saude",
    "saúde",
    "bem_estar",
    "bem-estar",
    "wellness",
    "sexual_wellness",
    "sexual wellness",
    "ejaculacao",
    "ejaculação",
    "disfuncao",
    "disfunção",
)

_CURE_CLAIM_TERMS = (
    "cura definitiva",
    "curar",
    "tratamento médico",
    "tratamento medico",
    "resultado garantido",
    "garantia de resultado",
)

_PERSONAL_ATTRIBUTE_TERMS = (
    "você tem",
    "voce tem",
    "você sofre",
    "voce sofre",
    "seu problema",
    "sua doença",
    "sua doenca",
)

_SEXUAL_PERFORMANCE_TERMS = (
    "prazer garantido",
    "performance sexual",
    "melhorar desempenho sexual",
    "aumentar desejo",
    "ficar potente",
)

_EXPLICIT_CONTENT_TERMS = (
    "porn",
    "pornografia",
    "nudez explícita",
    "nudez explicita",
    "conteúdo adulto explícito",
    "conteudo adulto explicito",
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

    digital_product = _is_digital_product(offer)
    regulated_vertical = _is_regulated_vertical(task, offer)
    manual_source_reviewed = _manual_source_reviewed(offer)
    educational_positioning = _educational_positioning(offer)

    if digital_product:
        if not manual_source_reviewed:
            issues.append("Digital product source must be manually reviewed before promotion.")
        if not offer.metadata.get("platform_policy_reviewed", False):
            warnings.append("Digital product platform policy should be reviewed before paid distribution.")

    if regulated_vertical:
        if not educational_positioning:
            issues.append("Regulated digital product must be positioned as educational content.")
        if not task.require_human_approval:
            issues.append("Regulated digital product requires human approval.")
        for term in _CURE_CLAIM_TERMS:
            if term in body_lower:
                issues.append(f"Medical cure/treatment claim is not allowed: {term}")
        for term in _PERSONAL_ATTRIBUTE_TERMS:
            if term in body_lower:
                issues.append(f"Personal attribute targeting is not allowed: {term}")
        for term in _SEXUAL_PERFORMANCE_TERMS:
            if term in body_lower:
                issues.append(f"Sexual performance promise is not allowed: {term}")
        if bool(offer.metadata.get("contains_explicit_or_erotic_content", False)):
            issues.append("Explicit or erotic content is not allowed in this affiliate flow.")
        for term in _EXPLICIT_CONTENT_TERMS:
            if term in body_lower:
                issues.append(f"Explicit content term is not allowed: {term}")
        if task.preferred_channel.lower().startswith("whatsapp"):
            warnings.append("Regulated digital products should stay out of automated WhatsApp flows.")

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
            "digital_product": digital_product,
            "regulated_vertical": regulated_vertical,
            "manual_source_reviewed": manual_source_reviewed,
            "educational_positioning": educational_positioning,
        },
    )


def _is_digital_product(offer: ProductOffer) -> bool:
    marketplace = offer.marketplace.name.lower()
    product_format = str(offer.metadata.get("product_format", "")).lower()
    return (
        marketplace in _DIGITAL_PRODUCT_MARKETPLACES
        or product_format in ("digital", "digital_course", "infoproduct", "infoproduto")
    )


def _is_regulated_vertical(task: AffiliateDealTask, offer: ProductOffer) -> bool:
    values = (
        offer.category,
        offer.audience,
        offer.metadata.get("regulated_vertical", ""),
        offer.metadata.get("vertical", ""),
        task.campaign.niche,
        task.campaign.campaign_type,
    )
    text = " ".join(str(v).lower() for v in values)
    return any(marker in text for marker in _REGULATED_VERTICAL_MARKERS)


def _manual_source_reviewed(offer: ProductOffer) -> bool:
    return bool(
        offer.metadata.get("manual_source_reviewed", False)
        or offer.marketplace.metadata.get("manual_source_reviewed", False)
        or offer.marketplace.metadata.get("human_reviewed", False)
    )


def _educational_positioning(offer: ProductOffer) -> bool:
    positioning = str(offer.metadata.get("positioning", "")).lower()
    product_format = str(offer.metadata.get("product_format", "")).lower()
    if positioning:
        return positioning in ("educational", "educacional", "behavioral", "comportamental")
    return product_format in (
        "course",
        "curso",
        "digital_course",
    )
