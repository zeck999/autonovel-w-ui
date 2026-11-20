from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api import app
from src import coherence
from tests_helpers import wait_job

client = TestClient(app)


def test_workflow_api():
    project = client.post('/api/projects', json={'name':'API universe','concept':'fixture'}).json()
    pid = project['id']
    assert project['universe_id']
    assert client.get(f'/api/projects/{pid}/publication').json()['publication_status'] == 'draft'
    assert client.post(f'/api/projects/{pid}/publish', json={'confirmation':True}).status_code == 400
    client.put(f'/api/projects/{pid}/files/chapters/ch_01.md', json={'content':'Le roi règne.'})
    with patch.object(coherence, '_provider', return_value={'complete':True,'issues':[],'assertions':[]}):
        response = client.post(f'/api/projects/{pid}/coherence/analyze', json={'full':True})
        assert response.status_code == 202
        assert wait_job(client, response.json()['id'])['status'] == 'succeeded'
    assert client.get(f'/api/projects/{pid}/coherence').json()['report']['complete']
    assert client.post(f'/api/projects/{pid}/publish', json={'confirmation':True}).status_code == 200
    assert client.put(f'/api/projects/{pid}/files/chapters/ch_01.md', json={'content':'Change'}).status_code == 400
    assert client.delete(f'/api/projects/{pid}').status_code == 400
    assert client.post(f'/api/projects/{pid}/chapters/modify', json={'file_path':'chapters/ch_01.md','content':'Le roi règne.','prompt':'Change'}).status_code == 400
    assert client.post('/api/pipeline/run', json={'project_id':pid,'phase':'foundation'}).status_code == 400


def test_review_rationale_is_not_publication_override():
    project = client.post('/api/projects', json={'name':'Review dispute','concept':'fixture'}).json()
    pid = project['id']
    client.put(f'/api/projects/{pid}/files/chapters/ch_01.md', json={'content':'Un roi vit. Un roi meurt.'})
    issue = {'kind':'contradiction','severity':'error','source':{'file':'chapters/ch_01.md','quote':'Un roi vit.'},
             'against':{'source':'chapters/ch_01.md','quote':'Un roi meurt.'},'description':'Conflit','suggestion':'Clarifier les dates'}
    with patch.object(coherence, '_provider', return_value={'complete':True,'issues':[issue],'assertions':[]}):
        response = client.post(f'/api/projects/{pid}/coherence/review',json={'rationale':'Les deux événements sont séparés dans le temps.'})
        assert response.status_code == 202
        assert wait_job(client, response.json()['id'])['status'] == 'succeeded'
    assert client.post(f'/api/projects/{pid}/publish', json={'confirmation':True}).status_code == 400
