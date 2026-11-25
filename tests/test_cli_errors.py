from pathlib import Path
import shutil
import subprocess
import pytest
from typer.testing import CliRunner
from transcribe_cli.cli import app
from transcribe_cli.media import probe
from test_batch import setup, FakeEngine


def configure(monkeypatch):
    setup(monkeypatch)
    monkeypatch.setattr('transcribe_cli.engine.Engine', FakeEngine)
    monkeypatch.setattr('transcribe_cli.cli.load_config', lambda: {})


def test_unsupported(tmp_path, monkeypatch):
    configure(monkeypatch)
    source = tmp_path / 'notes.txt'
    source.touch()
    result = CliRunner().invoke(app, [str(source)])
    assert result.exit_code == 2
    assert 'Format tidak didukung' in result.output


def test_invalid_media_exit_one(tmp_path, monkeypatch):
    configure(monkeypatch)
    def bad(path):
        raise ValueError('Media tidak memiliki aliran audio.')
    monkeypatch.setattr('transcribe_cli.media.probe', bad)
    source = tmp_path / 'silent.mp4'
    source.touch()
    result = CliRunner().invoke(app, [str(source)])
    assert result.exit_code == 1
    assert 'tidak memiliki aliran audio' in result.output


def test_glossary_and_no_color(tmp_path, monkeypatch):
    configure(monkeypatch)
    source = tmp_path / 'a.wav'
    source.touch()
    terms = tmp_path / 'terms.txt'
    terms.write_text('BPJS\n\nPrambanan\n')
    result = CliRunner().invoke(app, [str(source), '-t', str(terms), '-o', 'text'], env={'NO_COLOR': '1'})
    assert result.exit_code == 0
    assert '\x1b' not in result.output
    assert (tmp_path / 'a.txt').read_text() == 'BPJS, Prambanan\n'


def test_low_confidence(tmp_path, monkeypatch):
    configure(monkeypatch)
    class LowConfidence(FakeEngine):
        def transcribe(self, *args):
            data = super().transcribe(*args)
            data.language_probability = .4
            return data
    monkeypatch.setattr('transcribe_cli.engine.Engine', LowConfidence)
    source = tmp_path / 'a.wav'
    source.touch()
    result = CliRunner().invoke(app, [str(source), '-l', 'auto'])
    assert result.exit_code == 0
    assert 'Keyakinan bahasa rendah' in result.output


def test_cli_interrupt(tmp_path, monkeypatch):
    configure(monkeypatch)
    class Interrupted(FakeEngine):
        def transcribe(self, *args):
            raise KeyboardInterrupt
    monkeypatch.setattr('transcribe_cli.engine.Engine', Interrupted)
    source = tmp_path / 'a.wav'
    source.touch()
    assert CliRunner().invoke(app, [str(source)]).exit_code == 130


def test_real_no_audio(tmp_path):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('FFmpeg tidak tersedia')
    path = tmp_path / 'video.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=size=16x16:duration=0.1',
                    '-an', '-c:v', 'mpeg4', str(path)], check=True)
    with pytest.raises(ValueError, match='tidak memiliki aliran audio'):
        probe(path)


@pytest.mark.slow
def test_local_tiny_integration(tmp_path):
    from transcribe_cli.engine import cached, Engine
    from transcribe_cli.config import merge
    if not cached('tiny'):
        pytest.skip('Siapkan model tiny di cache; tes tidak mengunduh model.')
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg tidak tersedia')
    source = tmp_path / 'nada.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=duration=1', str(source)], check=True)
    worker = Engine('tiny', 'cpu', 'int8', lambda text: pytest.fail('Model seharusnya sudah lokal'))
    data = worker.transcribe(source, merge())
    assert data.model == 'tiny'
    assert data.duration > 0
