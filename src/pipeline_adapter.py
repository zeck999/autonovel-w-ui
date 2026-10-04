"""
src/pipeline_adapter.py — Integration adapter with existing Autonovel scripts.
Invokes run_pipeline.py, evaluate.py, and manages pipeline execution per project.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent

def get_pipeline_status(project_id: Optional[str] = None) -> Dict:
    state_file = BASE_DIR / "state.json"
    if project_id:
        p_state = BASE_DIR / "projects" / project_id / "state.json"
        if p_state.exists():
            state_file = p_state

    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "phase": "foundation",
        "current_focus": "planning",
        "iteration": 0,
        "foundation_score": 0.0,
        "chapters_drafted": 0,
        "chapters_total": 0,
        "novel_score": 0.0,
        "revision_cycle": 0
    }

def run_pipeline_phase(phase: str, project_id: Optional[str] = None, max_cycles: Optional[int] = None) -> Dict:
    cmd = f"uv run python run_pipeline.py --phase {phase}"
    if max_cycles is not None:
        cmd += f" --max-cycles {max_cycles}"

    cwd = BASE_DIR
    if project_id:
        p_path = BASE_DIR / "projects" / project_id
        if p_path.exists():
            # If running in project context, we can point or copy state
            cwd = p_path

    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=300)
        status = get_pipeline_status(project_id)
        status["last_run_output"] = res.stdout[-500:] if res.stdout else ""
        status["last_run_returncode"] = res.returncode
        return status
    except subprocess.TimeoutExpired:
        return {"error": "Pipeline phase timed out", "returncode": -1}
    except Exception as e:
        return {"error": str(e), "returncode": -1}

def evaluate_project(project_id: Optional[str] = None, chapter_num: Optional[int] = None) -> Dict:
    cmd = "uv run python evaluate.py"
    if chapter_num is not None:
        cmd += f" --chapter={chapter_num}"
    else:
        cmd += " --full"

    cwd = BASE_DIR
    if project_id:
        p_path = BASE_DIR / "projects" / project_id
        if p_path.exists():
            cwd = p_path

    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=120)
        return {
            "returncode": res.returncode,
            "output": res.stdout,
            "error": res.stderr
        }
    except Exception as e:
        return {"returncode": -1, "output": "", "error": str(e)}
