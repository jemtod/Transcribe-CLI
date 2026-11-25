"""Conservative transcript filters, pure and independent of the engine."""
from dataclasses import replace
import re


def cleanup(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    return re.sub(r'(^|[.!?]\s+)([^\W\d_])', lambda m: m[1] + m[2].upper(), text)


def process(segments, clean_text=False):
    filtered, dropped = [], 0
    i = 0
    while i < len(segments):
        current = segments[i]
        j = i + 1
        while j < len(segments) and segments[j].text.strip() == current.text.strip():
            j += 1
        run = segments[i:j]
        if len(run) >= 3:
            dropped += len(run) - 1
            run = run[:1]
        for segment in run:
            if segment.no_speech_prob > .9 and segment.avg_logprob < -1.0:
                dropped += 1
                continue
            filtered.append(replace(segment, text=cleanup(segment.text)) if clean_text else segment)
        i = j
    return filtered, dropped
