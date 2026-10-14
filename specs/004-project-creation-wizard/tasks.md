---
description: "Task list for Project Creation and Workspace Initialization feature (Reconciled with effective implementation)"
---

# Tasks: Project Creation & Workspace Initialization

**Input**: Design documents from `specs/004-project-creation-wizard/` and effective codebase implementation (`src/projects.py`, `src/api.py`, `ui/js/views/projects.js`, `tests/test_projects.py`)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup & Testing Infrastructure

- [x] T001 Implement comprehensive project unit tests in `tests/test_projects.py` for backend CRUD and file management
- [x] T002 [P] Document API contracts in `specs/004-project-creation-wizard/contracts/api.json`

---

## Phase 2: Foundational Project Management & Workspace Generation

- [x] T003 Implement project data models and validation schemas (`ProjectCreate`, `ProjectResponse`) in `src/projects.py`
- [x] T004 [P] Implement workspace initialization, unique slugification, `seed.txt`, `state.json`, and shared universe inheritance in `src/projects.py`

---

## Phase 3: Project Creation UI & Navigation (Priority: P1)

- [x] T004.1 [US1] Add 'Assistant Créatif' button in the navigation bar right next to Dashboard in `ui/index.html` and wire routing in `ui/js/router.js`
- [x] T005 [P] [US1] Create project creation form and active project selector in `ui/js/views/projects.js`
- [x] T006 [US1] Add contextual placeholders and input validation in `ui/js/views/projects.js`
- [x] T007 [US1] Add project selection, deletion, and file management navigation controls in `ui/js/views/projects.js`

---

## Phase 4: Extended AI Wizard Features & Refinement

- [x] T008 [P] [US2] Implement backend endpoint `POST /api/projects/wizard/suggest` for AI suggestions in `src/api.py` and `src/projects.py`
- [x] T009 [US2] Implement API client method for AI suggestions in `ui/js/api.js`
- [x] T010 [US2] Wire up "Generate AI Choices" button and choice selector in `ui/js/views/projects.js`

---

## Phase 5: Final Validation & Workspace Initialization (Priority: P3)

- [x] T011 [P] [US3] Implement project list summary and file inspection interface in `ui/js/views/projects.js`
- [x] T012 [US3] Implement backend project creation endpoint `POST /api/projects` in `src/api.py` and `src/projects.py`
- [x] T013 [US3] Ensure automatic generation of `seed.txt`, `state.json`, and standard workspace subdirectories (`chapters/`, `briefs/`, etc.) in `src/projects.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T014 [P] Run and verify test suite via `pytest tests/test_projects.py`
- [x] T015 Run quickstart validation per `specs/004-project-creation-wizard/quickstart.md`
- [x] T016 [P] Code cleanup and refactoring across project management modules

