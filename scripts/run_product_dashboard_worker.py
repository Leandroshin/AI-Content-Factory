"""Opt-in worker for product URLs submitted through the private dashboard."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.content_factory import ProductDashboardWorker, ProductUrlIntake
from core.tools.http import RealHttpClient, RetryPolicy, TimeoutPolicy


DEFAULT_ENDPOINT = "https://central-ai-content-factory.leandro-az-v.chatgpt.site/api/intake/products"
DEFAULT_SECRET_FILE = ROOT / "secrets/dashboard.env"


def main() -> None:
    if os.environ.get("AI_COMPANY_RUN_PRODUCT_WORKER", "") != "1":
        print("Dry run only. Set AI_COMPANY_RUN_PRODUCT_WORKER=1 to process the dashboard queue.")
        return
    token = _setting("DASHBOARD_INTAKE_TOKEN")
    if not token:
        raise RuntimeError("DASHBOARD_INTAKE_TOKEN is not configured.")
    endpoint = os.environ.get("AI_COMPANY_PRODUCT_WORKER_ENDPOINT", DEFAULT_ENDPOINT).strip()
    site_access_token = _setting("SITES_AUTHORIZATION_TOKEN")
    client = RealHttpClient(
        retry_policy=RetryPolicy(max_retries=1),
        timeout_policy=TimeoutPolicy(total=30.0),
    )
    result = ProductDashboardWorker(client, endpoint).run_once(
        ProductUrlIntake(client),
        token=token,
        enabled=True,
        site_access_token=site_access_token,
    )
    print(
        f"Product queue: received={result.received} submitted={result.submitted} "
        f"failed={result.failed} status={result.skipped_reason or 'completed'}"
    )


def _setting(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if value:
        return value
    if not DEFAULT_SECRET_FILE.is_file():
        return ""
    try:
        text = DEFAULT_SECRET_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


if __name__ == "__main__":
    main()
