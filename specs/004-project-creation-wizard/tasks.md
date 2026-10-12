---
description: "Task list for Project Creation Wizard feature"
---

# Tasks: Project Creation Wizard

**Input**: Design documents from `specs/004-project-creation-wizard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.json

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize test structure and backend/frontend hooks for wizard feature

- [ ] T001 Create test file `tests/test_wizard.py` for wizard backend logic
- [ ] T002 [P] Register wizard routes schema in `specs/004-project-creation-wizard/contracts/api.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and backend helper methods for wizard parameter handling

- [ ] T003 Implement wizard data models and validation schemas in `src/projects.py`
- [ ] T004 [P] Implement base lore file generator functions (`world.md`, `characters.md`, `canon.md`, `outline.md`) in `src/projects.py`

---

## Phase 3: User Story 1 - Guided Project Creation Wizard UI with Accordion Layout (Priority: P1) 🎯 MVP

**Goal**: Provide an accordion/section-based wizard interface with step-by-step examples in the web UI.

**Independent Test**: Verify wizard modal renders accordion steps correctly with contextual examples.

- [ ] T005 [P] [US1] Create accordion wizard view and components in `ui/js/views/projects.js`
- [ ] T006 [US1] Add step-by-step examples and helper tooltips in `ui/js/views/projects.js`
- [ ] T007 [US1] Add expand/collapse and navigation controls between wizard accordion sections in `ui/js/views/projects.js`

**Checkpoint**: User Story 1 UI is fully testable independently.

---

## Phase 4: User Story 2 - Free-Choice Input and 4 AI-Generated Choices per Parameter (Priority: P2)

**Goal**: Support free-form custom input and backend/frontend integration for generating 4 AI choices per parameter.

**Independent Test**: Verify clicking "Generate 4 AI Choices" returns 4 options and populates the selected parameter field.

- [ ] T008 [P] [US2] Implement backend endpoint `POST /api/projects/wizard/suggest` in `src/api.py` and `src/projects.py`
- [ ] T009 [US2] Implement API client method for AI suggestions in `ui/js/api.js`
- [ ] T010 [US2] Wire up "Generate 4 AI Choices" button and modal choice selector in `ui/js/views/projects.js`

**Checkpoint**: User Stories 1 and 2 work together.

---

## Phase 5: User Story 3 - Final Validation and Full Foundational/Lore Files Generation (Priority: P3)

**Goal**: Implement final summary review screen and automatic generation of all foundational/lore files upon validation.

**Independent Test**: Complete wizard, submit validation, and verify all lore files and `state.json` are created under `projects/`.

- [ ] T011 [P] [US3] Implement final summary review screen in `ui/js/views/projects.js`
- [ ] T012 [US3] Implement backend project creation validation endpoint `POST /api/projects/wizard/create` in `src/api.py` and `src/projects.py`
- [ ] T013 [US3] Ensure automatic generation of `seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json` in `src/projects.py`

**Checkpoint**: All user stories fully functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Testing, edge case hardening, and documentation updates.

- [ ] T014 [P] Add comprehensive backend unit tests in `tests/test_wizard.py`
- [ ] T015 Run quickstart validation per `specs/004-project-creation-wizard/quickstart.md`
- [ ] T016 [P] Code cleanup and refactoring across wizard modules

---

## Dependencies & Execution Order

### Phase Dependencies
- Setup (Phase 1) → Foundational (Phase 2) → User Story 1 (Phase 3) → User Story 2 (Phase 4) → User Story 3 (Phase 5) → Polish (Phase 6)

### Parallel Opportunities
- T002 and T004 can run in parallel during setup/foundational phases.
- T005 and T008 can be developed in parallel across frontend and backend.
- T014 and T016 can run in parallel during polish.
