"""
Unit tests for chapter modification with AI endpoint (/api/projects/{id}/chapters/modify)
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_chapter_modify_missing_key():
    # Create a project first
    res = client.post("/api/projects", json={"name": "AI Test Novel", "concept": "Concept for AI test"})
    assert res.status_code == 200
    pid = res.json()["id"]

    # Ensure ANTHROPIC_API_KEY is not set or placeholder
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "your-key-here"}):
        response = client.post(
            f"/api/projects/{pid}/chapters/modify",
            json={
                "file_path": "chapters/chapter_01.md",
                "content": "# Chapter 1\n\nOriginal text.",
                "prompt": "Make it more suspenseful."
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "ERR_AI_MOD_KEY_MISSING" in data["detail"]

    # Cleanup
    client.delete(f"/api/projects/{pid}")

def test_chapter_modify_project_not_found():
    response = client.post(
        "/api/projects/non-existent-proj/chapters/modify",
        json={
            "file_path": "chapters/chapter_01.md",
            "content": "Test",
            "prompt": "Test prompt"
        }
    )
    assert response.status_code == 404

def test_chapter_modify_success_mock():
    res = client.post("/api/projects", json={"name": "AI Success Novel", "concept": "Concept for AI success"})
    assert res.status_code == 200
    pid = res.json()["id"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"text": "# Chapter 1\n\nAI Modified text with suspense."}]
    }

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-testkey12345"}):
        with patch("httpx.post", return_value=mock_response):
            response = client.post(
                f"/api/projects/{pid}/chapters/modify",
                json={
                    "file_path": "chapters/chapter_01.md",
                    "content": "# Chapter 1\n\nOriginal text.",
                    "prompt": "Make it more suspenseful."
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "AI Modified text" in data["content"]

    # Cleanup
    client.delete(f"/api/projects/{pid}")
