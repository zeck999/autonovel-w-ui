# Spécification de Fonctionnalité : Section 'Chapitres' dans la Barre Latérale & Édition Directe

**Branche de Fonctionnalité** : `002-chapters-sidebar-editing`

**Créée** : 2026-10-07

**Statut** : Implémenté et validé

**Entrée** : Ajouter une section dédiée 'Chapitres' dans la barre latérale listant les fichiers du répertoire `chapters/` avec édition directe dans l'éditeur existant.

---

## Contexte et Objectif

Actuellement, l'interface Web (`ui/js/views/files.js`) et le back-office gèrent les fichiers de fondation et de lore du projet (`seed.txt`, `world.md`, `characters.md`, `outline.md`, `canon.md`, etc.). Cependant, les chapitres générés ou rédigés dans le répertoire `chapters/` du projet (ex. `chapters/chapter_01.md`, `chapters/chapitre-1.md`) ne sont pas directement listés dans la barre latérale de l'éditeur de fichiers, obligeant l'utilisateur à les manipuler hors de la Web UI ou via des mécanismes indirects.

Cette spécification définit l'ajout d'une section dédiée **« Chapitres »** dans la barre latérale de la vue Fichiers, listant tous les fichiers du répertoire `chapters/` du projet actif, et permettant leur sélection, lecture, édition directe et sauvegarde dans l'éditeur existant sans changement de paradigme.

---

## Scénarios Utilisateurs & Tests *(obligatoire)*

### Scénario 1 - Lister les fichiers du répertoire `chapters/` dans la barre latérale (Priorité : P1) 🎯 MVP
L'utilisateur ouvre la vue « Fichiers & Lore » d'un projet actif qui contient des chapitres dans son répertoire `chapters/`. La barre latérale présente une section visuelle claire « Chapitres » listant l'ensemble de ces fichiers de chapitres.

**Pourquoi cette priorité** : C'est le cœur de la fonctionnalité permettant d'accéder aux textes narratifs rédigés ou générés.

**Test Indépendant** : Créer un fichier de test dans `projects/<id>/chapters/chapter_01.md`, ouvrir la Web UI sur le projet, vérifier que la section « Chapitres » affiche `chapters/chapter_01.md`.

**Scénarios d'Acceptation** :
1. **Étant donné** un projet actif possédant des fichiers dans son sous-répertoire `chapters/`, **Quand** l'utilisateur navigue vers l'onglet « Fichiers », **Alors** la barre latérale affiche une section « Chapitres » distincte de la section « Fichiers du Projet » (Fondation & Lore).
2. **Étant donné** un répertoire `chapters/` vide, **Quand** l'utilisateur consulte la section « Chapitres », **Alors** un message discret ou un bouton d'ajout invite à créer le premier chapitre.

---

### Scénario 2 - Édition directe et sauvegarde d'un chapitre (Priorité : P1) 🎯 MVP
L'utilisateur clique sur un chapitre de la section « Chapitres », son contenu markdown s'affiche dans l'éditeur central existant, et l'utilisateur peut le modifier et le sauvegarder.

**Scénarios d'Acceptation** :
1. **Étant donné** un chapitre listé dans la barre latérale, **Quand** l'utilisateur clique dessus, **Alors** l'API récupère son contenu (`GET /api/projects/{id}/files/chapters/...`) et l'affiche dans l'éditeur texte existant avec le titre adapté.
2. **Étant donné** un chapitre chargé dans l'éditeur, **Quand** l'utilisateur modifie le texte et clique sur « Sauvegarder », **Alors** le fichier est enregistré sur le disque (`PUT /api/projects/{id}/files/chapters/...`) et un statut de confirmation s'affiche.

---

### Scénario 3 - Création d'un nouveau chapitre depuis la barre latérale (Priorité : P2)
L'utilisateur souhaite ajouter un nouveau chapitre à son roman directement depuis l'interface Web.

**Scénarios d'Acceptation** :
1. **Étant donné** la section « Chapitres » de la barre latérale, **Quand** l'utilisateur utilise le formulaire ou le bouton de création de chapitre (ex. saisie de `chapters/chapter_02.md` ou `chapter_02.md`), **Alors** le fichier est créé dans le sous-répertoire `chapters/` et sélectionné immédiatement dans l'éditeur.

---

### Edge Cases
- Que se passe-t-il si le répertoire `chapters/` n'existe pas encore sur le disque ? → Le back-office (`src/projects.py`) le crée automatiquement lors de l'initialisation du projet ou de la liste des fichiers, évitant toute erreur 500.
- Comment gérer les noms de fichiers avec des sous-chemins ? → L'API `/api/projects/{id}/files/{filename:path}` supporte déjà les chemins relatifs (`chapters/nom.md`), à condition que le front-office transmette correctement le chemin complet (ex. `chapters/chapter_01.md`).

---

## Exigences Fonctionnelles

- **FR-001**: La fonction `list_project_files` dans `src/projects.py` DOIT inspecter le sous-répertoire `chapters/` du projet et inclure ses fichiers markdown/texte dans la liste retournée avec un nom préfixé ou identifié (ex. `chapters/chapter_01.md`).
- **FR-002**: L'interface utilisateur (`ui/js/views/files.js`) DOIT organiser la barre latérale en deux sections distinctes : « Fichiers de Fondation & Lore » et « Chapitres ».
- **FR-003**: L'éditeur existant DOIT gérer l'affichage, l'édition et la sauvegarde de tout fichier de la section `chapters/` via les endpoints d'API existants.
- **FR-004**: Un mécanisme simple DOIT permettre la création d'un nouveau chapitre dans le répertoire `chapters/` depuis l'interface.
