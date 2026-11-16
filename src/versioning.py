"""Narrative Git repositories live inside projects, never in application code."""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from src.project_context import project_directory, narrative_git_dir

BASE_DIR = Path(__file__).resolve().parent.parent


def _directory(project_id):
    return project_directory(project_id, BASE_DIR / "projects")


def run_git_cmd(args: list[str], directory: Path) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True,
                            cwd=str(directory), timeout=15, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git operation failed")
    return result.stdout.strip()


def _repository(project_id, initialize=False):
    directory = _directory(project_id)
    if initialize and not (directory / ".git").exists():
        run_git_cmd(["init", "--initial-branch=main"], directory)
        # Branch creation needs one commit, independent of user Git identity.
        run_git_cmd(["-c", "user.name=Autonovel", "-c", "user.email=autonovel@localhost",
                     "commit", "--allow-empty", "-m", "Initialize narrative history"], directory)
    return narrative_git_dir(directory)


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
    name = _branch(branch_name)
    directory = _repository(project_id, initialize=True)
    run_git_cmd(["switch", "-c", name], directory)
    return True


def switch_branch(branch_name: str, project_id: Optional[str] = None) -> bool:
    name = _branch(branch_name)
    run_git_cmd(["switch", name], _repository(project_id))
    return True


def get_revision_history(chapter_num: Optional[int] = None,
                         project_id: Optional[str] = None) -> List[Dict]:
    directory = _directory(project_id)
    results_file = directory / "results.tsv"
    history = []
    if results_file.exists():
        lines = results_file.read_text(encoding="utf-8").splitlines()
        if lines:
            headers = lines[0].split("\t")
            for line in lines[1:]:
                row = dict(zip(headers, line.split("\t")))
                if chapter_num is not None and f"{chapter_num}" not in row.get("description", ""):
                    continue
                history.append(row)
    return list(reversed(history))
