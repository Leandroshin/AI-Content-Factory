"""Content-bound approvals that detect payload changes after review."""

from __future__ import annotations

import json
from typing import Any, Mapping

from core.approval import ApprovalRuntime, ApprovalStatus
from core.intelligence.canonical import canonical_json, content_sha256
from core.intelligence.contracts import BoundApprovalRef


class ApprovalBindingError(ValueError):
    """Raised when approved content no longer matches the reviewed payload."""


def request_bound_approval(
    runtime: ApprovalRuntime,
    *,
    title: str,
    preview_text: str,
    payload: Mapping[str, Any],
    requester: str,
    subject_type: str,
    subject_id: str,
    risk_level: str = "medium",
) -> BoundApprovalRef:
    normalized_payload = json.loads(canonical_json(payload))
    if not isinstance(normalized_payload, dict):
        raise TypeError("Bound approval payload must be a mapping.")
    payload_hash = content_sha256(normalized_payload)
    request = runtime.request_approval(
        title=title,
        preview_text=preview_text,
        payload=normalized_payload,
        requester=requester,
        source="market_intelligence_shadow",
        subject_type=subject_type,
        subject_id=subject_id,
        risk_level=risk_level,
        metadata={
            "binding_version": "1.0",
            "bound_payload_sha256": payload_hash,
            "promotion_allowed": False,
        },
    )
    return BoundApprovalRef(request.approval_id, payload_hash, subject_id)


def verify_bound_approval(runtime: ApprovalRuntime, binding: BoundApprovalRef, expected_payload: Any) -> dict[str, Any]:
    """Release only the exact payload that the owner approved."""
    request = runtime.require(binding.approval_id)
    if request.status != ApprovalStatus.APPROVED:
        raise ApprovalBindingError(f"Approval request is not approved: {request.status.value}")
    metadata_hash = str(request.metadata.get("bound_payload_sha256", ""))
    stored_hash = content_sha256(request.payload)
    expected_hash = content_sha256(expected_payload)
    if metadata_hash != binding.payload_sha256:
        raise ApprovalBindingError("Approval metadata hash does not match the binding.")
    if stored_hash != binding.payload_sha256:
        raise ApprovalBindingError("Stored approval payload changed after review.")
    if expected_hash != binding.payload_sha256:
        raise ApprovalBindingError("Execution payload differs from the approved content.")
    return json.loads(canonical_json(request.payload))
