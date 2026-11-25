"""Discovery and validation only; never decodes to temporary audio."""
import json
import math
from pathlib import Path
import shutil
import subprocess

SUPPORTED = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.opus', '.flac', '.mp4', '.mkv', '.mov', '.webm', '.avi'}
INSTALL = ('Pasang FFmpeg lalu buka terminal baru:\n'
           'Windows: winget install Gyan.FFmpeg atau choco install ffmpeg\n'
           'macOS: brew install ffmpeg\nLinux: sudo apt install ffmpeg')


def check_tools():
    missing = [name for name in ('ffmpeg', 'ffprobe') if not shutil.which(name)]
    if missing:
        raise RuntimeError(f"Tidak ditemukan: {', '.join(missing)}.\n{INSTALL}")


def discover(path: Path) -> list[Path]:
    if not path.exists():
        raise ValueError(f'Path tidak ditemukan: {path}')
    if path.is_dir():
        files = sorted(p for p in path.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED)
        if not files:
            raise ValueError('Folder tidak berisi media yang didukung.')
        return files
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f'Format tidak didukung: {path.suffix}')
    return [path]


def probe(path: Path) -> float:
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                                 '-of', 'json', str(path.resolve())], capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError('Media rusak atau tidak dapat dibaca oleh ffprobe.')
        data = json.loads(result.stdout)
        audio = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
        if not audio:
            raise ValueError('Media tidak memiliki aliran audio.')
        duration = float(data.get('format', {}).get('duration') or audio[0].get('duration') or 0)
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('Durasi audio tidak dapat ditentukan.')
        return duration
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise ValueError(f'Gagal memeriksa media: {exc}') from exc
