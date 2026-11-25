from types import SimpleNamespace
import sys
import types
from transcribe_cli import engine
from transcribe_cli.config import merge


def test_model_download_notice_and_local_reuse(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, 'cache_root', lambda: tmp_path)
    events = []
    module = types.ModuleType('faster_whisper')
    utils = types.ModuleType('faster_whisper.utils')

    def download(model, **kwargs):
        events.append(('download', model, kwargs))
        path = tmp_path / model / 'models--fake' / 'snapshots' / 'revision'
        path.mkdir(parents=True)
        for name in ('model.bin', 'config.json', 'tokenizer.json'):
            (path / name).touch()
        return str(path)

    class Backend:
        def __init__(self, path, **kwargs):
            events.append(('init', path, kwargs))
        def transcribe(self, path, **kwargs):
            events.append(('transcribe', path, kwargs))
            segment = SimpleNamespace(id=0, start=0, end=1, text=' Halo. ', avg_logprob=-.2,
                                      no_speech_prob=.01, words=[SimpleNamespace(start=0, end=1, word='Halo.', probability=.9)])
            return iter([segment]), SimpleNamespace(language='id', language_probability=.8, duration=1)

    module.WhisperModel, utils.download_model = Backend, download
    monkeypatch.setitem(sys.modules, 'faster_whisper', module)
    monkeypatch.setitem(sys.modules, 'faster_whisper.utils', utils)
    worker = engine.Engine('small', 'cpu', 'int8', lambda text: events.append(('notice', text)))
    assert events[0][0] == 'notice'
    assert 'unduhan satu kali' in events[0][1]
    assert 'small' in events[0][1] and '485 MB' in events[0][1]
    assert events[1][0] == 'download'
    assert 'cache_dir' in events[1][2] and 'output_dir' not in events[1][2]
    assert events[2][2]['local_files_only'] is True
    worker.transcribe(tmp_path / 'a.wav', merge(cli={'default_lang': 'auto', 'default_output': 'all', 'translate': True}), 'BPJS')
    args = events[-1][2]
    assert args['language'] is None
    assert args['initial_prompt'] == 'BPJS'
    assert args['task'] == 'translate'
    assert args['word_timestamps'] is True
    assert args['vad_filter'] is True
    events.clear()
    assert engine.cached('small')
    engine.Engine('small', 'cpu', 'int8', lambda text: events.append(('notice', text)))
    assert [e[0] for e in events] == ['init']


def test_best_mapping():
    from transcribe_cli.presets import model_for, FORMATS
    assert model_for('akurat', 'cuda', 12000) == 'large-v3'
    assert model_for('best', 'cuda', 4000) == 'turbo'
    assert model_for('best', translate=True) == 'large-v3'
    assert FORMATS['all'] == ('txt', 'srt', 'vtt', 'json', 'md')
