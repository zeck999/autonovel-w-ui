"""Separate immutable application code/configuration from per-novel data.

CLI callers opt into isolation with AUTONOVEL_PROJECT_DIR. Legacy commands may
still read root templates, but Git writes there are deliberately forbidden.
"""
import os
import re
import signal
import subprocess
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    value = os.environ.get("AUTONOVEL_PROJECT_DIR")
    return Path(value).expanduser().resolve() if value else CODE_DIR


DATA_DIR = data_dir()


def project_directory(project_id: str, root: Path | None = None) -> Path:
    from src.security import validate_id, safe_child
    root = (root or CODE_DIR / "projects").resolve()
    path = safe_child(root, validate_id(project_id))
    if not path.is_dir():
        raise ValueError("Project not found")
    return path


def ensure_data_editable(directory: Path) -> None:
    """Fail closed on published novels or interrupted publication transactions.

    This guard is intentionally separate from data_dir(): reading/evaluation of
    a published novel is allowed. It protects application entry points, not
    against someone editing files directly with OS permissions.
    """
    import json
    directory = Path(directory).resolve()
    for name in (".publication.json", ".publication-transaction.json", ".publication_transaction.json"):
        marker = directory / name
        if marker.is_symlink():
            raise ValueError("Invalid publication metadata")
        if not marker.exists():
            continue
        try:
            metadata = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("Unreadable publication metadata; editing is blocked")
        if not isinstance(metadata, dict):
            raise ValueError("Invalid publication metadata; editing is blocked")
        if name != ".publication.json" or metadata.get("publication_status") == "published" or metadata.get("status") in {"published", "publishing"}:
            raise ValueError("Published novels are read-only; use the proofread correction workflow")


def _narrative_fingerprint(directory: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    names = ("seed.txt", "world.md", "characters.md", "outline.md", "canon.md", "voice.md", "MYSTERY.md")
    paths = [directory / name for name in names]
    paths += sorted((directory / "chapters").glob("ch_*.md"))
    for path in paths:
        if path.is_file() and not path.is_symlink():
            digest.update(str(path.relative_to(directory)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def notify_data_changed(directory: Path) -> None:
    """Invalidate analysis after a CLI mutation; never call a provider here."""
    try:
        from src.coherence import mark_directory_changed
    except ImportError:
        # During upgrades the watcher may not be installed yet. Leave a durable
        # dirty marker rather than silently considering previous reports valid.
        import json
        (Path(directory) / ".coherence-dirty.json").write_text(
            json.dumps({"status": "stale", "reason": "CLI mutation"}), encoding="utf-8")
    else:
        mark_directory_changed(Path(directory))


def guard_mutating_cli(directory: Path) -> None:
    """Reject early (before API use) and invalidate if a CLI changed manuscript."""
    import atexit
    directory = Path(directory).resolve()
    ensure_data_editable(directory)
    # Shared generation leases prevent a simultaneous publication from freezing
    # a snapshot while this CLI (or a nested generator) can still write.
    import fcntl
    from src.security import safe_child
    lease = safe_child(directory, '.generation.lock').open('a+')
    try:
        fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        ensure_data_editable(directory)
    except BaseException:
        lease.close()
        raise
    atexit.register(lease.close)
    before = _narrative_fingerprint(directory)

    def after():
        if directory.exists() and _narrative_fingerprint(directory) != before:
            notify_data_changed(directory)
    atexit.register(after)


def execute(args: list[str], *, cwd: Path, timeout: int, env=None):
    """Run without a shell and terminate the whole process group on timeout.

    An outer pipeline subprocess owns its group; nested scripts must remain in
    that group so cancellation of the outer operation also stops its children.
    """
    inherited = os.environ.get("AUTONOVEL_PROCESS_GROUP") == "1"
    child_env = dict(os.environ if env is None else env)
    child_env["AUTONOVEL_PROCESS_GROUP"] = "1"
    process = subprocess.Popen(
        [str(arg) for arg in args], cwd=str(cwd), env=child_env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=not inherited,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        # Never leave a costly generation running after its caller has failed.
        if process.poll() is None:
            if not inherited and os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                if not inherited and os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.communicate()
        raise
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)


def narrative_git_dir(directory: Path) -> Path:
    """Require a dedicated repository, never a parent software repository."""
    directory = directory.resolve()
    if directory == CODE_DIR or not (directory / ".git").is_dir():
        raise ValueError("Narrative versioning requires a dedicated project repository")
    return directory
