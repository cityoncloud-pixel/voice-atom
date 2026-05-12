"""Audio helpers."""

from __future__ import annotations

from pathlib import Path

from voice_atom.errors import ErrorCode, VoiceAtomError

# whisper.cpp CLI commonly accepts these; non-wav may be converted before ASR (e.g. HTTP upload).
WHISPER_INPUT_SUFFIXES = frozenset(
    {".wav", ".flac", ".mp3", ".ogg", ".opus", ".webm", ".m4a", ".aac"}
)


def ensure_wav_file(path: str | Path) -> Path:
    """Require an existing .wav file (CLI / strict path API)."""
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
            "This entry only accepts .wav files",
            recoverable=True,
            details={"path": str(p)},
        )
    return p


def ensure_transcribable_file(path: str | Path) -> Path:
    """Existing file whose suffix is likely supported by whisper.cpp (after any conversion)."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise VoiceAtomError(
            ErrorCode.INVALID_AUDIO_FILE,
            f"Audio file not found: {p}",
            recoverable=True,
            details={"path": str(p)},
        )
    suf = p.suffix.lower()
    if suf not in WHISPER_INPUT_SUFFIXES:
        raise VoiceAtomError(
            ErrorCode.INVALID_AUDIO_FILE,
            f"Unsupported audio extension: {suf or '(none)'}",
            recoverable=True,
            details={"path": str(p), "allowed": sorted(WHISPER_INPUT_SUFFIXES)},
        )
    return p
