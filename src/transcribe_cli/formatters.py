"""Pure formatters: plain dataclasses in, strings out."""
from dataclasses import asdict
import json
from datetime import date
from .types import Transcript
from .segmenter import subtitle_cues


def paragraphs(segments, pause=1.5):
    result = []
    previous = None
    for s in segments:
        if previous is None or s.start - previous.end >= pause:
            result.append([s])
        else:
            result[-1].append(s)
        previous = s
    return result


def txt(data: Transcript):
    return '\n\n'.join(' '.join(s.text.strip() for s in group) for group in paragraphs(data.segments)) + '\n'


def timestamp(seconds, separator=','):
    ms = max(0, int(seconds * 1000 + 0.5))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{ms:03}'


def subtitles(data, vtt=False):
    cues = subtitle_cues(data.segments, data.settings.get('max_line_chars', 42), data.settings.get('max_lines', 2))
    sep = '.' if vtt else ','
    blocks = [f'{i}\n{timestamp(c.start, sep)} --> {timestamp(c.end, sep)}\n{c.text}'
              for i, c in enumerate(cues, 1)]
    return ('WEBVTT\n\n' if vtt else '') + '\n\n'.join(blocks) + '\n'


def json_text(data):
    payload = asdict(data)
    payload['schema_version'] = '1.0'
    if not data.settings.get('word_timestamps', False):
        for segment in payload['segments']:
            segment.pop('words', None)
    return json.dumps(payload, ensure_ascii=False, indent=2) + '\n'


def markdown(data, title, today=None):
    lines = [f'# {title}', '', f'Tanggal: {today or date.today().isoformat()}',
             f'Durasi: {data.duration:.1f} detik', f'Model: {data.model}', f'Bahasa: {data.language}', '']
    last_marker = -30.0
    for group in paragraphs(data.segments):
        parts = []
        for segment in group:
            if segment.start - last_marker >= 30:
                t = int(segment.start)
                parts.append(f'[{t // 60:02}:{t % 60:02}]')
                last_marker = segment.start
            parts.append(segment.text.strip())
        lines.extend([' '.join(parts), ''])
    return '\n'.join(lines)


def render(data, extension, title='Transkrip'):
    if extension == 'txt':
        return txt(data)
    if extension in ('srt', 'vtt'):
        return subtitles(data, extension == 'vtt')
    if extension == 'json':
        return json_text(data)
    if extension == 'md':
        return markdown(data, title)
    raise ValueError(f'Format keluaran tidak dikenal: {extension}')
