import json
import subprocess

from fastapi.testclient import TestClient

from src.api import app
from src.branch_graph import revision_graph
from src.state_store import prompt_context

A, B, C = ('chapters/ch_01.md', 'chapters/ch_02.md', 'chapters/ch_10.md')
URL = '/api/projects/story-fixture/story'


def fixture(tmp_path):
    project = tmp_path / 'projects' / 'story-fixture'
    (project / 'chapters').mkdir(parents=True)
    for chapter in (A, B, C):
        (project / chapter).write_text('Texte du chapitre.')
    return project


def story():
    return {'start': A, 'variables': {'trust': 2, 'key': False, 'mood': 'calme'},
            'overrides': {B: {'mood': 'inquiet'}}, 'choices': [
                {'id': 'enter', 'label': 'Entrer', 'source': A, 'target': B,
                 'conditions': [{'variable': 'trust', 'op': 'gte', 'value': 2}], 'effects': {'key': True}},
                {'id': 'leave', 'label': 'Sortir', 'source': B, 'target': C,
                 'conditions': [{'variable': 'key', 'op': 'eq', 'value': True}]},
            ]}


def save(client, data, revision=None):
    if revision is None:
        revision = client.get(URL).json()['revision']
    return client.put(URL, json={'story': data, 'expected_revision': revision})


def test_story_isolated_persistent_and_playable(tmp_path):
    project = fixture(tmp_path)
    client = TestClient(app)
    initial = client.get(URL).json()
    assert initial['chapters'] == [A, B, C]
    assert initial['editable'] is True
    assert prompt_context(project, A) == ''
    data = story()
    saved = save(client, data, initial['revision'])
    assert saved.status_code == 200, saved.text
    assert save(client, data, initial['revision']).status_code == 409
    preview = client.post(URL + '/step', json={'chapter': A}).json()
    assert [choice['id'] for choice in preview['choices']] == ['enter']
    blocked = client.post(URL + '/step', json={'chapter': A, 'values': {'trust': 1}, 'choice_id': 'enter'})
    assert blocked.status_code == 400
    next_step = client.post(URL + '/step', json={'chapter': A, 'choice_id': 'enter'}).json()
    assert next_step['chapter'] == B
    assert next_step['values'] == {'trust': 2, 'key': True, 'mood': 'inquiet'}
    assert [choice['id'] for choice in next_step['choices']] == ['leave']
    end = client.post(URL + '/step', json={'chapter': B, 'values': next_step['values'], 'choice_id': 'leave'}).json()
    assert end['chapter'] == C and end['choices'] == []
    assert client.get(URL).json() == saved.json()
    assert client.get('/api/projects/absent/story').status_code == 404
    assert '"mood": "inquiet"' in prompt_context(project, B)
    assert json.loads((project / 'story.json').read_text())['variables']['key'] is False


def test_story_rejects_inconsistent_data_and_publication_writes(tmp_path):
    project = fixture(tmp_path)
    client = TestClient(app)
    data = story()
    data['choices'][0]['effects']['key'] = 1
    assert save(client, data).status_code == 400
    data = story()
    data['choices'][0]['target'] = 'chapters/ch_99.md'
    assert save(client, data).status_code == 400
    data = story()
    data['choices'][1]['id'] = data['choices'][0]['id']
    assert save(client, data).status_code == 400
    data = story()
    assert save(client, data).status_code == 200
    (project / '.publication.json').write_text('{"publication_status":"published"}')
    assert client.get(URL).json()['editable'] is False
    assert save(client, data).status_code == 400
    assert client.post(URL + '/step', json={'chapter': A}).status_code == 200


def test_story_graph_distinguishes_choices_from_git_ancestry(tmp_path):
    project = fixture(tmp_path)
    client = TestClient(app)
    assert save(client, story()).status_code == 200
    graph = client.get(URL + '/graph').json()
    assert graph['history']['nodes'] == []
    assert [(edge['source'], edge['target']) for edge in graph['story']['edges']] == [(A, B), (B, C)]
    assert not (project / '.git').exists()

    def git(*args):
        return subprocess.check_output(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                                        '-c', 'commit.gpgsign=false', *args], cwd=project, text=True).strip()

    git('init', '-b', 'main')
    git('commit', '--allow-empty', '-m', 'Racine')
    base = git('rev-parse', 'HEAD')
    git('switch', '-c', 'alternative')
    git('commit', '--allow-empty', '-m', 'Alternative')
    fork = git('rev-parse', 'HEAD')
    git('switch', 'main')
    git('commit', '--allow-empty', '-m', 'Suite')
    main = git('rev-parse', 'HEAD')
    revisions = client.get(URL + '/graph').json()['history']
    assert {tuple(edge.values()) for edge in revisions['edges']} == {(base, fork), (base, main)}
    assert {node['id']: node['branches'] for node in revisions['nodes']} == {base: [], fork: ['alternative'], main: ['main']}
    assert revision_graph(project, limit=1)['truncated'] is True
    assert git('rev-parse', 'HEAD') == main
