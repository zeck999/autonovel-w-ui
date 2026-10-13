# Feature Specification: Wizard Button Verification via Chrome DevTools MCP & Novel 'the'

**Feature Branch**: `005-wizard-verification-chrome-devtools`

**Created**: 2026-10-13

**Status**: Ready for Verification & Reconciled

**Input**: User description: "Reconstruct specs, plan, and tasks for verifying the Wizard button with chrome-devtools MCP by creating a novel 'the', ensuring all specs/tasks.md files are fully up to date."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wizard Button Inspection & Interaction via Chrome DevTools MCP (Priority: P1) 🎯 MVP

As a QA engineer or developer using Chrome DevTools MCP, I want to inspect, navigate to, and click the Project Creation Wizard button in the Web UI, verifying that the accordion layout and step-by-step wizard interface open correctly.

**Why this priority**: P1 ensures that the UI entry point for project creation is fully accessible and verifiable through browser automation tools (Chrome DevTools MCP).

**Independent Test**: Can be tested by launching the web server, connecting via Chrome DevTools MCP, locating the Wizard button, clicking it, and verifying the modal/view state.

**Acceptance Scenarios**:

1. **Given** the web UI application is running, **When** the Chrome DevTools MCP inspects the Projects page, **Then** the Wizard button is identified and interactive.
2. **Given** the user/agent clicks the Wizard button, **When** the click event fires, **Then** the project creation wizard modal/view opens, displaying accordion sections (Concept, Genre & Tone, Characters, World Lore).

---

### User Story 2 - Creating Novel 'the' via Wizard Input & Slugification (Priority: P2)

As a creator, I want to create a new novel titled simply `'the'` through the wizard interface, ensuring the system handles short/single-word titles, custom inputs, and AI suggestions correctly without slug collisions or validation errors.

**Why this priority**: P2 tests edge-case handling for minimal/single-character or common-word titles (`'the'`) in slug generation and project initialization.

**Independent Test**: Can be tested by filling out the wizard with title `'the'`, submitting the form, and observing successful API response and redirect.

**Acceptance Scenarios**:

1. **Given** the wizard is open, **When** the user enters `'the'` as the project title/concept and proceeds through the steps, **Then** input validation accepts it.
2. **Given** the wizard summary is validated, **When** "Create Project" is clicked, **Then** the backend processes the request and successfully creates project `'the'`.

---

### User Story 3 - Workspace File Generation & Verification for Novel 'the' (Priority: P3)

As a creator and QA validator, I want the system to automatically generate all required foundational and lore files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`) inside the project directory for novel `'the'`, and verify them via Chrome DevTools MCP network/file inspection.

**Why this priority**: P3 verifies end-to-end data persistence and file generation for edge-case project titles.

**Independent Test**: Can be tested by inspecting the generated directory under `projects/` and viewing files in the Web UI file explorer.

**Acceptance Scenarios**:

1. **Given** project `'the'` has been created, **When** the project dashboard loads, **Then** all foundational files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, `state.json`) are present.
2. **Given** Chrome DevTools MCP inspects the file explorer view, **When** selecting `seed.txt`, **Then** the content corresponding to novel `'the'` is displayed correctly.

---

### Edge Cases

- How does the system handle single-word or stop-word titles like `'the'` in slug generation? The slugifier normalizes it safely without empty strings or invalid paths.
- What happens if the project directory already exists? A numeric suffix or unique identifier is appended.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Web UI MUST render the Project Creation Wizard button prominently on the Projects view.
- **FR-002**: Chrome DevTools MCP MUST be able to locate and trigger the Wizard button via DOM inspection and click commands.
- **FR-003**: The wizard form MUST accept minimal input strings such as `'the'` for project titles and concepts.
- **FR-004**: The backend MUST correctly slugify and initialize project directories for edge-case titles like `'the'`.
- **FR-005**: Upon validation, the backend MUST generate `seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`.
- **FR-006**: The Web UI file explorer MUST display and permit editing of all generated files for project `'the'`.

### Key Entities

- **WizardSession**: UI state managing accordion expansion and field inputs for project creation.
- **ProjectWorkspace (`the`)**: The isolated project storage structure containing lore markdown files and state metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chrome DevTools MCP successfully locates and clicks the Wizard button in < 2 seconds.
- **SC-002**: Project `'the'` is created successfully via the wizard with 0 HTTP errors.
- **SC-003**: 100% of foundational files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, `state.json`) are generated in project `'the'`.
- **SC-004**: Automated/manual verification test suite passes completely.

## Assumptions

- Local FastAPI server is running during browser inspection and testing.
- Chrome DevTools MCP is configured and connected to the browser/app instance.
