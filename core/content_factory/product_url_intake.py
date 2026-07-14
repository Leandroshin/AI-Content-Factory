"""Controlled product URL intake for affiliate research.

The intake performs one evidence request per owner-provided URL, extracts
structured product metadata, and converts it into the existing ProductCandidate
contract. It is intentionally not a crawler and never fabricates missing data.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from core.departments.product_research import ProductCandidate
from core.tools.http import HttpClient


class ProductUrlIntakeStatus(StrEnum):
    """Outcome of one controlled URL intake."""

    READY = "ready"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"
    BLOCKED = "blocked"
    FETCH_FAILED = "fetch_failed"


@dataclass(frozen=True, slots=True)
class MarketplaceProfile:
    """Allowlisted marketplace identity and default trust score."""

    key: str
    display_name: str
    domains: tuple[str, ...]
    trust_score: float


@dataclass(frozen=True, slots=True)
class ProductUrlEvidence:
    """Auditable evidence extracted from one product page."""

    requested_url: str
    canonical_url: str = ""
    marketplace: str = ""
    fetched_at: float = 0.0
    http_status: int = 0
    extractor: str = "none"
    content_sha256: str = ""
    product_name: str = ""
    current_price: float = 0.0
    old_price: float | None = None
    currency: str = ""
    image_url: str = ""
    seller: str = ""
    availability: str = ""
    sku: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "requested_url": self.requested_url,
            "canonical_url": self.canonical_url,
            "marketplace": self.marketplace,
            "fetched_at": self.fetched_at,
            "http_status": self.http_status,
            "extractor": self.extractor,
            "content_sha256": self.content_sha256,
            "product_name": self.product_name,
            "current_price": self.current_price,
            "old_price": self.old_price,
            "currency": self.currency,
            "image_url": self.image_url,
            "seller": self.seller,
            "availability": self.availability,
            "sku": self.sku,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ProductUrlIntakeResult:
    """Result of one intake, including manual-review guidance."""

    status: ProductUrlIntakeStatus
    evidence: ProductUrlEvidence
    candidate: ProductCandidate | None = None
    error: str = ""
    manual_fields: tuple[str, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> bool:
        return self.candidate is not None and self.status in {
            ProductUrlIntakeStatus.READY,
            ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW,
        }


@dataclass(frozen=True, slots=True)
class ProductUrlBatchResult:
    """Batch handoff from URL intake to Product Research."""

    results: tuple[ProductUrlIntakeResult, ...] = field(default_factory=tuple)

    @property
    def candidates(self) -> tuple[ProductCandidate, ...]:
        return tuple(
            result.candidate
            for result in self.results
            if result.usable and result.candidate
        )

    @property
    def blocked_count(self) -> int:
        return sum(
            result.status == ProductUrlIntakeStatus.BLOCKED for result in self.results
        )

    @property
    def review_count(self) -> int:
        return sum(
            result.status == ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW
            for result in self.results
        )


DEFAULT_MARKETPLACES: tuple[MarketplaceProfile, ...] = (
    MarketplaceProfile("amazon", "Amazon", ("amazon.com.br",), 0.92),
    MarketplaceProfile(
        "mercado_livre", "Mercado Livre", ("mercadolivre.com.br", "meli.la"), 0.86
    ),
    MarketplaceProfile("shopee", "Shopee", ("shopee.com.br",), 0.76),
    MarketplaceProfile("adidas", "Adidas", ("adidas.com.br",), 0.88),
    MarketplaceProfile("hotmart", "Hotmart", ("hotmart.com",), 0.78),
    MarketplaceProfile(
        "digistore24",
        "Digistore24",
        ("digistore24.com", "digistore24-app.com"),
        0.74,
    ),
    MarketplaceProfile("braip", "Braip", ("braip.com", "ev.braip.com"), 0.76),
    MarketplaceProfile("tiktok_shop", "TikTok Shop", ("tiktok.com",), 0.72),
    MarketplaceProfile("kiwify", "Kiwify", ("kiwify.com.br",), 0.74),
)


class ProductUrlIntake:
    """Fetch and normalize owner-provided product URLs without crawling."""

    _MAX_HTML_CHARS = 2_000_000

    def __init__(
        self,
        http_client: HttpClient,
        *,
        marketplaces: tuple[MarketplaceProfile, ...] = DEFAULT_MARKETPLACES,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._http_client = http_client
        self._marketplaces = marketplaces
        self._clock = clock

    def intake(
        self,
        url: str,
        *,
        affiliate_url: str = "",
        overrides: Mapping[str, Any] | None = None,
    ) -> ProductUrlIntakeResult:
        """Collect one URL and preserve explicit manual overrides as evidence."""
        overrides = dict(overrides or {})
        normalized, profile, error = self._validate_url(url)
        if error or profile is None:
            evidence = ProductUrlEvidence(
                requested_url=str(url).strip(),
                fetched_at=self._clock(),
                warnings=("url_blocked",),
            )
            return ProductUrlIntakeResult(
                status=ProductUrlIntakeStatus.BLOCKED,
                evidence=evidence,
                error=error or "Marketplace is not allowlisted.",
            )

        try:
            response = self._http_client.get(
                normalized,
                headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "User-Agent": "AIContentFactoryProductEvidence/1.0",
                },
                timeout=20.0,
            )
        except Exception as exc:
            return self._fallback_after_fetch_failure(
                normalized,
                profile,
                affiliate_url,
                overrides,
                f"{type(exc).__name__}: {exc}",
            )

        if not 200 <= response.status_code < 300:
            return self._fallback_after_fetch_failure(
                normalized,
                profile,
                affiliate_url,
                overrides,
                f"Marketplace returned HTTP {response.status_code}.",
                http_status=response.status_code,
            )

        html = _body_as_text(response.body)
        warnings: list[str] = []
        if len(html) > self._MAX_HTML_CHARS:
            html = html[: self._MAX_HTML_CHARS]
            warnings.append("html_truncated_for_safe_parsing")
        parsed = _extract_product_page(html, normalized)
        cleaned_overrides = _clean_overrides(overrides)
        values = {**parsed.values, **cleaned_overrides}
        warnings.extend(parsed.warnings)
        warnings.extend(f"manual_override_{key}" for key in cleaned_overrides)
        evidence = self._build_evidence(
            requested_url=normalized,
            profile=profile,
            http_status=response.status_code,
            extractor=parsed.extractor,
            html=html,
            values=values,
            warnings=warnings,
        )
        manual_fields = _manual_fields(_evidence_values(evidence))
        evidence = replace(
            evidence,
            warnings=tuple(
                dict.fromkeys(
                    (
                        *evidence.warnings,
                        *(f"manual_{field}_required" for field in manual_fields),
                    )
                )
            ),
        )
        candidate = self._candidate_from_evidence(
            evidence,
            profile,
            affiliate_url=affiliate_url,
            overrides=overrides,
        )
        status = (
            ProductUrlIntakeStatus.READY
            if not manual_fields
            else ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW
        )
        return ProductUrlIntakeResult(
            status=status,
            evidence=evidence,
            candidate=candidate,
            manual_fields=manual_fields,
        )

    def intake_many(
        self,
        urls: Iterable[str],
        *,
        affiliate_urls: Mapping[str, str] | None = None,
        overrides_by_url: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> ProductUrlBatchResult:
        affiliate_urls = affiliate_urls or {}
        overrides_by_url = overrides_by_url or {}
        results = tuple(
            self.intake(
                url,
                affiliate_url=str(affiliate_urls.get(url, "")),
                overrides=overrides_by_url.get(url),
            )
            for url in urls
        )
        return ProductUrlBatchResult(results=results)

    def _validate_url(
        self,
        raw_url: str,
    ) -> tuple[str, MarketplaceProfile | None, str]:
        value = str(raw_url).strip()
        try:
            parsed = urlsplit(value)
        except ValueError:
            return value, None, "URL is malformed."
        if parsed.scheme.lower() != "https":
            return value, None, "Only HTTPS product URLs are accepted."
        if parsed.username or parsed.password:
            return value, None, "URLs containing credentials are blocked."
        host = (parsed.hostname or "").lower().rstrip(".")
        if not host:
            return value, None, "URL host is required."
        if _is_private_host(host):
            return value, None, "Private, local, and IP hosts are blocked."
        profile = next(
            (
                item
                for item in self._marketplaces
                if any(
                    host == domain or host.endswith(f".{domain}")
                    for domain in item.domains
                )
            ),
            None,
        )
        if profile is None:
            return value, None, f"Marketplace host is not allowlisted: {host}"
        normalized = urlunsplit(
            ("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, "")
        )
        return normalized, profile, ""

    def _fallback_after_fetch_failure(
        self,
        url: str,
        profile: MarketplaceProfile,
        affiliate_url: str,
        overrides: Mapping[str, Any],
        error: str,
        *,
        http_status: int = 0,
    ) -> ProductUrlIntakeResult:
        cleaned = _clean_overrides(overrides)
        evidence = self._build_evidence(
            requested_url=url,
            profile=profile,
            http_status=http_status,
            extractor="manual_fallback",
            html="",
            values=cleaned,
            warnings=("fetch_failed", "manual_evidence_required"),
        )
        manual_fields = _manual_fields(_evidence_values(evidence))
        candidate = None
        status = ProductUrlIntakeStatus.FETCH_FAILED
        if not {"product_name", "current_price"}.intersection(manual_fields):
            candidate = self._candidate_from_evidence(
                evidence,
                profile,
                affiliate_url=affiliate_url,
                overrides=overrides,
            )
            status = ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW
        return ProductUrlIntakeResult(
            status=status,
            evidence=evidence,
            candidate=candidate,
            error=error,
            manual_fields=manual_fields,
        )

    def _build_evidence(
        self,
        *,
        requested_url: str,
        profile: MarketplaceProfile,
        http_status: int,
        extractor: str,
        html: str,
        values: Mapping[str, Any],
        warnings: Iterable[str],
    ) -> ProductUrlEvidence:
        warning_list = list(warnings)
        canonical_value = str(values.get("canonical_url", requested_url)).strip()
        canonical_url = _safe_marketplace_url(canonical_value, requested_url, profile)
        if canonical_value and canonical_url != canonical_value:
            warning_list.append("canonical_url_rejected")
        image_value = str(values.get("image_url", "")).strip()
        image_url = _safe_public_https_url(image_value)
        if image_value and not image_url:
            warning_list.append("image_url_rejected")
        return ProductUrlEvidence(
            requested_url=requested_url,
            canonical_url=canonical_url,
            marketplace=profile.key,
            fetched_at=self._clock(),
            http_status=http_status,
            extractor=extractor,
            content_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest()
            if html
            else "",
            product_name=str(values.get("product_name", "")).strip(),
            current_price=_price(values.get("current_price")),
            old_price=_optional_price(values.get("old_price")),
            currency=str(values.get("currency", "")).strip().upper(),
            image_url=image_url,
            seller=str(values.get("seller", "")).strip(),
            availability=str(values.get("availability", "")).strip(),
            sku=str(values.get("sku", "")).strip(),
            warnings=tuple(dict.fromkeys(str(item) for item in warning_list if item)),
        )

    def _candidate_from_evidence(
        self,
        evidence: ProductUrlEvidence,
        profile: MarketplaceProfile,
        *,
        affiliate_url: str,
        overrides: Mapping[str, Any],
    ) -> ProductCandidate:
        risk_flags = list(overrides.get("risk_flags", ()))
        if evidence.current_price <= 0:
            risk_flags.append("price_unverified")
        if not evidence.image_url:
            risk_flags.append("image_unverified")
        notes = list(overrides.get("notes", ()))
        notes.extend(evidence.warnings)
        return ProductCandidate(
            product_name=evidence.product_name,
            marketplace=profile.key,
            category=str(overrides.get("category", "")),
            niche=str(overrides.get("niche", "")),
            source_url=evidence.canonical_url or evidence.requested_url,
            affiliate_url=affiliate_url.strip(),
            image_url=evidence.image_url,
            current_price=evidence.current_price,
            old_price=evidence.old_price,
            commission_percent=_price(overrides.get("commission_percent")),
            marketplace_trust=profile.trust_score,
            competition_level=str(overrides.get("competition_level", "medium")),
            saturation_level=str(overrides.get("saturation_level", "medium")),
            risk_flags=tuple(dict.fromkeys(risk_flags)),
            notes=tuple(dict.fromkeys(notes)),
            metadata={
                **dict(overrides.get("metadata", {})),
                "currency": evidence.currency,
                "seller": evidence.seller,
                "availability": evidence.availability,
                "sku": evidence.sku,
                "evidence_sha256": evidence.content_sha256,
                "evidence_extractor": evidence.extractor,
                "evidence_fetched_at": evidence.fetched_at,
                "source_label": profile.display_name,
            },
        )


@dataclass(frozen=True, slots=True)
class _ParsedPage:
    values: dict[str, Any] = field(default_factory=dict)
    extractor: str = "none"
    warnings: tuple[str, ...] = field(default_factory=tuple)


class _ProductHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.canonical_url = ""
        self.title_parts: list[str] = []
        self.json_ld: list[str] = []
        self._in_title = False
        self._in_json_ld = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "meta":
            key = (
                values.get("property")
                or values.get("name")
                or values.get("itemprop")
                or ""
            ).lower()
            if key and values.get("content"):
                self.meta[key] = values["content"].strip()
        elif tag.lower() == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical_url = values.get("href", "").strip()
        elif tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "script" and "ld+json" in values.get("type", "").lower():
            self._in_json_ld = True
            self._json_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script" and self._in_json_ld:
            self._in_json_ld = False
            value = "".join(self._json_parts).strip()
            if value:
                self.json_ld.append(value)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_json_ld:
            self._json_parts.append(data)


def _extract_product_page(html: str, base_url: str) -> _ParsedPage:
    parser = _ProductHtmlParser()
    try:
        parser.feed(html)
    except Exception:
        return _ParsedPage(warnings=("html_parse_incomplete",))

    product = _find_json_ld_product(parser.json_ld)
    values: dict[str, Any] = {}
    extractor = "none"
    warnings: list[str] = []
    if product:
        extractor = "json_ld_product"
        offers = product.get("offers", {})
        if isinstance(offers, list):
            offers = next((item for item in offers if isinstance(item, dict)), {})
        if not isinstance(offers, dict):
            offers = {}
        values.update(
            {
                "product_name": product.get("name", ""),
                "image_url": _first_image(product.get("image")),
                "current_price": offers.get("price", offers.get("lowPrice", "")),
                "old_price": offers.get("highPrice"),
                "currency": offers.get("priceCurrency", ""),
                "availability": _schema_tail(offers.get("availability", "")),
                "seller": _nested_name(offers.get("seller"))
                or _nested_name(product.get("brand")),
                "sku": product.get("sku", product.get("productID", "")),
            }
        )
    else:
        warnings.append("json_ld_product_missing")

    meta = parser.meta
    fallback = {
        "product_name": meta.get("og:title")
        or meta.get("twitter:title")
        or "".join(parser.title_parts).strip(),
        "image_url": meta.get("og:image") or meta.get("twitter:image") or "",
        "current_price": meta.get("product:price:amount")
        or meta.get("og:price:amount")
        or "",
        "currency": meta.get("product:price:currency")
        or meta.get("og:price:currency")
        or "",
        "availability": meta.get("product:availability", ""),
    }
    for key, value in fallback.items():
        if not values.get(key) and value:
            values[key] = value
            if extractor == "none":
                extractor = "open_graph"
    canonical = parser.canonical_url or meta.get("og:url") or base_url
    values["canonical_url"] = urljoin(base_url, canonical)
    if extractor == "none":
        warnings.append("structured_product_metadata_missing")
    return _ParsedPage(values=values, extractor=extractor, warnings=tuple(warnings))


def _find_json_ld_product(documents: Iterable[str]) -> dict[str, Any]:
    for raw in documents:
        try:
            loaded = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _walk_json(loaded):
            node_type = node.get("@type", "")
            types = node_type if isinstance(node_type, list) else [node_type]
            if any(str(item).lower() == "product" for item in types):
                return node
    return {}


def _walk_json(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def _body_as_text(body: Any) -> str:
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    if isinstance(body, str):
        return body
    return json.dumps(body, ensure_ascii=False) if body is not None else ""


def _is_private_host(host: str) -> bool:
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return not address.is_global


def _safe_marketplace_url(
    value: str,
    fallback: str,
    profile: MarketplaceProfile,
) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return fallback
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() != "https"
        or parsed.username
        or parsed.password
        or _is_private_host(host)
        or not any(
            host == domain or host.endswith(f".{domain}") for domain in profile.domains
        )
    ):
        return fallback
    return urlunsplit(
        ("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, "")
    )


def _safe_public_https_url(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() != "https"
        or parsed.username
        or parsed.password
        or not host
        or _is_private_host(host)
    ):
        return ""
    return urlunsplit(
        ("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, "")
    )


def _clean_overrides(values: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "product_name",
        "current_price",
        "old_price",
        "currency",
        "image_url",
        "seller",
        "availability",
        "sku",
        "canonical_url",
    }
    return {
        key: value
        for key, value in values.items()
        if key in allowed and value not in (None, "")
    }


def _manual_fields(values: Mapping[str, Any]) -> tuple[str, ...]:
    missing = []
    if not str(values.get("product_name", "")).strip():
        missing.append("product_name")
    if _price(values.get("current_price")) <= 0:
        missing.append("current_price")
    if not str(values.get("image_url", "")).strip():
        missing.append("image_url")
    return tuple(missing)


def _evidence_values(evidence: ProductUrlEvidence) -> dict[str, Any]:
    return {
        "product_name": evidence.product_name,
        "current_price": evidence.current_price,
        "image_url": evidence.image_url,
    }


def _price(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(max(0.0, float(value)), 2)
    raw_text = str(value).strip()
    is_brl_display = "R$" in raw_text
    text = raw_text.replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif is_brl_display and text.count(".") == 1 and len(text.rsplit(".", 1)[-1]) == 3:
        text = text.replace(".", "")
    try:
        return round(max(0.0, float(text)), 2)
    except ValueError:
        return 0.0


def _optional_price(value: Any) -> float | None:
    parsed = _price(value)
    return parsed if parsed > 0 else None


def _first_image(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return next((str(item) for item in value if isinstance(item, str)), "")
    if isinstance(value, dict):
        return str(value.get("url", value.get("contentUrl", "")))
    return ""


def _nested_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name", ""))
    return str(value) if isinstance(value, str) else ""


def _schema_tail(value: Any) -> str:
    return str(value).rsplit("/", maxsplit=1)[-1] if value else ""
