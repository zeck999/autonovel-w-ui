"""Pipeline adapter contracts; no model calls or repository data writes."""
import json
import subprocess
from unittest.mock import patch
import pytest
from src import pipeline_adapter as adapter


@pytest.fixture
def novel(tmp_path, monkeypatch):
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "state.json").write_text('{"phase":"foundation"}')
    monkeypatch.setattr(adapter, "BASE_DIR", tmp_path)
    return project


def test_get_pipeline_status(novel):
    assert adapter.get_pipeline_status("demo")["phase"] == "foundation"


def test_run_pipeline_phase_success(novel):
    with patch.object(adapter, "execute", return_value=subprocess.CompletedProcess([], 0, "ok", "")) as run:
        result = adapter.run_pipeline_phase("foundation", "demo")
    assert result["returncode"] == 0
    args = run.call_args.args[0]
    assert args[1] == str(adapter.BASE_DIR / "run_pipeline.py")
    assert run.call_args.kwargs["cwd"] == novel
    assert run.call_args.kwargs["env"]["AUTONOVEL_PROJECT_DIR"] == str(novel)


def test_run_pipeline_phase_error(novel):
    with patch.object(adapter, "execute", return_value=subprocess.CompletedProcess([], 1, "", "Pipeline failure")):
        result = adapter.run_pipeline_phase("foundation", "demo")
    assert result["returncode"] == 1
    assert "Pipeline failure" in result["error"]


def test_evaluate_project_command(novel):
    with patch.object(adapter, "execute", return_value=subprocess.CompletedProcess([], 0, json.dumps({"overall_score":8.5}, indent=2), "")) as run:
        result = adapter.evaluate_project("demo")
    assert result["score"] == 8.5
    assert run.call_args.args[0][1] == str(adapter.BASE_DIR / "evaluate.py")
    assert json.loads((novel / "state.json").read_text())["novel_score"] == 8.5


def test_pipeline_requires_project(novel):
    with patch.object(adapter, "execute") as run:
        assert adapter.run_pipeline_phase("foundation")["returncode"] == -1
        run.assert_not_called()


def test_judge_error_is_scoped(novel):
    (novel / "state.json").write_text('{"error_code":"ERR_JUDGE_UNAUTHORIZED_401"}')
    root_state = adapter.BASE_DIR / "state.json"
    before = root_state.read_bytes() if root_state.exists() else None
    with patch.object(adapter, "execute", return_value=subprocess.CompletedProcess([], 1, "", "Unauthorized")):
        result = adapter.evaluate_project("demo")
    assert result["error_code"] == "ERR_JUDGE_UNAUTHORIZED_401"
    assert (root_state.read_bytes() if root_state.exists() else None) == before
