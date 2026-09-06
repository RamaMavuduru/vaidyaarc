"""
Phase 12: Deterministic Dashavidha Atura Pariksha Engine.

Evaluates and structures patient observations across the 10 classical parameters
of Dashavidha Atura Pariksha according to Charaka Samhita, Vimana Sthana 8/94.

Enforces strict epistemic boundaries:
- Patient Observation != Structured Modern Fact != Formal Assessment != Diagnosis
- 3-tier status model: explicitly_reported, structurally_extracted, not_assessed
- Zero LLM, 100% deterministic rule-based execution
- Complete preservation of upstream safety (Phase 2A, 2B, 10)
"""

from typing import Any, Optional

from app.dashavidha_schema import (
    EpistemicStatus,
    DashavidhaParameterRecord,
    DashavidhaAturaParikshaProfileDTO,
    Phase12DashavidhaOutputDTO,
)


def _clean_str(val: Any) -> Optional[str]:
    """Helper to sanitize string inputs."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _get_patient_profile(state: dict[str, Any]) -> dict[str, Any]:
    """Helper to extract patient_profile dictionary safely."""
    prof = state.get("patient_profile")
    return prof if isinstance(prof, dict) else {}


def evaluate_prakriti(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 1: Prakriti (Natural Constitution).
    Reference: Charaka Samhita, Vimana Sthana 8/95.
    Must remain not_assessed unless patient explicitly reports a prior formal assessment.
    """
    prof = _get_patient_profile(state)
    reported_prakriti = _clean_str(state.get("reported_prakriti")) or _clean_str(prof.get("reported_prakriti"))

    if reported_prakriti:
        return DashavidhaParameterRecord(
            parameter_id="param_01_prakriti",
            sanskrit_name="Prakriti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/95",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Prakriti assessment: {reported_prakriti}"],
            prior_formal_assessment={"reported_prakriti": reported_prakriti, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Prakriti recorded strictly from patient's explicit report of a previous clinical assessment. System does not independently determine or verify constitution."],
            assessment_note=f"Preserving patient-reported prior formal Prakriti assessment ({reported_prakriti}). System performs zero independent constitution prediction.",
            provenance_sources=["patient_profile.reported_prakriti"],
        )

    return DashavidhaParameterRecord(
        parameter_id="param_01_prakriti",
        sanskrit_name="Prakriti",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/95",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=[
            "Prakriti determination requires comprehensive physical, physiological, and behavioral examination by a qualified Ayurvedic physician.",
            "Prakriti is strictly not predicted from acute symptoms, body weight, BMI, food preferences, personality traits, or biomarkers.",
        ],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_vikriti(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 2: Vikriti (Pathological Morbidity / Alteration).
    Reference: Charaka Samhita, Vimana Sthana 8/101.
    Preserves current symptom observations; formal Vikriti assessment remains not_assessed.
    """
    prof = _get_patient_profile(state)
    prior_vikriti = _clean_str(state.get("reported_vikriti")) or _clean_str(prof.get("reported_vikriti"))

    if prior_vikriti:
        return DashavidhaParameterRecord(
            parameter_id="param_02_vikriti",
            sanskrit_name="Vikriti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/101",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Vikriti assessment: {prior_vikriti}"],
            prior_formal_assessment={"reported_vikriti": prior_vikriti, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Vikriti recorded strictly from patient's explicit report. System does not independently evaluate morbidity."],
            assessment_note=f"Preserving patient-reported prior formal Vikriti assessment ({prior_vikriti}).",
            provenance_sources=["patient_profile.reported_vikriti"],
        )

    # Compile observed features
    observed_features: list[str] = []
    provenance_sources: list[str] = []

    cc = _clean_str(state.get("chief_complaint"))
    if cc:
        observed_features.append(f"Chief complaint: {cc}")
        provenance_sources.append("intake.chief_complaint")

    pain = _clean_str(state.get("nature_of_pain"))
    if pain:
        observed_features.append(f"Pain character: {pain}")
        provenance_sources.append("intake.nature_of_pain")

    assoc = state.get("associated_symptoms")
    if isinstance(assoc, list) and assoc:
        for s in assoc:
            s_clean = _clean_str(s)
            if s_clean:
                observed_features.append(f"Associated symptom: {s_clean}")
        if any(_clean_str(s) for s in assoc):
            provenance_sources.append("intake.associated_symptoms")

    # Phase 7 descriptive concepts if present
    p7 = state.get("ayurveda_modern_output") or state.get("ayurvedic_representation")
    if isinstance(p7, dict):
        mapped = p7.get("mapped_concepts")
        if isinstance(mapped, list):
            for m in mapped:
                if isinstance(m, dict) and m.get("sanskrit_name"):
                    observed_features.append(f"Phase 7 descriptive descriptor: {m.get('sanskrit_name')} ({m.get('english_descriptor')})")
            if mapped:
                provenance_sources.append("phase7.ayurvedic_representation.mapped_concepts")

    # Phase 9 longitudinal recurrence if present
    long_ctx = state.get("longitudinal_context")
    if isinstance(long_ctx, dict):
        rec = long_ctx.get("recurrent_problems")
        if isinstance(rec, list) and rec:
            for r in rec:
                if isinstance(r, dict) and r.get("label"):
                    observed_features.append(f"Longitudinal recurrent problem: {r.get('label')}")
            provenance_sources.append("phase9.longitudinal_context.recurrent_problems")

    if observed_features:
        return DashavidhaParameterRecord(
            parameter_id="param_02_vikriti",
            sanskrit_name="Vikriti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/101",
            status=EpistemicStatus.NOT_ASSESSED,
            reported_observations=observed_features,
            structured_findings={"observed_current_features": observed_features, "formal_assessment": "not_assessed"},
            prior_formal_assessment=None,
            clinical_limitations=[
                "Observed symptoms and Phase 7 descriptive concepts are recorded as non-diagnostic patient observations.",
                "Formal Doshic morbidity categorizations and specific Ayurvedic classical disease classifications are strictly not generated.",
            ],
            assessment_note="Current symptomatic presentations documented as descriptive observations. Formal Vikriti assessment is not assessed.",
            provenance_sources=list(dict.fromkeys(provenance_sources)),
        )

    return DashavidhaParameterRecord(
        parameter_id="param_02_vikriti",
        sanskrit_name="Vikriti",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/101",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No acute symptomatic complaints documented."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_sara(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 3: Sara (Tissue Excellence / Dhatu Integrity).
    Reference: Charaka Samhita, Vimana Sthana 8/102-109.
    Must remain not_assessed unless explicit prior formal assessment is reported.
    """
    prof = _get_patient_profile(state)
    prior_sara = _clean_str(state.get("reported_sara")) or _clean_str(prof.get("reported_sara"))

    if prior_sara:
        return DashavidhaParameterRecord(
            parameter_id="param_03_sara",
            sanskrit_name="Sara",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/102-109",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Sara assessment: {prior_sara}"],
            prior_formal_assessment={"reported_sara": prior_sara, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Sara recorded strictly from patient's explicit report of a previous assessment."],
            assessment_note=f"Preserving patient-reported prior formal Sara assessment ({prior_sara}).",
            provenance_sources=["patient_profile.reported_sara"],
        )

    return DashavidhaParameterRecord(
        parameter_id="param_03_sara",
        sanskrit_name="Sara",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/102-109",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=[
            "Eight-fold Sara (tissue excellence) grading requires in-person physical inspection and palpation of tissue luster, muscle tone, and bone integrity.",
            "Sara is strictly not inferred from laboratory biomarkers (e.g. hemoglobin), blood tests, skin symptoms, hair, nails, or body weight.",
        ],
        assessment_note="Formal Sara grading requires in-person clinical examination by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_samhanana(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 4: Samhanana (Compactness / Musculoskeletal Symmetry).
    Reference: Charaka Samhita, Vimana Sthana 8/110.
    Must remain not_assessed unless explicit prior formal assessment is reported.
    """
    prof = _get_patient_profile(state)
    prior_samhanana = _clean_str(state.get("reported_samhanana")) or _clean_str(prof.get("reported_samhanana"))

    if prior_samhanana:
        return DashavidhaParameterRecord(
            parameter_id="param_04_samhanana",
            sanskrit_name="Samhanana",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/110",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Samhanana assessment: {prior_samhanana}"],
            prior_formal_assessment={"reported_samhanana": prior_samhanana, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Samhanana recorded strictly from patient's explicit report."],
            assessment_note=f"Preserving patient-reported prior formal Samhanana assessment ({prior_samhanana}).",
            provenance_sources=["patient_profile.reported_samhanana"],
        )

    return DashavidhaParameterRecord(
        parameter_id="param_04_samhanana",
        sanskrit_name="Samhanana",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/110",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=[
            "Samhanana (body compactness and musculoskeletal symmetry) requires physical clinical palpation of joints and bone articulation.",
            "Modern height, weight, and BMI measurements are not converted into classical Samhanana grades.",
        ],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_pramana(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 5: Pramana (Anthropometric Measurements).
    Reference: Charaka Samhita, Vimana Sthana 8/111-117.
    Preserves modern measurements as modern facts; classical Pramana assessment is not_assessed.
    """
    prof = _get_patient_profile(state)
    vitals = state.get("vitals") if isinstance(state.get("vitals"), dict) else prof.get("vitals")

    modern_measurements: dict[str, Any] = {}
    if isinstance(vitals, dict):
        if vitals.get("height") is not None:
            modern_measurements["height"] = vitals["height"]
        if vitals.get("weight") is not None:
            modern_measurements["weight"] = vitals["weight"]
        if vitals.get("bmi") is not None:
            modern_measurements["bmi"] = vitals["bmi"]

    if modern_measurements:
        obs_lines = [f"Modern anthropometric measurement: {k}={v}" for k, v in modern_measurements.items()]
        return DashavidhaParameterRecord(
            parameter_id="param_05_pramana",
            sanskrit_name="Pramana",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/111-117",
            status=EpistemicStatus.STRUCTURALLY_EXTRACTED,
            reported_observations=obs_lines,
            structured_findings={
                "modern_measurements": modern_measurements,
                "classical_pramana_assessment": "not_assessed",
            },
            prior_formal_assessment=None,
            clinical_limitations=[
                "Modern measurements (height, weight, BMI) are preserved as objective modern clinical facts only.",
                "Modern measurements are NOT converted into classical Pramana grades or claimed to be equivalent to classical Anguli or Anjali measurements.",
                "Classical Pramana assessment is not assessed.",
            ],
            assessment_note="Modern body measurements documented. Classical Pramana assessment remains not_assessed without specialized physical measurements.",
            provenance_sources=["patient_profile.vitals"],
        )

    return DashavidhaParameterRecord(
        parameter_id="param_05_pramana",
        sanskrit_name="Pramana",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/111-117",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No modern anthropometric measurements documented in patient profile."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_satmya(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 6: Satmya (Habituation / Adaptability).
    Reference: Charaka Samhita, Vimana Sthana 8/118.
    Preserves reported diet and intolerance observations; formal Satmya grading is not_assessed.
    """
    prof = _get_patient_profile(state)
    prior_satmya = _clean_str(state.get("reported_satmya")) or _clean_str(prof.get("reported_satmya"))

    if prior_satmya:
        return DashavidhaParameterRecord(
            parameter_id="param_06_satmya",
            sanskrit_name="Satmya",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/118",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Satmya assessment: {prior_satmya}"],
            prior_formal_assessment={"reported_satmya": prior_satmya, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Satmya recorded strictly from patient's explicit report."],
            assessment_note=f"Preserving patient-reported prior formal Satmya assessment ({prior_satmya}).",
            provenance_sources=["patient_profile.reported_satmya"],
        )

    reported_observations: list[str] = []
    provenance_sources: list[str] = []
    structured_findings: dict[str, Any] = {}

    diet = _clean_str(state.get("dietary_habits")) or _clean_str(prof.get("dietary_habits"))
    if diet:
        reported_observations.append(f"Reported dietary habits/foods: {diet}")
        structured_findings["dietary_habits"] = diet
        provenance_sources.append("patient_profile.dietary_habits")

    allergies = state.get("allergies") or prof.get("allergies")
    if isinstance(allergies, list) and allergies:
        valid_allergies = [_clean_str(a) for a in allergies if _clean_str(a)]
        if valid_allergies:
            reported_observations.append(f"Reported substance/food allergies or intolerances: {', '.join(valid_allergies)}")
            structured_findings["reported_allergies"] = valid_allergies
            provenance_sources.append("intake.allergies")

    if reported_observations:
        structured_findings["formal_satmya_assessment"] = "not_assessed"
        return DashavidhaParameterRecord(
            parameter_id="param_06_satmya",
            sanskrit_name="Satmya",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/118",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=reported_observations,
            structured_findings=structured_findings,
            prior_formal_assessment=None,
            clinical_limitations=[
                "Patient-reported dietary habits and substance intolerances are recorded as factual history.",
                "Modern drug/food allergies (such as penicillin allergy) are not equated to classical constitutional unsuitability, and formal Satmya adaptability grading is not assigned.",
            ],
            assessment_note="Reported dietary habits and intolerances preserved. Formal Satmya adaptability grading remains not_assessed.",
            provenance_sources=list(dict.fromkeys(provenance_sources)),
        )

    return DashavidhaParameterRecord(
        parameter_id="param_06_satmya",
        sanskrit_name="Satmya",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/118",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No dietary habits, habitual foods, or substance tolerances documented in intake."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_sattva(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 7: Sattva (Psychic Endurance / Mental Strength).
    Reference: Charaka Samhita, Vimana Sthana 8/119.
    Preserves reported emotional experiences; formal Sattva grading is not_assessed.
    """
    prof = _get_patient_profile(state)
    prior_sattva = _clean_str(state.get("reported_sattva")) or _clean_str(prof.get("reported_sattva"))

    if prior_sattva:
        return DashavidhaParameterRecord(
            parameter_id="param_07_sattva",
            sanskrit_name="Sattva",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/119",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Sattva assessment: {prior_sattva}"],
            prior_formal_assessment={"reported_sattva": prior_sattva, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Sattva recorded strictly from patient's explicit report."],
            assessment_note=f"Preserving patient-reported prior formal Sattva assessment ({prior_sattva}).",
            provenance_sources=["patient_profile.reported_sattva"],
        )

    reported_observations: list[str] = []
    provenance_sources: list[str] = []

    # Check for emotional/psychological observations in symptoms or social history
    assoc = state.get("associated_symptoms") or []
    if isinstance(assoc, list):
        for s in assoc:
            s_clean = str(s).lower()
            if any(w in s_clean for w in ["anxiety", "stress", "depression", "fear", "distress", "insomnia", "sleeplessness", "panic", "worry"]):
                reported_observations.append(f"Patient-reported emotional/sleep observation: {s}")
                provenance_sources.append("intake.associated_symptoms")

    soc = _clean_str(state.get("social_history")) or _clean_str(prof.get("social_history"))
    if soc and any(w in soc.lower() for w in ["stress", "anxiety", "distress", "mood", "sleep"]):
        reported_observations.append(f"Social history observation: {soc}")
        provenance_sources.append("patient_profile.social_history")

    if reported_observations:
        return DashavidhaParameterRecord(
            parameter_id="param_07_sattva",
            sanskrit_name="Sattva",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/119",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=reported_observations,
            structured_findings={"reported_emotional_observations": reported_observations, "formal_sattva_assessment": "not_assessed"},
            prior_formal_assessment=None,
            clinical_limitations=[
                "Patient-reported emotional state and coping distress are recorded as descriptive observations.",
                "Anxiety, depression, insomnia, or high pain severity scores are strictly not converted into mental endurance classifications or psychiatric diagnoses.",
            ],
            assessment_note="Reported emotional observations documented. Formal Sattva grading (Pravara/Madhyama/Avara) remains not_assessed without qualified clinical assessment.",
            provenance_sources=list(dict.fromkeys(provenance_sources)),
        )

    return DashavidhaParameterRecord(
        parameter_id="param_07_sattva",
        sanskrit_name="Sattva",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/119",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No psychological or emotional observations documented in intake."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_ahara_shakti(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 8: Ahara Shakti (Ingestion and Digestive Power).
    Reference: Charaka Samhita, Vimana Sthana 8/120.
    Preserves appetite and digestive observations; formal Ahara Shakti grading is not_assessed.
    """
    prof = _get_patient_profile(state)
    prior_ahara = _clean_str(state.get("reported_ahara_shakti")) or _clean_str(prof.get("reported_ahara_shakti"))

    if prior_ahara:
        return DashavidhaParameterRecord(
            parameter_id="param_08_ahara_shakti",
            sanskrit_name="Ahara Shakti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/120",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Ahara Shakti assessment: {prior_ahara}"],
            prior_formal_assessment={"reported_ahara_shakti": prior_ahara, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Ahara Shakti recorded strictly from patient's explicit report."],
            assessment_note=f"Preserving patient-reported prior formal Ahara Shakti assessment ({prior_ahara}).",
            provenance_sources=["patient_profile.reported_ahara_shakti"],
        )

    reported_observations: list[str] = []
    provenance_sources: list[str] = []

    # Check for appetite / digestion symptoms
    assoc = state.get("associated_symptoms") or []
    if isinstance(assoc, list):
        for s in assoc:
            s_clean = str(s).lower()
            if any(w in s_clean for w in ["appetite", "bloating", "digestion", "indigestion", "reflux", "heartburn", "nausea", "acidity", "fullness"]):
                reported_observations.append(f"Reported appetite/digestive observation: {s}")
                provenance_sources.append("intake.associated_symptoms")

    cc = _clean_str(state.get("chief_complaint"))
    if cc and any(w in cc.lower() for w in ["appetite", "bloating", "digestion", "indigestion", "reflux", "stomach", "acidity"]):
        reported_observations.append(f"Chief complaint digestive observation: {cc}")
        provenance_sources.append("intake.chief_complaint")

    if reported_observations:
        return DashavidhaParameterRecord(
            parameter_id="param_08_ahara_shakti",
            sanskrit_name="Ahara Shakti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/120",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=reported_observations,
            structured_findings={"reported_appetite_observations": reported_observations, "formal_ahara_shakti_assessment": "not_assessed"},
            prior_formal_assessment=None,
            clinical_limitations=[
                "Reported appetite and post-prandial symptoms are preserved as patient observations.",
                "They are strictly not converted into formal digestive power grades or clinical metabolic classifications.",
            ],
            assessment_note="Reported ingestion and digestion experience documented. Formal Abhyavaharana and Jarana Shakti grading remains not_assessed.",
            provenance_sources=list(dict.fromkeys(provenance_sources)),
        )

    return DashavidhaParameterRecord(
        parameter_id="param_08_ahara_shakti",
        sanskrit_name="Ahara Shakti",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/120",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No appetite or digestive power observations documented in intake."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_vyayama_shakti(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 9: Vyayama Shakti (Physical Work Capacity).
    Reference: Charaka Samhita, Vimana Sthana 8/121.
    Preserves functional exertion reports; formal Vyayama Shakti grading is not_assessed.
    """
    prof = _get_patient_profile(state)
    prior_vyayama = _clean_str(state.get("reported_vyayama_shakti")) or _clean_str(prof.get("reported_vyayama_shakti"))

    if prior_vyayama:
        return DashavidhaParameterRecord(
            parameter_id="param_09_vyayama_shakti",
            sanskrit_name="Vyayama Shakti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/121",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=[f"Patient explicitly reports prior formal Vyayama Shakti assessment: {prior_vyayama}"],
            prior_formal_assessment={"reported_vyayama_shakti": prior_vyayama, "source": "patient_reported_prior_assessment"},
            clinical_limitations=["Vyayama Shakti recorded strictly from patient's explicit report."],
            assessment_note=f"Preserving patient-reported prior formal Vyayama Shakti assessment ({prior_vyayama}).",
            provenance_sources=["patient_profile.reported_vyayama_shakti"],
        )

    reported_observations: list[str] = []
    provenance_sources: list[str] = []

    assoc = state.get("associated_symptoms") or []
    if isinstance(assoc, list):
        for s in assoc:
            s_clean = str(s).lower()
            if any(w in s_clean for w in ["fatigue", "tired", "weakness", "exhaustion", "walking", "stairs", "exertion", "breathless on walking"]):
                reported_observations.append(f"Patient-reported physical exertion observation: {s}")
                provenance_sources.append("intake.associated_symptoms")

    func = _clean_str(state.get("functional_status")) or _clean_str(prof.get("functional_status"))
    if func:
        reported_observations.append(f"Functional activity observation: {func}")
        provenance_sources.append("patient_profile.functional_status")

    if reported_observations:
        return DashavidhaParameterRecord(
            parameter_id="param_09_vyayama_shakti",
            sanskrit_name="Vyayama Shakti",
            framework_reference="Charaka Samhita, Vimana Sthana 8/94",
            parameter_reference="Charaka Samhita, Vimana Sthana 8/121",
            status=EpistemicStatus.EXPLICITLY_REPORTED,
            reported_observations=reported_observations,
            structured_findings={"reported_exertion_observations": reported_observations, "formal_vyayama_shakti_assessment": "not_assessed"},
            prior_formal_assessment=None,
            clinical_limitations=[
                "Patient-reported exercise and exertional limitations are recorded descriptively.",
                "Formal physical work capacity grading is strictly not inferred from laboratory biomarkers (e.g. hemoglobin, ESR), heart rate alone, risk scores, or disease labels.",
            ],
            assessment_note="Reported functional exertion observations documented. Formal Vyayama Shakti grading remains not_assessed without clinical evaluation.",
            provenance_sources=list(dict.fromkeys(provenance_sources)),
        )

    return DashavidhaParameterRecord(
        parameter_id="param_09_vyayama_shakti",
        sanskrit_name="Vyayama Shakti",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/121",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["No physical exercise, walking ability, or exertional capacity observations documented in intake."],
        assessment_note="Requires in-person clinical assessment by a qualified Ayurvedic physician.",
        provenance_sources=[],
    )


def evaluate_vaya(state: dict[str, Any]) -> DashavidhaParameterRecord:
    """
    Evaluates Parameter 10: Vaya (Chronological Life Stage / Age).
    Reference: Charaka Samhita, Vimana Sthana 8/122.
    Deterministically extracts chronological age stage based on verified Charaka thresholds:
    - Balyavastha: age <= 16 (Growth stage, Kapha predominant)
    - Madhyamavastha: 17 <= age <= 60 (Maturity stage, Pitta predominant)
    - Vriddhavastha: age > 60 (Senescence stage, Vata predominant)
    """
    prof = _get_patient_profile(state)
    age_val = state.get("age")
    if age_val is None:
        age_val = prof.get("age")

    if age_val is not None:
        try:
            age_num = float(age_val)
            if age_num >= 0:
                if age_num <= 16:
                    stage = "Balyavastha (Childhood / Growth stage, predominantly Kapha)"
                elif age_num <= 60:
                    stage = "Madhyamavastha (Middle age / Maturity stage, predominantly Pitta)"
                else:
                    stage = "Vriddhavastha (Old age / Senescence stage, predominantly Vata)"

                return DashavidhaParameterRecord(
                    parameter_id="param_10_vaya",
                    sanskrit_name="Vaya",
                    framework_reference="Charaka Samhita, Vimana Sthana 8/94",
                    parameter_reference="Charaka Samhita, Vimana Sthana 8/122",
                    status=EpistemicStatus.STRUCTURALLY_EXTRACTED,
                    reported_observations=[f"Chronological age: {int(age_num) if age_num.is_integer() else age_num} years"],
                    structured_findings={
                        "chronological_age": int(age_num) if age_num.is_integer() else age_num,
                        "classical_life_stage": stage,
                    },
                    prior_formal_assessment=None,
                    clinical_limitations=[
                        "Chronological age mapping based on verified Charaka Samhita life stage definitions (Vimana Sthana 8/122). Physiological aging rate is not independently assessed.",
                    ],
                    assessment_note=f"Chronologically categorized as {stage} based on verified age ({int(age_num) if age_num.is_integer() else age_num} years).",
                    provenance_sources=["patient_profile.age"],
                )
        except (ValueError, TypeError):
            pass

    return DashavidhaParameterRecord(
        parameter_id="param_10_vaya",
        sanskrit_name="Vaya",
        framework_reference="Charaka Samhita, Vimana Sthana 8/94",
        parameter_reference="Charaka Samhita, Vimana Sthana 8/122",
        status=EpistemicStatus.NOT_ASSESSED,
        reported_observations=[],
        structured_findings=None,
        prior_formal_assessment=None,
        clinical_limitations=["Chronological age not documented in patient profile."],
        assessment_note="Patient age not documented in intake data.",
        provenance_sources=[],
    )


def evaluate_dashavidha_atura_pariksha(state: dict[str, Any]) -> Phase12DashavidhaOutputDTO:
    """
    Main deterministic entry point for Phase 12: Dashavidha Atura Pariksha.

    Evaluates all 10 classical parameters strictly according to Charaka Samhita Vimana Sthana 8/94,
    preserves upstream safety (Phase 2A, Phase 2B, Phase 10), and produces an auditable,
    provenance-preserving representation.
    """
    p1 = evaluate_prakriti(state)
    p2 = evaluate_vikriti(state)
    p3 = evaluate_sara(state)
    p4 = evaluate_samhanana(state)
    p5 = evaluate_pramana(state)
    p6 = evaluate_satmya(state)
    p7 = evaluate_sattva(state)
    p8 = evaluate_ahara_shakti(state)
    p9 = evaluate_vyayama_shakti(state)
    p10 = evaluate_vaya(state)

    all_params = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]

    # Calculate precise parameter metrics
    obs_count = sum(1 for p in all_params if len(p.reported_observations) > 0 or p.structured_findings is not None)
    assessed_count = sum(1 for p in all_params if p.prior_formal_assessment is not None or (p.parameter_id == "param_10_vaya" and p.status == EpistemicStatus.STRUCTURALLY_EXTRACTED))
    not_assessed_count = sum(1 for p in all_params if p.status == EpistemicStatus.NOT_ASSESSED)

    # Narrative synthesis
    narrative_lines = [
        f"Phase 12 Dashavidha Atura Pariksha profile generated with {obs_count}/10 parameters containing descriptive observations or modern measurements.",
        f"Formal qualified Ayurvedic assessment count: {assessed_count}/10. Parameters remaining not assessed: {not_assessed_count}/10.",
    ]
    if p10.status == EpistemicStatus.STRUCTURALLY_EXTRACTED and p10.structured_findings:
        narrative_lines.append(f"Vaya (Age): {p10.structured_findings.get('classical_life_stage')}.")
    if p1.status == EpistemicStatus.EXPLICITLY_REPORTED and p1.prior_formal_assessment:
        narrative_lines.append(f"Prakriti: Patient-reported prior assessment preserved ({p1.prior_formal_assessment.get('reported_prakriti')}).")
    else:
        narrative_lines.append("Prakriti: Not assessed (requires qualified in-person examination).")

    summary_narrative = " ".join(narrative_lines)

    # Safety Context Preservation
    safety_context = {
        "red_flag_status": state.get("red_flag_status"),
        "immediate_attention_required": state.get("immediate_attention_required", False),
        "red_flags": state.get("red_flags") or [],
        "risk_level": state.get("risk_level"),
        "risk_score": state.get("risk_score"),
        "advanced_risk_assessment_present": state.get("advanced_risk_output") is not None or state.get("advanced_risk_assessment") is not None,
        "safety_preservation_note": "Safety findings and risk assessments preserved immutably. Not transformed into Ayurvedic diagnostic classifications.",
    }

    provenance_notes = [
        "Phase 12 deterministic Dashavidha Atura Pariksha representation engine (app/dashavidha_engine.py)",
        "Charaka Samhita, Vimana Sthana 8/94 tenfold clinical examination framework",
        "Strict 3-tier epistemic status model (explicitly_reported, structurally_extracted, not_assessed)",
        "Zero-diagnostic and non-prescriptive safety invariants enforced",
        "Upstream Phase 2A, 2B, and 10 safety immutability preserved",
    ]

    profile_dto = DashavidhaAturaParikshaProfileDTO(
        prakriti=p1,
        vikriti=p2,
        sara=p3,
        samhanana=p4,
        pramana=p5,
        satmya=p6,
        sattva=p7,
        ahara_shakti=p8,
        vyayama_shakti=p9,
        vaya=p10,
        parameters_with_observations_count=obs_count,
        parameters_formally_assessed_count=assessed_count,
        parameters_not_assessed_count=not_assessed_count,
        summary_narrative=summary_narrative,
        safety_context=safety_context,
        provenance_notes=provenance_notes,
    )

    return Phase12DashavidhaOutputDTO(
        dashavidha_atura_pariksha=profile_dto,
        safety_context=safety_context,
        provenance_notes=provenance_notes,
    )
