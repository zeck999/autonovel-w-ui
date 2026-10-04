"""
src/versioning.py — Narrative branches and revision history management for Autonovel.
Supports tracking revision history, scores, and narrative branches.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent.parent

def run_git_cmd(cmd: str) -> str:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(BASE_DIR), timeout=15)
        return res.stdout.strip()
    except Exception:
        return ""

def list_branches(project_id: Optional[str] = None) -> List[str]:
    # Returns git branches or project-specific branch folders
    out = run_git_cmd("git branch --list")
    branches = []
    for line in out.splitlines():
        branch = line.replace("*", "").strip()
        if branch:
            branches.append(branch)
    if not branches:
        branches = ["main"]
    return branches

def create_branch(branch_name: str, project_id: Optional[str] = None) -> bool:
    res = run_git_cmd(f"git checkout -b {branch_name}")
    # Switch back to main or stay? Usually checkout -b switches to it.
    return True

def switch_branch(branch_name: str, project_id: Optional[str] = None) -> bool:
    res = run_git_cmd(f"git checkout {branch_name}")
    return res != "" or "Switched" in run_git_cmd("git status")

def get_revision_history(chapter_num: Optional[int] = None, project_id: Optional[str] = None) -> List[Dict]:
    # Parse results.tsv or git log for chapter/revision history
    results_file = BASE_DIR / "results.tsv"
    if project_id:
        p_results = BASE_DIR / "projects" / project_id / "results.tsv"
        if p_results.exists():
            results_file = p_results

    history = []
    if results_file.exists():
        try:
            lines = results_file.read_text().splitlines()
            for line in lines[1:]: # skip header
                parts = line.split("\t")
                if len(parts) >= 6:
                    commit, phase, score, word_count, status, description = parts[:6]
                    if chapter_num is not None:
                        if f"ch{chapter_num:02d}" not in phase and f"ch{chapter_num}" not in description.lower():
                            continue
                    history.append({
                        "commit": commit,
                        "phase": phase,
                        "score": score,
                        "word_count": word_count,
                        "status": status,
                        "description": description
                    })
        except Exception:
            pass

    # Fallback to git log if no results.tsv entries
    if not history:
        log_out = run_git_cmd("git log --oneline -n 20")
        for line in log_out.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                history.append({
                    "commit": parts[0],
                    "phase": "git",
                    "score": "?",
                    "word_count": "0",
                    "status": "commit",
                    "description": parts[1]
                })

    return history
