# Spécification de Fonctionnalité : Web UI Autonovel (HTML/CSS/JS autonome, FastAPI)

**Branche de Fonctionnalité** : `001-web-ui-autonovel`

**Créée** : 2026-10-04

**Statut** : Validé, accompli et acté au commit `90ab158` (Phases 0 à 6 implémentées, Web UI SPA interactive, endpoints fichiers, vue UI Fondation & Lore opérationnels, correction du pipeline multi-projet dans `src/pipeline_adapter.py`, et suite de tests d'intégration E2E `pytest tests/` validée)

**Entrée** : Intégration d'une interface web interactive HTML/CSS/JS autonome, servie par FastAPI à la racine `/` (ou en couche client), permettant de piloter le pipeline de création de roman autonome à partir du back-office validé.

---

## Contexte et état actuel (réconciliation des preuves)

Le back-office existe et est validé par des tests (preuve durable) :

- `src/api.py` — FastAPI avec endpoints projets / univers / versioning / pipeline. Endpoint `/` retourne actuellement un JSON de bienvenue (noeud).
- `src/projects.py`, `src/universes.py`, `src/versioning.py`, `src/pipeline_adapter.py` — implémentés et couverts par `tests/test_api.py` / `tests/test_projects.py` / `tests/test_universes.py` / `tests/test_versioning.py`.
- `landing/index.html` — page de présentation marketing (non interactive, hors scope de la Web UI utilitaire).

Ce qui reste à construire : une **vraie interface interactive** pour l'humain, servie à la racine `/` de la même app FastAPI, qui repose sur le back-office existant (`/api/...`) et qui ne doit **ni le dupliquer, ni le remplacer**.

La UI choisie est un **SPA HTML/CSS/JS autonome** (fichiers statiques `ui/`) servi par FastAPI en lecture seule : pas de framework lourd, pas de build-time, zéro dépendance côté client, rechargement partiel au besoin. L'expérience est progressive : un squelette (layout + navigation) est toujours opérationnel, puis chaque module s'enrichit.

---

## Scénarios Utilisateurs & Tests *(obligatoire)*

### Scénario 1 - Piloter le pipeline et voir le statut global (Priorité : P1) 🎯 MVP
L'utilisateur ouvre `http://localhost:8000/`, voit d'un coup d'œil l'état de ses projets récents, choisit un projet et exécute une phase du pipeline avec visualisation des logs en temps réel.

**Pourquoi cette priorité** : C'est le flux principal d'un « vibe coder » — lancer, observer, itérer — sans écrire de commande en CLI.

**Test Indépendant** : Ouvrir `/`, créer un projet, lancer une phase (`--phase foundation`), puis vérifier que la page affiche la progression et les derniers logs.

**Scénarios d'Acceptation** :
1. **Étant donné** l'interface ouverte, **Quand** l'utilisateur arrive sur `/`, **Alors** le tableau de bord affiche la liste des projets récents + le statut global du pipeline (phase actuelle, score, itération, derniers logs).
2. **Étant donné** un projet sélectionné, **Quand** l'utilisateur clique sur « Lancer foundation », **Alors** l'API `/api/pipeline/run` est appelée, la page se met à jour sans rechargement complet, et les logs apparaissent dans le volet technique rétractable.
3. **Étant donné** un pipeline en cours, **Quand** l'utilisateur rafraîchit la page, **Alors** le statut reste visible (pas de perte d'information, polling ou affichage statique des dernières mesures).

---

### Scénario 2 - Gérer les projets (Priorité : P1)
L'utilisateur crée, renomme (visuellement), sélectionne et supprime des projets depuis la barre de navigation « Projets », sans basculer hors de l'interface.

