"""Every test runs on disposable application data; never mutate the checkout's novels."""
import shutil
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolated_application(tmp_path, monkeypatch):
    from src import projects, universes, settings, pipeline_adapter, versioning
    root = Path(__file__).resolve().parent.parent
    for name in ['world.md', 'characters.md', 'canon.md', 'outline.md', 'voice.md', 'MYSTERY.md', 'state.json']:
        source = root / name
        if source.is_file():
            shutil.copy2(source, tmp_path / name)
    (tmp_path / 'projects').mkdir()
    (tmp_path / 'universes').mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(projects, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(projects, 'PROJECTS_DIR', tmp_path / 'projects')
    monkeypatch.setattr(universes, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(universes, 'UNIVERSES_DIR', tmp_path / 'universes')
    monkeypatch.setattr(pipeline_adapter, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(versioning, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(settings, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(settings, 'ENV_FILE', tmp_path / '.env')
    monkeypatch.setattr(settings, 'ENV_EXAMPLE', tmp_path / 'absent.env.example')
    for key in settings.SUPPORTED_KEYS + ['AUTONOVEL_ACCESS_TOKEN', 'AUTONOVEL_PROJECT_DIR']:
        monkeypatch.delenv(key, raising=False)
    # Undo service writes to os.environ as well as monkeypatch's own edits.
    import os
    original = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original)
