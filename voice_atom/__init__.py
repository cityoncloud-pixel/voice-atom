"""voice-atom public API."""

from __future__ import annotations

from voice_atom.config import Settings, load_settings
from voice_atom.models import (
    ConfigCheckResponse,
    ProviderListResponse,
    TranscriptionFailure,
    TranscriptionSuccess,
    TranscriptionTiming,
)
from voice_atom.service import VoiceAtomService, get_service

__version__ = "0.1.0"


def transcribe_from_mic(seconds: int, *, settings: Settings | None = None) -> TranscriptionSuccess | TranscriptionFailure:
    return get_service(settings).transcribe_from_mic(seconds)


def transcribe_file(audio_path: str, *, settings: Settings | None = None) -> TranscriptionSuccess | TranscriptionFailure:
    return get_service(settings).transcribe_file(audio_path)


def get_providers(*, settings: Settings | None = None) -> ProviderListResponse:
    return get_service(settings).get_providers()


def check_config(*, settings: Settings | None = None) -> ConfigCheckResponse:
    return get_service(settings).check_config()


__all__ = [
    "VoiceAtomService",
    "get_service",
    "load_settings",
    "Settings",
    "transcribe_from_mic",
    "transcribe_file",
    "get_providers",
    "check_config",
    "TranscriptionTiming",
    "__version__",
]
