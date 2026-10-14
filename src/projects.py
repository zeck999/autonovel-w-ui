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

class WizardCreate(BaseModel):
    name: str
    concept: str
    genre: str
    tone: str
    protagonist: str
    conflict: str
    world_setting: str
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

def wizard_suggest(field_key: str, current_parameters: Dict[str, str]) -> List[str]:
    suggestions_map = {
        "concept": [
            "A clockwork artisan discovers an illegal cog that controls human memories.",
            "In a world where sunlight is rationed, a botanist grows the first forbidden glowing flower.",
            "An intergalactic archivist finds a manuscript detailing the end of the universe that hasn't happened yet.",
            "A detective investigates murders where the victims' shadows refuse to follow them."
        ],
        "genre": [
            "Cyberpunk / Tech Noir",
            "Epic High Fantasy",
            "Hard Science Fiction",
            "Gothic Mystery / Suspense"
        ],
        "tone": [
            "Dark, Gritty & Atmospheric",
            "Witty, Fast-paced & Adventurous",
            "Melancholic & Philosophical",
            "Suspenseful, Tense & Psychological"
        ],
        "protagonist": [
            "A cynical archival clerk with a hidden robotic arm and a penchant for forbidden lore.",
            "An exiled princess masquerading as a mercenary to reclaim her throne.",
            "A weary starship salvage engineer haunted by a ghost in the machine.",
            "An idealistic magistrate who uncovers systemic corruption in the capital."
        ],
        "conflict": [
            "Stopping a cascading collapse of the planetary power grid before midnight.",
            "Uncovering the conspiracy behind the disappearance of the upper echelons of society.",
            "Escaping a collapsing orbital colony while carrying the last seed bank of Earth.",
            "Proving innocence in a murder where all evidence points to an AI construct."
        ],
        "world_setting": [
            "A multi-tiered vertical city built inside a colossal hollow mountain.",
            "A dying solar system where humanity lives on massive wandering dreadnoughts.",
            "An archipelago of floating islands suspended in a perpetual storm sea.",
            "A subterranean empire powered by geothermal vents and ancient runes."
        ]
    }
    return suggestions_map.get(field_key, [
        "Alternative option A for " + field_key,
        "Alternative option B for " + field_key,
        "Alternative option C for " + field_key,
        "Alternative option D for " + field_key
    ])

def create_project_from_wizard(payload: WizardCreate) -> Dict:
    ensure_projects_dir()
    pid = slugify(payload.name)
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

    # 1. seed.txt
    (p_path / "seed.txt").write_text(payload.concept, encoding="utf-8")

    # 2. world.md
    world_content = f"""# World Setting: {payload.name}

## Overview & Environment
{payload.world_setting}

## Genre & Tone
- **Genre**: {payload.genre}
- **Tone**: {payload.tone}
"""
    (p_path / "world.md").write_text(world_content, encoding="utf-8")

    # 3. characters.md
    chars_content = f"""# Characters & Entities

## Protagonist
{payload.protagonist}

## Central Conflict & Stakes
{payload.conflict}
"""
    (p_path / "characters.md").write_text(chars_content, encoding="utf-8")

    # 4. canon.md
    canon_content = f"""# Story Canon & Rules

- **Core Premise**: {payload.concept}
- **Genre Conventions**: {payload.genre}
- **Atmospheric Tone**: {payload.tone}
"""
    (p_path / "canon.md").write_text(canon_content, encoding="utf-8")

    # 5. outline.md
    outline_content = f"""# Novel Outline: {payload.name}

## Act I: Setup & Inciting Incident
- Introduction of {payload.protagonist} within {payload.world_setting}.
- The emergence of the inciting conflict: {payload.conflict}.

## Act II: Rising Action & Complications
- Exploration of consequences and rising tensions.
- Confronting opposition and secondary obstacles.

## Act III: Climax & Resolution
- The peak confrontation regarding {payload.conflict}.
- Resolution and aftermath.
"""
    (p_path / "outline.md").write_text(outline_content, encoding="utf-8")

    # If universe_id provided, copy shared files
    if payload.universe_id:
        universe_path = BASE_DIR / "universes" / payload.universe_id
        if universe_path.exists():
            for fname in ["world.md", "characters.md", "canon.md"]:
                u_file = universe_path / fname
                if u_file.exists():
                    shutil.copy(u_file, p_path / fname)

    from datetime import datetime
    state = {
        "id": pid,
        "name": payload.name,
        "concept": payload.concept,
        "genre": payload.genre,
        "tone": payload.tone,
        "protagonist": payload.protagonist,
        "conflict": payload.conflict,
        "world_setting": payload.world_setting,
        "universe_id": payload.universe_id,
        "created_at": datetime.now().isoformat(),
        "phase": "foundation",
        "current_focus": "planning",
        "iteration": 0,
        "foundation_score": 0.85,
        "lore_score": 0.80,
        "chapters_drafted": 0,
        "chapters_total": 10,
        "novel_score": 0.0,
        "revision_cycle": 0,
        "debts": []
    }
    state_file = p_path / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    return state

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
