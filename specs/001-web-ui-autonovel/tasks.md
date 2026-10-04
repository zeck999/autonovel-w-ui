---
description: "Liste des tâches pour l'implémentation de l'interface web Autonovel (Multi-projet, Univers Partagés, Versioning)"
---

# Tâches : Interface Web Autonovel (Versioning, Multi-projet, Univers Partagés)

**Entrée** : Documents de conception de `/specs/001-web-ui-autonovel/`

## Phase 1 : Infrastructure de Base & Multi-projet (P1)
- [x] T001 [US1] Créer le gestionnaire de projets multiples (`src/projects.py` ou module équivalent) pour lister, créer et basculer entre les projets.
- [x] T002 [US1] Adapter l'arborescence des données pour supporter plusieurs projets dans des dossiers dédiés.
- [x] T003 [US1] Ajouter les endpoints API / vues pour la sélection et la création de projets.

## Phase 2 : Séries & Univers Partagés (P2)
- [x] T004 [US2] Implémenter la structure des "Univers Partagés" (`universes/`) pour partager `world.md`, `characters.md` et `canon.md` entre plusieurs projets.
- [x] T005 [US2] Mettre à jour l'initialisation des projets pour permettre le rattachement à un univers existant.

## Phase 3 : Versioning & Branches Narratives (P3)
- [x] T006 [US3] Implémenter la gestion des branches narratives et l'historique des révisions (suivi des versions de romans/chapitres).
- [x] T007 [US3] Intégrer l'affichage des révisions et des scores dans l'interface web.

## Phase 4 : Validation & Documentation
- [x] T008 [P] Rédiger les tests unitaires et d'intégration pour le multi-projet, les univers partagés et le versioning.
- [x] T009 Mettre à jour la documentation (README.md, PIPELINE.md) pour refléter ces nouvelles capacités.
