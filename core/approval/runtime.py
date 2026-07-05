"""Deterministic runtime for human approval gates."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any
from uuid import UUID

from core.approval.models import (
    ApprovalDecision,
    ApprovalQueueSnapshot,
    ApprovalRequest,
    ApprovalStatus,
)
from core.events.bus import EventBus
from core.events.domain_events import ApprovalDecided, ApprovalRequested


class ApprovalRuntime:
    """In-memory approval queue used before sensitive execution steps.

    This runtime does not publish, call providers, or decide on its own. It only
    records requests, owner decisions, and releases payloads after approval.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._requests: dict[UUID, ApprovalRequest] = {}
        self._decisions: dict[UUID, ApprovalDecision] = {}

    def request_approval(
        self,
        *,
        title: str,
        preview_text: str,
        payload: dict[str, Any] | None = None,
        requester: str = "system",
        source: str = "content_factory",
        subject_type: str = "publication",
        subject_id: str = "",
        risk_level: str = "medium",
        expires_at: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        if not title.strip():
            raise ValueError("Approval title is required.")
        if not preview_text.strip():
            raise ValueError("Approval preview_text is required.")

        request = ApprovalRequest(
            title=title,
            preview_text=preview_text,
            payload=dict(payload or {}),
            requester=requester,
            source=source,
            subject_type=subject_type,
            subject_id=subject_id,
            risk_level=risk_level,
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )
        self._requests[request.approval_id] = request
        self._publish(ApprovalRequested(
            approval_id=request.approval_id,
            source=request.source,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            risk_level=request.risk_level,
            timestamp=request.created_at,
            metadata=request.public_dict(),
        ))
        return request

    def get(self, approval_id: UUID) -> ApprovalRequest | None:
        request = self._requests.get(approval_id)
        if request is not None:
            request = self._refresh_expiration(request)
        return request

    def require(self, approval_id: UUID) -> ApprovalRequest:
        request = self.get(approval_id)
        if request is None:
            raise KeyError(f"Approval request not found: {approval_id}")
        return request

    def pending(self) -> tuple[ApprovalRequest, ...]:
        self.expire_due()
        return tuple(r for r in self._requests.values() if r.status == ApprovalStatus.PENDING)

    def all_requests(self) -> tuple[ApprovalRequest, ...]:
        self.expire_due()
        return tuple(self._requests.values())

    def approve(
        self,
        approval_id: UUID,
        *,
        decided_by: str,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalDecision:
        return self.decide(
            approval_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            reason=reason or "Approved.",
            metadata=metadata,
        )

    def reject(
        self,
        approval_id: UUID,
        *,
        decided_by: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalDecision:
        if not reason.strip():
            raise ValueError("Rejection reason is required.")
        return self.decide(
            approval_id,
            status=ApprovalStatus.REJECTED,
            decided_by=decided_by,
            reason=reason,
            metadata=metadata,
        )

    def cancel(
        self,
        approval_id: UUID,
        *,
        decided_by: str = "system",
        reason: str = "Cancelled.",
    ) -> ApprovalDecision:
        return self.decide(
            approval_id,
            status=ApprovalStatus.CANCELLED,
            decided_by=decided_by,
            reason=reason,
        )

    def decide(
        self,
        approval_id: UUID,
        *,
        status: ApprovalStatus,
        decided_by: str,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalDecision:
        if status not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED}:
            raise ValueError("Only approved, rejected, or cancelled decisions are manual.")
        if not decided_by.strip():
            raise ValueError("decided_by is required.")

        request = self.require(approval_id)
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request is not pending: {request.status.value}")
        if request.expired():
            self._expire(request)
            raise ValueError("Approval request has expired.")

        decision = ApprovalDecision(
            approval_id=approval_id,
            status=status,
            decided_by=decided_by,
            reason=reason,
            metadata=dict(metadata or {}),
        )
        updated = replace(
            request,
            status=status,
            decided_at=decision.decided_at,
            decided_by=decided_by,
            decision_reason=reason,
        )
        self._requests[approval_id] = updated
        self._decisions[approval_id] = decision
        self._publish_decision(decision, updated)
        return decision

    def is_approved(self, approval_id: UUID) -> bool:
        return self.require(approval_id).status == ApprovalStatus.APPROVED

    def release_payload(self, approval_id: UUID) -> dict[str, Any]:
        request = self.require(approval_id)
        if request.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Approval request is not approved: {request.status.value}")
        return dict(request.payload)

    def expire_due(self, now: float | None = None) -> tuple[ApprovalRequest, ...]:
        current = time.time() if now is None else now
        expired: list[ApprovalRequest] = []
        for request in tuple(self._requests.values()):
            if request.status == ApprovalStatus.PENDING and request.expired(current):
                expired.append(self._expire(request, now=current))
        return tuple(expired)

    def decision_for(self, approval_id: UUID) -> ApprovalDecision | None:
        return self._decisions.get(approval_id)

    def snapshot(self) -> ApprovalQueueSnapshot:
        self.expire_due()
        requests = tuple(self._requests.values())
        latest = requests[-1] if requests else None
        return ApprovalQueueSnapshot(
            total_requests=len(requests),
            pending=sum(1 for r in requests if r.status == ApprovalStatus.PENDING),
            approved=sum(1 for r in requests if r.status == ApprovalStatus.APPROVED),
            rejected=sum(1 for r in requests if r.status == ApprovalStatus.REJECTED),
            expired=sum(1 for r in requests if r.status == ApprovalStatus.EXPIRED),
            cancelled=sum(1 for r in requests if r.status == ApprovalStatus.CANCELLED),
            latest_approval_id=str(latest.approval_id) if latest else "",
            latest_status=latest.status.value if latest else "",
        )

    def _refresh_expiration(self, request: ApprovalRequest) -> ApprovalRequest:
        if request.status == ApprovalStatus.PENDING and request.expired():
            return self._expire(request)
        return request

    def _expire(self, request: ApprovalRequest, now: float | None = None) -> ApprovalRequest:
        decided_at = time.time() if now is None else now
        updated = replace(
            request,
            status=ApprovalStatus.EXPIRED,
            decided_at=decided_at,
            decided_by="system",
            decision_reason="Approval request expired.",
        )
        self._requests[request.approval_id] = updated
        decision = ApprovalDecision(
            approval_id=request.approval_id,
            status=ApprovalStatus.EXPIRED,
            decided_by="system",
            reason="Approval request expired.",
            decided_at=decided_at,
        )
        self._decisions[request.approval_id] = decision
        self._publish_decision(decision, updated)
        return updated

    def _publish_decision(self, decision: ApprovalDecision, request: ApprovalRequest) -> None:
        self._publish(ApprovalDecided(
            approval_id=decision.approval_id,
            status=decision.status.value,
            decided_by=decision.decided_by,
            reason=decision.reason,
            source=request.source,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            timestamp=decision.decided_at,
            metadata={
                "request": request.public_dict(),
                "decision": decision.to_dict(),
            },
        ))

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
