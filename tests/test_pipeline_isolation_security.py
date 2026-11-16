"""Security regressions using only temporary novels and simulated models."""
import json
import subprocess
import sys
import threading
from unittest.mock import patch
import pytest
from src import pipeline_adapter as adapter
from src import versioning
from src.project_context import execute, narrative_git_dir, project_directory


@pytest.fixture
def novels(tmp_path, monkeypatch):
    for name in ("alpha", "beta"):
        project = tmp_path / "projects" / name
        project.mkdir(parents=True)
        (project / "state.json").write_text(json.dumps({"id": name, "phase": "foundation"}))
    monkeypatch.setattr(adapter, "BASE_DIR", tmp_path)
    monkeypatch.setattr(versioning, "BASE_DIR", tmp_path)
    return tmp_path


@pytest.mark.parametrize("phase", ["foundation; touch hacked", "--help", "", "not-a-phase"])
def test_reject_injected_phase(novels, phase):
    with patch.object(adapter, "execute") as run:
        assert adapter.run_pipeline_phase(phase, "alpha")["returncode"] == -1
        run.assert_not_called()


@pytest.mark.parametrize("identifier", [None, "..", "../alpha", "/tmp", "alpha/beta"])
def test_reject_project_traversal(novels, identifier):
    with patch.object(adapter, "execute") as run:
        assert adapter.run_pipeline_phase("foundation", identifier)["returncode"] == -1
        run.assert_not_called()


def test_project_symlink_escape(novels, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (novels / "projects" / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        project_directory("escape", novels / "projects")


def test_no_global_sync(novels):
    (novels / "world.md").write_text("ROOT")
    alpha = novels / "projects" / "alpha"
    (alpha / "world.md").write_text("ALPHA")
    assert adapter.sync_project_to_root("alpha")["success"]
    assert (novels / "world.md").read_text() == "ROOT"
    assert adapter.sync_root_to_project("beta")["success"]
    assert not (novels / "projects" / "beta" / "world.md").exists()


def test_concurrent_same_project_rejected(novels):
    lock = adapter._lock(novels / "projects" / "alpha")
    with lock, patch.object(adapter, "execute") as run:
        assert "already running" in adapter.run_pipeline_phase("foundation", "alpha")["error"]
        assert adapter.run_pipeline_phase("foundation", "beta")["returncode"] != -1


def test_timeout_reported(novels):
    with patch.object(adapter, "execute", side_effect=subprocess.TimeoutExpired([], 1)):
        assert "timed out" in adapter.run_pipeline_phase("foundation", "alpha")["error"]


def test_score_json_protocol():
    assert adapter._score('log\n{\n "overall_score": 8.1\n}') == 8.1
    assert adapter._score('{"novel_score": 7.2}') == 7.2
    assert adapter._score('no score') is None


def test_git_cannot_use_application_repository(novels):
    with pytest.raises(ValueError):
        versioning.create_branch("test")
    with pytest.raises(ValueError):
        narrative_git_dir(novels)


def test_narrative_git_and_failure(novels):
    assert versioning.create_branch("draft-two", "alpha")
    assert "draft-two" in versioning.list_branches("alpha")
    assert (novels / "projects" / "alpha" / ".git").is_dir()
    assert not (novels / "projects" / "beta" / ".git").exists()
    with pytest.raises(ValueError):
        versioning.create_branch("draft-two", "alpha")
    with pytest.raises(ValueError):
        versioning.switch_branch("nonexistent", "alpha")


def test_process_timeout_stops_child(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired):
        execute([sys.executable, "-c", "import time;time.sleep(30)"], cwd=tmp_path, timeout=0.05)
