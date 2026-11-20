from unittest.mock import patch
import pytest
from src import coherence, canon, publication, projects


def novel():
    project = projects.create_project('Coherence', 'fixture')
    projects.save_project_file(project['id'], 'chapters/ch_01.md', 'Le roi est vivant. Paul croit le roi mort.')
    return project


def result(issues=None, assertions=None):
    return dict(complete=True, issues=issues or [], assertions=assertions or [])


def test_manual_then_auto_and_publication():
    project = novel(); pid = project['id']
    assert coherence.get_state(pid)['auto_enabled'] is False
    assertion = dict(kind='belief', statement='Paul croit le roi mort', subject='Paul', period='chapitre 1', source={'file':'chapters/ch_01.md','quote':'Paul croit le roi mort.'})
    with patch.object(coherence, '_provider', return_value=result(assertions=[assertion])):
        report = coherence.analyze(pid)
    assert coherence.get_state(pid)['status'] == 'awaiting_validation'
    with pytest.raises(ValueError): coherence.publication_check(pid)
    coherence.accept_proposals(pid, report['id'], [report['proposals'][0]['id']])
    assert coherence.publication_check(pid)['id'] == report['id']
    published = publication.publish(pid, True)
    assert published['publication_status'] == 'published'
    with pytest.raises(ValueError): projects.save_project_file(pid, 'chapters/ch_01.md', 'change')
    assert canon.get_registry(project['universe_id'])['assertions'][0]['canon']


def test_contradiction_and_incremental_block():
    project = novel(); pid = project['id']
    issue = dict(kind='contradiction',severity='error',source={'file':'chapters/ch_01.md','quote':'Le roi est vivant.'},against={'source':'universe','quote':'Paul croit le roi mort.'},description='Contradiction',suggestion='Corriger')
    with patch.object(coherence, '_provider', return_value=result(issues=[issue])):
        coherence.analyze(pid)
    with pytest.raises(ValueError): coherence.publication_check(pid)
    with patch.object(coherence, '_provider', return_value=result()):
        coherence.analyze(pid, full=False)
    with pytest.raises(ValueError): coherence.publication_check(pid)


def test_stale_and_failed_analysis():
    pid = novel()['id']
    with patch.object(coherence, '_provider', return_value=result()): coherence.analyze(pid)
    projects.save_project_file(pid, 'chapters/ch_01.md', 'Modifié')
    assert coherence.get_state(pid)['status'] == 'pending'
    with pytest.raises(ValueError): coherence.publication_check(pid)
    with patch.object(coherence, '_provider', return_value={'complete':False}):
        with pytest.raises(ValueError): coherence.analyze(pid)
    assert coherence.get_state(pid)['status'] == 'failed'


def test_no_fake_source_allowed():
    pid = novel()['id']
    assertion = dict(kind='fact',statement='Inventé',source={'file':'chapters/ch_01.md','quote':'Absent du texte'})
    with patch.object(coherence,'_provider',return_value=result(assertions=[assertion])):
        with pytest.raises(ValueError): coherence.analyze(pid)


def test_changed_universe_invalidates_report():
    project = novel(); pid = project['id']
    with patch.object(coherence, '_provider', return_value=result()): coherence.analyze(pid)
    canon.append_event(project['universe_id'], {'id':'external','type':'legacy_import','description':'new context'})
    with pytest.raises(ValueError): coherence.publication_check(pid)


def test_pending_request_is_durable():
    pid = novel()['id']
    coherence.request_analysis(pid, full=True)
    state = coherence._read(coherence.directory(pid))
    assert state['pending'] is True
    assert state['requested_full'] is True
    assert coherence.get_state(pid)['auto_enabled'] is False


def test_oversized_corpus_fails_closed_without_provider_call(monkeypatch):
    pid = novel()['id']
    monkeypatch.setattr(coherence, 'MAX_CONTEXT_CHARS', 1)
    with patch.object(coherence, '_provider') as provider:
        with pytest.raises(ValueError): coherence.analyze(pid)
        provider.assert_not_called()
    with pytest.raises(ValueError): coherence.publication_check(pid)


