"""
Unit and integration tests for settings and AI key testing endpoints (src/settings.py and /api/settings/*)
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.settings import get_api_keys_status, update_api_keys, verify_api_key

client = TestClient(app)

def test_get_settings_keys():
    response = client.get("/api/settings/keys")
    assert response.status_code == 200
    data = response.json()
    assert "ANTHROPIC_API_KEY" in data
    assert "ELEVENLABS_API_KEY" in data
    assert "FAL_KEY" in data
    assert "configured" in data["ANTHROPIC_API_KEY"]
    assert "masked_value" in data["ANTHROPIC_API_KEY"]

def test_update_settings_keys():
    payload = {
        "anthropic_api_key": "sk-ant-testkey1234567890",
        "elevenlabs_api_key": "eleven_test_key_abc123",
        "fal_key": "fal_test_key_xyz789"
    }
    response = client.put("/api/settings/keys", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["keys"]["ANTHROPIC_API_KEY"]["configured"] is True
    assert "****" in data["keys"]["ANTHROPIC_API_KEY"]["masked_value"]

def test_test_settings_key():
    payload = {
        "provider": "anthropic",
        "api_key": "sk-ant-testkey1234567890"
    }
    response = client.post("/api/settings/keys/test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "latency_ms" in data

def test_test_invalid_key():
    payload = {
        "provider": "anthropic",
        "api_key": "your-key-here"
    }
    response = client.post("/api/settings/keys/test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
