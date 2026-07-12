"""KokoroTTSAdapter contract demo without model download or REAL synthesis."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from core.tools.adapters import (
    ExecutionMode,
    KokoroTTSAdapter,
    ToolRequest,
)
from core.tools.capabilities import Capability

_ASSERTION_COUNTER = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _request(**params: object) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability=Capability.SPEECH_GENERATION.value,
        params=dict(params),
    )


def main() -> None:
    print("=" * 62)
    print("Kokoro Local TTS Adapter Demo")
    print("=" * 62)

    adapter = KokoroTTSAdapter()
    adapter.configure({})
    adapter.mark_ready()

    _check(adapter.adapter_id == "kokoro_tts", "Adapter id set")
    _check(adapter.tool_name == "Kokoro Local TTS", "Tool name set")
    _check(
        adapter.supported_capabilities() == frozenset({Capability.SPEECH_GENERATION}),
        "Only SPEECH_GENERATION is advertised",
    )
    _check(adapter.required_credential_keys() == (), "No credentials required")
    _check(adapter.validate_credentials(), "Credential validation is unconditional")
    _check(adapter.execution_mode == ExecutionMode.MOCK, "MOCK is the default mode")

    result = adapter.execute(
        _request(
            action="synthesize",
            text="A nova fase dos games comeca agora.",
            task_id="fase-nova-intro",
        )
    )
    _check(result.success, "MOCK synthesis succeeds")
    _check(result.output["provider"] == "kokoro", "Provider is recorded")
    _check(result.output["voice"] == "pm_alex", "Brazilian voice is the default")
    _check(result.output["speed"] == 1.0, "Default speed is recorded")
    _check(result.output["sample_rate"] == 24000, "Sample rate is 24 kHz")
    _check(
        result.output["file_path"] == "mock://audio/fase-nova-intro.wav",
        "MOCK file path is deterministic",
    )

    custom = adapter.execute(
        _request(text="Teste de ritmo.", voice="pf_dora", speed=1.15)
    )
    _check(custom.success, "Custom MOCK request succeeds")
    _check(custom.output["voice"] == "pf_dora", "Custom voice is preserved")
    _check(custom.output["speed"] == 1.15, "Custom speed is preserved")

    unsupported = adapter.execute(_request(action="clone", text="Nao executar."))
    _check(not unsupported.success, "Unsupported action is controlled")
    _check("Unsupported Kokoro action" in unsupported.error, "Action error is clear")
    empty = adapter.execute(_request(text="   "))
    _check(not empty.success, "Empty text is rejected")
    _check(empty.output == {}, "Validation failure has no fake output")
    invalid_speed = adapter.execute(_request(text="Teste.", speed=0))
    _check(not invalid_speed.success, "Invalid speed is rejected")

    guidance = adapter.owner_guidance()
    _check(guidance.docs_url == "https://github.com/hexgrad/kokoro", "Official docs linked")
    _check("pm_alex" in guidance.notes, "Default voice documented")
    _check(adapter.check_availability(), "Default Python and runner are available")

    missing_runner = KokoroTTSAdapter()
    missing_runner.configure({
        "python_executable": sys.executable,
        "runner_path": Path("missing-kokoro-runner.py"),
    })
    missing_runner.set_execution_mode(ExecutionMode.REAL)
    _check(not missing_runner.check_availability(), "Missing runner is unavailable")
    missing_result = missing_runner.execute(_request(text="Nao sintetizar."))
    _check(not missing_result.success, "REAL fails safely without runner")
    _check("runner was not found" in missing_result.error, "Missing runner error is clear")
    _check(missing_result.output == {}, "No REAL output is fabricated")

    invalid_config = KokoroTTSAdapter()
    invalid_config.configure({"default_speed": 0})
    _check(not invalid_config.validate_configuration({"default_speed": 0}), "Bad config rejected")

    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("No Kokoro model was downloaded and no REAL speech was generated.")
    print("=" * 62)


if __name__ == "__main__":
    main()
