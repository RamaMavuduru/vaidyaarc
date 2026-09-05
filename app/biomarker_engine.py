"""
Phase 9: Biomarker Engine & Numerical Trajectory Calculator.

Extracts, normalizes, and calculates purely mathematical time-series trajectories
for laboratory biomarkers without clinical overinterpretation.

SAFETY INVARIANTS:
1. Purely mathematical directional calculations (increasing, decreasing, stable, fluctuating).
2. NEVER infers clinical improvement or worsening from numerical direction.
3. Incompatible units block numeric delta calculations (unit_mismatch=True).
4. Mandatory non-diagnostic disclaimer on all trajectory outputs.
5. ZERO LLM dependencies. 100% Deterministic.
"""

import re
from typing import Any, Optional
from datetime import datetime
from app.longitudinal_schema import BiomarkerRecord, BiomarkerTrajectory, BiomarkerTrajectoryType


# Canonical Lab Test Normalization Mapping
BIOMARKER_ALIASES: dict[str, tuple[str, str]] = {
    # Glycemic
    "hba1c": ("hba1c", "HbA1c"),
    "glycated hemoglobin": ("hba1c", "HbA1c"),
    "a1c": ("hba1c", "HbA1c"),
    "fasting blood glucose": ("fasting_blood_glucose", "Fasting Blood Glucose"),
    "fbg": ("fasting_blood_glucose", "Fasting Blood Glucose"),
    "fasting blood sugar": ("fasting_blood_glucose", "Fasting Blood Glucose"),
    "fbs": ("fasting_blood_glucose", "Fasting Blood Glucose"),
    "postprandial blood glucose": ("postprandial_blood_glucose", "Postprandial Blood Glucose"),
    "ppbg": ("postprandial_blood_glucose", "Postprandial Blood Glucose"),
    "random blood glucose": ("random_blood_glucose", "Random Blood Glucose"),
    "rbg": ("random_blood_glucose", "Random Blood Glucose"),
    "blood glucose": ("blood_glucose", "Blood Glucose"),
    "blood sugar": ("blood_glucose", "Blood Glucose"),

    # Hematology
    "hemoglobin": ("hemoglobin", "Hemoglobin"),
    "hb": ("hemoglobin", "Hemoglobin"),
    "hgb": ("hemoglobin", "Hemoglobin"),
    "platelets": ("platelets", "Platelet Count"),
    "platelet count": ("platelets", "Platelet Count"),
    "plt": ("platelets", "Platelet Count"),
    "white blood cells": ("wbc", "White Blood Cell Count"),
    "wbc": ("wbc", "White Blood Cell Count"),
    "total leukocyte count": ("wbc", "White Blood Cell Count"),
    "tlc": ("wbc", "White Blood Cell Count"),

    # Renal & Electrolytes
    "serum creatinine": ("serum_creatinine", "Serum Creatinine"),
    "creatinine": ("serum_creatinine", "Serum Creatinine"),
    "blood urea nitrogen": ("blood_urea_nitrogen", "Blood Urea Nitrogen"),
    "bun": ("blood_urea_nitrogen", "Blood Urea Nitrogen"),
    "serum uric acid": ("uric_acid", "Serum Uric Acid"),
    "uric acid": ("uric_acid", "Serum Uric Acid"),

    # Hepatic & Lipids
    "total cholesterol": ("total_cholesterol", "Total Cholesterol"),
    "cholesterol": ("total_cholesterol", "Total Cholesterol"),
    "triglycerides": ("triglycerides", "Triglycerides"),
    "tg": ("triglycerides", "Triglycerides"),
    "hdl": ("hdl_cholesterol", "HDL Cholesterol"),
    "hdl cholesterol": ("hdl_cholesterol", "HDL Cholesterol"),
    "ldl": ("ldl_cholesterol", "LDL Cholesterol"),
    "ldl cholesterol": ("ldl_cholesterol", "LDL Cholesterol"),
    "sgot": ("ast", "AST / SGOT"),
    "ast": ("ast", "AST / SGOT"),
    "sgpt": ("alt", "ALT / SGPT"),
    "alt": ("alt", "ALT / SGPT"),
    "bilirubin": ("total_bilirubin", "Total Bilirubin"),
    "total bilirubin": ("total_bilirubin", "Total Bilirubin"),

    # Vitals
    "blood pressure systolic": ("blood_pressure_systolic", "Systolic Blood Pressure"),
    "systolic bp": ("blood_pressure_systolic", "Systolic Blood Pressure"),
    "systolic": ("blood_pressure_systolic", "Systolic Blood Pressure"),
    "blood pressure diastolic": ("blood_pressure_diastolic", "Diastolic Blood Pressure"),
    "diastolic bp": ("blood_pressure_diastolic", "Diastolic Blood Pressure"),
    "diastolic": ("blood_pressure_diastolic", "Diastolic Blood Pressure"),
    "heart rate": ("heart_rate", "Heart Rate"),
    "pulse": ("heart_rate", "Heart Rate"),
    "pulse rate": ("heart_rate", "Heart Rate"),
    "spo2": ("oxygen_saturation", "Oxygen Saturation (SpO2)"),
    "oxygen saturation": ("oxygen_saturation", "Oxygen Saturation (SpO2)"),
    "temperature": ("body_temperature", "Body Temperature"),
    "body temperature": ("body_temperature", "Body Temperature"),
    "weight": ("body_weight", "Body Weight"),
    "body weight": ("body_weight", "Body Weight"),
    "bmi": ("bmi", "Body Mass Index"),
}


