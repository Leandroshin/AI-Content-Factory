"""HyperFrames adapter for deterministic HTML-to-video rendering."""

from __future__ import annotations

import shutil
import subprocess
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


class HyperFramesRenderAdapter(AbstractToolAdapter):
    """Render audited HTML compositions through the local HyperFrames CLI."""

    @property
    def adapter_id(self) -> str:
        return "hyperframes_render"

    @property
    def tool_name(self) -> str:
        return "HyperFrames Renderer"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.VIDEO_EDITING, Capability.VIDEO_RENDERING})

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        return True

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        if self._execution_mode == ExecutionMode.MOCK:
            return True
        return shutil.which("node") is not None and shutil.which("npx") is not None

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Keep Node.js 22+ and FFmpeg available.",
                "2. Create and audit a HyperFrames HTML composition.",
                "3. Run lint and preview before REAL rendering.",
                "4. Keep generated media provenance and licenses with the project.",
            ),
            docs_url="https://hyperframes.video/docs",
            notes="HyperFrames is local/open source; paid image/video generation remains optional.",
        )

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = str(request.params.get("action", "render"))
        if action not in {"lint", "preview", "render"}:
            return AdapterExecutionResult(success=False, summary="", error=f"Unsupported HyperFrames action: {action}")
        task_id = str(request.params.get("task_id", request.tool_id))
        output_format = str(request.params.get("output_format", "mp4"))
        return AdapterExecutionResult(
            success=True,
            summary=f"HyperFrames mock {action} completed",
            output={
                "renderer": "hyperframes",
                "mode": "mock",
                "action": action,
                "task_id": task_id,
                "file_path": f"mock://video/{task_id}.{output_format}",
                "composition_file_path": str(request.params.get("composition_file_path", "")),
                "quality_standard": str(request.params.get("quality_standard", "hyperframes_editorial_v1")),
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = str(request.params.get("action", "render"))
        if action not in {"lint", "render"}:
            return AdapterExecutionResult(success=False, summary="", error=f"Unsupported HyperFrames REAL action: {action}")
        npx = shutil.which("npx")
        if npx is None:
            return AdapterExecutionResult(success=False, summary="", error="HyperFrames requires npx in PATH")
        composition = Path(str(request.params.get("composition_file_path", ""))).expanduser()
        if not composition.is_file() or composition.suffix.lower() != ".html":
            return AdapterExecutionResult(success=False, summary="", error="A valid HTML composition_file_path is required")
        if composition.name.lower() != "index.html":
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="HyperFrames REAL compositions must use a dedicated project directory with index.html",
            )

        base_command = [npx, "--yes", "hyperframes"]
        project_dir = composition.resolve().parent
        command = [*base_command, action, str(project_dir), "--json"]
        output_path: Path | None = None
        if action == "render":
            linted = subprocess.run(
                [*base_command, "lint", str(project_dir), "--json"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if linted.returncode != 0:
                return AdapterExecutionResult(
                    success=False,
                    summary="",
                    output={"lint_stdout": linted.stdout[-2000:], "lint_stderr": linted.stderr[-2000:]},
                    error=f"HyperFrames lint failed with exit code {linted.returncode}",
                )
            checked = subprocess.run(
                [*base_command, "check", str(project_dir), "--json", "--strict"],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if checked.returncode != 0:
                return AdapterExecutionResult(
                    success=False,
                    summary="",
                    output={"check_stdout": checked.stdout[-4000:], "check_stderr": checked.stderr[-2000:]},
                    error=f"HyperFrames quality check failed with exit code {checked.returncode}",
                )
            output_dir = Path(str(request.params.get("output_dir", "output/hyperframes"))).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)
            task_id = str(request.params.get("task_id", request.tool_id))
            output_path = output_dir / f"{task_id}.mp4"
            command.extend(["--output", str(output_path.resolve())])

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=max(60, int(request.params.get("timeout_seconds", 900))),
            check=False,
        )
        if completed.returncode != 0:
            return AdapterExecutionResult(
                success=False,
                summary="",
                output={"stderr": completed.stderr[-2000:]},
                error=f"HyperFrames {action} failed with exit code {completed.returncode}",
            )
        if output_path is not None and (not output_path.is_file() or output_path.stat().st_size == 0):
            return AdapterExecutionResult(
                success=False,
                summary="",
                output={"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]},
                error="HyperFrames reported success but did not create a non-empty MP4",
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"HyperFrames real {action} completed",
            output={
                "renderer": "hyperframes",
                "mode": "real",
                "action": action,
                "composition_file_path": str(composition.resolve()),
                "file_path": str(output_path.resolve()) if output_path else "",
                "file_size_bytes": output_path.stat().st_size if output_path else 0,
                "stdout": completed.stdout[-2000:],
                "_real": True,
            },
        )
