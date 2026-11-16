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
