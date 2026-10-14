# Quickstart Validation Guide: Project Creation Wizard

**Feature**: 004-project-creation-wizard

## Prerequisites
- Running Autonovel backend API and Web UI (Python 3.11+, FastAPI, static frontend).

## End-to-End Validation Steps

1. **Launch App**:
   Start the development server:
   ```bash
   python main.py
   ```
2. **Open Assistant Créatif Wizard**:
   Click the "Assistant Créatif" button in the navigation bar right next to Dashboard in the Web UI to launch the interactive Assistant Créatif wizard view.
3. **Interact with Accordion Layout**:
   - Expand accordion sections (Concept, Genre/Tone, Characters, World).
   - Observe step-by-step examples and helper text.
4. **Test AI 4-Choices Generation**:
   - Click "Generate 4 AI Choices" on any parameter field.
   - Verify 4 options appear and click one to populate the field.
5. **Final Validation & Creation**:
   - Proceed to the review screen.
   - Click "Create Project".
   - Verify redirect to the project dashboard and inspect `projects/<project-id>/` to confirm existence of `seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, and `state.json`.
