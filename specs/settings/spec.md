# Feature Specification: AI Keys Test and Edit Feature

**Feature Branch**: `settings-ai-keys`

**Created**: 2026-10-06

**Status**: Implemented / Verified (Covered by `tests/test_settings.py`)

**Input**: User description: "Reconstruct specs and tasks for the AI keys test and edit feature in specs/settings/ tasks.md and plan.md."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Edit AI API Keys (Priority: P1) 🎯 MVP
The user opens the Settings view in the Web UI to view the current status of their AI provider API keys (`ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`), sees masked representations of configured keys (e.g., `sk-ant-api03-****abcd`), and can update or replace them via an intuitive form.

**Why this priority**: Essential for vibe coders and users configuring their AI providers without needing manual file editing of `.env`.

**Independent Test**: Can be fully tested by opening the Settings view, entering a new API key, saving, and verifying it updates the backend `.env` securely.

**Acceptance Scenarios**:
1. **Given** the Web UI is open, **When** the user navigates to the "Settings / API Keys" view, **Then** the system fetches and displays the configuration status of all supported AI keys with masked values.
2. **Given** the Settings view is open, **When** the user enters a new API key and clicks "Save Keys", **Then** an API request (`PUT /api/settings/keys`) updates the `.env` file and displays a success notification.

---

### User Story 2 - Test AI API Key Connections (Priority: P1)
The user clicks a "Test Connection" button next to any configured or newly entered API key to verify its validity and connectivity against the respective provider API (Anthropic, ElevenLabs, Fal.ai).

**Why this priority**: Prevents pipeline failures by validating keys before running expensive or long-running generation phases.

**Independent Test**: Can be tested by clicking "Test Connection" for Anthropic API key and verifying a success/failure indicator based on a lightweight API ping.

**Acceptance Scenarios**:
1. **Given** an API key is entered or configured, **When** the user clicks "Test" next to the provider, **Then** `POST /api/settings/keys/test` is called and returns a success status with latency or an informative error message on failure.
2. **Given** an invalid or expired API key, **When** tested, **Then** the UI clearly displays an error message explaining the authentication failure without exposing sensitive key material.

---

### User Story 3 - Secure Masking and Secret Protection (Priority: P2)
The system ensures that raw API keys are never exposed in plaintext logs, error messages, or unmasked API responses.

**Why this priority**: Protects user credentials and maintains security compliance.

**Independent Test**: Verify that `GET /api/settings/keys` returns keys in masked format (`****xxxx`) and server logs redact any key strings.

**Acceptance Scenarios**:
1. **Given** API keys are stored in `.env`, **When** fetched via API, **Then** only masked previews (last 4 characters) are transmitted to the client.
2. **Given** pipeline or settings errors occur, **When** logged or returned in responses, **Then** regex masking patterns scrub `sk-`, `ai_`, `api_key`, and secret tokens.

---

### Edge Cases
- What happens when `.env` does not exist yet? → The system automatically initializes a new `.env` file based on `.env.example`.
- What happens during a timeout when testing an API key? → The test endpoint catches network timeouts and returns a clean error response ("Connection timeout with provider").
- How are empty keys handled? → Treated as unconfigured ("Not set").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a REST API endpoint `GET /api/settings/keys` returning configuration status and masked previews of `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, and `FAL_KEY`.
- **FR-002**: System MUST provide a REST API endpoint `PUT /api/settings/keys` to update one or more API keys and persist them securely into the local `.env` file.
- **FR-003**: System MUST provide a REST API endpoint `POST /api/settings/keys/test` to test connectivity and authentication for a specified provider.
- **FR-004**: Web UI MUST provide a dedicated Settings view (`ui/js/views/settings.js`) with input fields, mask/unmask toggles, save actions, and per-key test buttons with real-time feedback.
- **FR-005**: System MUST mask API keys in all API responses and console logs.
- **FR-006**: System MUST automatically create or update `.env` preserving existing unedited variables.

### Key Entities

- **ApiSettings**: Represents the configuration state of API keys (`provider`, `configured` boolean, `masked_value`).
- **TestResult**: Represents the outcome of an API key test (`success` boolean, `message`, `latency_ms`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view, update, and test their AI API keys entirely within the Web UI in under 30 seconds.
- **SC-002**: Zero plaintext API keys appear in API responses or server logs.
- **SC-003**: 100% of settings API endpoints are covered by automated unit and integration tests (`tests/test_settings.py`).
- **SC-004**: API key connection tests return response within 5 seconds under normal network conditions.

## Assumptions

- Users have valid API keys from Anthropic, ElevenLabs, or Fal.ai.
- The backend has write permissions to the repository root `.env` file.
- Network access to provider APIs is available when testing keys (or graceful error handling occurs when offline).
