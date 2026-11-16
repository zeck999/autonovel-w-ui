import threading
import time
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from src import api, projects, jobs
from src.security import safe_child, validate_id

client = TestClient(api.app)


def wait_job(job_id):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = client.get(f'/api/jobs/{job_id}').json()
        if job['status'] in ('succeeded', 'failed'):
            return job
        time.sleep(.01)
    raise AssertionError('Job never completed')


def test_path_escape_and_symlinks(tmp_path):
    root = tmp_path / 'safe'; root.mkdir()
    sibling = tmp_path / 'safe-other'; sibling.mkdir()
    (sibling / 'note.md').write_text('private fixture')
    (root / 'link').symlink_to(sibling, target_is_directory=True)
    for path in ['../safe-other/note.md', '/etc/passwd', 'link/note.md', 'a/../../bad', '.env']:
        if path == '.env':
            with pytest.raises(ValueError):
                projects.project_file(root, path)
        else:
            with pytest.raises(ValueError):
                safe_child(root, path)
    for value in ['..', '../x', 'a/b', 'a;b', '']:
        with pytest.raises(ValueError):
            validate_id(value)


def test_static_cannot_escape(tmp_path, monkeypatch):
    ui = tmp_path / 'ui'; ui.mkdir(); (ui / 'index.html').write_text('UI')
    (tmp_path / 'outside.txt').write_text('private fixture')
    monkeypatch.setattr(api, 'STATIC_UI', ui)
    response = client.get('/%2e%2e/outside.txt')
    assert response.status_code == 404
    assert 'private fixture' not in response.text
    assert client.get('/api/not-a-route').status_code == 404


def test_auth_and_origin(monkeypatch):
    monkeypatch.setenv('AUTONOVEL_ACCESS_TOKEN', 'test-access-token')
    assert client.get('/api/projects').status_code == 401
    assert client.get('/api/projects', headers={'Authorization': 'Bearer test-access-token'}).status_code == 200
    assert client.get('/api/projects', headers={'Authorization': 'Bearer test-access-token', 'Origin': 'https://evil.test'}).status_code == 403


def test_lan_requires_token():
    with TestClient(api.app, client=('192.0.2.1', 1234)) as remote:
        assert remote.get('/api/projects').status_code in (401, 403)


def test_forbid_shell_phase_and_missing_project():
    with patch.object(api, 'run_pipeline_phase') as run:
        response = client.post('/api/pipeline/run', json={'phase': 'foundation; touch bad', 'project_id': 'test'})
        assert response.status_code == 422
        assert client.post('/api/pipeline/run', json={'phase': 'foundation'}).status_code == 422
        run.assert_not_called()


def test_conflict_and_permissions():
    pid = projects.create_project('Conflict', 'concept')['id']
    assert client.put(f'/api/projects/{pid}/files/world.md', json={'content': 'v1'}).status_code == 200
    assert client.put(f'/api/projects/{pid}/files/world.md', json={'content': 'v2', 'expected_content': ''}).status_code == 409
    assert projects.get_project_file(pid, 'world.md') == 'v1'
    assert client.put(f'/api/projects/{pid}/files/state.json', json={'content': '{}'}).status_code == 400
    assert client.put(f'/api/projects/{pid}/files/chapters/chapter_01.md', json={'content': 'bad'}).status_code == 400


def test_job_dedup_and_competing_operations():
    gate = threading.Event()
    started = threading.Event()
    def work():
        started.set(); gate.wait(2); return {'score': 8.1}
    first = jobs.submit_job('job-fixture', 'draft', work)
    try:
        assert started.wait(1)
        assert jobs.submit_job('job-fixture', 'draft', work)['id'] == first['id']
        with pytest.raises(jobs.ProjectBusyError):
            jobs.submit_job('job-fixture', 'evaluate', work)
    finally:
        gate.set()
    assert wait_job(first['id'])['result']['score'] == 8.1


def test_async_api_returns_job():
    pid = projects.create_project('Job API', 'concept')['id']
    with patch.object(api, 'evaluate_project', return_value={'score': 7.2, 'returncode': 0}):
        response = client.post('/api/pipeline/evaluate', json={'project_id': pid})
        assert response.status_code == 202
        assert wait_job(response.json()['id'])['result']['score'] == 7.2


def test_ai_proposal_never_saves(monkeypatch):
    pid = projects.create_project('Proposal', 'concept')['id']
    projects.save_project_file(pid, 'chapters/ch_01.md', 'original')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'fixture-key')
    import httpx
    response = httpx.Response(200, json={'content': [{'text': 'proposed'}], 'stop_reason': 'end_turn'})
    with patch.object(httpx, 'post', return_value=response):
        job = client.post(f'/api/projects/{pid}/chapters/modify', json={'file_path': 'chapters/ch_01.md', 'content': 'original', 'prompt': 'revise'})
        assert job.status_code == 202
        completed = wait_job(job.json()['id'])
        assert completed['status'] == 'succeeded', completed
        assert completed['result']['content'] == 'proposed'
        assert completed['result']['original_content'] == 'original'
    assert projects.get_project_file(pid, 'chapters/ch_01.md') == 'original'


def test_idempotency_survives_completion():
    calls = []
    def work():
        calls.append(1)
        return {"ok": True}
    first = jobs.submit_job("idempotency-fixture", "draft", work, "fixture-idempotency")
    assert wait_job(first["id"])["status"] == "succeeded"
    assert jobs.submit_job("idempotency-fixture", "draft", work, "fixture-idempotency")["id"] == first["id"]
    assert len(calls) == 1


def test_key_newline_injection_rejected():
    response = client.put('/api/settings/keys', json={'anthropic_api_key': 'fixture\nOTHER_KEY=bad'})
    assert response.status_code == 400
