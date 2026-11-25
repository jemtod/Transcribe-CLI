from io import StringIO
from pathlib import Path
import pytest
from rich.console import Console
from typer.testing import CliRunner
from transcribe_cli.cli import app
from transcribe_cli.config import merge
from transcribe_cli.wizard import clean_path, run_wizard


@pytest.mark.parametrize('raw,expected', [('  "a b.mp4"  ', 'a b.mp4'), ("'a b.wav' ", 'a b.wav'),
                                        (r'a\ b.mp4 ', 'a b.mp4'), (r'C:\Users\A\file.wav', r'C:\Users\A\file.wav')])
def test_drag_path(raw, expected):
    assert clean_path(raw) == expected


def test_wizard(tmp_path, monkeypatch):
    monkeypatch.setattr('transcribe_cli.wizard.check_tools', lambda: None)
    monkeypatch.setattr('transcribe_cli.wizard.probe', lambda p: 60)
    path = tmp_path / 'a b.wav'
    path.touch()
    answers = iter([f'"{path}" ', 'bad', '2', '4'])
    output = []
    result = run_wizard(merge(), output.append, lambda *a, **k: next(answers), lambda *a, **k: True)
    assert result[0] == path
    assert result[1]['default_output'] == 'all'
    assert result[1]['word_timestamps']
    assert 'Ringkasan' in output[-1]


def test_doctor_missing(monkeypatch):
    monkeypatch.setattr('transcribe_cli.commands.shutil.which', lambda name: None)
    result = CliRunner().invoke(app, ['doctor'])
    assert result.exit_code == 1
    for text in ('winget', 'choco', 'brew', 'apt', 'Python', 'Cache model'):
        assert text in result.output


def test_help_version_no_path():
    runner = CliRunner()
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert '--quality' in result.output
    assert '--device' not in result.output
    assert '--install-completion' not in result.output
    assert runner.invoke(app, ['--version']).exit_code == 0
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert 'PATH' in result.output


def test_config_models(tmp_path, monkeypatch):
    monkeypatch.setattr('transcribe_cli.commands.config_path', lambda: tmp_path / 'config.toml')
    monkeypatch.setattr('transcribe_cli.commands.load_config', lambda: {})
    runner = CliRunner()
    assert runner.invoke(app, ['config']).exit_code == 0
    assert runner.invoke(app, ['models']).exit_code == 0
    assert runner.invoke(app, ['models', 'bad']).exit_code == 2
    opened = []
    monkeypatch.setattr('transcribe_cli.commands.typer.launch', lambda path: opened.append(path))
    assert runner.invoke(app, ['config', 'edit']).exit_code == 0
    assert opened == [str(tmp_path / 'config.toml')]
    assert '# ' in (tmp_path / 'config.toml').read_text()