def normalize_test_name(raw_name: str) -> tuple[str, str]:
    """
    Normalizes a raw lab test or biomarker string into a canonical key and display name.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", (raw_name or "").strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if cleaned in BIOMARKER_ALIASES:
        return BIOMARKER_ALIASES[cleaned]

    for alias, (norm_key, display) in BIOMARKER_ALIASES.items():
        if alias in cleaned or cleaned in alias:
            return norm_key, display

    key = re.sub(r"\s+", "_", cleaned)
    display = (raw_name or "Unspecified Test").strip().title()
    return key, display


def normalize_unit(raw_unit: Optional[str]) -> str:
    """
    Standardizes laboratory measurement units.
    """
    if not raw_unit:
        return ""
    u = str(raw_unit).strip().lower()
    mapping = {
        "mg/dl": "mg/dL",
        "mg%": "mg/dL",
        "g/dl": "g/dL",
        "gm/dl": "g/dL",
        "gm%": "g/dL",
        "g/l": "g/L",
        "%": "%",
        "percent": "%",
        "/mcl": "/mcL",
        "cells/mcl": "/mcL",
        "cells/mm3": "/mcL",
        "/mm3": "/mcL",
        "u/l": "U/L",
        "iu/l": "IU/L",
        "mmhg": "mmHg",
        "bpm": "bpm",
        "beats/min": "bpm",
        "c": "°C",
        "°c": "°C",
        "f": "°F",
        "°f": "°F",
        "kg": "kg",
        "lbs": "lbs",
    }
    return mapping.get(u, str(raw_unit).strip())


def extract_biomarker_records(
    documents: list[Any],
    investigations: list[dict[str, Any]],
) -> list[BiomarkerRecord]:
    """
    Extracts and normalizes BiomarkerRecord objects from clinical documents
    and standalone investigations.
    """
    records: list[BiomarkerRecord] = []

    # 1. Ingest from documents
    for doc in documents or []:
        if not doc:
            continue
        doc_dict = doc.model_dump() if hasattr(doc, "model_dump") else (doc if isinstance(doc, dict) else {})
        doc_id = doc_dict.get("document_id") or "DOC_UNKNOWN"
        doc_date = doc_dict.get("document_date")

        for bm in doc_dict.get("structured_biomarkers") or []:
            if not isinstance(bm, dict):
                continue
            raw_name = bm.get("biomarker") or bm.get("test_name") or bm.get("name")
            val_raw = bm.get("value")
            if raw_name is None or val_raw is None:
                continue

            try:
                val = float(val_raw)
            except (ValueError, TypeError):
                continue

            norm_key, display_name = normalize_test_name(raw_name)
            unit_norm = normalize_unit(bm.get("unit"))
            status = bm.get("status")
            is_abn = bm.get("is_abnormal") or (status in {"high", "low", "critical_high", "critical_low", "abnormal"})

            records.append(BiomarkerRecord(
                test_name=display_name,
                normalized_name=norm_key,
                value=val,
                unit=unit_norm,
                reference_range=bm.get("reference_range"),
                is_abnormal=is_abn,
                status=status,
                observation_date=doc_date,
                source_document_id=doc_id,
                provenance=f"document_{doc_id}",
            ))

    # 2. Ingest from standalone investigations
    for idx, inv in enumerate(investigations or [], start=1):
        if not isinstance(inv, dict):
            continue
        inv_id = inv.get("investigation_id") or inv.get("source_document_id") or f"INV_{idx:03d}"
        raw_name = inv.get("test_name") or inv.get("biomarker") or inv.get("name")
        val_raw = inv.get("value")
        if raw_name is None or val_raw is None:
            continue

        try:
            val = float(val_raw)
        except (ValueError, TypeError):
            continue

        norm_key, display_name = normalize_test_name(raw_name)
        unit_norm = normalize_unit(inv.get("unit"))
        status = inv.get("status")
        is_abn = inv.get("is_abnormal") or (status in {"high", "low", "critical_high", "critical_low", "abnormal"})
        obs_date = inv.get("observation_date") or inv.get("date")

        records.append(BiomarkerRecord(
            test_name=display_name,
            normalized_name=norm_key,
            value=val,
            unit=unit_norm,
            reference_range=inv.get("reference_range"),
            is_abnormal=is_abn,
            status=status,
            observation_date=obs_date,
            source_document_id=inv_id,
            provenance=f"investigation_{inv_id}",
        ))

    return records


def calculate_biomarker_trajectories(
    records: list[BiomarkerRecord],
) -> list[BiomarkerTrajectory]:
    """
    Groups biomarker records by normalized test name and calculates purely mathematical trajectories.
    """
    grouped: dict[str, list[BiomarkerRecord]] = {}
    for r in records:
        grouped.setdefault(r.normalized_name, []).append(r)

    trajectories: list[BiomarkerTrajectory] = []

    for norm_name, recs in grouped.items():
        def get_date_key(rec: BiomarkerRecord) -> str:
            return rec.observation_date or ""

        sorted_recs = sorted(recs, key=get_date_key)
        display_name = sorted_recs[0].test_name
        doc_sources = list(dict.fromkeys(r.source_document_id for r in sorted_recs if r.source_document_id))

        distinct_units = list(dict.fromkeys(r.unit for r in sorted_recs if r.unit))
        unit_mismatch = len(distinct_units) > 1
        canonical_unit = distinct_units[0] if distinct_units else None

        obs_count = len(sorted_recs)
        earliest_obs = sorted_recs[0]
        latest_obs = sorted_recs[-1]

        if obs_count < 2 or unit_mismatch:
            traj_type: BiomarkerTrajectoryType = "insufficient_data"
            direction = "insufficient_data" if obs_count < 2 else "unit_mismatch"
            trajectories.append(BiomarkerTrajectory(
                test_name=display_name,
                normalized_name=norm_name,
                observations=sorted_recs,
                observation_count=obs_count,
                earliest_observation=earliest_obs,
                latest_observation=latest_obs,
                absolute_delta=None,
                percentage_change=None,
                direction=direction,
                trajectory=traj_type,
                unit=canonical_unit,
                unit_mismatch=unit_mismatch,
                provenance_sources=doc_sources,
            ))
            continue

        values = [r.value for r in sorted_recs]
        v_early = values[0]
        v_late = values[-1]
        abs_delta = round(v_late - v_early, 4)

        pct_change = None
        if v_early != 0:
            pct_change = round((abs_delta / abs(v_early)) * 100.0, 2)

        is_monotone_inc = all(values[i] <= values[i + 1] for i in range(len(values) - 1)) and (values[-1] > values[0])
        is_monotone_dec = all(values[i] >= values[i + 1] for i in range(len(values) - 1)) and (values[-1] < values[0])
        is_all_equal = all(values[i] == values[0] for i in range(len(values)))

        if is_all_equal:
            traj_type = "stable"
            direction = "unchanged"
        elif is_monotone_inc:
            traj_type = "increasing"
            direction = "upward"
        elif is_monotone_dec:
            traj_type = "decreasing"
            direction = "downward"
        else:
            diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
            has_inc = any(d > 0 for d in diffs)
            has_dec = any(d < 0 for d in diffs)
            if has_inc and has_dec:
                traj_type = "fluctuating"
                direction = "fluctuating"
            elif v_late > v_early:
                traj_type = "increasing"
                direction = "upward"
            elif v_late < v_early:
                traj_type = "decreasing"
                direction = "downward"
            else:
                traj_type = "stable"
                direction = "unchanged"

        trajectories.append(BiomarkerTrajectory(
            test_name=display_name,
            normalized_name=norm_name,
            observations=sorted_recs,
            observation_count=obs_count,
            earliest_observation=earliest_obs,
            latest_observation=latest_obs,
            absolute_delta=abs_delta,
            percentage_change=pct_change,
            direction=direction,
            trajectory=traj_type,
            unit=canonical_unit,
            unit_mismatch=unit_mismatch,
            provenance_sources=doc_sources,
        ))

    return sorted(trajectories, key=lambda t: t.test_name)
