"""Filesystem boundary helpers shared by API services. Never use string prefixes."""
import re
from pathlib import Path


def validate_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[^\W_][\w-]{0,127}", value, re.UNICODE):
        raise ValueError("Invalid project or universe identifier")
    return value


def safe_child(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    rel = Path(relative)
    if not relative or rel.is_absolute() or ".." in rel.parts or "\\" in relative or "\x00" in relative:
        raise ValueError("Invalid relative path")
    candidate = root / rel
    # Reject symlinks even when their current target is within the boundary.
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symbolic links are not allowed")
    resolved = candidate.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError("Path is outside its permitted directory")
    return resolved


def project_file(root: Path, filename: str) -> Path:
    path = safe_child(root, filename)
    rel = path.relative_to(Path(root).resolve())
    allowed_root = {"seed.txt", "world.md", "characters.md", "outline.md", "canon.md", "voice.md", "MYSTERY.md"}
    chapter = len(rel.parts) == 2 and rel.parts[0] == "chapters" and re.fullmatch(r"ch_\d{2,}\.md", rel.name)
    if not (len(rel.parts) == 1 and rel.name in allowed_root) and not chapter:
        raise ValueError("File is not editable through the API")
    return path
