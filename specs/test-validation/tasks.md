---
description: "Task list for Test Validation & Full Journey Integration Suite reconstruction"
---

# Tasks: Test Validation & Full Journey Integration Suite

**Input**: Design documents from `/specs/test-validation/`

**Prerequisites**: plan.md, spec.md

## Phase 1: Exhaustive Journey Integration Test

**Purpose**: Implement and verify the end-to-end user journey integration test (`tests/test_full_journey.py`).

- [x] T001 Implement step-by-step full journey test in tests/test_full_journey.py covering project creation, file editing, foundation, outline, draft, and evaluation.
- [x] T002 Verify mocking of subprocess execution for robust and fast execution.

---

## Phase 2: Component Test Suite Verification

**Purpose**: Ensure all unit and integration tests pass successfully across the codebase.

- [x] T003 Verify API endpoints test in tests/test_api.py
- [x] T004 Verify pipeline adapter tests in tests/test_pipeline.py and tests/test_e2e_pipeline.py
- [x] T005 Verify project and universe management tests in tests/test_projects.py and tests/test_universes.py
- [x] T006 Verify versioning and review tests in tests/test_versioning.py and tests/test_reviews.py
- [x] T007 Verify settings tests in tests/test_settings.py and tests/test_settings_e2e.py

---

## Phase 3: Validation Project & Artifacts

**Purpose**: Maintain and verify reference validation project structure.

- [x] T008 Verify integrity of projects/test-de-validation-complet/ seed, world, outline, and state files.

---

## Phase 4: Polish & Documentation

**Purpose**: Finalize documentation and verify test suite pass rate.

- [x] T009 Run complete test suite via pytest and confirm 100% pass rate.
- [x] T010 Reconstruct specification, plan, and tasks under specs/test-validation/.
