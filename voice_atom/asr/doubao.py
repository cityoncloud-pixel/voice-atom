"""Doubao / Volcengine ASR via HTTPS upload (configurable endpoint)."""

from __future__ import annotations

from pathlib import Path

import httpx

from voice_atom.asr.base import ProviderStatus
from voice_atom.config import Settings
from voice_atom.errors import ErrorCode, VoiceAtomError


class DoubaoASRProvider:
    name = "doubao"
    priority = 2
    is_local = False

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check_available(self) -> ProviderStatus:
        if not self._settings.doubao_api_key.strip():
            return ProviderStatus(False, "DOUBAO_API_KEY is not set")
        if not self._settings.doubao_asr_upload_url.strip():
            return ProviderStatus(False, "DOUBAO_ASR_UPLOAD_URL is not set")
        if not self._settings.doubao_asr_model.strip():
            return ProviderStatus(False, "DOUBAO_ASR_MODEL is not set")
        return ProviderStatus(True, None)

    def transcribe(self, audio_path: Path) -> str:
        if not self._settings.doubao_api_key.strip():
            raise VoiceAtomError(
                ErrorCode.API_KEY_MISSING,
                "DOUBAO_API_KEY is required for doubao provider",
                details={},
            )
        if not self._settings.doubao_asr_upload_url.strip():
            raise VoiceAtomError(
                ErrorCode.CONFIG_INVALID,
                "DOUBAO_ASR_UPLOAD_URL must be configured for upload mode",
                details={},
            )
        if not self._settings.doubao_asr_model.strip():
            raise VoiceAtomError(
                ErrorCode.CONFIG_INVALID,
                "DOUBAO_ASR_MODEL must be configured",
                details={},
            )

        url = self._settings.doubao_asr_upload_url.strip()
        audio_path = audio_path.expanduser().resolve()

        headers = {
            "Authorization": f"Bearer {self._settings.doubao_api_key}",
        }

        try:
            with audio_path.open("rb") as f:
                files = {"file": (audio_path.name, f, "audio/wav")}
                data = {"model": self._settings.doubao_asr_model}
                with httpx.Client(timeout=120.0) as client:
                    resp = client.post(url, headers=headers, files=files, data=data)
        except httpx.TimeoutException as e:
            raise VoiceAtomError(
                ErrorCode.PROVIDER_TIMEOUT,
                "Doubao ASR request timed out",
                details={},
            ) from e
        except OSError as e:
            raise VoiceAtomError(
                ErrorCode.ASR_FAILED,
                f"failed to read audio or connect: {e}",
                details={},
            ) from e

        if resp.status_code >= 400:
            raise VoiceAtomError(
                ErrorCode.ASR_FAILED,
                "Doubao ASR HTTP error",
                recoverable=True,
                details={"status_code": resp.status_code, "body_tail": resp.text[-2000:]},
            )

        # Accept either plain text or JSON {"text": "..."} — product-specific parsers can evolve.
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype.lower():
            payload = resp.json()
            if isinstance(payload, dict) and "text" in payload:
                return str(payload["text"]).strip()
            if isinstance(payload, dict) and "result" in payload:
                return str(payload["result"]).strip()
            raise VoiceAtomError(
                ErrorCode.ASR_FAILED,
                "Unexpected JSON shape from Doubao ASR endpoint",
                recoverable=True,
                details={"keys": list(payload.keys()) if isinstance(payload, dict) else []},
            )

        return resp.text.strip()