**Scénarios d'Acceptation** :
1. **Étant donné** aucun projet, **Quand** l'utilisateur remplit le formulaire de création (nom + concept, option univers partagé), **Alors** un projet est créé via `/api/projects` et apparaît immédiatement dans la liste.
2. **Étant donné** plusieurs projets, **Quand** l'utilisateur clique sur un projet dans le sélecteur, **Alors** le contexte global change et le dashboard se met à jour sur le projet actif (`/api/projects/{id}` + `/api/pipeline/status`).
3. **Étant donné** un projet à supprimer, **Quand** l'utilisateur confirme la suppression, **Alors** `/api/projects/{id}` est appelé en DELETE et le projet disparaît de toutes les listes.

---

### Scénario 3 - Explorer et sélectionner des Univers / Séries (Priorité : P2)
L'utilisateur navigue vers la vue « Univers », voit la liste des mondes partagés et leurs projets rattachés, et attache ou détache un univers à un projet lors de la création/sélection.

**Scénarios d'Acceptation** :
1. **Étant donné** un ou plusieurs univers, **Quand** l'utilisateur ouvre « Univers », **Alors** la liste affiche nom, description, et le nombre de projets liés (via `/api/universes`).
2. **Étant donné** une création de projet, **Quand** l'utilisateur choisit un univers dans une liste déroulante, **Alors** l'ID de l'univers est transmis à `/api/projects` et les fichiers partagés (`world.md`, `characters.md`, `canon.md`) sont copiés dans le projet.
3. **Étant donné** un univers supprimé, **Alors** les projets qui y étaient liés restent intacts (rétention des copies), mais ne bénéficient plus des mises à jour futures.

---

### Scénario 4 - Explorer les branches narratives et l'historique (Priorité : P3)
L'utilisateur voit les branches du projet, crée une branche narrative, bascule dessus, et consulte l'historique des révisions avec scores.

**Scénarios d'Acceptation** :
1. **Étant donné** un projet actif, **Quand** l'utilisateur ouvre « Versions / Branches », **Alors** la liste des branches est affichée (git + branches de projet, `/api/versioning/branches`).
2. **Étant donné** une branche existante, **Quand** l'utilisateur la sélectionne, **Alors** le projet bascule vers cette branche (`/api/versioning/switch`) et le dashboard se met à jour.
3. **Étant donné** un chapitre, **QuAND** l'utilisateur consulte son historique, **Alors** les révisions s'affichent avec commit, phase, score, nombre de mots et description (`/api/versioning/history`).

---

### Scénario 5 - Volet d'inspection technique & logs (expérience progressive)
L'utilisateur ouvre le volet d'inspection en un clic, lit les logs de pipeline, les métadonnées du projet et les erreurs, et peut le réduire pour gagner de la place sans perdre le contexte.

**Scénarios d'Acceptation** :
1. **Étant donné** l'interface ouverte, **QuAND** l'utilisateur clique sur le bouton « Inspection », **Alors** un volet rétractable apparaît (side drawer) avec les logs du pipeline et les détails du contexte.
2. **Étant donné** le volet ouvert, **QuAND** l'utilisateur le réduit, **Alors** l'espace d'affichage se libère et le contenu reste intact (persisté en mémoire + local store optionnel).
3. **Étant donné** une erreur de pipeline, **Quand** les logs s'affichent, **Alors** les lignes d'erreur sont mises en évidence.

---

### Scénario 6 - Édition des fichiers de fondation et de lore (`world.md`, `characters.md`, `outline.md`, `canon.md`) (Priorité : P2)
L'utilisateur sélectionne un fichier de fondation ou de lore (`world.md`, `characters.md`, `outline.md`, `canon.md`) du projet actif, le consulte, le modifie dans un éditeur intégré à la Web UI, et sauvegarde les modifications.

**Scénarios d'Acceptation** :
1. **Étant donné** un projet actif, **Quand** l'utilisateur navigue vers la vue « Fondation & Lore », **Alors** la liste des fichiers éditables (`world.md`, `characters.md`, `outline.md`, `canon.md`) est affichée.
2. **Étant donné** un fichier sélectionné, **Quand** son contenu est chargé via l'API (`GET /api/projects/{id}/files/{filename}`), **Alors** il s'affiche dans un éditeur texte interactif.
3. **Étant donné** des modifications apportées au contenu, **Quand** l'utilisateur clique sur « Sauvegarder », **Alors** une requête `PUT` (ou `POST`) vers `/api/projects/{id}/files/{filename}` enregistre les modifications sur le disque dans le répertoire du projet.

