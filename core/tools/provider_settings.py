"""Provider control-center state for future settings panels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.tools.adapters.models import ExecutionMode
from core.tools.provider_control import (
    ProviderBudget,
    ProviderBudgetGuard,
    ProviderPricing,
    ProviderUsageSummary,
)
from core.tools.secrets.models import SecretKey
from core.tools.secrets.provider import SecretProvider


@dataclass(frozen=True, slots=True)
class ProviderSecretSlot:
    """UI-safe metadata for one provider secret slot."""

    key: str
    label: str
    required: bool = True
    configured: bool = False
    masked_hint: str = ""

    def with_status(self, configured: bool, masked_hint: str = "") -> ProviderSecretSlot:
        return ProviderSecretSlot(
            key=self.key,
            label=self.label,
            required=self.required,
            configured=configured,
            masked_hint=masked_hint if configured else "",
        )


@dataclass(frozen=True, slots=True)
class ProviderControlProfile:
    """Configurable provider profile for settings/UI state."""

    provider: str
    display_name: str
    category: str
    execution_mode: ExecutionMode = ExecutionMode.MOCK
    enabled: bool = True
    budget: ProviderBudget | None = None
    pricing: tuple[ProviderPricing, ...] = field(default_factory=tuple)
    secret_slots: tuple[ProviderSecretSlot, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_mode(self, mode: ExecutionMode) -> ProviderControlProfile:
        return self._replace(execution_mode=mode)

    def with_enabled(self, enabled: bool) -> ProviderControlProfile:
        return self._replace(enabled=enabled)

    def with_budget(self, budget: ProviderBudget) -> ProviderControlProfile:
        return self._replace(budget=budget)

    def with_pricing(self, pricing: tuple[ProviderPricing, ...]) -> ProviderControlProfile:
        return self._replace(pricing=pricing)

    def with_secret_slots(self, slots: tuple[ProviderSecretSlot, ...]) -> ProviderControlProfile:
        return self._replace(secret_slots=slots)

    def _replace(self, **changes: Any) -> ProviderControlProfile:
        data = {
            "provider": self.provider,
            "display_name": self.display_name,
            "category": self.category,
            "execution_mode": self.execution_mode,
            "enabled": self.enabled,
            "budget": self.budget,
            "pricing": self.pricing,
            "secret_slots": self.secret_slots,
            "metadata": dict(self.metadata),
        }
        data.update(changes)
        return ProviderControlProfile(**data)


@dataclass(frozen=True, slots=True)
class ProviderControlSnapshot:
    """UI-ready state for one provider control card."""

    provider: str
    display_name: str
    category: str
    status: str
    enabled: bool
    execution_mode: str
    owner_approved: bool
    required_secret_keys: tuple[str, ...] = field(default_factory=tuple)
    configured_secret_keys: tuple[str, ...] = field(default_factory=tuple)
    missing_secret_keys: tuple[str, ...] = field(default_factory=tuple)
    secret_hints: dict[str, str] = field(default_factory=dict)
    max_cost_usd: float = 0.0
    max_units: int = 0
    max_requests: int = 0
    pricing_operations: tuple[str, ...] = field(default_factory=tuple)
    usage_summary: ProviderUsageSummary | None = None
    can_execute_real: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe panel state."""
        summary = self.usage_summary
        return {
            "provider": self.provider,
            "display_name": self.display_name,
            "category": self.category,
            "status": self.status,
            "enabled": self.enabled,
            "execution_mode": self.execution_mode,
            "owner_approved": self.owner_approved,
            "required_secret_keys": self.required_secret_keys,
            "configured_secret_keys": self.configured_secret_keys,
            "missing_secret_keys": self.missing_secret_keys,
            "secret_hints": dict(self.secret_hints),
            "max_cost_usd": self.max_cost_usd,
            "max_units": self.max_units,
            "max_requests": self.max_requests,
            "pricing_operations": self.pricing_operations,
            "usage_summary": None if summary is None else {
                "requests": summary.requests,
                "successes": summary.successes,
                "failures": summary.failures,
                "billable_units": summary.billable_units,
                "estimated_cost_usd": summary.estimated_cost_usd,
            },
            "can_execute_real": self.can_execute_real,
            "metadata": dict(self.metadata),
        }


