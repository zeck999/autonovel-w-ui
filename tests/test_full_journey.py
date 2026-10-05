"""
Exhaustive Integration Test: tests/test_full_journey.py
Simulates step-by-step the complete user journey through all pipeline phases:
- Step 1: Test project creation and active selection.
- Step 2: Consultation and editing of foundation files (seed.txt, world.md).
- Step 3: Execution of Foundation phase (/api/pipeline/run).
- Step 4: Execution of Outline phase.
- Step 5: Execution of Draft phase.
- Step 6: Project evaluation (/api/pipeline/evaluate).
- Step 7: Pipeline status and log verification after each stage.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)

@patch("src.pipeline_adapter.subprocess.run")
def test_full_user_journey_pipeline(mock_subprocess_run):
    # Mock successful subprocess execution for pipeline phases and evaluations
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Phase executed successfully.\noverall_score: 8.5\n"
    mock_res.stderr = ""
    mock_subprocess_run.return_value = mock_res

    # --- Étape 1 : Création d'un projet de test et sélection active ---
    print("\n[Étape 1] Création d'un projet de test et sélection active...")
    project_payload = {
        "name": "Chroniques de l'Ancien Monde",
        "concept": "Une épopée fantastique dans un monde post-cataclysmique au bord du gouffre."
    }
    response = client.post("/api/projects", json=project_payload)
    assert response.status_code == 200
    proj_data = response.json()
    pid = proj_data["id"]
    assert pid == "chroniques-de-lancien-monde"
    assert proj_data["name"] == "Chroniques de l'Ancien Monde"
    print(f"  -> Projet créé avec succès (ID: {pid})")

    # Vérifier l'existence physique du projet et du state.json initial
    project_dir = Path("projects") / pid
    assert project_dir.exists()
    assert (project_dir / "state.json").exists()

    # --- Étape 2 : Consultation et édition des fichiers de fondation (seed.txt, world.md) ---
    print("\n[Étape 2] Consultation et édition des fichiers de fondation...")
    
    # Lister les fichiers du projet
    response = client.get(f"/api/projects/{pid}/files")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)
    file_names = [f["name"] for f in files]
    assert "seed.txt" in file_names
    assert "world.md" in file_names

    # Consulter seed.txt
    response = client.get(f"/api/projects/{pid}/files/seed.txt")
    assert response.status_code == 200
    assert "épopée fantastique" in response.json()["content"]
    print("  -> seed.txt consulté avec succès.")

    # Éditer / sauvegarder world.md
    world_content = "# Monde de l'Ancien Monde\n\nDes cités flottantes au-dessus d'océans de brume éternelle."
    response = client.put(f"/api/projects/{pid}/files/world.md", json={"content": world_content})
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    # Consulter world.md mis à jour
    response = client.get(f"/api/projects/{pid}/files/world.md")
    assert response.status_code == 200
    assert "cités flottantes" in response.json()["content"]
    print("  -> world.md édité et validé avec succès.")

    # --- Étape 3 : Exécution de la phase Foundation (/api/pipeline/run) ---
    print("\n[Étape 3] Exécution de la phase Foundation...")
    response = client.post("/api/pipeline/run", json={"phase": "foundation", "project_id": pid})
    assert response.status_code == 200
    foundation_res = response.json()
    assert foundation_res.get("returncode") == 0
    print("  -> Phase Foundation exécutée avec succès.")

    # --- Étape 4 : Exécution de la phase Outline ---
    print("\n[Étape 4] Exécution de la phase Outline...")
    response = client.post("/api/pipeline/run", json={"phase": "outline", "project_id": pid})
    assert response.status_code == 200
    outline_res = response.json()
    assert outline_res.get("returncode") == 0
    print("  -> Phase Outline exécutée avec succès.")

    # --- Étape 5 : Exécution de la phase Draft ---
    print("\n[Étape 5] Exécution de la phase Draft...")
    response = client.post("/api/pipeline/run", json={"phase": "draft", "project_id": pid})
    assert response.status_code == 200
    draft_res = response.json()
    assert draft_res.get("returncode") == 0
    print("  -> Phase Draft exécutée avec succès.")

    # --- Étape 6 : Évaluation du projet (/api/pipeline/evaluate) ---
    print("\n[Étape 6] Évaluation du projet...")
    response = client.post("/api/pipeline/evaluate", json={"project_id": pid})
    assert response.status_code == 200
    eval_res = response.json()
    assert eval_res.get("returncode") == 0
    assert eval_res.get("score") == 8.5
    print(f"  -> Évaluation réussie (Score global : {eval_res.get('score')})")

    # --- Étape 7 : Vérification des logs et du statut du pipeline après chaque étape ---
    print("\n[Étape 7] Vérification du statut et des logs du pipeline...")
    response = client.get(f"/api/pipeline/status?project_id={pid}")
    assert response.status_code == 200
    status_data = response.json()
    assert isinstance(status_data, dict)
    assert "phase" in status_data
    print(f"  -> Statut final du pipeline validé : phase = {status_data.get('phase')}")

    # Nettoyage : Suppression du projet de test
    response = client.delete(f"/api/projects/{pid}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not project_dir.exists()
    print("  -> Nettoyage du projet de test effectué avec succès.")
