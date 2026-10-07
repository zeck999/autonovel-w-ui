"""
Unit tests for src/api.py (FastAPI endpoints and UI static/HTML serving)
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Autonovel" in response.text

def test_static_css_endpoint():
    response = client.get("/css/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]

def test_static_js_endpoint():
    response = client.get("/js/router.js")
    assert response.status_code == 200

def test_api_projects_workflow():
    # Create project
    payload = {
        "name": "API Test Novel",
        "concept": "An experimental API test novel."
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 200
    data = response.json()
    pid = data["id"]
    assert data["name"] == "API Test Novel"
    
    # List projects
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert any(p["id"] == pid for p in projects)
    
    # Get project
    response = client.get(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["id"] == pid
    
    # Delete project
    response = client.delete(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_api_universes_workflow():
    payload = {
        "name": "API Test Universe",
        "description": "Shared lore for API tests."
    }
    response = client.post("/api/universes", json=payload)
    assert response.status_code == 200
    data = response.json()
    uid = data["id"]
    assert data["name"] == "API Test Universe"
    
    response = client.get("/api/universes")
    assert response.status_code == 200
    universes = response.json()
    assert any(u["id"] == uid for u in universes)
    
    response = client.get(f"/api/universes/{uid}")
    assert response.status_code == 200
    
    response = client.delete(f"/api/universes/{uid}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_api_versioning_and_pipeline():
    response = client.get("/api/versioning/branches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    response = client.get("/api/pipeline/status")
    assert response.status_code == 200
    assert "phase" in response.json()

def test_api_project_files_workflow():
    # Create project
    payload = {
        "name": "Files Test Novel",
        "concept": "A testing novel for project files API."
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 200
    data = response.json()
    pid = data["id"]

    # List files
    response = client.get(f"/api/projects/{pid}/files")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)
    assert any(f["name"] == "seed.txt" for f in files)

    # Read seed.txt
    response = client.get(f"/api/projects/{pid}/files/seed.txt")
    assert response.status_code == 200
    assert "A testing novel" in response.json()["content"]

    # Save world.md
    save_payload = {"content": "# World Lore\n\nNeo Tokyo 2150."}
    response = client.put(f"/api/projects/{pid}/files/world.md", json=save_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # Read world.md
    response = client.get(f"/api/projects/{pid}/files/world.md")
    assert response.status_code == 200
    assert "Neo Tokyo 2150" in response.json()["content"]

    # Save chapter_01.md
    ch_payload = {"content": "# Chapter 1 API\n\nBeginning of the journey."}
    response = client.put(f"/api/projects/{pid}/files/chapters/chapter_01.md", json=ch_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # Read chapter_01.md
    response = client.get(f"/api/projects/{pid}/files/chapters/chapter_01.md")
    assert response.status_code == 200
    assert "Beginning of the journey" in response.json()["content"]

    # List files includes chapters/chapter_01.md
    response = client.get(f"/api/projects/{pid}/files")
    assert response.status_code == 200
    files = response.json()
    assert any(f["name"] == "chapters/chapter_01.md" for f in files)

    # Cleanup: Delete project
    client.delete(f"/api/projects/{pid}")
