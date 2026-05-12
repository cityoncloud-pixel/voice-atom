"""ASR provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class ProviderStatus:
    available: bool
    message: str | None = None


@runtime_checkable
class ASRProvider(Protocol):
    name: str
    priority: int
    is_local: bool

    def check_available(self) -> ProviderStatus: ...

    def transcribe(self, audio_path: Path) -> str: ...
