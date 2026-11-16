from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api import app
from tests_helpers import wait_job

client = TestClient(app)


def chapter():
    pid = client.post('/api/projects', json={'name': 'AI test', 'concept': 'fixture'}).json()['id']
    client.put(f'/api/projects/{pid}/files/chapters/ch_01.md', json={'content': 'Original'})
    return pid


def test_chapter_modify_missing_key():
    pid = chapter()
    response = client.post(f'/api/projects/{pid}/chapters/modify', json={'file_path': 'chapters/ch_01.md', 'content': 'Original', 'prompt': 'revise'})
    assert response.status_code == 202
    job = wait_job(client, response.json()['id'])
    assert job['status'] == 'failed'
    assert 'ERR_AI_MOD_KEY_MISSING' in job['error']


def test_chapter_modify_project_not_found():
    response = client.post('/api/projects/not-found/chapters/modify', json={'file_path': 'chapters/ch_01.md', 'content': 'Original', 'prompt': 'revise'})
    assert response.status_code == 404


def test_chapter_modify_success_mock(monkeypatch):
    import httpx
    pid = chapter()
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'fixture-key')
    with patch('httpx.post', return_value=httpx.Response(200, json={'content': [{'text': 'Proposal'}]})):
        response = client.post(f'/api/projects/{pid}/chapters/modify', json={'file_path': 'chapters/ch_01.md', 'content': 'Original', 'prompt': 'revise'})
        assert response.status_code == 202
        job = wait_job(client, response.json()['id'])
        assert job['result']['status'] == 'proposal'
        assert job['result']['content'] == 'Proposal'
    assert client.get(f'/api/projects/{pid}/files/chapters/ch_01.md').json()['content'] == 'Original'