class ProviderControlCenter:
    """Operational state behind a future provider settings panel."""

    def __init__(
        self,
        *,
        secret_provider: SecretProvider | None = None,
        budget_guard: ProviderBudgetGuard | None = None,
    ) -> None:
        self._secret_provider = secret_provider
        self._budget_guard = budget_guard or ProviderBudgetGuard()
        self._profiles: dict[str, ProviderControlProfile] = {}

    @property
    def budget_guard(self) -> ProviderBudgetGuard:
        """Return the shared guard used by adapters."""
        return self._budget_guard

    @property
    def secret_provider(self) -> SecretProvider | None:
        """Return the configured secret provider, if any."""
        return self._secret_provider

    def register_profile(self, profile: ProviderControlProfile) -> ProviderControlProfile:
        """Register or replace one provider profile."""
        refreshed = self._refresh_secret_slots(profile)
        self._profiles[self._key(profile.provider)] = refreshed
        self._sync_guard(refreshed)
        return refreshed

    def register_elevenlabs(
        self,
        *,
        unit_cost_usd: float = 0.0,
        max_cost_usd: float = 0.0,
        max_units: int = 0,
        max_requests: int = 0,
        execution_mode: ExecutionMode = ExecutionMode.MOCK,
    ) -> ProviderControlProfile:
        """Register the default ElevenLabs control profile."""
        provider = "elevenlabs"
        budget = ProviderBudget(
            provider=provider,
            owner_approved=False,
            max_cost_usd=max_cost_usd,
            max_units=max_units,
            max_requests=max_requests,
            notes="Owner approval required before REAL TTS usage.",
        )
        pricing = (ProviderPricing(
            provider=provider,
            operation="synthesize",
            unit_name="characters",
            unit_cost_usd=unit_cost_usd,
            pricing_note="Estimated character-based TTS cost for planning.",
        ),)
        profile = ProviderControlProfile(
            provider=provider,
            display_name="ElevenLabs",
            category="audio",
            execution_mode=execution_mode,
            budget=budget,
            pricing=pricing,
            secret_slots=(ProviderSecretSlot(
                key="api_key",
                label="ElevenLabs API Key",
                required=True,
            ),),
            metadata={"capabilities": ("speech_generation", "voice_clone")},
        )
        return self.register_profile(profile)

    def register_telegram(
        self,
        *,
        max_messages: int = 0,
        max_requests: int = 0,
        execution_mode: ExecutionMode = ExecutionMode.MOCK,
    ) -> ProviderControlProfile:
        """Register the default Telegram Bot API control profile."""
        provider = "telegram"
        budget = ProviderBudget(
            provider=provider,
            owner_approved=False,
            max_cost_usd=0.0,
            max_units=max(0, int(max_messages)),
            max_requests=max(0, int(max_requests)),
            notes="Owner approval required before REAL Telegram publishing.",
        )
        pricing = (
            ProviderPricing(
                provider=provider,
                operation="send_message",
                unit_name="messages",
                unit_cost_usd=0.0,
                pricing_note="Telegram Bot API is treated as zero-cost; limits prevent spam.",
            ),
            ProviderPricing(
                provider=provider,
                operation="get_me",
                unit_name="requests",
                unit_cost_usd=0.0,
                pricing_note="Bot validation request.",
            ),
        )
        profile = ProviderControlProfile(
            provider=provider,
            display_name="Telegram Bot API",
            category="publishing",
            execution_mode=execution_mode,
            budget=budget,
            pricing=pricing,
            secret_slots=(ProviderSecretSlot(
                key="bot_token",
                label="Telegram Bot Token",
                required=True,
            ),),
            metadata={"capabilities": ("social_media", "telegram_publishing")},
        )
        return self.register_profile(profile)

    def register_meta_ads(
        self,
        *,
        max_requests: int = 100,
        execution_mode: ExecutionMode = ExecutionMode.MOCK,
        api_version: str = "",
        ad_account_id: str = "",
    ) -> ProviderControlProfile:
        """Register the strictly read-only Meta Marketing API profile."""
        provider = "meta_marketing"
        budget = ProviderBudget(
            provider=provider,
            owner_approved=False,
            max_cost_usd=0.0,
            max_units=max(0, int(max_requests)),
            max_requests=max(0, int(max_requests)),
            notes="Owner approval and request cap required for REAL read-only analytics.",
        )
        pricing = tuple(
            ProviderPricing(
                provider=provider,
                operation=operation,
                unit_name="requests",
                unit_cost_usd=0.0,
                pricing_note="Meta read-only API request; no ad spend action is available.",
            )
            for operation in (
                "get_permissions",
                "list_ad_accounts",
                "get_ad_account",
                "list_campaigns",
                "get_insights",
            )
        )
        profile = ProviderControlProfile(
            provider=provider,
            display_name="Meta Ads Analytics",
            category="analytics",
            execution_mode=execution_mode,
            budget=budget,
            pricing=pricing,
            secret_slots=(ProviderSecretSlot(
                key="meta_access_token",
                label="Meta Read-Only Access Token",
                required=True,
            ),),
            metadata={
                "capabilities": ("social_media", "read_only_analytics"),
                "read_only": True,
                "api_version": api_version,
                "ad_account_id": ad_account_id,
                "write_actions_available": False,
            },
        )
        return self.register_profile(profile)

    def register_mercado_livre(
        self,
        *,
        max_requests: int = 100,
        execution_mode: ExecutionMode = ExecutionMode.MOCK,
        site_id: str = "MLB",
    ) -> ProviderControlProfile:
        """Register the strictly read-only Mercado Livre catalog profile."""
        provider = "mercado_livre"
        budget = ProviderBudget(
            provider=provider,
            owner_approved=False,
            max_cost_usd=0.0,
            max_units=max(0, int(max_requests)),
            max_requests=max(0, int(max_requests)),
            notes="Owner approval and request cap required for REAL catalog reads.",
        )
        pricing = tuple(
            ProviderPricing(
                provider=provider,
                operation=operation,
                unit_name="requests",
                unit_cost_usd=0.0,
                pricing_note="Read-only catalog request; no sale or listing action is available.",
            )
            for operation in ("get_item", "search_items", "multiget_items", "get_category")
        )
        profile = ProviderControlProfile(
            provider=provider,
            display_name="Mercado Livre Catalog",
            category="commerce_research",
            execution_mode=execution_mode,
            budget=budget,
            pricing=pricing,
            secret_slots=(ProviderSecretSlot(
                key="mercado_livre_access_token",
                label="Mercado Livre OAuth Access Token",
                required=True,
            ),),
            metadata={
                "capabilities": ("web_search", "catalog_read"),
                "read_only": True,
                "site_id": site_id,
                "write_actions_available": False,
            },
        )
        return self.register_profile(profile)

    def register_gemini_omni(
        self,
        *,
        unit_cost_usd: float = 0.10,
        max_cost_usd: float = 0.0,
        max_seconds: int = 0,
        max_requests: int = 0,
        execution_mode: ExecutionMode = ExecutionMode.MOCK,
    ) -> ProviderControlProfile:
        """Register the paid Gemini Omni Flash video provider profile."""
        provider = "gemini_omni_flash"
        budget = ProviderBudget(
            provider=provider,
            owner_approved=False,
            max_cost_usd=max(0.0, float(max_cost_usd)),
            max_units=max(0, int(max_seconds)),
            max_requests=max(0, int(max_requests)),
            notes="Owner approval required before paid REAL video generation.",
        )
        pricing = (ProviderPricing(
            provider=provider,
            operation="generate_video",
            unit_name="seconds",
            unit_cost_usd=max(0.0, float(unit_cost_usd)),
            pricing_note="Estimated effective 720p preview video output price.",
        ),)
        profile = ProviderControlProfile(
            provider=provider,
            display_name="Gemini Omni Flash",
            category="video",
            execution_mode=execution_mode,
            budget=budget,
            pricing=pricing,
            secret_slots=(ProviderSecretSlot(
                key="api_key",
                label="Google AI Studio API Key",
                required=True,
            ),),
            metadata={
                "capabilities": ("video_generation", "video_editing"),
                "model": "gemini-omni-flash-preview",
                "preview": True,
                "free_tier": False,
                "resolution": "720p",
                "frame_rate": 24,
                "duration_seconds": (3, 10),
            },
        )
        return self.register_profile(profile)

    def set_execution_mode(self, provider: str, mode: ExecutionMode) -> ProviderControlProfile:
        """Switch provider mode for the future settings panel."""
        profile = self._require_profile(provider)
        return self.register_profile(profile.with_mode(mode))

    def configure_budget(
        self,
        provider: str,
        *,
        max_cost_usd: float = 0.0,
        max_units: int = 0,
        max_requests: int = 0,
        owner_approved: bool | None = None,
    ) -> ProviderControlProfile:
        """Configure explicit provider budget limits."""
        profile = self._require_profile(provider)
        previous = profile.budget or ProviderBudget(provider=profile.provider)
        approved = previous.owner_approved if owner_approved is None else owner_approved
        if approved and max_cost_usd <= 0 and max_units <= 0 and max_requests <= 0:
            raise ValueError("REAL provider approval requires at least one budget limit.")
        budget = ProviderBudget(
            provider=profile.provider,
            owner_approved=approved,
            max_cost_usd=max(0.0, float(max_cost_usd)),
            max_units=max(0, int(max_units)),
            max_requests=max(0, int(max_requests)),
            notes=previous.notes,
            metadata=dict(previous.metadata),
        )
        return self.register_profile(profile.with_budget(budget))

    def approve_provider(self, provider: str, approved: bool = True) -> ProviderControlProfile:
        """Approve or revoke REAL provider usage."""
        profile = self._require_profile(provider)
        budget = profile.budget or ProviderBudget(provider=profile.provider)
        if approved and not self._has_budget_limit(budget):
            raise ValueError("REAL provider approval requires at least one budget limit.")
        approved_budget = ProviderBudget(
            provider=budget.provider,
            owner_approved=approved,
            max_cost_usd=budget.max_cost_usd,
            max_units=budget.max_units,
            max_requests=budget.max_requests,
            notes=budget.notes,
            metadata=dict(budget.metadata),
        )
        return self.register_profile(profile.with_budget(approved_budget))

    def set_secret(self, provider: str, key: str, value: str) -> ProviderControlProfile:
        """Store a secret through the SecretProvider and refresh UI-safe state."""
        if self._secret_provider is None:
            raise ValueError("ProviderControlCenter has no SecretProvider.")
        profile = self._require_profile(provider)
        self._secret_provider.set(SecretKey(key=key, provider=profile.provider), value)
        return self.register_profile(profile)

    def mark_secret_configured(
        self,
        provider: str,
        key: str,
        masked_hint: str = "configured",
    ) -> ProviderControlProfile:
        """Mark a secret as externally configured without storing its value."""
        profile = self._require_profile(provider)
        slots = tuple(
            slot.with_status(True, masked_hint) if slot.key == key else slot
            for slot in profile.secret_slots
        )
        return self.register_profile(profile.with_secret_slots(slots))

    def apply_to_elevenlabs(self, adapter: Any) -> None:
        """Apply provider control settings to an ElevenLabs adapter instance."""
        profile = self._require_profile("elevenlabs")
        adapter.set_execution_mode(profile.execution_mode)
        adapter.set_budget_guard(self._budget_guard)
        if self._secret_provider is not None:
            adapter.set_secret_provider(self._secret_provider)

    def apply_to_telegram(self, adapter: Any) -> None:
        """Apply provider control settings to a Telegram adapter instance."""
        profile = self._require_profile("telegram")
        adapter.set_execution_mode(profile.execution_mode)
        adapter.set_budget_guard(self._budget_guard)
        if self._secret_provider is not None:
            adapter.set_secret_provider(self._secret_provider)

    def apply_to_meta_ads(self, adapter: Any) -> None:
        """Apply read-only Meta provider controls to an adapter instance."""
        profile = self._require_profile("meta_marketing")
        adapter.set_execution_mode(profile.execution_mode)
        adapter.set_budget_guard(self._budget_guard)
        if self._secret_provider is not None:
            adapter.set_secret_provider(self._secret_provider)

    def apply_to_mercado_livre(self, adapter: Any) -> None:
        """Apply read-only Mercado Livre controls to an adapter instance."""
        profile = self._require_profile("mercado_livre")
        adapter.set_execution_mode(profile.execution_mode)
        adapter.set_budget_guard(self._budget_guard)
        if self._secret_provider is not None:
            adapter.set_secret_provider(self._secret_provider)

    def apply_to_gemini_omni(self, adapter: Any) -> None:
        """Apply paid Gemini video controls to an adapter instance."""
        profile = self._require_profile("gemini_omni_flash")
        adapter.set_execution_mode(profile.execution_mode)
        adapter.set_budget_guard(self._budget_guard)
        if self._secret_provider is not None:
            adapter.set_secret_provider(self._secret_provider)

    def profile(self, provider: str) -> ProviderControlProfile | None:
        """Return a provider profile, or None."""
        return self._profiles.get(self._key(provider))

    def snapshot(self, provider: str) -> ProviderControlSnapshot:
        """Return UI-ready state for one provider."""
        profile = self._refresh_secret_slots(self._require_profile(provider))
        budget = profile.budget
        required = tuple(slot.key for slot in profile.secret_slots if slot.required)
        configured = tuple(slot.key for slot in profile.secret_slots if slot.configured)
        missing = tuple(key for key in required if key not in configured)
        secret_hints = {
            slot.key: slot.masked_hint
            for slot in profile.secret_slots
            if slot.configured and slot.masked_hint
        }
        owner_approved = bool(budget.owner_approved) if budget is not None else False
        can_execute_real = (
            profile.enabled
            and profile.execution_mode == ExecutionMode.REAL
            and owner_approved
            and not missing
            and budget is not None
            and self._has_budget_limit(budget)
        )
        return ProviderControlSnapshot(
            provider=profile.provider,
            display_name=profile.display_name,
            category=profile.category,
            status=self._status(profile, missing, can_execute_real),
            enabled=profile.enabled,
            execution_mode=profile.execution_mode.value,
            owner_approved=owner_approved,
            required_secret_keys=required,
            configured_secret_keys=configured,
            missing_secret_keys=missing,
            secret_hints=secret_hints,
            max_cost_usd=budget.max_cost_usd if budget else 0.0,
            max_units=budget.max_units if budget else 0,
            max_requests=budget.max_requests if budget else 0,
            pricing_operations=tuple(p.operation for p in profile.pricing),
            usage_summary=self._budget_guard.summary(profile.provider),
            can_execute_real=can_execute_real,
            metadata=dict(profile.metadata),
        )

    def dashboard_state(self) -> dict[str, Any]:
        """Return UI-ready state for all providers."""
        snapshots = [self.snapshot(p.provider).to_dict() for p in self._profiles.values()]
        return {
            "providers": snapshots,
            "ready_real_providers": tuple(
                snap["provider"] for snap in snapshots if snap["can_execute_real"]
            ),
            "total_providers": len(snapshots),
        }

    def _refresh_secret_slots(self, profile: ProviderControlProfile) -> ProviderControlProfile:
        if self._secret_provider is None:
            return profile
        slots: list[ProviderSecretSlot] = []
        for slot in profile.secret_slots:
            key = SecretKey(key=slot.key, provider=profile.provider)
            secret = self._secret_provider.get(key)
            configured = secret is not None and self._secret_provider.validate(key)
            slots.append(slot.with_status(configured, secret.masked if secret else ""))
        return profile.with_secret_slots(tuple(slots))

    def _sync_guard(self, profile: ProviderControlProfile) -> None:
        if profile.budget is not None:
            self._budget_guard.configure_budget(profile.budget)
        for pricing in profile.pricing:
            self._budget_guard.configure_pricing(pricing)

    def _require_profile(self, provider: str) -> ProviderControlProfile:
        profile = self._profiles.get(self._key(provider))
        if profile is None:
            raise KeyError(f"Provider {provider} is not registered.")
        return profile

    @staticmethod
    def _has_budget_limit(budget: ProviderBudget) -> bool:
        return budget.max_cost_usd > 0 or budget.max_units > 0 or budget.max_requests > 0

    @staticmethod
    def _key(value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    @staticmethod
    def _status(
        profile: ProviderControlProfile,
        missing: tuple[str, ...],
        can_execute_real: bool,
    ) -> str:
        if not profile.enabled:
            return "disabled"
        if profile.execution_mode == ExecutionMode.MOCK:
            return "safe_mock"
        if missing:
            return "missing_credentials"
        if profile.budget is None or not ProviderControlCenter._has_budget_limit(profile.budget):
            return "missing_budget"
        if not profile.budget.owner_approved:
            return "awaiting_owner_approval"
        if can_execute_real:
            return "real_ready"
        return "needs_attention"
