import json
from pathlib import Path
import pytest
from src import narrative_history as h


def novel(tmp_path):
    (tmp_path/'chapters').mkdir()
    (tmp_path/'chapters/ch_01.md').write_text('Original')
    (tmp_path/'state.json').write_text(json.dumps({'id':'fixture','universe_id':'one','phase':'foundation'}))
    h.initialize(tmp_path)
    return tmp_path


def test_baseline_and_exclusions(tmp_path):
    p=novel(tmp_path)
    (p/'.env').write_text('FIXTURE=no-real-secret')
    (p/'.generation.lock').touch()
    h.snapshot(p,'Again')
    tracked=h.git(p,'ls-files').splitlines()
    assert 'chapters/ch_01.md' in tracked
    assert 'state.json' not in tracked and '.env' not in tracked and '.generation.lock' not in tracked
    assert not h.dirty(p)


def test_branches_restore_and_progress(tmp_path):
    p=novel(tmp_path); first=h.git(p,'rev-parse','HEAD')
    h.git(p,'switch','-c','alternative')
    (p/'chapters/ch_01.md').write_text('Alternative')
    state=json.loads((p/'state.json').read_text());state.update(phase='drafting',universe_id='two')
    (p/'state.json').write_text(json.dumps(state));h.snapshot(p,'Alternative')
    h.git(p,'switch','main');h.restore_progress(p)
    assert (p/'chapters/ch_01.md').read_text()=='Original'
    state=json.loads((p/'state.json').read_text());assert state['phase']=='foundation' and state['universe_id']=='two'
    h.git(p,'switch','alternative');h.restore_progress(p)
    h.rollback(p,first);h.snapshot(p,'Restore')
    assert (p/'chapters/ch_01.md').read_text()=='Original'
    assert len(h.git(p,'log','--oneline').splitlines())==3


def test_dirty_and_deletion(tmp_path):
    p=novel(tmp_path);first=h.git(p,'rev-parse','HEAD')
    (p/'chapters/ch_01.md').unlink()
    with pytest.raises(ValueError):h.require_clean(p)
    h.snapshot(p,'Delete');assert not (p/'chapters/ch_01.md').exists()
    h.rollback(p,first);assert (p/'chapters/ch_01.md').read_text()=='Original'


def test_published_is_blocked(tmp_path):
    p=novel(tmp_path);(p/'.publication.json').write_text('{"publication_status":"published"}')
    with pytest.raises(ValueError):h.snapshot(p,'Forbidden')
