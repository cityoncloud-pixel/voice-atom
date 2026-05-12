from __future__ import annotations

from pathlib import Path

import pytest

from voice_atom.asr.base import ProviderStatus
from voice_atom.asr.doubao import DoubaoASRProvider
from voice_atom.asr.whisper_cpp import WhisperCppProvider
from voice_atom.config import Settings
from voice_atom.errors import ErrorCode, VoiceAtomError
from voice_atom.service import VoiceAtomService

from tests.helpers import minimal_wav_bytes


class _FakeProvider:
    name = "whisper_cpp"
    priority = 1
    is_local = True

    def check_available(self) -> ProviderStatus:
        return ProviderStatus(True, None)

    def transcribe(self, audio_path: Path) -> str:
        return "hello world"


def _settings_with_whisper(tmp_path: Path) -> Settings:
    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    model_path = tmp_path / "model.bin"
    model_path.write_text("", encoding="utf-8")
    return Settings(
        voice_atom_provider="whisper_cpp",
        voice_atom_output_dir=tmp_path / "runs",
        voice_atom_whisper_cpp_bin=bin_path,
        voice_atom_whisper_model=model_path,
    )


def test_transcribe_file_invalid_ext(tmp_path: Path) -> None:
    p = tmp_path / "a.zip"
    p.write_text("x", encoding="utf-8")
    svc = VoiceAtomService(_settings_with_whisper(tmp_path))
    res = svc.transcribe_file(str(p))
    assert res.ok is False
    assert res.error.code == ErrorCode.INVALID_AUDIO_FILE.value


def test_transcribe_file_missing(tmp_path: Path) -> None:
    svc = VoiceAtomService(_settings_with_whisper(tmp_path))
    res = svc.transcribe_file(str(tmp_path / "missing.wav"))
    assert res.ok is False
    assert res.error.code == ErrorCode.INVALID_AUDIO_FILE.value


def test_transcribe_file_success(tmp_path: Path) -> None:
    wav = tmp_path / "x.wav"
    wav.write_bytes(minimal_wav_bytes())
    svc = VoiceAtomService(_settings_with_whisper(tmp_path))

    svc._make_active_provider = lambda: _FakeProvider()  # type: ignore[method-assign]

    res = svc.transcribe_file(str(wav))
    assert res.ok is True
    assert res.text == "hello world"


def test_transcribe_from_mic_success(tmp_path: Path) -> None:
    svc = VoiceAtomService(_settings_with_whisper(tmp_path))

    def fake_recorder(out: Path, seconds: int, samplerate: int = 16000) -> float:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(minimal_wav_bytes())
        return 0.1

    svc._recorder = fake_recorder  # type: ignore[method-assign]
    svc._make_active_provider = lambda: _FakeProvider()  # type: ignore[method-assign]

    res = svc.transcribe_from_mic(1)
    assert res.ok is True
    assert res.text == "hello world"


def test_provider_failure_maps_to_error(tmp_path: Path) -> None:
    class BadProvider:
        name = "whisper_cpp"
        priority = 1
        is_local = True

        def check_available(self) -> ProviderStatus:
            return ProviderStatus(True, None)

        def transcribe(self, audio_path: Path) -> str:
            raise VoiceAtomError(ErrorCode.ASR_FAILED, "boom", details={"x": 1})

    wav = tmp_path / "x.wav"
    wav.write_bytes(minimal_wav_bytes())
    svc = VoiceAtomService(_settings_with_whisper(tmp_path))
    svc._make_active_provider = lambda: BadProvider()  # type: ignore[method-assign]

    res = svc.transcribe_file(str(wav))
    assert res.ok is False
    assert res.error.code == ErrorCode.ASR_FAILED.value
