"""
Unit tests for src/versioning.py
"""

import pytest
from src.versioning import list_branches, create_branch, switch_branch, get_revision_history

def test_versioning_functions():
    branches = list_branches()
    assert isinstance(branches, list)
    assert len(branches) > 0
    
    history = get_revision_history()
    assert isinstance(history, list)
