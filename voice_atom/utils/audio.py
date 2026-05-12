"""Audio helpers."""

from __future__ import annotations

from pathlib import Path

from voice_atom.errors import ErrorCode, VoiceAtomError


def ensure_wav_file(path: str | Path) -> Path:
    p = Path(path).expanduser()
    if not p.is_file():
        raise VoiceAtomError(
            ErrorCode.INVALID_AUDIO_FILE,
            f"Audio file not found: {p}",
            recoverable=True,
            details={"path": str(p)},
        )
    if p.suffix.lower() != ".wav":
        raise VoiceAtomError(
            ErrorCode.INVALID_AUDIO_FILE,
            "First batch only supports .wav files",
            recoverable=True,
            details={"path": str(p)},
        )
    return p
