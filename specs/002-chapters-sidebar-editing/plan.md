# Plan d'Implémentation : Section 'Chapitres' dans la Barre Latérale & Édition Directe

**Branche** : `002-chapters-sidebar-editing` | **Date** : 2026-10-07 | **Spec** : [spec.md](./spec.md)

**Entrée** : Spécification de la fonctionnalité pour l'ajout de la section Chapitres dans la barre latérale de l'éditeur de fichiers.

## Résumé

Permettre aux utilisateurs de lister, visualiser, créer et éditer directement les fichiers du répertoire `chapters/` d'un projet dans la Web UI (onglet Fichiers), en adaptant le back-office (`src/projects.py`) pour inclure les fichiers de `chapters/` dans `list_project_files` et en enrichissant la vue front-end (`ui/js/views/files.js`).

## Contexte Technique

- **Langage/Version** : Python 3.11+, JavaScript (ES6+ Vanilla SPA)
- **Dépendances principales** : FastAPI, Pydantic, Vanilla JS DOM API
- **Stockage** : Fichiers locaux sous `projects/{id}/chapters/`
- **Tests** : pytest (`tests/test_api.py`, `tests/test_projects.py`)

## Constitution Check

*GATE : Conforme aux règles d'architecture modulaire et de séparation des responsabilités de ZPI.*

## Structure du Projet

### Documentation (cette fonctionnalité)
```text
specs/002-chapters-sidebar-editing/
├── plan.md
├── spec.md
└── tasks.md
```

### Code Source (racine du dépôt)
```text
src/
└── projects.py          # Mise à jour de list_project_files pour inclure chapters/

ui/
└── js/
    └── views/
        └── files.js     # Ajout de la section Chapitres et gestion des sous-chemins
```

## Phases d'Implémentation

1. **Phase 1 : Back-Office & API (`src/projects.py`)**
   - Mettre à jour `list_project_files(project_id)` pour parcourir également le sous-répertoire `chapters/` et retourner les fichiers avec le préfixe `chapters/...` (ou un attribut distinct).
   - S'assurer que `get_project_file` et `save_project_file` gèrent correctement les chemins relatifs sous `chapters/`.

2. **Phase 2 : Front-End Web UI (`ui/js/views/files.js`)**
   - Séparer la barre latérale en deux blocs : "Fichiers de Fondation & Lore" et "Chapitres".
   - Ajouter un formulaire ou bouton d'ajout rapide pour créer un nouveau chapitre dans `chapters/`.
   - Mettre à jour la logique de sélection et de sauvegarde pour supporter les fichiers de chapitres.

3. **Phase 3 : Tests & Validation**
   - Ajouter ou mettre à jour les tests unitaires/intégration (`tests/test_projects.py`, `tests/test_api.py`) pour vérifier la liste et l'accès aux fichiers de chapitres.
   - Valider la suite de tests complète (`pytest`).
