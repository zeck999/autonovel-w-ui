# Data Model: Project Creation Wizard

**Feature**: 004-project-creation-wizard

## Entities

### 1. WizardStep / Section
Represents a section in the accordion wizard.
- `id`: string (e.g., "concept", "genre", "characters", "world")
- `title`: string
- `description`: string
- `fields`: List[WizardField]

### 2. WizardField
Represents an individual parameter field within a wizard step.
- `key`: string (e.g., "protagonist_name", "conflict", "tone")
- `label`: string
- `type`: string ("text", "textarea", "select")
- `placeholder`: string
- `examples`: List[string] (step-by-step example suggestions)
- `value`: string (user input or selected AI choice)

### 3. AIParameterSuggestion
Represents the 4 AI-generated choices for a given field.
- `field_key`: string
- `suggestions`: List[string] (exactly 4 distinct generated options)

### 4. ProjectCreationPayload
The complete payload submitted upon final validation.
- `name`: string
- `concept`: string
- `genre`: string
- `tone`: string
- `protagonist`: string
- `conflict`: string
- `world_setting`: string
- `universe_id`: Optional[str]
