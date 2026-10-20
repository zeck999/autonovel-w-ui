---
description: "Task list for Chapter Modification with AI & Toolbar Prompt Field feature implementation"
---

# Tasks: Chapter Modification with AI & Toolbar Prompt Field (Option A)

**Input**: Design documents from `/specs/006-chapter-modification-ai-prompt/`

**Prerequisites**: plan.md, spec.md

## Phase 1: Setup & Backend API

**Purpose**: Implement backend endpoint to process chapter AI modification requests.

- [ ] T001 Create backend unit test for chapter AI modification in tests/test_chapter_ai.py
- [ ] T002 Implement POST /api/projects/{id}/chapters/modify endpoint in src/api.py utilizing pipeline revision / LLM adapter

---

## Phase 2: Foundational UI & Styles

**Purpose**: Add AI prompt toolbar styling and layout in the chapter editor.

- [ ] T003 Add CSS styling for AI toolbar, prompt input, and "Modifier avec l'IA" button in ui/css/style.css

---

## Phase 3: User Story 1 - AI Prompt Toolbar in Chapter Editor (Priority: P1) 🎯 MVP

**Goal**: Render AI prompt input and button in the editor toolbar when a chapter file is selected.

- [ ] T004 [US1] Update `ui/js/views/files.js` to conditionally render AI toolbar (prompt input + button) only when a chapter file (`chapters/...`) is selected

---

## Phase 4: User Story 2 - AI Chapter Modification Execution & Response (Priority: P1)

**Goal**: Wire up API call, loading indicator, and editor text update upon successful AI modification.

- [ ] T005 [US2] Implement `modifyChapterWithAI(projectId, filePath, content, prompt)` method in `ui/js/api.js`
- [ ] T006 [US2] Wire up event listener on "Modifier avec l'IA" button in `ui/js/views/files.js` to send prompt, display loading state, and update editor textarea with returned content

---

## Phase 5: User Story 3 - Graceful Error Handling & Fallback for AI Calls (Priority: P2)

**Goal**: Handle API failures, timeouts, and unconfigured keys gracefully with user-friendly messages and error codes.

- [ ] T007 [US3] Implement robust error catching in backend API endpoint and map exceptions to structured error responses with stable support codes
- [ ] T008 [US3] Handle error responses gracefully in frontend UI with notification banner/status message

---

## Phase 6: Polish & Validation

**Purpose**: Verify all tests pass and end-to-end functionality is robust.

- [ ] T009 Run pytest tests/test_chapter_ai.py and verify test success
- [ ] T010 Verify UI responsiveness and edge cases (empty prompt, non-chapter files)
