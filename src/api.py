from src.text_provider import post_messages, api_key as text_api_key
"""
src/api.py — FastAPI application exposing REST endpoints for Autonovel Web UI and harness.
Covers multi-project management, shared universes, narrative versioning, and pipeline control,
plus serving the Autonovel Web UI (HTML/CSS/JS).
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Literal
import os
import secrets
import ipaddress
from urllib.parse import urlsplit
from src.security import safe_child, validate_id
from src.jobs import submit_job, get_job, ProjectBusyError, project_guard
from src import coherence, publication, canon
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    coherence.start_worker()
    try:
        yield
    finally:
        coherence.stop_worker()

from src.projects import FileConflictError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json
from typing import Optional, List, Dict
from pydantic import BaseModel

from src.projects import list_projects, create_project, get_project, delete_project, list_project_files, get_project_file, save_project_file, ProjectCreate, WizardCreate, wizard_suggest, create_project_from_wizard
from src.universes import list_universes, create_universe, get_universe, delete_universe, UniverseCreate
from src.versioning import list_branches, create_branch, switch_branch, get_revision_history
from src.pipeline_adapter import get_pipeline_status, run_pipeline_phase, evaluate_project
from src.settings import get_api_keys_status, update_api_keys, verify_api_key

app = FastAPI(
    lifespan=lifespan,
    title="Autonovel API",
    description="Backend API for Autonovel Web UI, multi-project, shared universes, and pipeline orchestration.",
    version="0.3.0"
)

STATIC_UI = Path(__file__).resolve().parent.parent / "ui"

@app.middleware("http")
async def protect_access(request: Request, call_next):
    token = os.environ.get("AUTONOVEL_ACCESS_TOKEN", "")
    host = request.client.host if request.client else ""
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host == "testclient"
    # Reject cross-origin browser requests, including localhost DNS rebinding.
    origin = request.headers.get("origin")
    hostname = request.url.hostname or ""
    if not token and hostname not in {"localhost", "127.0.0.1", "::1", "testserver"}:
        return JSONResponse({"detail": "Configure AUTONOVEL_ACCESS_TOKEN for network access"}, status_code=403)
    if origin and urlsplit(origin).netloc != request.url.netloc:
        return JSONResponse({"detail": "Cross-origin requests are not allowed"}, status_code=403)
    if request.url.path.startswith("/api") or request.url.path in {"/docs", "/redoc", "/openapi.json"}:
        authorized = token and secrets.compare_digest(request.headers.get("authorization", ""), "Bearer " + token)
        if (token and not authorized) or (not token and not local):
            return JSONResponse({"detail": "Authentication required"}, status_code=401,
                                headers={"WWW-Authenticate": "Bearer"})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ValueError)
async def invalid_input(request, exc):
    status = 409 if isinstance(exc, (FileConflictError, ProjectBusyError)) else 400
    return JSONResponse({"detail": str(exc)}, status_code=status)


def require_project(project_id):
    if not project_id:
        raise HTTPException(status_code=422, detail="project_id is required")
    validate_id(project_id)
    if not get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Task not found (tasks are lost after server restart)")
    return job


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

class WizardSuggestRequest(BaseModel):
    field_key: str
    current_parameters: Optional[Dict[str, str]] = {}

@app.post("/api/projects/wizard/suggest", response_model=Dict)
def api_wizard_suggest(payload: WizardSuggestRequest):
    suggestions = wizard_suggest(payload.field_key, payload.current_parameters or {})
    return {"field_key": payload.field_key, "suggestions": suggestions}

@app.post("/api/projects/wizard/create", response_model=Dict)
def api_wizard_create(payload: WizardCreate):
    return create_project_from_wizard(payload)

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

from src import branch_graph, state_store


def _story_data(project_id):
    require_project(project_id)
    directory = coherence.directory(project_id)
    story, revision = state_store.read_story(directory)
    return directory, story, revision, state_store.chapters(directory)


def _story_response(directory, story, revision, chapters):
    try:
        publication.ensure_directory_editable(directory)
    except ValueError:
        editable = False
    else:
        editable = True
    return dict(story=story.model_dump(), revision=revision, chapters=chapters, editable=editable)


@app.get('/api/projects/{project_id}/story')
def api_story(project_id: str):
    return _story_response(*_story_data(project_id))


@app.put('/api/projects/{project_id}/story')
def api_save_story(project_id: str, payload: state_store.StorySave):
    import fcntl

    with project_guard(project_id):
        require_project(project_id)
        directory = coherence.directory(project_id)
        publication.ensure_directory_editable(directory)
        with safe_child(directory, '.generation.lock').open('a+') as lease:
            try:
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ProjectBusyError('Une opération est en cours pour ce roman') from exc
            publication.ensure_directory_editable(directory)
            _, _, revision, chapters = _story_data(project_id)
            if revision != payload.expected_revision:
                raise FileConflictError('L’état narratif a changé ; rechargez-le avant de sauvegarder')
            state_store.validate_story(payload.story, set(chapters))
            data = payload.story.model_dump()
            if len(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')) > 1_000_000:
                raise HTTPException(status_code=413, detail='État narratif trop volumineux')
            canon.atomic_json(state_store.story_path(directory), data)
            return _story_response(*_story_data(project_id))


@app.post('/api/projects/{project_id}/story/step')
def api_story_step(project_id: str, payload: state_store.StoryStep):
    _, story, _, chapters = _story_data(project_id)
    return state_store.step(story, set(chapters), payload)


@app.get('/api/projects/{project_id}/story/graph')
def api_story_graph(project_id: str):
    directory, story, _, chapters = _story_data(project_id)
    return dict(story=branch_graph.story_graph(story, chapters), history=branch_graph.revision_graph(directory))


class StagePreviewPayload(BaseModel):
    content: str


@app.post('/api/projects/{project_id}/stage-preview')
def api_stage_preview(project_id: str, payload: StagePreviewPayload):
    from src.stage_parser import parse_stage

    if len(payload.content) > 300_000:
        raise HTTPException(status_code=413, detail='Chapitre trop long pour cet aperçu')
    if not get_project(project_id):
        raise HTTPException(status_code=404, detail='Project not found')
    return parse_stage(payload.content)


@app.get('/api/projects/{project_id}/stage-assets/{filename}')
def api_stage_asset(project_id: str, filename: str):
    from src.projects import PROJECTS_DIR
    from src.stage_parser import ASSET, ASSET_TYPES

    if not ASSET.fullmatch(filename) or not get_project(project_id):
        raise HTTPException(status_code=404, detail='Image introuvable')
    directory = safe_child(PROJECTS_DIR, validate_id(project_id))
    assets = directory / 'stage-assets'
    path = assets / filename
    if assets.is_symlink() or path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail='Image introuvable')
    return FileResponse(path, media_type=ASSET_TYPES[path.suffix], headers={'Cache-Control': 'private, no-store'})


class FileSavePayload(BaseModel):
    content: str
    expected_content: Optional[str] = None

@app.put("/api/projects/{project_id}/files/{filename:path}", response_model=Dict)
def api_save_project_file(project_id: str, filename: str, payload: FileSavePayload):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    success = save_project_file(project_id, filename, payload.content, payload.expected_content)
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
    require_project(payload.project_id)
    success = create_branch(payload.branch_name, payload.project_id)
    return {"status": "created" if success else "failed", "branch": payload.branch_name}

class BranchSwitch(BaseModel):
    branch_name: str
    project_id: Optional[str] = None

@app.post("/api/versioning/switch")
def api_switch_branch(payload: BranchSwitch):
    require_project(payload.project_id)
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
    phase: Literal["foundation", "outline", "draft", "drafting", "review", "revise", "revision", "typeset", "export", "audiobook"]
    project_id: Optional[str] = None
    max_cycles: Optional[int] = None

@app.post("/api/pipeline/run", response_model=Dict, status_code=202)
def api_pipeline_run(payload: PipelineRun, request: Request):
    require_project(payload.project_id)
    publication.ensure_editable(payload.project_id)
    if payload.max_cycles is not None and not 1 <= payload.max_cycles <= 6:
        raise HTTPException(status_code=422, detail="max_cycles must be between 1 and 6")
    return submit_job(payload.project_id, f"pipeline:{payload.phase}:{payload.max_cycles}",
                      lambda: run_pipeline_phase(payload.phase, payload.project_id, payload.max_cycles), request.headers.get("Idempotency-Key"))


class PipelineEvaluate(BaseModel):
    project_id: Optional[str] = None
    chapter_num: Optional[int] = None

@app.post("/api/pipeline/evaluate", response_model=Dict, status_code=202)
def api_pipeline_evaluate(payload: PipelineEvaluate, request: Request):
    require_project(payload.project_id)
    if payload.chapter_num is not None and payload.chapter_num < 1:
        raise HTTPException(status_code=422, detail="Invalid chapter number")
    return submit_job(payload.project_id, f"evaluate:{payload.chapter_num}",
                      lambda: evaluate_project(payload.project_id, payload.chapter_num), request.headers.get("Idempotency-Key"))


# --- Universe coherence and irreversible publication ---
class AnalyzePayload(BaseModel):
    full: bool = True

class ReviewIssuePayload(BaseModel):
    rationale: str

@app.post("/api/projects/{project_id}/coherence/review", status_code=202)
def api_review_issue(project_id: str, payload: ReviewIssuePayload, request: Request):
    require_project(project_id)
    if not 10 <= len(payload.rationale.strip()) <= 4000:
        raise ValueError('Provide a sourced rationale between 10 and 4000 characters')
    path = coherence.directory(project_id)
    with coherence._LOCK:
        state = coherence._read(path)
        state['review_rationale'] = payload.rationale.strip()
        coherence._write(coherence._state_path(path), state)
    coherence.request_analysis(project_id, True)
    return submit_job(project_id, "coherence-review", lambda: coherence.analyze(project_id, True), request.headers.get('Idempotency-Key'), serialize=False)

class AcceptAssertions(BaseModel):
    analysis_id: str
    assertion_ids: List[str]

class ChangeUniversePayload(BaseModel):
    universe_id: str

@app.put("/api/projects/{project_id}/universe")
def api_change_universe(project_id: str, payload: ChangeUniversePayload):
    from src.projects import change_universe
    require_project(project_id)
    return change_universe(project_id, payload.universe_id)

class PublishPayload(BaseModel):
    confirmation: bool = False

@app.get("/api/projects/{project_id}/coherence")
def api_coherence_state(project_id: str):
    require_project(project_id)
    return coherence.get_state(project_id)

@app.get("/api/projects/{project_id}/coherence/estimate")
def api_coherence_estimate(project_id: str):
    require_project(project_id)
    return coherence.estimate(project_id)

@app.post("/api/projects/{project_id}/coherence/analyze", status_code=202)
def api_coherence_analyze(project_id: str, payload: AnalyzePayload, request: Request):
    require_project(project_id)
    coherence.request_analysis(project_id, payload.full)
    return submit_job(project_id, "coherence:" + str(payload.full),
                      lambda: coherence.analyze(project_id, payload.full), request.headers.get("Idempotency-Key"), serialize=False)

@app.post("/api/projects/{project_id}/coherence/accept")
def api_coherence_accept(project_id: str, payload: AcceptAssertions):
    require_project(project_id)
    publication.ensure_editable(project_id)
    with project_guard(project_id):
        return coherence.accept_proposals(project_id, payload.analysis_id, payload.assertion_ids)

@app.get("/api/projects/{project_id}/publication")
def api_publication_status(project_id: str):
    require_project(project_id)
    return publication.get_status(project_id)

@app.post("/api/projects/{project_id}/publish")
def api_publish(project_id: str, payload: PublishPayload):
    require_project(project_id)
    return publication.publish(project_id, payload.confirmation)

class ProofreadPayload(BaseModel):
    file_path: str
    content: str
    expected_content: str
    confirmation: bool = False

class ApplyProofreadPayload(BaseModel):
    proposal_id: str
    confirmation: bool = False

@app.post("/api/projects/{project_id}/proofread", status_code=202)
def api_proofread(project_id: str, payload: ProofreadPayload, request: Request):
    from src import proofreading
    require_project(project_id)
    import hashlib
    fingerprint = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    return submit_job(project_id, "proofread:" + fingerprint,
                      lambda: proofreading.propose(project_id, payload.file_path, payload.content, payload.expected_content, payload.confirmation),
                      request.headers.get("Idempotency-Key"))

@app.post("/api/projects/{project_id}/proofread/apply")
def api_proofread_apply(project_id: str, payload: ApplyProofreadPayload):
    from src import proofreading
    require_project(project_id)
    return proofreading.apply(project_id, payload.proposal_id, payload.confirmation)

@app.get("/api/universes/{universe_id}/canon")
def api_universe_canon(universe_id: str):
    return canon.get_registry(universe_id)

# --- Settings Endpoints ---
@app.get("/api/settings/keys", response_model=Dict)
def api_get_settings_keys():
    return get_api_keys_status()

class SettingsUpdate(BaseModel):
    text_provider: Optional[str] = None
    text_base_url: Optional[str] = None
    text_model: Optional[str] = None
    text_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    fal_key: Optional[str] = None

@app.put("/api/settings/keys", response_model=Dict)
def api_update_settings_keys(payload: SettingsUpdate):
    updates = {}
    for field in ("text_provider", "text_base_url", "text_model", "text_api_key"):
        value = getattr(payload, field)
        if value is not None:
            updates["AUTONOVEL_" + field.upper()] = value
    if payload.anthropic_api_key is not None:
        updates["ANTHROPIC_API_KEY"] = payload.anthropic_api_key
    if payload.elevenlabs_api_key is not None:
        updates["ELEVENLABS_API_KEY"] = payload.elevenlabs_api_key
    if payload.fal_key is not None:
        updates["FAL_KEY"] = payload.fal_key
        
    success = update_api_keys(updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update settings")
    return {"status": "updated", "keys": get_api_keys_status()}

class KeyTestRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None

@app.post("/api/settings/keys/test", response_model=Dict)
def api_test_settings_key(payload: KeyTestRequest):
    return verify_api_key(payload.provider, payload.api_key)


# --- Chapter AI Modification Endpoint ---
class ChapterModifyPayload(BaseModel):
    file_path: str
    content: str
    prompt: str

@app.post("/api/projects/{project_id}/chapters/modify", response_model=Dict, status_code=202)
def api_modify_chapter_ai(project_id: str, payload: ChapterModifyPayload, request: Request):
    require_project(project_id)
    publication.ensure_editable(project_id)
    # Validate the file boundary and type before spending provider credits.
    from src.projects import PROJECTS_DIR
    from src.security import project_file
    project_file(safe_child(PROJECTS_DIR, project_id), payload.file_path)
    original = get_project_file(project_id, payload.file_path)
    if original is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    import hashlib
    operation = "modify:" + hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    return submit_job(project_id, operation, lambda: _modify_chapter_proposal(project_id, payload, original), request.headers.get("Idempotency-Key"))


def _modify_chapter_proposal(project_id: str, payload: ChapterModifyPayload, original_content: str):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    import os
    import httpx
    import logging
    logger = logging.getLogger(__name__)

    api_key = text_api_key()
    if not api_key or api_key.startswith("your-") or "your-" in api_key:
        logger.error("ERR_AI_MOD_KEY_MISSING: ANTHROPIC_API_KEY is not configured.")
        raise HTTPException(
            status_code=400,
            detail="ERR_AI_MOD_KEY_MISSING: ANTHROPIC_API_KEY n'est pas configurée. Veuillez configurer votre clé API dans les Paramètres."
        )

    writer_model = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
    api_base = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

    from src.projects import PROJECTS_DIR
    project_dir = safe_child(PROJECTS_DIR, validate_id(project_id))
    voice = (project_dir / "voice.md").read_text() if (project_dir / "voice.md").exists() else ""
    characters = (project_dir / "characters.md").read_text() if (project_dir / "characters.md").exists() else ""
    world = (project_dir / "world.md").read_text() if (project_dir / "world.md").exists() else ""

    system_prompt = (
        "You are an expert novel writing assistant modifying a chapter based on specific user revision instructions. "
        "You preserve the voice, world, and characters while implementing the requested changes precisely. "
        "You write the FULL chapter content. Do not truncate or summarize."
    )

    user_prompt = f"""Modify the following chapter according to the user instruction.

