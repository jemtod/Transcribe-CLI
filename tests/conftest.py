"""No network connections are allowed in any test, including slow tests."""
import socket
import pytest


@pytest.fixture(autouse=True)
def offline_tests(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError('Jaringan dilarang dalam tes; gunakan fake atau model cache lokal.')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
