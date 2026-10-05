---
description: "Tâches pour l'implémentation de la VRAIE Web UI HTML/CSS/JS interactive pour Autonovel, incluant l'édition des fichiers de fondation et de lore"
---

# Tâches : Web UI Autonovel (HTML/CSS/JS autonome, FastAPI) - Clôturées (Commit `90ab158`)

**Entrée** : Documents de conception de `/specs/001-web-ui-autonovel/`

**Statut** : Toutes les phases (0 à 6) sont pleinement implémentées, testées et validées. Réconcilié et acté au commit `90ab158`.

**Préréquis** : Back-office API existant et testé (`src/api.py`, `src/projects.py`, `src/universes.py`, `src/versioning.py`, `src/pipeline_adapter.py` avec synchronisation multi-projet corrigée et validée) — marqué comme `[x]` ci-dessous (acquis par réconciliation).

---

## Phase 0 : Rétrocompatibilité Back-office & Squelette UI (Fondations)

- [x] T001 [US1] Valider le back-office existant via `pytest tests/` (garantir les contrats `/api/...`).
- [x] T002 Créer l'arborescence `ui/` et le fichier squelette `ui/index.html` (doctype, viewport, polices et styles de base).
- [x] T003 Ajouter les routes statiques et SPA dans `src/api.py` (`@app.get("/")`, `StaticFiles` pour `ui/css` et `ui/js`, et catch-all `/{path:path}` respectant l'ordre avant `/api/*`).

---

## Phase 1 : Infrastructure Frontend & Dashboard (Priorité : P1) 🎯 MVP

- [x] T011 [P] [US1] Implémenter la couche `ui/js/api.js` (`fetch()` avec gestion d'erreurs, états de connexion, `AbortController`).
- [x] T012 [P] [US1] Implémenter le store global (`ui/js/store.js`) et le routeur SPA (`ui/js/router.js`, support `/#/projects`, `/#/universes`, `/#/branches`, `/#/pipeline`).
- [x] T013 [US1] Implémenter le thème global (`ui/css/style.css`) aux couleurs d'Autonovel (`#0a0a08`, `#e8e4db`, `#daa548`, EB Garamond / Bebas Neue).
- [x] T014 [US1] Créer la vue Dashboard (`ui/js/views/dashboard.js`) affichant la liste des projets récents, le statut global du pipeline et les actions rapides.

---

## Phase 2 : Gestion des Projets & Univers Partagés (Priorité : P1 / P2)

- [x] T021 [US1] Créer la vue Projets (`ui/js/views/projects.js`) pour créer un projet (formulaire nom/concept/univers), basculer et supprimer (`DELETE /api/projects/{id}`).
- [x] T022 [US2] Créer la vue Univers (`ui/js/views/universes.js`) pour lister les univers, afficher le nombre de projets liés, et permettre de rattacher un projet à un univers existant.

---

## Phase 3 : Versioning & Branches Narratives (Priorité : P3)

- [x] T031 [US3] Créer la vue Branches (`ui/js/views/branches.js`) pour lister les branches (`/api/versioning/branches`), en créer une, basculer (`/api/versioning/switch`), et afficher l'historique des révisions et des scores (`/api/versioning/history`).

---

## Phase 4 : Pipeline, Monitoring, Logging Temps Réel & Mode Review-Only (Priorité : P1 & P5)

- [x] T040 [US1] Corriger et valider la synchronisation multi-projet dans l'adaptateur de pipeline (`src/pipeline_adapter.py`) pour cibler correctement le répertoire projet (`projects/{project_id}`) et son état (`state.json`).
- [x] T041 [US1] Créer la vue Pipeline & Monitoring (`ui/js/views/pipeline.js`) pour exécuter une phase (`POST /api/pipeline/run`), afficher l'état courant et lancer des évaluations (`POST /api/pipeline/evaluate`).
- [x] T042 [US5] Implémenter le volet d'inspection et de logs rétractable (`ui/js/inspector.js`), accessible par bouton toggle ou raccourci (`Alt+I`/`Esc`), avec polling asynchrone, mise en évidence des erreurs et masquage des secrets.
- [x] T043 [US1/US5] Acter et implémenter le **logging temps réel du pipeline** via polling asynchrone (`state.json` / logs) et affichage dynamique dans le volet d'inspection, avec coloration des erreurs/succès et protection des secrets.
- [x] T044 [US1/US4] Acter et intégrer le **mode review-only** (phase de review et évaluation critique indépendante via `/api/pipeline/evaluate`) permettant l'audit littéraire sans modification destructive des chapitres.

---

## Phase 5 : Édition des Fichiers de Fondation et de Lore (Priorité : P2)

- [x] T050 [US6] Implémenter les endpoints API de lecture et écriture des fichiers de projet (`GET /api/projects/{id}/files/{filename}` et `PUT /api/projects/{id}/files/{filename}`) pour `world.md`, `characters.md`, `outline.md`, `canon.md`.
- [x] T051 [US6] Créer la vue Fondation & Lore (`ui/js/views/files.js` / `ui/js/views/foundation.js`) permettant de sélectionner, éditer et sauvegarder les fichiers de fondation/lore du projet actif.

---

## Phase 6 : Polissage, Responsive & Documentation

- [x] T061 [P] Ajuster le design responsive (mobile ≤ 480 px : navigation en drawer, volet d'inspection en modal).
- [x] T062 Valider le parcours complet (SC-001..SC-006) en local (`uv run uvicorn src.api:app --port 8000`) et vérifier que tous les tests `pytest tests/` restent PASS.
- [x] T063 Mettre à jour `README.md`, `PIPELINE.md` et les artéfacts Spec Kit pour acter l'implémentation de la Web UI interactive, du logging temps réel du pipeline et du mode review-only.
- [x] T064 Acter dans Spec Kit (`spec.md`, `plan.md`, `tasks.md`) le nettoyage complet du worktree et l'exclusion propre de `projects/` dans `.gitignore`.

---

## Dépendances & Séquencement

- **Phase 0** bloque toutes les phases UI (dépend du back-office existant).
- **Phase 1 (Dashboard)** est le premier livrable MVP (US1).
- **Phase 2 & 3** peuvent s'exécuter en parallèle après Phase 1.
- **Phase 4, 5 & 6** finalisent l'expérience utilisateur progressive, l'édition de lore et la documentation.
