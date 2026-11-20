import json
from pathlib import Path
from unittest.mock import patch
import pytest
from src import projects, universes, canon, publication
from src.migrate_universes import migrate


def novel():
    result = projects.create_project('Novel', 'A world')
    directory = projects.PROJECTS_DIR / result['id']
    (directory / 'chapters' / 'ch_01.md').write_text('Alice believes the king is dead. The king lives.')
    return result, directory


def test_universe_mandatory_and_distinct():
    one = projects.create_project('Same name', 'one')
    two = projects.create_project('Same name', 'two')
    assert one['universe_id'] != two['universe_id']
    assert universes.get_universe(one['universe_id'])['name'] == 'Same name'
    with pytest.raises(ValueError):
        universes.delete_universe(one['universe_id'])
    with pytest.raises(ValueError):
        projects.create_project('Invalid', 'test', 'missing-universe')


def test_ledger_additive_belief_and_supersedes():
    project, directory = novel()
    assertion = {'text': 'Alice believes king dead', 'kind': 'belief', 'character': 'Alice', 'time': 'Chapter 1',
                 'source': {'file': 'chapters/ch_01.md', 'quote': 'Alice believes the king is dead.'}}
    ids = canon.add_assertions(project['universe_id'], project['id'], [assertion], canon.manuscript_hash(directory))
    replacement = dict(assertion, text='Alice mistakenly believes king dead', supersedes=ids[0])
    canon.add_assertions(project['universe_id'], project['id'], [replacement], canon.manuscript_hash(directory))
    registry = canon.get_registry(project['universe_id'])
    assert len(registry['assertions']) == 2
    assert registry['assertions'][0]['active'] is False
    assert registry['assertions'][1]['active'] is True
    with pytest.raises(ValueError):
        canon.add_assertions(project['universe_id'], project['id'], [dict(assertion, character='')], canon.manuscript_hash(directory))


def test_publication_freezes_and_recovers():
    project, directory = novel()
    assertion = {'text': 'King lives', 'kind': 'fact', 'source': {'file': 'chapters/ch_01.md', 'quote': 'The king lives.'}}
    ids = canon.add_assertions(project['universe_id'], project['id'], [assertion], canon.manuscript_hash(directory))
    report = {'manuscript_hash': canon.manuscript_hash(directory), 'universe_revision': canon.universe_revision(project['universe_id'])}
    with patch('src.coherence.publication_check', return_value=report):
        status = publication.publish(project['id'], True)
    assert status['publication_status'] == 'published'
    assert canon.get_registry(project['universe_id'])['assertions'][0]['canon'] is True
    original = json.loads((directory / '.published/original.json').read_text())
    assert original['chapters/ch_01.md'].startswith('Alice')
    (directory / '.publication.json').unlink()
    assert publication.get_status(project['id'])['publication_status'] == 'published'
    with pytest.raises(ValueError):
        projects.save_project_file(project['id'], 'chapters/ch_01.md', 'changed')
    with pytest.raises(ValueError):
        projects.delete_project(project['id'])
    with pytest.raises(ValueError):
        canon.add_assertions(project['universe_id'], project['id'], [dict(assertion, supersedes=ids[0])], canon.manuscript_hash(directory))


def test_publication_stale_report_blocked():
    project, directory = novel()
    with patch('src.coherence.publication_check', return_value={'manuscript_hash': 'stale', 'universe_revision': 'stale'}):
        with pytest.raises(ValueError):
            publication.publish(project['id'], True)
    assert publication.get_status(project['id'])['publication_status'] == 'draft'


def test_migration_dry_run_idempotent_and_invalid_metadata(tmp_path):
    root = tmp_path / 'migration'
    directory = root / 'projects' / 'old'; directory.mkdir(parents=True)
    (directory / 'state.json').write_text(json.dumps({'id': 'old', 'name': 'Old', 'universe_id': None}))
    assert migrate(root)[0]['action'] == 'create_universe'
    assert not (root / 'universes').exists()
    assert migrate(root, True)[0]['action'] == 'create_universe'
    uid = json.loads((directory / 'state.json').read_text())['universe_id']
    assert (root / 'universes' / uid / 'state.json').exists()
    assert migrate(root, True)[0]['action'] == 'unchanged'
    assert len(list((root / 'universes').iterdir())) == 1
    broken = root / 'projects' / 'broken'; broken.mkdir(); (broken / 'state.json').write_text('{broken')
    assert any(item['action'] == 'error' for item in migrate(root, True))
    assert (broken / 'state.json').read_text() == '{broken'


def test_migration_resumes_prepared_universe_without_duplicate(tmp_path):
    root = tmp_path / 'interrupted'
    directory = root / 'projects' / 'old'; directory.mkdir(parents=True)
    (directory / 'state.json').write_text(json.dumps({'name': 'Old'}))
    canon.atomic_json(root / '.universe-migration.json', {'version': 1, 'projects': {'old': {'name': 'Old', 'universe_id': 'reserved', 'status': 'prepared'}}})
    (root / 'universes' / 'reserved').mkdir(parents=True)
    assert migrate(root, True)[0]['universe_id'] == 'reserved'
    assert len(list((root / 'universes').iterdir())) == 1


def test_broken_explicit_link_is_repaired_without_reading_outside(tmp_path):
    root = tmp_path / 'broken-link'
    directory = root / 'projects' / 'old'; directory.mkdir(parents=True)
    (directory / 'state.json').write_text(json.dumps({'name': 'Old', 'universe_id': '../outside'}))
    assert migrate(root, True)[0]['action'] == 'create_universe'
    assert json.loads((directory / 'state.json').read_text())['universe_id'] == 'old'
