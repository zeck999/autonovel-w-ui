"""
Unit tests for review API endpoints (/api/reviews/latest)
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
from src.api import app

client = TestClient(app)

def test_reviews_latest_empty():
    response = client.get("/api/reviews/latest")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_reviews_latest_with_mock_data():
    edit_logs = Path("edit_logs")
    edit_logs.mkdir(exist_ok=True)
    mock_file = edit_logs / "20261006_120000_review.json"
    mock_data = {
        "timestamp": "20261006_120000",
        "title": "Test Novel",
        "stars": 4.5,
        "total_items": 1,
        "major_items": 0,
        "qualified_items": 1,
        "critic_summary": "Great novel.",
        "professor_items": [
            {
                "number": 1,
                "title": "Pacing adjustment",
                "severity": "minor",
                "type": "compression",
                "qualified": True,
                "suggestion": "Trim paragraph 3.",
                "full_text": "1. Pacing adjustment..."
            }
        ]
    }
    mock_file.write_text(json.dumps(mock_data))
    try:
        response = client.get("/api/reviews/latest")
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == "Test Novel"
        assert data.get("stars") == 4.5
        assert "file_path" in data
    finally:
        if mock_file.exists():
            mock_file.unlink()
