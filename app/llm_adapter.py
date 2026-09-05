"""
Phase 8A: LLM Adapter Abstraction Layer.

Decouples clinical intake reasoning from specific LLM providers.
Provides a clean protocol and concrete OllamaAdapter wrapping the existing
local Llama 3 model with deterministic fallback.

ZERO new cloud SDKs. Fully backward-compatible.
"""

from typing import Optional, Protocol
from urllib.request import urlopen

from langchain_ollama import ChatOllama
from app.schemas import IntakeResult


class LLMAdapter(Protocol):
    """Protocol for clinical language extraction adapters."""

    def extract_intake(self, message: str, previous_question: Optional[str] = None) -> IntakeResult:
        """Extract structured intake fields from patient message."""
        ...

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available."""
        ...


class OllamaAdapter:
    """
    Adapter wrapping the existing local Ollama (Llama 3) implementation.
    """

    def __init__(self, model_name: str = "llama3:latest", endpoint: str = "http://localhost:11434"):
        self.model_name = model_name
        self.endpoint = endpoint
        self._model = ChatOllama(
            model=model_name,
            temperature=0,
            format="json"
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


# Global adapter instance registry
_CURRENT_ADAPTER: LLMAdapter = OllamaAdapter()


def get_llm_adapter() -> LLMAdapter:
    """Get the active LLM adapter instance."""
    global _CURRENT_ADAPTER
    return _CURRENT_ADAPTER


def set_llm_adapter(adapter: LLMAdapter) -> None:
    """Set the active LLM adapter instance (useful for testing or switching backends)."""
    global _CURRENT_ADAPTER
    _CURRENT_ADAPTER = adapter


def reset_llm_adapter() -> None:
    """Reset the LLM adapter to the default OllamaAdapter."""
    global _CURRENT_ADAPTER
    _CURRENT_ADAPTER = OllamaAdapter()
