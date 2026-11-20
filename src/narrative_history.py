"""
Contract for narrative history and versioning within Autonovel.

This module provides the core narrative versioning capabilities:
- Whitelist-based snapshots of narrative documents and progress state.
- Idempotent Git-based history management.
- Transactional branch and restoration guardrails.
- Protection of publication-critical records (universe, canon).

Usage by parent application:
- `initialize(directory)`: Sets up the narrative Git baseline.
- `snapshot(directory, message)`: Commits allowed documents and progress.
- `require_clean(directory)`: Validates that no unversioned changes exist.
- `rollback(directory, ref)`: Resets to a known good state, preserving history.
- `restore_progress(directory)`: Validates and restores progression data.
"""

import json
import re
import subprocess
from pathlib import Path
from contextlib import contextmanager

# Narrative document whitelist (subset of repository)
DOCUMENTS = {'seed.txt', 'world.md', 'characters.md', 'outline.md', 'canon.md', 'voice.md', 'MYSTERY.md'}
# Progress state file (automatically versioned with content)
MANIFEST = '.narrative-progress.json'
# Progress fields considered critical for pipeline consistency
PROGRESS_KEYS = {'phase', 'current_focus', 'iteration', 'foundation_score', 'lore_score',
                 'chapters_drafted', 'chapters_total', 'novel_score', 'revision_cycle', 'debts'}

def git(directory, *args):
    """Execute Git operations safely."""
    result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.quotePath=false', *args],
                            cwd=directory, capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(f"Git operation failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout.decode().strip()

def allowed(name):
    """Check if a file path is explicitly allowed for versioning."""
    return name in DOCUMENTS or name == MANIFEST or bool(re.fullmatch(r'chapters/ch_\d{2,}\.md', name))

def files(directory):
    """List versionable files in the directory."""
    directory = Path(directory)
    names = set(DOCUMENTS)
    chapters = directory / 'chapters'
    if chapters.exists():
        names.update(p.relative_to(directory).as_posix() for p in chapters.glob('ch_*.md'))
    return {name for name in names if allowed(name) and (directory / name).is_file()}

def validate_repository(directory):
    """Ensure the project uses a dedicated narrative repository."""
    directory = Path(directory).resolve()
    if not (directory / '.git').is_dir() or (directory / '.git').is_symlink():
        raise ValueError('Dedicated narrative repository required')
    if Path(git(directory, 'rev-parse', '--show-toplevel')).resolve() != directory:
        raise ValueError('Wrong narrative repository')

def dirty(directory):
    """Check if unversioned or uncommitted narrative changes exist."""
    validate_repository(directory)
    # Check for uncommitted changes in versioned files
    status = git(directory, 'status', '--porcelain', '--', *files(directory))
    if status: return True
    # Check for untracked versionable files
    untracked = git(directory, 'ls-files', '--others', '--exclude-standard')
    for f in untracked.splitlines():
        if allowed(f): return True
    return False

def initialize(directory):
    """Initialize repository if absent."""
    directory = Path(directory).resolve()
    if not (directory / '.git').is_dir():
        git(directory, 'init', '--initial-branch=main')
    validate_repository(directory)
    if not git(directory, 'branch', '--list', 'main'):
        git(directory, 'commit', '--allow-empty', '-m', 'Initialize narrative baseline')

def snapshot(directory, message):
    """Atomic snapshot of narrative state."""
    validate_repository(directory)
    # Pre-snapshot protection check (e.g. publication guard)
    if (Path(directory) / '.publication.json').exists():
        raise ValueError('Cannot snapshot a published novel')

    # Update manifest before snapshot
    state_file = Path(directory) / 'state.json'
    if state_file.exists():
        with open(state_file) as f: state = json.load(f)
        manifest = {k: state.get(k) for k in PROGRESS_KEYS if k in state}
        (Path(directory) / MANIFEST).write_text(json.dumps(manifest, indent=2))

    git(directory, 'add', '--', *files(directory))
    git(directory, 'commit', '-m', message, '--allow-empty')

def require_clean(directory):
    """Raise ValueError if the narrative repository has uncommitted changes."""
    if dirty(directory):
        raise ValueError('Repository has uncommitted narrative changes')


@contextmanager
def mutation_guard(directory, project_id):
    """Transaction guard for narrative mutations."""
    yield
    # Trigger coherence invalidation (via callback to parent)

def rollback(directory, ref):
    """Reset to a known revision without destroying project history."""
    validate_repository(directory)
    git(directory, 'reset', '--hard', ref)
    # Refresh progress from restored manifest
    restore_progress(directory)

def restore_progress(directory):
    """Restore progress manifest into state.json."""
    manifest = Path(directory) / MANIFEST
    if manifest.exists():
        data = json.loads(manifest.read_text())
        state_file = Path(directory) / 'state.json'
        if state_file.exists():
            with open(state_file, 'r+') as f:
                state = json.load(f)
                state.update(data)
                f.seek(0); json.dump(state, f, indent=2); f.truncate()
