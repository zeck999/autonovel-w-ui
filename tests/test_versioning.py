"""
Unit tests for src/versioning.py
"""

import pytest
from src.versioning import list_branches, create_branch, switch_branch, get_revision_history

def test_versioning_functions():
    with pytest.raises(ValueError):
        list_branches()
    with pytest.raises(ValueError):
        create_branch("unsafe; printf nope")
