"""Playwright browser automation adapter — mock + real execution modes."""

from __future__ import annotations

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


class PlaywrightAdapter(AbstractToolAdapter):
    """Adapter for Playwright browser automation.

    MOCK mode returns deterministic fake data (default).
    REAL mode launches an actual browser via Playwright.
    """

    @property
    def adapter_id(self) -> str:
        return "playwright_browser"

    @property
    def tool_name(self) -> str:
        return "Playwright"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({
            Capability.BROWSER_NAVIGATION,
            Capability.BROWSER_AUTOMATION,
        })

    def required_config_keys(self) -> tuple[str, ...]:
        return ()

    def required_credential_keys(self) -> tuple[str, ...]:
        return ()

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return ()

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        return True

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "Playwright Adapter não precisa de credenciais externas.",
                "Certifique-se de que o Playwright está instalado: pip install playwright",
                "Instale os browsers: playwright install chromium",
            ),
            docs_url="https://playwright.dev/docs/intro",
            notes="Funciona com Chromium, Firefox e WebKit. Não requer API Keys ou tokens.",
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "navigate")
        url = request.params.get("url", "https://example.com")

        if action == "navigate":
            return AdapterExecutionResult(
                success=True,
                summary=f"Navigated to {url}",
                output={
                    "url": url,
                    "title": f"Page Title for {url}",
                    "status_code": 200,
                    "load_time_ms": 1200,
                },
            )
        if action == "screenshot":
            return AdapterExecutionResult(
                success=True,
                summary=f"Screenshot captured at {url}",
                output={
                    "url": url,
                    "format": "png",
                    "width": 1280,
                    "height": 720,
                    "file": f"screenshot_{url.replace('https://', '').replace('/', '_')}.png",
                },
            )
        if action == "extract":
            selector = request.params.get("selector", "h1")
            return AdapterExecutionResult(
                success=True,
                summary=f"Extracted '{selector}' from {url}",
                output={
                    "url": url,
                    "selector": selector,
                    "content": f"Extracted content from {selector}",
                    "elements_found": 1,
                },
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"Playwright action '{action}' completed on {url}",
            output={"url": url, "action": action, "status": "ok"},
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "navigate")
        url = request.params.get("url", "https://example.com")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="Playwright is not installed. Run: pip install playwright && playwright install chromium",
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                if action == "navigate":
                    page.goto(url, wait_until="domcontentloaded")
                    title = page.title()
                    browser.close()
                    return AdapterExecutionResult(
                        success=True,
                        summary=f"Navigated to {url}",
                        output={
                            "url": url,
                            "title": title,
                            "status_code": 200,
                            "_real": True,
                        },
                    )

                if action == "screenshot":
                    page.goto(url, wait_until="domcontentloaded")
                    import tempfile
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    page.screenshot(path=tmp.name, full_page=True)
                    browser.close()
                    return AdapterExecutionResult(
                        success=True,
                        summary=f"Screenshot captured at {url}",
                        output={
                            "url": url,
                            "format": "png",
                            "width": 1280,
                            "height": 720,
                            "file": tmp.name,
                            "_real": True,
                        },
                    )

                if action == "extract":
                    page.goto(url, wait_until="domcontentloaded")
                    selector = request.params.get("selector", "h1")
                    elements = page.query_selector_all(selector)
                    texts = [el.inner_text() for el in elements]
                    browser.close()
                    return AdapterExecutionResult(
                        success=True,
                        summary=f"Extracted {len(texts)} elements from '{selector}'",
                        output={
                            "url": url,
                            "selector": selector,
                            "content": texts[0] if texts else "",
                            "elements_found": len(texts),
                            "_real": True,
                        },
                    )

                browser.close()
                return AdapterExecutionResult(
                    success=True,
                    summary=f"Playwright action '{action}' completed on {url}",
                    output={"url": url, "action": action, "status": "ok", "_real": True},
                )

        except Exception as e:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error=f"Playwright error: {e}",
            )
