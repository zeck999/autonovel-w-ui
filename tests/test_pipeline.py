"""
Unit tests for src/pipeline_adapter.py and pipeline execution
"""

import pytest
from unittest.mock import patch, MagicMock
from src.pipeline_adapter import run_pipeline_phase, evaluate_project, get_pipeline_status, BASE_DIR
from src.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_pipeline_status():
    status = get_pipeline_status()
    assert isinstance(status, dict)
    assert "phase" in status

@patch("src.pipeline_adapter.subprocess.run")
def test_run_pipeline_phase_success(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Pipeline success"
    mock_run.return_value = mock_res

    res = run_pipeline_phase("foundation")
    assert res["returncode"] == 0
    assert "error" not in res or res.get("error") is None

    # Verify absolute path was used in command
    called_cmd = mock_run.call_args[0][0]
    expected_script = str(BASE_DIR / "run_pipeline.py")
    assert expected_script in called_cmd

@patch("src.pipeline_adapter.subprocess.run")
def test_run_pipeline_phase_error(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = ""
    mock_res.stderr = "Traceback: Error in pipeline"
    mock_run.return_value = mock_res

    res = run_pipeline_phase("foundation")
    assert res["returncode"] == 1
    assert "error" in res
    assert "Error in pipeline" in res["error"]

@patch("src.pipeline_adapter.subprocess.run")
def test_evaluate_project_command(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Evaluation passed\noverall_score: 8.5"
    mock_res.stderr = ""
    mock_run.return_value = mock_res

    res = evaluate_project()
    assert res["returncode"] == 0
    assert res["score"] == 8.5
    called_cmd = mock_run.call_args[0][0]
    assert str(BASE_DIR / "evaluate.py") in called_cmd

@patch("src.pipeline_adapter.subprocess.run")
def test_api_pipeline_run_error_raises_400(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = ""
    mock_res.stderr = "Pipeline failure"
    mock_run.return_value = mock_res

    response = client.post("/api/pipeline/run", json={"phase": "foundation"})
    assert response.status_code == 400
    assert "detail" in response.json()
