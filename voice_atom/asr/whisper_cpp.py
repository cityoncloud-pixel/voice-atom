"""whisper.cpp subprocess provider (CLI only in v1)."""

from __future__ import annotations

import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from voice_atom.asr.base import ProviderStatus
from voice_atom.config import Settings
from voice_atom.errors import ErrorCode, VoiceAtomError


class WhisperCppProvider:
    name = "whisper_cpp"
    priority = 1
    is_local = True

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check_available(self) -> ProviderStatus:
        bin_path = self._settings.voice_atom_whisper_cpp_bin.expanduser()
        if not bin_path.is_file():
            return ProviderStatus(False, f"whisper binary not found: {bin_path}")
        model_path = self._settings.voice_atom_whisper_model.expanduser()
        if not model_path.is_file():
            return ProviderStatus(False, f"whisper model not found: {model_path}")
        return ProviderStatus(True, None)

    def transcribe(self, audio_path: Path) -> str:
        bin_path = self._settings.voice_atom_whisper_cpp_bin.expanduser()
        if not bin_path.is_file():
            raise VoiceAtomError(
                ErrorCode.WHISPER_CPP_NOT_FOUND,
                f"whisper.cpp binary not found: {bin_path}",
                details={"path": str(bin_path)},
            )
        model_path = self._settings.voice_atom_whisper_model.expanduser()
        if not model_path.is_file():
            raise VoiceAtomError(
                ErrorCode.WHISPER_MODEL_NOT_FOUND,
                f"whisper.cpp model not found: {model_path}",
                details={"path": str(model_path)},
            )

        audio_path = audio_path.expanduser().resolve()

        with tempfile.TemporaryDirectory(prefix="voice_atom_whisper_") as tmp:
            out_prefix = Path(tmp) / "out"
            cmd: list[str] = [
                str(bin_path),
                "-m",
                str(model_path),
                "-f",
                str(audio_path),
                "-l",
                self._settings.voice_atom_language,
                "-t",
                str(self._settings.voice_atom_threads),
                "-otxt",
                "-of",
                str(out_prefix),
            ]
            extra = self._settings.voice_atom_whisper_extra_args.strip()
            if extra:
                cmd.extend(shlex.split(extra))

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3600,
                    check=False,
                )
            except subprocess.TimeoutExpired as e:
                raise VoiceAtomError(
                    ErrorCode.PROVIDER_TIMEOUT,
                    "whisper.cpp subprocess timed out",
                    details={"timeout_seconds": 3600},
                ) from e
            except OSError as e:
                raise VoiceAtomError(
                    ErrorCode.WHISPER_TRANSCRIBE_FAILED,
                    f"failed to execute whisper.cpp: {e}",
                    details={"cmd": " ".join(cmd[:6]) + " ..."},
                ) from e

            txt_path = Path(str(out_prefix) + ".txt")
            text = ""
            if txt_path.is_file():
                text = txt_path.read_text(encoding="utf-8", errors="replace").strip()
            if not text and proc.stdout:
                text = proc.stdout.strip()

            if proc.returncode != 0:
                err_tail = (proc.stderr or proc.stdout or "").strip()[-2000:]
                raise VoiceAtomError(
                    ErrorCode.WHISPER_TRANSCRIBE_FAILED,
                    "whisper.cpp returned non-zero exit code",
                    recoverable=True,
                    details={"returncode": proc.returncode, "stderr_tail": err_tail},
                )

            if not text:
                raise VoiceAtomError(
                    ErrorCode.WHISPER_TRANSCRIBE_FAILED,
                    "whisper.cpp produced empty transcript",
                    recoverable=True,
                    details={},
                )

            return _strip_boilerplate(text)


def _strip_boilerplate(text: str) -> str:
    """Remove common whisper.cpp header lines if present."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # drop leading [hh:mm:ss] style timestamps if entire line matches
    ts = re.compile(r"^\[\d{2}:\d{2}:\d{2}\.\d+\]\s*")
    cleaned: list[str] = []
    for ln in lines:
        cleaned.append(ts.sub("", ln).strip())
    return " ".join(s for s in cleaned if s).strip()
