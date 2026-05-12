"""Central orchestration: all entrypoints must go through this module."""

from __future__ import annotations

import logging
import time
import wave
from pathlib import Path

from voice_atom.asr.doubao import DoubaoASRProvider
from voice_atom.asr.whisper_cpp import WhisperCppProvider
from voice_atom.config import Settings, load_settings
from voice_atom.errors import ErrorCode, VoiceAtomError
from voice_atom.models import (
    ConfigCheckItem,
    ConfigCheckResponse,
    ErrorBody,
    ProviderListResponse,
    ProviderStatusModel,
    TranscriptionFailure,
    TranscriptionSuccess,
    TranscriptionTiming,
    utc_now_iso,
)
from voice_atom.recorder import record_wav_seconds
from voice_atom.utils.audio import ensure_transcribable_file
from voice_atom.utils.paths import next_wav_path

_log = logging.getLogger(__name__)


def _wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:
        return None


def _mask_key(key: str) -> str | None:
    key = key.strip()
    if not key:
        return None
    if len(key) <= 8:
        return "***"
    return f"{key[:3]}***{key[-4:]}"


def _failure(exc: VoiceAtomError) -> TranscriptionFailure:
    return TranscriptionFailure(
        error=ErrorBody(
            code=exc.code.value,
            message=exc.message,
            recoverable=exc.recoverable,
            details=exc.details,
        )
    )


