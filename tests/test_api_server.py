"""
Integration & Contract tests for the VaidyaArc FastAPI HTTP Server.
Tests /health and /v1/clinical/turn endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.api import app


from app.llm_adapter import set_llm_adapter, DeterministicFallbackAdapter

@pytest.fixture(autouse=True)
def setup_deterministic_adapter():
    set_llm_adapter(DeterministicFallbackAdapter())

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """Verifies GET /health returns 200 and valid status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vaidyaarc-clinical-brain"
    assert "phases" in data


def test_clinical_turn_normal_intake(client):
    """Verifies normal non-emergency turn execution."""
    payload = {
        "patient_id": "PAT_TEST_001",
        "episode_id": "EP_TEST_001",
        "channel": "mobile_app",
        "message": {
            "original_text": "I have mild headache since yesterday morning",
            "original_language": "en",
            "source": "patient",
            "confidence": 1.0,
            "provenance": "patient_typed"
        },
        "patient_profile": {
            "age": 28,
            "sex": "female",
            "medical_conditions": [],
            "allergies": []
        }
    }

    response = client.post("/v1/clinical/turn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "PAT_TEST_001"
    assert data["session_id"] == "EP_TEST_001"
    assert data["status"] in ["in_progress", "complete"]
    assert data["immediate_attention_required"] is False
    assert "updated_state" in data
    assert isinstance(data["updated_state"], dict)


def test_clinical_turn_emergency_short_circuit(client):
    """Verifies immediate emergency red flag detection and short-circuiting."""
    payload = {
        "patient_id": "PAT_EMERGENCY",
        "episode_id": "EP_EMERGENCY",
        "channel": "mobile_app",
        "message": {
            "original_text": "I am having sudden severe chest pain with shortness of breath",
            "original_language": "en",
            "source": "patient"
        }
    }

    response = client.post("/v1/clinical/turn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "emergency"
    assert data["immediate_attention_required"] is True
    assert "EMERGENCY" in data["conversation_message"].upper()
    assert data["red_flag_status"] == "red_flags_detected"
    assert len(data["red_flags"]) > 0
    assert data["clinical_output"] is not None


def test_clinical_turn_invalid_payload_returns_422(client):
    """Verifies schema validation rejection on missing required fields."""
    # message is missing
    payload = {
        "patient_id": "PAT_INVALID"
    }

    response = client.post("/v1/clinical/turn", json=payload)
    assert response.status_code == 422


from tests.fixtures.brain_acceptance_fixtures import JOURNEY_01_ROUTINE_SIMPLE

def test_clinical_turn_state_snapshot_rehydration(client):
    """Verifies state_snapshot is accepted and state is preserved across turns."""
    payload = JOURNEY_01_ROUTINE_SIMPLE.model_dump()
    response = client.post("/v1/clinical/turn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["updated_state"]["chief_complaint"] == "tension headache"
    assert data["updated_state"]["nature_of_pain"] == "dull ache"
    assert data["updated_state"]["duration"] == "1 day"
    assert data["updated_state"]["severity"] == "mild"
    assert data["status"] == "complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
