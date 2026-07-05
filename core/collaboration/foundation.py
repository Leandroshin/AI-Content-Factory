"""Collaboration Runtime Foundation.

Stateless, deterministic collaboration between employees.
No AI, no IO, no async, no threads — pure request/response orchestration.

Flow: create_request → add_participants → send_request →
      simulate_responses → consolidate → build_result
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.events.domain_events import (
    CollaborationCompleted,
    CollaborationStarted,
    ParticipantResponded,
)


# ------------------------------------------------------------------
# CollaborationParticipant
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationParticipant:
    """A participant in a collaboration session.

    Attributes:
        participant_id: Unique identifier.
        name: Human-readable name.
        role: Functional role (e.g. "senior", "junior", "manager", "lead").
        department: Department the participant belongs to.
        metadata: Optional extra data.
    """

    participant_id: UUID
    name: str
    role: str = "member"
    department: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        name: str,
        role: str = "member",
        department: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationParticipant:
        """Factory that auto-generates participant_id."""
        return CollaborationParticipant(
            participant_id=uuid4(),
            name=name,
            role=role,
            department=department,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# CollaborationRequest
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationRequest:
    """A request for collaboration sent by an employee.

    Attributes:
        request_id: Unique identifier.
        title: Short title of the collaboration.
        description: Detailed description of what is needed.
        sender_id: The employee who created the request.
        created_at: Unix timestamp of creation.
        metadata: Optional extra data.
    """

    request_id: UUID
    title: str
    description: str = ""
    sender_id: UUID | None = None
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        title: str,
        description: str = "",
        sender_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationRequest:
        """Factory that auto-generates request_id and timestamp."""
        return CollaborationRequest(
            request_id=uuid4(),
            title=title,
            description=description,
            sender_id=sender_id,
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        title: str,
        created_at: float,
        description: str = "",
        sender_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationRequest:
        """Factory with explicit timestamp (for determinism in tests)."""
        return CollaborationRequest(
            request_id=uuid4(),
            title=title,
            description=description,
            sender_id=sender_id,
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# CollaborationResponse
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationResponse:
    """A response from a participant to a collaboration request.

    Attributes:
        response_id: Unique identifier.
        request_id: The request this responds to.
        participant_id: The participant who responded.
        content: Response content/message.
        decision: Decision ("approved", "rejected", "needs_info", "abstained").
        created_at: Unix timestamp.
        metadata: Optional extra data.
    """

    response_id: UUID
    request_id: UUID
    participant_id: UUID
    content: str = ""
    decision: str = "approved"
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        request_id: UUID,
        participant_id: UUID,
        content: str = "",
        decision: str = "approved",
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationResponse:
        """Factory that auto-generates response_id and timestamp."""
        return CollaborationResponse(
            response_id=uuid4(),
            request_id=request_id,
            participant_id=participant_id,
            content=content,
            decision=decision,
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        request_id: UUID,
        participant_id: UUID,
        created_at: float,
        content: str = "",
        decision: str = "approved",
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationResponse:
        """Factory with explicit timestamp (for determinism in tests)."""
        return CollaborationResponse(
            response_id=uuid4(),
            request_id=request_id,
            participant_id=participant_id,
            content=content,
            decision=decision,
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# CollaborationSession
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationSession:
    """A collaboration session linking a request to participants and responses.

    Attributes:
        session_id: Unique identifier.
        request: The collaboration request.
        participants: Participants involved in the session.
        responses: Responses received so far.
        status: Current status ("pending", "active", "completed", "cancelled").
        created_at: Unix timestamp.
        metadata: Optional extra data.
    """

    session_id: UUID
    request: CollaborationRequest
    participants: tuple[CollaborationParticipant, ...] = ()
    responses: tuple[CollaborationResponse, ...] = ()
    status: str = "pending"
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        request: CollaborationRequest,
        participants: tuple[CollaborationParticipant, ...]
        | list[CollaborationParticipant]
        | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationSession:
        """Factory that auto-generates session_id and timestamp."""
        return CollaborationSession(
            session_id=uuid4(),
            request=request,
            participants=tuple(participants) if participants else (),
            status="pending",
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        request: CollaborationRequest,
        created_at: float,
        participants: tuple[CollaborationParticipant, ...]
        | list[CollaborationParticipant]
        | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationSession:
        """Factory with explicit timestamp (for determinism in tests)."""
        return CollaborationSession(
            session_id=uuid4(),
            request=request,
            participants=tuple(participants) if participants else (),
            status="pending",
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# CollaborationContext
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationContext:
    """Context for a collaboration operation.

    Attributes:
        task_id: Optional associated task.
        task_name: Human-readable task name.
        sender_id: The employee requesting collaboration.
        department: Department context.
        urgency: Urgency level ("low", "medium", "high", "critical").
        metadata: Optional extra data.
    """

    task_id: UUID | None = None
    task_name: str = ""
    sender_id: UUID | None = None
    department: str = "general"
    urgency: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        task_name: str = "",
        sender_id: UUID | None = None,
        department: str = "general",
        urgency: str = "medium",
        task_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationContext:
        """Factory that auto-generates task_id if not provided."""
        return CollaborationContext(
            task_id=task_id or uuid4(),
            task_name=task_name,
            sender_id=sender_id,
            department=department,
            urgency=urgency,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# CollaborationTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationTrace:
    """Execution trace for a collaboration cycle.

    Attributes:
        stages: Ordered stage names that were executed.
        requests_sent: Number of requests created.
        responses_received: Number of responses received.
        participants_count: Number of participants.
        approvals: Number of "approved" decisions.
        rejections: Number of "rejected" decisions.
        abstentions: Number of "abstained" decisions.
        needs_info_count: Number of "needs_info" decisions.
        consensus: The final consensus ("unanimous", "majority", "tie",
                   "no_consensus").
        timestamps: Dict mapping stage name to Unix timestamp.
    """

    stages: tuple[str, ...] = ()
    requests_sent: int = 0
    responses_received: int = 0
    participants_count: int = 0
    approvals: int = 0
    rejections: int = 0
    abstentions: int = 0
    needs_info_count: int = 0
    consensus: str = ""
    timestamps: dict[str, float] = field(default_factory=dict)


# ------------------------------------------------------------------
# CollaborationResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CollaborationResult:
    """Outcome of a collaboration cycle.

    Attributes:
        success: True if the cycle completed without errors.
        session: The collaboration session (None if setup failed).
        context: The collaboration context used.
        trace: Execution trace with metrics and timing.
        consolidated_response: The final consolidated response.
        consensus: The final consensus reached.
        error_message: Human-readable error (empty on success).
    """

    success: bool
    session: CollaborationSession | None = None
    context: CollaborationContext | None = None
    trace: CollaborationTrace | None = None
    consolidated_response: CollaborationResponse | None = None
    consensus: str = ""
    error_message: str = ""


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _determine_decision(
    participant: CollaborationParticipant,
    title: str,
    description: str,
    urgency: str = "medium",
) -> tuple[str, str]:
    """Deterministically simulate a participant's decision.

    Rules:
    - "senior" role → approved, supportive content.
    - "junior" role → approved, deferring content.
    - "manager" role → approved if urgent != "critical", else needs_info.
    - "lead" role → rejected if "complex" in title/desc, else approved.
    - Default "member" → approved with neutral content.
    """
    combined = f"{title} {description}".lower()
    content_templates = {
        "senior": "Approved. I support this initiative and will contribute accordingly.",
        "junior": "Approved. I will follow the lead of more experienced team members.",
        "manager": "Requesting additional information before final approval.",
        "lead": "I have concerns about this approach and cannot approve in its current form.",
        "member": "Acknowledged and approved. Happy to collaborate.",
    }
    default_content = "Approved. No additional comments."

    if participant.role == "senior":
        return "approved", content_templates["senior"]

    if participant.role == "junior":
        return "approved", content_templates["junior"]

    if participant.role == "manager":
        if "critical" in combined or urgency == "critical":
            return "needs_info", content_templates["manager"]
        return "approved", "Approved. The plan looks reasonable."

    if participant.role == "lead":
        if any(kw in combined for kw in ["complex", "risky", "restructure"]):
            return "rejected", content_templates["lead"]
        if "critical" in combined or urgency == "critical":
            return "needs_info", "I need more details on the timeline and resources."
        return "approved", "Approved. Proceed as planned."

    if participant.role == "observer":
        return "abstained", "Abstained. I have no input on this matter."

    if participant.role == "member":
        return "approved", content_templates["member"]

    return "approved", default_content


def _calculate_consensus(responses: tuple[CollaborationResponse, ...]) -> str:
    """Calculate consensus from a set of responses."""
    if not responses:
        return "no_consensus"

    approved = sum(1 for r in responses if r.decision == "approved")
    rejected = sum(1 for r in responses if r.decision == "rejected")
    needs_info = sum(1 for r in responses if r.decision == "needs_info")
    abstained = sum(1 for r in responses if r.decision == "abstained")
    total = len(responses)

    if approved == total:
        return "unanimous"
    if approved > total / 2:
        return "majority"
    if approved == rejected and approved > 0 and rejected > 0:
        return "tie"
    if rejected >= total / 2:
        return "rejected"
    if needs_info > 0 and approved + rejected == 0:
        return "needs_info"
    return "no_consensus"


# ------------------------------------------------------------------
# CollaborationRuntime
# ------------------------------------------------------------------


class CollaborationRuntime:
    """Stateless runtime for collaboration between employees.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    # ------------------------------------------------------------------
    # Pipeline: create_request
    # ------------------------------------------------------------------

    @staticmethod
    def create_request(
        title: str,
        description: str = "",
        sender_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationRequest:
        """Create a new collaboration request.

        Args:
            title: Short title of the collaboration.
            description: Detailed description.
            sender_id: The employee creating the request.
            metadata: Optional extra metadata.

        Returns:
            A new CollaborationRequest.
        """
        return CollaborationRequest.create(
            title=title,
            description=description,
            sender_id=sender_id,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Pipeline: add_participants
    # ------------------------------------------------------------------

    @staticmethod
    def add_participants(
        request: CollaborationRequest,
        participants: tuple[CollaborationParticipant, ...]
        | list[CollaborationParticipant],
        metadata: dict[str, Any] | None = None,
    ) -> CollaborationSession:
        """Create a session with participants for a request.

        Args:
            request: The collaboration request.
            participants: Participants to include.
            metadata: Optional session-level metadata.

        Returns:
            A new CollaborationSession in "pending" status.
        """
        merged_meta = dict(metadata) if metadata else {}
        merged_meta["title"] = request.title
        return CollaborationSession.create(
            request=request,
            participants=tuple(participants),
            metadata=merged_meta,
        )

    # ------------------------------------------------------------------
    # Pipeline: send_request
    # ------------------------------------------------------------------

    @staticmethod
    def send_request(
        session: CollaborationSession,
        context: CollaborationContext | None = None,
    ) -> CollaborationSession:
        """Transition a session from "pending" to "active".

        Args:
            session: The current session.
            context: Optional collaboration context.

        Returns:
            A new session with status "active".
        """
        meta = dict(session.metadata)
        if context is not None:
            meta["urgency"] = context.urgency
            meta["department"] = context.department
        return CollaborationSession(
            session_id=session.session_id,
            request=session.request,
            participants=session.participants,
            responses=session.responses,
            status="active",
            created_at=session.created_at,
            metadata=meta,
        )

    # ------------------------------------------------------------------
    # Pipeline: simulate_responses
    # ------------------------------------------------------------------

    @staticmethod
    def simulate_responses(
        session: CollaborationSession,
        context: CollaborationContext | None = None,
        response_decisions: list[str] | None = None,
        response_contents: list[str] | None = None,
    ) -> tuple[CollaborationResponse, ...]:
        """Simulate deterministic responses from all participants.

        Uses role-based rules to generate responses. Can be overridden
        with explicit decisions and contents for testing.

        Args:
            session: The active collaboration session.
            context: Optional context with urgency info.
            response_decisions: Optional explicit decisions per participant.
            response_contents: Optional explicit contents per participant.

        Returns:
            A tuple of CollaborationResponse, one per participant.
        """
        title = session.request.title
        description = session.request.description
        urgency = context.urgency if context else "medium"
        responses: list[CollaborationResponse] = []

        for i, participant in enumerate(session.participants):
            if response_decisions is not None and i < len(response_decisions):
                decision = response_decisions[i]
            else:
                decision, _ = _determine_decision(participant, title, description, urgency)

            if response_contents is not None and i < len(response_contents):
                content = response_contents[i]
            else:
                _, generated_content = _determine_decision(participant, title, description, urgency)
                content = generated_content

            resp = CollaborationResponse.create(
                request_id=session.request.request_id,
                participant_id=participant.participant_id,
                content=content,
                decision=decision,
                metadata={"role": participant.role},
            )
            responses.append(resp)

        return tuple(responses)

    # ------------------------------------------------------------------
    # Pipeline: append_responses
    # ------------------------------------------------------------------

    @staticmethod
    def append_responses(
        session: CollaborationSession,
        responses: tuple[CollaborationResponse, ...] | list[CollaborationResponse],
    ) -> CollaborationSession:
        """Append responses to a session and mark it completed.

        Args:
            session: The current session.
            responses: Responses to append.

        Returns:
            A new session with responses appended and status "completed".
        """
        merged = list(session.responses) + list(responses)
        return CollaborationSession(
            session_id=session.session_id,
            request=session.request,
            participants=session.participants,
            responses=tuple(merged),
            status="completed",
            created_at=session.created_at,
            metadata=dict(session.metadata),
        )

    # ------------------------------------------------------------------
    # Pipeline: consolidate
    # ------------------------------------------------------------------

    @staticmethod
    def consolidate(
        session: CollaborationSession,
        context: CollaborationContext | None = None,
    ) -> CollaborationResult:
        """Consolidate all responses and produce a final result.

        Args:
            session: The completed session with all responses.
            context: Optional collaboration context.

        Returns:
            A CollaborationResult with consensus and consolidated response.
        """
        responses = session.responses
        consensus = _calculate_consensus(responses)

        approvals = sum(1 for r in responses if r.decision == "approved")
        rejections = sum(1 for r in responses if r.decision == "rejected")
        abstentions = sum(1 for r in responses if r.decision == "abstained")
        needs_info_count = sum(1 for r in responses if r.decision == "needs_info")

        success = consensus in ("unanimous", "majority")

        # Build a consolidated response (the first approved response if any)
        consolidated = None
        for r in responses:
            if r.decision == "approved":
                consolidated = r
                break

        trace = CollaborationRuntime.build_trace(
            stages=[
                "create_request", "add_participants", "send_request",
                "simulate_responses", "consolidate",
            ],
            session=session,
            approvals=approvals,
            rejections=rejections,
            abstentions=abstentions,
            needs_info_count=needs_info_count,
            consensus=consensus,
        )

        return CollaborationResult(
            success=success,
            session=session,
            context=context,
            trace=trace,
            consolidated_response=consolidated,
            consensus=consensus,
        )

    # ------------------------------------------------------------------
    # Pipeline: build_trace
    # ------------------------------------------------------------------

    @staticmethod
    def build_trace(
        stages: tuple[str, ...] | list[str],
        session: CollaborationSession | None = None,
        approvals: int = 0,
        rejections: int = 0,
        abstentions: int = 0,
        needs_info_count: int = 0,
        consensus: str = "",
        timestamps: dict[str, float] | None = None,
    ) -> CollaborationTrace:
        """Assemble a CollaborationTrace from pipeline data.

        Args:
            stages: Ordered stage names that were executed.
            session: The session (or None).
            approvals: Number of approved responses.
            rejections: Number of rejected responses.
            abstentions: Number of abstained responses.
            needs_info_count: Number of needs_info responses.
            consensus: The final consensus.
            timestamps: Optional dict of stage timestamps.

        Returns:
            A new CollaborationTrace.
        """
        participants_count = len(session.participants) if session else 0
        responses_received = len(session.responses) if session else 0

        return CollaborationTrace(
            stages=tuple(stages),
            requests_sent=1 if session else 0,
            responses_received=responses_received,
            participants_count=participants_count,
            approvals=approvals,
            rejections=rejections,
            abstentions=abstentions,
            needs_info_count=needs_info_count,
            consensus=consensus,
            timestamps=dict(timestamps) if timestamps else {},
        )

    # ------------------------------------------------------------------
    # Pipeline: build_result
    # ------------------------------------------------------------------

    @staticmethod
    def build_result(
        session: CollaborationSession | None = None,
        context: CollaborationContext | None = None,
        trace: CollaborationTrace | None = None,
        consolidated_response: CollaborationResponse | None = None,
        consensus: str = "",
        success: bool = True,
        error_message: str = "",
    ) -> CollaborationResult:
        """Assemble a CollaborationResult from pipeline data.

        Args:
            session: The session (None if setup failed).
            context: The collaboration context.
            trace: Execution trace.
            consolidated_response: The final consolidated response.
            consensus: Final consensus.
            success: Whether the cycle succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new CollaborationResult.
        """
        return CollaborationResult(
            success=success,
            session=session,
            context=context,
            trace=trace,
            consolidated_response=consolidated_response,
            consensus=consensus,
            error_message=error_message,
        )

    # ------------------------------------------------------------------
    # Convenience: full cycle
    # ------------------------------------------------------------------

    @staticmethod
    def full_collaboration_cycle(
        title: str,
        description: str = "",
        sender_id: UUID | None = None,
        participants: tuple[CollaborationParticipant, ...]
        | list[CollaborationParticipant] | None = None,
        urgency: str = "medium",
        department: str = "general",
        metadata: dict[str, Any] | None = None,
        response_decisions: list[str] | None = None,
        response_contents: list[str] | None = None,
        event_bus: EventBus | None = None,
    ) -> CollaborationResult:
        """Run the full collaboration pipeline end-to-end.

        Convenience method that calls all stages in order.

        Args:
            title: Short title of the collaboration.
            description: Detailed description.
            sender_id: The employee creating the request.
            participants: Participants to include.
            urgency: Urgency level.
            department: Department context.
            metadata: Optional metadata.
            response_decisions: Optional explicit decisions.
            response_contents: Optional explicit contents.
            event_bus: Optional EventBus for publishing events.

        Returns:
            A CollaborationResult from the completed pipeline.
        """
        ts: dict[str, float] = {}

        def _pub(e: Any) -> None:
            if event_bus is not None:
                event_bus.publish(e)

        request = CollaborationRuntime.create_request(
            title=title, description=description,
            sender_id=sender_id, metadata=metadata,
        )
        ts["create_request"] = time.time()

        if not participants:
            return CollaborationRuntime.build_result(
                success=False,
                error_message="No participants provided for collaboration.",
                consensus="no_consensus",
            )

        session = CollaborationRuntime.add_participants(request, participants)
        ts["add_participants"] = time.time()

        ctx = CollaborationContext.create(
            task_name=title, sender_id=sender_id,
            department=department, urgency=urgency,
        )

        _pub(CollaborationStarted(
            session_id=session.session_id,
            title=title, participants_count=len(participants),
            timestamp=time.time(),
        ))

        session = CollaborationRuntime.send_request(session, ctx)
        ts["send_request"] = time.time()

        responses = CollaborationRuntime.simulate_responses(
            session, ctx,
            response_decisions=response_decisions,
            response_contents=response_contents,
        )
        ts["simulate_responses"] = time.time()

        for r in responses:
            _pub(ParticipantResponded(
                session_id=session.session_id,
                participant_id=r.participant_id,
                decision=r.decision,
                timestamp=time.time(),
            ))

        session = CollaborationRuntime.append_responses(session, responses)
        ts["consolidate"] = time.time()

        result = CollaborationRuntime.consolidate(session, ctx)

        _pub(CollaborationCompleted(
            session_id=session.session_id,
            consensus=result.consensus,
            success=result.success,
            timestamp=time.time(),
        ))

        trace = CollaborationTrace(
            stages=result.trace.stages if result.trace else (),
            requests_sent=1,
            responses_received=len(responses),
            participants_count=len(participants),
            approvals=sum(1 for r in responses if r.decision == "approved"),
            rejections=sum(1 for r in responses if r.decision == "rejected"),
            abstentions=sum(1 for r in responses if r.decision == "abstained"),
            needs_info_count=sum(1 for r in responses if r.decision == "needs_info"),
            consensus=result.consensus,
            timestamps=ts,
        )

        return CollaborationResult(
            success=result.success,
            session=session,
            context=ctx,
            trace=trace,
            consolidated_response=result.consolidated_response,
            consensus=result.consensus,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def count_by_decision(
        responses: tuple[CollaborationResponse, ...] | list[CollaborationResponse],
        decision: str,
    ) -> int:
        """Count responses with a given decision."""
        return sum(1 for r in responses if r.decision == decision)

    @staticmethod
    def find_participant(
        session: CollaborationSession,
        participant_id: UUID,
    ) -> CollaborationParticipant | None:
        """Find a participant by ID in a session."""
        for p in session.participants:
            if p.participant_id == participant_id:
                return p
        return None

    @staticmethod
    def response_from_participant(
        session: CollaborationSession,
        participant_id: UUID,
    ) -> CollaborationResponse | None:
        """Find a response from a specific participant."""
        for r in session.responses:
            if r.participant_id == participant_id:
                return r
        return None

    @staticmethod
    def all_approved(responses: tuple[CollaborationResponse, ...] | list[CollaborationResponse]) -> bool:
        """Check whether all responses are approved."""
        if not responses:
            return False
        return all(r.decision == "approved" for r in responses)

    @staticmethod
    def all_rejected(responses: tuple[CollaborationResponse, ...] | list[CollaborationResponse]) -> bool:
        """Check whether all responses are rejected."""
        if not responses:
            return False
        return all(r.decision == "rejected" for r in responses)