USER INSTRUCTION / PROMPT:
{payload.prompt}

EXISTING CHAPTER CONTENT:
{payload.content}

{f"VOICE DEFINITION:\\n{voice}" if voice else ""}
{f"CHARACTER REGISTRY:\\n{characters}" if characters else ""}
{f"WORLD BIBLE:\\n{world}" if world else ""}

Return the complete modified chapter text now."""
    user_prompt += state_store.prompt_context(project_dir, payload.file_path)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "context-1m-2025-08-07",
        "content-type": "application/json",
    }

    try:
        resp = post_messages(
            f"{api_base}/v1/messages",
            headers=headers,
            json={
                "model": writer_model,
                "max_tokens": 16000,
                "temperature": 0.8,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            },
            timeout=120.0
        )
        if resp.status_code == 401:
            logger.error("ERR_AI_MOD_UNAUTHORIZED_401: API authentication failed.")
            raise HTTPException(status_code=401, detail="ERR_AI_MOD_UNAUTHORIZED_401: Clé API Anthropic invalide ou non autorisée.")
        elif resp.status_code == 429:
            logger.error("ERR_AI_MOD_RATE_LIMIT_429: Rate limit exceeded.")
            raise HTTPException(status_code=429, detail="ERR_AI_MOD_RATE_LIMIT_429: Trop de requêtes (rate limit).")
        elif resp.status_code >= 400:
            logger.error("ERR_AI_MOD_ERROR: API status %s", resp.status_code)
            raise HTTPException(status_code=500, detail=f"ERR_AI_MOD_ERROR: Erreur API externe ({resp.status_code}).")

        data = resp.json()
        modified_content = data["content"][0]["text"]

        if data.get("stop_reason") == "max_tokens":
            raise HTTPException(status_code=502, detail="AI response truncated; no file was changed")
        return {
            "file_path": payload.file_path, "filename": payload.file_path,
            "content": modified_content, "original_content": original_content,
            "status": "proposal", "message": "Review the proposal before applying it"
        }
    except httpx.TimeoutException:
        logger.error("ERR_AI_MOD_TIMEOUT: AI request timed out.")
        raise HTTPException(status_code=504, detail="ERR_AI_MOD_TIMEOUT: La requête IA a expiré (timeout).")
    except httpx.RequestError as e:
        logger.error(f"ERR_AI_MOD_NETWORK_ERROR: Network error: {e}")
        raise HTTPException(status_code=502, detail="ERR_AI_MOD_NETWORK_ERROR: Erreur réseau")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERR_AI_MOD_ERROR: Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="ERR_AI_MOD_ERROR: Erreur inattendue")


# --- Reviews Endpoints ---
@app.get("/api/reviews/latest", response_model=Dict)
def api_get_latest_review(project_id: Optional[str] = None):
    require_project(project_id)
    from src.projects import PROJECTS_DIR
    project_dir = safe_child(PROJECTS_DIR, validate_id(project_id))
    edit_logs_dir = safe_child(project_dir, "edit_logs")
    if not edit_logs_dir.exists():
        return {"exists": False, "message": "No edit_logs directory found"}
    reviews = sorted(edit_logs_dir.glob("*_review.json"), reverse=True)
    if not reviews:
        return {"exists": False, "message": "No reviews found"}
    latest_file = safe_child(edit_logs_dir, reviews[0].name)
    try:
        data = json.loads(latest_file.read_text())
        data["file_path"] = str(latest_file.relative_to(project_dir))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read review log: {e}")


# --- Static Files & SPA Fallback ---
app.mount("/css", StaticFiles(directory=STATIC_UI / "css"), name="ui-css")
app.mount("/js", StaticFiles(directory=STATIC_UI / "js"), name="ui-js")

@app.get('/api/versioning/status')
def api_versioning_status(project_id: str):
    from src.versioning import get_status
    return get_status(project_id)


class RevisionRestore(BaseModel):
    project_id: str
    revision: str
    confirmation: bool = False


@app.post('/api/versioning/restore')
def api_restore_revision(payload: RevisionRestore):
    from src.versioning import restore_revision
    return restore_revision(payload.project_id, payload.revision, payload.confirmation)


@app.get("/{path:path}")
def ui_spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    try:
        file_path = safe_child(STATIC_UI, path)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    if file_path.is_file():
        if file_path.suffix not in {".html", ".css", ".js", ".png", ".svg", ".ico", ".woff2"}:
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(file_path)
    return FileResponse(STATIC_UI / "index.html")
