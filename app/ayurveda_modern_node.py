"""
Phase 7: Ayurveda <-> Modern Medicine Representation LangGraph Node.

Consumes upstream intake (Phase 1B), safety (Phase 2A), risk convergence (Phase 2B),
clinical case representation (Phase 3), care navigation (Phase 4), and follow-up (Phase 5).
Executes deterministic dual-perspective descriptive representation and correspondence mapping.

ZERO-LLM. 100% DETERMINISTIC.
"""

from typing import Any

from app.state import VaidyaArcState
from app.ayurveda_modern_schema import AyurvedaModernOutput
from app.ayurveda_modern_mapping import generate_ayurveda_modern_representation


def ayurveda_modern_representation(state: VaidyaArcState) -> dict[str, Any]:
    """
    Phase 7 LangGraph Node: Ayurveda <-> Modern Medicine Representation.

    Produces structured, dual-perspective representation without diagnosis,
    without treatment prescription, and without automatic Dosha/Prakriti classification.
    """
    try:
        output: AyurvedaModernOutput = generate_ayurveda_modern_representation(state)

        safety_notes: list[str] = [
            output.safety_constraints.no_diagnosis_disclaimer,
            output.safety_constraints.no_treatment_disclaimer,
            output.safety_constraints.non_equivalence_disclaimer,
            output.safety_constraints.missing_not_absent_disclaimer,
        ]
        if output.safety_constraints.emergency_warning:
            safety_notes.insert(0, output.safety_constraints.emergency_warning)

        return {
            "ayurveda_modern_output": output.model_dump(),
            "modern_representation": output.modern_representation.model_dump(),
            "ayurvedic_representation": output.ayurvedic_representation.model_dump(),
            "correspondence_summary": output.correspondence.model_dump(),
            "representation_status": output.representation_status.value,
            "ayurveda_safety_notes": safety_notes,
        }

    except Exception as e:
        error_msg = f"Phase 7 dual representation failed: {str(e)}"
        return {
            "ayurveda_modern_output": None,
            "modern_representation": None,
            "ayurvedic_representation": None,
            "correspondence_summary": None,
            "representation_status": "insufficient_information",
            "ayurveda_safety_notes": [
                error_msg,
                "Physician clinical review required.",
            ],
        }
