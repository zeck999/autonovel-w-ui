# Plan d'Implémentation : Web UI Autonovel (HTML/CSS/JS autonome, FastAPI)

**Branche** : `001-web-ui-autonovel` | **Date** : 2026-10-04 | **Statut** : Accompli et acté (Commit `90ab158`) | **Spécification** : [spec.md](./spec.md)

## Résumé

Le **back-office API FastAPI** (`src/api.py` + modules `projects`, `universes`, `versioning`, `pipeline_adapter` avec synchronisation bidirectionnelle multi-projet) et ses tests (`tests/test_api.py`, `tests/test_pipeline.py`, etc., soit **19/19 tests validés**) sont **pleinement implémentés, testés et validés**. 

Ce plan couvre également la spécification et l'architecture de la couche **Web UI interactive** (HTML/CSS/JS autonome / SPA) destinée à être servie par FastAPI pour exploiter ce back-office.

Objectifs prioritaires :

1. **Accueil / Dashboard** — vue synthétique des projets récents, statut global du pipeline, actions rapides (créer un projet, lancer une phase).
2. **Navigation** — menu global : **Projets**, **Univers / Séries**, **Versions / Branches**, **Pipeline & Monitoring**, plus le bouton **Inspection**.
3. **Pilotage du pipeline** — lancer/observer les phases avec logs affichés dans un volet rétractable.
4. **Gestion des projets & sélection d'univers partagés** — créer/sélectionner/supprimer, attacher un univers.
5. **Exploration des branches narratives** — liste, création, bascule, historique des révisions.
6. **Édition des fichiers de fondation et de lore** — consultation et modification directe de `world.md`, `characters.md`, `outline.md`, `canon.md` via des endpoints dédiés et une vue UI dédiée.

## État de la base (preuves)

Implémenté et testé (à **réutiliser intact**) :

| Module | Rôle | Tests |
|---|---|---|
| `src/api.py` | FastAPI, endpoints `/api/projects`, `/api/universes`, `/api/versioning/*`, `/api/pipeline/*` | `tests/test_api.py` |
| `src/projects.py` | CRUD projets | `tests/test_projects.py` |
| `src/universes.py` | CRUD univers partagés | `tests/test_universes.py` |
| `src/versioning.py` | branches + historique des révisions | `tests/test_versioning.py` |
| `src/pipeline_adapter.py` | invoque `run_pipeline.py` / `evaluate.py` avec **synchronisation bidirectionnelle multi-projet** (`sync_project_to_root` / `sync_root_to_project`) et isolation par projet | `tests/test_pipeline.py`, `tests/test_api.py` |

À construire : la couche UI. `landing/index.html` (page marketing) reste hors scope de la Web UI.

## Choix techniques

| Aspect | Décision | Justification |
|---|---|---|
| Serveur | `uv run uvicorn src.api:app --port 8000` inchangé | Le back-office reste la source ; on ajoute des routes statiques |
| Frontend | **HTML/CSS/JS autonome**, sans framework, sans build-time (npm/webpack/vite absents) | Respect de la contrainte « pas de dépendances npm », démarrage immédiat, un seul fichier HTML central robuste |
| Placement | `ui/index.html` (single-file) + chargement progressif de `ui/css/style.css` et `ui/js/*.js` | Single-file = MVP immédiat et portable ; modules = évolutivité |
| Routing UI | SPA progressive : history.pushState (`/#/projects`, `/#/universes`, `/#/branches`, `/#/pipeline`) + fallback route par défaut | Navigable, partageable, pas de rechargement complet |
| Communication | `fetch()` avec `AbortController`, états `idle/loading/success/error`, pas de cache indéfini | API locale, gestion propre du long-running pipeline |
| Logs | affichage par tranches, masquage des secrets (clés/tokens) | Sécurité minimale |
| Tests UI | d'abord manuels (checklist SC-001..SC-006), E2E optionnel (Playwright) ensuite | MVP rapide ; la validation backend (pytest) reste la garantie durable |

## Architecture des fichiers (nouveau)

```text
ui/
├── index.html          # page unique (style + nav + layout + logiques globales)
├── css/
│   └── style.css       # thème (EB Garamond / Bebas Neue, palette sobre, drawer, cartes)
└── js/
    ├── api.js          # couche fetch autour des routes /api/* (+ reconnexion automatique)
    ├── store.js        # contexte global : projet actif, univers, branches, historique
    ├── router.js       # SPA routing + vues vides
    ├── views/
    │   ├── dashboard.js    # Scénario 1 (accueil, projets récents, statut global)
    │   ├── projects.js     # Scénario 2 (créer/sélectionner/supprimer)
    │   ├── universes.js    # Scénario 3 (liste, sélection, attache)
    │   ├── branches.js     # Scénario 4 (listes, création, bascule, historique)
    │   ├── pipeline.js     # Scénario 1 + 5 (lancer une phase, logs, polling)
    │   └── foundation.js   # Scénario 6 (édition des fichiers world.md, characters.md, outline.md, canon.md)
    └── inspector.js      # Scénario 5 (volet d'inspection & logs rétractable)
```

## Route map (FastAPI)

| URL | Méthode | Vue / comportement |
|---|---|---|
| `/` | `GET` | Sert `ui/index.html` (route **au-dessus** de toutes les routes `/api/*` pour éviter la collision) |
| `/{path:path}` | `GET` | Sert statiquement `ui/index.html` → SPA fallback (toutes les routes UI passent par une seule route catch-all) |
| `/{name}/css/{path:path}` | `GET` | Serveur statique pour `ui/css/…` |
| `/{name}/js/{path:path}` | `GET` | Serveur statique pour `ui/js/…` |
| `/api/projects/{id}/files/{filename}` | `GET` / `PUT` | Lecture et sauvegarde des fichiers de fondation et lore (`world.md`, `characters.md`, `outline.md`, `canon.md`) |

