"""Administrative command actions."""
import sys
import shutil
import typer
from rich.table import Table
from . import engine, media
from .config import config_path, load_config, merge, default_text
from .presets import MODELS


def dispatch(command, args, console):
    if command != 'config' and args or command == 'config' and args not in ([], ['edit']):
        raise ValueError('Perintah tersedia: models, config, config edit, doctor.')
    if command == 'models':
        table = Table('Model', 'Unduhan ~', 'RAM ~', 'Kecepatan', 'Catatan', 'Tersimpan')
        for name, details in MODELS.items():
            row = (name, *details, 'ya' if engine.cached(name) else 'belum')
            if console.is_terminal:
                table.add_row(*row)
            else:
                console.print(' | '.join(row), markup=False)
        if console.is_terminal:
            console.print(table)
        console.print('Ukuran dan RAM adalah perkiraan; kebutuhan aktual bergantung compute_type dan durasi.')
        return 0
    if command == 'config':
        path = config_path()
        console.print(f'Konfigurasi: {path}', markup=False)
        if args:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with path.open('x', encoding='utf-8') as stream:
                    stream.write(default_text())
            except FileExistsError:
                pass
            typer.launch(str(path))
        else:
            for key, value in merge(load_config()).items():
                console.print(f'{key} = {value!r}', markup=False)
        return 0
    failures = 0
    console.print(f'Python {sys.version.split()[0]}: ' + ('OK' if sys.version_info >= (3, 10) else 'pasang Python 3.10+'))
    failures += int(sys.version_info < (3, 10))
    for name in ('ffmpeg', 'ffprobe'):
        location = shutil.which(name)
        console.print(f'{name}: {location or "tidak ditemukan"}', markup=False)
        failures += int(not location)
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        console.print(media.INSTALL)
    try:
        import faster_whisper  # noqa: F401
        console.print('faster-whisper: tersedia')
    except ImportError:
        console.print('faster-whisper: belum tersedia. Pasang ulang: pipx install --force .')
        failures += 1
    device, vram = engine.hardware()
    console.print(f'GPU CUDA: {"tersedia" if device == "cuda" else "tidak tersedia; CPU akan digunakan"}; VRAM bebas {vram} MB')
    console.print('Untuk GPU NVIDIA, pastikan driver serta CUDA/cuDNN yang sesuai CTranslate2 terpasang.')
    root = engine.cache_root()
    console.print(f'Cache model: {root}', markup=False)
    downloaded = [name for name in MODELS if engine.cached(name)]
    console.print('Model tersimpan: ' + (', '.join(downloaded) or 'belum ada; model diunduh saat transkripsi pertama'))
    if root.exists() and not root.is_dir():
        console.print('Cache bukan folder. Pindahkan file tersebut lalu coba lagi.')
        failures += 1
    return int(failures > 0)
