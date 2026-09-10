"""Source adapter interface and normalized result model (PRD FR-06)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SourceResult:
    """Normalized result returned by every source adapter.

    `status` uses SourceStatus; a technical failure must be UNAVAILABLE
    (→ UNVERIFIABLE downstream), never NON_COMPLIANT (PRD §17).
    """
    source: str
    subject_identifier: str
    status: str  # SourceStatus value
    simulated: bool = True
    fields: dict = field(default_factory=dict)
    error: str | None = None
    freshness: str = "MOCK_TODAY"
    queried_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "subject_identifier": self.subject_identifier,
            "status": self.status,
            "simulated": self.simulated,
            "fields": self.fields,
            "error": self.error,
            "freshness": self.freshness,
            "queried_at": self.queried_at,
        }


class SourceAdapter:
    """Interface every official-source adapter implements.

    Real adapters (future) and mock adapters share this exact interface so the
    verification pipeline never needs to know which one it is talking to.
    """

    source_type: str = "BASE"

    def verify(self, identifier: str) -> SourceResult:
        raise NotImplementedError
