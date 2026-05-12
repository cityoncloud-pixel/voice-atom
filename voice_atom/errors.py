"""Stable error codes (see project_control/.ggs/idea.md §9)."""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    MIC_NOT_FOUND = "MIC_NOT_FOUND"
    RECORDING_FAILED = "RECORDING_FAILED"
    AUDIO_SAVE_FAILED = "AUDIO_SAVE_FAILED"
    WHISPER_CPP_NOT_FOUND = "WHISPER_CPP_NOT_FOUND"
    WHISPER_MODEL_NOT_FOUND = "WHISPER_MODEL_NOT_FOUND"
    WHISPER_TRANSCRIBE_FAILED = "WHISPER_TRANSCRIBE_FAILED"
    API_KEY_MISSING = "API_KEY_MISSING"
    ASR_FAILED = "ASR_FAILED"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    INVALID_AUDIO_FILE = "INVALID_AUDIO_FILE"
    CONFIG_INVALID = "CONFIG_INVALID"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class VoiceAtomError(Exception):
    """Domain error with a stable machine code."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        recoverable: bool = True,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable
        self.details = details or {}
