"""Append-only, source-backed universe ledger. Markdown files are not authority."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4
from src.security import safe_child, validate_id

_LOCKS = {}
_LOCKS_GUARD = RLock()
NARRATIVE_FILES = {'seed.txt', 'world.md', 'characters.md', 'outline.md', 'canon.md', 'voice.md', 'MYSTERY.md'}


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.transaction-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def manuscript_snapshot(project_dir):
    root = Path(project_dir)
    result = {}
    for name in sorted(NARRATIVE_FILES):
        path = safe_child(root, name)
        if path.is_file():
            result[name] = path.read_text(encoding='utf-8')
    chapters = safe_child(root, 'chapters')
    if chapters.is_dir():
        for path in sorted(chapters.glob('*.md')):
            checked = safe_child(root, f'chapters/{path.name}')
            if checked.is_file():
                result[f'chapters/{path.name}'] = checked.read_text(encoding='utf-8')
    return result


def content_hash(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def manuscript_hash(project_dir):
    return content_hash(manuscript_snapshot(project_dir))


def universe_path(universe_id):
    from src.universes import UNIVERSES_DIR
    path = safe_child(UNIVERSES_DIR, validate_id(universe_id))
    if not path.is_dir() or not (path / 'state.json').is_file():
        raise ValueError('Universe not found')
    return path


@contextmanager
def universe_guard(universe_id):
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(validate_id(universe_id), RLock())
    with lock:
        yield


def _events(universe_id):
    directory = safe_child(universe_path(universe_id), '.registry')
    if not directory.exists():
        return []
    events = []
    for path in sorted(directory.glob('*.json')):
        checked = safe_child(directory, path.name)
        events.append(json.loads(checked.read_text(encoding='utf-8')))
    return events


def universe_revision(universe_id):
    root = universe_path(universe_id)
    legacy = {name: safe_child(root, name).read_text(encoding='utf-8')
              for name in ('world.md', 'characters.md', 'canon.md') if safe_child(root, name).is_file()}
    return content_hash({'events': _events(universe_id), 'historical_documents': legacy})


def append_event(universe_id, event):
    """Atomic immutable event file. Caller must hold universe_guard."""
    directory = safe_child(universe_path(universe_id), '.registry')
    directory.mkdir(exist_ok=True)
    event = dict(event)
    event.setdefault('id', uuid4().hex)
    event.setdefault('created_at', datetime.now(timezone.utc).isoformat())
    # Idempotent transaction recovery, never overwrite an existing event.
    for existing in _events(universe_id):
        if existing['id'] == event['id']:
            if any(existing.get(k) != v for k, v in event.items() if k != 'created_at'):
                raise ValueError('Conflicting immutable event')
            return existing
    sequence = len(list(directory.glob('*.json')))
    path = directory / f'{sequence:012d}-{event["id"]}.json'
    atomic_json(path, event)
    render_registry(universe_id)
    return event


def render_registry(universe_id):
    """Rebuildable view only; existing historical Markdown is never overwritten."""
    registry = get_registry(universe_id)
    lines = ['# Registre de l’univers', '', 'Vue dérivée ; les événements .registry sont la source de vérité.', '']
    for item in registry['assertions']:
        label = 'CANON' if item['canon'] else ('ACTIF' if item['active'] else 'REMPLACÉ')
        lines.extend([f'## {label} — {item["id"]}', item['text'],
                      f'Type : {item["kind"]} ; personnage : {item.get("character", "—")} ; époque : {item.get("time", "inconnue")}',
                      f'Source : {item["project_id"]} / {item["source"]["file"]}',
                      '> ' + item['source']['quote'], ''])
    lines.append(f'Publications immuables : {len(registry["publications"])}')
    view = safe_child(universe_path(universe_id), 'registry.md')
    temporary = view.with_name('.registry-view-' + uuid4().hex)
    temporary.write_text('\n'.join(lines), encoding='utf-8')
    temporary.replace(view)


def get_registry(universe_id):
    with universe_guard(universe_id):
        events = _events(universe_id)
        assertions = {}
        publications = []
        corrections = []
        for event in events:
            if event['type'] == 'assertions':
                for assertion in event['assertions']:
                    assertions[assertion['id']] = dict(assertion, canon=False, active=True, lifecycle='active', source_verified=bool(assertion.get('source_evidence')))
                    if assertion.get('supersedes'):
                        assertions[assertion['supersedes']]['active'] = False
                        assertions[assertion['supersedes']]['lifecycle'] = 'superseded'
            elif event['type'] == 'assertion_lifecycle':
                item = assertions.get(event['assertion_id'])
                if item:
                    item.update(lifecycle=event['status'], active=event['status'] == 'active')
            elif event['type'] == 'source_evidence':
                for proof in event['proofs']:
                    if proof['assertion_id'] in assertions:
                        assertions[proof['assertion_id']].update(source_evidence=proof.get('evidence'), source_verified=proof.get('verified', False))
            elif event['type'] == 'publication':
                publications.append(event)
                for identifier in event['assertion_ids']:
                    assertions[identifier]['canon'] = True
            elif event['type'] == 'proofreading':
                corrections.append(event)
        return {'revision': universe_revision(universe_id), 'assertions': list(assertions.values()), 'publications': publications, 'corrections': corrections}


def add_assertions(universe_id, project_id, assertions, manuscript_hash):
    from src import projects
    from src.publication import ensure_editable
    ensure_editable(project_id)
    project = projects.get_project(project_id)
    if project['universe_id'] != universe_id:
        raise ValueError('Project belongs to another universe')
    directory = safe_child(projects.PROJECTS_DIR, validate_id(project_id))
    snapshot = manuscript_snapshot(directory)
    if content_hash(snapshot) != manuscript_hash:
        raise ValueError('Analysis is stale')
    with universe_guard(universe_id):
        ensure_editable(project_id)
        if content_hash(manuscript_snapshot(directory)) != manuscript_hash:
            raise ValueError('Analysis is stale')
        previous = {a['id']: a for a in get_registry(universe_id)['assertions']}
        prepared = []
        replaced = set()
        for raw in assertions:
            item = dict(raw)
            if item.get('kind') not in {'fact', 'belief', 'rumor', 'uncertain'} or not item.get('text'):
                raise ValueError('Invalid assertion')
            source = item.get('source', {})
            if not source.get('quote') or source.get('file') not in snapshot or source['quote'] not in snapshot[source['file']]:
                raise ValueError('Assertion must quote an existing narrative source')
            if item['kind'] == 'belief' and (not item.get('character') or not item.get('time')):
                raise ValueError('Beliefs require a character and narrative time')
            supersedes = item.get('supersedes')
            if supersedes:
                old = previous.get(supersedes)
                if not old or old['canon'] or not old['active'] or old['project_id'] != project_id or supersedes in replaced:
                    raise ValueError('Cannot replace canonical or unrelated assertion')
                replaced.add(supersedes)
            # IDs and authority flags are assigned only by the service.
            evidence = {'file': source['file'], 'text': snapshot[source['file']],
                        'file_hash': content_hash({source['file']: snapshot[source['file']]}),
                        'manuscript_hash': manuscript_hash}
            item.update(id=uuid4().hex, project_id=project_id, manuscript_hash=manuscript_hash,
                        source_evidence=evidence)
            item.pop('canon', None)
            item.pop('active', None)
            prepared.append(item)
        if prepared:
            append_event(universe_id, {'type': 'assertions', 'project_id': project_id, 'assertions': prepared})
        return [a['id'] for a in prepared]


def assertion_lifecycle(universe_id, project_id, assertion_id, status, rationale):
    """Append an audited draft assertion transition. Published assertions never mutate."""
    from src.publication import ensure_editable
    if status not in {'active', 'contested', 'withdrawn'} or not isinstance(rationale, str) or not rationale.strip():
        raise ValueError('A supported status and a reason are required')
    with universe_guard(universe_id):
        ensure_editable(project_id)
        item = next((a for a in get_registry(universe_id)['assertions'] if a['id'] == assertion_id), None)
        if not item or item['project_id'] != project_id or item['canon']:
            raise ValueError('Cannot change canonical or unrelated assertion')
        if item.get('lifecycle') == 'superseded':
            raise ValueError('A superseded assertion cannot be reactivated')
        append_event(universe_id, {'type': 'assertion_lifecycle', 'project_id': project_id,
                                  'assertion_id': assertion_id, 'status': status, 'rationale': rationale.strip()})
    from src.coherence import invalidate_project
    invalidate_project(project_id)
    return next(a for a in get_registry(universe_id)['assertions'] if a['id'] == assertion_id)


def verify_assertion_source(assertion, snapshot):
    source = assertion.get('source', {})
    name, quote = source.get('file'), source.get('quote')
    proof = assertion.get('source_evidence')
    return bool(isinstance(quote, str) and quote and name in snapshot and quote in snapshot[name]
                and assertion.get('source_verified') and isinstance(proof, dict)
                and proof.get('file') == name and isinstance(proof.get('text'), str)
                and quote in proof['text']
                and proof.get('file_hash') == content_hash({name: proof['text']}))


def migrate_source_evidence(universe_id, apply=False):
    """Append proofs only when the original source revision can be verified.

    Legacy mismatches remain explicitly unverified; never manufacture historical text.
    Safe for published projects: publication snapshots are immutable evidence.
    """
    from src import projects
    with universe_guard(universe_id):
        registry = get_registry(universe_id)
        previously = {p['assertion_id'] for e in _events(universe_id) if e['type'] == 'source_evidence' for p in e['proofs']}
        proofs = []
        for item in registry['assertions']:
            if item.get('source_evidence') or item['id'] in previously: continue
            source, snapshot = item['source'], None
            for publication in registry['publications']:
                if publication['project_id'] == item['project_id'] and publication.get('manuscript_hash') == item.get('manuscript_hash'):
                    snapshot = publication.get('snapshot')
                    break
            if snapshot is None:
                path = safe_child(projects.PROJECTS_DIR, validate_id(item['project_id']))
                if path.is_dir():
                    candidate = manuscript_snapshot(path)
                    if content_hash(candidate) == item.get('manuscript_hash'): snapshot = candidate
            name, quote = source.get('file'), source.get('quote')
            verified = bool(snapshot is not None and isinstance(quote, str) and quote and name in snapshot and quote in snapshot[name])
            evidence = ({'file': name, 'text': snapshot[name], 'file_hash': content_hash({name: snapshot[name]}),
                         'manuscript_hash': item.get('manuscript_hash')} if verified else None)
            proofs.append({'assertion_id': item['id'], 'verified': verified, 'evidence': evidence,
                           'reason': 'original_revision_verified' if verified else 'historical_source_unavailable'})
        if apply and proofs: append_event(universe_id, {'type': 'source_evidence', 'proofs': proofs})
        return proofs


def supersede_assertion(universe_id, project_id, assertion_id, proposal, rationale):
    """Replace one active draft assertion with a newly source-validated assertion."""
    from src import projects
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError('An audited replacement reason is required')
    path = safe_child(projects.PROJECTS_DIR, validate_id(project_id))
    snapshot = manuscript_snapshot(path)
    replacement = dict(proposal, supersedes=assertion_id, rationale=rationale.strip())
    result = add_assertions(universe_id, project_id, content_hash(snapshot), [replacement])
    from src.coherence import invalidate_project
    invalidate_project(project_id)
    return result[0]
