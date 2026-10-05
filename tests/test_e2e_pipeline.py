"""
End-to-End (E2E) integration test for Autonovel Web UI & Pipeline API.
Simulates the complete user journey using TestClient and httpx.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from src.api import app

client = TestClient(app)

@patch("src.pipeline_adapter.subprocess.run")
def test_e2e_user_journey(mock_subprocess_run):
    # Mock successful pipeline execution subprocess run
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Pipeline phase executed successfully with absolute path."
    mock_res.stderr = ""
    mock_subprocess_run.return_value = mock_res

    # 1. Create a new project ("Test Projet E2E")
    payload = {
        "name": "Test Projet E2E",
        "concept": "A comprehensive end-to-end test story about interstellar exploration."
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 200
    data = response.json()
    pid = data["id"]
    assert pid == "test-projet-e2e"
    assert data["name"] == "Test Projet E2E"

    # 2. Verify that the project directory and seed.txt are created in projects/test-projet-e2e/
    project_dir = Path("projects") / pid
    assert project_dir.exists()
    assert project_dir.is_dir()
    seed_file = project_dir / "seed.txt"
    assert seed_file.exists()
    assert "interstellar exploration" in seed_file.read_text(encoding="utf-8")

    # 3. Test reading and writing lore/foundation files via /api/projects/{id}/files/...
    # Write world.md
    world_payload = {"content": "# World Lore\n\nSector 4 Alpha Centauri."}
    response = client.put(f"/api/projects/{pid}/files/world.md", json=world_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # Read world.md back
    response = client.get(f"/api/projects/{pid}/files/world.md")
    assert response.status_code == 200
    assert "Sector 4 Alpha Centauri" in response.json()["content"]

    # 4. Trigger pipeline phase run via API (verifying absolute path correction in adapter)
    pipeline_payload = {
        "phase": "foundation",
        "project_id": pid
    }
    response = client.post("/api/pipeline/run", json=pipeline_payload)
    assert response.status_code == 200
    pipeline_data = response.json()
    assert pipeline_data.get("returncode") == 0

    # Verify subprocess.run was called with absolute path to run_pipeline.py
    assert mock_subprocess_run.called
    called_cmd = mock_subprocess_run.call_args[0][0]
    expected_script = str(Path(__file__).resolve().parent.parent / "run_pipeline.py")
    assert expected_script in called_cmd

    # 5. Cleanup: Delete project
    response = client.delete(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not project_dir.exists()
