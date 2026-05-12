from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from voice_atom.asr.whisper_cpp import WhisperCppProvider
from voice_atom.cli import app

runner = CliRunner()


def test_cli_providers_list_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    model_path = tmp_path / "model.bin"
    model_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("VOICE_ATOM_WHISPER_CPP_BIN", str(bin_path))
    monkeypatch.setenv("VOICE_ATOM_WHISPER_MODEL", str(model_path))
    monkeypatch.setenv("VOICE_ATOM_OUTPUT_DIR", str(tmp_path / "runs"))

    r = runner.invoke(app, ["providers", "list", "--json"])
    assert r.exit_code == 0, r.output
    assert "whisper_cpp" in r.output


def test_cli_config_check_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    model_path = tmp_path / "model.bin"
    model_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("VOICE_ATOM_WHISPER_CPP_BIN", str(bin_path))
    monkeypatch.setenv("VOICE_ATOM_WHISPER_MODEL", str(model_path))
    monkeypatch.setenv("VOICE_ATOM_OUTPUT_DIR", str(tmp_path / "runs"))

    r = runner.invoke(app, ["config", "check", "--json"])
    assert r.exit_code == 0, r.output


def test_cli_transcribe_file_json(tmp_path: Path, monkeypatch) -> None:
    import wave
    from io import BytesIO

    monkeypatch.chdir(tmp_path)
    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    model_path = tmp_path / "model.bin"
    model_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("VOICE_ATOM_WHISPER_CPP_BIN", str(bin_path))
    monkeypatch.setenv("VOICE_ATOM_WHISPER_MODEL", str(model_path))
    monkeypatch.setenv("VOICE_ATOM_OUTPUT_DIR", str(tmp_path / "runs"))

    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 160)
    wav = tmp_path / "t.wav"
    wav.write_bytes(buf.getvalue())

    def fake_transcribe(self, audio_path: Path) -> str:
        return "cli-ok"

    monkeypatch.setattr(WhisperCppProvider, "transcribe", fake_transcribe)

    r = runner.invoke(app, ["transcribe-file", str(wav), "--json"])
    assert r.exit_code == 0, r.output
    assert "cli-ok" in r.output
