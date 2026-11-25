from pathlib import Path
import subprocess
import shutil
import pytest
from transcribe_cli.media import discover, probe
from transcribe_cli.presets import quality, model_for


def test_discovery(tmp_path):
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'test.MP3').touch()
    assert len(discover(tmp_path)) == 1
    with pytest.raises(ValueError):
        discover(tmp_path / 'missing.wav')


def test_quality():
    assert quality('seimbang') == 'balanced'
    assert model_for('cepat') == 'base'
    assert model_for('best') == 'turbo'


@pytest.fixture
def audio(tmp_path):
    if not shutil.which('ffmpeg'):
        pytest.skip('ffmpeg tidak tersedia')
    path = tmp_path / 'nada.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', str(path)], check=True)
    return path


def test_probe(audio):
    assert 0.9 < probe(audio) < 1.1


def test_corrupt(tmp_path):
    if not shutil.which('ffprobe'):
        pytest.skip('ffprobe tidak tersedia')
    path = tmp_path / 'bad.mp3'
    path.write_text('bad')
    with pytest.raises(ValueError, match='rusak'):
        probe(path)


def test_fake_engine_txt(audio):
    from transcribe_cli.types import Transcript, Segment
    from transcribe_cli.formatters import txt

    class FakeEngine:
        def transcribe(self, path):
            return Transcript('id', 0.99, probe(path), 'fake', {}, [Segment(0, 0, 1, 'Selamat pagi.')])

    assert txt(FakeEngine().transcribe(audio)) == 'Selamat pagi.\n'
