"""Two distinct graphs: authored choices and the project's local Git ancestry."""
from src import narrative_history as history

HISTORY_LIMIT = 150


def story_graph(story, chapters):
    known = set(chapters)
    return {
        'start': story.start if story.start in known else None,
        'nodes': [{'id': name, 'label': f'Chapitre {int(name[12:-3])}'} for name in chapters],
        'edges': [{'id': choice.id, 'source': choice.source, 'target': choice.target, 'label': choice.label}
                  for choice in story.choices if choice.source in known and choice.target in known],
    }


def revision_graph(directory, limit=HISTORY_LIMIT):
    empty = {'nodes': [], 'edges': [], 'truncated': False}
    if not (directory / '.git').exists() and not (directory / '.git').is_symlink():
        return empty
    history.validate_repository(directory)
    refs = history.git(directory, 'for-each-ref', '--format=%(objectname)%00%(refname:short)', 'refs/heads')
    if not refs:
        return empty
    branches = {}
    for line in refs.split('\n'):
        sha, name = line.split('\0', 1)
        branches.setdefault(sha, []).append(name)
    log = history.git(directory, '--no-pager', 'log', '--branches', '--topo-order', '--no-notes', '--no-show-signature',
                      f'--max-count={limit + 1}', '--format=%H%x00%P%x00%aI%x00%s', '--')
    rows = log.split('\n') if log else []
    nodes = []
    for row in rows[:limit]:
        sha, parents, date, label = row.split('\0', 3)
        nodes.append(dict(id=sha, parents=parents.split(), date=date, label=label[:300], branches=branches.get(sha, [])))
    known = {node['id'] for node in nodes}
    return {'nodes': nodes, 'edges': [{'source': parent, 'target': node['id']} for node in nodes
                                     for parent in node['parents'] if parent in known],
            'truncated': len(rows) > limit}
