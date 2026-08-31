from __future__ import annotations

from typing import Any


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_as_text(item) for item in value if item is not None)
    return str(value).strip()


def _normalize(text: str) -> str:
    return _as_text(text).lower().strip()


def _contains_any(text: str, phrases: list[str]) -> bool:
    normalized = _normalize(text)
    return any(phrase.lower() in normalized for phrase in phrases)


def _collect_relevant_text(state: dict[str, Any]) -> str:
    parts: list[str] = []

    for field in [
        "chief_complaint",
        "nature_of_pain",
        "location",
        "duration",
        "severity",
    ]:
        value = state.get(field)
        if value is not None:
            parts.append(_as_text(value))

    for item in state.get("associated_symptoms") or []:
        if item is not None:
            parts.append(_as_text(item))

    message = state.get("current_message")
    if message:
        parts.append(_as_text(message))

    return " ".join(part for part in parts if part)


def _make_hit(rule_id: str, label: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "label": label,
        "evidence": evidence,
    }


def evaluate_red_flags(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("information_complete"):
        return {
            "red_flag_status": "insufficient_information",
            "red_flags": [],
            "red_flag_evidence": [],
            "immediate_attention_required": False,
            "red_flag_rule_hits": [],
        }

    combined_text = _collect_relevant_text(state)
    red_flags: list[str] = []
    evidence: list[str] = []
    rule_hits: list[dict[str, Any]] = []

    if _contains_any(combined_text, [
        "difficulty breathing",
        "trouble breathing",
        "shortness of breath",
        "can't breathe",
        "cannot breathe",
        "struggling to breathe",
        "breathless",
        "unable to breathe",
    ]):
        red_flags.append("difficulty breathing")
        evidence.append("difficulty breathing")
        rule_hits.append(_make_hit("difficulty_breathing", "Difficulty breathing", ["difficulty breathing"]))

    if _contains_any(combined_text, [
        "fainted",
        "passed out",
        "loss of consciousness",
        "unconscious",
        "blackout",
        "syncope",
        "fell unconscious",
    ]):
        red_flags.append("fainting or loss of consciousness")
        evidence.append("fainting or loss of consciousness")
        rule_hits.append(_make_hit("fainting_loss_of_consciousness", "Fainting or loss of consciousness", ["fainting or loss of consciousness"]))

    chest_text = combined_text
    if _contains_any(chest_text, ["chest pain", "pain in chest"]) and _contains_any(chest_text, [
        "severe",
        "very severe",
        "excruciating",
        "worst pain",
        "sudden severe",
    ]):
        red_flags.append("severe chest pain")
        evidence.append("severe chest pain")
        rule_hits.append(_make_hit("severe_chest_pain", "Severe chest pain", ["severe chest pain"]))

    if _contains_any(combined_text, [
        "uncontrolled bleeding",
        "major bleeding",
        "bleeding heavily",
        "bleeding a lot",
        "heavy bleeding",
        "severe bleeding",
    ]) or (
        _contains_any(combined_text, ["bleeding", "bleed"]) and _contains_any(combined_text, [
            "heavy",
            "lots of",
            "major",
            "uncontrolled",
        ])
    ):
        red_flags.append("uncontrolled or major bleeding")
        evidence.append("uncontrolled or major bleeding")
        rule_hits.append(_make_hit("uncontrolled_major_bleeding", "Uncontrolled or major bleeding", ["uncontrolled or major bleeding"]))

    if _contains_any(combined_text, [
        "vomiting blood",
        "throwing up blood",
        "blood in vomit",
        "bloody vomit",
        "vomit blood",
    ]):
        red_flags.append("vomiting blood")
        evidence.append("vomiting blood")
        rule_hits.append(_make_hit("vomiting_blood", "Vomiting blood", ["vomiting blood"]))

    if _contains_any(combined_text, [
        "black stool",
        "black stools",
        "bloody stool",
        "bloody stools",
        "blood in stool",
        "blood in my stool",
        "blood in the stool",
    ]):
        red_flags.append("black or bloody stools")
        evidence.append("black or bloody stools")
        rule_hits.append(_make_hit("black_or_bloody_stools", "Black or bloody stools", ["black or bloody stools"]))

    if _contains_any(combined_text, [
        "sudden weakness",
        "one sided weakness",
        "one-sided weakness",
        "slurred speech",
        "facial droop",
        "sudden confusion",
        "sudden numbness",
        "sudden severe headache",
        "seizure",
    ]):
        red_flags.append("sudden severe neurological symptoms")
        evidence.append("sudden severe neurological symptoms")
        rule_hits.append(_make_hit("sudden_severe_neurological_symptoms", "Sudden severe neurological symptoms", ["sudden severe neurological symptoms"]))

    if _contains_any(combined_text, [
        "rapidly worsening",
        "worsening quickly",
        "getting worse quickly",
        "suddenly worse",
        "very rapidly worsening",
    ]) and _contains_any(combined_text, [
        "severe",
        "very severe",
        "worst pain",
        "excruciating",
    ]):
        red_flags.append("rapidly worsening severe symptoms")
        evidence.append("rapidly worsening severe symptoms")
        rule_hits.append(_make_hit("rapidly_worsening_severe_symptoms", "Rapidly worsening severe symptoms", ["rapidly worsening severe symptoms"]))

    severe_abdominal = (
        _contains_any(combined_text, [
            "severe abdominal pain",
            "severe stomach pain",
            "abdominal pain",
            "stomach pain",
            "pain in my abdomen",
            "pain in my stomach",
            "upper abdomen",
        ])
        and _contains_any(combined_text, [
            "severe",
            "very severe",
            "excruciating",
            "worst pain",
        ])
        and (
            _contains_any(combined_text, [
                "vomiting",
                "fainting",
                "difficulty breathing",
                "black stool",
                "bloody stool",
                "vomiting blood",
                "blood in stool",
            ])
            or _contains_any(_as_text(state.get("associated_symptoms")), [
                "vomiting",
                "fainting",
                "difficulty breathing",
                "black stool",
                "bloody stool",
                "vomiting blood",
            ])
        )
    )
    if severe_abdominal:
        red_flags.append("severe abdominal pain with concerning associated symptoms")
        evidence.append("severe abdominal pain with concerning associated symptoms")
        rule_hits.append(_make_hit("severe_abdominal_pain_concerning_symptoms", "Severe abdominal pain with concerning associated symptoms", ["severe abdominal pain with concerning associated symptoms"]))

    unique_flags = []
    unique_evidence = []
    seen_flags = set()
    for flag in red_flags:
        if flag not in seen_flags:
            seen_flags.add(flag)
            unique_flags.append(flag)
    for item in evidence:
        if item not in unique_evidence:
            unique_evidence.append(item)

    if unique_flags:
        return {
            "red_flag_status": "red_flags_detected",
            "red_flags": unique_flags,
            "red_flag_evidence": unique_evidence,
            "immediate_attention_required": True,
            "red_flag_rule_hits": rule_hits,
        }

    return {
        "red_flag_status": "no_obvious_red_flags",
        "red_flags": [],
        "red_flag_evidence": [],
        "immediate_attention_required": False,
        "red_flag_rule_hits": [],
    }
