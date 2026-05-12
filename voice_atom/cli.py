"""Typer CLI entrypoint."""

from __future__ import annotations

import json
from typing import Optional

import typer
import uvicorn

from voice_atom import __version__
from voice_atom.config import load_settings
from voice_atom.service import get_service

providers_app = typer.Typer(help="Inspect ASR providers.")
config_app = typer.Typer(help="Configuration helpers.")

app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
)
app.add_typer(providers_app, name="providers")
app.add_typer(config_app, name="config")


def _print_result(data: object, as_json: bool) -> None:
    if as_json:
        if hasattr(data, "model_dump"):
            typer.echo(json.dumps(data.model_dump(), ensure_ascii=False, indent=2))
        else:
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if hasattr(data, "ok") and getattr(data, "ok", False) is True:
            typer.echo(getattr(data, "text", ""))
        elif hasattr(data, "ok") and getattr(data, "ok", False) is False:
            err = getattr(data, "error", None)
            msg = err.message if err is not None else "error"
            typer.echo(msg, err=True)
            raise typer.Exit(code=2)
        else:
            typer.echo(str(data))


@app.command("record")
def record_cmd(
    seconds: int = typer.Option(8, "--seconds", "-s", min=1, max=600),
    as_json: bool = typer.Option(False, "--json", help="Print JSON envelope"),
) -> None:
    """Record from microphone for a fixed duration, then transcribe."""
    svc = get_service()
    res = svc.transcribe_from_mic(seconds)
    _print_result(res, as_json)


@app.command("transcribe-file")
def transcribe_file_cmd(
    audio_path: str = typer.Argument(..., metavar="PATH"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Transcribe a local WAV file."""
    svc = get_service()
    res = svc.transcribe_file(audio_path)
    _print_result(res, as_json)


@providers_app.command("list")
def providers_list(as_json: bool = typer.Option(True, "--json/--no-json", help="Output JSON")) -> None:
    svc = get_service()
    res = svc.get_providers()
    if as_json:
        typer.echo(json.dumps(res.model_dump(), ensure_ascii=False, indent=2))
    else:
        for p in res.providers:
            typer.echo(f"{p.name} priority={p.priority} local={p.local} enabled={p.enabled}")


@config_app.command("check")
def config_check(as_json: bool = typer.Option(True, "--json/--no-json")) -> None:
    svc = get_service()
    res = svc.check_config()
    if as_json:
        typer.echo(json.dumps(res.model_dump(), ensure_ascii=False, indent=2))
    else:
        typer.echo(f"ok={res.ok} provider={res.provider} http={res.host}:{res.port}")


@app.command("server")
def server_cmd(
    host: Optional[str] = typer.Option(None, "--host", help="Bind host (default from env)"),
    port: Optional[int] = typer.Option(None, "--port", help="Bind port (default from env)"),
) -> None:
    """Run the local HTTP API (FastAPI + Uvicorn)."""
    settings = load_settings()
    bind_host = host or settings.voice_atom_host
    bind_port = port or settings.voice_atom_port
    if bind_host in ("0.0.0.0", "::") and not settings.voice_atom_allow_public_bind:
        typer.echo(
            "Refusing to bind all interfaces without VOICE_ATOM_ALLOW_PUBLIC_BIND=1",
            err=True,
        )
        raise typer.Exit(code=1)
    uvicorn.run(
        "voice_atom.server:app",
        host=bind_host,
        port=bind_port,
        factory=False,
        log_level="info",
    )


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """voice-atom: atomic speech-to-text."""
    if version:
        return
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
