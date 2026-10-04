"""
Unit tests for src/projects.py
"""

import pytest
from pathlib import Path
from src.projects import create_project, list_projects, get_project, delete_project

def test_project_crud(tmp_path):
    # Test creation
    name = "Test Novel Project"
    concept = "A cyberpunk detective story in Neo Paris."
    proj = create_project(name, concept)
    
    assert proj["name"] == name
    assert proj["concept"] == concept
    pid = proj["id"]
    
    # Test listing
    projects = list_projects()
    assert any(p["id"] == pid for p in projects)
    
    # Test retrieval
    retrieved = get_project(pid)
    assert retrieved is not None
    assert retrieved["name"] == name
    
    # Test deletion
    deleted = delete_project(pid)
    assert deleted is True
    assert get_project(pid) is None
