"""Path helpers for run artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def next_wav_path(output_dir: Path) -> Path:
    """Return runs/YYYY-MM-DD/NNN.wav with incrementing NNN for that day."""
    output_dir = output_dir.resolve()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = output_dir / day
    day_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        candidate = day_dir / f"{n:03d}.wav"
        if not candidate.exists():
            return candidate
        n += 1
