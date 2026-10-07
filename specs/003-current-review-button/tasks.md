---
description: "Task list for Current Review Button feature implementation"
---

# Tasks: Current Review Button in Top Menu Bar

**Input**: Design documents from `/specs/003-current-review-button/`

**Prerequisites**: plan.md, spec.md

## Phase 1: Setup & Backend API

**Purpose**: Implement backend endpoint to fetch the latest manuscript review summary and file path.

- [ ] T001 Create backend unit test for review API in tests/test_reviews.py
- [ ] T002 Implement GET /api/reviews/latest endpoint in src/api.py to read latest review from edit_logs/

---

## Phase 2: Foundational UI & Styles

**Purpose**: Add Current Review button structure to HTML header and style it with CSS.

- [ ] T003 Add Current Review button element in ui/index.html header navigation
- [ ] T004 Add CSS styling for review button, status badge, and hover tooltip in ui/css/style.css
- [ ] T005 Add review details modal container and CSS styles in ui/index.html and ui/css/style.css

---

## Phase 3: User Story 1 - Current Review Status Button in Top Navigation (Priority: P1) 🎯 MVP

**Goal**: Display live review status badge on the top menu button.

- [ ] T006 [US1] Implement fetchLatestReview() method in ui/js/api.js
- [ ] T007 [US1] Initialize review status fetch on app startup and update button badge in ui/index.html or ui/js/store.js

---

## Phase 4: User Story 2 - Review Criteria Modal and Details on Click (Priority: P1)

**Goal**: Open review modal with star ratings, critic summary, and professor suggestions when clicked.

- [ ] T008 [US2] Implement click handler on Current Review button to open modal with review details in ui/index.html or UI controller
- [ ] T009 [US2] Render star ratings, critic summary, and professor suggestions inside the review modal

---

## Phase 5: User Story 3 - File Path Tooltip on Hover (Priority: P2)

**Goal**: Display exact review JSON file path and timestamp on button hover.

- [ ] T010 [US3] Populate button title/tooltip attribute with review source file path (`edit_logs/...`) on hover in UI script

---

## Phase 6: Polish & Validation

**Purpose**: Test integration, verify tests pass, and clean up code.

- [ ] T011 Run pytest tests/test_reviews.py and verify 100% pass rate
- [ ] T012 Verify responsiveness and edge cases (empty edit_logs directory)
