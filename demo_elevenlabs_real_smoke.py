"""Opt-in ElevenLabs REAL smoke test with a tiny budget cap.

Default execution is a dry run so full regression never spends credits.
Set AI_COMPANY_RUN_REAL_ELEVENLABS=1 to perform one short real TTS request.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from uuid import uuid4

from core.tools import (
    ElevenLabsAdapter,
    ElevenLabsProvider,
    ExecutionMode,
    MockSecretProvider,
    ProviderControlCenter,
    RealHttpClient,
    RetryPolicy,
    SecretKey,
    TimeoutPolicy,
    ToolRequest,
)


_ASSERTION_COUNTER: int = 0
_MAX_CHARS = 40
_MAX_COST_USD = 0.002
_MAX_REQUESTS = 1
_UNIT_COST_USD = 0.0001
_SMOKE_TEXT = "Teste real AI."
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
_CANDIDATE_SECRET_FILES = (
    Path(r"C:\Users\Shin\Documents\New project\assistente-chave\.env"),
    Path(r"C:\Users\Shin\Documents\New project\youtube\chave api.txt"),
    Path(r"C:\Users\Shin\Documents\New project\experimentos\luma-airi\services\discord-bot\.env"),
    Path(r"C:\Users\Shin\Documents\New project\experimentos\airi\services\discord-bot\.env"),
)


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _extract_env_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*(?:export\s+)?{re.escape(key)}\s*=\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip()
    if value and value[0] in ("'", '"') and value[-1:] == value[0]:
        value = value[1:-1]
    return value.strip()


def _load_secret(key: str) -> tuple[str, str]:
    env_value = os.environ.get(key, "").strip()
    if env_value:
        return env_value, "process_env"

    override = os.environ.get("AI_COMPANY_ELEVENLABS_ENV_FILE", "").strip()
    candidates = (Path(override),) if override else _CANDIDATE_SECRET_FILES
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        value = _extract_env_value(text, key)
        if value:
            return value, str(path)
    return "", ""


def _prepare_center(api_key: str) -> ProviderControlCenter:
    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_elevenlabs(
        unit_cost_usd=_UNIT_COST_USD,
        max_cost_usd=_MAX_COST_USD,
        max_units=_MAX_CHARS,
        max_requests=_MAX_REQUESTS,
        execution_mode=ExecutionMode.REAL,
    )
    center.set_secret("elevenlabs", "api_key", api_key)
    center.approve_provider("elevenlabs", True)
    return center


def _adapter(center: ProviderControlCenter) -> ElevenLabsAdapter:
    adapter = ElevenLabsAdapter()
    adapter.configure({"api_key": "configured_via_secret_provider"})
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_provider(ElevenLabsProvider())
    adapter.set_http_client(RealHttpClient(
        retry_policy=RetryPolicy(max_retries=1),
        timeout_policy=TimeoutPolicy(total=25.0),
    ))
    center.apply_to_elevenlabs(adapter)
    return adapter


def _request(voice_id: str, output_dir: Path) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="speech_generation",
        params={
            "action": "synthesize",
            "text": _SMOKE_TEXT,
            "voice": "smoke_test",
            "voice_id": voice_id,
            "model_id": "eleven_multilingual_v2",
            "output_format": "mp3",
            "duration_seconds": 1.0,
            "task_id": "elevenlabs_real_smoke",
            "output_dir": str(output_dir),
            "write_file": True,
        },
    )


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("ElevenLabs REAL Smoke Test - Opt-in")
    print("=" * 70)

    run_real = os.environ.get("AI_COMPANY_RUN_REAL_ELEVENLABS", "") == "1"
    _check(len(_SMOKE_TEXT) <= _MAX_CHARS, "Smoke text stays below max character budget")
    _check(_MAX_REQUESTS == 1, "Smoke test allows exactly one REAL request")
    _check(_MAX_COST_USD <= 0.002, "Smoke test cost cap is tiny")

    if not run_real:
        print("\nDry run only. Set AI_COMPANY_RUN_REAL_ELEVENLABS=1 for the real call.")
        print(f"\n{'=' * 70}")
        print(f"All {_ASSERTION_COUNTER} assertions passed.")
        print(f"{'=' * 70}")
        return

    api_key, key_source = _load_secret("ELEVENLABS_API_KEY")
    voice_id, voice_source = _load_secret("ELEVENLABS_LUMI_VOICE_ID")
    if not voice_id:
        voice_id, voice_source = _load_secret("ELEVENLABS_VOICE_ID")
    if not voice_id:
        voice_id, voice_source = _DEFAULT_VOICE_ID, "default_voice"

    _check(bool(api_key), "ElevenLabs API key was found without printing it")
    _check(bool(voice_id), "Voice id is available")

    center = _prepare_center(api_key)
    snap = center.snapshot("elevenlabs")
    _check(snap.can_execute_real, "ProviderControlCenter marks ElevenLabs REAL-ready")

    decision = center.budget_guard.check(
        provider="elevenlabs",
        operation="synthesize",
        units=len(_SMOKE_TEXT),
        unit_name="characters",
    )
    _check(decision.allowed, "ProviderBudgetGuard allows the tiny smoke request")

    output_dir = Path("output/elevenlabs_real_smoke")
    adapter = _adapter(center)
    result = adapter.execute(_request(voice_id, output_dir))
    report_path = output_dir / "report.json"
    if not result.success:
        summary = center.budget_guard.summary("elevenlabs")
        report = {
            "status": "failed_controlled",
            "error": result.error,
            "http_error": result.output.get("_http_error"),
            "text_characters": len(_SMOKE_TEXT),
            "estimated_cost_usd": summary.estimated_cost_usd,
            "max_cost_usd": _MAX_COST_USD,
            "max_requests": _MAX_REQUESTS,
            "requests_attempted": summary.requests,
            "failures": summary.failures,
            "key_source": key_source,
            "voice_source": voice_source,
            "voice_id_last4": voice_id[-4:],
            "raw_secret_written": False,
        }
        _write_report(report_path, report)
        _check(result.output.get("_real") is True, "REAL failure returned a controlled adapter result")
        _check(bool(result.output.get("_http_error")), "HTTP error type is captured without traceback")
        _check(summary.requests == 1, "Usage summary records one failed REAL attempt")
        _check(summary.billable_units == 0, "Failed REAL attempt is not billable in local accounting")
        _check(summary.estimated_cost_usd == 0.0, "Failed REAL attempt has zero estimated local cost")
        _check(report_path.exists(), "Redacted failure report was written")
        _check(api_key not in report_path.read_text(encoding="utf-8"), "Failure report does not contain raw API key")
        print(f"\nREAL attempt did not generate audio: {result.error}")
        print(f"Report written to: {report_path.resolve()}")
        print(f"\n{'=' * 70}")
        print(f"All {_ASSERTION_COUNTER} assertions passed.")
        print(f"{'=' * 70}")
        return

    _check(result.success, "ElevenLabs REAL request succeeded")
    _check(result.output.get("physical_asset") is True, "REAL response was written as a physical asset")

    file_path = Path(str(result.output.get("file_path", "")))
    _check(file_path.exists(), "Generated REAL audio file exists")
    _check(file_path.stat().st_size > 100, "Generated REAL audio file is non-empty")

    summary = center.budget_guard.summary("elevenlabs")
    _check(summary.requests == 1, "Usage summary counts one REAL request")
    _check(summary.billable_units == len(_SMOKE_TEXT), "Usage summary counts exact characters")
    _check(summary.estimated_cost_usd <= _MAX_COST_USD, "Estimated cost stays within cap")

    report = {
        "status": "success",
        "text_characters": len(_SMOKE_TEXT),
        "estimated_cost_usd": summary.estimated_cost_usd,
        "max_cost_usd": _MAX_COST_USD,
        "max_requests": _MAX_REQUESTS,
        "key_source": key_source,
        "voice_source": voice_source,
        "voice_id_last4": voice_id[-4:],
        "audio_file_path": str(file_path.resolve()),
        "audio_file_size_bytes": file_path.stat().st_size,
        "raw_secret_written": False,
    }
    _write_report(report_path, report)
    _check(report_path.exists(), "Redacted smoke report was written")
    _check(api_key not in report_path.read_text(encoding="utf-8"), "Report does not contain raw API key")

    print(f"\nAudio written to: {file_path.resolve()}")
    print(f"Report written to: {report_path.resolve()}")
    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
