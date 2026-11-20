from unittest.mock import patch
import pytest
from src import projects, coherence, publication, canon, proofreading


def published():
    project = projects.create_project('Forme', 'fixture')
    projects.save_project_file(project['id'], 'chapters/ch_01.md', 'Un roi regne.')
    with patch.object(coherence, '_provider', return_value={'complete':True,'issues':[],'assertions':[]}):
        coherence.analyze(project['id'])
    publication.publish(project['id'], True)
    return project


def test_form_correction_preserves_original():
    p = published(); pid = p['id']
    with patch.object(coherence, '_provider', return_value={'complete':True,'equivalent':True,'issues':[]}):
        proposal = proofreading.propose(pid, 'chapters/ch_01.md', 'Un roi règne.', 'Un roi regne.', True)
    assert projects.get_project_file(pid, 'chapters/ch_01.md') == 'Un roi regne.'
    proofreading.apply(pid, proposal['id'], True)
    assert projects.get_project_file(pid, 'chapters/ch_01.md') == 'Un roi règne.'
    assert proofreading.apply(pid, proposal['id'], True)['status'] == 'applied'
    assert canon.get_registry(p['universe_id'])['publications'][0]['snapshot']['chapters/ch_01.md'] == 'Un roi regne.'


def test_semantic_change_refused():
    pid = published()['id']
    with patch.object(coherence, '_provider', return_value={'complete':True,'equivalent':False,'issues':[]}):
        with pytest.raises(ValueError):
            proofreading.propose(pid, 'chapters/ch_01.md', 'Un roi meurt.', 'Un roi regne.', True)


def test_proofreading_requires_human_confirmation():
    pid = published()['id']
    with pytest.raises(ValueError):
        proofreading.propose(pid, 'chapters/ch_01.md', 'Un roi règne.', 'Un roi regne.', False)
