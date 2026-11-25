"""Subtitle layout and timing; no I/O or engine imports."""
import math
from .types import Cue


def wrap_words(text, width):
    """Keep words intact. An unbreakable token wider than width is rejected."""
    words = text.split()
    if any(len(w) > width for w in words):
        raise ValueError(f'Kata lebih panjang dari {width} karakter; naikkan max_line_chars di config.')
    lines = []
    while words:
        count, length = 0, 0
        for word in words:
            added = len(word) + bool(count)
            if length + added > width:
                break
            length += added
            count += 1
        # Prefer punctuation when it does not make a very short line.
        choices = [i + 1 for i, w in enumerate(words[:count]) if w.endswith(('.', ',', ';', ':', '!', '?'))]
        if choices and len(' '.join(words[:choices[-1]])) >= width * 0.6:
            count = choices[-1]
        lines.append(' '.join(words[:count]))
        words = words[count:]
    return lines


def subtitle_cues(segments, max_line_chars=42, max_lines=2, max_duration=7.0, min_duration=0.8):
    if max_line_chars < 1 or max_lines < 1 or min_duration <= 0 or max_duration < min_duration:
        raise ValueError('Pengaturan subtitle tidak valid.')
    cues = []
    cursor = 0.0
    for segment in segments:
        if not segment.text.strip():
            continue
        start = max(cursor, segment.start, 0.0)
        duration = max(min_duration, segment.end - start)
        lines = wrap_words(segment.text, max_line_chars)
        # Split by both reading capacity and duration. Reserve at least one word per cue.
        count = max(math.ceil(len(lines) / max_lines), math.ceil(duration / max_duration))
        words = segment.text.split()
        count = min(count, len(words))
        groups = []
        remaining = words
        for index in range(count):
            take = math.ceil(len(remaining) / (count - index))
            chunk = ' '.join(remaining[:take])
            remaining = remaining[take:]
            wrapped = wrap_words(chunk, max_line_chars)
            groups.extend('\n'.join(wrapped[i:i + max_lines]) for i in range(0, len(wrapped), max_lines))
        # Long silences need no caption. Very dense speech extends rather than overlapping.
        step = min(max_duration, max(min_duration, duration / len(groups)))
        for group in groups:
            end = start + step
            cues.append(Cue(round(start, 3), round(end, 3), group))
            start = end
        cursor = start
    return cues
