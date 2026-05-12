"""Pydantic models for API / JSON responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    recoverable: bool
    details: dict[str, Any] = Field(default_factory=dict)


class TranscriptionTiming(BaseModel):
    """Wall-clock stages in milliseconds (best-effort breakdown)."""

    upload_save_ms: int = 0
    audio_convert_ms: int = 0
    asr_ms: int = 0
    total_ms: int = 0


class TranscriptionSuccess(BaseModel):
    ok: Literal[True] = True
    text: str
    language: str | None = None
    provider: str
    audio_path: str | None = None
    duration_seconds: float | None = None
    created_at: str
    meta: dict[str, Any] = Field(default_factory=dict)
    timing: TranscriptionTiming | None = None


class TranscriptionFailure(BaseModel):
    ok: Literal[False] = False
    error: ErrorBody


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProviderStatusModel(BaseModel):
    name: str
    enabled: bool
    priority: int
    local: bool
    message: str | None = None


class ProviderListResponse(BaseModel):
    ok: Literal[True] = True
    default_provider: str
    providers: list[ProviderStatusModel]


class HealthResponse(BaseModel):
    ok: Literal[True] = True
    service: str = "voice-atom"
    version: str


class ConfigCheckItem(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ConfigCheckResponse(BaseModel):
    ok: bool
    items: list[ConfigCheckItem]
    host: str
    port: int
    provider: str
    doubao_api_key: str | None = None  # masked or None


class RecordRequest(BaseModel):
    seconds: int = Field(ge=1, le=600)


class TranscribeFileRequest(BaseModel):
    audio_path: str
