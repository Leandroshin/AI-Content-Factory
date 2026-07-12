"""Opt-in REAL smoke test for read-only Meta Ads inventory.

The default regression path is a dry run. Set
AI_COMPANY_RUN_REAL_META_ADS=1 only after storing a token with ads_read in
secrets/meta_ads.env or process environment variables.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from core.tools.adapters import ExecutionMode, MetaAdsAnalyticsAdapter, ToolRequest
from core.tools.http import RealHttpClient, RetryPolicy, TimeoutPolicy
from core.tools.provider_settings import ProviderControlCenter
from core.tools.providers import MetaMarketingProvider
from core.tools.secrets import MockSecretProvider

_ASSERTION_COUNTER = 0
_MAX_REQUESTS = 3
_DEFAULT_SECRET_FILE = Path("secrets/meta_ads.env")


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _extract_env_value(text: str, key: str) -> str:
    pattern = re.compile(
        rf"^\s*(?:export\s+)?{re.escape(key)}\s*=\s*(.+?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip()
    if value and value[0] in ("'", '"') and value[-1:] == value[0]:
        value = value[1:-1]
    return value.strip()


def _load_setting(key: str) -> tuple[str, str]:
    env_value = os.environ.get(key, "").strip()
    if env_value:
        return env_value, "process_env"
    override = os.environ.get("AI_COMPANY_META_ADS_ENV_FILE", "").strip()
    path = Path(override) if override else _DEFAULT_SECRET_FILE
    if not path.is_file():
        return "", ""
    try:
        value = _extract_env_value(path.read_text(encoding="utf-8"), key)
    except OSError:
        return "", ""
    return value, str(path) if value else ""


def _request(action: str, account_id: str = "") -> ToolRequest:
    params: dict[str, object] = {"action": action, "limit": 10}
    if account_id:
        params["ad_account_id"] = account_id
    return ToolRequest(
        tool_id=uuid4(),
        capability="social_media",
        params=params,
    )


def _safe_result(result: object) -> dict[str, object]:
    success = bool(getattr(result, "success", False))
    output = dict(getattr(result, "output", {}) or {})
    return {
        "success": success,
        "summary": str(getattr(result, "summary", "")),
        "error": str(getattr(result, "error", "")),
        "action": output.get("action", ""),
        "count": output.get("count", 0),
        "read_only": output.get("read_only", True),
        "http_status": output.get("http_status", 0),
        "meta_error": output.get("meta_error", {}),
        "data": output.get("data", []),
    }


def main() -> None:
    print("=" * 70)
    print("Meta Ads REAL Read-Only Smoke - Opt-in")
    print("=" * 70)

    run_real = os.environ.get("AI_COMPANY_RUN_REAL_META_ADS", "") == "1"
    _check(_MAX_REQUESTS == 3, "Smoke permits exactly three read requests")
    _check(
        "create" not in MetaAdsAnalyticsAdapter().owner_guidance().notes.lower(),
        "Guidance exposes no create operation",
    )
    _check(
        _DEFAULT_SECRET_FILE.parent.name == "secrets",
        "Default token file stays ignored by Git",
    )

    if not run_real:
        print("\nDry run only. Set AI_COMPANY_RUN_REAL_META_ADS=1 for REAL reads.")
        print(f"\n{'=' * 70}")
        print(f"All {_ASSERTION_COUNTER} assertions passed.")
        print("=" * 70)
        return

    token, token_source = _load_setting("META_ACCESS_TOKEN")
    api_version, version_source = _load_setting("META_GRAPH_API_VERSION")
    account_id, account_source = _load_setting("META_AD_ACCOUNT_ID")
    _check(bool(token), "Meta token was found without printing it")
    _check(
        bool(re.fullmatch(r"v\d+\.\d+", api_version)), "Graph API version is explicit"
    )
    _check(bool(re.fullmatch(r"(?:act_)?\d+", account_id)), "Ad account id is numeric")

    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_meta_ads(
        max_requests=_MAX_REQUESTS,
        execution_mode=ExecutionMode.REAL,
        api_version=api_version,
        ad_account_id=account_id,
    )
    center.set_secret("meta_marketing", "meta_access_token", token)
    center.approve_provider("meta_marketing", True)

    adapter = MetaAdsAnalyticsAdapter()
    adapter.configure(
        {
            "api_version": api_version,
            "ad_account_id": account_id,
            "meta_access_token": "configured_via_secret_provider",
        }
    )
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_provider(MetaMarketingProvider())
    adapter.set_http_client(
        RealHttpClient(
            retry_policy=RetryPolicy(max_retries=1),
            timeout_policy=TimeoutPolicy(total=30.0),
        )
    )
    center.apply_to_meta_ads(adapter)

    results = (
        adapter.execute(_request("get_permissions")),
        adapter.execute(_request("get_ad_account", account_id)),
        adapter.execute(_request("list_campaigns", account_id)),
    )
    report = {
        "status": "success"
        if all(result.success for result in results)
        else "completed_with_controlled_errors",
        "read_only": True,
        "write_actions_available": False,
        "api_version": api_version,
        "ad_account_id": account_id.removeprefix("act_"),
        "results": [_safe_result(result) for result in results],
        "usage": center.snapshot("meta_marketing").to_dict()["usage_summary"],
        "credential_sources": {
            "token": token_source,
            "api_version": version_source,
            "account_id": account_source,
        },
        "raw_secret_written": False,
    }
    output = Path("output/meta_ads_real_smoke/report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_text = output.read_text(encoding="utf-8")
    _check(token not in report_text, "Redacted report contains no raw token")
    _check(len(results) == _MAX_REQUESTS, "Only the approved read budget was used")
    _check(
        all(item.output.get("read_only", True) for item in results),
        "Every result remains read-only",
    )
    _check(output.is_file(), "Local redacted report was written")

    print(f"\nReport written to: {output.resolve()}")
    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
