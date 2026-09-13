"""
Interactive Telugu Clinical Intake Dialogue Runner.
Allows manual testing of VaidyaArc Clinical Brain in native Telugu (and Telugu-English code-switching).
"""

import sys
import os
import io

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

# Ensure repository root is on sys.path
repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.normalized_schemas import (
    NormalizedClinicalInputDTO,
    NormalizedMessageDTO,
    PatientProfileDTO,
)
from app.orchestrator import process_turn

# Quick clinical translation helper for manual Telugu testing
TELUGU_TRANSLATION_MAP = {
    # Symptoms / Complaints
    "జ్వరం": "fever",
    "తలనొప్పి": "headache",
    "కాళ్ళ నొప్పి": "foot pain",
    "కాలు నొప్పి": "foot pain",
    "మోకాళ్ళు నొప్పి": "knee pain",
    "మోకాలు నొప్పి": "knee pain",
    "కడుపు నొప్పి": "abdominal pain",
    "కడుపులో మంట": "burning sensation in stomach",
    "వాంతులు": "vomiting",
    "వాపు": "swelling",
    "దగ్గు": "cough",
    "రొంప": "cold",
    
    # Durations / Timing
    "రెండు రోజుల": "two days",
    "రెండు రోజులు": "two days",
    "నిన్నటి నుండి": "since yesterday",
    "నిన్న": "yesterday",
    "వారం రోజుల": "one week",
    "రాత్రి": "night",
    
    # Severities / Intensities
    "తీవ్రమైన": "severe",
    "విపరీతంగా": "very severe",
    "ఎక్కువగా": "high / severe",
    "కొంచెం": "mild",
    "చలి": "chills",
    
    # Laterality & Activities
    "కుడి": "right",
    "ఎడమ": "left",
    "నడవడం": "walking",
    "మెట్లు": "climbing stairs",
    "చాలా దూరం నడిచాను": "walked a long distance",
    "లాగుతున్నట్లు": "pulling sensation",
    
    # Negations & PMH
    "లేదు": "no / denied",
    "బీపీ": "blood pressure",
    "షుగర్": "diabetes",
    "మందులు": "regular medications",
}

def translate_telugu_input(telugu_text: str) -> str:
    """Translates common Telugu clinical terms to normalized English."""
    cleaned = telugu_text.strip()
    english_terms = []
    
    # If user provided mixed Telugu-English or English directly, keep it
    has_english = any('a' <= ch <= 'z' or 'A' <= ch <= 'Z' for ch in cleaned)
    if has_english and len(cleaned.split()) > 2:
        return cleaned

    for te, en in TELUGU_TRANSLATION_MAP.items():
        if te in cleaned:
            english_terms.append(en)

    if english_terms:
        return "Patient reports: " + ", ".join(english_terms)
    return cleaned

SAMPLE_CONVERSATIONS = {
    "1": {
        "title": "Scenario 1: జ్వరం మరియు తలనొప్పి (Fever & Headache)",
        "turns": [
            ("నాకు జ్వరం మరియు తలనొప్పి ఉంది.", "I have a fever and a headache."),
            ("నాకు ఈ జ్వరం రెండు రోజుల నుంచి ఉంది.", "I have been suffering from fever for two days."),
            ("అవును, రాత్రి సమయంలో జ్వరం ఎక్కువగా ఉంటుంది, కొంచెం చలి కూడా వేస్తుంది.", "Yes, the fever comes with a high temperature and a little chill at night."),
            ("తలనొప్పి కూడా ఎక్కువగా వస్తుంది.", "I am also getting severe headaches."),
        ]
    },
    "2": {
        "title": "Scenario 2: కాళ్ళ నొప్పి & వాపు (Foot Pain & Swelling)",
        "turns": [
            ("నాకు కాళ్ళ నొప్పి వస్తుంది.", "I have severe pain in my feet."),
            ("నాకు ఈ కాళ్ళు నొప్పి రెండు రోజులుగా వస్తుంది, చాలా విపరీతంగా ఉంది.", "I have had this leg pain for the past two days and it has become very severe."),
            ("మెట్లు ఎక్కి దిగినప్పుడు నడుస్తున్నప్పుడు నొప్పి వస్తుంది.", "Hurts especially when climbing stairs and walking."),
            ("నొప్పి తీవ్రత 10 కి 7 గా ఉంది.", "Pain severity is 7 out of 10."),
        ]
    },
    "3": {
        "title": "Scenario 3: కడుపులో మంట & ఎసిడిటీ (Stomach Burning & Acidity)",
        "turns": [
            ("నాకు కడుపులో మంటగా ఉంది మరియు వాంతులు అవుతున్నాయి.", "I have a burning sensation in my stomach and vomiting."),
            ("ఇది 3 రోజుల నుండి ఉంది, తిన్న తర్వాత ఎక్కువవుతుంది.", "This has been happening for 3 days, worsens after eating."),
            ("నొప్పి మితంగా ఉంది (moderate).", "The pain is moderate."),
        ]
    }
}

