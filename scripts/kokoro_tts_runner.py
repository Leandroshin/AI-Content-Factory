"""Isolated Kokoro TTS subprocess runner.

Reads one JSON object from stdin and writes one JSON result line to stdout.
Optional Kokoro dependencies are deliberately imported only in this process.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SAMPLE_RATE = 24000


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _read_request() -> dict[str, Any]:
    raw = sys.stdin.read()
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("stdin JSON must be an object")
    return loaded


def _positive_speed(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("speed must be a positive number")
    speed = float(value)
    if speed <= 0:
        raise ValueError("speed must be a positive number")
    return speed


def main() -> int:
    try:
        request = _read_request()
        text = request.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        voice = request.get("voice", "pm_alex")
        if not isinstance(voice, str) or not voice.strip():
            raise ValueError("voice must be a non-empty string")
        speed = _positive_speed(request.get("speed", 1.0))
        output_value = request.get("output_path")
        if not isinstance(output_value, str) or not output_value.strip():
            raise ValueError("output_path must be a non-empty string")
        output_path = Path(output_value).expanduser().resolve()

        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline

        pipeline = KPipeline(lang_code="p")
        chunks = []
        for _, _, audio in pipeline(text.strip(), voice=voice.strip(), speed=speed):
            chunk = np.asarray(audio, dtype=np.float32).reshape(-1)
            if chunk.size:
                chunks.append(chunk)
        if not chunks:
            raise RuntimeError("Kokoro produced no audio chunks")

        combined = np.concatenate(chunks)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, combined, SAMPLE_RATE, subtype="PCM_16")
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError("Kokoro did not create a non-empty WAV")

        _emit({
            "success": True,
            "file_path": str(output_path),
            "sample_rate": SAMPLE_RATE,
            "samples": int(combined.size),
            "duration_seconds": round(float(combined.size) / SAMPLE_RATE, 3),
            "chunks": len(chunks),
            "voice": voice.strip(),
            "speed": speed,
        })
        return 0
    except Exception as exc:  # Runner boundary converts all failures to protocol data.
        _emit({
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
