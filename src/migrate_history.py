"""Idempotent narrative baseline migration. Defaults to a read-only preview."""
import argparse
import json
from pathlib import Path
from src import narrative_history as history


def migrate(root, apply=False):
    results = []
    for directory in sorted((Path(root) / 'projects').iterdir()):
        if not directory.is_dir() or directory.is_symlink(): continue
        item = {'project_id': directory.name}
        try:
            from src.project_context import ensure_data_editable
            ensure_data_editable(directory)
            exists = (directory / '.git').exists()
            tracked = history.validate_repository(directory) if exists else set()
            if tracked:
                item['action'] = 'preserved'
            else:
                item['action'] = 'initialize_baseline'
                item['files'] = sorted(history.files(directory)) + [history.MANIFEST]
                if apply:
                    with history.mutation_guard(directory, directory.name):
                        history.initialize(directory)
                    item['commit'] = history.git(directory, 'rev-parse', 'HEAD')
        except Exception as error:
            item.update(action='blocked', error=str(error))
        results.append(item)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(migrate(args.root, args.apply), ensure_ascii=False, indent=2))
