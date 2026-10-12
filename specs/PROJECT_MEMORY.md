# PROJECT_MEMORY.md — Mémo de Projet Autonovel & Spécifications Spec Kit

**Date de création** : 2026-10-04  
**Date de mise à jour REQ-20261012095042** : 2026-10-12  
**Statut** : Acté, validé et synchronisé avec le Spec Kit  
**Périmètre** : Projet Autonovel — Pipeline autonome de rédaction de romans par IA avec back-office FastAPI, Web UI interactive (SPA), et gestion multi-projet.

---

## 1. Vision et Contexte Produit

Autonovel est un système de vibe coding et d'ingénierie créative autonome permettant de concevoir, rédiger, réviser, évaluer, illustrer et mettre en forme des romans complets à partir d'un concept initial (`seed.txt`). Inspiré des boucles de recherche itérative (type `autoresearch`), Autonovel applique un cycle d'ingénierie logicielle rigoureux à l'art littéraire.

La finalité de l'intégration de la Web UI et du back-office FastAPI est de doter Autonovel d'une interface graphique moderne, fluide et autonome, permettant au « vibe coder » de piloter l'ensemble du pipeline, de gérer ses projets et univers, d'explorer les branches narratives et d'éditer directement les fichiers de lore et de fondation sans quitter l'interface web.

---

## 2. Architecture Modulaire & Composants Validés

Le projet repose sur une architecture modulaire strictement cloisonnée :

1. **Back-office API (`src/`)** :
   - `src/api.py` : Application FastAPI exposant les endpoints REST `/api/projects`, `/api/universes`, `/api/versioning/*`, `/api/pipeline/*`, `/api/reviews/latest` (suivi de la critique courante du manuscrit), ainsi que les routes statiques et le fallback SPA pour la Web UI.
   - `src/projects.py` : Gestion CRUD des projets, initialisation des structures de dossiers, scan des chapitres (`chapters/`), isolation et génération automatique des fichiers de fondation et de lore (`seed.txt`, `world.md`, `characters.md`, `canon.md`, `outline.md`, `state.json`) via l'assistant wizard (`/api/projects/wizard/create`, `/api/projects/wizard/suggest`).
   - `src/universes.py` : Gestion des univers partagés et de l'héritage de lore.
   - `src/versioning.py` : Gestion des branches narratives et de l'historique des révisions avec scores.
   - `src/pipeline_adapter.py` : Adaptateur d'exécution du pipeline avec **synchronisation bidirectionnelle multi-projet** (`sync_project_to_root` / `sync_root_to_project`) et isolation par projet (`projects/{project_id}`).
   - `src/settings.py` *(Spécifié & Planifié)* : Service de gestion, lecture, écriture et masquage sécurisé des clés API dans le fichier `.env` (`specs/settings/`).

2. **Web UI SPA (`ui/`)** :
   - `ui/index.html` : Fichiers statiques uniques et point d'entrée SPA avec chargement asynchrone des modules CSS/JS.
   - `ui/css/style.css` : Thème visuel élégant (EB Garamond / Bebas Neue, palettes `#0a0a08`, `#e8e4db`, `#daa548`).
   - `ui/js/` : Modules autonomes (`api.js`, `store.js`, `router.js`, `inspector.js` et vues `dashboard.js`, `projects.js` incluant l'assistant de création wizard en accordéon avec exemples contextuels et sélecteur de choix IA, `universes.js`, `branches.js`, `pipeline.js`, `foundation.js`).
   - `ui/js/views/settings.js` *(Spécifié & Planifié)* : Vue Paramètres et Clés API (`specs/settings/`).

3. **Pipeline & Outils CLI (`*.py`, `specs/`, `typeset/`)** :
   - Scripts Python de fondation, de rédaction, d'évaluation, de révision et d'export.

---

## 3. État Actuel Validé & Preuves Durables

- **Tests unitaires et d'intégration** : Suite de tests validés (`pytest tests/`), incluant `test_api.py`, `test_pipeline.py`, `test_projects.py`, `test_universes.py`, `test_versioning.py`, et `test_reviews.py`.
- **Intégration Web UI** :
  - Dashboard interactif (projets récents, statut global du pipeline, actions rapides).
  - Gestion complète des projets et univers partagés.
  - Pilotage du pipeline en temps réel avec volet d'inspection rétractable et logging dynamique.
  - Mode review-only (évaluation critique via `/api/pipeline/evaluate`).
  - Assistant de création de projet en mode wizard (en accordéon/sections) avec aide contextuelle, saisie libre et 4 suggestions IA par paramètre (`/api/projects/wizard/suggest`, `/api/projects/wizard/create`).
  - Édition et sauvegarde asynchrone des fichiers de fondation et de lore (`world.md`, `characters.md`, `outline.md`, `canon.md`) ainsi que des chapitres narratifs (`chapters/*.md`) via la section dédiée dans la barre latérale de l'éditeur.
- **Hygiène du worktree & verrouillage strict du scope** :
  - Le répertoire de stockage des projets générés (`projects/`) est strictement exclu du versioning Git (`.gitignore`).
  - **Interdiction absolue de manipulation ou de commit sur les dossiers de projets générés non suivis**.

---

## 4. Réconciliation Spec Kit & Clôture

Ce mémo de projet (`PROJECT_MEMORY.md`) est officiellement rattaché aux spécifications Spec Kit des répertoires `specs/001-web-ui-autonovel/`, `specs/002-chapters-sidebar-editing/`, `specs/003-current-review-button/`, `specs/004-project-creation-wizard/` ainsi qu'aux spécifications de la fonctionnalité de gestion des clés API (`specs/settings/`).

Toute évolution future devra maintenir la stricte cohérence entre ce mémo, les spécifications vivantes (`specs/`) et la suite de tests validée.
