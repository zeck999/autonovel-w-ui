"""
src/pipeline_adapter.py — Integration adapter with existing Autonovel scripts.
Invokes run_pipeline.py, evaluate.py, and manages pipeline execution per project.
"""

import subprocess
import json
import re
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

# Liste des fichiers et dossiers à synchroniser
SYNC_FILES_AND_DIRS = [
    "seed.txt",
    "state.json",
    "world.md",
    "characters.md",
    "outline.md",
    "canon.md",
    "voice.md",
    "chapters/",
    "briefs/",
    "edit_logs/",
    "eval_logs/"
]

def sync_project_to_root(project_id: str) -> Dict:
    """
    Synchronise les fichiers du projet vers la racine (BASE_DIR).
    Copie les fichiers depuis projects/{id}/ vers BASE_DIR.
    """
    try:
        project_dir = BASE_DIR / "projects" / project_id
        if not project_dir.exists():
            return {"success": False, "error": f"Project directory {project_dir} does not exist"}
        
        sync_results = []
        for item in SYNC_FILES_AND_DIRS:
            src = project_dir / item.rstrip('/')
            dst = BASE_DIR / item.rstrip('/')
            
            if src.exists():
                # Pour les dossiers, on utilise copytree avec overwrite
                if src.is_dir():
                    # Créer le dossier de destination si nécessaire
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    # Copier récursivement
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    sync_results.append(f"Copied directory: {item}")
                else:
                    # Pour les fichiers
                    shutil.copy2(src, dst)
                    sync_results.append(f"Copied file: {item}")
        
        logger.info(f"Synchronized project {project_id} to root: {len(sync_results)} items")
        return {
            "success": True,
            "items_synced": sync_results,
            "project_id": project_id,
            "direction": "project_to_root"
        }
    except Exception as e:
        logger.error(f"Error syncing project {project_id} to root: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id,
            "direction": "project_to_root"
        }

def sync_root_to_project(project_id: str) -> Dict:
    """
    Synchronise les fichiers de la racine (BASE_DIR) vers le projet.
    Copie les fichiers depuis BASE_DIR vers projects/{id}/.
    """
    try:
        project_dir = BASE_DIR / "projects" / project_id
        if not project_dir.exists():
            return {"success": False, "error": f"Project directory {project_dir} does not exist"}
        
        sync_results = []
        for item in SYNC_FILES_AND_DIRS:
            src = BASE_DIR / item.rstrip('/')
            dst = project_dir / item.rstrip('/')
            
            if src.exists():
                # Pour les dossiers, on utilise copytree avec overwrite
                if src.is_dir():
                    # Créer le dossier de destination si nécessaire
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    # Copier récursivement
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    sync_results.append(f"Copied directory: {item}")
                else:
                    # Pour les fichiers
                    shutil.copy2(src, dst)
                    sync_results.append(f"Copied file: {item}")
        
        logger.info(f"Synchronized root to project {project_id}: {len(sync_results)} items")
        return {
            "success": True,
            "items_synced": sync_results,
            "project_id": project_id,
            "direction": "root_to_project"
        }
    except Exception as e:
        logger.error(f"Error syncing root to project {project_id}: {e}")

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
    """
    Exécute une phase du pipeline avec synchronisation bidirectionnelle.
    """
    # 1. Synchronisation avant exécution (projet → racine)
    sync_before = None
    if project_id:
        sync_before = sync_project_to_root(project_id)
        if not sync_before.get("success", False):
            logger.warning(f"Sync before pipeline failed: {sync_before.get('error')}")
    
    # Déterminer le script à exécuter
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

    # Construire la commande
    if script_to_run == "run_pipeline.py":
        cmd = f"uv run python {BASE_DIR / 'run_pipeline.py'} --phase {actual_phase}"
    elif script_to_run == "evaluate.py":
        cmd = f"uv run python {BASE_DIR / 'evaluate.py'} --full"
    else:
        cmd = f"uv run python {BASE_DIR / script_to_run}"

    if max_cycles is not None and script_to_run == "run_pipeline.py":
        cmd += f" --max-cycles {max_cycles}"

    # Toujours exécuter depuis BASE_DIR après la synchronisation
    cwd = BASE_DIR

    try:
        # 2. Exécuter le pipeline
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=300)
        
        # 3. Synchronisation après exécution (racine → projet)
        sync_after = None
        if project_id:
            sync_after = sync_root_to_project(project_id)
            if not sync_after.get("success", False):
                logger.warning(f"Sync after pipeline failed: {sync_after.get('error')}")
        
        # Récupérer le statut
        status = get_pipeline_status(project_id)
        if res.returncode == 0:
            status["phase"] = phase
            status.pop("error", None)
            status.pop("error_code", None)
        
        # Ajouter les informations de sortie
        status["last_run_output"] = res.stdout[-500:] if res.stdout else ""
        status["last_run_returncode"] = res.returncode
        status["returncode"] = res.returncode
        
        # Ajouter les informations de synchronisation
        if project_id:
            status["sync_before"] = sync_before
            status["sync_after"] = sync_after
        
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

        error_code = None
        for code in ["ERR_JUDGE_UNAUTHORIZED_401", "ERR_JUDGE_RATE_LIMIT_429", "ERR_JUDGE_TIMEOUT", "ERR_JUDGE_NETWORK_ERROR", "ERR_JUDGE_ERROR"]:
            if code in res.stdout or code in res.stderr:
                error_code = code
                break
        if not error_code and res.returncode != 0:
            error_code = "ERR_JUDGE_ERROR"

        # Update state.json in lease / project / root
        state_files = [BASE_DIR / "state.json"]
        if project_id:
            p_state = BASE_DIR / "projects" / project_id / "state.json"
            if p_state.exists():
                state_files.append(p_state)

        for sf in state_files:
            if sf.exists():
                try:
                    with open(sf, "r") as f:
                        st = json.load(f)
                    if error_code:
                        st["error_code"] = error_code
                        st["error"] = res.stderr or res.stdout[-300:]
                    else:
                        st.pop("error_code", None)
                        st.pop("error", None)
                    with open(sf, "w") as f:
                        json.dump(st, f, indent=2)
                except Exception:
                    pass

        return {
            "returncode": res.returncode,
            "output": res.stdout,
            "error": res.stderr if res.returncode != 0 else None,
            "error_code": error_code,
            "score": score
        }
    except Exception as e:
        return {"returncode": -1, "output": "", "error": str(e), "error_code": "ERR_JUDGE_EXCEPTION", "score": None}
