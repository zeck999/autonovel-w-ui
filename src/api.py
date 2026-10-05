"""
src/api.py — FastAPI application exposing REST endpoints for Autonovel Web UI and harness.
Covers multi-project management, shared universes, narrative versioning, and pipeline control,
plus serving the Autonovel Web UI (HTML/CSS/JS).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel

from src.projects import list_projects, create_project, get_project, delete_project, list_project_files, get_project_file, save_project_file, ProjectCreate
from src.universes import list_universes, create_universe, get_universe, delete_universe, UniverseCreate
from src.versioning import list_branches, create_branch, switch_branch, get_revision_history
from src.pipeline_adapter import get_pipeline_status, run_pipeline_phase, evaluate_project

app = FastAPI(
    title="Autonovel API",
    description="Backend API for Autonovel Web UI, multi-project, shared universes, and pipeline orchestration.",
    version="0.1.0"
)

STATIC_UI = Path(__file__).resolve().parent.parent / "ui"

@app.get("/")
def ui_root():
    return FileResponse(STATIC_UI / "index.html")

# --- Projects Endpoints ---
@app.get("/api/projects", response_model=List[Dict])
def api_list_projects():
    return list_projects()

@app.post("/api/projects", response_model=Dict)
def api_create_project(payload: ProjectCreate):
    return create_project(name=payload.name, concept=payload.concept, universe_id=payload.universe_id)

@app.get("/api/projects/{project_id}", response_model=Dict)
def api_get_project(project_id: str):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@app.delete("/api/projects/{project_id}")
def api_delete_project(project_id: str):
    success = delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted", "id": project_id}

@app.get("/api/projects/{project_id}/files", response_model=List[Dict])
def api_list_project_files(project_id: str):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_files(project_id)

@app.get("/api/projects/{project_id}/files/{filename:path}", response_model=Dict)
def api_get_project_file(project_id: str, filename: str):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    content = get_project_file(project_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"filename": filename, "content": content}

class FileSavePayload(BaseModel):
    content: str

@app.put("/api/projects/{project_id}/files/{filename:path}", response_model=Dict)
def api_save_project_file(project_id: str, filename: str, payload: FileSavePayload):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    success = save_project_file(project_id, filename, payload.content)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to save file")
    return {"status": "saved", "filename": filename}

# --- Universes Endpoints ---
@app.get("/api/universes", response_model=List[Dict])
def api_list_universes():
    return list_universes()

@app.post("/api/universes", response_model=Dict)
def api_create_universe(payload: UniverseCreate):
    return create_universe(name=payload.name, description=payload.description)

@app.get("/api/universes/{universe_id}", response_model=Dict)
def api_get_universe(universe_id: str):
    univ = get_universe(universe_id)
    if not univ:
        raise HTTPException(status_code=404, detail="Universe not found")
    return univ

@app.delete("/api/universes/{universe_id}")
def api_delete_universe(universe_id: str):
    success = delete_universe(universe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Universe not found")
    return {"status": "deleted", "id": universe_id}

# --- Versioning Endpoints ---
@app.get("/api/versioning/branches", response_model=List[str])
def api_list_branches(project_id: Optional[str] = None):
    return list_branches(project_id)

class BranchCreate(BaseModel):
    branch_name: str
    project_id: Optional[str] = None

@app.post("/api/versioning/branches")
def api_create_branch(payload: BranchCreate):
    success = create_branch(payload.branch_name, payload.project_id)
    return {"status": "created" if success else "failed", "branch": payload.branch_name}

class BranchSwitch(BaseModel):
    branch_name: str
    project_id: Optional[str] = None

@app.post("/api/versioning/switch")
def api_switch_branch(payload: BranchSwitch):
    success = switch_branch(payload.branch_name, payload.project_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to switch branch")
    return {"status": "switched", "branch": payload.branch_name}

@app.get("/api/versioning/history", response_model=List[Dict])
def api_get_history(chapter_num: Optional[int] = None, project_id: Optional[str] = None):
    return get_revision_history(chapter_num, project_id)

# --- Pipeline Endpoints ---
@app.get("/api/pipeline/status", response_model=Dict)
def api_pipeline_status(project_id: Optional[str] = None):
    return get_pipeline_status(project_id)

class PipelineRun(BaseModel):
    phase: str
    project_id: Optional[str] = None
    max_cycles: Optional[int] = None

@app.post("/api/pipeline/run", response_model=Dict)
def api_pipeline_run(payload: PipelineRun):
    res = run_pipeline_phase(payload.phase, payload.project_id, payload.max_cycles)
    if res.get("returncode", 0) != 0 or res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error", "Pipeline execution failed"))
    return res

class PipelineEvaluate(BaseModel):
    project_id: Optional[str] = None
    chapter_num: Optional[int] = None

@app.post("/api/pipeline/evaluate", response_model=Dict)
def api_pipeline_evaluate(payload: PipelineEvaluate):
    res = evaluate_project(payload.project_id, payload.chapter_num)
    if res.get("returncode", 0) != 0 or res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error", "Evaluation failed"))
    return res

# --- Static Files & SPA Fallback ---
app.mount("/css", StaticFiles(directory=STATIC_UI / "css"), name="ui-css")
app.mount("/js", StaticFiles(directory=STATIC_UI / "js"), name="ui-js")

@app.get("/{path:path}")
def ui_spa(path: str):
    file_path = STATIC_UI / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(STATIC_UI / "index.html")
