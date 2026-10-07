# PROJECT_MEMORY.md — Mémo de Projet Autonovel & Spécifications Spec Kit

**Date de création** : 2026-10-04  
**Statut** : Acté, validé et synchronisé avec le Spec Kit (Commit `90ab158`)  
**Périmètre** : Projet Autonovel — Pipeline autonome de rédaction de romans par IA avec back-office FastAPI et Web UI interactive (SPA).

---

## 1. Vision et Contexte Produit

Autonovel est un système de vibe coding et d'ingénierie créative autonome permettant de concevoir, rédiger, réviser, évaluer, illustrer et mettre en forme des romans complets à partir d'un concept initial (`seed.txt`). Inspiré des boucles de recherche itérative (type `autoresearch`), Autonovel applique un cycle d'ingénierie logicielle rigoureux (fondation, rédaction, révision contradictoire, revues par double persona, export typographique et audio) à l'art littéraire.

La finalité de l'intégration de la Web UI et du back-office FastAPI est de doter Autonovel d'une interface graphique moderne, fluide et autonome, permettant au « vibe coder » de piloter l'ensemble du pipeline, d'gérer ses projets et univers, d'explorer les branches narratives et d'éditer directement les fichiers de lore et de fondation sans quitter l'interface web.

---

## 2. Architecture Modulaire & Composants Validés

Le projet repose sur une architecture modulaire strictement cloisonnée :

1. **Back-office API (`src/`)** :
   - `src/api.py` : Application FastAPI exposant les endpoints REST `/api/projects`, `/api/universes`, `/api/versioning/*`, `/api/pipeline/*`, ainsi que les routes statiques et le fallback SPA pour la Web UI.
   - `src/projects.py` : Gestion CRUD des projets, initialisation des structures de dossiers et isolation.
   - `src/universes.py` : Gestion des univers partagés et de l'héritage de lore.
   - `src/versioning.py` : Gestion des branches narratives et de l'historique des révisions avec scores.
   - `src/pipeline_adapter.py` : Adaptateur d'exécution du pipeline (`run_pipeline.py`, `evaluate.py`, etc.) avec **synchronisation bidirectionnelle multi-projet** (`sync_project_to_root` / `sync_root_to_project`) et isolation par projet (`projects/{project_id}`).
   - `src/settings.py` : Service de gestion, lecture, écriture et masquage sécurisé des clés API dans le fichier `.env`, incluant les tests de connexion pour Anthropic, ElevenLabs et Fal.ai.

2. **Web UI SPA (`ui/`)** :
   - `ui/index.html` : Fichiers statiques uniques et point d'entrée SPA avec chargement asynchrone des modules CSS/JS.
   - `ui/css/style.css` : Thème visuel élégant (EB Garamond / Bebas Neue, palettes `#0a0a08`, `#e8e4db`, `#daa548`).
   - `ui/js/` : Modules autonomes (`api.js`, `store.js`, `router.js`, `inspector.js` et vues `dashboard.js`, `projects.js`, `universes.js`, `branches.js`, `pipeline.js`, `foundation.js`).
   - `ui/js/views/settings.js` : Vue Paramètres et Clés API avec masquage, sauvegarde et tests de connexion en temps réel.

3. **Pipeline & Outils CLI (`*.py`, `specs/`, `typeset/`)** :
   - Scripts Python de fondation (`seed.py`, `gen_world.py`, `gen_characters.py`, `gen_outline.py`, `gen_canon.py`), de rédaction (`draft_chapter.py`), d'évaluation (`evaluate.py`, `adversarial_edit.py`, `review.py`), de révision (`gen_revision.py`) et d'export (`typeset/build_tex.py`, `gen_audiobook.py`).

---

## 3. État Actuel Validé & Preuves Durables

- **Tests unitaires et d'intégration** : Suite complète de tests validés (`pytest tests/`), incluant `test_api.py`, `test_pipeline.py`, `test_projects.py`, `test_universes.py`, `test_versioning.py` et `test_settings.py`.
- **Intégration Web UI** :
  - Dashboard interactif (projets récents, statut global du pipeline, actions rapides).
  - Gestion complète des projets et univers partagés.
  - Pilotage du pipeline en temps réel avec volet d'inspection rétractable et logging dynamique (polling, mise en évidence des erreurs, masquage des secrets).
  - Mode review-only (évaluation critique via `/api/pipeline/evaluate`).
  - Édition et sauvegarde asynchrone des fichiers de fondation et de lore (`world.md`, `characters.md`, `outline.md`, `canon.md`).
- **Hygiène du worktree & verrouillage strict du scope** :
  - Le répertoire de stockage des projets générés (`projects/`) est strictement exclu du versioning Git (`.gitignore`).
  - **Interdiction absolue de manipulation ou de commit sur les dossiers de projets générés non suivis** par les agents, garantissant un worktree propre, étanche et focalisé sur le code source et les spécifications Spec Kit.

---

## 4. Réconciliation Spec Kit

Ce mémo de projet (`PROJECT_MEMORY.md`) est officiellement rattaché aux spécifications Spec Kit du répertoire `specs/001-web-ui-autonovel/` ainsi qu'à la spécification de la fonctionnalité de gestion des clés API (`specs/settings/`, tâches T001 à T011 entièrement achevées et validées). Toute évolution future du projet devra maintenir la cohérence entre ce mémo, les spécifications vivantes et la suite de tests validés.
