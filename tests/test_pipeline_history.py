"""Exercise pipeline history boundaries without importing mutating CLI startup."""
import ast
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / 'run_pipeline.py'


def functions(*names, **namespace):
    tree = ast.parse(SOURCE.read_text())
    selected = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
    exec(compile(selected, str(SOURCE), 'exec'), namespace)
    return namespace


def test_snapshot_and_rollback_delegate_without_broad_git(tmp_path):
    calls = []
    ns = functions('git_add_commit', 'git_reset_hard', BASE_DIR=tmp_path,
                   ensure_data_editable=lambda p: None,
                   narrative_git_dir=lambda p: p,
                   snapshot=lambda p, message: calls.append(('snapshot', p, message)) or 'hash',
                   rollback=lambda p, ref: calls.append(('rollback', p, ref)))
    assert ns['git_add_commit']('fixture') == 'hash'
    ns['git_reset_hard']('HEAD')
    assert calls == [('snapshot', tmp_path, 'fixture'), ('rollback', tmp_path, 'HEAD')]


def test_foundation_progression_saved_before_snapshot():
    state = {'foundation_score': 0, 'iteration': 0}
    saved = {}
    captured = []
    ns = functions('run_foundation', BASE_DIR=Path('/fixture'), FOUNDATION_THRESHOLD=7.5,
        MAX_FOUNDATION_ITERS=1, ensure_data_editable=lambda p: None,
        banner=lambda *a: None, step=lambda *a: None,
        uv_run=lambda *a, **k: SimpleNamespace(stdout='fixture'),
        parse_score=lambda *a: 8, parse_lore_score=lambda *a: 8,
        save_state=lambda s: (saved.clear(), saved.update(s)),
        git_add_commit=lambda message: captured.append((message, dict(saved))) or 'hash',
        log_result=lambda *a: None, get_total_chapters=lambda s: 3)
    ns['run_foundation'](state)
    assert captured[0][1]['foundation_score'] == 8
    assert captured[0][1]['lore_score'] == 8
    assert captured[-1][1]['phase'] == 'drafting'
    assert captured[-1][1]['chapters_total'] == 3


def test_no_global_staging_or_hard_reset_remains():
    source = SOURCE.read_text()
    assert '["git", "add", "--", "."]' not in source
    assert '["git", "reset", "--hard"' not in source
    assert '["git", "restore"' not in source
