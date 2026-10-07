# Implementation Plan: Current Review Button in Top Menu Bar

**Branch**: `003-current-review-button` | **Date**: 2026-10-06 | **Status**: Implemented & Validated | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-current-review-button/spec.md`

## Summary

Add a persistent "Current Review" button to the top navigation bar of the Autonovel Web UI (`ui/index.html`). The button displays live review status (star rating/score), shows the underlying review JSON file path (`edit_logs/...`) in a tooltip on hover, and opens a rich review criteria and feedback modal when clicked. Backed by a new FastAPI endpoint (`GET /api/reviews/latest`) that inspects `edit_logs/`.

## Technical Context

**Language/Version**: Python 3.11+, Vanilla JavaScript (ES Modules), HTML5/CSS3

**Primary Dependencies**: FastAPI, Uvicorn, httpx

**Storage**: Local JSON files in `edit_logs/`

**Testing**: Pytest for backend API endpoints (`tests/test_reviews.py`)

**Target Platform**: Local web browser & FastAPI server

**Project Type**: Web application (FastAPI backend + vanilla SPA frontend)

**Performance Goals**: UI loads review status in < 500ms; modal opens in < 100ms

**Constraints**: No external npm dependencies; single-file modular JS/CSS architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- No API contract breaks: `/api/*` remains fully backward-compatible.
- No npm dependencies added.
- Modular architecture respected.

## Project Structure

### Documentation (this feature)

```text
specs/003-current-review-button/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Task breakdown
```

### Source Code (repository root)

```text
src/
├── api.py               # Add GET /api/reviews/latest
└── ...

ui/
├── index.html           # Add Current Review button & modal container
├── css/
│   └── style.css        # Styles for review button badge, tooltip, modal
└── js/
    ├── api.js           # Add getLatestReview()
    ├── inspector.js     # Or review modal controller
    └── views/
tests/
└── test_reviews.py      # Backend unit tests for review API
```

**Structure Decision**: Single project web app structure with modular backend endpoints and frontend UI modules.
