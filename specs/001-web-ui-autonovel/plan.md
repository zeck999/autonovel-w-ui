# Plan d'Implémentation : Interface Web Autonovel (Versioning, Multi-projet, Univers Partagés)

**Branche** : `001-web-ui-autonovel` | **Date** : 2026-10-04 | **Spécification** : [spec.md](./spec.md)

## Résumé

Implémentation d'une interface web et d'une couche d'orchestration pour Autonovel supportant :
1. La gestion multi-projet (projets multiples isolés).
2. Les univers partagés (lore, personnages et world-building communs aux séries/spin-offs).
3. Le versioning et les branches narratives (historique des révisions, branches de test/écriture).

## Contexte Technique

**Langage/Version** : Python 3.12+, FastAPI / Streamlit / ou UI Web légère (FastAPI backend + interface web moderne), HTML/CSS/JS ou framework léger.
**Stockage** : Structure de fichiers locale enrichie (répertoires `projects/`, `universes/`, métadonnées JSON/YAML).
**Tests** : pytest pour les services backend, tests unitaires et d'intégration.
