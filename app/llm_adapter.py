"""
Phase 8A & Phase 13: Multi-Provider Clinical LLM Adapter Abstraction Layer.

Decouples clinical intake reasoning and adaptive history-taking from specific LLM providers.
Supports:
1. Google Cloud Gemini (default when GEMINI_API_KEY is configured)
2. Local Ollama Llama 3
3. Deterministic zero-LLM fallback

ZERO heavy cloud SDK dependencies - runs natively via httpx and standard HTTP.
"""

import os
import json
import logging
from typing import Optional, Protocol, Dict, Any, List
from urllib.request import urlopen

import httpx
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from app.schemas import IntakeResult, AdaptiveIntakeResult
from app.domain.clinical_history_schema import (
    ClinicalFinding,
    VersionedAttribute,
    AttributeEvidence,
    ClinicalDelta,
    EpistemicStatus,
)

load_dotenv()
logger = logging.getLogger(__name__)


class LLMAdapter(Protocol):
    """Protocol for clinical language extraction and dynamic question generation adapters."""

    def extract_intake(self, message: str, previous_question: Optional[str] = None) -> IntakeResult:
        """Extract structured intake fields from patient message."""
        ...

    def conduct_adaptive_turn(
        self,
        current_message: str,
        conversation_history: list[dict],
        current_state: dict,
    ) -> AdaptiveIntakeResult:
        """Conduct an adaptive clinical intake turn: interpret symptoms, accumulate associated symptoms, formulate next question, decide completion."""
        ...

    def generate_next_question(
        self,
        current_message: str,
        known_info: dict,
        missing_info: list[str],
        target_field: str,
        previous_question: Optional[str] = None,
    ) -> Optional[str]:
        """Generate a single focused patient-facing question targeting target_field."""
        ...

    def extract_clinical_delta(
        self,
        message: str,
        history_dict: dict,
        turn_count: int,
        previous_question: Optional[str] = None,
    ) -> Optional[Any]:
        """Extract clinical delta for evolving clinical history ledger."""
        ...

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available."""
        ...



class OllamaAdapter:
    """
    Adapter wrapping the existing local Ollama (Llama 3) implementation.
    """

    def __init__(
        self,
        model_name: str = "llama3:latest",
        endpoint: str = "http://127.0.0.1:11434",
        timeout: float = 18.0,
    ):
        self.model_name = model_name
        self.endpoint = endpoint
        self.timeout = timeout
        self._model = ChatOllama(
            base_url=endpoint,
            model=model_name,
            temperature=0.0,
            num_predict=60,
            sync_client_kwargs={"timeout": timeout},
        )
        self._adaptive_chat = ChatOllama(
            base_url=endpoint,
            model=model_name,
            temperature=0.1,
            num_predict=300,
            sync_client_kwargs={"timeout": timeout},
        )
        self._adaptive_model = self._adaptive_chat.with_structured_output(
            AdaptiveIntakeResult,
            method="json_schema"
        )
        self._structured_model = self._model.with_structured_output(
            IntakeResult,
            method="json_schema"
        )

    def is_available(self) -> bool:
        try:
            with urlopen(f"{self.endpoint}/api/tags", timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def extract_intake(self, message: str, previous_question: Optional[str] = None) -> IntakeResult:
        """
        Attempts structured LLM extraction via Ollama; falls back to deterministic regex
        if Ollama is unreachable or extraction raises an error.
        """
        if not (message or "").strip():
            return IntakeResult()

        from app.nodes import _fallback_extract_information

        if self.is_available():
            try:
                system_prompt = (
                    "You are an AI medical intake assistant. "
                    "Extract structured clinical information explicitly stated in the patient's message. "
                    "Do NOT guess or infer unmentioned details. Return strictly valid JSON."
                )
                user_content = message
                if previous_question:
                    user_content = f"Previous Question: {previous_question}\nPatient Response: {message}"

                result = self._structured_model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ])
                if isinstance(result, IntakeResult):
                    return result
            except Exception:
                pass

        # Deterministic fallback
        raw_dict = _fallback_extract_information(message, previous_question or "")
        return IntakeResult(**raw_dict)

    def conduct_adaptive_turn(
        self,
        current_message: str,
        conversation_history: list[dict],
        current_state: dict,
    ) -> AdaptiveIntakeResult:
        """
        Conducts an adaptive clinical intake turn: interprets symptoms,
        accumulates associated symptoms, formulates adaptive follow-up question,
        and determines when intake is complete.
        """
        if not (current_message or "").strip():
            return _deterministic_adaptive_turn(current_message, current_state)

        if self.is_available():
            try:
                system_prompt = (
                    "You are the empathetic, expert AI Clinical Intake Specialist for VaidyaArc.\n"
                    "Your objective is to conduct a natural, thorough, and clinically rigorous medical history taking with the patient to prepare a physician-ready clinical summary report.\n\n"
                    "CLINICAL HISTORY TAKING PROTOCOL:\n"
                    "Guide the consultation through the following medical history stages:\n"
                    "1. SYMPTOM CHARACTERIZATION & ASSOCIATED SYMPTOMS:\n"
                    "   - Identify 'chief_complaint' (e.g. 'headache', 'head injury', 'chest pain', 'abdominal pain', 'fever', 'cough').\n"
                    "   - Differentiate spontaneous pain from trauma: if trauma/impact occurred (e.g. hit head, fell, bumped, blow), record 'chief_complaint' as 'head injury' (NOT headache).\n"
                    "   - Extract onset & duration ('2 days', 'since yesterday'), severity ('mild', 'moderate', 'severe'), location, and nature of pain ('throbbing', 'burning', 'dull', 'sharp').\n"
                    "   - Map natural language severity qualifiers: 'minimal', 'slight', 'a little', 'bearable' -> 'mild'; 'manageable', 'tolerable' -> 'moderate'; 'unbearable', 'excruciating', 'intense' -> 'severe'.\n"
                    "   - Actively explore co-occurring symptoms tailored to the complaint (e.g. for headache: nausea, visual aura, light sensitivity, neck stiffness; for abdominal pain: nausea, vomiting, fever, bowel changes; for fever: chills, cough, body ache).\n"
                    "   - Record reported symptoms into 'associated_symptoms', and explicitly denied symptoms into 'pertinent_negatives'.\n\n"
                    "2. PREVIOUS OCCURRENCES & MEDICAL HISTORY INQUIRY:\n"
                    "   - Once primary symptoms are characterized, you MUST ask whether the patient has ever experienced this symptom before:\n"
                    "     * e.g., 'Have you ever experienced this kind of pain before, or is this the first time?'\n"
                    "     * e.g., 'When was the last time you had an episode or fever like this?'\n"
                    "     * e.g., 'Do you have any existing chronic health conditions or take regular daily medications?'\n"
                    "   - Record their response into 'past_history' (e.g. 'First episode ever' or 'Recurrent episodes for 6 months; no chronic illnesses').\n\n"
                    "3. OPEN-FLOOR INVITATION BEFORE COMPLETION:\n"
                    "   - After symptoms and previous history are recorded, offer the patient an open floor to describe anything else:\n"
                    "     * e.g., 'Thank you. I have recorded your symptoms and history. If there are any other things you want to describe to me, please go on with that.'\n"
                    "   - Record any additional descriptions into 'additional_notes'.\n\n"
                    "4. TRIAGE COMPLETION & PHYSICIAN REPORT PREPARATION:\n"
                    "   - Set 'is_complete' = True ONLY AFTER:\n"
                    "     (a) Symptoms are characterized (onset/duration, severity, associated symptoms/pertinent negatives),\n"
                    "     (b) Previous history/recurrence has been explored, AND\n"
                    "     (c) The patient has been offered the open floor to describe anything else (or after 4-5 turns).\n"
                    "   - When 'is_complete' is True, set 'adaptive_question' to:\n"
                    "     'Thank you. Your clinical intake and assessment are complete. I have organized your details into a clinical summary for the doctor. If there are any other things you want to describe to me as you wait, please feel free to go on with that.'\n\n"
                    "5. ADAPTIVE QUESTIONING RULES:\n"
                    "   - Formulate exactly ONE natural, conversational, context-aware question ('adaptive_question') based on the patient's previous answer and conversation history.\n"
                    "   - Acknowledge what the patient shared before asking the next question.\n"
                    "   - Never ask for information the patient already provided.\n"
                    "   - NEVER diagnose any disease or condition.\n"
                    "   - NEVER prescribe any medication or treatment."
                )

                known_info = {
                    "chief_complaint": current_state.get("chief_complaint"),
                    "associated_symptoms": current_state.get("associated_symptoms") or [],
                    "pertinent_negatives": current_state.get("pertinent_negatives") or [],
                    "duration": current_state.get("duration"),
                    "severity": current_state.get("severity"),
                    "location": current_state.get("location"),
                    "nature_of_pain": current_state.get("nature_of_pain"),
                    "past_history": current_state.get("past_history_notes"),
                    "additional_notes": current_state.get("additional_patient_notes"),
                }
                questions_asked = current_state.get("questions_asked") or []

                # Format conversation history for context
                conv_history = current_state.get("conversation_history") or []
                conv_summary = "\n".join(
                    f"{entry.get('role', 'speaker').capitalize()}: {entry.get('content', '')}"
                    for entry in conv_history[-6:]
                ) if conv_history else "None (Beginning of encounter)"

                user_content = (
                    f"Prior Known Clinical State: {known_info}\n"
                    f"Recent Conversation History:\n{conv_summary}\n"
                    f"Questions Asked Count: {len(questions_asked)}\n"
                    f"Latest Patient Utterance: {current_message}"
                )

                result = self._adaptive_model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ])
                if isinstance(result, AdaptiveIntakeResult):
                    from app.nodes import (
                        _sanitize_associated_symptoms,
                        _canonicalize_chief_complaint,
                        _extract_duration,
                        _extract_severity,
                        _has_trauma_context,
                    )
                    det = _deterministic_adaptive_turn(current_message, current_state)

                    all_assoc = list(result.associated_symptoms or []) + list(det.associated_symptoms or [])
                    result.associated_symptoms = _sanitize_associated_symptoms(all_assoc)

                    all_negs = list(result.pertinent_negatives or []) + list(det.pertinent_negatives or [])
                    result.pertinent_negatives = list(dict.fromkeys(all_negs))

                    if result.chief_complaint:
                        result.chief_complaint = _canonicalize_chief_complaint(result.chief_complaint)
                    if not result.chief_complaint and not current_state.get("chief_complaint"):
                        result.chief_complaint = det.chief_complaint

                    loc_val = result.location or det.location or current_state.get("location")
                    if result.chief_complaint and result.chief_complaint.lower() in {"pain", "discomfort"} and loc_val:
                        has_trauma = _has_trauma_context(current_message) or _has_trauma_context(loc_val)
                        if "head" in loc_val.lower():
                            result.chief_complaint = "head injury" if has_trauma else "headache"
                        elif "chest" in loc_val.lower():
                            result.chief_complaint = "chest injury" if has_trauma else "chest pain"

                    if result.duration:
                        result.duration = _extract_duration(result.duration)
                    if not result.duration and det.duration:
                        result.duration = det.duration

                    if result.severity:
                        result.severity = _extract_severity(result.severity) or result.severity
                    if not result.severity and det.severity:
                        result.severity = det.severity

                    if not result.location and det.location:
                        result.location = det.location
                    if not result.nature_of_pain and det.nature_of_pain:
                        result.nature_of_pain = det.nature_of_pain

                    past_indicators = [
                        "first time", "never had", "had this before", "had a similar", "in the past",
                        "months ago", "weeks ago", "years ago", "recurrent", "history of", "happened before"
                    ]
                    prev_q_lower = (current_state.get("conversation_message") or "").lower()
                    is_past_hist_prompt = any(q_kw in prev_q_lower for q_kw in ["before", "first time", "experienced this", "similar episode", "past"])
                    has_past_evidence = any(ind in current_message.lower() for ind in past_indicators) or is_past_hist_prompt

                    if not has_past_evidence and not current_state.get("past_history_notes"):
                        result.past_history = None
                    elif not result.past_history and det.past_history:
                        result.past_history = det.past_history

                    if not result.additional_notes and det.additional_notes:
                        result.additional_notes = det.additional_notes

                    # Check open-floor prompt response
                    is_open_floor_prompt = any(phrase in prev_q_lower for phrase in ["any other things", "describe to me", "anything else you want to describe"])
                    patient_ended = any(term in current_message.lower() for term in ["nothing else", "no other", "that's all", "that is all", "that is everything", "nope", "nothing", "no"])

                    if is_open_floor_prompt:
                        if not patient_ended and not result.additional_notes:
                            result.additional_notes = current_message
                        result.is_complete = True

                    # Turn budget completion guard
                    has_cc = bool(result.chief_complaint or current_state.get("chief_complaint"))
                    if has_cc and (len(questions_asked) >= 4 or (result.past_history and is_open_floor_prompt)):
                        result.is_complete = True

                    from app.nodes import _validate_clinical_question
                    known_clinical_info = {
                        "chief_complaint": result.chief_complaint or current_state.get("chief_complaint"),
                        "duration": result.duration or current_state.get("duration"),
                        "severity": result.severity or current_state.get("severity"),
                        "location": result.location or current_state.get("location"),
                        "nature_of_pain": result.nature_of_pain or current_state.get("nature_of_pain"),
                    }
                    if not result.adaptive_question or not _validate_clinical_question(result.adaptive_question, "follow_up", known_clinical_info):
                        result.adaptive_question = det.adaptive_question

                    if not result.intake_stage:
                        result.intake_stage = det.intake_stage

                    if det.is_complete:
                        result.is_complete = True

                    if result.is_complete:
                        result.adaptive_question = (
                            "Thank you. Your clinical intake and assessment are complete. "
                            "I have organized your details into a clinical summary for the doctor. "
                            "If there are any other things you want to describe to me as you wait, please feel free to go on with that."
                        )

                    return result
            except Exception:
                pass

        return _deterministic_adaptive_turn(current_message, current_state)

    def generate_next_question(
        self,
        current_message: str,
        known_info: dict,
        missing_info: list[str],
        target_field: str,
        previous_question: Optional[str] = None,
    ) -> Optional[str]:
        """
        Attempts to generate a single focused next question via Ollama.
        Executes ONE direct LLM call without an extra preliminary probe.
        Falls back to None on any error, timeout, or malformed generation.
        """
        try:
            sys_prompt = (
                "You are an empathetic clinical intake assistant. "
                "Formulate exactly ONE natural, conversational, patient-facing question targeting the specified missing clinical field. "
                "Rules:\n"
                "- Ask exactly ONE short question ending with a question mark.\n"
                "- Target the requested missing field directly and empathetically.\n"
                "- Do NOT diagnose, suggest treatments, prescribe medications, or provide medical opinions.\n"
                "- Do NOT ask compound questions or ask about already known details.\n"
                "- Return ONLY the question. No explanations, no markdown, no quotes."
            )

            known_items = [f"{k}={v}" for k, v in known_info.items() if v]
            known_str = ", ".join(known_items) if known_items else "None"

            user_prompt = (
                f"Patient message: {current_message}\n"
                f"Known clinical facts: {known_str}\n"
                f"Target missing field to ask about: {target_field}\n"
                f"ONE question to ask patient about {target_field}:"
            )

            response = self._model.invoke([
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ])

            content = (response.content or "").strip()
            # Strip enclosing single/double quotes if present
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                content = content[1:-1].strip()
            return content if content else None
        except Exception:
            return None

    def extract_clinical_delta(
        self,
        message: str,
        history_dict: dict,
        turn_count: int,
        previous_question: Optional[str] = None,
    ) -> Optional[Any]:
        """Ollama does not perform deep schema delta extraction directly; falls back to deterministic rule projection."""
        return None


class GeminiAdapter:
    """
    Cloud-based LLM adapter using Google Gemini REST API.
    Zero heavy cloud SDK dependencies - uses lightweight, high-performance httpx.
    Equipped with automatic secondary model failover (gemini-flash-latest -> gemini-flash-lite-latest)
    and graceful failover to deterministic logic on network error.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 12.0,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
        self.fallback_model = "gemini-flash-lite-latest"
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.api_key)

    def _call_gemini_json(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        """Make a structured JSON call to Gemini API with automatic model failover."""
        if not self.is_available():
            return None

        models_to_try = [self.model_name]
        if self.fallback_model != self.model_name:
            models_to_try.append(self.fallback_model)

        combined_text = f"System Instruction:\n{system_prompt}\n\nTask Input:\n{user_prompt}"
        payload = {
            "contents": [{"parts": [{"text": combined_text}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        for model in models_to_try:
            url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "").strip()
                                return json.loads(raw_text)
                    elif resp.status_code in (503, 429):
                        logger.warning(f"Gemini model {model} returned status {resp.status_code}, trying fallback...")
                        continue
                    else:
                        logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"Gemini API call to {model} failed: {e}")
                continue

        return None

    def _call_gemini_text(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Make a text completion call to Gemini API with automatic model failover."""
        if not self.is_available():
            return None

        models_to_try = [self.model_name]
        if self.fallback_model != self.model_name:
            models_to_try.append(self.fallback_model)

        combined_text = f"System Instruction:\n{system_prompt}\n\nTask Input:\n{user_prompt}"
        payload = {
            "contents": [{"parts": [{"text": combined_text}]}],
            "generationConfig": {
                "temperature": 0.2,
            },
        }

        for model in models_to_try:
            url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    elif resp.status_code in (503, 429):
                        logger.warning(f"Gemini model {model} returned status {resp.status_code}, trying fallback...")
                        continue
            except Exception as e:
                logger.warning(f"Gemini text API call to {model} failed: {e}")
                continue

        return None

    def extract_intake(self, message: str, previous_question: Optional[str] = None) -> IntakeResult:
        """Extract structured intake fields from patient message via Gemini."""
        if not (message or "").strip():
            return IntakeResult()

        from app.nodes import _fallback_extract_information

        if self.is_available():
            try:
                system_prompt = (
                    "You are an AI medical intake assistant. "
                    "Extract structured clinical information explicitly stated in the patient's message. "
                    "Do NOT guess or infer unmentioned details. "
                    "Return strictly valid JSON with keys: "
                    "chief_complaint (str or null), symptoms (list of str), duration (str or null), "
                    "severity (str or null), location (str or null), nature_of_pain (str or null), "
                    "associated_symptoms (list of str), pertinent_negatives (list of str)."
                )
                user_content = message
                if previous_question:
                    user_content = f"Previous Question: {previous_question}\nPatient Response: {message}"

                result_dict = self._call_gemini_json(system_prompt, user_content)
                if result_dict and isinstance(result_dict, dict):
                    return IntakeResult(**result_dict)
            except Exception as e:
                logger.warning(f"Gemini extract_intake failed: {e}")

        # Deterministic fallback
        raw_dict = _fallback_extract_information(message, previous_question or "")
        return IntakeResult(**raw_dict)

    def conduct_adaptive_turn(
        self,
        current_message: str,
        conversation_history: list[dict],
        current_state: dict,
    ) -> AdaptiveIntakeResult:
        """
        Conducts an adaptive clinical intake turn using Google Gemini:
        interprets symptoms, accumulates associated symptoms, formulates adaptive follow-up question,
        and determines when intake is complete.
        """
        if not (current_message or "").strip():
            return _deterministic_adaptive_turn(current_message, current_state)

        if self.is_available():
            try:
                system_prompt = (
                    "You are the empathetic, expert AI Clinical Intake Specialist for VaidyaArc.\n"
                    "Your objective is to conduct a natural, thorough, and clinically rigorous medical history taking with the patient to prepare a physician-ready clinical summary report.\n\n"
                    "CLINICAL HISTORY TAKING PROTOCOL:\n"
                    "Guide the consultation through the following medical history stages:\n"
                    "1. SYMPTOM CHARACTERIZATION & ASSOCIATED SYMPTOMS:\n"
                    "   - Identify 'chief_complaint' (e.g. 'headache', 'head injury', 'chest pain', 'abdominal pain', 'fever', 'cough').\n"
                    "   - Differentiate spontaneous pain from trauma: if trauma/impact occurred (e.g. hit head, fell, bumped, blow), record 'chief_complaint' as 'head injury' (NOT headache).\n"
                    "   - Extract onset & duration ('2 days', 'since yesterday'), severity ('mild', 'moderate', 'severe'), location, and nature of pain ('throbbing', 'burning', 'dull', 'sharp').\n"
                    "   - Map natural language severity qualifiers: 'minimal', 'slight', 'a little', 'bearable' -> 'mild'; 'manageable', 'tolerable' -> 'moderate'; 'unbearable', 'excruciating', 'intense' -> 'severe'.\n"
                    "   - Actively explore co-occurring symptoms tailored to the complaint (e.g. for headache: nausea, visual aura, light sensitivity, neck stiffness; for abdominal pain: nausea, vomiting, fever, bowel changes; for fever: chills, cough, body ache).\n"
                    "   - Record reported symptoms into 'associated_symptoms', and explicitly denied symptoms into 'pertinent_negatives'.\n\n"
                    "2. PREVIOUS OCCURRENCES & MEDICAL HISTORY INQUIRY:\n"
                    "   - Once primary symptoms are characterized, you MUST ask whether the patient has ever experienced this symptom before:\n"
                    "     * e.g., 'Have you ever experienced this kind of pain before, or is this the first time?'\n"
                    "     * e.g., 'When was the last time you had an episode or fever like this?'\n"
                    "     * e.g., 'Do you have any existing chronic health conditions or take regular daily medications?'\n"
                    "   - Record their response into 'past_history' (e.g. 'First episode ever' or 'Recurrent episodes for 6 months; no chronic illnesses').\n\n"
                    "3. OPEN-FLOOR INVITATION BEFORE COMPLETION:\n"
                    "   - After symptoms and previous history are recorded, offer the patient an open floor to describe anything else:\n"
                    "     * e.g., 'Thank you. I have recorded your symptoms and history. If there are any other things you want to describe to me, please go on with that.'\n"
                    "   - Record any additional descriptions into 'additional_notes'.\n\n"
                    "4. TRIAGE COMPLETION & PHYSICIAN REPORT PREPARATION:\n"
                    "   - Set 'is_complete' = True ONLY AFTER:\n"
                    "     (a) Symptoms are characterized (onset/duration, severity, associated symptoms/pertinent negatives),\n"
                    "     (b) Previous history/recurrence has been explored, AND\n"
                    "     (c) The patient has been offered the open floor to describe anything else (or after 4-5 turns).\n"
                    "   - When 'is_complete' is True, set 'adaptive_question' to:\n"
                    "     'Thank you. Your clinical intake and assessment are complete. I have organized your details into a clinical summary for the doctor. If there are any other things you want to describe to me as you wait, please feel free to go on with that.'\n\n"
                    "5. ADAPTIVE QUESTIONING RULES:\n"
                    "   - Formulate exactly ONE natural, conversational, context-aware question ('adaptive_question') based on the patient's previous answer and conversation history.\n"
                    "   - Acknowledge what the patient shared before asking the next question.\n"
                    "   - Never ask for information the patient already provided.\n"
                    "   - NEVER diagnose any disease or condition.\n"
                    "   - NEVER prescribe any medication or treatment.\n\n"
                    "OUTPUT FORMAT: Return strictly a valid JSON object with keys:\n"
                    "- chief_complaint: string or null\n"
                    "- associated_symptoms: list of strings\n"
                    "- pertinent_negatives: list of strings\n"
                    "- duration: string or null\n"
                    "- severity: string or null\n"
                    "- location: string or null\n"
                    "- nature_of_pain: string or null\n"
                    "- past_history: string or null\n"
                    "- additional_notes: string or null\n"
                    "- adaptive_question: string or null\n"
                    "- is_complete: boolean\n"
                    "- intake_stage: string"
                )

                known_info = {
                    "chief_complaint": current_state.get("chief_complaint"),
                    "associated_symptoms": current_state.get("associated_symptoms") or [],
                    "pertinent_negatives": current_state.get("pertinent_negatives") or [],
                    "duration": current_state.get("duration"),
                    "severity": current_state.get("severity"),
                    "location": current_state.get("location"),
                    "nature_of_pain": current_state.get("nature_of_pain"),
                    "past_history": current_state.get("past_history_notes"),
                    "additional_notes": current_state.get("additional_patient_notes"),
                }
                questions_asked = current_state.get("questions_asked") or []

                conv_history = current_state.get("conversation_history") or []
                conv_summary = "\n".join(
                    f"{entry.get('role', 'speaker').capitalize()}: {entry.get('content', '')}"
                    for entry in conv_history[-6:]
                ) if conv_history else "None (Beginning of encounter)"

                user_content = (
                    f"Prior Known Clinical State: {known_info}\n"
                    f"Recent Conversation History:\n{conv_summary}\n"
                    f"Questions Asked Count: {len(questions_asked)}\n"
                    f"Latest Patient Utterance: {current_message}"
                )

                raw_dict = self._call_gemini_json(system_prompt, user_content)
                if raw_dict and isinstance(raw_dict, dict):
                    result = AdaptiveIntakeResult(**raw_dict)

                    from app.nodes import (
                        _sanitize_associated_symptoms,
                        _canonicalize_chief_complaint,
                        _extract_duration,
                        _extract_severity,
                        _has_trauma_context,
                        _validate_clinical_question,
                    )
                    det = _deterministic_adaptive_turn(current_message, current_state)

                    all_assoc = list(result.associated_symptoms or []) + list(det.associated_symptoms or [])
                    result.associated_symptoms = _sanitize_associated_symptoms(all_assoc)

                    all_negs = list(result.pertinent_negatives or []) + list(det.pertinent_negatives or [])
                    result.pertinent_negatives = list(dict.fromkeys(all_negs))

                    if result.chief_complaint:
                        result.chief_complaint = _canonicalize_chief_complaint(result.chief_complaint)
                    if not result.chief_complaint and not current_state.get("chief_complaint"):
                        result.chief_complaint = det.chief_complaint

                    loc_val = result.location or det.location or current_state.get("location")
                    if result.chief_complaint and result.chief_complaint.lower() in {"pain", "discomfort"} and loc_val:
                        has_trauma = _has_trauma_context(current_message) or _has_trauma_context(loc_val)
                        if "head" in loc_val.lower():
                            result.chief_complaint = "head injury" if has_trauma else "headache"
                        elif "chest" in loc_val.lower():
                            result.chief_complaint = "chest injury" if has_trauma else "chest pain"

                    if result.duration:
                        result.duration = _extract_duration(result.duration)
                    if not result.duration and det.duration:
                        result.duration = det.duration

                    if result.severity:
                        result.severity = _extract_severity(result.severity) or result.severity
                    if not result.severity and det.severity:
                        result.severity = det.severity

                    if not result.location and det.location:
                        result.location = det.location
                    if not result.nature_of_pain and det.nature_of_pain:
                        result.nature_of_pain = det.nature_of_pain

                    past_indicators = [
                        "first time", "never had", "had this before", "had a similar", "in the past",
                        "months ago", "weeks ago", "years ago", "recurrent", "history of", "happened before"
                    ]
                    prev_q_lower = (current_state.get("conversation_message") or "").lower()
                    is_past_hist_prompt = any(q_kw in prev_q_lower for q_kw in ["before", "first time", "experienced this", "similar episode", "past"])
                    has_past_evidence = any(ind in current_message.lower() for ind in past_indicators) or is_past_hist_prompt

                    if not has_past_evidence and not current_state.get("past_history_notes"):
                        result.past_history = None
                    elif not result.past_history and det.past_history:
                        result.past_history = det.past_history

                    if not result.additional_notes and det.additional_notes:
                        result.additional_notes = det.additional_notes

                    # Check open-floor prompt response
                    is_open_floor_prompt = any(phrase in prev_q_lower for phrase in ["any other things", "describe to me", "anything else you want to describe"])
                    patient_ended = any(term in current_message.lower() for term in ["nothing else", "no other", "that's all", "that is all", "that is everything", "nope", "nothing", "no"])

                    if is_open_floor_prompt:
                        if not patient_ended and not result.additional_notes:
                            result.additional_notes = current_message
                        result.is_complete = True

                    # Turn budget completion guard
                    has_cc = bool(result.chief_complaint or current_state.get("chief_complaint"))
                    if has_cc and (len(questions_asked) >= 4 or (result.past_history and is_open_floor_prompt)):
                        result.is_complete = True

                    known_clinical_info = {
                        "chief_complaint": result.chief_complaint or current_state.get("chief_complaint"),
                        "duration": result.duration or current_state.get("duration"),
                        "severity": result.severity or current_state.get("severity"),
                        "location": result.location or current_state.get("location"),
                        "nature_of_pain": result.nature_of_pain or current_state.get("nature_of_pain"),
                    }
                    if not result.adaptive_question or not _validate_clinical_question(result.adaptive_question, "follow_up", known_clinical_info):
                        result.adaptive_question = det.adaptive_question

                    if not result.intake_stage:
                        result.intake_stage = det.intake_stage

                    if det.is_complete:
                        result.is_complete = True

                    if result.is_complete:
                        result.adaptive_question = (
                            "Thank you. Your clinical intake and assessment are complete. "
                            "I have organized your details into a clinical summary for the doctor. "
                            "If there are any other things you want to describe to me as you wait, please feel free to go on with that."
                        )

                    return result
            except Exception as e:
                logger.warning(f"Gemini conduct_adaptive_turn failed: {e}")

        return _deterministic_adaptive_turn(current_message, current_state)

    def generate_next_question(
        self,
        current_message: str,
        known_info: dict,
        missing_info: list[str],
        target_field: str,
        previous_question: Optional[str] = None,
    ) -> Optional[str]:
        """Generate a single focused patient-facing question targeting target_field using Gemini."""
        try:
            sys_prompt = (
                "You are an empathetic clinical intake assistant. "
                "Formulate exactly ONE natural, conversational, patient-facing question targeting the specified missing clinical field. "
                "Rules:\n"
                "- Ask exactly ONE short question ending with a question mark.\n"
                "- Target the requested missing field directly and empathetically.\n"
                "- Do NOT diagnose, suggest treatments, prescribe medications, or provide medical opinions.\n"
                "- Do NOT ask compound questions or ask about already known details.\n"
                "- Return ONLY the question. No explanations, no markdown, no quotes."
            )

            known_items = [f"{k}={v}" for k, v in known_info.items() if v]
            known_str = ", ".join(known_items) if known_items else "None"

            user_prompt = (
                f"Patient message: {current_message}\n"
                f"Known clinical facts: {known_str}\n"
                f"Target missing field to ask about: {target_field}\n"
                f"ONE question to ask patient about {target_field}:"
            )

            content = self._call_gemini_text(sys_prompt, user_prompt)
            if content:
                content = content.strip()
                if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                    content = content[1:-1].strip()
                return content if content else None
            return None
        except Exception:
            return None

    def extract_clinical_delta(
        self,
        message: str,
        history_dict: dict,
        turn_count: int,
        previous_question: Optional[str] = None,
    ) -> Optional[ClinicalDelta]:
        """
        Extract clinical delta findings using Gemini cognitive parsing.
        Returns ClinicalDelta or None (triggering safe deterministic delta extraction).
        """
        if not self.is_available() or not (message or "").strip():
            return None

        try:
            existing_cc_obj = history_dict.get("chief_complaint") or {}
            existing_cc_name = existing_cc_obj.get("canonical_name") if isinstance(existing_cc_obj, dict) else None
            existing_cc_id = existing_cc_obj.get("entity_id") if isinstance(existing_cc_obj, dict) else None

            sys_prompt = (
                "You are an expert AI clinical extraction specialist for an evolving medical intake conversation.\n"
                "The patient is responding in an ongoing clinical consultation.\n"
                "If the patient's message is a direct/short answer (such as 'Since yesterday', 'Mild', 'On the right side', 'First time'), "
                "extract that information in relation to the active chief complaint and previous question.\n\n"
                "Extract explicitly stated symptoms, duration, severity, location, character, and pertinent negatives into JSON.\n"
                "JSON format:\n"
                "{\n"
                '  "chief_complaint": string or null,\n'
                '  "duration": string or null,\n'
                '  "severity": string or null,\n'
                '  "location": string or null,\n'
                '  "character": string or null,\n'
                '  "past_history": string or null,\n'
                '  "associated_symptoms": [string],\n'
                '  "pertinent_negatives": [string],\n'
                '  "is_sufficient": boolean,\n'
                '  "sufficiency_rationale": string\n'
                "}"
            )
            user_prompt = (
                f"Active Chief Complaint in Encounter: {existing_cc_name or 'None'}\n"
                f"Previous Question Asked to Patient: {previous_question or 'None'}\n"
                f"Current Patient Message: {message}\n"
                f"Current Turn Count: {turn_count}"
            )
            raw = self._call_gemini_json(sys_prompt, user_prompt)
            if not raw or not isinstance(raw, dict):
                return None

            findings: List[ClinicalFinding] = []
            cc = raw.get("chief_complaint") or existing_cc_name
            if cc:
                ev = AttributeEvidence(
                    source_turn_id=turn_count,
                    evidence_text=message,
                    extraction_confidence=0.95,
                )
                ent_id = existing_cc_id if (existing_cc_name and existing_cc_name.lower() == str(cc).lower() and existing_cc_id) else f"ent_gemini_cc_{turn_count}"
                finding = ClinicalFinding(
                    entity_id=ent_id,
                    canonical_name=str(cc).lower(),
                    epistemic_status=EpistemicStatus.REPORTED,
                    verbatim_patient_term=str(cc),
                    status_evidence=ev,
                )
                if raw.get("duration"):
                    finding.duration = VersionedAttribute(
                        attribute_name="duration",
                        current_value=str(raw["duration"]),
                        evidence=ev,
                    )
                if raw.get("severity"):
                    finding.severity = VersionedAttribute(
                        attribute_name="severity",
                        current_value=str(raw["severity"]),
                        evidence=ev,
                    )
                if raw.get("location"):
                    finding.anatomical_site = VersionedAttribute(
                        attribute_name="anatomical_site",
                        current_value=str(raw["location"]),
                        evidence=ev,
                    )
                if raw.get("character"):
                    finding.character = VersionedAttribute(
                        attribute_name="character",
                        current_value=str(raw["character"]),
                        evidence=ev,
                    )
                findings.append(finding)

            if raw.get("past_history"):
                ev = AttributeEvidence(
                    source_turn_id=turn_count,
                    evidence_text=message,
                    extraction_confidence=0.9,
                )
                findings.append(ClinicalFinding(
                    entity_id=f"ent_gemini_pmh_{turn_count}",
                    canonical_name="past occurrence",
                    epistemic_status=EpistemicStatus.REPORTED,
                    verbatim_patient_term=str(raw["past_history"]),
                    status_evidence=ev,
                ))

            for sym in raw.get("associated_symptoms") or []:
                if str(sym).strip():
                    ev = AttributeEvidence(
                        source_turn_id=turn_count,
                        evidence_text=str(sym),
                        extraction_confidence=0.9,
                    )
                    findings.append(ClinicalFinding(
                        entity_id=f"ent_gemini_assoc_{turn_count}_{len(findings)}",
                        canonical_name=str(sym).lower(),
                        epistemic_status=EpistemicStatus.REPORTED,
                        verbatim_patient_term=str(sym),
                        status_evidence=ev,
                    ))

            for neg in raw.get("pertinent_negatives") or []:
                if str(neg).strip():
                    ev = AttributeEvidence(
                        source_turn_id=turn_count,
                        evidence_text=str(neg),
                        extraction_confidence=0.95,
                    )
                    findings.append(ClinicalFinding(
                        entity_id=f"ent_gemini_neg_{turn_count}_{len(findings)}",
                        canonical_name=str(neg).lower(),
                        epistemic_status=EpistemicStatus.DENIED,
                        verbatim_patient_term=str(neg),
                        status_evidence=ev,
                    ))

            return ClinicalDelta(
                turn_id=turn_count,
                extracted_findings=findings,
                supersessions=[],
                unresolved_clarifications=[],
                llm_sufficiency_recommendation=bool(raw.get("is_sufficient", False)),
                sufficiency_rationale=str(raw.get("sufficiency_rationale", "Gemini cognitive extraction")),
            )
        except Exception as e:
            logger.warning(f"Gemini extract_clinical_delta failed: {e}")
            return None






def _deterministic_adaptive_turn(current_message: str, current_state: dict) -> AdaptiveIntakeResult:
    """Deterministic offline fallback for adaptive intake turns."""
    from app.nodes import (
        _fallback_extract_information,
        _canonicalize_chief_complaint,
        _sanitize_associated_symptoms,
        _extract_duration,
        _extract_severity,
        _extract_location,
        _extract_pain_nature,
        _has_trauma_context,
    )
    import re
    msg = (current_message or "").strip()
    msg_lower = msg.lower()
    existing_cc = current_state.get("chief_complaint")
    existing_assoc = list(current_state.get("associated_symptoms") or [])
    existing_negs = list(current_state.get("pertinent_negatives") or [])
    questions_asked = list(current_state.get("questions_asked") or [])
    prev_q = (current_state.get("conversation_message") or "").lower()
    existing_past_hist = current_state.get("past_history_notes")
    existing_add_notes = current_state.get("additional_patient_notes")

    extracted = _fallback_extract_information(msg, prev_q)

    # 1. Chief complaint resolution
    cc = existing_cc or extracted.get("chief_complaint")
    if not cc and msg:
        cc = _canonicalize_chief_complaint(msg)

    # 2. Associated symptoms & Pertinent negatives extraction
    new_symptoms = list(extracted.get("associated_symptoms") or [])
    common_symptoms = [
        "fever", "cough", "headache", "cold", "shivering", "chills", "nausea",
        "vomiting", "dizziness", "fatigue", "weakness", "body pain", "body ache",
        "shortness of breath", "chest pain", "stomach pain", "sore throat", "rash"
    ]
    for sym in common_symptoms:
        if sym in msg_lower:
            if re.search(rf"\b(?:no|not having|don't have|without|denies)\s+{sym}\b", msg_lower):
                if sym not in existing_negs:
                    existing_negs.append(f"denies {sym}")
            elif not cc or sym.lower() not in cc.lower():
                new_symptoms.append(sym)

    combined_assoc = _sanitize_associated_symptoms(existing_assoc + new_symptoms)

    # 3. Descriptors
    dur = _extract_duration(extracted.get("duration") or "") or current_state.get("duration") or _extract_duration(msg)
    sev = _extract_severity(extracted.get("severity") or "") or current_state.get("severity") or _extract_severity(msg)
    loc = extracted.get("location") or current_state.get("location") or _extract_location(msg)
    nat = extracted.get("nature_of_pain") or current_state.get("nature_of_pain") or _extract_pain_nature(msg)

    # Smart synthesis if chief complaint is generic 'pain' or None but location is known
    if (not cc or cc.lower() in {"pain", "discomfort"}) and loc:
        has_trauma = _has_trauma_context(msg) or _has_trauma_context(loc)
        if "head" in loc.lower():
            cc = "head injury" if has_trauma else "headache"
        elif "chest" in loc.lower():
            cc = "chest injury" if has_trauma else "chest pain"
        elif any(ab in loc.lower() for ab in ["abdomen", "stomach"]):
            cc = "abdominal pain"
        elif "knee" in loc.lower():
            cc = f"{loc.lower()} injury" if has_trauma else f"{loc.lower()} pain"

    # 4. Past history / previous occurrences extraction
    past_hist = existing_past_hist
    past_indicators = [
        "first time", "never had", "had this before", "had a similar", "in the past",
        "months ago", "weeks ago", "years ago", "recurrent", "history of", "happened before"
    ]
    if any(ind in msg_lower for ind in past_indicators) or any(q_kw in prev_q for q_kw in ["before", "first time", "experienced this"]):
        past_hist = msg

    # 5. Open floor / additional notes extraction
    add_notes = existing_add_notes
    is_open_floor_prompt = any(phrase in prev_q for phrase in ["any other things", "describe to me", "anything else you want to describe"])
    if is_open_floor_prompt:
        if not any(term in msg_lower for term in ["nothing else", "no other", "that's all", "that is all", "that is everything", "nope", "nothing", "no"]):
            add_notes = msg

    # 6. Clinical Stage Progression & Question Formulation
    turn_count = len(questions_asked)
    is_complete = False
    question = None
    stage = "symptom_exploration"

    # If open floor was already asked, or if 4 turns reached:
    if is_open_floor_prompt or turn_count >= 4:
        is_complete = True
        stage = "complete"
        question = (
            "Thank you. Your clinical intake and assessment are complete. "
            "I have organized your details into a clinical summary for the doctor. "
            "If there are any other things you want to describe to me as you wait, please feel free to go on with that."
        )
    elif not dur:
        stage = "symptom_exploration"
        question = f"When did your {cc.lower() if cc else 'symptoms'} first start?"
    elif not sev:
        stage = "symptom_exploration"
        question = f"How severe would you describe your {cc.lower() if cc else 'discomfort'} (mild, moderate, or severe), and are you experiencing any other symptoms?"
    elif not past_hist:
        stage = "past_history"
        question = f"Have you ever experienced this kind of {cc.lower() if cc else 'pain'} before, or is this the first time?"
    else:
        stage = "open_floor"
        question = "Thank you. I have recorded your symptoms and history. If there are any other things you want to describe to me, please go on with that."

    return AdaptiveIntakeResult(
        chief_complaint=cc,
        associated_symptoms=combined_assoc,
        pertinent_negatives=existing_negs,
        duration=dur,
        severity=sev,
        location=loc,
        nature_of_pain=nat,
        past_history=past_hist,
        additional_notes=add_notes,
        intake_stage=stage,
        is_complete=is_complete,
        adaptive_question=question,
    )


class DeterministicFallbackAdapter:
    """
    Pure zero-LLM deterministic adapter for fast offline testing and fallback execution.
    """

    def is_available(self) -> bool:
        return True

    def extract_intake(self, message: str, previous_question: Optional[str] = None) -> IntakeResult:
        if not (message or "").strip():
            return IntakeResult()
        from app.nodes import _fallback_extract_information
        raw_dict = _fallback_extract_information(message, previous_question or "")
        return IntakeResult(**raw_dict)

    def conduct_adaptive_turn(
        self,
        current_message: str,
        conversation_history: list[dict],
        current_state: dict,
    ) -> AdaptiveIntakeResult:
        return _deterministic_adaptive_turn(current_message, current_state)

    def generate_next_question(
        self,
        current_message: str,
        known_info: dict,
        missing_info: list[str],
        target_field: str,
        previous_question: Optional[str] = None,
    ) -> Optional[str]:
        return None

    def extract_clinical_delta(
        self,
        message: str,
        history_dict: dict,
        turn_count: int,
        previous_question: Optional[str] = None,
    ) -> Optional[Any]:
        return None


def get_default_adapter() -> LLMAdapter:
    """
    Resolve and instantiate the configured default LLM adapter based on environment variables:
    1. If LLM_PROVIDER is 'gemini' (or unset, but GEMINI_API_KEY is present) -> GeminiAdapter
    2. If LLM_PROVIDER is 'deterministic' -> DeterministicFallbackAdapter
    3. If LLM_PROVIDER is 'ollama' -> OllamaAdapter
    """
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if provider == "gemini" or (not provider and gemini_key):
        logger.info("Initializing GeminiAdapter as active clinical brain LLM provider.")
        return GeminiAdapter()
    elif provider == "deterministic":
        logger.info("Initializing DeterministicFallbackAdapter as active provider.")
        return DeterministicFallbackAdapter()
    else:
        logger.info("Initializing OllamaAdapter as active clinical brain LLM provider.")
        return OllamaAdapter()


# Global adapter instance registry initialized with configured default provider
_CURRENT_ADAPTER: LLMAdapter = get_default_adapter()


def get_llm_adapter() -> LLMAdapter:
    """Get the active LLM adapter instance."""
    global _CURRENT_ADAPTER
    return _CURRENT_ADAPTER


def set_llm_adapter(adapter: LLMAdapter) -> None:
    """Set the active LLM adapter instance (useful for testing or switching backends)."""
    global _CURRENT_ADAPTER
    _CURRENT_ADAPTER = adapter


def reset_llm_adapter() -> None:
    """Reset the LLM adapter to the configured default provider."""
    global _CURRENT_ADAPTER
    _CURRENT_ADAPTER = get_default_adapter()


def get_active_provider_info() -> Dict[str, Any]:
    """
    Get metadata about the currently active LLM adapter for health checks, telemetry, and observability.
    Returns provider name, model, cloud status, and availability.
    """
    adapter = get_llm_adapter()
    if isinstance(adapter, GeminiAdapter):
        return {
            "provider": "gemini",
            "model": adapter.model_name,
            "cloud": True,
            "available": adapter.is_available(),
        }
    elif isinstance(adapter, OllamaAdapter):
        return {
            "provider": "ollama",
            "model": adapter.model_name,
            "cloud": False,
            "available": adapter.is_available(),
        }
    elif isinstance(adapter, DeterministicFallbackAdapter):
        return {
            "provider": "deterministic",
            "model": "rule-based",
            "cloud": False,
            "available": True,
        }
    return {
        "provider": getattr(adapter, "provider", "custom"),
        "model": getattr(adapter, "model_name", "unknown"),
        "cloud": False,
        "available": adapter.is_available() if hasattr(adapter, "is_available") else True,
    }

