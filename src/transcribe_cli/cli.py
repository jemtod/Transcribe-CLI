"""Typer presentation and argument dispatch only."""
from pathlib import Path
from typing import Optional
import os
import sys
import typer
from rich.console import Console
from . import __version__
from .config import load_config, merge
from .service import glossary, run_batch
from .wizard import prompt_id, confirm_id

HELP = '''transcribe [PATH]

Transkripsi audio/video lokal. Tanpa PATH: panduan interaktif.

  -q, --quality   fast | balanced | best   (default: balanced)
                 Alias: cepat | seimbang | akurat
  -l, --lang      id | en | auto           (default: id)
  -o, --output    text | subtitle | both | all (default: both)
  -t, --terms     File glosarium (opsional)
  --translate     Terjemahkan ke Inggris
  --version       Tampilkan versi

Perintah: models, config [edit], doctor
Bantuan: --help
Pengaturan lain: transcribe config
'''


def show_help(value: bool):
    if value:
        typer.echo(HELP)
        raise typer.Exit()


def show_version(value: bool):
    if value:
        typer.echo(f'transcribe-cli {__version__}')
        raise typer.Exit()


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command(context_settings={'allow_extra_args': True, 'help_option_names': []})
def transcribe(ctx: typer.Context,
               path: Optional[str] = typer.Argument(None),
               quality: Optional[str] = typer.Option(None, '--quality', '-q'),
               lang: Optional[str] = typer.Option(None, '--lang', '-l'),
               output: Optional[str] = typer.Option(None, '--output', '-o'),
               terms: Optional[Path] = typer.Option(None, '--terms', '-t'),
               translate: Optional[bool] = typer.Option(None, '--translate'),
               version: bool = typer.Option(False, '--version', callback=show_version, is_eager=True),
               help_: bool = typer.Option(False, '--help', callback=show_help, is_eager=True, hidden=True)):
    console = Console(no_color='NO_COLOR' in os.environ, highlight=False)
    try:
        if path in ('models', 'config', 'doctor'):
            from .commands import dispatch
            raise typer.Exit(dispatch(path, ctx.args, console))
        if ctx.args:
            raise ValueError('Gunakan satu PATH. Bungkus path yang mengandung spasi dengan tanda kutip.')
        settings = merge(load_config(), dict(default_quality=quality, default_lang=lang,
                                             default_output=output, translate=translate))
        interactive = bool(sys.stdin.isatty() and console.is_terminal)
        if path is None:
            if not interactive:
                raise ValueError('Masukkan PATH, misalnya: transcribe rapat.mp4. Panduan membutuhkan terminal interaktif.')
            from .wizard import run_wizard
            choice = run_wizard(settings, lambda text: console.print(text, markup=False), prompt_id, confirm_id)
            if choice is None:
                raise typer.Exit(0)
            path, settings = choice
        text = glossary(terms)
        raise typer.Exit(run_batch(Path(path).expanduser().resolve(), settings, console, interactive,
                                   confirm_id, text))
    except typer.Exit:
        raise
    except (ValueError, OSError) as exc:
        console.print(f'Kesalahan: {exc}', markup=False)
        raise typer.Exit(2)
    except RuntimeError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1)
    except (KeyboardInterrupt, EOFError):
        console.print('Dihentikan.')
        raise typer.Exit(130)


def main():
    try:
        code = app(standalone_mode=False)
        raise SystemExit(code if isinstance(code, int) else 0)
    except typer.Exit as exc:
        raise SystemExit(exc.exit_code)
    except (KeyboardInterrupt, typer.Abort):
        typer.echo('Dihentikan.')
        raise SystemExit(130)
    except Exception:
        typer.echo('Argumen tidak valid. Jalankan transcribe --help untuk contoh pemakaian.', err=True)
        raise SystemExit(2)
