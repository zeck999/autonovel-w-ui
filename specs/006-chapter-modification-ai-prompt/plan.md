# Implementation Plan: Chapter Modification with AI & Toolbar Prompt Field (Option A)

**Branch**: `006-chapter-modification-ai-prompt` | **Date**: 2026-10-20 | **Status**: Completed | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-chapter-modification-ai-prompt/spec.md`

## Summary

Add AI-powered chapter modification capability to the Autonovel Web UI via an Option A toolbar prompt field in the chapter editor (`ui/js/views/files.js`). When a chapter file is selected, an inline prompt input and "Modifier avec l'IA" button allow vibe-coders to give natural language instructions to revise the text. Backed by a new FastAPI endpoint (`POST /api/projects/{id}/chapters/modify`) that interfaces with the backend AI revision logic (`src/pipeline_adapter.py` / `gen_revision.py`).

## Technical Context

**Language/Version**: Python 3.11+, Vanilla JavaScript (ES Modules), HTML5/CSS3

**Primary Dependencies**: FastAPI, Uvicorn, httpx

**Storage**: Local Markdown files in `chapters/`

**Testing**: Pytest for backend API endpoints (`tests/test_api.py` or new `tests/test_chapter_ai.py`)

**Target Platform**: Local web browser & FastAPI server

**Project Type**: Web application (FastAPI backend + vanilla SPA frontend)

**Performance Goals**: AI toolbar renders instantly; API response handled asynchronously with loading states

**Constraints**: No external npm dependencies; modular architecture respected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- No API contract breaks: `/api/*` remains fully backward-compatible.
- No npm dependencies added.
- Modular architecture respected.

## Project Structure

### Documentation (this feature)

```text
specs/006-chapter-modification-ai-prompt/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Task breakdown
```

### Source Code (repository root)

```text
src/
├── api.py               # Add POST /api/projects/{id}/chapters/modify endpoint
└── ...

ui/
├── index.html           # (If needed)
├── css/
│   └── style.css        # Styles for AI toolbar & prompt input
└── js/
    ├── api.js           # Add modifyChapterWithAI() API method
    └── views/
        └── files.js     # Render AI toolbar and handle modify event
tests/
└── test_chapter_ai.py   # Backend unit tests for chapter AI modification API
```

**Structure Decision**: Single project web app structure with modular backend endpoints and frontend UI modules.
