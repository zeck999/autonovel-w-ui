# Research: Project Creation Wizard

**Feature**: 004-project-creation-wizard

## Decisions & Rationale

### Decision 1: Accordion UI Component in Vanilla JS / Web UI
- **Choice**: Build a reusable accordion component using standard HTML `<details>` or custom DOM state in `ui/js/views/projects.js` or a dedicated wizard component.
- **Rationale**: Keeps the frontend lightweight, adheres to existing vanilla JS architecture in `ui/`, and avoids heavy framework dependencies while providing clean collapsible sections.

### Decision 2: AI Choice Generation Endpoint
- **Choice**: Implement backend API endpoints (`POST /api/projects/wizard/suggest`) that leverage the existing LLM integration (`src/api.py` or pipeline adapter) to prompt for 4 structured choices given current wizard parameters.
- **Rationale**: Reuses existing LLM client capabilities securely on the backend while keeping frontend clean.

### Decision 3: Foundational & Lore Generation Pipeline
- **Choice**: Extend project creation logic in `src/projects.py` (or a dedicated `gen_wizard_lore.py` module) to synthesize `world.md`, `characters.md`, `canon.md`, `outline.md`, and `seed.txt` from the final wizard parameter dictionary.
- **Rationale**: Ensures complete autonomy and zero missing files upon project creation.