def run_interactive_session():
    print("=" * 80)
    print(" వైద్యాఆర్క్ తెలుగు క్లినికల్ ఇంటేక్ టెస్టింగ్ టూల్")
    print(" VaidyaArc Interactive Telugu Clinical Intake CLI")
    print("=" * 80)
    print("\nఎంపికలు (Options):")
    print(" [1] Sample Scenario 1: జ్వరం & తలనొప్పి (Fever & Headache)")
    print(" [2] Sample Scenario 2: కాళ్ళ నొప్పి & వాపు (Foot Pain & Swelling)")
    print(" [3] Sample Scenario 3: కడుపులో మంట & ఎసిడిటీ (Stomach Burning & Acidity)")
    print(" [4] Custom Interactive Chat (మీరే నేరుగా తెలుగులో టైప్ చేయండి)")
    print(" [q] నిష్క్రమించు (Quit)\n")

    choice = input("మీ ఎంపికను నమోదు చేయండి (1/2/3/4/q): ").strip().lower()
    if choice == "q":
        print("ధన్యవాదాలు (Exiting).")
        return

    state_snapshot = None

    if choice in ["1", "2", "3"]:
        scenario = SAMPLE_CONVERSATIONS[choice]
        print(f"\n--- {scenario['title']} ---")
        for i, (te_msg, en_msg) in enumerate(scenario["turns"], 1):
            print(f"\n[Turn {i}] పేషెంట్ (Telugu): {te_msg}")
            print(f"[Turn {i}] ట్రాన్స్‌లేషన్ (English): {en_msg}")

            dto = NormalizedClinicalInputDTO(
                patient_id="TELUGU_TEST_USER",
                episode_id="EP_CLI_TELUGU",
                channel="cli_test",
                message=NormalizedMessageDTO(
                    original_text=te_msg,
                    original_language="te-IN",
                    english_text=en_msg,
                    source="patient",
                ),
                state_snapshot=state_snapshot,
            )
            response = process_turn(dto)
            state_snapshot = response.updated_state

            print(f"\nమోడల్ స్పందన (Model Response):\n{response.conversation_message}")
            print(f"స్టేటస్: {response.status} (సమాచారం పూర్తయిందా: {response.information_complete})")
            if response.information_complete:
                print("\n ఇంటేక్ విజయవంతంగా పూర్తయింది! (Intake Complete)")
                break

    elif choice == "4":
        print("\n--- Custom Telugu Intake Chat ---")
        print("మీ లక్షణాలను తెలుగులో టైప్ చేయండి. (Type 'exit' or 'q' to stop)\n")
        turn_num = 1
        while True:
            user_input = input(f"\n[Turn {turn_num}] పేషెంట్: ").strip()
            if user_input.lower() in ["exit", "q", "quit"]:
                print("చర్చ ముగిసింది (Chat ended).")
                break
            if not user_input:
                continue

            en_translation = translate_telugu_input(user_input)
            print(f" -> అంతర్గత అనువాదం (Translated): {en_translation}")

            dto = NormalizedClinicalInputDTO(
                patient_id="TELUGU_INTERACTIVE_USER",
                episode_id="EP_INTERACTIVE_001",
                channel="cli_test",
                message=NormalizedMessageDTO(
                    original_text=user_input,
                    original_language="te-IN",
                    english_text=en_translation,
                    source="patient",
                ),
                state_snapshot=state_snapshot,
            )
            response = process_turn(dto)
            state_snapshot = response.updated_state

            print(f"\nవైద్యాఆర్క్ మోడల్ (Model Response):\n{response.conversation_message}")
            print(f"(Status: {response.status}, Complete: {response.information_complete})")

            if response.information_complete:
                print("\n ఇంటేక్ పూర్తయింది. డాక్టర్ కోసం కేస్-షీట్ సిద్ధంగా ఉంది. (Intake complete!)")
                break
            turn_num += 1

if __name__ == "__main__":
    run_interactive_session()
