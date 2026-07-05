"""FFmpeg render adapter — deterministic mock + local real rendering."""

from __future__ import annotations

import json
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


class FFmpegRenderAdapter(AbstractToolAdapter):
    """Adapter for local video rendering through FFmpeg.

    MOCK mode returns deterministic render metadata.
    REAL mode invokes the local FFmpeg/ffprobe binaries via subprocess.
    """

    @property
    def adapter_id(self) -> str:
        return "ffmpeg_render"

    @property
    def tool_name(self) -> str:
        return "FFmpeg Renderer"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({
            Capability.VIDEO_RENDERING,
            Capability.VIDEO_EDITING,
        })

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        return True

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Instale o FFmpeg no Windows.",
                "2. Garanta que 'ffmpeg' e 'ffprobe' estejam no PATH.",
                "3. Configure output_dir/temp_dir se quiser mudar os destinos.",
                "4. Use REAL mode apenas quando quiser gerar arquivo local.",
            ),
            docs_url="https://ffmpeg.org/documentation.html",
            notes="MOCK mode nao precisa de binario instalado.",
        )

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "render_short_video")
        if action not in {"render", "render_short_video"}:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error=f"Unsupported FFmpeg action: {action}",
            )

        duration = int(request.params.get("duration_seconds", 30))
        resolution = str(request.params.get("output_resolution", "1080x1920"))
        output_format = str(request.params.get("output_format", "mp4"))
        task_id = str(request.params.get("task_id", request.tool_id))
        inputs = self._input_summary(request)

        return AdapterExecutionResult(
            success=True,
            summary=f"FFmpeg mock render completed: {resolution} {output_format}",
            output={
                "renderer": "ffmpeg",
                "mode": "mock",
                "task_id": task_id,
                "file_path": f"mock://video/{task_id}.{output_format}",
                "output_format": output_format,
                "output_resolution": resolution,
                "duration_seconds": duration,
                "estimated_size_mb": max(1, round(duration * 2.4)),
                "inputs": inputs,
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "render_short_video")
        if action not in {"render", "render_short_video"}:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error=f"Unsupported FFmpeg action: {action}",
            )

        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if ffmpeg is None or ffprobe is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="FFmpeg REAL mode requires both 'ffmpeg' and 'ffprobe' in PATH",
            )

        task_id = str(request.params.get("task_id", request.tool_id))
        duration = max(1, int(request.params.get("duration_seconds", 30)))
        output_format = str(request.params.get("output_format", "mp4")).lstrip(".")
        resolution = str(request.params.get("output_resolution", "1080x1920"))
        width, height = self._parse_resolution(resolution)
        output_dir = Path(str(self._config.get(
            "output_dir",
            request.params.get("output_dir", "output/video"),
        )))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{task_id}.{output_format}"

        background = str(request.params.get("background_color", "#111827"))
        color = background.replace("#", "0x")
        fps = max(1, int(request.params.get("fps", 30)))
        audio_file = self._existing_path(request.params.get("audio_file_path"))
        image_file = self._existing_path(request.params.get("image_file_path"))
        ffmpeg_cmd = [ffmpeg, "-y"]
        if image_file is not None:
            ffmpeg_cmd.extend([
                "-loop", "1",
                "-framerate", str(fps),
                "-i", str(image_file),
            ])
        else:
            ffmpeg_cmd.extend([
                "-f", "lavfi",
                "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration}",
            ])
        if audio_file is not None:
            ffmpeg_cmd.extend(["-i", str(audio_file)])
        else:
            ffmpeg_cmd.extend([
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            ])

        ffmpeg_cmd.extend([
            "-t", str(duration),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-vf", (
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},format=yuv420p"
            ),
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ])
        rendered = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=max(30, duration + 30),
            check=False,
        )
        if rendered.returncode != 0:
            return AdapterExecutionResult(
                success=False,
                summary="",
                output={"command": ffmpeg_cmd, "stderr": rendered.stderr[-2000:]},
                error=f"FFmpeg failed with exit code {rendered.returncode}",
            )

        probe = self._probe(ffprobe, output_path)
        return AdapterExecutionResult(
            success=True,
            summary=f"FFmpeg real render completed: {output_path.name}",
            output={
                "renderer": "ffmpeg",
                "mode": "real",
                "task_id": task_id,
                "file_path": str(output_path.resolve()),
                "output_format": output_format,
                "output_resolution": f"{width}x{height}",
                "duration_seconds": duration,
                "file_size_bytes": output_path.stat().st_size,
                "inputs": {
                    "audio_file_path": str(audio_file.resolve()) if audio_file else "",
                    "image_file_path": str(image_file.resolve()) if image_file else "",
                    "used_audio_file": audio_file is not None,
                    "used_image_file": image_file is not None,
                },
                "probe": probe,
                "_real": True,
            },
        )

    def _parse_resolution(self, resolution: str) -> tuple[int, int]:
        parts = resolution.lower().split("x", 1)
        if len(parts) != 2:
            return 1080, 1920
        try:
            width = max(1, int(parts[0]))
            height = max(1, int(parts[1]))
        except ValueError:
            return 1080, 1920
        return width, height

    def _probe(self, ffprobe: str, output_path: Path) -> dict[str, Any]:
        probe_cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration,size,format_name",
            "-show_entries", "stream=codec_type,codec_name,width,height",
            "-of", "json",
            str(output_path),
        ]
        probed = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if probed.returncode != 0:
            return {"error": probed.stderr[-1000:]}
        try:
            loaded = json.loads(probed.stdout or "{}")
        except json.JSONDecodeError:
            return {"error": "ffprobe returned invalid JSON"}
        return loaded if isinstance(loaded, dict) else {}

    def _existing_path(self, raw: Any) -> Path | None:
        if raw is None:
            return None
        value = str(raw).strip()
        if not value:
            return None
        path = Path(value).expanduser()
        if path.is_file():
            return path.resolve()
        return None

    def _input_summary(self, request: ToolRequest) -> dict[str, Any]:
        audio_file = self._existing_path(request.params.get("audio_file_path"))
        image_file = self._existing_path(request.params.get("image_file_path"))
        return {
            "audio_file_path": str(audio_file) if audio_file else "",
            "image_file_path": str(image_file) if image_file else "",
            "used_audio_file": False,
            "used_image_file": False,
            "available_audio_file": audio_file is not None,
            "available_image_file": image_file is not None,
        }
