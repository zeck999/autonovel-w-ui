# Implementation Plan: AI Keys Test and Edit Feature

**Branch**: `settings-ai-keys` | **Date**: 2026-10-06 | **Spec**: [specs/settings/spec.md](spec.md)

**Input**: Feature specification from `specs/settings/spec.md`

## Summary

Implement backend REST endpoints and Web UI interface for viewing, securely updating, and testing AI provider API keys (`ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`) stored in the `.env` file, with secure masking and real-time connection testing.

## Technical Context

**Language/Version**: Python 3.11+ / JavaScript (Vanilla ES6 SPA)

**Primary Dependencies**: FastAPI, Pydantic, python-dotenv, requests/httpx

**Storage**: Local `.env` configuration file in project root

**Testing**: `pytest tests/test_settings.py`

**Target Platform**: Local development & server (Linux/macOS/Windows)

**Project Type**: Web service (FastAPI backend + HTML/CSS/JS SPA frontend)

**Performance Goals**: Key test results returned in <5s; UI updates instantly

**Constraints**: Zero plaintext key leakage in logs or API responses

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Modular architecture adhered to (`src/settings.py`, `ui/js/views/settings.js`).
- Strict security & masking enforced.
- Tested via pytest.

## Project Structure

### Documentation (this feature)

```text
specs/settings/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Task list
```

### Source Code (repository root)

```text
src/
├── api.py               # FastAPI app (include settings router/endpoints)
└── settings.py          # Settings service (dotenv read/write, key testing, masking)

ui/
├── index.html           # SPA root (include settings nav link)
└── js/
    ├── router.js        # Route registration for /settings
    └── views/
        └── settings.js  # Settings view component

tests/
└── test_settings.py     # Unit & integration tests for settings and key testing
```

**Structure Decision**: Integrated cleanly into the existing FastAPI + SPA architecture of Autonovel without external heavy frameworks.

## Implementation Status

- **Status**: Planned / Pending Implementation.
- **Scope**: Designed for `src/settings.py`, endpoints in `src/api.py`, `ui/js/views/settings.js`, router integration, and unit tests (`tests/test_settings.py`).
