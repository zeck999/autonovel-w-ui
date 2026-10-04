"""
Unit tests for src/universes.py
"""

import pytest
from src.universes import create_universe, list_universes, get_universe, delete_universe

def test_universe_crud():
    name = "Elaria Epic Universe"
    desc = "High fantasy setting with dual moons and crystal magic."
    univ = create_universe(name, desc)
    
    assert univ["name"] == name
    assert univ["description"] == desc
    uid = univ["id"]
    
    universes = list_universes()
    assert any(u["id"] == uid for u in universes)
    
    retrieved = get_universe(uid)
    assert retrieved is not None
    assert retrieved["name"] == name
    
    deleted = delete_universe(uid)
    assert deleted is True
    assert get_universe(uid) is None
