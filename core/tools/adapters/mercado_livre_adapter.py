"""Strictly read-only Mercado Livre catalog adapter."""

from __future__ import annotations

import re
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

_SITE_RE = re.compile(r"^[A-Z]{3}$")
_ITEM_RE = re.compile(r"^MLB\d{6,20}$")
_CATEGORY_RE = re.compile(r"^MLB\d{2,20}$")
_READ_ACTIONS = frozenset({"get_item", "search_items", "multiget_items", "get_category"})
_ITEM_FIELDS = (
    "id",
    "site_id",
    "title",
    "family_name",
    "seller_id",
    "category_id",
    "official_store_id",
    "price",
    "base_price",
    "original_price",
    "currency_id",
    "available_quantity",
    "sold_quantity",
    "condition",
    "permalink",
    "thumbnail",
    "pictures",
    "shipping",
    "status",
    "tags",
    "catalog_product_id",
    "date_created",
    "last_updated",
)


class MercadoLivreCatalogAdapter(AbstractToolAdapter):
    """Read catalog data while blocking every marketplace write pre-HTTP."""

    def __init__(self) -> None:
        super().__init__()
        self._budget_guard: ProviderBudgetGuard | None = None

    @property
    def adapter_id(self) -> str:
        return "mercado_livre_catalog"

    @property
    def tool_name(self) -> str:
        return "Mercado Livre Catalog (Read Only)"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.WEB_SEARCH, Capability.DOCUMENT_GENERATION})

    def required_config_keys(self) -> tuple[str, ...]:
        return ("site_id",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("mercado_livre_access_token",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (
            CredentialRequirement(
                key="mercado_livre_access_token",
                label="Mercado Livre OAuth Access Token",
                description="Token OAuth autorizado pelo owner; nunca use senha da conta.",
            ),
        )

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        return _SITE_RE.fullmatch(str(config.get("site_id", "")).strip()) is not None

    def validate_credentials(self) -> bool:
        return self._valid_token(self._resolve_credential("mercado_livre_access_token"))

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Autorize o app pelo fluxo OAuth oficial sem compartilhar sua senha.",
                "2. Guarde access_token e refresh_token fora do Git.",
                "3. Use apenas permissoes de leitura quando o portal permitir separar escopos.",
                "4. Configure site_id=MLB para o catalogo brasileiro.",
                "5. Defina aprovacao e limite de requests antes do modo REAL.",
            ),
            docs_url="https://developers.mercadolivre.com.br/pt_br/publicacao-de-produtos/gestao-de-identidades-e-acessos-oauth-e-tokens",
            notes=(
                "Somente get_item, search_items, multiget_items e get_category existem. "
                "Publicar, editar, pausar, responder, comprar e operar vendas sao bloqueados antes do HTTP."
            ),
        )

    def set_budget_guard(self, budget_guard: ProviderBudgetGuard | None) -> None:
        self._budget_guard = budget_guard

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        action = str(request.params.get("action", "get_item")).strip()
        if action not in _READ_ACTIONS:
            return self._blocked_result(action)
        error = self._validate_request(action, request.params)
        if error:
            return AdapterExecutionResult(success=False, summary="", error=error)
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(action, request.params)
        return self._execute_mock(action, request.params)

    def _execute_mock(self, action: str, values: dict[str, Any]) -> AdapterExecutionResult:
        item_id = str(values.get("item_id", "MLB1234567890"))
        item = {
            "id": item_id,
            "site_id": "MLB",
            "title": "Produto demonstrativo",
            "price": 299.90,
            "original_price": 399.90,
            "currency_id": "BRL",
            "condition": "new",
            "permalink": f"https://produto.mercadolivre.com.br/{item_id}",
            "available_quantity": 50,
            "sold_quantity": 120,
            "status": "active",
        }
        data: Any
        if action == "get_category":
            data = {"id": str(values["category_id"]), "name": "Categoria demonstrativa"}
        elif action == "search_items":
            data = {"paging": {"total": 1, "offset": 0, "limit": 1}, "results": [item]}
        elif action == "multiget_items":
            data = [{"code": 200, "body": {**item, "id": item_id_value}} for item_id_value in self._item_ids(values)]
        else:
            data = item
        return AdapterExecutionResult(
            success=True,
            summary=f"Mercado Livre read-only action completed in MOCK: {action}",
            output={"action": action, "data": data, "read_only": True, "_mock": True},
        )

    def _execute_real(self, action: str, values: dict[str, Any]) -> AdapterExecutionResult:
        if self._http_client is None or self._provider is None:
            return AdapterExecutionResult(success=False, summary="", error="Mercado Livre REAL mode requires HttpClient and MercadoLivreProvider")
        token = self._resolve_credential("mercado_livre_access_token")
        if not self._valid_token(token):
            return AdapterExecutionResult(success=False, summary="", error="Mercado Livre REAL mode requires a valid OAuth access token")
        decision = self._budget_check(action)
        if decision is not None and not decision.allowed:
            return self._budget_blocked(action, decision)
        path, params = self._request_spec(action, values)
        url = f"{self._provider.base_url.rstrip('/')}/{path.lstrip('/')}"
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
                summary="Mercado Livre read-only request failed before a usable response.",
                output={"action": action, "read_only": True, "_real": True},
                error=type(exc).__name__,
            )
        body = response.body
        if not 200 <= response.status_code < 300:
            self._budget_record(action, success=False)
            return AdapterExecutionResult(
                success=False,
                summary=f"Mercado Livre read-only action failed: {action}",
                output={"action": action, "read_only": True, "http_status": response.status_code, "_real": True},
                error=self._safe_error(body, token),
            )
        self._budget_record(action, success=True)
        return AdapterExecutionResult(
            success=True,
            summary=f"Mercado Livre read-only action completed: {action}",
            output={"action": action, "data": self._sanitize(body, token), "read_only": True, "_real": True},
        )

    def _request_spec(self, action: str, values: dict[str, Any]) -> tuple[str, dict[str, str]]:
        if action == "get_item":
            return f"items/{values['item_id']}", {"attributes": ",".join(_ITEM_FIELDS)}
        if action == "multiget_items":
            return "items", {"ids": ",".join(self._item_ids(values)), "attributes": ",".join(_ITEM_FIELDS)}
        if action == "get_category":
            return f"categories/{values['category_id']}", {}
        params = {"q": str(values["query"]).strip(), "limit": str(self._limit(values)), "offset": str(self._offset(values))}
        category = str(values.get("category_id", "")).strip()
        if category:
            params["category"] = category
        return f"sites/{self._config['site_id']}/search", params

    def _validate_request(self, action: str, values: dict[str, Any]) -> str:
        if action == "get_item" and _ITEM_RE.fullmatch(str(values.get("item_id", "")).strip()) is None:
            return "Mercado Livre get_item requires an item_id like MLB1234567890."
        if action == "multiget_items":
            try:
                self._item_ids(values)
            except ValueError as exc:
                return str(exc)
        if action == "get_category" and _CATEGORY_RE.fullmatch(str(values.get("category_id", "")).strip()) is None:
            return "Mercado Livre get_category requires a category_id like MLB1055."
        if action == "search_items":
            query = str(values.get("query", "")).strip()
            if not 2 <= len(query) <= 120:
                return "Mercado Livre search query must contain 2 to 120 characters."
            category = str(values.get("category_id", "")).strip()
            if category and _CATEGORY_RE.fullmatch(category) is None:
                return "Mercado Livre search category_id is malformed."
            try:
                self._limit(values)
                self._offset(values)
            except ValueError as exc:
                return str(exc)
        return ""

    @staticmethod
    def _limit(values: dict[str, Any]) -> int:
        try:
            value = int(values.get("limit", 20))
        except (TypeError, ValueError) as exc:
            raise ValueError("Mercado Livre limit must be an integer from 1 to 50.") from exc
        if not 1 <= value <= 50:
            raise ValueError("Mercado Livre limit must be an integer from 1 to 50.")
        return value

    @staticmethod
    def _offset(values: dict[str, Any]) -> int:
        try:
            value = int(values.get("offset", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Mercado Livre offset must be an integer from 0 to 1000.") from exc
        if not 0 <= value <= 1000:
            raise ValueError("Mercado Livre offset must be an integer from 0 to 1000.")
        return value

    @staticmethod
    def _item_ids(values: dict[str, Any]) -> tuple[str, ...]:
        raw = values.get("item_ids", ())
        ids = tuple(str(item).strip() for item in raw) if isinstance(raw, (list, tuple)) else tuple(part.strip() for part in str(raw).split(",") if part.strip())
        if not 1 <= len(ids) <= 20 or any(_ITEM_RE.fullmatch(item) is None for item in ids):
            raise ValueError("Mercado Livre multiget requires 1 to 20 valid MLB item ids.")
        return ids

    def _resolve_credential(self, key: str) -> str:
        if self._secret_provider is not None:
            for secret_key in (SecretKey(key=key, tool_id=self.adapter_id), SecretKey(key=key, provider="mercado_livre")):
                secret = self._secret_provider.get(secret_key)
                if secret is not None:
                    return secret.value
        return str(self._config.get(key, ""))

    def _budget_check(self, action: str) -> ProviderBudgetDecision | None:
        return None if self._budget_guard is None else self._budget_guard.check(provider="mercado_livre", operation=action, units=1, unit_name="requests")

    def _budget_record(self, action: str, *, success: bool) -> None:
        if self._budget_guard is not None:
            self._budget_guard.record_usage(provider="mercado_livre", operation=action, mode=self._execution_mode.value, units=1, unit_name="requests", success=success, billable=False, metadata={"adapter": self.adapter_id, "read_only": True})

    @staticmethod
    def _valid_token(token: str) -> bool:
        return token == "test_mercado_livre_access_token_read_only" or (len(token) >= 20 and not any(char.isspace() for char in token))

    @classmethod
    def _sanitize(cls, value: Any, token: str) -> Any:
        if isinstance(value, dict):
            return {key: cls._sanitize(item, token) for key, item in value.items() if "token" not in str(key).lower() and key not in {"next", "previous"}}
        if isinstance(value, list):
            return [cls._sanitize(item, token) for item in value]
        return value.replace(token, "<redacted>") if isinstance(value, str) and token else value

    @classmethod
    def _safe_error(cls, body: Any, token: str) -> str:
        safe = cls._sanitize(body, token)
        if isinstance(safe, dict):
            return str(safe.get("message") or safe.get("error") or "Mercado Livre API error")
        return "Mercado Livre API error"

    @staticmethod
    def _blocked_result(action: str) -> AdapterExecutionResult:
        return AdapterExecutionResult(
            success=False,
            summary="Mercado Livre action blocked by read-only policy.",
            output={"action": action, "read_only": True, "blocked_before_http": True, "allowed_actions": sorted(_READ_ACTIONS)},
            error=f"Mercado Livre adapter does not permit write or unknown action: {action}",
        )

    @staticmethod
    def _budget_blocked(action: str, decision: ProviderBudgetDecision) -> AdapterExecutionResult:
        return AdapterExecutionResult(
            success=False,
            summary=f"Mercado Livre read-only action blocked by request budget: {action}",
            output={"action": action, "read_only": True, "blocked_before_http": True, "blocked_by_budget": True, "provider_control": decision.to_dict(), "_real": True},
            error=decision.reason,
        )
