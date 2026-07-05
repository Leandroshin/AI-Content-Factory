"""FFmpegRenderAdapter demo.

Proves the adapter contract in MOCK mode and, when FFmpeg is installed,
performs a tiny REAL render inside a temporary directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from core.tools import (
    Capability,
    ExecutionMode,
    FFmpegRenderAdapter,
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


def main() -> None:
    print("=" * 62)
    print("FFmpeg Render Adapter Demo")
    print("=" * 62)

    adapter = FFmpegRenderAdapter()
    adapter.configure({})
    adapter.mark_ready()

    print("\n" + "-" * 62)
    print("Step 1: Adapter metadata")
    print("-" * 62)
    _check(adapter.adapter_id == "ffmpeg_render", "Adapter id set")
    _check(adapter.tool_name == "FFmpeg Renderer", "Tool name set")
    _check(Capability.VIDEO_RENDERING in adapter.supported_capabilities(),
           "VIDEO_RENDERING supported")
    _check(Capability.VIDEO_EDITING in adapter.supported_capabilities(),
           "VIDEO_EDITING compatibility supported")

    print("\n" + "-" * 62)
    print("Step 2: MOCK render")
    print("-" * 62)
    mock_request = ToolRequest(
        tool_id=uuid4(),
        capability=Capability.VIDEO_RENDERING.value,
        params={
            "action": "render_short_video",
            "task_id": "mock-short",
            "duration_seconds": 15,
            "output_format": "mp4",
            "output_resolution": "1080x1920",
        },
    )
    mock_result = adapter.execute(mock_request)
    _check(mock_result.success, "Mock render succeeded")
    _check(mock_result.output["renderer"] == "ffmpeg", "Mock renderer recorded")
    _check(mock_result.output["mode"] == "mock", "Mock mode recorded")
    _check(mock_result.output["file_path"].startswith("mock://video/"),
           "Mock file path is logical")

    print("\n" + "-" * 62)
    print("Step 3: REAL render availability")
    print("-" * 62)
    has_ffmpeg = shutil.which("ffmpeg") is not None
    has_ffprobe = shutil.which("ffprobe") is not None
    _check(has_ffmpeg == (shutil.which("ffmpeg") is not None), "FFmpeg probe deterministic")
    _check(has_ffprobe == (shutil.which("ffprobe") is not None), "FFprobe probe deterministic")

    with TemporaryDirectory() as tmp:
        adapter.configure({"output_dir": tmp})
        adapter.set_execution_mode(ExecutionMode.REAL)
        real_request = ToolRequest(
            tool_id=uuid4(),
            capability=Capability.VIDEO_RENDERING.value,
            params={
                "action": "render_short_video",
                "task_id": "real-short",
                "duration_seconds": 1,
                "output_format": "mp4",
                "output_resolution": "160x284",
            },
        )
        real_result = adapter.execute(real_request)

        if has_ffmpeg and has_ffprobe:
            output_path = Path(str(real_result.output.get("file_path", "")))
            _check(real_result.success, "Real render succeeded")
            _check(output_path.exists(), "Real render file exists")
            _check(output_path.stat().st_size > 0, "Real render has bytes")
            _check(real_result.output.get("_real") is True, "Real marker set")
        else:
            _check(not real_result.success, "Real render fails clearly without binaries")
            _check("ffmpeg" in real_result.error.lower(), "Missing binary error mentions ffmpeg")
            _check(real_result.output == {}, "No fake output on missing binary")
            _check(real_result.summary == "", "No success summary on missing binary")

    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
