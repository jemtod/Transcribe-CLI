"""Validated flat configuration; CLI > file > defaults."""
import ast
import tokenize
from pathlib import Path
from platformdirs import user_config_path
from .presets import quality, FORMATS

DEFAULTS = dict(default_quality='balanced', default_lang='id', default_output='both',
                model_override='', device='auto', compute_type='auto', max_line_chars=42,
                max_lines=2, vad=True, clean_text=False, word_timestamps=False, output_dir='')


def config_path():
    return user_config_path('transcribe-cli') / 'config.toml'


def _flat_toml(text):
    """Python 3.10 fallback, only the documented scalar keys (no dependencies)."""
    import io
    import tokenize
    result = {}
    for line in text.splitlines():
        # tokenize preserves # inside quoted strings, unlike split('#').
        tokens = list(tokenize.generate_tokens(io.StringIO(line).readline))
        comment = next((t.start[1] for t in tokens if t.type == tokenize.COMMENT), len(line))
        line = line[:comment].strip()
        if not line:
            continue
        key, sep, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not sep or key in result or not key.isidentifier():
            raise ValueError('TOML tidak valid; gunakan key = nilai, satu per baris.')
        if value in ('true', 'false'):
            parsed = value == 'true'
        elif value.startswith(('"', "'")):
            parsed = ast.literal_eval(value)
        else:
            parsed = int(value)
        result[key] = parsed
    return result


def load_config(path=None):
    path = Path(path) if path else config_path()
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding='utf-8')
        try:
            import tomllib
        except ImportError:
            return _flat_toml(text)
        return tomllib.loads(text)
    except (ValueError, SyntaxError, OSError, tokenize.TokenError) as exc:
        raise ValueError(f'Konfigurasi tidak valid ({path}): {exc}') from exc


def merge(file=None, cli=None):
    file, cli = file or {}, cli or {}
    unknown = set(file) - DEFAULTS.keys()
    if unknown:
        raise ValueError(f"Kunci config tidak dikenal: {', '.join(sorted(unknown))}")
    settings = {**DEFAULTS, **file, **{k: v for k, v in cli.items() if v is not None}}
    for key, default in DEFAULTS.items():
        if type(settings[key]) is not type(default):
            raise ValueError(f'Tipe nilai config {key} tidak sesuai.')
    settings['default_quality'] = quality(settings['default_quality'])
    for key, choices in [('default_lang', ('id', 'en', 'auto')), ('default_output', FORMATS),
                         ('device', ('auto', 'cpu', 'cuda')),
                         ('compute_type', ('auto', 'float16', 'float32', 'int8', 'int8_float16', 'int8_float32'))]:
        if settings[key] not in choices:
            raise ValueError(f'Nilai {key} tidak valid: {settings[key]}')
    if not 8 <= settings['max_line_chars'] <= 200 or not 1 <= settings['max_lines'] <= 4:
        raise ValueError('max_line_chars harus 8..200 dan max_lines harus 1..4.')
    settings['translate'] = bool(settings.get('translate', False))
    if settings['default_output'] == 'all':
        settings['word_timestamps'] = True
    return settings


def default_text():
    import json
    comments = {
        'default_quality': 'fast/cepat, balanced/seimbang, best/akurat',
        'default_lang': 'id, en, auto', 'default_output': 'text, subtitle, both, all',
        'model_override': 'Kosong = otomatis; nama model atau folder model lokal.',
        'device': 'auto, cpu, cuda', 'compute_type': 'auto = float16 CUDA, int8 CPU',
        'max_line_chars': 'Lebar baris subtitle; kata panjang ditolak, tidak dipotong.',
        'max_lines': 'Jumlah baris per blok; durasi maksimum tetap 7 detik.',
        'vad': 'Saring keheningan.', 'clean_text': 'Rapikan spasi dan kapital awal kalimat; tidak menulis ulang kata.',
        'word_timestamps': 'Otomatis true untuk output all (JSON).',
        'output_dir': 'Kosong = di samping media; string path untuk mengganti lokasi.',
    }
    return '\n'.join(f'# {comments[k]}\n{k} = {json.dumps(v)}\n' for k, v in DEFAULTS.items())
