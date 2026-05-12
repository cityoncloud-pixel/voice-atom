from __future__ import annotations

from pathlib import Path

import pytest

from voice_atom.asr.doubao import DoubaoASRProvider
from voice_atom.asr.whisper_cpp import WhisperCppProvider
from voice_atom.config import Settings
from voice_atom.errors import ErrorCode, VoiceAtomError

from tests.helpers import minimal_wav_bytes


def test_whisper_cpp_not_found(tmp_path: Path) -> None:
    model = tmp_path / "m.bin"
    model.write_text("", encoding="utf-8")
    settings = Settings(
        voice_atom_whisper_cpp_bin=tmp_path / "missing_bin",
        voice_atom_whisper_model=model,
        voice_atom_output_dir=tmp_path / "runs",
    )
    p = WhisperCppProvider(settings)
    wav = tmp_path / "a.wav"
    wav.write_bytes(minimal_wav_bytes())
    with pytest.raises(VoiceAtomError) as e:
        p.transcribe(wav)
    assert e.value.code == ErrorCode.WHISPER_CPP_NOT_FOUND


def test_whisper_model_not_found(tmp_path: Path) -> None:
    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    settings = Settings(
        voice_atom_whisper_cpp_bin=bin_path,
        voice_atom_whisper_model=tmp_path / "missing_model.bin",
        voice_atom_output_dir=tmp_path / "runs",
    )
    p = WhisperCppProvider(settings)
    wav = tmp_path / "a.wav"
    wav.write_bytes(minimal_wav_bytes())
    with pytest.raises(VoiceAtomError) as e:
        p.transcribe(wav)
    assert e.value.code == ErrorCode.WHISPER_MODEL_NOT_FOUND


def test_doubao_api_key_missing(tmp_path: Path) -> None:
    settings = Settings(
        voice_atom_provider="doubao",
        doubao_api_key="",
        doubao_asr_model="m",
        doubao_asr_upload_url="https://example.invalid",
        voice_atom_output_dir=tmp_path / "runs",
    )
    p = DoubaoASRProvider(settings)
    wav = tmp_path / "a.wav"
    wav.write_bytes(minimal_wav_bytes())
    with pytest.raises(VoiceAtomError) as e:
        p.transcribe(wav)
    assert e.value.code == ErrorCode.API_KEY_MISSING
