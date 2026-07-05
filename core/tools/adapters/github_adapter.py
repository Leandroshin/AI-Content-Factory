"""GitHub REST API adapter — mock + real execution modes."""

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


class GitHubAdapter(AbstractToolAdapter):
    """Adapter for GitHub REST API.

    MOCK mode returns deterministic fake data (default).
    REAL mode calls the actual GitHub API via HttpClient + Provider.
    """

    @property
    def adapter_id(self) -> str:
        return "github_rest"

    @property
    def tool_name(self) -> str:
        return "GitHub"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({
            Capability.REPOSITORY_MANAGEMENT,
            Capability.CODE_SEARCH,
            Capability.CODE_EXECUTION,
        })

    def required_config_keys(self) -> tuple[str, ...]:
        return ("token",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("personal_access_token",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (CredentialRequirement(
            key="personal_access_token",
            label="GitHub Personal Access Token",
            description="Classic or Fine-grained PAT with repo, read:org scopes",
        ),)

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        token = config.get("token", "")
        return bool(token) and token.startswith((
            "ghp_",
            "github_pat_",
            "test_github_token_",
        ))

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Acesse GitHub Settings > Developer settings > Personal access tokens",
                "2. Clique em 'Generate new token' (classic ou fine-grained)",
                "3. Selecione os scopes necessários (repo, read:org, read:user)",
                "4. Gere o token e copie o valor (mostrado apenas uma vez)",
                "5. Cole o Personal Access Token no sistema",
            ),
            docs_url="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
            notes="Nunca compartilhe seu token. Armazene-o de forma segura.",
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "info")
        repo = request.params.get("repo", "user/repo")

        if action == "create_repo":
            return AdapterExecutionResult(
                success=True,
                summary=f"GitHub repository '{repo}' created",
                output={
                    "repo": repo,
                    "url": f"https://github.com/{repo}",
                    "visibility": request.params.get("visibility", "private"),
                },
            )
        if action == "search_code":
            query = request.params.get("query", "")
            return AdapterExecutionResult(
                success=True,
                summary=f"Code search for '{query}' in {repo}",
                output={
                    "query": query,
                    "repo": repo,
                    "matches": [
                        {"file": "src/main.py", "line": 42},
                        {"file": "src/utils.py", "line": 15},
                    ],
                    "total_count": 2,
                },
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"GitHub repository info: {repo}",
            output={
                "repo": repo,
                "stars": 42,
                "forks": 7,
                "language": "Python",
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "info")
        repo = request.params.get("repo", "user/repo")

        client = self._http_client
        provider = self._provider
        if client is None or provider is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="GitHub REAL mode requires HttpClient and Provider",
            )

        token = self._resolve_credential("personal_access_token")
        if not token:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="GitHub REAL mode requires 'personal_access_token' credential",
            )

        base = provider.base_url.rstrip("/")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Content-Factory/1.0",
        }

        if action == "create_repo":
            url = f"{base}/user/repos"
            body = {
                "name": repo.split("/")[-1] if "/" in repo else repo,
                "private": request.params.get("visibility", "private") == "private",
            }
            resp = client.post(url, headers=headers, body=body)
            resp_body = resp.body if isinstance(resp.body, dict) else {}
            return AdapterExecutionResult(
                success=resp.status_code in (200, 201),
                summary=f"GitHub repo created: {resp_body.get('full_name', repo)}"
                        if resp.status_code in (200, 201) else f"Creation failed: HTTP {resp.status_code}",
                output={
                    "repo": resp_body.get("full_name", repo),
                    "url": resp_body.get("html_url", f"https://github.com/{repo}"),
                    "visibility": resp_body.get("visibility", "private"),
                    "_real": True,
                },
                error="" if resp.status_code in (200, 201) else f"HTTP {resp.status_code}",
            )

        if action == "search_code":
            query = request.params.get("query", "")
            url = f"{base}/search/code"
            resp = client.get(url, headers=headers, params={"q": query, "per_page": "5"})
            resp_body = resp.body if isinstance(resp.body, dict) else {}
            items = resp_body.get("items", [])
            return AdapterExecutionResult(
                success=resp.status_code == 200,
                summary=f"Code search: {resp_body.get('total_count', 0)} matches" if resp.status_code == 200
                        else f"Search failed: HTTP {resp.status_code}",
                output={
                    "query": query,
                    "matches": [
                        {"file": i.get("path", ""), "line": 0}
                        for i in (items or [])
                    ],
                    "total_count": resp_body.get("total_count", 0),
                    "_real": True,
                },
                error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
            )

        url = f"{base}/repos/{repo}"
        resp = client.get(url, headers=headers)
        resp_body = resp.body if isinstance(resp.body, dict) else {}
        return AdapterExecutionResult(
            success=resp.status_code == 200,
            summary=f"GitHub repo: {resp_body.get('full_name', repo)}" if resp.status_code == 200
                    else f"Info failed: HTTP {resp.status_code}",
            output={
                "repo": resp_body.get("full_name", repo),
                "stars": resp_body.get("stargazers_count", 0),
                "forks": resp_body.get("forks_count", 0),
                "language": resp_body.get("language", ""),
                "_real": True,
            },
            error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_credential(self, key: str) -> str:
        if self._secret_provider is not None:
            from core.tools.secrets.models import SecretKey
            secret = self._secret_provider.get(SecretKey(key=key, tool_id=self.adapter_id))
            if secret is not None:
                return secret.value
        return self._config.get(key, "")
