"""Local HTTP API (FastAPI)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from voice_atom import __version__
from voice_atom.models import RecordRequest, TranscribeFileRequest
from voice_atom.service import get_service

app = FastAPI(title="voice-atom", version=__version__)
_svc = get_service()


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


@app.get("/providers")
def get_providers() -> dict:
    return _svc.get_providers().model_dump()


@app.get("/config/check")
def config_check() -> dict:
    return _svc.check_config().model_dump()


@app.get("/")
def root() -> dict:
    return {"ok": True, "service": "voice-atom", "docs": "/docs"}
