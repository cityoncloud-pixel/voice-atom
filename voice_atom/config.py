"""Load settings from environment and optional `.env` file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    voice_atom_provider: str = Field(default="whisper_cpp")
    voice_atom_output_dir: Path = Field(default=Path("./runs"))
    voice_atom_default_seconds: int = Field(default=10)

    voice_atom_whisper_cpp_bin: Path = Field(default=Path("./bin/whisper-cli"))
    voice_atom_whisper_model: Path = Field(default=Path("./models/ggml-small.bin"))
    voice_atom_language: str = Field(default="zh")
    voice_atom_threads: int = Field(default=4)
    voice_atom_whisper_extra_args: str = Field(default="")

    voice_atom_host: str = Field(default="127.0.0.1")
    voice_atom_port: int = Field(default=17860)
    voice_atom_allow_public_bind: bool = Field(default=False)

    doubao_api_key: str = Field(default="")
    doubao_asr_model: str = Field(default="")
    doubao_asr_upload_url: str = Field(default="")


def load_settings() -> Settings:
    return Settings()
