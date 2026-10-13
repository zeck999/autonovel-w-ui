---
description: "Task list for verifying the Wizard button with chrome-devtools MCP by creating a novel 'the'"
---

# Tasks: Wizard Button Verification via Chrome DevTools MCP & Novel 'the'

**Input**: Design documents from `specs/005-wizard-verification-chrome-devtools/`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup & Environment Verification

- [x] T001 Verify local web server and test suite readiness (`pytest tests/test_projects.py`)
- [x] T002 [P] Confirm Chrome DevTools MCP connectivity and target web page accessibility

---

## Phase 2: User Story 1 - Wizard Button Inspection & Interaction via Chrome DevTools MCP (Priority: P1) 🎯 MVP

- [x] T003 [US1] Inspect Projects view DOM via Chrome DevTools MCP to locate the Wizard button
- [x] T004 [US1] Trigger click action on the Wizard button and verify modal expansion and accordion sections load correctly

---

## Phase 3: User Story 2 - Creating Novel 'the' via Wizard Input & Slugification (Priority: P2)

- [x] T005 [US2] Input project title and concept as `'the'` in the wizard interface
- [x] T006 [US2] Complete wizard steps and submit project creation request via API/UI
- [x] T007 [US2] Verify backend slugification and project record creation for title `'the'` without validation errors

---

## Phase 4: User Story 3 - Workspace File Generation & Verification for Novel 'the' (Priority: P3)

- [x] T008 [US3] Verify automatic generation of foundational files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`) for novel `'the'` under `projects/`
- [x] T009 [US3] Inspect generated files via Chrome DevTools MCP and Web UI file explorer view

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T010 [P] Run full test suite (`pytest tests/`) to ensure zero regressions
- [x] T011 Verify quickstart and documentation alignment across all living specs
