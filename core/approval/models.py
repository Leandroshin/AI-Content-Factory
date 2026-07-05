"""Human approval models for gated publishing and provider actions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ApprovalStatus(StrEnum):
    """Lifecycle state for a human approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """A single human approval ticket.

    The payload is the private execution payload released only after approval.
    The preview is the safe text shown to the owner for review.
    """

    approval_id: UUID = field(default_factory=uuid4)
    title: str = ""
    preview_text: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    requester: str = "system"
    source: str = "content_factory"
    subject_type: str = "publication"
    subject_id: str = ""
    risk_level: str = "medium"
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    decided_at: float | None = None
    decided_by: str = ""
    decision_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def short_id(self) -> str:
        return str(self.approval_id)[:8]

    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.CANCELLED,
        }

    def expired(self, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at

    def public_dict(self) -> dict[str, Any]:
        """Return safe review metadata without exposing execution payload."""
        return {
            "approval_id": str(self.approval_id),
            "short_id": self.short_id,
            "title": self.title,
            "preview_text": self.preview_text,
            "requester": self.requester,
            "source": self.source,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
            "decision_reason": self.decision_reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """Decision made by the owner or another authorized approver."""

    decision_id: UUID = field(default_factory=uuid4)
    approval_id: UUID = field(default_factory=uuid4)
    status: ApprovalStatus = ApprovalStatus.APPROVED
    decided_by: str = ""
    reason: str = ""
    decided_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": str(self.decision_id),
            "approval_id": str(self.approval_id),
            "status": self.status.value,
            "approved": self.approved,
            "decided_by": self.decided_by,
            "reason": self.reason,
            "decided_at": self.decided_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ApprovalQueueSnapshot:
    """Compact approval queue metrics for dashboards and demos."""

    total_requests: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    expired: int = 0
    cancelled: int = 0
    latest_approval_id: str = ""
    latest_status: str = ""

    @property
    def terminal(self) -> int:
        return self.approved + self.rejected + self.expired + self.cancelled
