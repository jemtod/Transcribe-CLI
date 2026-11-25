"""Output planning and staged, exclusive writes."""
import os
from pathlib import Path
import tempfile


def output_paths(source, extensions, output_dir=''):
    parent = Path(output_dir).expanduser() if output_dir else source.parent
    if len(extensions) > 1:
        parent = parent / f'{source.stem}_transkrip'
    paths = [parent / f'{source.stem}.{ext}' for ext in extensions]
    if any(p.resolve() == source.resolve() for p in paths):
        raise ValueError('Lokasi keluaran sama dengan file masukan.')
    return paths


def write_outputs(payloads, approved=()):
    """Stage all content first. Exclusive creation protects races and symlinks.

    On interruption remove new outputs; completed replacements stay complete.
    Existing files are replaced only when explicitly approved by the user.
    """
    staged, created, written = [], [], []
    approved = set(approved)
    try:
        for path, content in payloads:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix='.transcribe-', suffix='.tmp', dir=path.parent)
            stage = Path(name)
            staged.append((stage, path))
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(content)
        for stage, path in staged:
            if path in approved:
                # os.replace replaces the link itself, never follows it into input media.
                os.replace(stage, path)
            else:
                # Hard link publishes a complete file atomically without replacing anything.
                os.link(stage, path)
                created.append(path)
                stage.unlink()
            written.append(path)
        return written
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    finally:
        for stage, _ in staged:
            stage.unlink(missing_ok=True)
