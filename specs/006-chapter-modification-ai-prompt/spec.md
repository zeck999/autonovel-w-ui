# Feature Specification: Chapter Modification with AI & Toolbar Prompt Field (Option A)

**Feature Branch**: `006-chapter-modification-ai-prompt`

**Created**: 2026-10-20

**Status**: Completed

**Input**: User description: "Create Spec Kit specification, plan, and tasks for adding chapter modification with AI and a prompt field (Option A: toolbar prompt field) in autonovel-w-ui."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Prompt Toolbar in Chapter Editor (Priority: P1) 🎯 MVP
When the user selects and views a chapter in the Web UI Files/Editor view (`ui/js/views/files.js`), a dedicated AI modification toolbar is visible right above or within the editor header. It features a prompt input field for custom revision instructions (e.g., "Make the dialogue more suspenseful", "Add more sensory details to the forest scene") and an "Modifier avec l'IA" (Modify with AI) action button.

**Why this priority**: Enables creative vibe-coders to iteratively refine and polish individual chapters using natural language prompts directly inside their workflow without leaving the UI.

**Independent Test**: Open the Files view, select any chapter in `chapters/`, verify the AI prompt input field and "Modifier avec l'IA" button appear in the editor toolbar.

**Acceptance Scenarios**:
1. **Given** a chapter file (e.g., `chapters/chapter_01.md`) is open in the editor, **When** the user looks at the editor top action bar, **Then** an AI prompt input box and "Modifier avec l'IA" button are present.
2. **Given** foundation files (e.g., `seed.txt`, `world.md`) are open, **When** viewed in the editor, **Then** the AI chapter modification toolbar is hidden or disabled (as it applies specifically to chapters).

---

### User Story 2 - AI Chapter Modification Execution & Response (Priority: P1)
When the user types a prompt instruction into the toolbar and clicks "Modifier avec l'IA", the backend processes the request by feeding the current chapter content and prompt instruction to the AI revision model (or adapter), returning the rewritten/modified chapter text into the active editor textarea with a loading state indication and success feedback.

**Why this priority**: Delivers the core autonomous generation value of ZPI harnesses, allowing creative intent to directly reshape prose.

**Independent Test**: Enter an instruction in the prompt field, click "Modifier avec l'IA", observe loading state, and verify the textarea updates with the AI-modified chapter content.

**Acceptance Scenarios**:
1. **Given** the user enters a prompt in the toolbar and clicks "Modifier avec l'IA", **When** the request is sent to `/api/projects/{id}/chapters/modify`, **Then** the button shows a loading state (e.g., "IA en cours..."), and upon completion, the textarea content is updated with the modified chapter text.
2. **Given** the AI modification completes, **When** the editor updates, **Then** a success status is displayed and the user can review or save the changes.

---

### User Story 3 - Graceful Error Handling & Fallback for AI Calls (Priority: P2)
When the AI backend service encounters errors (such as missing API keys, rate limits 429, timeouts, or network failures), the system gracefully intercepts the error, prevents unhandled Python tracebacks, and displays a user-friendly error message in the UI with a stable support code (e.g., `ERR_AI_MOD_UNAUTHORIZED_401`, `ERR_AI_MOD_TIMEOUT`).

**Why this priority**: Ensures robust user experience even in offline or unconfigured API key test environments.

**Independent Test**: Simulate an API failure or unconfigured key during chapter AI modification and verify a clean error message and support code appear in the UI.

**Acceptance Scenarios**:
1. **Given** an API failure occurs during AI modification, **When** the response returns an error, **Then** the UI displays a clear notification banner/status without freezing or crashing.

---

### Edge Cases
- What happens if the prompt field is empty when the user clicks "Modifier avec l'IA"? -> The system prompts the user to enter a brief instruction (e.g., "Veuillez saisir une instruction pour l'IA").
- What happens if no chapter is selected? -> The AI toolbar is hidden.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Backend MUST provide an API endpoint (e.g., `POST /api/projects/{id}/chapters/modify`) accepting a chapter file path, current content, and prompt instruction, and returning the AI-modified chapter content.
- **FR-002**: Web UI Files view (`ui/js/views/files.js`) MUST render an AI toolbar (prompt input and "Modifier avec l'IA" button) when a chapter file (`chapters/...`) is selected.
- **FR-003**: Clicking "Modifier avec l'IA" MUST trigger the API call while disabling the button and displaying a loading indicator.
- **FR-004**: Upon successful response, the editor textarea MUST be populated with the modified chapter content and a success status shown.
- **FR-005**: System MUST handle API failures and unconfigured keys gracefully with clear user messages and error codes.

### Key Entities

- **ChapterModificationRequest**: Represents the payload (`file_path`, `content`, `prompt`) sent to the AI modification endpoint.
- **ChapterModificationResponse**: Represents the result (`file_path`, `content`, `status`, `message`) returned by the backend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The AI modification toolbar appears within < 100ms when a chapter is selected.
- **SC-002**: AI modification request successfully dispatches and updates the editor content upon completion.
- **SC-003**: 100% test coverage for the new chapter modification API endpoint and UI integration.

## Assumptions

- Chapter files are located within the `chapters/` subdirectory of the active project.
- AI revision utilizes existing pipeline revision helpers (`gen_revision.py` or direct LLM client calls via `src/pipeline_adapter.py` / `src/api.py`).
