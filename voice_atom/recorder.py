"""Microphone capture to WAV (fixed duration)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import sounddevice as sd
import wave

from voice_atom.errors import ErrorCode, VoiceAtomError


def record_wav_seconds(out_path: Path, seconds: int, samplerate: int = 16000) -> float:
    """Record mono int16 WAV to out_path; returns duration in seconds."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * samplerate)
    try:
        audio = sd.rec(frames, samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
    except RuntimeError as e:
        msg = str(e).lower()
        if "input" in msg or "device" in msg or "wasapi" in msg:
            raise VoiceAtomError(
                ErrorCode.MIC_NOT_FOUND,
                f"microphone not available: {e}",
                details={},
            ) from e
        raise VoiceAtomError(
            ErrorCode.RECORDING_FAILED,
            f"recording failed: {e}",
            details={},
        ) from e
    except Exception as e:  # noqa: BLE001 - surface as recording failure
        raise VoiceAtomError(
            ErrorCode.RECORDING_FAILED,
            f"recording failed: {e}",
            details={},
        ) from e

    audio = np.clip(audio.reshape(-1), -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)

    try:
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(pcm.tobytes())
    except OSError as e:
        raise VoiceAtomError(
            ErrorCode.AUDIO_SAVE_FAILED,
            f"failed to write wav: {e}",
            details={"path": str(out_path)},
        ) from e

    return float(len(pcm)) / float(samplerate)
