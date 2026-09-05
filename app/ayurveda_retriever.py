"""
Phase 8B: Deterministic Ayurveda Knowledge Retrieval Layer.

Matches patient clinical presentation against verified knowledge records from
the 3 approved sources, enforcing strict source authority hierarchy:
    Primary Official (API-II, CCRAS) > Secondary Literature (eCAM).

ZERO vector database dependencies. 100% Deterministic and Auditable.
"""

from typing import Protocol, Optional
import re

from app.ayurveda_knowledge_schema import (
    AyurvedaKnowledgeRecord,
    AyurvedaMatchCandidate,
    AuthorityLevel,
    RecordType,
)
from app.ayurveda_knowledge_repository import (
    AyurvedaKnowledgeRepository,
    get_ayurveda_repository,
)


class AyurvedaRetriever(Protocol):
    """Protocol for Ayurveda knowledge retrieval."""

    def retrieve_candidates(
        self,
        chief_complaint: Optional[str] = None,
        symptoms: Optional[list[str]] = None,
        limit: int = 5
    ) -> list[AyurvedaMatchCandidate]:
        """Retrieve and rank relevant approved Ayurveda records for clinical presentation."""
        ...


class DeterministicAyurvedaRetriever:
    """
    Deterministic keyword and indication matcher with source-authority weighting.
    """

    def __init__(self, repository: Optional[AyurvedaKnowledgeRepository] = None):
        self.repository = repository or get_ayurveda_repository()

    def _normalize_term(self, text: str) -> str:
        """Normalize query term for matching."""
        if not text:
            return ""
        # Remove non-alphanumeric except whitespace
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        return " ".join(cleaned.split())

    def _calculate_match(
        self,
        query_terms: list[str],
        record: AyurvedaKnowledgeRecord
    ) -> Optional[tuple[str, str, float]]:
        """
        Calculates match between patient query terms and a knowledge record.
        Returns: (matched_symptom, match_strength, base_score) or None.
        """
        # Normalize record indication strings
        record_indications = [self._normalize_term(ind) for ind in record.traditional_indications]
        record_names = [self._normalize_term(record.name)] + [self._normalize_term(a) for a in record.aliases]

        best_match_symptom = None
        best_match_strength = None
        highest_base_score = 0.0

        for term in query_terms:
            if not term or len(term) < 2:
                continue

            # 1. Exact or substring match in traditional indications
            for ind in record_indications:
                if term == ind or (len(term) >= 4 and (term in ind or ind in term)):
                    score = 8.0 if term == ind else 5.0
                    if score > highest_base_score:
                        highest_base_score = score
                        best_match_symptom = term
                        best_match_strength = "direct_indication"

            # 2. Match in plant/remedy names or aliases
            for name_alias in record_names:
                if term == name_alias or (len(term) >= 4 and term in name_alias):
                    score = 4.0
                    if score > highest_base_score:
                        highest_base_score = score
                        best_match_symptom = term
                        best_match_strength = "alias_match"

        if highest_base_score > 0 and best_match_symptom and best_match_strength:
            # Special case for secondary literature
            if record.authority_level == AuthorityLevel.SECONDARY:
                best_match_strength = "secondary_evidence"
            return (best_match_symptom, best_match_strength, highest_base_score)

        return None

    def retrieve_candidates(
        self,
        chief_complaint: Optional[str] = None,
        symptoms: Optional[list[str]] = None,
        limit: int = 5
    ) -> list[AyurvedaMatchCandidate]:
        """
        Retrieve candidate records matching clinical symptoms.
        Enforces: Primary Official > Secondary Literature.
        """
        all_terms: list[str] = []
        if chief_complaint:
            norm_cc = self._normalize_term(chief_complaint)
            all_terms.append(norm_cc)
            # Add subwords if compound (e.g., 'stomach pain' -> 'stomach', 'pain')
            all_terms.extend(norm_cc.split())

        for sym in symptoms or []:
            norm_sym = self._normalize_term(sym)
            if norm_sym:
                all_terms.append(norm_sym)
                all_terms.extend(norm_sym.split())

        # Deduplicate terms
        unique_terms = list(dict.fromkeys([t for t in all_terms if len(t) >= 3]))

        if not unique_terms:
            return []

        candidates: list[AyurvedaMatchCandidate] = []
        for record in self.repository.get_all_records():
            match_res = self._calculate_match(unique_terms, record)
            if match_res:
                matched_sym, match_strength, base_score = match_res

                # Authority hierarchy bonus:
                # Primary Official gets +100.0, Secondary gets +10.0
                # Official sources ALWAYS outrank secondary regardless of keyword overlap
                authority_bonus = 100.0 if record.authority_level == AuthorityLevel.PRIMARY_OFFICIAL else 10.0
                rank_score = authority_bonus + base_score

                candidates.append(
                    AyurvedaMatchCandidate(
                        record=record,
                        matched_symptom=matched_sym,
                        match_strength=match_strength,
                        rank_score=rank_score,
                    )
                )

        # Sort descending by rank_score
        candidates.sort(key=lambda c: c.rank_score, reverse=True)
        return candidates[:limit]


# Global singleton retriever instance
_GLOBAL_RETRIEVER = DeterministicAyurvedaRetriever()


def get_ayurveda_retriever() -> AyurvedaRetriever:
    """Access active Ayurveda retriever."""
    return _GLOBAL_RETRIEVER

