# Spécification de Fonctionnalité : Interface Web Autonovel avec Versioning, Multi-projet et Univers Partagés

**Branche de Fonctionnalité** : `001-web-ui-autonovel`

**Créée** : 2026-10-04

**Statut** : Validée / Spécifiée

**Entrée** : Demande utilisateur pour intégrer le Versioning, le Multi-projet et les Séries & Univers Partagés dans l'interface web d'Autonovel.

## Scénarios Utilisateurs & Tests *(obligatoire)*

### Scénario 1 - Gestion Multi-projet (Priorité : P1) 🎯 MVP
L'utilisateur souhaite pouvoir créer, basculer, renommer et supprimer plusieurs romans/projets d'écriture en parallèle depuis l'interface web principale sans mélanger leurs états (chapitres, outline, personnages, state.json).

**Pourquoi cette priorité** : C'est la base indispensable pour qu'un utilisateur gère plus d'un livre ou projet créatif dans l'application.

**Test Indépendant** : Peut être entièrement testé en créant deux projets distincts (ex: "Roman A" et "Roman B"), en basculant entre eux dans l'interface et en vérifiant que les données affichées (chapitres, world, characters) correspondent bien au projet actif.

**Scénarios d'Acceptation** :
1. **Étant donné** l'interface web ouverte, **Quand** l'utilisateur clique sur "Nouveau Projet" et saisit un titre et un concept, **Alors** un nouveau projet isolé est créé et devient actif.
2. **Étant donné** plusieurs projets existants, **Quand** l'utilisateur sélectionne un autre projet dans le sélecteur global, **Alors** l'interface charge instantanément l'état, les chapitres et les métadonnées de ce projet.

---

### Scénario 2 - Séries & Univers Partagés (Priorité : P2)
L'utilisateur souhaite rattacher plusieurs projets à un même univers partagé (world-building, base de personnages, lore et canon communs), permettant d'écrire une série de romans ou des spin-offs dans le même monde.

**Pourquoi cette priorité** : Permet l'écriture cohérente d'œuvres sérielles ou de spin-offs en évitant de dupliquer ou de corrompre le lore global.

**Test Indépendant** : Peut être testé en créant un "Univers Partagé" (ex: "Monde d'Elaria"), puis en rattachant deux projets distincts (ex: "Livre 1" et "Spin-off de Lenne") à cet univers, et en vérifiant le partage des bases `world.md`, `characters.md` et `canon.md`.

**Scénarios d'Acceptation** :
1. **Étant donné** un univers partagé existant avec son lore et ses personnages, **Quand** l'utilisateur crée un nouveau projet en l'associant à cet univers, **Alors** le projet hérite des fichiers de référence de l'univers tout en gardant son propre manuscrit et ses chapitres.
2. **Étant donné** une modification du world-building dans l'univers partagé, **Quand** l'utilisateur valide la mise à jour, **Alors** les projets rattachés peuvent synchroniser ou consulter ces évolutions.

---

### Scénario 3 - Versioning et Branches Narratives (Priorité : P3)
L'utilisateur souhaite suivre les différentes versions de ses romans, créer des branches narratives (ex: fin alternative, réécriture majeure par l'agent d'une branche `branch-draft-v2`), et consulter l'historique des révisions et des scores d'évaluation.

**Pourquoi cette priorité** : Permet d'explorer des directions créatives alternatives et de revenir en arrière en cas de réécriture insatisfaisante, s'alignant sur l'esprit "autoresearch" et git-like d'Autonovel.

**Test Indépendant** : Peut être testé en créant une branche narrative à partir d'un chapitre ou d'un roman, en modifiant la branche, et en effectuant un diff ou un basculement entre la branche principale et la branche alternative.

**Scénarios d'Acceptation** :
1. **Étant donné** un projet avec plusieurs chapitres rédigés, **Quand** l'utilisateur crée une branche narrative (ex: `alternative-ending`), **Alors** une copie isolée de l'état narratif est créée pour cette branche.
2. **Étant donné** l'historique des révisions d'un chapitre, **Quand** l'utilisateur sélectionne une révision passée, **Alors** l'interface affiche le texte de cette révision et son score d'évaluation associé.

---

## Exigences Fonctionnelles

- **FR-001** : Le système DOIT permettre la création, le listage, la sélection et la suppression de projets multiples stockés dans des répertoires isolés.
- **FR-002** : Le système DOIT supporter le concept d'Univers Partagés (World / Lore / Characters partagés entre plusieurs projets).
- **FR-003** : Le système DOIT offrir un système de versioning et de branches narratives pour chaque projet ou chapitre.
- **FR-004** : L'interface web DOIT exposer ces fonctionnalités de manière fluide et intuitive (sélecteur de projet, gestionnaire d'univers, explorateur de branches et historique).
- **FR-005** : Le système DOIT conserver la compatibilité avec les scripts Python existants d'Autonovel (`run_pipeline.py`, `gen_world.py`, etc.).
