"""
Phase 7: Versioned Ayurvedic Knowledge Base (AYURVEDA_KB_V1).

A curated, small, explicit, versioned repository of Ayurvedic descriptive symptom
concepts (Lakshana / Rupa / Guna).

STRICT BOUNDARIES:
- Contains ONLY descriptive symptom concepts.
- NO disease diagnoses (Nidana).
- NO treatment or medication recommendations.
- NO automatic Dosha or Prakriti determinations.
- Explicit source references and limitations for every concept.
- Verifiable citations only (no fabricated citations).

ZERO-LLM. 100% DETERMINISTIC.
"""

from typing import Optional, Any
from dataclasses import dataclass, field


AYURVEDA_KB_VERSION = "1.0.0"


@dataclass(frozen=True)
class AyurvedicKBEntry:
    """Explicit knowledge base entry for an Ayurvedic descriptive symptom concept."""
    concept_id: str
    sanskrit_name: str
    english_descriptor: str
    category: str
    description: str
    trigger_keywords: tuple[str, ...]
    required_evidence_criteria: tuple[str, ...]
    excluded_or_insufficient_conditions: tuple[str, ...]
    limitations: tuple[str, ...]
    source_reference: Optional[str]
    is_reference_verified: bool


# Curated, explicit descriptive concept entries in AYURVEDA_KB_V1
AYURVEDA_KB_ENTRIES: dict[str, AyurvedicKBEntry] = {
    "vidaha": AyurvedicKBEntry(
        concept_id="vidaha",
        sanskrit_name="Vidaha",
        english_descriptor="Burning sensation / Burning discomfort descriptor",
        category="sensory_quality",
        description="Sensory perception of heat, burning, or acid-like irritation in the GI tract, chest, or abdomen.",
        trigger_keywords=("burning", "burning pain", "burning sensation", "heartburn", "acid burning", "burning stomach", "burning in chest"),
        required_evidence_criteria=("Patient reports burning or heat-like character in chief complaint or nature of pain.",),
        excluded_or_insufficient_conditions=("Vague pain without burning quality", "Isolated non-burning dull ache"),
        limitations=(
            "Descriptive sensory quality only.",
            "Does NOT establish Pitta-Dosha imbalance.",
            "Does NOT establish modern gastritis, GERD, or ulcer diagnosis.",
        ),
        source_reference="Charaka Samhita, Sutrasthana Ch. 20 (Symptom descriptor taxonomy: Vidaha / Daha)",
        is_reference_verified=True,
    ),
    "shoola_udara": AyurvedicKBEntry(
        concept_id="shoola_udara",
        sanskrit_name="Udara Shoola",
        english_descriptor="Abdominal colic / Pain descriptor",
        category="symptom_descriptor",
        description="Ache, colic, or cramp localized to the abdominal or epigastric region.",
        trigger_keywords=("stomach pain", "abdominal pain", "belly ache", "belly pain", "stomach cramp", "colic", "cramping abdomen", "upper abdomen pain"),
        required_evidence_criteria=("Patient reports abdominal or stomach pain as primary complaint or location.",),
        excluded_or_insufficient_conditions=("Pain outside the abdomen", "Vague malaise without pain"),
        limitations=(
            "General anatomical colic/pain descriptor.",
            "Does NOT identify specific organ pathology or surgical abdomen.",
            "Must NOT delay modern emergency evaluation if red flags exist.",
        ),
        source_reference="Sushruta Samhita, Uttaratantra Ch. 42 (Symptom descriptor: Shoola)",
        is_reference_verified=True,
    ),
    "toda_bheda": AyurvedicKBEntry(
        concept_id="toda_bheda",
        sanskrit_name="Toda / Bheda",
        english_descriptor="Pricking / Sharp / Piercing pain descriptor",
        category="sensory_quality",
        description="Sharp, needle-like, stabbing, or piercing sensation of pain.",
        trigger_keywords=("sharp pain", "pricking", "piercing", "stabbing", "shooting pain", "sharp"),
        required_evidence_criteria=("Patient characterizes pain as sharp, stabbing, or piercing.",),
        excluded_or_insufficient_conditions=("Dull, heavy, or aching pain without sharp quality",),
        limitations=(
            "Character of pain only.",
            "Does NOT establish Vata-Dosha etiology or nerve injury.",
        ),
        source_reference="Charaka Samhita, Sutrasthana Ch. 20 (Pain character descriptor: Toda / Bheda)",
        is_reference_verified=True,
    ),
    "aruchi": AyurvedicKBEntry(
        concept_id="aruchi",
        sanskrit_name="Aruchi",
        english_descriptor="Loss of taste / Loss of appetite descriptor",
        category="functional_impairment",
        description="Absence of desire for food, tastelessness, or reduced appetite.",
        trigger_keywords=("loss of appetite", "no appetite", "reduced appetite", "loss of taste", "tastelessness", "anorexia", "poor appetite"),
        required_evidence_criteria=("Patient explicitly mentions loss of appetite or lack of desire for food.",),
        excluded_or_insufficient_conditions=("Normal appetite", "Unmentioned appetite status"),
        limitations=(
            "Subjective functional descriptor.",
            "Does NOT diagnose systemic or metabolic disorder.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 26 (Symptom descriptor: Aruchi)",
        is_reference_verified=True,
    ),
    "hrillasa": AyurvedicKBEntry(
        concept_id="hrillasa",
        sanskrit_name="Hrillasa",
        english_descriptor="Nausea / Salivation / Urge to vomit descriptor",
        category="functional_impairment",
        description="Qualmishness, excess salivation, or impending sensation of emesis.",
        trigger_keywords=("nausea", "nauseous", "feel sick", "urge to vomit", "queasy", "nausea feeling"),
        required_evidence_criteria=("Patient explicitly reports nausea or qualmishness.",),
        excluded_or_insufficient_conditions=("Actual emesis without preceding nausea", "Unmentioned nausea"),
        limitations=(
            "Reflex symptom descriptor.",
            "Does NOT identify modern GI, vestibular, or central etiology.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 20 (Symptom descriptor: Hrillasa)",
        is_reference_verified=True,
    ),
    "chhardi_vega": AyurvedicKBEntry(
        concept_id="chhardi_vega",
        sanskrit_name="Chhardi",
        english_descriptor="Emesis / Vomiting impulse descriptor",
        category="symptom_descriptor",
        description="Active regurgitation and forceful expulsion of gastric contents.",
        trigger_keywords=("vomiting", "vomit", "threw up", "throwing up", "emesis"),
        required_evidence_criteria=("Patient explicitly reports vomiting episodes.",),
        excluded_or_insufficient_conditions=("Isolated nausea without vomiting", "Unmentioned vomiting"),
        limitations=(
            "Physical expulsion descriptor.",
            "Does NOT evaluate volume loss, electrolyte disturbance, or hematemesis.",
            "Hematemesis triggers modern emergency red-flag layer.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 20 (Descriptor: Chhardi)",
        is_reference_verified=True,
    ),
    "kasa_vega": AyurvedicKBEntry(
        concept_id="kasa_vega",
        sanskrit_name="Kasa",
        english_descriptor="Cough impulse / Airway irritation descriptor",
        category="symptom_descriptor",
        description="Spasmodic respiratory expulsion caused by airway irritation.",
        trigger_keywords=("cough", "coughing", "dry cough", "wet cough", "productive cough", "throat irritation cough"),
        required_evidence_criteria=("Patient reports cough as chief complaint or associated symptom.",),
        excluded_or_insufficient_conditions=("Isolated throat pain without coughing", "Unmentioned cough"),
        limitations=(
            "Airway irritation descriptor.",
            "Does NOT determine infectious (viral/bacterial), allergic, or neoplastic etiology.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 18 (Descriptor: Kasa)",
        is_reference_verified=True,
    ),
    "shwasa_kashta": AyurvedicKBEntry(
        concept_id="shwasa_kashta",
        sanskrit_name="Shwasa Kashtata",
        english_descriptor="Dyspnea / Labored breathing descriptor",
        category="symptom_descriptor",
        description="Perceived difficulty, labor, or shortness of breath during respiration.",
        trigger_keywords=("shortness of breath", "difficulty breathing", "breathless", "wheezing", "gasping", "hard to breathe"),
        required_evidence_criteria=("Patient reports difficulty breathing or shortness of breath.",),
        excluded_or_insufficient_conditions=("Normal respiratory effort", "Unmentioned respiratory status"),
        limitations=(
            "Symptom descriptor for respiratory distress.",
            "CRITICAL: Modern emergency evaluation takes absolute precedence.",
            "Must NOT delay acute emergency care.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 17 (Descriptor: Shwasa)",
        is_reference_verified=True,
    ),
    "jwara_lakshana": AyurvedicKBEntry(
        concept_id="jwara_lakshana",
        sanskrit_name="Jwara Lakshana",
        english_descriptor="Elevated temperature / Febrile sensation descriptor",
        category="symptom_descriptor",
        description="Sensation of elevated body temperature, heat, or chills.",
        trigger_keywords=("fever", "high temperature", "chills", "feverish", "shivering", "warm body"),
        required_evidence_criteria=("Patient reports fever or elevated temperature.",),
        excluded_or_insufficient_conditions=("Subjective feeling of heat without fever", "Unmentioned temperature"),
        limitations=(
            "Thermoregulatory symptom descriptor.",
            "Does NOT identify pathogen, focus of infection, or inflammatory source.",
        ),
        source_reference="Charaka Samhita, Nidanasthana Ch. 1 (Descriptor: Jwara Lakshana)",
        is_reference_verified=True,
    ),
    "gurutva": AyurvedicKBEntry(
        concept_id="gurutva",
        sanskrit_name="Gurutva",
        english_descriptor="Sensation of heaviness descriptor",
        category="sensory_quality",
        description="Feeling of heaviness, fullness, or sluggishness in the body, abdomen, or head.",
        trigger_keywords=("heaviness", "heavy feeling", "bloated heaviness", "heavy head", "body heaviness", "feeling heavy"),
        required_evidence_criteria=("Patient reports heaviness or fullness quality.",),
        excluded_or_insufficient_conditions=("Lightness or weakness without heaviness sensation",),
        limitations=(
            "Subjective somatic sensation.",
            "Does NOT establish Kapha-Dosha or Ama diagnosis.",
        ),
        source_reference="Charaka Samhita, Sutrasthana Ch. 20 (Descriptor: Gurutva)",
        is_reference_verified=True,
    ),
    "vibandha": AyurvedicKBEntry(
        concept_id="vibandha",
        sanskrit_name="Vibandha / Malasanga",
        english_descriptor="Constipation / Hard stool descriptor",
        category="functional_impairment",
        description="Infrequent, difficult, or hard bowel evacuation.",
        trigger_keywords=("constipation", "hard stool", "difficulty passing stool", "irregular bowel", "constipated"),
        required_evidence_criteria=("Patient reports constipation or difficulty passing stools.",),
        excluded_or_insufficient_conditions=("Normal bowel habit", "Loose stools"),
        limitations=(
            "Bowel transit symptom descriptor.",
            "Does NOT evaluate structural colonic pathology or obstruction.",
        ),
        source_reference="Sushruta Samhita, Uttaratantra (Descriptor: Vibandha / Malasanga)",
        is_reference_verified=True,
    ),
    "atisara_vega": AyurvedicKBEntry(
        concept_id="atisara_vega",
        sanskrit_name="Atisara",
        english_descriptor="Diarrhea / Loose watery stool descriptor",
        category="symptom_descriptor",
        description="Excessive, frequent, or watery bowel evacuations.",
        trigger_keywords=("diarrhea", "loose motion", "watery stool", "loose stools", "frequent stool", "watery bowel"),
        required_evidence_criteria=("Patient reports diarrhea or loose watery stools.",),
        excluded_or_insufficient_conditions=("Formed normal stools", "Constipation"),
        limitations=(
            "Fluid stool descriptor.",
            "Does NOT evaluate infectious etiology or degree of dehydration.",
        ),
        source_reference="Charaka Samhita, Chikitsasthana Ch. 19 (Descriptor: Atisara)",
        is_reference_verified=True,
    ),
    "shiroruk": AyurvedicKBEntry(
        concept_id="shiroruk",
        sanskrit_name="Shiroruk / Shirotapa",
        english_descriptor="Cephalea / Head pain descriptor",
        category="symptom_descriptor",
        description="Pain, ache, or throbbing discomfort localized to the cranial region.",
        trigger_keywords=("headache", "head pain", "migraine", "pain in head", "throbbing head", "head ache"),
        required_evidence_criteria=("Patient reports headache or pain in head.",),
        excluded_or_insufficient_conditions=("Pain in other regions", "Dizziness without head pain"),
        limitations=(
            "Cranial pain descriptor.",
            "Does NOT rule out intracranial pathology, acute glaucoma, or secondary headache emergencies.",
        ),
        source_reference="Charaka Samhita, Siddhisthana Ch. 9 (Descriptor: Shiroruk / Shirotapa)",
        is_reference_verified=True,
    ),
    "sandhishoola": AyurvedicKBEntry(
        concept_id="sandhishoola",
        sanskrit_name="Sandhishoola",
        english_descriptor="Articular pain / Joint discomfort descriptor",
        category="symptom_descriptor",
        description="Pain, ache, or stiffness localized to one or more anatomical joints.",
        trigger_keywords=("joint pain", "knee pain", "joint ache", "arthralgia", "stiff joints", "pain in joints", "ankle pain", "elbow pain"),
        required_evidence_criteria=("Patient reports joint pain or stiffness.",),
        excluded_or_insufficient_conditions=("Muscle ache without joint involvement",),
        limitations=(
            "Articular symptom descriptor.",
            "Does NOT diagnose specific inflammatory, degenerative, or autoimmune arthritis.",
        ),
        source_reference="Madhava Nidana, Sandhivata/Amavata Lakshana (Descriptor: Sandhishoola)",
        is_reference_verified=True,
    ),
    "klama": AyurvedicKBEntry(
        concept_id="klama",
        sanskrit_name="Klama / Daurbalya",
        english_descriptor="Fatigue / Unprovoked exhaustion descriptor",
        category="functional_impairment",
        description="Subjective sensation of fatigue, weariness, or weakness without proportional exertion.",
        trigger_keywords=("fatigue", "tiredness", "exhaustion", "weakness", "lethargy", "feeling tired", "worn out"),
        required_evidence_criteria=("Patient reports fatigue, weakness, or tiredness.",),
        excluded_or_insufficient_conditions=("Normal energy levels", "Unmentioned energy state"),
        limitations=(
            "General somatic descriptor.",
            "Does NOT determine metabolic, anemia, thyroid, or post-viral causes.",
        ),
        source_reference="Charaka Samhita, Sutrasthana Ch. 20 (Descriptor: Klama / Daurbalya)",
        is_reference_verified=True,
    ),
}


def lookup_ayurvedic_concepts(patient_tokens: list[str]) -> list[AyurvedicKBEntry]:
    """
    Deterministically lookup matched Ayurvedic KB entries based on patient-reported observation tokens.
    Returns matched entries ordered by concept_id for complete determinism.
    """
    matched: list[AyurvedicKBEntry] = []
    seen_ids: set[str] = set()

    for token in patient_tokens:
        clean_token = token.strip().lower()
        if not clean_token:
            continue

        for concept_id, entry in AYURVEDA_KB_ENTRIES.items():
            if concept_id in seen_ids:
                continue

            for keyword in entry.trigger_keywords:
                if keyword in clean_token or clean_token in keyword:
                    matched.append(entry)
                    seen_ids.add(concept_id)
                    break

    # Sort deterministically
    return sorted(matched, key=lambda e: e.concept_id)
