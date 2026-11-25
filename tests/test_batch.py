from io import StringIO
import json
from rich.console import Console
from transcribe_cli.config import merge
from transcribe_cli.service import run_batch
from transcribe_cli.types import Transcript, Segment, Word


class FakeEngine:
    def __init__(self, *args):
        pass

    def transcribe(self, path, settings, terms='', progress=lambda t: None):
        progress(1)
        return Transcript('id', .95, 1, 'fake', settings, [Segment(0, 0, 1, terms or 'Halo.', words=[Word(0, 1, 'Halo.')])])


def setup(monkeypatch):
    monkeypatch.setattr('transcribe_cli.service.media.check_tools', lambda: None)
    monkeypatch.setattr('transcribe_cli.service.media.probe', lambda p: 1)
    monkeypatch.setattr('transcribe_cli.engine.hardware', lambda: ('cpu', 0))
    return Console(file=StringIO())


def test_single_all(tmp_path, monkeypatch):
    console = setup(monkeypatch)
    path = tmp_path / 'rapat.wav'
    path.write_bytes(b'input')
    assert run_batch(path, merge(cli={'default_output': 'all'}), console, factory=FakeEngine) == 0
    outputs = list((tmp_path / 'rapat_transkrip').iterdir())
    assert len(outputs) == 5
    assert json.loads(next(p for p in outputs if p.suffix == '.json').read_text())['schema_version'] == '1.0'
    assert path.read_bytes() == b'input'


def test_skip_and_confirm(tmp_path, monkeypatch):
    console = setup(monkeypatch)
    source = tmp_path / 'a.wav'
    source.touch()
    dest = tmp_path / 'a.txt'
    dest.write_text('lama')
    settings = merge(cli={'default_output': 'text'})
    assert run_batch(source, settings, console, factory=FakeEngine) == 0
    assert dest.read_text() == 'lama'
    assert 'dilewati' in console.file.getvalue()
    assert run_batch(source, settings, console, True, lambda *args: True, factory=FakeEngine) == 0
    assert dest.read_text() == 'Halo.\n'


def test_batch_continues(tmp_path, monkeypatch):
    console = setup(monkeypatch)
    (tmp_path / 'a.wav').touch()
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'b.wav').touch()
    def probe(path):
        if path.name == 'a.wav':
            raise ValueError('rusak')
        return 1
    monkeypatch.setattr('transcribe_cli.media.probe', probe)
    assert run_batch(tmp_path, merge(), console, factory=FakeEngine) == 1
    assert (tmp_path / 'sub' / 'b_transkrip' / 'b.txt').exists()


def test_cli(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from transcribe_cli.cli import app
    setup(monkeypatch)
    monkeypatch.setattr('transcribe_cli.engine.Engine', FakeEngine)
    monkeypatch.setattr('transcribe_cli.cli.load_config', lambda: {})
    path = tmp_path / 'a.wav'
    path.touch()
    result = CliRunner().invoke(app, [str(path), '-o', 'text', '-q', 'cepat'])
    assert result.exit_code == 0, result.output
    assert (tmp_path / 'a.txt').exists()
    assert CliRunner().invoke(app, ['--lang', 'bad', str(path)]).exit_code == 2