class VoiceAtomService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        recorder=None,
    ) -> None:
        self.settings = settings or load_settings()
        self._recorder = record_wav_seconds if recorder is None else recorder

    def _provider_name(self) -> str:
        return self.settings.voice_atom_provider.strip().lower() or "whisper_cpp"

    def _default_provider_label(self) -> str:
        n = self._provider_name()
        if n in ("whisper_cpp", "whisper-cpp"):
            return "whisper_cpp"
        if n == "doubao":
            return "doubao"
        return "whisper_cpp"

    def _make_active_provider(self):
        name = self._provider_name()
        if name in ("whisper_cpp", "whisper-cpp"):
            return WhisperCppProvider(self.settings)
        if name == "doubao":
            return DoubaoASRProvider(self.settings)
        raise VoiceAtomError(
            ErrorCode.CONFIG_INVALID,
            f"Unknown VOICE_ATOM_PROVIDER: {self.settings.voice_atom_provider}",
            details={"provider": self.settings.voice_atom_provider},
        )

    def transcribe_file(self, audio_path: str) -> TranscriptionSuccess | TranscriptionFailure:
        t0 = time.perf_counter()
        try:
            path = ensure_transcribable_file(audio_path)
            provider = self._make_active_provider()
            t_asr0 = time.perf_counter()
            text = provider.transcribe(path)
            t_asr1 = time.perf_counter()
            duration = _wav_duration(path)
            asr_ms = int((t_asr1 - t_asr0) * 1000)
            total_ms = int((time.perf_counter() - t0) * 1000)
            timing = TranscriptionTiming(
                upload_save_ms=0,
                audio_convert_ms=0,
                asr_ms=asr_ms,
                total_ms=total_ms,
            )
            _log.info("transcribe_file timing %s path=%s", timing.model_dump(), path)
            return TranscriptionSuccess(
                text=text,
                language=self.settings.voice_atom_language,
                provider=provider.name,
                audio_path=str(path),
                duration_seconds=duration,
                created_at=utc_now_iso(),
                meta={
                    "model": str(self.settings.voice_atom_whisper_model)
                    if provider.name == "whisper_cpp"
                    else self.settings.doubao_asr_model,
                    "source": "file",
                },
                timing=timing,
            )
        except VoiceAtomError as e:
            return _failure(e)
        except Exception as e:  # noqa: BLE001
            return _failure(
                VoiceAtomError(
                    ErrorCode.UNKNOWN_ERROR,
                    str(e),
                    recoverable=False,
                    details={"type": type(e).__name__},
                )
            )

    def transcribe_from_mic(self, seconds: int) -> TranscriptionSuccess | TranscriptionFailure:
        t0 = time.perf_counter()
        try:
            out_path = next_wav_path(self.settings.voice_atom_output_dir)
            duration = float(self._recorder(out_path, int(seconds)))
            provider = self._make_active_provider()
            t_asr0 = time.perf_counter()
            text = provider.transcribe(out_path)
            t_asr1 = time.perf_counter()
            asr_ms = int((t_asr1 - t_asr0) * 1000)
            total_ms = int((time.perf_counter() - t0) * 1000)
            timing = TranscriptionTiming(
                upload_save_ms=0,
                audio_convert_ms=0,
                asr_ms=asr_ms,
                total_ms=total_ms,
            )
            _log.info("transcribe_from_mic timing %s", timing.model_dump())
            return TranscriptionSuccess(
                text=text,
                language=self.settings.voice_atom_language,
                provider=provider.name,
                audio_path=str(out_path),
                duration_seconds=duration,
                created_at=utc_now_iso(),
                meta={
                    "model": str(self.settings.voice_atom_whisper_model)
                    if provider.name == "whisper_cpp"
                    else self.settings.doubao_asr_model,
                    "source": "mic",
                },
                timing=timing,
            )
        except VoiceAtomError as e:
            return _failure(e)
        except Exception as e:  # noqa: BLE001
            return _failure(
                VoiceAtomError(
                    ErrorCode.UNKNOWN_ERROR,
                    str(e),
                    recoverable=False,
                    details={"type": type(e).__name__},
                )
            )

    def get_providers(self) -> ProviderListResponse:
        default_provider = self._default_provider_label()
        whisper = WhisperCppProvider(self.settings)
        doubao = DoubaoASRProvider(self.settings)
        wst = whisper.check_available()
        dst = doubao.check_available()

        return ProviderListResponse(
            default_provider=default_provider,
            providers=[
                ProviderStatusModel(
                    name=whisper.name,
                    enabled=wst.available,
                    priority=whisper.priority,
                    local=whisper.is_local,
                    message=wst.message,
                ),
                ProviderStatusModel(
                    name=doubao.name,
                    enabled=dst.available,
                    priority=doubao.priority,
                    local=doubao.is_local,
                    message=dst.message,
                ),
            ],
        )

    def check_config(self) -> ConfigCheckResponse:
        items: list[ConfigCheckItem] = []
        active = self._provider_name()

        items.append(
            ConfigCheckItem(
                name="provider",
                ok=True,
                detail=f"active={active}",
            )
        )

        bin_ok = Path(self.settings.voice_atom_whisper_cpp_bin).expanduser().is_file()
        model_ok = Path(self.settings.voice_atom_whisper_model).expanduser().is_file()
        items.append(
            ConfigCheckItem(
                name="whisper_cpp_bin",
                ok=bin_ok,
                detail=str(self.settings.voice_atom_whisper_cpp_bin),
            )
        )
        items.append(
            ConfigCheckItem(
                name="whisper_model",
                ok=model_ok,
                detail=str(self.settings.voice_atom_whisper_model),
            )
        )

        out_dir = self.settings.voice_atom_output_dir.expanduser()
        out_ok = False
        detail = str(out_dir)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            probe = out_dir / ".voice_atom_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            out_ok = True
        except OSError:
            out_ok = False
        items.append(ConfigCheckItem(name="output_dir_writable", ok=out_ok, detail=detail))

        doubao = DoubaoASRProvider(self.settings)
        dst = doubao.check_available()
        items.append(
            ConfigCheckItem(
                name="doubao_config",
                ok=dst.available,
                detail=dst.message or "ok",
            )
        )

        items.append(
            ConfigCheckItem(
                name="http_bind",
                ok=True,
                detail=f"{self.settings.voice_atom_host}:{self.settings.voice_atom_port}",
            )
        )

        core_ok = out_ok
        if active in ("doubao",):
            overall = core_ok and dst.available
        else:
            overall = core_ok and bin_ok and model_ok

        return ConfigCheckResponse(
            ok=overall,
            items=items,
            host=self.settings.voice_atom_host,
            port=self.settings.voice_atom_port,
            provider=active,
            doubao_api_key=_mask_key(self.settings.doubao_api_key),
        )


def get_service(settings: Settings | None = None, **kwargs) -> VoiceAtomService:
    return VoiceAtomService(settings, **kwargs)
