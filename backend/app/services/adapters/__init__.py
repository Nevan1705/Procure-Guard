"""Mock source adapters sharing one normalized interface (PRD FR-06, §16).

Every response is flagged simulated=True.

Semantics (PRD FR-06 critical rule + §17):
- Dataset file missing entirely (integration not configured) ⇒ UNAVAILABLE
  → downstream UNVERIFIABLE, never NON_COMPLIANT and never VERIFIED.
- Dataset entry marked `_unavailable` (simulated outage) ⇒ UNAVAILABLE.
- Identifier absent from a configured registry ⇒ NOT_FOUND (a real answer,
  which rules may treat as NON_COMPLIANT where absence is not the pass condition).
"""
import json
import os

from app.core.config import MOCK_DATA_DIR
from app.core.enums import SourceStatus, SourceType
from app.services.adapters.base import SourceAdapter, SourceResult


def _dataset_path(source: SourceType) -> str:
    return os.path.join(MOCK_DATA_DIR, f"{source.value.lower()}.json")


def _load_dataset(source: SourceType) -> dict | None:
    """Return the registry dict, or None when no dataset is configured."""
    path = _dataset_path(source)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


class MockSourceAdapter(SourceAdapter):
    """Deterministic JSON-file-backed mock adapter."""

    def __init__(self, source_type: SourceType):
        self.source_type = source_type
        self._dataset = _load_dataset(source_type)

    def verify(self, identifier: str) -> SourceResult:
        identifier = (identifier or "").strip().upper()

        if self._dataset is None:
            # Missing integration must yield Unverifiable, not Verified (PRD FR-06).
            return SourceResult(
                source=self.source_type.value,
                subject_identifier=identifier,
                status=SourceStatus.UNAVAILABLE.value,
                fields={},
                error=(f"{self.source_type.value} registry is not configured in this "
                       f"prototype; verification is not possible."),
            )

        entry = self._dataset.get(identifier)

        if entry is None:
            return SourceResult(
                source=self.source_type.value,
                subject_identifier=identifier,
                status=SourceStatus.NOT_FOUND.value,
                fields={},
                error="Identifier not present in mock registry",
            )

        if entry.get("_unavailable"):
            return SourceResult(
                source=self.source_type.value,
                subject_identifier=identifier,
                status=SourceStatus.UNAVAILABLE.value,
                fields={},
                error=entry.get("reason", "Source unavailable"),
            )

        return SourceResult(
            source=self.source_type.value,
            subject_identifier=identifier,
            status=entry.get("status", SourceStatus.NOT_FOUND.value),
            fields={k: v for k, v in entry.items() if not k.startswith("_")},
            error=None,
        )


def get_adapter(source_type: SourceType) -> SourceAdapter:
    """Adapter factory. Real adapters plug in here behind the same interface."""
    return MockSourceAdapter(source_type)


# Sources with datasets in this prototype (mock playground exposes these).
ADAPTER_SOURCES = [SourceType.GST, SourceType.UDYAM, SourceType.MCA, SourceType.OEM]
