"""Deterministic provider quotes with no external execution side effects."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderQuoteItem:
    """One provider choice inside a media production quote."""

    department: str
    provider: str
    display_name: str
    available: bool
    estimated_cost_usd: float
    pricing_status: str
    limitation: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MediaProviderQuote:
    """A complete, non-binding media provider plan."""

    plan_id: str
    display_name: str
    estimated_duration_seconds: int
    estimated_cost_usd: float
    complete_price: bool
    executable_now: bool
    items: tuple[ProviderQuoteItem, ...]
    warning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "display_name": self.display_name,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "estimated_cost_usd": self.estimated_cost_usd,
            "complete_price": self.complete_price,
            "executable_now": self.executable_now,
            "items": tuple({
                "department": item.department,
                "provider": item.provider,
                "display_name": item.display_name,
                "available": item.available,
                "estimated_cost_usd": item.estimated_cost_usd,
                "pricing_status": item.pricing_status,
                "limitation": item.limitation,
                "metadata": dict(item.metadata),
            } for item in self.items),
            "warning": self.warning,
        }


class MediaProviderQuotePlanner:
    """Compare provider plans without calling, approving, or charging providers."""

    GEMINI_OMNI_COST_PER_SECOND_USD = 0.10
    GEMINI_OMNI_MAX_CLIP_SECONDS = 10
    GEMINI_PRICING_SOURCE = "https://ai.google.dev/gemini-api/docs/pricing"

    def quote(self, *, script: str, target_duration_seconds: int = 0) -> tuple[MediaProviderQuote, ...]:
        duration = self._duration(script, target_duration_seconds)
        local = MediaProviderQuote(
            plan_id="local_free",
            display_name="Local gratuito",
            estimated_duration_seconds=duration,
            estimated_cost_usd=0.0,
            complete_price=True,
            executable_now=True,
            items=(
                ProviderQuoteItem(
                    department="audio",
                    provider="kokoro_local",
                    display_name="Kokoro local",
                    available=True,
                    estimated_cost_usd=0.0,
                    pricing_status="free_local",
                    limitation="Voz gratuita; pronúncia e emoção ainda exigem revisão humana.",
                ),
                ProviderQuoteItem(
                    department="image",
                    provider="owned_source_assets",
                    display_name="Materiais próprios/licenciados",
                    available=True,
                    estimated_cost_usd=0.0,
                    pricing_status="free_owned_assets",
                    limitation="Não gera imagem nova; usa capturas e materiais com proveniência.",
                ),
                ProviderQuoteItem(
                    department="video",
                    provider="hyperframes_ffmpeg",
                    display_name="HyperFrames + FFmpeg",
                    available=True,
                    estimated_cost_usd=0.0,
                    pricing_status="free_local",
                    limitation="Compõe e codifica localmente; a qualidade depende dos assets de entrada.",
                ),
            ),
            warning="Plano sem custo de API. Ainda exige uma aprovação separada antes de gerar arquivos locais.",
        )
        clips = max(1, math.ceil(duration / self.GEMINI_OMNI_MAX_CLIP_SECONDS))
        video_cost = round(duration * self.GEMINI_OMNI_COST_PER_SECOND_USD, 2)
        hybrid = MediaProviderQuote(
            plan_id="hybrid_quality",
            display_name="Híbrido de maior qualidade",
            estimated_duration_seconds=duration,
            estimated_cost_usd=video_cost,
            complete_price=False,
            executable_now=False,
            items=(
                ProviderQuoteItem(
                    department="audio",
                    provider="elevenlabs",
                    display_name="ElevenLabs",
                    available=False,
                    estimated_cost_usd=0.0,
                    pricing_status="billing_blocked_quote_pending",
                    limitation="Fatura pendente; custo por produção não será presumido.",
                ),
                ProviderQuoteItem(
                    department="image",
                    provider="image_provider_pending",
                    display_name="Provider de imagem a escolher",
                    available=False,
                    estimated_cost_usd=0.0,
                    pricing_status="provider_not_selected",
                    limitation="A comparação de custo, qualidade e licença ainda não foi concluída.",
                ),
                ProviderQuoteItem(
                    department="video",
                    provider="gemini_omni_flash",
                    display_name="Gemini Omni Flash",
                    available=False,
                    estimated_cost_usd=video_cost,
                    pricing_status="official_estimate",
                    limitation="Preview pago; requer aprovação, orçamento e revisão de cada clipe.",
                    metadata={
                        "estimated_requests": clips,
                        "max_clip_seconds": self.GEMINI_OMNI_MAX_CLIP_SECONDS,
                        "pricing_source": self.GEMINI_PRICING_SOURCE,
                    },
                ),
            ),
            warning="Estimativa parcial: inclui vídeo, mas não inclui voz nem imagem. Execução bloqueada.",
        )
        return local, hybrid

    @staticmethod
    def _duration(script: str, target: int) -> int:
        if target > 0:
            return max(3, min(60, int(target)))
        words = len(script.split())
        return max(15, min(60, round(words / 2.6)))
