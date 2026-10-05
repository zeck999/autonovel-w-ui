"""
src/pipeline_adapter.py — Integration adapter with existing Autonovel scripts.
Invokes run_pipeline.py, evaluate.py, and manages pipeline execution per project.
"""

import subprocess
import json
import re
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
    script_to_run = "run_pipeline.py"
    actual_phase = phase

    if phase == "outline":
        script_to_run = "gen_outline.py"
    elif phase == "draft":
        actual_phase = "drafting"
    elif phase == "review":
        script_to_run = "evaluate.py"
    elif phase == "revise":
        actual_phase = "revision"
    elif phase == "typeset":
        actual_phase = "export"
    elif phase == "audiobook":
        script_to_run = "gen_audiobook.py"

    if script_to_run == "run_pipeline.py":
        cmd = f"uv run python {BASE_DIR / 'run_pipeline.py'} --phase {actual_phase}"
    elif script_to_run == "evaluate.py":
        cmd = f"uv run python {BASE_DIR / 'evaluate.py'} --full"
    else:
        cmd = f"uv run python {BASE_DIR / script_to_run}"

    if max_cycles is not None and script_to_run == "run_pipeline.py":
        cmd += f" --max-cycles {max_cycles}"

    cwd = BASE_DIR
    if project_id:
        p_path = BASE_DIR / "projects" / project_id
        if p_path.exists():
            cwd = p_path

    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=300)
        status = get_pipeline_status(project_id)
        if res.returncode == 0:
            status["phase"] = phase
        status["last_run_output"] = res.stdout[-500:] if res.stdout else ""
        status["last_run_returncode"] = res.returncode
        status["returncode"] = res.returncode
        if res.returncode != 0:
            status["error"] = res.stderr[-500:] if res.stderr else f"Pipeline failed with return code {res.returncode}"
        return status
    except subprocess.TimeoutExpired:
        return {"error": "Pipeline phase timed out", "returncode": -1}
    except Exception as e:
        return {"error": str(e), "returncode": -1}

def evaluate_project(project_id: Optional[str] = None, chapter_num: Optional[int] = None) -> Dict:
    script_path = BASE_DIR / "evaluate.py"
    cmd = f"uv run python {script_path}"
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
        score = None
        match = re.search(r'(?:overall_score|novel_score):\s*([0-9.]+)', res.stdout)
        if match:
            try:
                score = float(match.group(1))
            except ValueError:
                pass

        return {
            "returncode": res.returncode,
            "output": res.stdout,
            "error": res.stderr if res.returncode != 0 else None,
            "score": score
        }
    except Exception as e:
        return {"returncode": -1, "output": "", "error": str(e), "score": None}
