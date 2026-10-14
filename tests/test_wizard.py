"""
Unit tests for backend wizard endpoints and helpers in src/projects.py and src/api.py
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.projects import wizard_suggest, create_project_from_wizard, WizardCreate, get_project, delete_project

client = TestClient(app)

def test_wizard_suggest_endpoint():
    response = client.post("/api/projects/wizard/suggest", json={
        "field_key": "concept",
        "current_parameters": {"genre": "Sci-Fi"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["field_key"] == "concept"
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) == 4

def test_wizard_create_endpoint():
    payload = {
        "name": "Wizard Test Novel",
        "concept": "A magical steampunk journey across the skies.",
        "genre": "Steampunk Fantasy",
        "tone": "Adventurous & Witty",
        "protagonist": "A daring sky-captain with a mechanical compass.",
        "conflict": "Stopping an aerial pirate armada from plundering the cloud cities.",
        "world_setting": "Endless layers of floating cloud continents.",
        "universe_id": None
    }
    response = client.post("/api/projects/wizard/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    pid = data["id"]
    assert data["name"] == "Wizard Test Novel"
    assert data["genre"] == "Steampunk Fantasy"

    # Verify project files exist
    proj = get_project(pid)
    assert proj is not None

    files_resp = client.get(f"/api/projects/{pid}/files")
    assert files_resp.status_code == 200
    file_names = [f["name"] for f in files_resp.json()]
    for expected_file in ["seed.txt", "world.md", "characters.md", "canon.md", "outline.md"]:
        assert expected_file in file_names

    # Clean up
    delete_project(pid)
