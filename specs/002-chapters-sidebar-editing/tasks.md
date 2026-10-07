# Tâches : Section 'Chapitres' dans la Barre Latérale & Édition Directe

**Entrée** : Documents de conception de `/specs/002-chapters-sidebar-editing/`

**Organisation** : Les tâches sont regroupées par user story et phase pour permettre une implémentation et un test indépendants.

## Format : `[ID] [P?] [Story] Description`

- **[P]** : Peut s'exécuter en parallèle (fichiers différents, pas de dépendances bloquantes)
- **[Story]** : User Story associée (US1, US2, US3)

---

## Phase 1 : Back-Office & API (`src/projects.py`)

- [ ] T001 [US1] Mettre à jour `list_project_files` dans `src/projects.py` pour scanner le répertoire `projects/{id}/chapters/` et inclure les fichiers avec le chemin relatif `chapters/<filename>`.
- [ ] T002 [US1] Vérifier que `get_project_file` et `save_project_file` gèrent correctement les chemins relatifs de chapitres (ex. `chapters/chapter_01.md`).

---

## Phase 2 : Front-End Web UI (`ui/js/views/files.js`)

- [ ] T003 [US1] [US2] Mettre à jour `ui/js/views/files.js` pour séparer l'affichage de la barre latérale en deux sections : « Fichiers de Fondation & Lore » et « Chapitres ».
- [ ] T004 [US2] Mettre à jour la gestion des clics et de l'éditeur dans `ui/js/views/files.js` pour charger et sauvegarder les fichiers de chapitres via l'API.
- [ ] T005 [US3] Ajouter un formulaire de création rapide de nouveau chapitre (ex. `chapter_01.md`) dans la section Chapitres.

---

## Phase 3 : Tests & Validation

- [ ] T006 [P] Ajouter des tests unitaires dans `tests/test_projects.py` pour tester le listage des fichiers de chapitres.
- [ ] T007 Exécuter la suite complète des tests (`pytest`) pour s'assurer de la non-régression et du succès de la validation.
