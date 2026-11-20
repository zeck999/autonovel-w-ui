from fastapi.testclient import TestClient

from src.api import app
from src.stage_parser import parse_stage


def test_staging_cues_keep_order_and_text():
    result = parse_stage('Intro\n\n[bg image="forest.png"]\n[emotion char="Elena" state="rire"]\nArrivée\n[shake intensity="high"]\nOrage')
    assert result == {'warnings': [], 'cues': [
        {'text': 'Intro', 'actions': []},
        {'text': 'Arrivée', 'actions': [
            {'kind': 'bg', 'image': 'forest.png'},
            {'kind': 'emotion', 'char': 'Elena', 'state': 'rire', 'image': 'Elena--rire.png'},
        ]},
        {'text': 'Orage', 'actions': [{'kind': 'shake', 'intensity': 'high'}]},
    ]}


def test_invalid_and_code_lines_remain_literal():
    content = '```md\n[bg image="example.png"]\n```\n[shake intensity="no"]\nUn passage.'
    result = parse_stage(content)
    assert result['cues'] == [{'text': content, 'actions': []}]
    assert [warning['line'] for warning in result['warnings']] == [4]
    assert parse_stage('  \n')['cues'] == []


def test_project_preview_and_private_assets(tmp_path, monkeypatch):
    project = tmp_path / 'projects' / 'fixture'
    assets = project / 'stage-assets'
    assets.mkdir(parents=True)
    image = b'\x89PNG\r\n\x1a\n'
    (assets / 'forest.png').write_bytes(image)
    monkeypatch.setenv('AUTONOVEL_ACCESS_TOKEN', 'fixture-token')
    client = TestClient(app)
    headers = {'Authorization': 'Bearer fixture-token'}
    url = '/api/projects/fixture'
    assert client.get(f'{url}/stage-assets/forest.png').status_code == 401
    response = client.get(f'{url}/stage-assets/forest.png', headers=headers)
    assert response.status_code == 200
    assert response.content == image
    assert response.headers['content-type'] == 'image/png'
    assert client.get(f'{url}/stage-assets/missing.png', headers=headers).status_code == 404
    draft = '[bg image="forest.png"]\nUn brouillon.'
    response = client.post(f'{url}/stage-preview', json={'content': draft}, headers=headers)
    assert response.status_code == 200
    assert response.json() == parse_stage(draft)
    assert list(project.iterdir()) == [assets]
    assert client.post('/api/projects/absent/stage-preview', json={'content': draft}, headers=headers).status_code == 404
