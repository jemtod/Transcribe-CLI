"""Application orchestration, independent of Typer."""
from dataclasses import dataclass, field
from pathlib import Path
import time
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from . import engine, media
from .formatters import render
from .output import output_paths, write_outputs
from .presets import FORMATS, model_for
from .postprocess import process


@dataclass
class FileResult:
    path: Path
    duration: float = 0
    status: str = 'gagal'
    elapsed: float = 0
    outputs: list[Path] = field(default_factory=list)


def glossary(path):
    if not path:
        return ''
    return ', '.join(line.strip() for line in Path(path).expanduser().read_text(encoding='utf-8-sig').splitlines() if line.strip())


def run_batch(path, settings, console, interactive=False, confirm=lambda text, default=False: False, terms='', factory=None):
    media.check_tools()
    files = media.discover(path)
    factory = factory or engine.Engine
    detected, vram = engine.hardware()
    device = detected if settings['device'] == 'auto' else settings['device']
    compute = settings['compute_type']
    if compute == 'auto':
        compute = 'float16' if device == 'cuda' else 'int8'
    settings = {**settings, 'device': device, 'compute_type': compute}
    if settings['default_quality'] == 'best' and device == 'cpu':
        console.print('Kualitas akurat di CPU dapat memakan waktu lama.')
        if interactive and confirm('Beralih ke kualitas seimbang?', True):
            settings['default_quality'] = 'balanced'
    model = settings['model_override'] or model_for(settings['default_quality'], device, vram, settings['translate'])
    if settings['translate'] and model in ('turbo', 'large-v3-turbo'):
        raise ValueError('Model turbo tidak mendukung terjemahan dengan baik; gunakan model_override = "large-v3".')
    extensions = FORMATS[settings['default_output']]
    results, worker = [], None
    try:
        for path in files:
            started = time.monotonic()
            result = FileResult(path)
            results.append(result)
            try:
                result.duration = media.probe(path)
                destinations = output_paths(path, extensions, settings['output_dir'])
                allowed, approved = [], []
                for dest in destinations:
                    if dest.exists() or dest.is_symlink():
                        if interactive and confirm(f'{dest}: File sudah ada, timpa?', False):
                            approved.append(dest)
                        else:
                            console.print(f'{dest}: dilewati (file sudah ada).', markup=False)
                            continue
                    allowed.append(dest)
                if not allowed:
                    result.status = 'dilewati'
                    continue
                # Confirmation time is user time, not processing time.
                started = time.monotonic()
                if worker is None:
                    console.print(f'Memuat model {model} ({device}, {compute})...', markup=False)
                    worker = factory(model, device, compute, lambda msg: console.print(msg, markup=False))
                console.print(f'Memproses: {path}', markup=False)
                if console.is_terminal:
                    with Progress(TextColumn('{task.description}'), BarColumn(),
                                  TextColumn('{task.completed:.0f}/{task.total:.0f} dtk'),
                                  TimeElapsedColumn(), TimeRemainingColumn(), console=console) as progress:
                        task = progress.add_task(path.name, total=result.duration)
                        data = worker.transcribe(path, settings, terms,
                                                 lambda t: progress.update(task, completed=min(t, result.duration)))
                else:
                    data = worker.transcribe(path, settings, terms)
                data.segments, dropped = process(data.segments, settings['clean_text'])
                payloads = [(dest, render(data, dest.suffix[1:], path.stem)) for dest in allowed]
                result.outputs = write_outputs(payloads, approved)
                result.status = 'selesai'
                result.elapsed = time.monotonic() - started
                if settings['default_lang'] == 'auto':
                    console.print(f'Bahasa terdeteksi: {data.language} ({data.language_probability:.0%})')
                    if data.language_probability < .6:
                        console.print('Keyakinan bahasa rendah; periksa hasil atau atur --lang id/en.')
                summary = (f'Durasi {result.duration:.1f} dtk | Proses {result.elapsed:.1f} dtk | '
                           f'RTF {result.elapsed / result.duration:.2f}\n'
                           f'Bahasa {data.language} ({data.language_probability:.0%}) | {len(data.segments)} segmen | '
                           f'{dropped} segmen dibuang\n'
                           + '\n'.join(str(p) for p in result.outputs))
                if not data.segments:
                    console.print('Tidak ada ucapan terdeteksi. Keluaran kosong telah ditulis.')
                if console.is_terminal:
                    from rich.text import Text
                    console.print(Panel(Text(summary), title='Selesai', border_style='green'))
                else:
                    console.print(summary, markup=False)
            except Exception as exc:
                console.print(f'{path}: gagal: {exc}', markup=False)
            finally:
                result.elapsed = time.monotonic() - started
    except KeyboardInterrupt:
        console.print(f'Dihentikan. Selesai: {sum(r.status == "selesai" for r in results)} file. Keluaran parsial dibersihkan.')
        return 130
    if len(files) > 1:
        table = Table('File', 'Durasi', 'Status', 'Waktu', 'Keluaran', title='Ringkasan batch')
        for r in results:
            table.add_row(str(r.path), f'{r.duration:.1f}s', r.status, f'{r.elapsed:.1f}s', ', '.join(str(p) for p in r.outputs))
        if console.is_terminal:
            console.print(table)
        else:
            for r in results:
                console.print(f'{r.path}: {r.status} | {r.duration:.1f}s | {r.elapsed:.1f}s | {len(r.outputs)} keluaran', markup=False)
        console.print(f'Total: {len(results)} file; {sum(r.status == "selesai" for r in results)} selesai; '
                      f'{sum(r.status == "gagal" for r in results)} gagal; '
                      f'{sum(r.status == "dilewati" for r in results)} dilewati. '
                      f'Durasi {sum(r.duration for r in results):.1f}s; proses {sum(r.elapsed for r in results):.1f}s.')
    return int(any(r.status == 'gagal' for r in results))
