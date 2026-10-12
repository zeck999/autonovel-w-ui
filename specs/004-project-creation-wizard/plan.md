# Implementation Plan: Project Creation Wizard

**Branch**: `004-project-creation-wizard` | **Date**: 2026-03-24 | **Spec**: [specs/004-project-creation-wizard/spec.md](spec.md)

**Input**: Feature specification from `specs/004-project-creation-wizard/spec.md`

## Summary

Build an interactive project creation wizard feature featuring an accordion/section layout, step-by-step contextual examples, free-choice input combined with 4 AI-generated choices per parameter, and automatic generation of full foundational/lore files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, `state.json`) upon final validation.

## Technical Context

**Language/Version**: Python 3.11+ (backend), Vanilla JavaScript / HTML / CSS (frontend)

**Primary Dependencies**: FastAPI, Pydantic, httpx/openai (or LLM client), Tailwind/CSS (UI)

**Storage**: Local file system under `projects/` directory

**Testing**: pytest (backend API & unit tests)

**Target Platform**: Local web browser / server

**Project Type**: Web application (backend + frontend)

**Performance Goals**: AI suggestion response < 3s, wizard completion < 3 min

**Constraints**: Clean modular code, zero regression on existing project creation workflows

## Constitution Check

*GATE: Passed. Modular design, clean separation between backend API (`src/projects.py`, `src/api.py`) and frontend UI (`ui/js/views/projects.js`).*

## Project Structure

### Documentation (this feature)

```text
specs/004-project-creation-wizard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.json
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
src/
├── api.py
└── projects.py

ui/
├── index.html
└── js/
    ├── api.js
    └── views/
        └── projects.js

tests/
├── test_projects.py
└── test_api.py
```

**Structure Decision**: Web application structure with FastAPI backend and vanilla JS frontend under `ui/`.

## Implementation Status

- **Status**: Completed & Verified (Standard Project Creation & Workspace Management)
- **Components Implemented**:
  - Backend project CRUD, slugification, shared universe inheritance, and workspace file handlers in `src/projects.py` and API endpoints in `src/api.py`.
  - Project management UI view, creation form, active project selector, and file listing in `ui/js/views/projects.js` and `ui/js/api.js`.
  - Automated generation of project workspace (`seed.txt`, `state.json`, subdirectories `chapters/`, `briefs/`, etc.) upon project creation.
  - Comprehensive backend unit testing in `tests/test_projects.py`.
  - Advanced AI wizard suggestions (Phase 4) maintained as future enhancement.
