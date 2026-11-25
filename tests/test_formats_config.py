import json
import pytest
from transcribe_cli.config import merge, load_config, default_text, _flat_toml
from transcribe_cli.formatters import render
from transcribe_cli.types import Transcript, Segment, Word


def test_all_formats():
    data = Transcript('id', .8, 60, 'small', {'word_timestamps': True},
                      [Segment(0, 0, 1, 'Halo.', words=[Word(0, 1, 'Halo.')]), Segment(1, 31, 32, 'Lanjut.')])
    for ext in ('txt', 'srt', 'vtt', 'json', 'md'):
        assert 'Halo.' in render(data, ext)
    result = json.loads(render(data, 'json'))
    assert result['schema_version'] == '1.0'
    assert result['segments'][0]['words'][0]['word'] == 'Halo.'
    assert '[00:31]' in render(data, 'md')


def test_precedence():
    assert merge({'default_lang': 'en'}, {'default_lang': 'auto'})['default_lang'] == 'auto'
    assert merge({'default_lang': 'en'}, {'default_lang': None})['default_lang'] == 'en'
    assert merge()['default_lang'] == 'id'
    assert merge(cli={'default_output': 'all'})['word_timestamps']


def test_file(tmp_path):
    path = tmp_path / 'config.toml'
    path.write_text(default_text())
    assert merge(load_config(path)) == merge()
    assert merge(_flat_toml(default_text())) == merge()
    assert _flat_toml('output_dir = "a#b" # comment')['output_dir'] == 'a#b'


@pytest.mark.parametrize('file', [{'device': 'bad'}, {'vad': 'yes'}, {'unknown': 1}, {'max_lines': 0}])
def test_invalid(file):
    with pytest.raises(ValueError):
        merge(file)
