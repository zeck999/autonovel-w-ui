"""
Comprehensive E2E validation of the AI keys settings user journey against FastAPI application.
Verifies GET /api/settings/keys, PUT /api/settings/keys, and POST /api/settings/keys/test.
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_ai_keys_settings_e2e_journey():
    # Step 1: Initial GET /api/settings/keys
    res_get = client.get("/api/settings/keys")
    assert res_get.status_code == 200, f"Expected 200, got {res_get.status_code}"
    initial_data = res_get.json()
    assert isinstance(initial_data, dict)
    for k in ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "FAL_KEY"]:
        assert k in initial_data
        assert "configured" in initial_data[k]
        assert "masked_value" in initial_data[k]

    # Step 2: PUT /api/settings/keys with test API keys
    payload_update = {
        "anthropic_api_key": "sk-ant-e2etestkey987654321",
        "elevenlabs_api_key": "eleven_e2e_test_key_xyz",
        "fal_key": "fal_e2e_test_key_abc"
    }
    res_put = client.put("/api/settings/keys", json=payload_update)
    assert res_put.status_code == 200, f"Expected 200, got {res_put.status_code}"
    put_data = res_put.json()
    assert put_data.get("status") == "updated"
    assert put_data["keys"]["ANTHROPIC_API_KEY"]["configured"] is True
    assert "321" in put_data["keys"]["ANTHROPIC_API_KEY"]["masked_value"]

    # Step 3: Verify GET /api/settings/keys after update
    res_get_updated = client.get("/api/settings/keys")
    assert res_get_updated.status_code == 200
    updated_data = res_get_updated.json()
    assert updated_data["ANTHROPIC_API_KEY"]["configured"] is True
    assert updated_data["ELEVENLABS_API_KEY"]["configured"] is True
    assert updated_data["FAL_KEY"]["configured"] is True

    # Step 4: POST /api/settings/keys/test for each provider (valid & invalid)
    providers = [
        ("anthropic", "sk-ant-validtestkey12345", True),
        ("anthropic", "invalid-key", False),
        ("elevenlabs", "elevenlabsvalidkey12345", True),
        ("elevenlabs", "short", False),
        ("fal", "faltestkeyvalid12345678", True),
        ("fal", "bad", False)
    ]

    for provider, api_key, expected_success in providers:
        test_payload = {
            "provider": provider,
            "api_key": api_key
        }
        res_test = client.post("/api/settings/keys/test", json=test_payload)
        assert res_test.status_code == 200, f"Provider {provider} failed with status {res_test.status_code}"
        test_result = res_test.json()
        assert "success" in test_result
        assert test_result["success"] == expected_success, f"Provider {provider} with key '{api_key}' expected success={expected_success}, got {test_result}"
        assert "message" in test_result
        assert "latency_ms" in test_result
        assert isinstance(test_result["latency_ms"], int)
        assert test_result["latency_ms"] >= 0

    print("E2E AI Keys Settings user journey successfully validated!")
