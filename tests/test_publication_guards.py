"""Published novels remain readable but ordinary generators must fail closed."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
from src import pipeline_adapter, versioning
from src.project_context import ensure_data_editable

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('metadata', [
    {'publication_status': 'published'}, {'status': 'publishing'},
])
def test_publication_metadata_blocks_write(tmp_path, metadata):
    (tmp_path / '.publication.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        ensure_data_editable(tmp_path)


@pytest.mark.parametrize('name', ['.publication-transaction.json', '.publication_transaction.json'])
def test_interrupted_transaction_blocks_write(tmp_path, name):
    (tmp_path / name).write_text('{}')
    with pytest.raises(ValueError):
        ensure_data_editable(tmp_path)


def test_bad_metadata_fails_closed(tmp_path):
    (tmp_path / '.publication.json').write_text('broken')
    with pytest.raises(ValueError):
        ensure_data_editable(tmp_path)


def test_draft_editable(tmp_path):
    (tmp_path / '.publication.json').write_text('{"publication_status":"draft"}')
    ensure_data_editable(tmp_path)


def test_pipeline_and_git_reject_before_process(tmp_path, monkeypatch):
    directory = tmp_path / 'projects' / 'published'; directory.mkdir(parents=True)
    (directory / '.publication.json').write_text('{"publication_status":"published"}')
    monkeypatch.setattr(pipeline_adapter, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(versioning, 'BASE_DIR', tmp_path)
    with patch.object(pipeline_adapter, 'execute') as execute:
        result = pipeline_adapter.run_pipeline_phase('foundation', 'published')
        assert result['returncode'] != 0
        assert 'read-only' in result['error']
        execute.assert_not_called()
    with patch.object(versioning, 'run_git_cmd') as git:
        for function in (versioning.create_branch, versioning.switch_branch):
            with pytest.raises(ValueError):
                function('other', 'published')
        git.assert_not_called()
    assert versioning.list_branches('published') == []


@pytest.mark.parametrize('script', [
    'gen_world.py', 'gen_characters.py', 'gen_outline.py', 'gen_outline_part2.py',
    'gen_canon.py', 'gen_revision.py', 'draft_chapter.py', 'apply_cuts.py',
    'run_pipeline.py', 'run_drafts.py', 'voice_fingerprint.py', 'seed.py',
    'build_outline.py', 'adversarial_edit.py', 'gen_audiobook.py',
])
def test_cli_rejects_published_before_config_or_api(tmp_path, script):
    (tmp_path / '.publication.json').write_text('{"publication_status":"published"}')
    environment = dict(os.environ, AUTONOVEL_PROJECT_DIR=str(tmp_path),
                       PYTHONPATH=str(ROOT))
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=tmp_path,
                            env=environment, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'Published novels are read-only' in result.stderr
    assert {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


def test_data_context_import_allows_reading_published(tmp_path):
    (tmp_path / '.publication.json').write_text('{"publication_status":"published"}')
    result = subprocess.run([sys.executable, '-c',
                             'from src.project_context import DATA_DIR; print(DATA_DIR)'],
                            cwd=ROOT, env=dict(os.environ, AUTONOVEL_PROJECT_DIR=str(tmp_path)),
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_pipeline_invalidates_after_partial_failure(tmp_path, monkeypatch):
    directory = tmp_path / 'projects' / 'partial'; directory.mkdir(parents=True)
    (directory / 'state.json').write_text('{}')
    monkeypatch.setattr(pipeline_adapter, 'BASE_DIR', tmp_path)
    def fail(*args, **kwargs):
        (directory / 'world.md').write_text('partially generated world')
        raise RuntimeError('fixture failure')
    with patch.object(pipeline_adapter, 'execute', side_effect=fail), patch.object(pipeline_adapter, 'notify_data_changed') as notify:
        with pytest.raises(RuntimeError, match='fixture failure'):
            pipeline_adapter.run_pipeline_phase('foundation', 'partial')
        notify.assert_called_once_with(directory)


def test_git_checkout_invalidates_analysis(tmp_path, monkeypatch):
    directory = tmp_path / 'projects' / 'draft'; directory.mkdir(parents=True)
    monkeypatch.setattr(versioning, 'BASE_DIR', tmp_path)
    from src import narrative_history as history
    history.initialize(directory)
    history.snapshot(directory, 'Initial snapshot')
    history.git(directory, 'branch', 'other')
    with patch.object(versioning, 'notify_data_changed') as notify:
        assert versioning.switch_branch('other', 'draft') is True
        notify.assert_called_once_with(directory)
