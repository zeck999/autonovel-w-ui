"""
Unit tests for src/projects.py
"""

import pytest
from pathlib import Path
from src.projects import create_project, list_projects, get_project, delete_project, list_project_files, get_project_file, save_project_file

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

def test_project_files_functions():
    proj = create_project("Files Func Test", "Testing project files helper functions.")
    pid = proj["id"]

    files = list_project_files(pid)
    assert any(f["name"] == "seed.txt" for f in files)

    content = get_project_file(pid, "seed.txt")
    assert "Testing project files" in content

    success = save_project_file(pid, "characters.md", "# Characters\n\nHero: Alex.")
    assert success is True

    chars_content = get_project_file(pid, "characters.md")
    assert "Hero: Alex" in chars_content

    delete_project(pid)
