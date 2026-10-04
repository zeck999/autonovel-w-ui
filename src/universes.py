"""
src/universes.py — Shared universes management for Autonovel series and spin-offs.
Manages universes under universes/ directory containing shared world.md, characters.md, and canon.md.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
UNIVERSES_DIR = BASE_DIR / "universes"

class UniverseCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class UniverseResponse(BaseModel):
    id: str
    name: str
    description: str
    projects_count: int

def ensure_universes_dir():
    UNIVERSES_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text or "universe"

def list_universes() -> List[Dict]:
    ensure_universes_dir()
    universes = []
    if not UNIVERSES_DIR.exists():
        return universes
    for u_dir in UNIVERSES_DIR.iterdir():
        if u_dir.is_dir():
            state_file = u_dir / "state.json"
            meta = {
                "id": u_dir.name,
                "name": u_dir.name,
                "description": "",
                "projects_count": 0
            }
            if state_file.exists():
                try:
                    with open(state_file, "r") as f:
                        data = json.load(f)
                        meta.update(data)
                except Exception:
                    pass
            # Count projects linked to this universe
            projects_dir = BASE_DIR / "projects"
            count = 0
            if projects_dir.exists():
                for p_dir in projects_dir.iterdir():
                    if p_dir.is_dir():
                        p_state = p_dir / "state.json"
                        if p_state.exists():
                            try:
                                with open(p_state) as pf:
                                    pdata = json.load(pf)
                                    if pdata.get("universe_id") == u_dir.name:
                                        count += 1
                            except Exception:
                                pass
            meta["projects_count"] = count
            universes.append(meta)
    return universes

def create_universe(name: str, description: str = "") -> Dict:
    ensure_universes_dir()
    uid = slugify(name)
    u_path = UNIVERSES_DIR / uid
    counter = 1
    base_uid = uid
    while u_path.exists():
        uid = f"{base_uid}-{counter}"
        u_path = UNIVERSES_DIR / uid
        counter += 1

    u_path.mkdir(parents=True, exist_ok=True)

    # Initialize shared files if they don't exist
    for fname, default_content in [
        ("world.md", f"# Shared Universe: {name}\n\n## Lore & Geography\n\n"),
        ("characters.md", f"# Shared Characters: {name}\n\n## Registry\n\n"),
        ("canon.md", f"# Shared Canon: {name}\n\n## Hard Facts\n\n")
    ]:
        f_path = u_path / fname
        if not f_path.exists():
            f_path.write_text(default_content)

    state = {
        "id": uid,
        "name": name,
        "description": description
    }
    state_file = u_path / "state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    return {**state, "projects_count": 0}

def get_universe(universe_id: str) -> Optional[Dict]:
    u_path = UNIVERSES_DIR / universe_id
    if not u_path.exists() or not u_path.is_dir():
        return None
    state_file = u_path / "state.json"
    state = {
        "id": universe_id,
        "name": universe_id,
        "description": ""
    }
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
                state.update(data)
        except Exception:
            pass
    return state

def delete_universe(universe_id: str) -> bool:
    u_path = UNIVERSES_DIR / universe_id
    if u_path.exists() and u_path.is_dir():
        shutil.rmtree(u_path)
        return True
    return False
