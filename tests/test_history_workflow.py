import json
from unittest.mock import patch
import pytest
from src import projects, versioning, narrative_history as h
from src.migrate_history import migrate


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'projects';p=root/'fixture';(p/'chapters').mkdir(parents=True)
    (p/'state.json').write_text(json.dumps({'id':'fixture','universe_id':'one','phase':'foundation'}))
    (p/'chapters/ch_01.md').write_text('Original')
    monkeypatch.setattr(projects,'PROJECTS_DIR',root)
    monkeypatch.setattr(versioning,'BASE_DIR',tmp_path)
    return p


def test_manual_saves_branches_restore(tmp_path,monkeypatch):
    p=fixture(tmp_path,monkeypatch)
    with patch('src.coherence.invalidate_project'),patch.object(versioning,'notify_data_changed'):
        projects.save_project_file('fixture','chapters/ch_01.md','First')
        main=h.git(p,'rev-parse','HEAD')
        versioning.create_branch('alternate','fixture')
        projects.save_project_file('fixture','chapters/ch_01.md','Alternative')
        versioning.switch_branch('main','fixture')
        assert (p/'chapters/ch_01.md').read_text()=='First'
        versioning.switch_branch('alternate','fixture')
        assert (p/'chapters/ch_01.md').read_text()=='Alternative'
        versioning.restore_revision('fixture',main,True)
        assert (p/'chapters/ch_01.md').read_text()=='First'
        assert len(versioning.get_revision_history(project_id='fixture'))==4
        (p/'chapters/ch_01.md').write_text('External')
        with pytest.raises(ValueError):versioning.switch_branch('main','fixture')
        assert (p/'chapters/ch_01.md').read_text()=='External'


def test_migration_idempotent_and_private(tmp_path,monkeypatch):
    p=fixture(tmp_path,monkeypatch);(p/'.env').write_text('FAKE=fixture')
    assert migrate(tmp_path)[0]['action']=='initialize_baseline'
    assert not (p/'.git').exists()
    assert migrate(tmp_path,True)[0]['action']=='initialize_baseline'
    first=h.git(p,'rev-parse','HEAD')
    assert migrate(tmp_path,True)[0]['action']=='preserved'
    assert h.git(p,'rev-parse','HEAD')==first
    assert '.env' not in h.git(p,'ls-files')


def test_generation_lease_blocks_save(tmp_path,monkeypatch):
    import fcntl
    p=fixture(tmp_path,monkeypatch)
    with (p/'.generation.lock').open('w') as lease:
        fcntl.flock(lease,fcntl.LOCK_SH|fcntl.LOCK_NB)
        with pytest.raises(ValueError):projects.save_project_file('fixture','chapters/ch_01.md','Changed')
    assert (p/'chapters/ch_01.md').read_text()=='Original'


def test_history_failure_keeps_saved_text_and_invalidates(tmp_path,monkeypatch):
    p=fixture(tmp_path,monkeypatch)
    h.initialize(p)
    real=h.snapshot
    def fail_after_write(directory,message):
        if message.startswith('Save '): raise ValueError('fixture Git failure')
        return real(directory,message)
    with patch.object(h,'snapshot',side_effect=fail_after_write),patch('src.coherence.invalidate_project') as invalidate:
        with pytest.raises(ValueError,match='File saved'):
            projects.save_project_file('fixture','chapters/ch_01.md','New saved text')
        invalidate.assert_called_once_with('fixture')
    assert (p/'chapters/ch_01.md').read_text()=='New saved text'
    assert h.dirty(p)
    with patch('src.coherence.invalidate_project'):
        projects.save_project_file('fixture','chapters/ch_01.md','New saved text')
    assert not h.dirty(p)
