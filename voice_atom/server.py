"""Local HTTP API (FastAPI)."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from voice_atom import __version__
from voice_atom.models import RecordRequest, TranscribeFileRequest
from voice_atom.service import get_service
from voice_atom.utils.audio import WHISPER_INPUT_SUFFIXES

app = FastAPI(title="voice-atom", version=__version__)
_svc = get_service()

_MAX_UPLOAD_BYTES = 30 * 1024 * 1024
_STATIC_DIR = Path(__file__).resolve().parent / "static"


def _ffmpeg_to_wav(src: Path, dst: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH (required to convert browser WebM to WAV)")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            str(dst),
        ],
        check=True,
        timeout=120,
    )


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "service": "voice-atom", "version": __version__}


@app.post("/record")
def post_record(body: RecordRequest) -> JSONResponse:
    res = _svc.transcribe_from_mic(body.seconds)
    return JSONResponse(content=res.model_dump())


@app.post("/transcribe-file")
def post_transcribe_file(body: TranscribeFileRequest) -> JSONResponse:
    res = _svc.transcribe_file(body.audio_path)
    return JSONResponse(content=res.model_dump())


@app.post("/transcribe-upload")
async def transcribe_upload(file: UploadFile = File(..., description="Browser-recorded audio (e.g. WebM)")) -> JSONResponse:
    """Save upload, convert to WAV if needed (ffmpeg), then run the same service path as transcribe-file."""
    raw = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(raw) > _MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "ok": False,
                "error": {
                    "code": "INVALID_AUDIO_FILE",
                    "message": f"Upload exceeds {_MAX_UPLOAD_BYTES} bytes",
                    "recoverable": True,
                    "details": {},
                },
            },
        )
    orig_name = file.filename or "clip.webm"
    ext = Path(orig_name).suffix.lower()
    if not ext or ext not in WHISPER_INPUT_SUFFIXES:
        ext = ".webm"

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = _svc.settings.voice_atom_output_dir.expanduser() / day / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex
    raw_path = base / f"{uid}{ext}"
    wav_path = base / f"{uid}.wav"
    raw_path.write_bytes(raw)
    work_path: Path | None = None
    try:
        if raw_path.suffix.lower() == ".wav":
            work_path = raw_path
        else:
            try:
                _ffmpeg_to_wav(raw_path, wav_path)
            except (subprocess.CalledProcessError, RuntimeError, subprocess.TimeoutExpired) as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "ok": False,
                        "error": {
                            "code": "WHISPER_TRANSCRIBE_FAILED",
                            "message": f"Audio conversion failed: {e}",
                            "recoverable": True,
                            "details": {"stage": "ffmpeg"},
                        },
                    },
                )
            work_path = wav_path
        res = _svc.transcribe_file(str(work_path))
        return JSONResponse(content=res.model_dump())
    finally:
        for p in (raw_path, wav_path):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass


@app.get("/providers")
def get_providers() -> dict:
    return _svc.get_providers().model_dump()


@app.get("/config/check")
def config_check() -> dict:
    return _svc.check_config().model_dump()


@app.get("/")
def root() -> dict:
    return {"ok": True, "service": "voice-atom", "docs": "/docs", "web_ui": "/ui/"}


if _STATIC_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")
