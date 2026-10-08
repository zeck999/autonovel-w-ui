# Feature Specification: Test Validation & Full Journey Integration Suite

**Feature Branch**: `test-validation`

**Created**: 2026-10-08

**Status**: Implemented & Validated

**Input**: User description: "Reconstruct specs, plan, and tasks for request REQ-20261008135642 (test) under specs/test-validation/ for comprehensive test validation and full user journey integration suite."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full User Journey Pipeline Integration Test (Priority: P1) 🎯 MVP
The system executes a step-by-step exhaustive integration test (`tests/test_full_journey.py`) simulating a complete user journey from project creation, file editing, sequential pipeline phase execution (foundation, outline, draft), evaluation, and status/log monitoring.

**Why this priority**: Ensures end-to-end reliability and correctness of the autonomous novel creation harness before deployment or release.

**Independent Test**: Run `pytest tests/test_full_journey.py` and verify all journey steps pass successfully.

**Acceptance Scenarios**:
1. **Given** the FastAPI test client is initialized, **When** a new project is created via `/api/projects`, **Then** the project is stored correctly on disk with `state.json` initialized.
2. **Given** an active project, **When** foundation files like `seed.txt` and `world.md` are queried and edited via `/api/projects/{id}/files/...`, **Then** content updates are successfully persisted.
3. **Given** project files are ready, **When** pipeline phases (`foundation`, `outline`, `draft`) are executed via `/api/pipeline/run`, **Then** successful return codes and valid logs are produced.
4. **Given** a drafted project, **When** project evaluation is triggered via `/api/pipeline/evaluate`, **Then** overall scores and literary review metrics are returned correctly.

---

### User Story 2 - Comprehensive Test Suite Coverage (Priority: P1)
All component tests (`tests/test_api.py`, `tests/test_pipeline.py`, `tests/test_projects.py`, `tests/test_universes.py`, `tests/test_versioning.py`, `tests/test_settings.py`, `tests/test_e2e_pipeline.py`) execute successfully to guarantee regression-free robust operation across the entire codebase.

**Why this priority**: Guarantees modular integrity and contract stability across API endpoints, pipeline adapters, projects, universes, versioning, and settings.

**Independent Test**: Run `pytest tests/` and verify 100% test pass rate.

**Acceptance Scenarios**:
1. **Given** the full test suite, **When** `pytest tests/` is executed, **Then** all tests pass without errors or regressions.

---

### User Story 3 - Dedicated Test Validation Project Artifacts (Priority: P2)
The project includes a pre-configured test project (`projects/test-de-validation-complet/`) containing baseline seed, world, characters, outline, canon, and state files for integration testing and live validation.

**Why this priority**: Provides a stable real-world sample project structure for robust end-to-end testing and validation exercises.

**Independent Test**: Verify `projects/test-de-validation-complet/` exists with valid configuration and markdown files.

**Acceptance Scenarios**:
1. **Given** the repository workspace, **When** inspecting `projects/test-de-validation-complet/`, **Then** `seed.txt`, `world.md`, `characters.md`, `outline.md`, `canon.md`, and `state.json` are present and properly structured.

---

### Edge Cases
- What happens when subprocess pipeline execution fails during testing? → Integration tests mock subprocess output or handle error return codes gracefully.
- What happens if test projects already exist? → Test teardown and isolation fixtures clean up temporary test projects correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an exhaustive integration test in `tests/test_full_journey.py` covering project creation, file editing, pipeline execution steps, and evaluation.
- **FR-002**: System MUST maintain 100% passing test suite across all modules (`tests/`).
- **FR-003**: System MUST provide a dedicated validation project template in `projects/test-de-validation-complet/`.
- **FR-004**: Pipeline execution wrapper (`src/pipeline_adapter.py`) MUST correctly invoke pipeline phases and record execution logs and scores.

### Key Entities

- **FullJourneyTest**: Represents the end-to-end integration test suite simulating user actions.
- **ValidationProject**: Represents the reference project `test-de-validation-complet` used for verification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/test_full_journey.py` passes successfully with all journey steps verified.
- **SC-002**: `pytest tests/` executes all unit and integration tests with a 100% pass rate.
- **SC-003**: Dedicated validation project structure is intact and accessible.

## Assumptions

- Python 3.11+ and pytest environment are available.
- Subprocess execution during testing can be mocked using `unittest.mock` for deterministic test runs.
