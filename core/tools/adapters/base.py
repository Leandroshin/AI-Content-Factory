"""Abstract base class for all tool adapters.

Every external tool (YouTube, GitHub, ElevenLabs, Playwright, etc.)
must implement this interface. Adapters are stateful for lifecycle
tracking (UNCONFIGURED -> CONFIGURED -> AUTHENTICATED -> READY -> ERROR)
but receive only typed requests — they never access company internals.

Adapters support two execution modes:
  MOCK — return deterministic fake data (default)
  REAL — make actual HTTP/SDK calls via injected HttpClient + Provider
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from core.tools.adapters.models import (
    AdapterConfigStatus,
    AdapterExecutionResult,
    AdapterStatus,
    CredentialRequirement,
    ExecutionMode,
    OwnerGuidance,
    ToolRequest,
)
from core.tools.capabilities import Capability

if TYPE_CHECKING:
    from core.tools.http.client import HttpClient
    from core.tools.providers.base import Provider
    from core.tools.secrets.provider import SecretProvider


class AbstractToolAdapter(ABC):
    """Pluggable adapter for a single external tool.

    Subclasses implement only the integration logic for
    their specific tool. All lifecycle orchestration
    (registration, validation, availability, execution)
    is managed by ToolRuntime.

    Each adapter tracks its own lifecycle state:
      UNCONFIGURED -> CONFIGURED -> AUTHENTICATED -> READY -> ERROR

    Supports MOCK and REAL execution modes.
    """

    # --------------------------------------------------------------
    # Internal lifecycle state (tracked per instance)
    # --------------------------------------------------------------

    def __init__(self) -> None:
        self._adapter_status: AdapterStatus = AdapterStatus.UNCONFIGURED
        self._config: dict[str, Any] = {}
        self._has_credentials: bool = False
        self._error_message: str = ""
        self._execution_mode: ExecutionMode = ExecutionMode.MOCK
        self._http_client: HttpClient | None = None
        self._provider: Provider | None = None
        self._secret_provider: SecretProvider | None = None

    # --------------------------------------------------------------
    # Abstract — must be overridden
    # --------------------------------------------------------------

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique identifier for this adapter (e.g. 'youtube_v3')."""
        ...

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Human-readable name (e.g. 'YouTube Data API v3')."""
        ...

    @abstractmethod
    def supported_capabilities(self) -> frozenset[Capability]:
        """Set of capabilities this adapter provides."""
        ...

    @abstractmethod
    def validate_configuration(self, config: dict[str, Any]) -> bool:
        """Check whether the given configuration is valid."""
        ...

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check whether current credentials are valid."""
        ...

    @abstractmethod
    def check_availability(self) -> bool:
        """Check whether the external service is reachable."""
        ...

    @abstractmethod
    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        """Execute a tool request and return a normalised result."""
        ...

    # --------------------------------------------------------------
    # Lifecycle control (concrete — may be overridden)
    # --------------------------------------------------------------

    def configure(self, config: dict[str, Any]) -> None:
        """Validate and store configuration, then transition to CONFIGURED."""
        self._config = dict(config)
        if self.validate_configuration(config):
            self._adapter_status = AdapterStatus.CONFIGURED
        else:
            self._adapter_status = AdapterStatus.ERROR
            self._error_message = f"Configuration validation failed for {self.tool_name}"

    def authenticate(self) -> None:
        """Mark credentials as provided and transition to AUTHENTICATED.

        Subclasses should call this after credential values are stored.
        Use validate_credentials() as a separate check for credential
        validity when needed.
        """
        self._has_credentials = True
        self._adapter_status = AdapterStatus.AUTHENTICATED

    def mark_ready(self) -> None:
        """Transition to READY (called when all checks pass)."""
        self._adapter_status = AdapterStatus.READY

    def mark_error(self, message: str) -> None:
        """Transition to ERROR with a descriptive message."""
        self._adapter_status = AdapterStatus.ERROR
        self._error_message = message

    def reset(self) -> None:
        """Reset adapter to UNCONFIGURED (clears config and credentials)."""
        self._adapter_status = AdapterStatus.UNCONFIGURED
        self._config = {}
        self._has_credentials = False
        self._error_message = ""

    @property
    def status(self) -> AdapterStatus:
        """Current lifecycle status."""
        return self._adapter_status

    @property
    def error_message(self) -> str:
        """Last error message (empty string if none)."""
        return self._error_message

    # --------------------------------------------------------------
    # Configuration & credential queries (concrete — may be overridden)
    # --------------------------------------------------------------

    def required_config_keys(self) -> tuple[str, ...]:
        """Keys this adapter expects in the configuration dict."""
        return ()

    def required_credential_keys(self) -> tuple[str, ...]:
        """Keys this adapter expects for authentication."""
        return ()

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        """Detailed descriptions of each required credential."""
        return tuple(
            CredentialRequirement(
                key=k,
                label=k.replace("_", " ").title(),
                description=f"Value for {k}",
            )
            for k in self.required_credential_keys()
        )

    def configuration_status(self) -> AdapterConfigStatus:
        """Return what this adapter still needs to become ready."""
        missing_cfg: list[str] = []
        for k in self.required_config_keys():
            if k not in self._config or not self._config[k]:
                missing_cfg.append(k)

        missing_creds: list[str] = []
        if not self._has_credentials:
            missing_creds.extend(self.required_credential_keys())

        if self._adapter_status == AdapterStatus.ERROR:
            return AdapterConfigStatus(
                status=AdapterStatus.ERROR,
                missing_config=tuple(missing_cfg),
                missing_credentials=tuple(missing_creds),
                error_message=self._error_message,
            )

        if missing_cfg and missing_creds:
            return AdapterConfigStatus(
                status=AdapterStatus.UNCONFIGURED,
                missing_config=tuple(missing_cfg),
                missing_credentials=tuple(missing_creds),
            )
        if missing_cfg:
            return AdapterConfigStatus(
                status=AdapterStatus.UNCONFIGURED,
                missing_config=tuple(missing_cfg),
            )
        if missing_creds:
            return AdapterConfigStatus(
                status=AdapterStatus.CONFIGURED,
                missing_credentials=tuple(missing_creds),
            )

        return AdapterConfigStatus(status=AdapterStatus.READY)

    # --------------------------------------------------------------
    # Owner guidance (concrete — may be overridden)
    # --------------------------------------------------------------

    def owner_guidance(self) -> OwnerGuidance:
        """Return step-by-step instructions for the Owner.

        Subclasses should override to provide tool-specific guidance.
        """
        keys = self.required_credential_keys()
        if not keys:
            return OwnerGuidance(
                steps=(f"{self.tool_name} does not require any credentials.",),
                notes="No configuration needed.",
            )
        reqs = {r.key: r.description for r in self.credential_requirements()}
        steps: list[str] = [
            f"Configure {self.tool_name}:",
        ]
        for k in keys:
            desc = reqs.get(k, f"Your {k}")
            steps.append(f"  1. Provide '{k}' - {desc}")
        return OwnerGuidance(steps=tuple(steps))

    # --------------------------------------------------------------
    # Execution mode (MOCK / REAL)
    # --------------------------------------------------------------

    @property
    def execution_mode(self) -> ExecutionMode:
        """Current execution mode (MOCK or REAL)."""
        return self._execution_mode

    def set_execution_mode(self, mode: ExecutionMode) -> None:
        """Switch between MOCK and REAL execution.

        In MOCK mode the adapter returns deterministic fake data.
        In REAL mode the adapter uses its HttpClient + Provider
        to make actual API calls.
        """
        self._execution_mode = mode

    # --------------------------------------------------------------
    # HTTP client injection
    # --------------------------------------------------------------

    @property
    def http_client(self) -> HttpClient | None:
        """Injected HTTP client (None = use default mock)."""
        return self._http_client

    def set_http_client(self, client: HttpClient | None) -> None:
        """Inject an HTTP client for REAL execution mode."""
        self._http_client = client

    # --------------------------------------------------------------
    # Provider injection
    # --------------------------------------------------------------

    @property
    def provider(self) -> Provider | None:
        """Injected SDK provider contract."""
        return self._provider

    def set_provider(self, provider: Provider | None) -> None:
        """Inject an SDK provider for REAL execution mode."""
        self._provider = provider

    # --------------------------------------------------------------
    # Secret provider injection
    # --------------------------------------------------------------

    def set_secret_provider(self, secret_provider: SecretProvider | None) -> None:
        """Inject a secret provider for credential retrieval.

        In REAL mode the adapter will fetch credentials via this
        provider instead of reading them from raw config or memory.
        """
        self._secret_provider = secret_provider
