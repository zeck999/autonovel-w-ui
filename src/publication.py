"""Irreversible publication, journalled across project and universe directories."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from src import canon
from src.security import safe_child, validate_id
from src.jobs import project_guard


def _directory(project_id):
    from src.projects import PROJECTS_DIR
    path = safe_child(PROJECTS_DIR, validate_id(project_id))
    if not path.is_dir():
        raise ValueError('Project not found')
    return path


def _read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _finish(directory, transaction):
    universe_id = transaction['universe_id']
    with canon.universe_guard(universe_id):
        snapshot = directory / '.published' / 'original.json'
        if snapshot.exists():
            if _read(snapshot) != transaction['snapshot']:
                raise ValueError('Published original is immutable')
        else:
            canon.atomic_json(snapshot, transaction['snapshot'])
        canon.append_event(universe_id, transaction['event'])
        status = transaction['status']
        canon.atomic_json(directory / '.publication.json', status)
        # Keep immutable transaction journal for recovery/audit.
        return status


def recover(project_id):
    directory = _directory(project_id)
    transaction = _read(directory / '.publication-transaction.json')
    if transaction:
        status = _read(directory / '.publication.json')
        if status and status.get('publication_id') == transaction['status']['publication_id']:
            return status
        return _finish(directory, transaction)
    return _read(directory / '.publication.json', {'publication_status': 'draft'})


def get_status(project_id):
    return recover(project_id)


def ensure_directory_editable(directory):
    directory = Path(directory)
    # The presence of the prepare journal freezes writes even before recovery.
    if (directory / '.publication-transaction.json').exists():
        raise ValueError('Published novels are read-only; use the formal correction workflow')
    status = _read(directory / '.publication.json', {})
    if status.get('publication_status') == 'published':
        raise ValueError('Published novels are read-only; use the formal correction workflow')


def ensure_editable(project_id):
    ensure_directory_editable(_directory(project_id))


def _readiness(project_id, directory, manuscript_hash, universe_revision):
    from src.coherence import publication_check
    report = publication_check(project_id)
    if report.get('manuscript_hash') != manuscript_hash or report.get('universe_revision') != universe_revision:
        raise ValueError('Coherence report is stale')
    return report


def publish(project_id, confirmation=False):
    import fcntl
    directory = _directory(project_id)
    with safe_child(directory, '.generation.lock').open('a+') as lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('A CLI generation is active; publication is blocked until it finishes')
        return _publish_locked(project_id, confirmation)


def _publish_locked(project_id, confirmation=False):
    if confirmation is not True:
        raise ValueError('Explicit irreversible-publication confirmation is required')
    with project_guard(project_id):
        directory = _directory(project_id)
        status = recover(project_id)
        if status['publication_status'] == 'published':
            return status
        from src.projects import get_project
        project = get_project(project_id)
        universe_id = project.get('universe_id')
        if not universe_id:
            raise ValueError('A valid universe is required')
        with canon.universe_guard(universe_id):
            snapshot = canon.manuscript_snapshot(directory)
            if not any(name.startswith('chapters/') and value.strip() for name, value in snapshot.items()):
                raise ValueError('Cannot publish a novel without chapters')
            fingerprint = canon.content_hash(snapshot)
            revision = canon.universe_revision(universe_id)
            report = _readiness(project_id, directory, fingerprint, revision)
            identifier = uuid4().hex
            date = datetime.now(timezone.utc).isoformat()
            active = [a for a in canon.get_registry(universe_id)['assertions']
                      if a['project_id'] == project_id and a['active']]
            for assertion in active:
                source = assertion.get('source', {})
                if not canon.verify_assertion_source(assertion, snapshot):
                    raise ValueError('An active universe assertion has an outdated source; replace it before publication')
            assertions = [a['id'] for a in active]
            event = {'id': identifier, 'type': 'publication', 'project_id': project_id,
                     'created_at': date, 'assertion_ids': assertions,
                     'manuscript_hash': fingerprint, 'snapshot': snapshot}
            status = {'publication_status': 'published', 'published_at': date,
                      'manuscript_hash': fingerprint, 'universe_id': universe_id,
                      'verified_universe_revision': revision, 'publication_id': identifier}
            transaction = {'snapshot': snapshot, 'event': event, 'status': status, 'universe_id': universe_id}
            # No write is allowed after prepare; readers recover both sides.
            canon.atomic_json(directory / '.publication-transaction.json', transaction)
            return _finish(directory, transaction)
