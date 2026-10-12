# Feature Specification: Project Creation Wizard

**Feature Branch**: `004-project-creation-wizard`

**Created**: 2026-03-24

**Status**: Completed

**Input**: User description: "Generate specifications, implementation plan, and task list for the project creation Wizard feature with full foundational/lore files generation, accordion/section layout, step-by-step examples, free-choice input, and 4 AI-generated choices per parameter before final validation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guided Project Creation Wizard UI with Accordion Layout (Priority: P1)

As a creative writer using Autonovel, I want to create a new project through an intuitive accordion/section-based wizard interface with step-by-step examples, so that I can define my novel's premise, genre, characters, and world without feeling overwhelmed by a single giant form.

**Why this priority**: P1 delivers the core user-facing workflow and reduces cognitive load during project inception, which is critical for creative flow.

**Independent Test**: Can be fully tested by opening the project creation wizard in the web UI, navigating through accordion sections, viewing examples, and verifying the layout renders correctly.

**Acceptance Scenarios**:

1. **Given** the user opens the new project modal or page, **When** the wizard loads, **Then** it presents an accordion/section layout (e.g., Concept, Genre & Tone, Characters, World Lore) with clear step-by-step guidance and examples.
2. **Given** the user is viewing a wizard section, **When** they click to expand/collapse sections, **Then** sections toggle smoothly while preserving entered state.

---

### User Story 2 - Free-Choice Input and 4 AI-Generated Choices per Parameter (Priority: P2)

As a creator, I want the ability to either type custom free-choice inputs for any parameter or request 4 AI-generated choices to inspire me, so that I have complete creative control while benefiting from AI ideation when stuck.

**Why this priority**: P2 implements the core intelligence feature (AI choices + free-form input) that makes the wizard powerful for vibe coding.

**Independent Test**: Can be tested by clicking the "Generate AI Choices" button on a wizard parameter field, verifying that 4 distinct suggestions are returned and selectable, or typing custom text.

**Acceptance Scenarios**:

1. **Given** the user is on a parameter field (e.g., protagonist motivation or world setting), **When** they click "Generate AI Choices", **Then** the system fetches and displays 4 distinct AI-generated options.
2. **Given** 4 AI choices are displayed, **When** the user clicks one, **Then** it populates the parameter input field, while still allowing manual editing or entering completely free-choice text.

---

### User Story 3 - Final Validation and Full Foundational/Lore Files Generation (Priority: P3)

As a creator, I want to review my final wizard summary before validation and have the system automatically generate and save all foundational and lore files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`), so that my project is fully initialized and ready for drafting.

**Why this priority**: P3 ensures end-to-end integration from wizard input to robust file structure creation.

**Independent Test**: Can be tested by completing the wizard, submitting the final validation, and inspecting the newly created project directory under `projects/` to verify all lore files and state exist.

**Acceptance Scenarios**:

1. **Given** the user has filled out the wizard sections, **When** they reach the final validation step and click "Create Project", **Then** the system displays a summary review of all parameters.
2. **Given** the user confirms creation, **When** the backend processes the request, **Then** it generates `seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json` inside the project directory and redirects to the project dashboard.

---

### Edge Cases

- What happens when AI generation times out or fails? The system provides graceful fallback to manual free-choice input with an error notification.
- How does the system handle empty required fields during final validation? It highlights incomplete accordion sections and prevents submission until resolved.
- What happens if a project name collision occurs? The backend automatically appends a numeric suffix to ensure unique directory creation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an interactive wizard interface organized into accordion/section steps (Concept, Genre/Tone, Characters, Lore/World).
- **FR-002**: Each wizard step/parameter MUST display contextual step-by-step examples and helper descriptions to guide the user.
- **FR-003**: Users MUST be able to provide custom free-choice text input for any wizard parameter.
- **FR-004**: For each parameter, the system MUST provide an action to generate exactly 4 AI-driven choice options based on prior context.
- **FR-005**: The system MUST provide a final review/validation screen summarizing all wizard parameters before project creation.
- **FR-006**: Upon final validation, the backend MUST automatically generate project workspace files including `seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`.
- **FR-007**: The system MUST handle AI generation failures gracefully by allowing manual entry and displaying a clear message.

### Key Entities

- **WizardSession / WizardState**: Temporary state tracking user selections across accordion sections during project creation.
- **AIParameterChoice**: Structured response containing 4 alternative suggestions for a given novel parameter.
- **ProjectWorkspace**: The resulting isolated project directory containing generated markdown lore files and state metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the full project creation wizard in under 3 minutes.
- **SC-002**: AI choice generation returns 4 distinct options in under 3 seconds per request.
- **SC-003**: 100% of validated wizard submissions successfully generate all required foundational files (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, `state.json`).
- **SC-004**: 90% of users successfully complete project creation on the first attempt without validation errors.

## Assumptions

- Users have internet connection or active local LLM configuration for AI choice generation.
- Default templates exist for fallback generation if AI service is unavailable.
- Project storage utilizes the local file system under the `projects/` directory.
