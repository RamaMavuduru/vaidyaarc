"""
Phase 9: Active Problem & Recurrence Registry.

Maintains structured records of active, resolved, recurrent, and unresolved
clinical problems across historical and current encounters.

SAFETY INVARIANTS:
1. 'Missing later' != 'Resolved'. Problems move to resolved ONLY with explicit evidence.
2. Conservative recurrence detection: flags recurrence only across non-consecutive
   encounters or when explicitly noted.
3. 100% Deterministic rule-based processing. ZERO LLM.
"""

import re
from typing import Any, Optional
from app.longitudinal_schema import ProblemRecord, ProblemStatus


def normalize_problem_label(label: str) -> tuple[str, str]:
    """
    Normalizes a problem/symptom/condition string into a canonical key and clean title.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", (label or "").strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # Common medical condition and symptom normalizations
    canonical_map = {
        "headache": ("headache", "Headache"),
        "fever": ("fever", "Fever"),
        "cough": ("cough", "Cough"),
        "chest pain": ("chest_pain", "Chest Pain"),
        "stomach pain": ("abdominal_pain", "Abdominal Pain"),
        "abdominal pain": ("abdominal_pain", "Abdominal Pain"),
        "acidity": ("acidity", "Acidity / Heartburn"),
        "heartburn": ("acidity", "Acidity / Heartburn"),
        "vomiting": ("vomiting", "Vomiting"),
        "nausea": ("nausea", "Nausea"),
        "shortness of breath": ("dyspnea", "Shortness of Breath"),
        "difficulty breathing": ("dyspnea", "Shortness of Breath"),
        "breathlessness": ("dyspnea", "Shortness of Breath"),
        "hypertension": ("hypertension", "Hypertension"),
        "high blood pressure": ("hypertension", "Hypertension"),
        "type 2 diabetes": ("diabetes_type_2", "Type 2 Diabetes Mellitus"),
        "diabetes": ("diabetes_type_2", "Type 2 Diabetes Mellitus"),
        "diabetes mellitus": ("diabetes_type_2", "Type 2 Diabetes Mellitus"),
        "asthma": ("asthma", "Asthma"),
        "osteoarthritis": ("osteoarthritis", "Osteoarthritis"),
        "arthritis": ("arthritis", "Arthritis"),
        "joint pain": ("joint_pain", "Joint Pain"),
        "fatigue": ("fatigue", "Fatigue"),
        "dizziness": ("dizziness", "Dizziness / Giddiness"),
        "giddiness": ("dizziness", "Dizziness / Giddiness"),
        "diarrhea": ("diarrhea", "Diarrhea"),
        "loose stools": ("diarrhea", "Diarrhea"),
        "constipation": ("constipation", "Constipation"),
        "rash": ("skin_rash", "Skin Rash"),
        "skin rash": ("skin_rash", "Skin Rash"),
    }

    if cleaned in canonical_map:
        return canonical_map[cleaned]

    key = re.sub(r"\s+", "_", cleaned)
    display = (label or "Unspecified Problem").strip().title()
    return key, display


def detect_explicit_resolution(text: Optional[str], problem_norm_key: str) -> bool:
    """
    Checks if text contains explicit confirmation of resolution for a problem.
    """
    if not text:
        return False
    t = text.lower()
    
    # Generic resolution patterns
    resolution_keywords = ["resolved", "completely resolved", "cured", "gone", "stopped", "no longer present", "healed"]
    
    # Check if text mentions the problem and a resolution keyword
    if any(kw in t for kw in resolution_keywords):
        key_words = problem_norm_key.replace("_", " ").split()
        if any(w in t for w in key_words if len(w) > 2):
            return True
            
    return False


def build_problem_registry(
    patient_profile: Optional[dict[str, Any]],
    previous_encounters: list[dict[str, Any]],
    current_encounter_state: Optional[dict[str, Any]] = None,
) -> tuple[list[ProblemRecord], list[ProblemRecord], list[ProblemRecord], list[ProblemRecord]]:
    """
    Synthesizes active, resolved, recurrent, and unresolved problem records.
    
    Returns:
    (active_problems, resolved_problems, recurrent_complaints, unresolved_issues)
    """
    # Track problem occurrences across chronological encounters
    # Key: normalized_label -> metadata dict
    problems_map: dict[str, dict[str, Any]] = {}

    # 1. Ingest baseline chronic conditions from patient profile
    profile = patient_profile or {}
    for cond in profile.get("medical_conditions") or []:
        if not cond:
            continue
        norm_key, display = normalize_problem_label(str(cond))
        problems_map[norm_key] = {
            "label": display,
            "norm_key": norm_key,
            "encounter_ids": ["BASELINE_PROFILE"],
            "dates": [],
            "status": "active",
            "is_chronic_baseline": True,
            "episode_indices": [0],
            "resolved_encounter": None,
            "resolution_evidence": None,
            "associated_symptoms": [],
        }

    # 2. Ingest historical encounters chronologically
    # Sort previous encounters by timestamp if available
    def get_enc_date(enc: dict[str, Any]) -> str:
        return enc.get("timestamp") or enc.get("date") or ""

    sorted_encounters = sorted(previous_encounters or [], key=get_enc_date)

    for enc_idx, enc in enumerate(sorted_encounters, start=1):
        enc_id = enc.get("encounter_id") or f"ENC_HIST_{enc_idx:03d}"
        enc_date = enc.get("timestamp") or enc.get("date")
        cc = enc.get("chief_complaint")
        assoc = enc.get("associated_symptoms") or []
        resolved_list = enc.get("resolved_symptoms") or []

        # Process chief complaint
        if cc:
            norm_key, display = normalize_problem_label(str(cc))
            if norm_key not in problems_map:
                problems_map[norm_key] = {
                    "label": display,
                    "norm_key": norm_key,
                    "encounter_ids": [],
                    "dates": [],
                    "status": "active",
                    "is_chronic_baseline": False,
                    "episode_indices": [],
                    "resolved_encounter": None,
                    "resolution_evidence": None,
                    "associated_symptoms": [],
                }
            entry = problems_map[norm_key]
            if enc_id not in entry["encounter_ids"]:
                entry["encounter_ids"].append(enc_id)
            if enc_date and enc_date not in entry["dates"]:
                entry["dates"].append(enc_date)
            entry["episode_indices"].append(enc_idx)
            for s in assoc:
                if s and s not in entry["associated_symptoms"]:
                    entry["associated_symptoms"].append(s)

        # Process associated symptoms as secondary problem entries
        for s in assoc:
            if not s or s == cc:
                continue
            norm_key, display = normalize_problem_label(str(s))
            if norm_key not in problems_map:
                problems_map[norm_key] = {
                    "label": display,
                    "norm_key": norm_key,
                    "encounter_ids": [],
                    "dates": [],
                    "status": "active",
                    "is_chronic_baseline": False,
                    "episode_indices": [],
                    "resolved_encounter": None,
                    "resolution_evidence": None,
                    "associated_symptoms": [],
                }
            entry = problems_map[norm_key]
            if enc_id not in entry["encounter_ids"]:
                entry["encounter_ids"].append(enc_id)
            if enc_date and enc_date not in entry["dates"]:
                entry["dates"].append(enc_date)
            entry["episode_indices"].append(enc_idx)

        # Process explicit resolutions in this encounter
        for res_symptom in resolved_list:
            if not res_symptom:
                continue
            norm_key, _ = normalize_problem_label(str(res_symptom))
            if norm_key in problems_map:
                problems_map[norm_key]["status"] = "resolved"
                problems_map[norm_key]["resolved_encounter"] = enc_id
                problems_map[norm_key]["resolution_evidence"] = f"Explicitly confirmed resolved in {enc_id}"

    # 3. Ingest current encounter state
    curr_enc_id = None
    curr_cc = None
    curr_assoc: list[str] = []
    curr_resolved: list[str] = []
    curr_idx = len(sorted_encounters) + 1

    if current_encounter_state:
        curr_enc_id = current_encounter_state.get("session_id") or current_encounter_state.get("episode_id") or "ENC_CURRENT"
        curr_cc = current_encounter_state.get("chief_complaint")
        curr_assoc = current_encounter_state.get("associated_symptoms") or []
        curr_resolved = current_encounter_state.get("resolved_signals") or []
        curr_date = current_encounter_state.get("evaluated_at") or current_encounter_state.get("date")

        # Chief complaint
        if curr_cc:
            norm_key, display = normalize_problem_label(str(curr_cc))
            if norm_key not in problems_map:
                problems_map[norm_key] = {
                    "label": display,
                    "norm_key": norm_key,
                    "encounter_ids": [],
                    "dates": [],
                    "status": "active",
                    "is_chronic_baseline": False,
                    "episode_indices": [],
                    "resolved_encounter": None,
                    "resolution_evidence": None,
                    "associated_symptoms": [],
                }
            entry = problems_map[norm_key]
            if curr_enc_id not in entry["encounter_ids"]:
                entry["encounter_ids"].append(curr_enc_id)
            if curr_date and curr_date not in entry["dates"]:
                entry["dates"].append(curr_date)
            entry["episode_indices"].append(curr_idx)
            entry["status"] = "active"  # Active in current turn
            for s in curr_assoc:
                if s and s not in entry["associated_symptoms"]:
                    entry["associated_symptoms"].append(s)

        # Associated symptoms
        for s in curr_assoc:
            if not s or s == curr_cc:
                continue
            norm_key, display = normalize_problem_label(str(s))
            if norm_key not in problems_map:
                problems_map[norm_key] = {
                    "label": display,
                    "norm_key": norm_key,
                    "encounter_ids": [],
                    "dates": [],
                    "status": "active",
                    "is_chronic_baseline": False,
                    "episode_indices": [],
                    "resolved_encounter": None,
                    "resolution_evidence": None,
                    "associated_symptoms": [],
                }
            entry = problems_map[norm_key]
            if curr_enc_id not in entry["encounter_ids"]:
                entry["encounter_ids"].append(curr_enc_id)
            if curr_date and curr_date not in entry["dates"]:
                entry["dates"].append(curr_date)
            entry["episode_indices"].append(curr_idx)
            entry["status"] = "active"

        # Explicit resolutions in current turn
        for res_s in curr_resolved:
            norm_key, _ = normalize_problem_label(str(res_s))
            if norm_key in problems_map:
                problems_map[norm_key]["status"] = "resolved"
                problems_map[norm_key]["resolved_encounter"] = curr_enc_id
                problems_map[norm_key]["resolution_evidence"] = f"Explicitly confirmed resolved in current encounter ({curr_enc_id})"

        # Check raw message for explicit resolution assertions (e.g. "fever has resolved")
        msg = current_encounter_state.get("current_message")
        for norm_key, entry in problems_map.items():
            if entry["status"] != "resolved" and detect_explicit_resolution(msg, norm_key):
                entry["status"] = "resolved"
                entry["resolved_encounter"] = curr_enc_id
                entry["resolution_evidence"] = f"Explicit resolution stated in message: '{msg}'"

    # 4. Classify each problem into output buckets
    active_problems: list[ProblemRecord] = []
    resolved_problems: list[ProblemRecord] = []
    recurrent_complaints: list[ProblemRecord] = []
    unresolved_issues: list[ProblemRecord] = []

    for norm_key, entry in problems_map.items():
        first_date = entry["dates"][0] if entry["dates"] else None
        last_date = entry["dates"][-1] if entry["dates"] else None
        ep_indices = entry["episode_indices"]
        episode_count = len(ep_indices)

        # Recurrence detection:
        # A problem is recurrent if it appears in >= 2 distinct non-consecutive encounter indices
        # (e.g. Encounter 1 and Encounter 3, or Encounters 1, 2, 4)
        is_recurrent = False
        if episode_count >= 2:
            # Check for non-consecutive encounter indices
            for i in range(len(ep_indices) - 1):
                if ep_indices[i + 1] - ep_indices[i] > 1:
                    is_recurrent = True
                    break
            # Also if episode count >= 3, flag as recurrent pattern
            if episode_count >= 3:
                is_recurrent = True

        # Determine effective status
        if entry["status"] == "resolved":
            eff_status: ProblemStatus = "resolved"
        elif is_recurrent:
            eff_status = "recurrent"
        elif curr_enc_id and curr_enc_id in entry["encounter_ids"]:
            eff_status = "active"
        elif entry.get("is_chronic_baseline"):
            eff_status = "active"
        else:
            # Historically reported but unmentioned in current encounter (Missing != Resolved)
            eff_status = "unresolved"

        record = ProblemRecord(
            problem_id=f"PROB_{norm_key.upper()}",
            label=entry["label"],
            normalized_label=norm_key,
            status=eff_status,
            first_observed_date=first_date,
            last_observed_date=last_date,
            encounter_ids=entry["encounter_ids"],
            episode_count=episode_count,
            is_recurrent=is_recurrent,
            resolution_evidence=entry.get("resolution_evidence"),
            resolution_encounter_id=entry.get("resolved_encounter"),
            associated_symptoms=entry["associated_symptoms"],
            provenance=f"encounters:{','.join(entry['encounter_ids'])}",
        )

        if eff_status == "resolved":
            resolved_problems.append(record)
        elif eff_status == "active":
            active_problems.append(record)
        elif eff_status == "recurrent":
            recurrent_complaints.append(record)
            # If also active in current encounter, include in active as well
            if curr_enc_id and curr_enc_id in entry["encounter_ids"]:
                active_problems.append(record)
        elif eff_status == "unresolved":
            unresolved_issues.append(record)

    # Sort deterministically
    active_problems = sorted(active_problems, key=lambda p: p.label)
    resolved_problems = sorted(resolved_problems, key=lambda p: p.label)
    recurrent_complaints = sorted(recurrent_complaints, key=lambda p: p.label)
    unresolved_issues = sorted(unresolved_issues, key=lambda p: p.label)

    return active_problems, resolved_problems, recurrent_complaints, unresolved_issues

