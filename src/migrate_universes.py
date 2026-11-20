"""Idempotent, offline data migration. Never performs provider calls.

python -m src.migrate_universes --data-dir /path/to/application [--apply]
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from src import canon
from src.security import safe_child, validate_id


def migrate(data_dir, apply=False):
    root = Path(data_dir).resolve()
    projects_dir = root / 'projects'
    universes_dir = root / 'universes'
    journal_path = root / '.universe-migration.json'
    journal = json.loads(journal_path.read_text()) if journal_path.exists() else {'version': 1, 'projects': {}}
    results = []
    if not projects_dir.exists():
        return results
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir() or project_dir.is_symlink():
            continue
        try:
            pid = validate_id(project_dir.name)
            state_file = safe_child(project_dir, 'state.json')
            state = json.loads(state_file.read_text(encoding='utf-8'))
            if not isinstance(state, dict):
                raise ValueError('Invalid project metadata')
            uid = state.get('universe_id')
            valid = False
            if uid:
                try:
                    candidate = safe_child(universes_dir, validate_id(uid))
                except ValueError:
                    candidate = universes_dir / ".invalid-selection"
                if (candidate / 'state.json').is_file():
                    metadata = json.loads((candidate / 'state.json').read_text())
                    valid = isinstance(metadata, dict)
            if valid:
                results.append({'project_id': pid, 'action': 'unchanged', 'universe_id': uid})
                continue
            entry = journal['projects'].get(pid)
            if not entry:
                from src.universes import slugify
                base = slugify(state.get('name') or pid)
                uid = base
                number = 1
                reserved = {e['universe_id'] for e in journal['projects'].values()}
                while (universes_dir / uid).exists() or uid in reserved:
                    uid = f'{base}-{number}'
                    number += 1
                entry = {'universe_id': uid, 'name': state.get('name') or pid, 'status': 'prepared'}
                journal['projects'][pid] = entry
            uid = entry['universe_id']
            result = {'project_id': pid, 'action': 'create_universe', 'universe_id': uid, 'name': entry['name']}
            if apply:
                # Persist reservation before creating the universe: restart reuses its ID.
                canon.atomic_json(journal_path, journal)
                backup = root / '.migration-backups' / 'universes-v1' / pid / 'state.json'
                if not backup.exists():
                    canon.atomic_json(backup, state)
                universe_dir = safe_child(universes_dir, validate_id(uid))
                universe_dir.mkdir(parents=True, exist_ok=True)
                universe_state = universe_dir / 'state.json'
                if not universe_state.exists():
                    canon.atomic_json(universe_state, {'id': uid, 'name': entry['name'],
                        'description': 'Automatically created for this novel',
                        'created_at': datetime.now(timezone.utc).isoformat(), 'analysis_status': 'not_analyzed'})
                for filename in ('world.md', 'characters.md', 'canon.md'):
                    path = universe_dir / filename
                    if not path.exists():
                        path.write_text(f'# {filename[:-3].title()}\n', encoding='utf-8')
                state['universe_id'] = uid
                canon.atomic_json(state_file, state)
                entry['status'] = 'completed'
                canon.atomic_json(journal_path, journal)
            results.append(result)
        except (ValueError, OSError, TypeError) as exc:
            results.append({'project_id': project_dir.name, 'action': 'error', 'error': str(exc)})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    results = migrate(args.data_dir, args.apply)
    print(json.dumps({'dry_run': not args.apply, 'results': results}, ensure_ascii=False, indent=2))
    return int(any(result['action'] == 'error' for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
