"""Kokoro TTS adapter with deterministic MOCK and isolated local REAL execution."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.tools.adapters.base import AbstractToolAdapter
from core.tools.adapters.models import (
    AdapterExecutionResult,
    ExecutionMode,
    OwnerGuidance,
    ToolRequest,
)
from core.tools.capabilities import Capability


class KokoroTTSAdapter(AbstractToolAdapter):
    """Generate Brazilian Portuguese speech through a separate Kokoro runner.

    The main application never imports Kokoro or its optional dependencies.
    REAL execution sends a JSON request through stdin to a configurable Python
    process, keeping long text and user content out of command-line arguments.
    """

    @property
    def adapter_id(self) -> str:
        return "kokoro_tts"

    @property
    def tool_name(self) -> str:
        return "Kokoro Local TTS"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.SPEECH_GENERATION})

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        python_executable = config.get("python_executable", sys.executable)
        runner_path = config.get("runner_path", self._default_runner_path())
        timeout_seconds = config.get("timeout_seconds", 900)
        speed = config.get("default_speed", 1.0)
        return (
            isinstance(python_executable, (str, Path))
            and bool(str(python_executable).strip())
            and isinstance(runner_path, (str, Path))
            and bool(str(runner_path).strip())
            and self._positive_number(timeout_seconds)
            and self._positive_number(speed)
        )

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        python_executable = self._resolve_python_executable()
        runner_path = self._resolve_runner_path()
        return python_executable is not None and runner_path.is_file()

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Crie um ambiente Python isolado para o Kokoro.",
                "2. Instale o pacote oficial kokoro e a dependencia soundfile.",
                "3. Instale o eSpeak NG exigido para portugues no Windows.",
                "4. Configure python_executable para o Python desse ambiente.",
                "5. Use REAL somente quando quiser gerar um WAV local.",
            ),
            docs_url="https://github.com/hexgrad/kokoro",
            notes=(
                "Nao requer chave de API. O runner usa KPipeline(lang_code='p') "
                "e a voz brasileira pm_alex por padrao."
            ),
        )

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        validation_error = self._validate_request(request)
        if validation_error:
            return self._failure(validation_error)

        text = str(request.params["text"]).strip()
        voice = str(request.params.get("voice", "pm_alex")).strip()
        speed = self._request_speed(request)
        task_id = self._task_id(request)
        duration_seconds = round(max(0.25, len(text) * 0.065 / speed), 2)
        return AdapterExecutionResult(
            success=True,
            summary=f"Kokoro mock speech generated: {len(text)} chars ({voice})",
            output={
                "provider": "kokoro",
                "mode": "mock",
                "task_id": task_id,
                "text": text,
                "voice": voice,
                "speed": speed,
                "sample_rate": 24000,
                "duration_seconds": duration_seconds,
                "file_path": f"mock://audio/{task_id}.wav",
                "output_format": "wav",
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        validation_error = self._validate_request(request)
        if validation_error:
            return self._failure(validation_error)

        python_executable = self._resolve_python_executable()
        if python_executable is None:
            return self._failure(
                "Kokoro REAL mode requires a valid configured Python executable"
            )
        runner_path = self._resolve_runner_path()
        if not runner_path.is_file():
            return self._failure(
                f"Kokoro REAL runner was not found: {runner_path}"
            )

        text = str(request.params["text"]).strip()
        voice = str(request.params.get("voice", "pm_alex")).strip()
        speed = self._request_speed(request)
        output_path = self._output_path(request)
        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "output_path": str(output_path),
        }
        timeout_seconds = float(
            request.params.get(
                "timeout_seconds",
                self._config.get("timeout_seconds", 900),
            )
        )

        try:
            completed = subprocess.run(
                [python_executable, str(runner_path)],
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            return self._failure(
                f"Kokoro REAL execution timed out after {timeout_seconds:g} seconds"
            )
        except OSError as exc:
            return self._failure(f"Kokoro REAL process could not start: {exc}")

        runner_result = self._parse_runner_result(completed.stdout)
        if completed.returncode != 0:
            error = str(runner_result.get("error", "")).strip()
            if not error:
                error = completed.stderr.strip()[-2000:]
            return self._failure(
                error or f"Kokoro runner failed with exit code {completed.returncode}",
                output={"returncode": completed.returncode, "_real": True},
            )
        if not runner_result.get("success"):
            return self._failure(
                str(runner_result.get("error", "Kokoro runner returned an invalid result")),
                output={"_real": True},
            )

        created_path = Path(str(runner_result.get("file_path", output_path)))
        if not created_path.is_file() or created_path.stat().st_size == 0:
            return self._failure(
                "Kokoro runner reported success but did not create a non-empty WAV",
                output={"_real": True},
            )

        return AdapterExecutionResult(
            success=True,
            summary=f"Kokoro real speech generated: {created_path.name}",
            output={
                "provider": "kokoro",
                "mode": "real",
                "task_id": self._task_id(request),
                "text": text,
                "voice": voice,
                "speed": speed,
                "sample_rate": int(runner_result.get("sample_rate", 24000)),
                "samples": int(runner_result.get("samples", 0)),
                "duration_seconds": float(
                    runner_result.get("duration_seconds", 0.0)
                ),
                "chunks": int(runner_result.get("chunks", 0)),
                "file_path": str(created_path.resolve()),
                "file_size_bytes": created_path.stat().st_size,
                "output_format": "wav",
                "_real": True,
            },
        )

    def _validate_request(self, request: ToolRequest) -> str:
        action = str(request.params.get("action", "synthesize"))
        if action not in {"synthesize", "text_to_speech"}:
            return f"Unsupported Kokoro action: {action}"
        text = request.params.get("text")
        if not isinstance(text, str) or not text.strip():
            return "Kokoro requires non-empty text"
        voice = request.params.get("voice", "pm_alex")
        if not isinstance(voice, str) or not voice.strip():
            return "Kokoro requires a non-empty voice"
        speed = request.params.get(
            "speed",
            self._config.get("default_speed", 1.0),
        )
        if not self._positive_number(speed):
            return "Kokoro speed must be a positive number"
        timeout_seconds = request.params.get(
            "timeout_seconds",
            self._config.get("timeout_seconds", 900),
        )
        if not self._positive_number(timeout_seconds):
            return "Kokoro timeout_seconds must be a positive number"
        return ""

    def _request_speed(self, request: ToolRequest) -> float:
        return float(
            request.params.get(
                "speed",
                self._config.get("default_speed", 1.0),
            )
        )

    def _output_path(self, request: ToolRequest) -> Path:
        explicit = str(request.params.get("output_file_path", "")).strip()
        if explicit:
            return Path(explicit).expanduser().resolve()
        output_dir = Path(
            str(
                request.params.get(
                    "output_dir",
                    self._config.get("output_dir", "output/kokoro"),
                )
            )
        ).expanduser()
        return (output_dir / f"{self._task_id(request)}.wav").resolve()

    def _task_id(self, request: ToolRequest) -> str:
        raw = str(request.params.get("task_id", request.tool_id)).strip()
        safe = "".join(char if char.isalnum() or char in "-_." else "-" for char in raw)
        return safe.strip(".-") or str(request.tool_id)

    def _resolve_python_executable(self) -> str | None:
        raw = str(self._config.get("python_executable", sys.executable)).strip()
        path = Path(raw).expanduser()
        if path.is_file():
            return str(path.resolve())
        return shutil.which(raw)

    def _resolve_runner_path(self) -> Path:
        raw = self._config.get("runner_path", self._default_runner_path())
        return Path(str(raw)).expanduser().resolve()

    def _default_runner_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "scripts" / "kokoro_tts_runner.py"

    def _parse_runner_result(self, stdout: str) -> dict[str, Any]:
        for line in reversed(stdout.splitlines()):
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                return loaded
        return {}

    def _positive_number(self, value: Any) -> bool:
        if isinstance(value, bool):
            return False
        try:
            return float(value) > 0
        except (TypeError, ValueError):
            return False

    def _failure(
        self,
        error: str,
        *,
        output: dict[str, Any] | None = None,
    ) -> AdapterExecutionResult:
        return AdapterExecutionResult(
            success=False,
            summary="",
            output=output or {},
            error=error,
        )
