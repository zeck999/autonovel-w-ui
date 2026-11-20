"""Run application scripts against explicitly isolated novel directories."""
import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, Optional
from src.project_context import execute, project_directory, ensure_data_editable, notify_data_changed, _narrative_fingerprint

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()
PHASES = {
    "foundation": ("run_pipeline.py", "foundation"),
    "drafting": ("run_pipeline.py", "drafting"),
    "draft": ("run_pipeline.py", "drafting"),
    "revision": ("run_pipeline.py", "revision"),
    "revise": ("run_pipeline.py", "revision"),
    "export": ("run_pipeline.py", "export"),
    "typeset": ("run_pipeline.py", "export"),
    "outline": ("gen_outline.py", None),
    "review": ("evaluate.py", "--full"),
    "audiobook": ("gen_audiobook.py", None),
}


def _project(project_id):
    return project_directory(project_id, Path(os.environ.get("AUTONOVEL_APP_DATA_DIR", BASE_DIR)) / "projects")


def _lock(directory):
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(str(directory), threading.Lock())


def sync_project_to_root(project_id: str) -> Dict:
    """Compatibility shim: no global copying is ever performed."""
    try:
        _project(project_id)
        return {"success": True, "items_synced": [], "isolated": True}
    except ValueError as exc:
        return {"success": False, "error": str(exc)}


sync_root_to_project = sync_project_to_root


def get_pipeline_status(project_id: Optional[str] = None) -> Dict:
    directory = _project(project_id) if project_id else BASE_DIR
    path = directory / "state.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"phase": "foundation", "current_focus": "planning", "iteration": 0,
            "foundation_score": 0.0, "chapters_drafted": 0,
            "chapters_total": 0, "novel_score": 0.0, "revision_cycle": 0}


def _score(output):
    """Prefer the explicit JSON protocol; accept pretty-printed CLI JSON too."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(output):
        if char != "{":
            continue
        try:
            result, _ = decoder.raw_decode(output[index:])
        except ValueError:
            continue
        for key in ("overall_score", "novel_score", "foundation_score"):
            value = result.get(key) if isinstance(result, dict) else None
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return None


def _run(project_id, args, timeout, *, record_score=False):
    directory = _project(project_id)
    if not record_score:
        ensure_data_editable(directory)
    before = _narrative_fingerprint(directory)
    lock = _lock(directory)
    if not lock.acquire(blocking=False):
        return {"error": "A task is already running for this project", "returncode": -1}
    try:
        env = dict(os.environ, AUTONOVEL_PROJECT_DIR=str(directory))
        result = execute([sys.executable, *args], cwd=directory, timeout=timeout, env=env)
        status = get_pipeline_status(project_id)
        if record_score and result.returncode == 0:
            score = _score(result.stdout)
            if score is None:
                raise ValueError("Evaluation did not return a numeric JSON score")
            status["novel_score"] = score
            state = dict(status)
            state.pop("error", None)
            state.pop("error_code", None)
            temporary = directory / "state.json.tmp"
            temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
            temporary.replace(directory / "state.json")
        status.update(last_run_output=result.stdout[-4000:],
                      last_run_returncode=result.returncode, returncode=result.returncode)
        if result.returncode:
            status["error"] = result.stderr[-2000:] or "Pipeline execution failed"
        else:
            status.pop("error", None)
            status.pop("error_code", None)
        return status
    except subprocess.TimeoutExpired:
        return {"error": "Operation timed out; subprocess group stopped", "returncode": -1}
    finally:
        lock.release()
        if _narrative_fingerprint(directory) != before:
            notify_data_changed(directory)


def run_pipeline_phase(phase: str, project_id: Optional[str] = None,
                       max_cycles: Optional[int] = None) -> Dict:
    try:
        if phase not in PHASES:
            raise ValueError("Unsupported pipeline phase")
        if max_cycles is not None and (isinstance(max_cycles, bool) or not 1 <= max_cycles <= 6):
            raise ValueError("max_cycles must be between 1 and 6")
        script, option = PHASES[phase]
        args = [str(BASE_DIR / script)]
        if script == "run_pipeline.py":
            args += ["--phase", option]
            if max_cycles is not None:
                args += ["--max-cycles", str(max_cycles)]
        elif option:
            args.append(option)
        # A complete phase contains many model calls; API jobs own its lifetime.
        return _run(project_id, args, timeout=6 * 60 * 60)
    except (ValueError, OSError) as exc:
        return {"error": str(exc), "returncode": -1}


def evaluate_project(project_id: Optional[str] = None, chapter_num: Optional[int] = None) -> Dict:
    try:
        if chapter_num is not None and (isinstance(chapter_num, bool) or chapter_num < 1):
            raise ValueError("chapter_num must be positive")
        args = [str(BASE_DIR / "evaluate.py"),
                f"--chapter={chapter_num}" if chapter_num is not None else "--full"]
        status = _run(project_id, args, timeout=900, record_score=True)
        status["score"] = status.get("novel_score") if status.get("returncode") == 0 else None
        status["output"] = status.get("last_run_output", "")
        return status
    except (ValueError, OSError) as exc:
        return {"error": str(exc), "returncode": -1}
