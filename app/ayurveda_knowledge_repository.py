"""
Phase 8B: Controlled Ayurveda Knowledge Repository.

Loads and serves verified, source-grounded Ayurveda records from
knowledge/ayurveda/ingested_records.json and metadata.json.

ZERO synthetic/invented medical facts. 100% Pydantic v2 validated.
"""

import json
import os
from typing import Optional

from app.ayurveda_knowledge_schema import (
    AyurvedaKnowledgeRecord,
    AuthorityLevel,
    RecordType,
)


class AyurvedaKnowledgeRepository:
    """In-memory repository managing verified Ayurveda records with provenance."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "knowledge", "ayurveda", "ingested_records.json")
        self.data_path = data_path
        self._records: dict[str, AyurvedaKnowledgeRecord] = {}
        self._records_by_source: dict[str, list[AyurvedaKnowledgeRecord]] = {}
        self._load_records()

    def _load_records(self) -> None:
        if not os.path.exists(self.data_path):
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        source_groups = raw_data.get("source_records", {})
        for source_id, records in source_groups.items():
            self._records_by_source[source_id] = []
            for item in records:
                try:
                    rec = AyurvedaKnowledgeRecord(**item)
                    self._records[rec.record_id] = rec
                    self._records_by_source[source_id].append(rec)
                except Exception as e:
                    print(f"Warning: Failed to parse record {item.get('record_id')}: {e}")

    def get_record(self, record_id: str) -> Optional[AyurvedaKnowledgeRecord]:
        """Retrieve record by unique record ID."""
        return self._records.get(record_id)

    def get_all_records(self) -> list[AyurvedaKnowledgeRecord]:
        """Return all loaded records."""
        return list(self._records.values())

    def get_records_by_source(self, source_id: str) -> list[AyurvedaKnowledgeRecord]:
        """Return records originating from a specific approved source."""
        return list(self._records_by_source.get(source_id, []))

    def get_records_by_authority(self, authority: AuthorityLevel) -> list[AyurvedaKnowledgeRecord]:
        """Filter records by authority level (primary_official vs secondary)."""
        return [r for r in self._records.values() if r.authority_level == authority]

    def get_records_by_type(self, record_type: RecordType) -> list[AyurvedaKnowledgeRecord]:
        """Filter records by record type."""
        return [r for r in self._records.values() if r.record_type == record_type]

    def count_by_source(self) -> dict[str, int]:
        """Return record count per source."""
        return {src: len(recs) for src, recs in self._records_by_source.items()}


# Global singleton instance
_GLOBAL_REPOSITORY = AyurvedaKnowledgeRepository()


def get_ayurveda_repository() -> AyurvedaKnowledgeRepository:
    """Access active knowledge repository."""
    return _GLOBAL_REPOSITORY