---

### Edge Cases
- Que se passe-t-il quand le back-office n'est pas disponible (`uvicorn` non lancé) ? → message d'état « API déconnectée » sans casser la page ; re-connexion automatique au retour.
- Comment gérer un pipeline long (10+ min) ? → l'app appelle `/api/pipeline/run` en attente courte et passe en mode polling sur `/api/pipeline/status`, avec affichage des logs par tranches.
- Que se passe-t-il sur une page inconnue ? → affichage d'une page « 404 UI » interne (SPA), sans appel API.
- Comment gérer les projets/inventaires vides ? → écrans « vide » polis avec incitation à créer le premier projet, jamais de bug.

---

## Exigences Fonctionnelles

### Back-office (déjà implémenté et testé — à réutiliser intact)
- **FR-B001** : Le back-office DOIT conserver les endpoints `/api/projects`, `/api/universes`, `/api/versioning/*`, `/api/pipeline/*` existants sans rupture de contrat (tests `test_api.py` doivent rester PASS).
- **FR-B002** : Les modèles Pydantic (`ProjectCreate`, `UniverseCreate`, `BranchCreate`, `PipelineRun`…) DOIVENT rester la source de vérité des payloads.

### Web UI (à implémenter)
- **FR-001** : La Web UI DOIT être servie par FastAPI à la racine `/` (route `@app.get("/")`) — le même serveur que l'API (`uv run uvicorn src.api:app --port 8000`).
- **FR-002** : L'interface DOIT être une page HTML/CSS/JS autonome, sans framework JS lourd ni étape de build, stockée dans le répertoire `ui/` du projet.
- **FR-003** : Le fichier `ui/index.html` DOIT embarquer le CSS (`<style>`) et le JS (`<script>`) pour la navigation et le volet d'inspection (single-file pour la robustesse), avec un chargement progressif des modules CSS/JS supplémentaires (`ui/css/style.css`, `ui/js/*.js`) par balises asynchrones.
- **FR-004** : L'interface DOIT offrir un menu de navigation global : **Projets**, **Univers / Séries**, **Versions / Branches**, **Pipeline & Monitoring**, plus le bouton **Inspection**.
- **FR-005** : La page d'accueil `/` DOIT afficher un dashboard : vue synthétique des projets récents (nom, univers, phase, score, chapitres) + indicateur de statut global du pipeline + actions rapides (créer un projet, lancer une phase).
- **FR-006** : Toutes les interactions DOIVENT être asynchrones (fetch / AbortController) vers `/api/...`, avec gestion des états `loading`, `idle`, `error` et `success`.
- **FR-007** : Le volet d'inspection & logs DOIT être rétractable (clavier : `Alt+I` ou `Esc` ; souris : bouton toggle).
- **FR-008** : L'interface DOIT rester utilisable en mode dégradé (pas d'API) avec un message clair ; aucune donnée ne DOIT être perdue lors d'une déconnexion.
- **FR-009** : Les URLs DOIVENT évoluer progressivement (SPA, history.pushState) pour les vues principales (`/#/projects`, `/#/universes`, `/#/branches`, `/#/pipeline`, `/#/foundation`) afin d'être navigables et partageables en mode SPA.
- **FR-010** : L'interface DOIT être responsive (mobile ≤ 480px : menu en drawer, volet d'inspection en modal).
- **FR-011** : L'API DOIT fournir des endpoints de lecture et écriture des fichiers de projet (`GET /api/projects/{id}/files/{filename}` et `PUT /api/projects/{id}/files/{filename}`) pour `world.md`, `characters.md`, `outline.md`, `canon.md`, etc.
- **FR-012** : La Web UI DOIT intégrer une vue/onglet « Fondation & Lore » permettant de sélectionner, éditer et sauvegarder ces fichiers de manière fluide et asynchrone.
- **FR-013** : Le système DOIT fournir un **logging temps réel du pipeline** via polling asynchrone et affichage dynamique des logs dans le volet d'inspection (`ui/js/inspector.js`), avec mise en évidence des erreurs et masquage des secrets.
- **FR-014** : Le système DOIT supporter un **mode review-only** (via la phase de review et les endpoints d'évaluation critique `/api/pipeline/evaluate`) permettant l'audit littéraire et le scoring sans modification destructive des chapitres.

---

## Exigences Non-Fonctionnelles

- **ENF-001** : Charge initiale de la page `< 1 s` en local (un seul fichier HTML < 60 Ko).
- **ENF-002** : Aucune donnée d'API ne DOIT être mise en cache indéfiniment ; un état « staling » DOIT être signalé après 30 s d'inactivité.
- **ENF-003** : Les logs affichés DOIVENT être masqués du navigateur si un secret (clé API, token) y transite — afficher uniquement les tranches sûres.
- **ENF-004** : Le code JS DOIT respecter le style existant du projet (pas de dépendances npm).

---

## Success Criteria *(mesurables)*

- **SC-001** : Lancement — `uv run uvicorn src.api:app --port 8000` puis `curl -s http://localhost:8000/` renvoie un document HTML (`Content-Type: text/html`) contenant « Autonovel ».
- **SC-002** : Dashboard — `/` affiche au moins les champs : liste des projets, statut global, score courant.
- **SC-003** : Pipeline — le bouton de lancement appelle `/api/pipeline/run` et l'affichage se met à jour en < 2 s après le retour API.
- **SC-004** : Navigation — toutes les vues (`Projets`, `Univers`, `Branches`, `Pipeline`, `Inspection`) sont accessibles sans rechargement complet de page.
- **SC-005** : Rétrocompatibilité — les tests API existants (`pytest tests/`) restent PASS après l'ajout des routes statiques.
- **SC-006** : Dégradé — avec l'API hors ligne, l'interface affiche un message « hors connexion » et ne plante pas.

---

## Assomptions

- L'utilisateur lance le serveur avec `uv run uvicorn src.api:app --port 8000` — pas de changement à `main.py` pour l'instant.
- Le serveur FastAPI tourne sur le même hôte/ports que prévu (8000), donc pas de CORS spécifique nécessaire en local ; le module UI n'est servi qu'en développement.
- Les tests E2E UI sont facultatifs au MVP ; la validation se fait d'abord manuellement (ouverture navigateur + checklist SC-001..SC-006).
- La police et le style visuel suivent l'identité du projet (EB Garamond / Bebas Neue présents dans `landing/index.html`).

---

## Clauses de réconciliation

- **Ce qui est validé** : back-office API + endpoints (`src/api.py`, `src/projects.py`, `src/universes.py`, `src/versioning.py`, `src/pipeline_adapter.py` avec correction du pipeline multi-projet ciblant `projects/{project_id}/state.json`) + suite complète de tests d'intégration E2E (`tests/test_api.py`, `tests/test_pipeline.py`, `tests/test_projects.py`, `tests/test_universes.py`, `tests/test_versioning.py`) → entièrement validée et actée.
- **Ce qui est specifié (non implémenté)** : `ui/index.html` + `ui/css/style.css` + `ui/js/*.js` + routes statiques dans `src/api.py` → tâches ouvertes `[ ]`.
- **Ce qui est exclu de cette spécification** : système d'authentification, multi-utilisateurs, hébergement, build-time (webpack/vite) — hors scope v1.
- **Hygiène du worktree & verrouillage du scope** : Le répertoire de stockage des projets générés (`projects/`) est strictement exclu du périmètre de versioning et des opérations Git. **Aucune tentative de commit ou de manipulation (ajout, modification, suppression via l'agent) sur les dossiers de projets générés non suivis n'est autorisée**, garantissant un worktree propre, étanche et focalisé uniquement sur le code source et les spécifications.
