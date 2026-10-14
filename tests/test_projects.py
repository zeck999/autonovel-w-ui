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

    # Test chapter files
    chapter_path = "chapters/chapter_01.md"
    success_ch = save_project_file(pid, chapter_path, "# Chapter 1\n\nIt was a dark and stormy night.")
    assert success_ch is True

    ch_content = get_project_file(pid, chapter_path)
    assert "It was a dark and stormy night" in ch_content

    files_list = list_project_files(pid)
    assert any(f["name"] == chapter_path for f in files_list)

    delete_project(pid)

def test_existing_projects_consistency():
    projects = list_projects()
    project_ids = [p["id"] for p in projects]
    assert "project-nebulae" in project_ids
    assert "the-clock-work-empire" in project_ids
    assert "chronicles-of-the-astral-vault" in project_ids

    nebulae = get_project("project-nebulae")
    assert nebulae is not None
    assert nebulae["id"] == "project-nebulae"
    assert nebulae["name"] == "Project Nebulae"

    empire = get_project("the-clock-work-empire")
    assert empire is not None
    assert empire["id"] == "the-clock-work-empire"
    assert empire["name"] == "The Clock Work Empire"

    vault = get_project("chronicles-of-the-astral-vault")
    assert vault is not None
    assert vault["id"] == "chronicles-of-the-astral-vault"
    assert vault["name"] == "Chronicles of the Astral Vault"

