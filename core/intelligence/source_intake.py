"""Contracts for sources that are not ready to enter intelligence workflows."""

from dataclasses import dataclass
from enum import StrEnum


class SourceIntakeStatus(StrEnum):
    PENDING_TRANSCRIPT = "pending_transcript"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class PendingLearningSource:
    intake_id: str
    platform: str
    source_uri: str
    external_id: str
    submitted_at: float
    fingerprint: str
    status: SourceIntakeStatus
    blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.intake_id.strip():
            raise ValueError("intake_id is required.")
        if not self.platform.strip():
            raise ValueError("platform is required.")
        if not self.source_uri.startswith("https://"):
            raise ValueError("source_uri must use HTTPS.")
        if not self.external_id.strip():
            raise ValueError("external_id is required.")
        if len(self.fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.fingerprint):
            raise ValueError("fingerprint must be a lowercase SHA-256 hash.")
        if self.status == SourceIntakeStatus.PENDING_TRANSCRIPT and not self.blockers:
            raise ValueError("A pending source requires blockers.")

    @property
    def audit_allowed(self) -> bool:
        return False

    @property
    def learning_allowed(self) -> bool:
        return False

    @property
    def provider_called(self) -> bool:
        return False

    @property
    def estimated_cost(self) -> float:
        return 0.0

