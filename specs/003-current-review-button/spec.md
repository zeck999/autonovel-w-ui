# Feature Specification: Current Review Button in Top Menu Bar

**Feature Branch**: `003-current-review-button`

**Created**: 2026-10-06

**Status**: Implemented & Validated

**Input**: User description: "Create Spec Kit specify, plan, and tasks under specs/003-current-review-button/ for adding a Current Review button in the top menu bar displaying live status, review criteria, and file path tooltip on hover."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Current Review Status Button in Top Navigation (Priority: P1) 🎯 MVP
The user sees a prominent "Current Review" button in the top menu bar (`ui/index.html` header) across all Web UI views, displaying a live status badge (e.g., star rating, score, or "No Review" status) derived from the latest manuscript review logs (`edit_logs/*_review.json` or `eval_logs/`).

**Why this priority**: Gives vibe coders instant visibility into manuscript quality and review status without navigating away from their current workspace.

**Independent Test**: Open `/`, verify the "Current Review" button is visible in the header and correctly reflects review state (score/stars or unreviewed state).

**Acceptance Scenarios**:
1. **Given** the Web UI is loaded, **When** the user looks at the top navigation bar, **Then** the "Current Review" button is present with a status badge showing the latest evaluation score or star rating.
2. **Given** a review has been run via `review.py` or `/api/pipeline/evaluate`, **When** the backend state or review logs update, **Then** the button polls or refreshes to display the updated live status.

---

### User Story 2 - Review Criteria Modal and Details on Click (Priority: P1)
When the user clicks the "Current Review" button, an interactive popover or modal opens displaying the comprehensive review breakdown: literary critic summary, professor craft suggestions, severity breakdown, and whether revision criteria are satisfied.

**Why this priority**: Empowers the user to inspect qualitative and quantitative critique instantly to guide the next writing iteration.

**Independent Test**: Click the "Current Review" button and verify that a modal/popover opens displaying review details, scores, and actionable items.

**Acceptance Scenarios**:
1. **Given** the "Current Review" button is clicked, **When** review logs exist, **Then** a modal opens showing star ratings, critic summary, and numbered professor suggestions.
2. **Given** no review logs exist yet, **When** clicked, **Then** the modal gracefully informs the user that no review has been run yet with a prompt to trigger an evaluation.

---

### User Story 3 - File Path Tooltip on Hover (Priority: P2)
When the user hovers over the "Current Review" button, a tooltip appears displaying the exact source file path (e.g., `edit_logs/YYYYMMDD_HHMMSS_review.json`) and timestamp of the review data.

**Why this priority**: Provides absolute transparency and traceability into the underlying artifacts powering the harness UI.

**Independent Test**: Hover the mouse over the "Current Review" button and verify the tooltip correctly shows the review JSON file path and timestamp.

**Acceptance Scenarios**:
1. **Given** the user hovers over the "Current Review" button, **When** active review data is loaded, **Then** a title/tooltip attribute displays `Source: edit_logs/<timestamp>_review.json`.

---

### Edge Cases
- What happens when `edit_logs/` is empty? → The button shows "Unreviewed" or "No Review" and clicking it prompts the user to run a review.
- What happens if the API endpoint for reviews fails? → The button gracefully falls back to cached state or shows a disconnected status without breaking the header navigation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a backend API endpoint (e.g., `GET /api/reviews/latest`) that reads the most recent review log from `edit_logs/` (or evaluation logs) and returns its summary, scores, items, and file path.
- **FR-002**: Web UI header (`ui/index.html` and `ui/css/style.css`) MUST include a "Current Review" button positioned in the top navigation bar.
- **FR-003**: The "Current Review" button MUST display a live status indicator (such as star rating or score percentage).
- **FR-004**: Hovering over the "Current Review" button MUST display a tooltip with the relative file path of the review source (e.g., `edit_logs/...`).
- **FR-005**: Clicking the "Current Review" button MUST open an interactive modal/popover displaying the detailed review criteria, critic summary, and professor suggestions.
- **FR-006**: The system MUST handle missing review logs gracefully with informative empty states and actions.

### Key Entities

- **ReviewSummary**: Represents the latest manuscript review (`timestamp`, `title`, `stars`, `total_items`, `major_items`, `qualified_items`, `file_path`, `critic_summary`, `professor_items`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The "Current Review" button is rendered in the top header on all SPA views and loads review status in under 500ms.
- **SC-002**: Clicking the button opens the review criteria modal in < 100ms.
- **SC-003**: Hovering over the button accurately displays the source file path tooltip.
- **SC-004**: 100% test coverage for new review API endpoints and UI component logic.

## Assumptions

- Review logs are stored in `edit_logs/*_review.json` following the existing format produced by `review.py`.
- The Web UI runs locally on FastAPI alongside the backend routes.
