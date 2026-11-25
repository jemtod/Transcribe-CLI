from transcribe_cli.types import Segment
from transcribe_cli.postprocess import process, cleanup
from transcribe_cli.output import write_outputs
from transcribe_cli.service import run_batch
from transcribe_cli.config import merge
from test_batch import setup
import pytest


def test_filters():
    segments = [Segment(i, i, i+1, 'Terima kasih.') for i in range(4)]
    segments.extend([Segment(4, 4, 5, 'musik', -2, .99), Segment(5, 5, 6, 'wajar', -2, .1)])
    result, dropped = process(segments)
    assert dropped == 4
    assert [s.text for s in result] == ['Terima kasih.', 'wajar']
    assert len(segments) == 6


def test_cleanup():
    assert cleanup('  halo   BCA , teman . sampai jumpa! ') == 'Halo BCA, teman. Sampai jumpa!'
    segments = [Segment(0, 0, 1, 'halo')]
    assert process(segments)[0][0].text == 'halo'
    assert process(segments, True)[0][0].text == 'Halo'
    assert segments[0].text == 'halo'


def test_interrupt_engine(tmp_path, monkeypatch):
    console = setup(monkeypatch)
    source = tmp_path / 'a.wav'
    source.touch()
    class Interrupted:
        def __init__(self, *args):
            pass
        def transcribe(self, *args):
            raise KeyboardInterrupt
    assert run_batch(source, merge(), console, factory=Interrupted) == 130
    assert not list(tmp_path.rglob('*.txt'))


def test_write_rollback(tmp_path, monkeypatch):
    import os
    real = os.link
    def fail_on_second(src, dest):
        if dest.name == 'b.txt':
            raise KeyboardInterrupt
        real(src, dest)
    monkeypatch.setattr(os, 'link', fail_on_second)
    with pytest.raises(KeyboardInterrupt):
        write_outputs([(tmp_path / 'a.txt', 'a'), (tmp_path / 'b.txt', 'b')])
    assert not list(tmp_path.iterdir())


def test_race_does_not_overwrite(tmp_path):
    target = tmp_path / 'a.txt'
    target.write_text('lama')
    with pytest.raises(FileExistsError):
        write_outputs([(target, 'baru')])
    assert target.read_text() == 'lama'
