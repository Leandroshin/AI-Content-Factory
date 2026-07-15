"""Opt-in worker for owner-approved Telegram publications."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.content_factory.telegram_publication_worker import TelegramPublicationWorker
from core.tools import (
    ExecutionMode,
    MockSecretProvider,
    ProviderControlCenter,
    TelegramAdapter,
    TelegramProvider,
)
from core.tools.http import RealHttpClient, RetryPolicy, TimeoutPolicy


DEFAULT_ENDPOINT = "https://central-ai-content-factory.leandro-az-v.chatgpt.site/api/intake/telegram-publications"
DASHBOARD_SECRET_FILE = ROOT / "secrets/dashboard.env"
TELEGRAM_SECRET_FILE = ROOT / "secrets/telegram.env"


def main() -> None:
    if os.environ.get("AI_COMPANY_RUN_TELEGRAM_WORKER", "") != "1":
        print("Dry run only. Set AI_COMPANY_RUN_TELEGRAM_WORKER=1 to process one approved publication.")
        return
    queue_token = _setting("DASHBOARD_INTAKE_TOKEN", DASHBOARD_SECRET_FILE)
    bot_token = _setting("TELEGRAM_BOT_TOKEN", TELEGRAM_SECRET_FILE)
    if not queue_token:
        raise RuntimeError("DASHBOARD_INTAKE_TOKEN is not configured.")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured in secrets/telegram.env.")

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "@achadosbaratosBrasil").strip()
    endpoint = os.environ.get("AI_COMPANY_TELEGRAM_WORKER_ENDPOINT", DEFAULT_ENDPOINT).strip()
    site_access_token = _setting("SITES_AUTHORIZATION_TOKEN", DASHBOARD_SECRET_FILE)
    client = RealHttpClient(
        retry_policy=RetryPolicy(max_retries=1),
        timeout_policy=TimeoutPolicy(total=30.0),
    )

    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_telegram(max_messages=1, max_requests=2)
    center.set_secret("telegram", "bot_token", bot_token)
    center.set_execution_mode("telegram", ExecutionMode.REAL)
    center.approve_provider("telegram", True)

    adapter = TelegramAdapter()
    adapter.configure({"bot_token": "configured_via_secret_provider"})
    adapter.set_provider(TelegramProvider())
    adapter.set_http_client(client)
    center.apply_to_telegram(adapter)
    adapter.authenticate()
    adapter.mark_ready()

    result = TelegramPublicationWorker(
        client,
        endpoint,
        allowed_chat_ids=(chat_id,),
    ).run_once(
        adapter,
        token=queue_token,
        enabled=True,
        site_access_token=site_access_token,
    )
    print(
        f"Telegram queue: received={result.received} sent={result.sent} "
        f"failed={result.failed} status={result.skipped_reason or 'completed'}"
    )


def _setting(key: str, secret_file: Path) -> str:
    value = os.environ.get(key, "").strip()
    if value:
        return value
    if not secret_file.is_file():
        return ""
    try:
        text = secret_file.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


if __name__ == "__main__":
    main()
