"""Scriptable wizard: prompt and output functions are injected."""
from pathlib import Path
import re
from .media import check_tools, discover, probe
from .presets import FORMATS


def clean_path(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    return re.sub(r'\\ ', ' ', text).rstrip()


def prompt_id(text, default=None):
    suffix = f' [{default}]' if default is not None else ''
    value = input(f'{text}{suffix}: ').strip()
    return str(default) if not value and default is not None else value


def confirm_id(text, default=False):
    while True:
        value = input(f'{text} [{"Y/n" if default else "y/N"}]: ').strip().lower()
        if not value:
            return default
        if value in ('y', 'ya', 'yes'):
            return True
        if value in ('n', 'tidak', 'no'):
            return False
        print('Jawab y (ya) atau n (tidak).')


def run_wizard(settings, emit, ask, confirm):
    check_tools()
    while True:
        raw = clean_path(ask('File atau folder (boleh seret ke terminal)'))
        try:
            path = Path(raw).expanduser().resolve()
            if not raw:
                raise ValueError('Path belum diisi.')
            files = discover(path)
            break
        except ValueError as exc:
            emit(str(exc))
    quality_choices = {'1': 'fast', '2': 'balanced', '3': 'best'}
    output_choices = {'1': 'text', '2': 'subtitle', '3': 'both', '4': 'all'}
    def choose(label, choices, default):
        while True:
            answer = str(ask(label, default=default)).strip()
            if answer in choices:
                return choices[answer]
            emit('Pilih nomor yang tercantum.')
    q_default = next(k for k, v in quality_choices.items() if v == settings['default_quality'])
    o_default = next(k for k, v in output_choices.items() if v == settings['default_output'])
    q = choose('Kualitas: [1] Cepat  [2] Seimbang  [3] Akurat', quality_choices, q_default)
    o = choose('Keluaran: [1] Teks saja  [2] Subtitle (.srt)  [3] Teks + subtitle  [4] Semua format', output_choices, o_default)
    duration, invalid = 0.0, 0
    for file in files:
        try:
            duration += probe(file)
        except ValueError as exc:
            invalid += 1
            emit(f'{file.name}: {exc}')
    # Deliberately a broad, labeled planning estimate, not a benchmark.
    emit(f'Ringkasan: {path}\n{len(files)} file | durasi terbaca {duration / 60:.1f} menit | '
         f'{invalid} tidak valid\nKualitas: {q} | keluaran: {", ".join(FORMATS[o])}\n'
         f'Estimasi waktu kasar: {duration / 60 * .2:.1f} sampai {duration / 60 * 10:.1f} menit; '
         'dapat lebih lama, bergantung perangkat/model. Unduhan belum termasuk.')
    if not confirm('Mulai?', default=True):
        return None
    from .config import merge
    # Revalidate the choice to enable word timestamps for all formats.
    translate = settings.get('translate', False)
    settings = dict(settings)
    settings.pop('translate', None)
    selected = merge(settings, {'default_quality': q, 'default_output': o})
    selected['translate'] = translate
    return path, selected
