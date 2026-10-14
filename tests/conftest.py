import pytest
from pathlib import Path

TRACKED_FILES = [
    "state.json",
    "seed.txt",
    "world.md",
    "characters.md",
    "canon.md",
    "outline.md",
    "voice.md",
]

@pytest.fixture(autouse=True)
def preserve_repo_root_files():
    base_dir = Path(__file__).resolve().parent.parent
    saved = {}
    for filename in TRACKED_FILES:
        filepath = base_dir / filename
        if filepath.exists():
            saved[filepath] = filepath.read_bytes()
        else:
            saved[filepath] = None

    yield

    for filepath, original_bytes in saved.items():
        if original_bytes is not None:
            if not filepath.exists() or filepath.read_bytes() != original_bytes:
                filepath.write_bytes(original_bytes)
        else:
            if filepath.exists():
                filepath.unlink()
