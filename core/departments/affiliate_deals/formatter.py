"""Offer copy formatting for affiliate deal channels."""

from __future__ import annotations

from core.departments.affiliate_deals.models import (
    DEFAULT_DISCLOSURE,
    OfferCreative,
    OfferMessage,
    ProductOffer,
)


def build_offer_message(
    offer: ProductOffer,
    *,
    channel: str = "telegram",
    disclosure_text: str = DEFAULT_DISCLOSURE,
) -> OfferMessage:
    """Build a compact Telegram/WhatsApp-style affiliate message."""

    title = f"{_category_icon(offer.category)} {offer.product_name}".strip()
    price_line = _price_line(offer)
    coupon_line = f"🎟 Cupom: {offer.coupon.code}" if offer.coupon.present else ""
    link = offer.affiliate.public_url
    hashtags = _hashtags(offer)

    body_parts = [
        title,
        "",
        price_line,
        coupon_line,
        "",
        "🔗 Pegue aqui:",
        link,
        "",
        disclosure_text,
    ]
    body = "\n".join(part for part in body_parts if part != "")

    return OfferMessage(
        channel=channel,
        title=title,
        body=body,
        disclosure_text=disclosure_text,
        hashtags=hashtags,
        character_count=len(body),
        metadata={
            "marketplace": offer.marketplace.name,
            "category": offer.category,
        },
    )


def build_offer_creative(offer: ProductOffer) -> OfferCreative:
    """Prepare a creative brief for a visual deal asset."""

    discount = offer.discount_percent
    callouts = [
        f"{discount:.0f}% OFF" if discount else "Oferta selecionada",
        f"Por {_money(offer.price.current_price)}",
    ]
    if offer.coupon.present:
        callouts.append(f"Cupom {offer.coupon.code}")
    if offer.price.shipping_notes:
        callouts.append(offer.price.shipping_notes)

    return OfferCreative(
        creative_type="offer_card",
        headline=offer.product_name,
        image_url=offer.image_url,
        layout="marketplace_price_drop_card",
        color_theme=_theme_for_category(offer.category),
        callouts=tuple(callouts),
        requires_image_enhancement=bool(offer.image_url),
        metadata={
            "marketplace": offer.marketplace.display_name,
            "source_label": offer.source_label,
        },
    )


def _price_line(offer: ProductOffer) -> str:
    current = _money(offer.price.current_price)
    terms = f" {offer.price.payment_terms}" if offer.price.payment_terms else ""
    if offer.price.old_price and offer.price.old_price > offer.price.current_price:
        return f"🔥 De {_money(offer.price.old_price)} por {current}{terms}"
    return f"🔥 Por {current}{terms}"


def _money(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${formatted}"


def _category_icon(category: str) -> str:
    key = category.lower()
    if any(part in key for part in ("game", "gamer", "controle", "console")):
        return "🎮"
    if any(part in key for part in ("monitor", "tech", "eletron", "comput")):
        return "🖥"
    if any(part in key for part in ("audio", "headset", "fone")):
        return "🎧"
    if any(part in key for part in ("casa", "cozinha")):
        return "🏠"
    return "🛒"


def _theme_for_category(category: str) -> str:
    key = category.lower()
    if "gamer" in key or "game" in key:
        return "tech_blue"
    if "casa" in key or "cozinha" in key:
        return "home_green"
    if "beleza" in key:
        return "beauty_magenta"
    return "marketplace_neutral"


def _hashtags(offer: ProductOffer) -> tuple[str, ...]:
    tags = ["#ofertas", f"#{offer.marketplace.name.lower()}"]
    if offer.category:
        tags.append("#" + offer.category.lower().replace(" ", ""))
    return tuple(dict.fromkeys(tags))
