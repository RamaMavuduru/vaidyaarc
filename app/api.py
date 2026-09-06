"""
VaidyaArc Clinical Brain Service - Minimal FastAPI HTTP Wrapper.

Exposes:
- GET /health
- POST /v1/clinical/turn

Directly delegates turn execution to app.orchestrator.process_turn().
Contains ZERO clinical logic, rules, or state manipulation.
"""

from typing import Any
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    TurnResponseDTO,
)
from app.orchestrator import process_turn


app = FastAPI(
    title="VaidyaArc Clinical Brain Service",
    description="Authoritative, decoupled clinical intelligence core for VaidyaArc (Phases 1B-12.5)",
    version="1.0.0",
)

# Enable CORS for local backend/development communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Health & Readiness probe for the clinical brain service."""
    return {
        "status": "healthy",
        "service": "vaidyaarc-clinical-brain",
        "version": "1.0.0",
        "phases": "1B-12.5",
    }


@app.post(
    "/v1/clinical/turn",
    response_model=TurnResponseDTO,
    status_code=status.HTTP_200_OK,
    tags=["Clinical Turn"],
)
def handle_clinical_turn(input_dto: NormalizedClinicalInputDTO) -> TurnResponseDTO:
    """
    Executes a single clinical turn for a patient encounter.
    Directly invokes authoritative process_turn() orchestrator.
    """
    try:
        response = process_turn(input_dto)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical brain execution failed: {str(exc)}",
        ) from exc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

