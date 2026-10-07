"""
src/projects.py — Multi-project management for Autonovel.
Supports creating, listing, retrieving, updating, and deleting isolated projects under projects/ directory.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"

class ProjectCreate(BaseModel):
    name: str
    concept: str
    universe_id: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    concept: str
    universe_id: Optional[str] = None
    created_at: str
    phase: str
    chapters_drafted: int
    chapters_total: int

def ensure_projects_dir():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text or "project"

def list_projects() -> List[Dict]:
    ensure_projects_dir()
    projects = []
    if not PROJECTS_DIR.exists():
        return projects
    for p_dir in PROJECTS_DIR.iterdir():
        if p_dir.is_dir():
            state_file = p_dir / "state.json"
            meta = {
                "id": p_dir.name,
                "name": p_dir.name,
                "concept": "",
                "universe_id": None,
                "created_at": "",
                "phase": "foundation",
                "chapters_drafted": 0,
                "chapters_total": 0
            }
            if state_file.exists():
                try:
                    with open(state_file, "r") as f:
                        data = json.load(f)
                        meta.update(data)
                except Exception:
                    pass
            seed_file = p_dir / "seed.txt"
            if seed_file.exists() and not meta.get("concept"):
                meta["concept"] = seed_file.read_text().strip()
            projects.append(meta)
    return projects

def create_project(name: str, concept: str, universe_id: Optional[str] = None) -> Dict:
    ensure_projects_dir()
    pid = slugify(name)
    # Ensure uniqueness
    p_path = PROJECTS_DIR / pid
    counter = 1
    base_pid = pid
    while p_path.exists():
        pid = f"{base_pid}-{counter}"
        p_path = PROJECTS_DIR / pid
        counter += 1

    p_path.mkdir(parents=True, exist_ok=True)
    (p_path / "chapters").mkdir(exist_ok=True)
    (p_path / "briefs").mkdir(exist_ok=True)
    (p_path / "edit_logs").mkdir(exist_ok=True)
    (p_path / "eval_logs").mkdir(exist_ok=True)

    # Save seed.txt
    seed_file = p_path / "seed.txt"
    seed_file.write_text(concept)

    # If universe_id provided, link/copy initial shared universe files if available
    if universe_id:
        universe_path = BASE_DIR / "universes" / universe_id
        if universe_path.exists():
            for fname in ["world.md", "characters.md", "canon.md"]:
                u_file = universe_path / fname
                if u_file.exists():
                    shutil.copy(u_file, p_path / fname)

    # Initial state.json
    from datetime import datetime
    state = {
        "id": pid,
        "name": name,
        "concept": concept,
        "universe_id": universe_id,
        "created_at": datetime.now().isoformat(),
        "phase": "foundation",
        "current_focus": "planning",
        "iteration": 0,
        "foundation_score": 0.0,
        "lore_score": 0.0,
        "chapters_drafted": 0,
        "chapters_total": 0,
        "novel_score": 0.0,
        "revision_cycle": 0,
        "debts": []
    }
    state_file = p_path / "state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    return state

def get_project(project_id: str) -> Optional[Dict]:
    p_path = PROJECTS_DIR / project_id
    if not p_path.exists() or not p_path.is_dir():
        return None
    state_file = p_path / "state.json"
    state = {
        "id": project_id,
        "name": project_id,
        "concept": "",
        "universe_id": None,
        "created_at": "",
        "phase": "foundation",
        "chapters_drafted": 0,
        "chapters_total": 0
    }
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
                state.update(data)
        except Exception:
            pass
    seed_file = p_path / "seed.txt"
    if seed_file.exists() and not state.get("concept"):
        state["concept"] = seed_file.read_text().strip()
    return state

def delete_project(project_id: str) -> bool:
    p_path = PROJECTS_DIR / project_id
    if p_path.exists() and p_path.is_dir():
        shutil.rmtree(p_path)
        return True
    return False

STANDARD_PROJECT_FILES = ["seed.txt", "world.md", "characters.md", "outline.md", "canon.md"]

def list_project_files(project_id: str) -> List[Dict]:
    ensure_projects_dir()
    p_path = PROJECTS_DIR / project_id
    if not p_path.exists():
        return []
    files = []
    seen = set()
    for fname in STANDARD_PROJECT_FILES:
        seen.add(fname)
        f_path = p_path / fname
        files.append({
            "name": fname,
            "exists": f_path.exists(),
            "size": f_path.stat().st_size if f_path.exists() else 0
        })
    for item in p_path.iterdir():
        if item.is_file() and item.name not in seen and item.suffix in [".md", ".txt", ".json"]:
            seen.add(item.name)
            files.append({
                "name": item.name,
                "exists": True,
                "size": item.stat().st_size
            })
    chapters_dir = p_path / "chapters"
    if chapters_dir.exists() and chapters_dir.is_dir():
        for item in sorted(chapters_dir.iterdir()):
            if item.is_file() and item.suffix in [".md", ".txt", ".json"]:
                rel_name = f"chapters/{item.name}"
                seen.add(rel_name)
                files.append({
                    "name": rel_name,
                    "exists": True,
                    "size": item.stat().st_size
                })
    return files

def get_project_file(project_id: str, filename: str) -> Optional[str]:
    ensure_projects_dir()
    p_path = PROJECTS_DIR / project_id
    if not p_path.exists():
        return None
    f_path = (p_path / filename).resolve()
    if not str(f_path).startswith(str(p_path.resolve())):
        return None
    if not f_path.exists():
        if filename in STANDARD_PROJECT_FILES or f_path.suffix in [".md", ".txt"]:
            return ""
        return None
    try:
        return f_path.read_text(encoding="utf-8")
    except Exception:
        return None

def save_project_file(project_id: str, filename: str, content: str) -> bool:
    ensure_projects_dir()
    p_path = PROJECTS_DIR / project_id
    if not p_path.exists():
        return False
    f_path = (p_path / filename).resolve()
    if not str(f_path).startswith(str(p_path.resolve())):
        return False
    try:
        f_path.parent.mkdir(parents=True, exist_ok=True)
        f_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False