Implémentation FastAPI : ajouter dans `src/api.py` :

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

STATIC_UI = Path(__file__).resolve().parent.parent / "ui"

@app.get("/")
def ui_root():
    return FileResponse(STATIC_UI / "index.html")

@app.get("/{path:path}")
def ui_spa(path: str):
    if (STATIC_UI / path).exists() and (STATIC_UI / path).is_file():
        return FileResponse(STATIC_UI / path)
    return FileResponse(STATIC_UI / "index.html")

app.mount("/css", StaticFiles(directory=STATIC_UI / "css"), name="ui-css")
app.mount("/js", StaticFiles(directory=STATIC_UI / "js"), name="ui-js")
```

La route racine `/` DOIT être définie **avant** la route catch-all `/{path:path}`, car FastAPI correspond l'ordre des routes.

## Phasage (aligné sur les user stories)

**Phase 0 — Fondations UI** (bloque tout le reste)
- T-01 : créer l'arborescence `ui/` et le fichier `index.html` squelette (doctype, titre, viewport, titre « Autonovel »).
- T-02 : routes FastAPI racine + catch-all + `StaticFiles` ; vérifier `curl` sur `/` renvoie `text/html`.
- T-03 : CSS global minimal + layout (header + nav + content + drawer d'inspection) ; palette issue du design existant (`landing/index.html` : `#0a0a08`, `#e8e4db`, `#daa548`).

**Phase 1 — Dashboard + navigation + API layer (P1, MVP)**
- T-11 : couche `api.js` (`get`, `post`, `delete` + gestion erreurs + reconnexion automatique) + store global (`store.js`).
- T-12 : navigation HTML (`Projets / Univers / Branches / Pipeline / Inspection`) + SPA routing (`router.js`, `/#/...`).
- T-13 : vue `dashboard.js` — projets récents, statut global, actions rapides ; appelle `/api/projects` + `/api/pipeline/status`.

**Phase 2 — Gestion des projets & univers (P1 / P2)**
- T-21 : vue `projects.js` — créer (form), sélectionner (liste), supprimer (confirm + DELETE).
- T-22 : vue `universes.js` — liste des univers avec compteur projets, sélection dans le formulaire de création, attachement.

**Phase 3 — Versioning & branches (P3)**
- T-31 : vue `branches.js` — lister branches, créer une branche narrative, bascule (`/api/versioning/switch`), historique des révisions avec scores.

**Phase 4 — Pipeline & Monitoring + logs (P1 + P5)**
- T-41 : vue `pipeline.js` — formulaire de phase (`/api/pipeline/run`), polling sur `/api/pipeline/status`, affichage des logs.
- T-42 : volet d'inspection & logs (`inspector.js`) — rétractable (clavier `Alt+I`/`Esc`, bouton toggle), persistance locale, mise en évidence des erreurs, masquage des secrets.

**Phase 5 — Fondation & Lore (Édition des fichiers)**
- T-50 : endpoints API `/api/projects/{id}/files/{filename}` (GET/PUT) pour lire et écrire `world.md`, `characters.md`, `outline.md`, `canon.md`.
- T-51 : vue `foundation.js` — sélection de fichier, éditeur texte markdown, sauvegarde asynchrone avec feedback visuel.

**Phase 6 — Polissage & validation**
- T-61 : responsive (mobile ≤ 480 px : nav en drawer, inspection en modal).
- T-62 : tests manuels checklist SC-001..SC-006 + tests API `pytest tests/` à rester PASS (rétrocompatibilité).
- T-63 : mise à jour `README.md` (section « Web UI ») et `PIPELINE.md`.

## Constitution Check

| Question | Réponse |
|---|---|
| Rupture de contrat API ? | **Non** — routes UI ajoutées ; `/api/*` inchangé. |
| Ajout d'une dépendance npm ? | **Non** — pas de build-time. |
| Dépassement de scope (auth, multi-users) ? | **Exclu** de v1 (documenté dans spec.md « Clauses de réconciliation »). |
| Risque d'atteinte à la CLI existante ? | **Aucun** — le serveur existe déjà, seule l'interface change. |

## Complexité tracking

- **Risque principal** : collision de routes FastAPI (`/` vs `/api/*`). Résolu par l'ordre des routes et le guard `is_file()` du catch-all.
- **Hygiène du worktree & verrouillage strict du scope** : Le répertoire de stockage des projets générés (`projects/`) est explicitement exclu du versioning et protégé par règle absolue. **Aucune tentative de commit ou de manipulation (ajout, modification, suppression via l'agent ou les outils Git) sur les dossiers de projets générés non suivis n'est permise**, garantissant l'étanchéité totale du worktree.
- **Durée du pipeline** : risquée (> 10 min). Atténuée par le polling sur `/api/pipeline/status` et l'affichage par tranches, non par une attente bloquante côté client.
- **Secrets dans les logs** : atténuée par un masque simple (`\*\*\*\*`) des lignes contenant `sk-`, `AI_`, `api_key`, `password` à l'affichage.

---

## Structure livrée (documentation feature)

```text
specs/001-web-ui-autonovel/
├── spec.md              # Spécification (cette branche — UI + back-office à réutiliser)
├── plan.md              # Ce fichier
└── tasks.md             # Tâches (État : ouvert, alignées sur les user stories)
```