def test_pairwise_coverage_includes_every_source(monkeypatch):
    monkeypatch.setattr(coherence, 'MAX_CONTEXT_CHARS', 1600)
    monkeypatch.setattr(coherence, 'CHUNK_CHARS', 600)
    files = {'chapters/ch_01.md': 'a' * 700, 'chapters/ch_02.md': 'b' * 700}
    contexts = coherence._audit_contexts(files, files, {'canon':'c' * 700}, True)
    assert len(contexts) > 1
    assert any('universe_section' in context for context in contexts)
    assert any('manuscript_sections' in context for context in contexts)


def test_save_during_analysis_never_certifies_new_text():
    pid = novel()['id']
    def provider(prompt):
        projects.save_project_file(pid, 'chapters/ch_01.md', 'Texte plus récent')
        return result()
    with patch.object(coherence, '_provider', side_effect=provider):
        report = coherence.analyze(pid)
    assert report['stale'] is True
    assert coherence.get_state(pid)['status'] == 'pending'
    with pytest.raises(ValueError): coherence.publication_check(pid)


def test_cli_generation_lease_blocks_publication():
    import fcntl
    pid = novel()['id']
    with patch.object(coherence, '_provider', return_value=result()): coherence.analyze(pid)
    with (coherence.directory(pid) / '.generation.lock').open('a+') as lease:
        fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='CLI generation'):
            publication.publish(pid, True)
    assert publication.publish(pid, True)['publication_status'] == 'published'


def test_worker_resumes_pending_request(monkeypatch):
    import threading
    pid = novel()['id']
    coherence.request_analysis(pid, True)
    path = coherence.directory(pid)
    state = coherence._read(path)
    state['due_at'] = 0
    coherence._write(coherence._state_path(path), state)
    called = threading.Event()
    real_analyze = coherence.analyze
    def resumed(project_id, full=True):
        try:
            return real_analyze(project_id, full)
        finally:
            called.set()
    with patch.object(coherence, '_provider', return_value=result()), patch.object(coherence, 'analyze', side_effect=resumed):
        coherence.start_worker()
        try:
            assert called.wait(6)
        finally:
            coherence.stop_worker()
            coherence._WORKER.join(timeout=3)
    assert coherence.get_state(pid)['status'] == 'current'


def test_readonly_analysis_job_allows_editor_save():
    import threading
    from src import jobs
    pid = novel()['id']
    entered, release = threading.Event(), threading.Event()
    def audit():
        entered.set()
        assert release.wait(3)
        return {'ok':True}
    job = jobs.submit_job(pid, 'coherence-fixture', audit, serialize=False)
    try:
        assert entered.wait(2)
        projects.save_project_file(pid, 'chapters/ch_01.md', 'Saved during audit')
    finally:
        release.set()
    assert projects.get_project_file(pid, 'chapters/ch_01.md') == 'Saved during audit'


def test_historical_universe_change_invalidates_check():
    project = novel(); pid = project['id']
    with patch.object(coherence, '_provider', return_value=result()): coherence.analyze(pid)
    (canon.universe_path(project['universe_id']) / 'world.md').write_text('Nouveau contexte historique')
    with pytest.raises(ValueError): coherence.publication_check(pid)


def test_full_reanalysis_does_not_duplicate_accepted_assertions():
    project = novel(); pid = project['id']
    assertion = dict(kind='fact', statement='Le roi vit', source={'file':'chapters/ch_01.md','quote':'Le roi est vivant.'})
    with patch.object(coherence, '_provider', return_value=result(assertions=[assertion])):
        report = coherence.analyze(pid)
        coherence.accept_proposals(pid, report['id'], [report['proposals'][0]['id']])
        second = coherence.analyze(pid)
    assert second['proposals'] == []
    assert len(canon.get_registry(project['universe_id'])['assertions']) == 1
    assert coherence.publication_check(pid)['id'] == second['id']
