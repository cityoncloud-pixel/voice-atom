from __future__ import annotations

from pathlib import Path

import json
import pytest
from fastapi.testclient import TestClient

from voice_atom.server import app

from tests.helpers import minimal_wav_bytes


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from voice_atom import server
    from voice_atom.config import Settings
    from voice_atom.service import VoiceAtomService

    bin_path = tmp_path / "whisper-cli"
    bin_path.write_text("", encoding="utf-8")
    model_path = tmp_path / "model.bin"
    model_path.write_text("", encoding="utf-8")
    settings = Settings(
        voice_atom_provider="whisper_cpp",
        voice_atom_output_dir=tmp_path / "runs",
        voice_atom_whisper_cpp_bin=bin_path,
        voice_atom_whisper_model=model_path,
    )
    svc = VoiceAtomService(settings)

    class _FakeProvider:
        name = "whisper_cpp"
        priority = 1
        is_local = True

        def check_available(self):
            from voice_atom.asr.base import ProviderStatus

            return ProviderStatus(True, None)

        def transcribe(self, audio_path: Path) -> str:
            return "hello world"

    svc._make_active_provider = lambda: _FakeProvider()  # type: ignore[method-assign]

    def fake_recorder(out: Path, seconds: int, samplerate: int = 16000) -> float:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(minimal_wav_bytes())
        return 0.1

    svc._recorder = fake_recorder  # type: ignore[method-assign]

    monkeypatch.setattr(server, "_svc", svc, raising=False)
    return TestClient(app)


def test_http_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["service"] == "voice-atom"


def test_http_providers(client: TestClient) -> None:
    r = client.get("/providers")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert any(p["name"] == "whisper_cpp" for p in body["providers"])


def test_http_config_check_no_full_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from voice_atom import server

    monkeypatch.setattr(server._svc.settings, "doubao_api_key", "sk-1234567890abcdef", raising=False)
    r = client.get("/config/check")
    assert r.status_code == 200
    body = r.json()
    assert "sk-1234567890abcdef" not in json.dumps(body, ensure_ascii=False)


def test_http_transcribe_file(client: TestClient, tmp_path: Path) -> None:
    wav = tmp_path / "api.wav"
    wav.write_bytes(minimal_wav_bytes())
    r = client.post("/transcribe-file", json={"audio_path": str(wav)})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["text"] == "hello world"
    assert body["timing"]["asr_ms"] >= 0
    assert body["timing"]["total_ms"] >= body["timing"]["asr_ms"]


def test_http_record(client: TestClient) -> None:
    r = client.post("/record", json={"seconds": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["text"] == "hello world"
    assert body["timing"]["asr_ms"] >= 0


def test_http_transcribe_upload_wav(client: TestClient) -> None:
    r = client.post(
        "/transcribe-upload",
        files={"file": ("clip.wav", minimal_wav_bytes(), "audio/wav")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["text"] == "hello world"
    ti = body["timing"]
    assert ti["upload_save_ms"] >= 0
    assert ti["audio_convert_ms"] == 0
    assert ti["asr_ms"] >= 0
    assert ti["total_ms"] >= ti["upload_save_ms"] + ti["asr_ms"]


def test_http_root_lists_web_ui(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("web_ui") == "/ui/"
