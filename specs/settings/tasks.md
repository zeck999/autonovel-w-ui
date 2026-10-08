---
description: "Tâches pour l'implémentation de la fonctionnalité de test et d'édition des clés API IA (specs/settings/)"
---

# Tâches : AI Keys Test and Edit Feature

**Entrée** : Documents de conception de `/specs/settings/` (`spec.md`, `plan.md`)

**Préréquis** : Back-office FastAPI existant (`src/api.py`), structure UI SPA (`ui/`)

---

## Phase 1 : Backend Settings & Key Management Service (Priorité : P1) 🎯 MVP

- [x] T001 [US1] Créer le module `src/settings.py` gérant la lecture, l'écriture et le masquage sécurisé des variables dans le fichier `.env`.
- [x] T002 [US1] Implémenter l'endpoint `GET /api/settings/keys` dans `src/api.py` (ou `src/settings.py`) retournant l'état configuré et les valeurs masquées des clés (`ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`).
- [x] T003 [US1] Implémenter l'endpoint `PUT /api/settings/keys` pour mettre à jour et persister les clés API dans `.env` de manière sécurisée.

---

## Phase 2 : Key Testing Logic & Endpoint (Priorité : P1)

- [x] T004 [US2] Implémenter la logique de test de connexion pour chaque fournisseur (Anthropic `/v1/messages` ping, ElevenLabs, Fal.ai) dans `src/settings.py`.
- [x] T005 [US2] Implémenter l'endpoint `POST /api/settings/keys/test` pour tester un fournisseur spécifique et retourner le statut de succès ou l'erreur détaillée (avec gestion des timeouts et masquage des secrets).

---

## Phase 3 : Web UI Settings View (Priorité : P1 / P2)

- [x] T006 [P] [US1] Ajouter le lien de navigation « Paramètres / Clés API » dans `ui/index.html` et l'enregistrer dans le routeur `ui/js/router.js`.
- [x] T007 [US1/US2] Créer la vue Paramètres `ui/js/views/settings.js` affichant les champs de saisie masqués pour chaque clé, les boutons de sauvegarde (`PUT /api/settings/keys`) et les boutons de test de connexion (`POST /api/settings/keys/test`) avec indicateurs visuels en temps réel.

---

## Phase 4 : Tests & Validation (Priorité : P1)

- [x] T008 [US3] Créer la suite de tests unitaires et d'intégration `tests/test_settings.py` validant les endpoints de lecture, écriture, masquage et test des clés API.
- [x] T009 Exécuter `pytest tests/test_settings.py` (et l'ensemble de la suite `pytest tests/`) pour garantir l'absence de régression.

---

## Phase 5 : Polissage & Documentation

- [x] T010 Mettre à jour `README.md` et `specs/PROJECT_MEMORY.md` pour documenter la nouvelle vue Paramètres et la gestion sécurisée des clés API.
- [x] T011 Vérifier la propreté du worktree git et valider la conformité avec les directives Spec Kit.

---

## Phase 6 : Convergence

- [x] T012 Implémenter le module `src/settings.py` et les endpoints REST de gestion des clés API (`GET /api/settings/keys`, `PUT /api/settings/keys`) per FR-001, FR-002, FR-005, FR-006
- [x] T013 Implémenter la logique de test de connexion et l'endpoint (`POST /api/settings/keys/test`) per FR-003, US2
- [x] T014 Implémenter la vue Web UI Paramètres (`ui/js/views/settings.js`), le lien de navigation et l'enregistrement dans le routeur per FR-004, US1
- [x] T015 Implémenter la suite de tests unitaires et d'intégration (`tests/test_settings.py`) et valider avec pytest per SC-003, US3
