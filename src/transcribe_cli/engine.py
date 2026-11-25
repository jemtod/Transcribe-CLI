"""Lazy faster-whisper boundary. Tests replace Engine, never download models."""
import os
from pathlib import Path
import subprocess
from platformdirs import user_cache_path
from .presets import MODELS
from .types import Segment, Transcript, Word

# Set before importing any of the lazy backend / Hub modules, including doctor.
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['DO_NOT_TRACK'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'


def cache_root():
    return user_cache_path('transcribe-cli') / 'models'


def hardware():
    try:
        import ctranslate2
        cuda = ctranslate2.get_cuda_device_count() > 0
    except (ImportError, RuntimeError):
        cuda = False
    vram = 0
    if cuda:
        try:
            proc = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                                  capture_output=True, text=True, timeout=5)
            vram = int(proc.stdout.splitlines()[0]) if proc.returncode == 0 else 0
        except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
            pass
    return ('cuda' if cuda else 'cpu'), vram


def model_path(model):
    path = Path(model).expanduser()
    if path.is_dir():
        return path
    root = cache_root() / model
    if _complete(root):
        return root
    # download_model's native Hub cache avoids deprecated local_dir arguments.
    snapshots = sorted(root.glob('models--*/snapshots/*')) if root.exists() else []
    return next((p for p in snapshots if _complete(p)), root)


def _complete(path):
    return all((path / name).is_file() for name in ('model.bin', 'config.json', 'tokenizer.json'))


def cached(model):
    path = model_path(model)
    return _complete(path)


class Engine:
    def __init__(self, model, device, compute_type, announce):
        # Must precede imports that may initialize hub clients. No telemetry.
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['DO_NOT_TRACK'] = '1'
        os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model
        path = model_path(model)
        if not cached(model):
            if model not in MODELS:
                raise ValueError('model_override harus nama model yang didukung atau folder model lokal lengkap.')
            announce(f"Model {model}, sekitar {MODELS[model][0]}: unduhan satu kali. "
                     'Hanya model yang diunduh; audio dan transkrip tetap di perangkat.')
            path = Path(download_model(model, cache_dir=str(path)))
            if not _complete(path):
                raise RuntimeError('Unduhan model belum lengkap (termasuk tokenizer.json). Coba ulang saat terhubung internet.')
        self.model = model
        self.backend = WhisperModel(str(path), device=device, compute_type=compute_type, local_files_only=True)

    def transcribe(self, path, settings, terms='', progress=lambda position: None):
        iterator, info = self.backend.transcribe(
            str(path), language=None if settings['default_lang'] == 'auto' else settings['default_lang'],
            task='translate' if settings['translate'] else 'transcribe', initial_prompt=terms or None,
            vad_filter=settings['vad'], word_timestamps=settings['word_timestamps'],
            condition_on_previous_text=False, no_speech_threshold=0.6, log_prob_threshold=-1.0,
            hallucination_silence_threshold=2.0)
        segments = []
        for s in iterator:
            segments.append(Segment(s.id, s.start, s.end, s.text.strip(), s.avg_logprob, s.no_speech_prob,
                                    [Word(w.start, w.end, w.word, w.probability) for w in s.words or []]))
            progress(s.end)
        return Transcript(info.language, info.language_probability, info.duration, self.model, dict(settings), segments)
