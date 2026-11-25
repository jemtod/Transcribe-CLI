import pytest
from transcribe_cli.types import Segment, Transcript
from transcribe_cli.segmenter import subtitle_cues, wrap_words
from transcribe_cli.formatters import timestamp, subtitles


def test_punctuation():
    lines = wrap_words('Selamat pagi, teman-teman. Kita mulai rapat sekarang.', 28)
    assert all(len(line) <= 28 for line in lines)
    assert ' '.join(lines) == 'Selamat pagi, teman-teman. Kita mulai rapat sekarang.'


def test_bounds():
    cues = subtitle_cues([Segment(0, 0, 25, 'kata ' * 80), Segment(1, 24, 24.1, 'Akhir.')])
    for i, cue in enumerate(cues):
        assert 0.799 <= cue.end - cue.start <= 7.001
        assert len(cue.text.splitlines()) <= 2
        assert all(len(line) <= 42 for line in cue.text.splitlines())
        assert i == 0 or cue.start >= cues[i-1].end


def test_long_token():
    with pytest.raises(ValueError):
        wrap_words('a' * 43, 42)


@pytest.mark.parametrize('seconds,expected', [(3599.9996, '01:00:00,000'), (3600.001, '01:00:00,001'), (0, '00:00:00,000')])
def test_rounding(seconds, expected):
    assert timestamp(seconds) == expected


def test_formats():
    data = Transcript('id', .9, 1, 'fake', {}, [Segment(0, 0, 1, 'Halo.')])
    assert '00:00:00,000 --> 00:00:01,000' in subtitles(data)
    assert subtitles(data, True).startswith('WEBVTT\n\n1\n00:00:00.000')
