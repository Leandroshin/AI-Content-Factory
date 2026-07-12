"""Strictly read-only Meta Ads analytics adapter."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from core.tools.adapters.base import AbstractToolAdapter
from core.tools.adapters.models import (
    AdapterExecutionResult,
    CredentialRequirement,
    ExecutionMode,
    OwnerGuidance,
    ToolRequest,
)
from core.tools.capabilities import Capability
from core.tools.http.errors import HttpError
from core.tools.provider_control import ProviderBudgetDecision, ProviderBudgetGuard
from core.tools.secrets.models import SecretKey

_API_VERSION_RE = re.compile(r"^v\d+\.\d+$")
_ACCOUNT_ID_RE = re.compile(r"^(?:act_)?\d+$")
_READ_ACTIONS = frozenset(
    {
        "get_permissions",
        "list_ad_accounts",
        "get_ad_account",
        "list_campaigns",
        "get_insights",
    }
)
_DATE_PRESETS = frozenset(
    {
        "today",
        "yesterday",
        "this_month",
        "last_month",
        "this_quarter",
        "maximum",
        "last_3d",
        "last_7d",
        "last_14d",
        "last_28d",
        "last_30d",
        "last_90d",
        "last_week_mon_sun",
        "last_week_sun_sat",
        "last_quarter",
        "last_year",
        "this_week_mon_today",
        "this_week_sun_today",
        "this_year",
    }
)
_INSIGHT_LEVELS = frozenset({"account", "campaign", "adset", "ad"})
_ACCOUNT_FIELDS = (
    "id",
    "account_id",
    "name",
    "account_status",
    "disable_reason",
    "currency",
    "timezone_name",
    "business_name",
    "amount_spent",
    "balance",
    "spend_cap",
)
_CAMPAIGN_FIELDS = (
    "id",
    "name",
    "status",
    "effective_status",
    "objective",
    "created_time",
    "updated_time",
    "start_time",
    "stop_time",
    "daily_budget",
    "lifetime_budget",
)
_INSIGHT_FIELDS = (
    "account_id",
    "account_name",
    "campaign_id",
    "campaign_name",
    "adset_id",
    "adset_name",
    "ad_id",
    "ad_name",
    "impressions",
    "reach",
    "frequency",
    "clicks",
    "inline_link_clicks",
    "spend",
    "cpc",
    "cpm",
    "ctr",
    "actions",
    "cost_per_action_type",
    "date_start",
    "date_stop",
)


class MetaAdsAnalyticsAdapter(AbstractToolAdapter):
    """Read Meta ad accounts, campaigns and insights without write actions."""

    def __init__(self) -> None:
        super().__init__()
        self._budget_guard: ProviderBudgetGuard | None = None

    @property
    def adapter_id(self) -> str:
        return "meta_ads_analytics"

    @property
    def tool_name(self) -> str:
        return "Meta Ads Analytics (Read Only)"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.SOCIAL_MEDIA, Capability.DOCUMENT_GENERATION})

    def required_config_keys(self) -> tuple[str, ...]:
        return ("api_version",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("meta_access_token",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (
            CredentialRequirement(
                key="meta_access_token",
                label="Meta Read-Only Access Token",
                description=(
                    "OAuth or system-user token with ads_read; "
                    "business_management is optional for business asset inventory"
                ),
            ),
        )

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        version = str(config.get("api_version", "")).strip()
        account_id = str(config.get("ad_account_id", "")).strip()
        return bool(_API_VERSION_RE.fullmatch(version)) and (
            not account_id or _ACCOUNT_ID_RE.fullmatch(account_id) is not None
        )

    def validate_credentials(self) -> bool:
        return self._valid_token(self._resolve_credential("meta_access_token"))

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. No app Meta, use somente a permissao ads_read para relatorios.",
                "2. Use business_management apenas se precisar inventariar ativos do portfolio.",
                "3. Nao conceda ads_management para esta integracao read-only.",
                "4. Vincule a conta de anuncios ao usuario do sistema ou token autorizado.",
                "5. Informe a versao Graph API exibida no painel do app.",
                "6. Guarde o token fora do Git no SecretProvider local.",
            ),
            docs_url="https://developers.facebook.com/docs/marketing-api/",
            notes=(
                "O adapter implementa apenas GET para permissoes, contas, campanhas e insights. "
                "Criacao, edicao, pausa, orcamento e exclusao sao bloqueados antes do HTTP."
            ),
        )

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        action = str(request.params.get("action", "list_ad_accounts")).strip()
        if action not in _READ_ACTIONS:
            return self._blocked_write_result(action)
        validation = self._validate_request(action, request.params)
        if validation:
            return AdapterExecutionResult(success=False, summary="", error=validation)
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(action, request)
        return self._execute_mock(action, request)

    def set_budget_guard(self, budget_guard: ProviderBudgetGuard | None) -> None:
        """Inject request limits for REAL read-only analytics."""
        self._budget_guard = budget_guard

    def _execute_mock(
        self,
        action: str,
        request: ToolRequest,
    ) -> AdapterExecutionResult:
        account_id = (
            self._account_id(request.params, required=False) or "act_2069488655023"
        )
        if action == "get_permissions":
            data = (
                {"permission": "ads_read", "status": "granted"},
                {"permission": "business_management", "status": "granted"},
            )
        elif action == "list_ad_accounts":
            data = (
                {
                    "id": account_id,
                    "account_id": account_id.removeprefix("act_"),
                    "name": "Achados Baratos BR",
                    "account_status": 1,
                    "currency": "BRL",
                    "timezone_name": "America/Sao_Paulo",
                    "amount_spent": "0",
                },
            )
        elif action == "get_ad_account":
            data = (
                {
                    "id": account_id,
                    "account_id": account_id.removeprefix("act_"),
                    "name": "Achados Baratos BR",
                    "account_status": 1,
                    "currency": "BRL",
                    "timezone_name": "America/Sao_Paulo",
                    "amount_spent": "0",
                    "balance": "0",
                },
            )
        elif action == "list_campaigns":
            data = (
                {
                    "id": "120000000000001",
                    "name": "Campanha demonstracao pausada",
                    "status": "PAUSED",
                    "effective_status": "PAUSED",
                    "objective": "OUTCOME_TRAFFIC",
                },
            )
        else:
            data = (
                {
                    "account_id": account_id.removeprefix("act_"),
                    "campaign_id": "120000000000001",
                    "campaign_name": "Campanha demonstracao pausada",
                    "impressions": "1000",
                    "reach": "800",
                    "clicks": "30",
                    "spend": "25.00",
                    "cpc": "0.83",
                    "cpm": "25.00",
                    "ctr": "3.00",
                    "date_start": "2026-07-01",
                    "date_stop": "2026-07-07",
                },
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"Meta Ads read-only action completed in MOCK: {action}",
            output={
                "action": action,
                "data": list(data),
                "count": len(data),
                "read_only": True,
                "monetary_values_are_api_native": True,
                "_mock": True,
            },
        )

    def _execute_real(
        self,
        action: str,
        request: ToolRequest,
    ) -> AdapterExecutionResult:
        if self._http_client is None or self._provider is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="Meta Ads REAL mode requires HttpClient and MetaMarketingProvider",
            )
        token = self._resolve_credential("meta_access_token")
        if not self._valid_token(token):
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="Meta Ads REAL mode requires a valid meta_access_token credential",
            )

        budget_decision = self._budget_check(action)
        if budget_decision is not None and not budget_decision.allowed:
            return self._budget_blocked_result(action, budget_decision)

        path, params = self._request_spec(action, request.params)
        version = str(self._config["api_version"])
        url = f"{self._provider.base_url.rstrip('/')}/{version}/{path.lstrip('/')}"
        try:
            response = self._http_client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=30.0,
            )
        except HttpError as exc:
            self._budget_record(action, success=False)
            return AdapterExecutionResult(
                success=False,
                summary="Meta Ads read-only request failed before a usable response.",
                output={"action": action, "read_only": True, "_real": True},
                error=type(exc).__name__,
            )

        body = response.body if isinstance(response.body, dict) else {}
        if response.status_code < 200 or response.status_code >= 300 or "error" in body:
            self._budget_record(action, success=False)
            return self._graph_error(action, response.status_code, body, token)
        normalized = self._normalize_body(action, body, token)
        self._budget_record(action, success=True)
        return AdapterExecutionResult(
            success=True,
            summary=f"Meta Ads read-only action completed: {action}",
            output={
                "action": action,
                **normalized,
                "read_only": True,
                "monetary_values_are_api_native": True,
                "_real": True,
            },
        )

    def _request_spec(
        self,
        action: str,
        values: dict[str, Any],
    ) -> tuple[str, dict[str, str]]:
        limit = str(self._limit(values))
        if action == "get_permissions":
            return "me/permissions", {"limit": limit}
        if action == "list_ad_accounts":
            return "me/adaccounts", {
                "fields": ",".join(_ACCOUNT_FIELDS),
                "limit": limit,
            }

        account_id = self._account_id(values, required=True)
        if action == "get_ad_account":
            return account_id, {"fields": ",".join(_ACCOUNT_FIELDS)}
        if action == "list_campaigns":
            return f"{account_id}/campaigns", {
                "fields": ",".join(_CAMPAIGN_FIELDS),
                "limit": limit,
            }

        params = {
            "fields": ",".join(_INSIGHT_FIELDS),
            "level": str(values.get("level", "campaign")),
            "limit": limit,
        }
        since = str(values.get("since", "")).strip()
        until = str(values.get("until", "")).strip()
        if since and until:
            params["time_range"] = json.dumps({"since": since, "until": until})
        else:
            params["date_preset"] = str(values.get("date_preset", "last_30d"))
        return f"{account_id}/insights", params

    def _validate_request(self, action: str, values: dict[str, Any]) -> str:
        if action in {"get_ad_account", "list_campaigns", "get_insights"}:
            account = str(
                values.get("ad_account_id", self._config.get("ad_account_id", ""))
            ).strip()
            if not _ACCOUNT_ID_RE.fullmatch(account):
                return "Meta Ads read action requires a numeric ad_account_id."
        try:
            self._limit(values)
        except ValueError as exc:
            return str(exc)
        if action != "get_insights":
            return ""
        level = str(values.get("level", "campaign"))
        if level not in _INSIGHT_LEVELS:
            return f"Unsupported insights level: {level}"
        since = str(values.get("since", "")).strip()
        until = str(values.get("until", "")).strip()
        if bool(since) != bool(until):
            return "Meta Ads insights requires both since and until, or neither."
        if since and until:
            try:
                since_date = date.fromisoformat(since)
                until_date = date.fromisoformat(until)
            except ValueError:
                return "Meta Ads insight dates must use YYYY-MM-DD."
            if since_date > until_date:
                return "Meta Ads insights since date must not be after until date."
            if (until_date - since_date).days > 366:
                return (
                    "Meta Ads insights time range cannot exceed 366 days per request."
                )
        else:
            preset = str(values.get("date_preset", "last_30d"))
            if preset not in _DATE_PRESETS:
                return f"Unsupported Meta Ads date_preset: {preset}"
        return ""

    def _normalize_body(
        self,
        action: str,
        body: dict[str, Any],
        token: str,
    ) -> dict[str, Any]:
        raw_data = body.get("data")
        if isinstance(raw_data, list):
            data = raw_data
        elif action == "get_ad_account":
            data = [body]
        else:
            data = []
        paging = body.get("paging", {}) if isinstance(body.get("paging"), dict) else {}
        cursors = (
            paging.get("cursors", {}) if isinstance(paging.get("cursors"), dict) else {}
        )
        sanitized = self._sanitize_value(data, token)
        return {
            "data": sanitized,
            "count": len(sanitized),
            "paging": {
                "before": str(cursors.get("before", "")),
                "after": str(cursors.get("after", "")),
                "has_next": bool(paging.get("next")),
            },
        }

    def _graph_error(
        self,
        action: str,
        status_code: int,
        body: dict[str, Any],
        token: str,
    ) -> AdapterExecutionResult:
        raw = body.get("error", {}) if isinstance(body.get("error"), dict) else {}
        safe = self._sanitize_value(raw, token)
        return AdapterExecutionResult(
            success=False,
            summary=f"Meta Ads read-only action failed: {action}",
            output={
                "action": action,
                "read_only": True,
                "http_status": status_code,
                "meta_error": {
                    "message": str(safe.get("message", "Meta Graph API error")),
                    "type": str(safe.get("type", "")),
                    "code": safe.get("code", 0),
                    "error_subcode": safe.get("error_subcode", 0),
                    "fbtrace_id": str(safe.get("fbtrace_id", "")),
                },
                "_real": True,
            },
            error=str(safe.get("message", f"HTTP {status_code}")),
        )

    def _resolve_credential(self, key: str) -> str:
        if self._secret_provider is not None:
            for secret_key in (
                SecretKey(key=key, tool_id=self.adapter_id),
                SecretKey(key=key, provider="meta_marketing"),
            ):
                secret = self._secret_provider.get(secret_key)
                if secret is not None:
                    return secret.value
        return str(self._config.get(key, ""))

    def _budget_check(self, action: str) -> ProviderBudgetDecision | None:
        if self._budget_guard is None:
            return None
        return self._budget_guard.check(
            provider="meta_marketing",
            operation=action,
            units=1,
            unit_name="requests",
        )

    def _budget_record(self, action: str, *, success: bool) -> None:
        if self._budget_guard is None:
            return
        self._budget_guard.record_usage(
            provider="meta_marketing",
            operation=action,
            mode=self._execution_mode.value,
            units=1,
            unit_name="requests",
            success=success,
            billable=False,
            metadata={"adapter": self.adapter_id, "read_only": True},
        )

    def _account_id(self, values: dict[str, Any], *, required: bool) -> str:
        raw = str(
            values.get("ad_account_id", self._config.get("ad_account_id", ""))
        ).strip()
        if not raw:
            return "" if not required else "act_"
        return raw if raw.startswith("act_") else f"act_{raw}"

    @staticmethod
    def _limit(values: dict[str, Any]) -> int:
        try:
            limit = int(values.get("limit", 50) or 50)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Meta Ads limit must be an integer from 1 to 100."
            ) from exc
        if not 1 <= limit <= 100:
            raise ValueError("Meta Ads limit must be an integer from 1 to 100.")
        return limit

    @staticmethod
    def _valid_token(token: str) -> bool:
        if token in {
            "configured_via_secret_provider",
            "test_meta_access_token_read_only",
        }:
            return True
        return len(token) >= 20 and not any(char.isspace() for char in token)

    @staticmethod
    def _sanitize_value(value: Any, token: str) -> Any:
        if isinstance(value, dict):
            return {
                key: MetaAdsAnalyticsAdapter._sanitize_value(item, token)
                for key, item in value.items()
                if "token" not in str(key).lower() and key not in {"next", "previous"}
            }
        if isinstance(value, list):
            return [
                MetaAdsAnalyticsAdapter._sanitize_value(item, token) for item in value
            ]
        if isinstance(value, str) and token:
            return value.replace(token, "<redacted>")
        return value

    @staticmethod
    def _blocked_write_result(action: str) -> AdapterExecutionResult:
        return AdapterExecutionResult(
            success=False,
            summary="Meta Ads action blocked by read-only policy.",
            output={
                "action": action,
                "read_only": True,
                "blocked_before_http": True,
                "allowed_actions": sorted(_READ_ACTIONS),
            },
            error=f"Meta Ads adapter does not permit write or unknown action: {action}",
        )

    @staticmethod
    def _budget_blocked_result(
        action: str,
        decision: ProviderBudgetDecision,
    ) -> AdapterExecutionResult:
        return AdapterExecutionResult(
            success=False,
            summary=f"Meta Ads read-only action blocked by request budget: {action}",
            output={
                "action": action,
                "read_only": True,
                "blocked_before_http": True,
                "blocked_by_budget": True,
                "provider_control": decision.to_dict(),
                "_real": True,
            },
            error=decision.reason,
        )
