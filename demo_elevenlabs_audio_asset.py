"""Demo: ElevenLabs adapter writes physical audio assets.

This validates file materialization without spending API credits:
- MOCK mode writes a deterministic local WAV.
- REAL mode is simulated with MockHttpClient returning binary audio bytes.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.tools import (
    ElevenLabsAdapter,
    ElevenLabsProvider,
    ExecutionMode,
    HttpResponse,
    MockHttpClient,
    MockSecretProvider,
    SecretKey,
    ToolRequest,
)


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _ready_mock_adapter() -> ElevenLabsAdapter:
    adapter = ElevenLabsAdapter()
    adapter.configure({"api_key": "mock_api_key"})
    adapter.authenticate()
    adapter.mark_ready()
    return adapter


def _ready_real_adapter() -> ElevenLabsAdapter:
    adapter = ElevenLabsAdapter()
    adapter.set_execution_mode(ExecutionMode.REAL)
    adapter.set_provider(ElevenLabsProvider())
    adapter.set_http_client(MockHttpClient(default_response=HttpResponse(
        status_code=200,
        headers={"content-type": "audio/mpeg"},
        body=b"FAKE_MP3_BYTES_FROM_ELEVENLABS",
    )))
    secrets = MockSecretProvider()
    secrets.set(SecretKey(key="api_key", tool_id=adapter.adapter_id), "test_api_key_123")
    adapter.set_secret_provider(secrets)
    adapter.configure({"api_key": "test_api_key_123"})
    adapter.authenticate()
    adapter.mark_ready()
    return adapter


def main() -> None:
    print("=" * 62)
    print("ElevenLabs Audio Asset Demo")
    print("=" * 62)

    output_dir = Path("output/elevenlabs_audio_asset")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 62)
    print("Step 1: MOCK mode writes WAV")
    print("-" * 62)

    mock_adapter = _ready_mock_adapter()
    mock_request = ToolRequest(
        tool_id=uuid4(),
        capability="speech_generation",
        params={
            "action": "synthesize",
            "task_id": "mock_voiceover_asset",
            "text": "Arquivo de voz gerado localmente no modo mock.",
            "voice": "Narrator",
            "output_dir": str(output_dir),
            "output_format": "wav",
            "duration_seconds": 1,
            "write_file": True,
        },
    )
    mock_result = mock_adapter.execute(mock_request)
    mock_path = Path(str(mock_result.output.get("file_path", "")))
    _check(mock_result.success, "Mock synthesis succeeded")
    _check(mock_result.output.get("physical_asset") is True, "Mock output is a physical asset")
    _check(mock_result.output.get("audio_format") == "wav", "Mock output format is WAV")
    _check(mock_path.exists(), "Mock WAV exists")
    _check(mock_path.stat().st_size > 44, "Mock WAV has audio bytes")

    print("\n" + "-" * 62)
    print("Step 2: REAL mode writes mocked binary response")
    print("-" * 62)

    real_adapter = _ready_real_adapter()
    real_request = ToolRequest(
        tool_id=uuid4(),
        capability="speech_generation",
        params={
            "action": "synthesize",
            "task_id": "real_mocked_voiceover_asset",
            "text": "Resposta binaria simulada para validar o caminho real.",
            "voice": "Rachel",
            "voice_id": "mock_voice_id",
            "model_id": "mock_model",
            "output_dir": str(output_dir),
            "output_format": "mp3",
            "duration_seconds": 1,
            "write_file": True,
        },
    )
    real_result = real_adapter.execute(real_request)
    real_path = Path(str(real_result.output.get("file_path", "")))
    _check(real_result.success, "Real-mode mocked synthesis succeeded")
    _check(real_result.output.get("_real") is True, "Real-mode flag preserved")
    _check(real_result.output.get("_audio_in_response") is True, "Audio response detected")
    _check(real_result.output.get("physical_asset") is True, "Real-mode output is a physical asset")
    _check(real_path.exists(), "Real-mode MP3 exists")
    _check(real_path.read_bytes() == b"FAKE_MP3_BYTES_FROM_ELEVENLABS", "Real-mode bytes were written exactly")

    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
