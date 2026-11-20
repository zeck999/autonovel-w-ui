import os
"""Narrative Git repositories live inside projects, never in application code."""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from src.project_context import project_directory, narrative_git_dir, ensure_data_editable, notify_data_changed

BASE_DIR = Path(__file__).resolve().parent.parent


def _directory(project_id):
    return project_directory(project_id, Path(os.environ.get("AUTONOVEL_APP_DATA_DIR", BASE_DIR)) / "projects")


def run_git_cmd(args: list[str], directory: Path) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True,
                            cwd=str(directory), timeout=15, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git operation failed")
    return result.stdout.strip()


def _repository(project_id, initialize=False):
    from src import narrative_history as history
    directory = _directory(project_id)
    if initialize:
        history.initialize(directory)
    history.validate_repository(directory)
    return directory


def _branch(branch_name):
    if not branch_name or branch_name.startswith("-"):
        raise ValueError("Invalid branch name")
    # check-ref-format is validation, not shell execution.
    result = subprocess.run(["git", "check-ref-format", "--branch", branch_name],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError("Invalid branch name")
    return branch_name


def list_branches(project_id: Optional[str] = None) -> List[str]:
    directory = _directory(project_id)
    if not (directory / ".git").is_dir():
        return []
    return run_git_cmd(["branch", "--format=%(refname:short)"],
                       narrative_git_dir(directory)).splitlines()


def create_branch(branch_name: str, project_id: Optional[str] = None) -> bool:
    from src import narrative_history as history
    directory = _directory(project_id)
    with history.mutation_guard(directory, project_id):
        new_repository = not (directory / '.git').exists()
        history.initialize(directory)
        if new_repository or not history.git(directory, 'ls-tree', '-r', '--name-only', 'HEAD'):
            history.snapshot(directory, 'Initial narrative snapshot')
        history.require_clean(directory)
        history.git(directory, 'switch', '-c', _branch(branch_name))
    return True


def switch_branch(branch_name: str, project_id: Optional[str] = None) -> bool:
    from src import narrative_history as history
    directory = _directory(project_id)
    with history.mutation_guard(directory, project_id):
        history.require_clean(directory)
        branch = _branch(branch_name)
        names = history.git(directory, 'ls-tree', '-r', '--name-only', 'refs/heads/' + branch).splitlines()
        if history.MANIFEST not in names or any(not history.allowed(name) for name in names):
            raise ValueError('Target branch has no safe narrative snapshot')
        for name in names:
            from src.security import safe_child
            safe_child(directory, name)
        history.git(directory, 'switch', branch)
        history.restore_progress(directory)
        notify_data_changed(directory)
    return True


def get_status(project_id):
    from src import narrative_history as history
    directory = _directory(project_id)
    if not (directory / '.git').is_dir(): return {'branch': None, 'dirty': False}
    return {'branch': history.git(directory, 'branch', '--show-current'), 'dirty': history.dirty(directory)}


def restore_revision(project_id, ref, confirmation=False):
    from src import narrative_history as history
    if confirmation is not True: raise ValueError('Explicit restore confirmation required')
    directory = _directory(project_id)
    with history.mutation_guard(directory, project_id):
        history.require_clean(directory)
        target = history.revision(directory, ref)
        history.rollback(directory, target)
        commit = history.snapshot(directory, 'Restore narrative revision ' + target[:12])
        notify_data_changed(directory)
    return {'commit': commit}


def get_revision_history(chapter_num: Optional[int] = None,
                         project_id: Optional[str] = None) -> List[Dict]:
    from src import narrative_history as history
    directory = _directory(project_id)
    if not (directory / '.git').is_dir(): return []
    args = ['log', '--format=%H%x09%s', '-100']
    if chapter_num is not None: args += ['--', f'chapters/ch_{chapter_num:02d}.md']
    return [{'commit': line.split('\t',1)[0], 'description': line.split('\t',1)[1],
             'phase': '', 'score': '', 'word_count': '', 'status': 'snapshot'}
            for line in history.git(directory, *args).splitlines()]
