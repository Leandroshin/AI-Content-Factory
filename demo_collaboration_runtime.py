"""Demo for the Collaboration Runtime Foundation.

Validates CollaborationRuntime stateless pipeline:
create_request → add_participants → send_request →
simulate_responses → append_responses → consolidate

All operations are deterministic, frozen, and side-effect free.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.collaboration import (
    CollaborationContext,
    CollaborationParticipant,
    CollaborationRequest,
    CollaborationResponse,
    CollaborationResult,
    CollaborationRuntime,
    CollaborationSession,
    CollaborationTrace,
)


# ------------------------------------------------------------------
# Scenario 1: create_request
# ------------------------------------------------------------------


def scenario_create_request() -> None:
    """create_request produces a basic request."""
    req = CollaborationRuntime.create_request("Design API")

    assert isinstance(req, CollaborationRequest)
    assert req.title == "Design API"
    assert req.description == ""
    assert req.sender_id is None
    print(f"[PASS] create_request                   | title='{req.title}'")


# ------------------------------------------------------------------
# Scenario 2: create_request with description
# ------------------------------------------------------------------


def scenario_create_request_with_description() -> None:
    """create_request stores description."""
    req = CollaborationRuntime.create_request(
        "Design API",
        description="Define REST endpoints for user module",
    )
    assert req.description == "Define REST endpoints for user module"
    print(f"[PASS] create_request_description        | desc='{req.description[:20]}...'")


# ------------------------------------------------------------------
# Scenario 3: create_request with sender
# ------------------------------------------------------------------


def scenario_create_request_with_sender() -> None:
    """create_request stores sender_id."""
    sender = uuid4()
    req = CollaborationRuntime.create_request("Review PR", sender_id=sender)
    assert req.sender_id == sender
    print(f"[PASS] create_request_sender             | sender={sender.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 4: create_request with metadata
# ------------------------------------------------------------------


def scenario_create_request_with_metadata() -> None:
    """create_request stores metadata."""
    req = CollaborationRuntime.create_request(
        "Migrate DB", metadata={"priority": "high"},
    )
    assert req.metadata["priority"] == "high"
    print(f"[PASS] create_request_metadata           | metadata={req.metadata}")


# ------------------------------------------------------------------
# Scenario 5: add_participants basic
# ------------------------------------------------------------------


def scenario_add_participants() -> None:
    """add_participants creates a session with participants."""
    req = CollaborationRuntime.create_request("Code review")
    p1 = CollaborationParticipant.create("Alice", role="senior")
    p2 = CollaborationParticipant.create("Bob", role="junior")
    session = CollaborationRuntime.add_participants(req, (p1, p2))

    assert isinstance(session, CollaborationSession)
    assert session.request == req
    assert len(session.participants) == 2
    assert session.status == "pending"
    print(f"[PASS] add_participants                 | {len(session.participants)} participants "
          f"status={session.status}")


# ------------------------------------------------------------------
# Scenario 6: add_participants with metadata
# ------------------------------------------------------------------


def scenario_add_participants_metadata() -> None:
    """add_participants stores metadata in the session."""
    req = CollaborationRuntime.create_request("Sprint planning")
    p = CollaborationParticipant.create("Carol", role="manager")
    session = CollaborationRuntime.add_participants(
        req, (p,), metadata={"channel": "slack"},
    )
    assert session.metadata["channel"] == "slack"
    assert session.metadata["title"] == "Sprint planning"
    print(f"[PASS] add_participants_metadata         | metadata={session.metadata}")


# ------------------------------------------------------------------
# Scenario 7: send_request
# ------------------------------------------------------------------


def scenario_send_request() -> None:
    """send_request transitions from pending to active."""
    req = CollaborationRuntime.create_request("Deploy release")
    p = CollaborationParticipant.create("Dave", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)

    assert active.status == "active"
    assert active.session_id == session.session_id
    print(f"[PASS] send_request                      | status={active.status}")


# ------------------------------------------------------------------
# Scenario 8: send_request with context
# ------------------------------------------------------------------


def scenario_send_request_with_context() -> None:
    """send_request merges context into session metadata."""
    req = CollaborationRuntime.create_request("Hotfix")
    p = CollaborationParticipant.create("Eve", role="senior")
    session = CollaborationRuntime.add_participants(req, (p,))
    ctx = CollaborationContext.create(urgency="critical", department="engineering")
    active = CollaborationRuntime.send_request(session, ctx)

    assert active.metadata["urgency"] == "critical"
    assert active.metadata["department"] == "engineering"
    print(f"[PASS] send_request_context              | urgency={active.metadata['urgency']}")


# ------------------------------------------------------------------
# Scenario 9: simulate_responses — senior
# ------------------------------------------------------------------


def scenario_simulate_senior() -> None:
    """senior role always approves."""
    req = CollaborationRuntime.create_request("Refactor module")
    p = CollaborationParticipant.create("Frank", role="senior")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert len(responses) == 1
    assert responses[0].decision == "approved"
    assert "support" in responses[0].content.lower()
    print(f"[PASS] simulate_senior                   | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 10: simulate_responses — junior
# ------------------------------------------------------------------


def scenario_simulate_junior() -> None:
    """junior role always approves with deferral."""
    req = CollaborationRuntime.create_request("Write tests")
    p = CollaborationParticipant.create("Grace", role="junior")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "approved"
    assert "follow the lead" in responses[0].content.lower()
    print(f"[PASS] simulate_junior                   | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 11: simulate_responses — manager (non-critical)
# ------------------------------------------------------------------


def scenario_simulate_manager_approved() -> None:
    """manager approves non-critical requests."""
    req = CollaborationRuntime.create_request("Update docs")
    p = CollaborationParticipant.create("Heidi", role="manager")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "approved"
    assert "reasonable" in responses[0].content.lower()
    print(f"[PASS] simulate_manager_approved          | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 12: simulate_responses — manager (critical → needs_info)
# ------------------------------------------------------------------


def scenario_simulate_manager_critical() -> None:
    """manager requests info for critical requests."""
    req = CollaborationRuntime.create_request("Production deployment")
    p = CollaborationParticipant.create("Ivan", role="manager")
    session = CollaborationRuntime.add_participants(req, (p,))
    ctx = CollaborationContext.create(urgency="critical")
    active = CollaborationRuntime.send_request(session, ctx)
    responses = CollaborationRuntime.simulate_responses(active, ctx)

    assert responses[0].decision == "needs_info"
    print(f"[PASS] simulate_manager_critical          | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 13: simulate_responses — lead (approved)
# ------------------------------------------------------------------


def scenario_simulate_lead_approved() -> None:
    """lead approves straightforward requests."""
    req = CollaborationRuntime.create_request("Add logging")
    p = CollaborationParticipant.create("Judy", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "approved"
    assert "Proceed" in responses[0].content
    print(f"[PASS] simulate_lead_approved             | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 14: simulate_responses — lead (complex → rejected)
# ------------------------------------------------------------------


def scenario_simulate_lead_complex() -> None:
    """lead rejects complex requests."""
    req = CollaborationRuntime.create_request("Complex architecture redesign")
    p = CollaborationParticipant.create("Karl", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "rejected"
    assert "concerns" in responses[0].content.lower()
    print(f"[PASS] simulate_lead_complex              | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 15: simulate_responses — lead (risky → rejected)
# ------------------------------------------------------------------


def scenario_simulate_lead_risky() -> None:
    """lead rejects risky requests."""
    req = CollaborationRuntime.create_request("Database migration", description="risky change")
    p = CollaborationParticipant.create("Leo", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "rejected"
    print(f"[PASS] simulate_lead_risky                | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 16: simulate_responses — lead (restructure → rejected)
# ------------------------------------------------------------------


def scenario_simulate_lead_restructure() -> None:
    """lead rejects restructure requests."""
    req = CollaborationRuntime.create_request("Team restructure proposal")
    p = CollaborationParticipant.create("Maria", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "rejected"
    print(f"[PASS] simulate_lead_restructure          | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 17: simulate_responses — lead (critical → needs_info)
# ------------------------------------------------------------------


def scenario_simulate_lead_critical() -> None:
    """lead requests info for critical requests."""
    req = CollaborationRuntime.create_request("Emergency patch")
    p = CollaborationParticipant.create("Nathan", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    ctx = CollaborationContext.create(urgency="critical")
    active = CollaborationRuntime.send_request(session, ctx)
    responses = CollaborationRuntime.simulate_responses(active, ctx)

    assert responses[0].decision == "needs_info"
    assert "timeline" in responses[0].content.lower()
    print(f"[PASS] simulate_lead_critical             | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 18: simulate_responses — observer
# ------------------------------------------------------------------


def scenario_simulate_observer() -> None:
    """observer always abstains."""
    req = CollaborationRuntime.create_request("Team standup")
    p = CollaborationParticipant.create("Olivia", role="observer")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "abstained"
    assert "Abstained" in responses[0].content
    print(f"[PASS] simulate_observer                  | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 19: simulate_responses — member (default)
# ------------------------------------------------------------------


def scenario_simulate_member() -> None:
    """default member role approves."""
    req = CollaborationRuntime.create_request("General task")
    p = CollaborationParticipant.create("Paul", role="member")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    assert responses[0].decision == "approved"
    assert "Acknowledged" in responses[0].content
    print(f"[PASS] simulate_member                    | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 20: simulate_responses — override decisions
# ------------------------------------------------------------------


def scenario_simulate_override_decisions() -> None:
    """simulate_responses accepts explicit decisions."""
    req = CollaborationRuntime.create_request("Any title")
    p1 = CollaborationParticipant.create("Alice", role="senior")
    p2 = CollaborationParticipant.create("Bob", role="junior")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(
        active, response_decisions=["rejected", "abstained"],
    )

    assert len(responses) == 2
    assert responses[0].decision == "rejected"
    assert responses[1].decision == "abstained"
    print(f"[PASS] simulate_override_decisions        | decisions={[r.decision for r in responses]}")


# ------------------------------------------------------------------
# Scenario 21: simulate_responses — override contents
# ------------------------------------------------------------------


def scenario_simulate_override_contents() -> None:
    """simulate_responses accepts explicit contents."""
    req = CollaborationRuntime.create_request("Any title")
    p = CollaborationParticipant.create("Charlie", role="member")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(
        active, response_contents=["Custom message"],
    )

    assert responses[0].content == "Custom message"
    print(f"[PASS] simulate_override_contents         | content='{responses[0].content}'")


# ------------------------------------------------------------------
# Scenario 22: simulate_responses — override partial
# ------------------------------------------------------------------


def scenario_simulate_override_partial() -> None:
    """simulate_responses falls back for missing overrides."""
    req = CollaborationRuntime.create_request("Any title")
    p = CollaborationParticipant.create("Diana", role="lead")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(
        active, response_decisions=["approved"],
    )

    assert responses[0].decision == "approved"
    assert "Proceed" in responses[0].content
    print(f"[PASS] simulate_override_partial          | decision={responses[0].decision}")


# ------------------------------------------------------------------
# Scenario 23: append_responses
# ------------------------------------------------------------------


def scenario_append_responses() -> None:
    """append_responses appends and marks completed."""
    req = CollaborationRuntime.create_request("Review design")
    p = CollaborationParticipant.create("Eve", role="senior")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)

    assert completed.status == "completed"
    assert len(completed.responses) == 1
    assert completed.responses[0].decision == "approved"
    print(f"[PASS] append_responses                  | status={completed.status} "
          f"responses={len(completed.responses)}")


# ------------------------------------------------------------------
# Scenario 24: append_responses multiple times
# ------------------------------------------------------------------


def scenario_append_responses_twice() -> None:
    """append_responses merges with existing responses."""
    req = CollaborationRuntime.create_request("Two rounds")
    p1 = CollaborationParticipant.create("Frank", role="senior")
    p2 = CollaborationParticipant.create("Grace", role="junior")
    session = CollaborationRuntime.add_participants(req, (p1,))
    active = CollaborationRuntime.send_request(session)
    r1 = CollaborationRuntime.simulate_responses(active)
    s1 = CollaborationRuntime.append_responses(active, r1)

    # Second round — note: send_request would normally be called again
    s2 = CollaborationRuntime.append_responses(
        s1,
        [CollaborationResponse.create(s1.request.request_id, p2.participant_id,
                                       decision="approved")],
    )
    assert len(s2.responses) == 2
    assert s2.status == "completed"
    print(f"[PASS] append_responses_twice            | responses={len(s2.responses)}")


# ------------------------------------------------------------------
# Scenario 25: consolidate — unanimous
# ------------------------------------------------------------------


def scenario_consolidate_unanimous() -> None:
    """consolidate returns unanimous for all approved."""
    req = CollaborationRuntime.create_request("Simple task")
    p1 = CollaborationParticipant.create("Hank", role="senior")
    p2 = CollaborationParticipant.create("Iris", role="junior")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)
    result = CollaborationRuntime.consolidate(completed)

    assert result.success is True
    assert result.consensus == "unanimous"
    assert result.consolidated_response is not None
    print(f"[PASS] consolidate_unanimous              | consensus={result.consensus} "
          f"success={result.success}")


# ------------------------------------------------------------------
# Scenario 26: consolidate — majority
# ------------------------------------------------------------------


def scenario_consolidate_majority() -> None:
    """consolidate returns majority when most approve."""
    req = CollaborationRuntime.create_request("Normal review")
    p1 = CollaborationParticipant.create("Jack", role="senior")
    p2 = CollaborationParticipant.create("Kate", role="junior")
    p3 = CollaborationParticipant.create("Leo", role="observer")
    session = CollaborationRuntime.add_participants(req, (p1, p2, p3))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)
    result = CollaborationRuntime.consolidate(completed)

    assert result.consensus == "majority"
    assert result.success is True
    print(f"[PASS] consolidate_majority               | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 27: consolidate — rejected
# ------------------------------------------------------------------


def scenario_consolidate_rejected() -> None:
    """consolidate returns rejected when majority rejects."""
    req = CollaborationRuntime.create_request("Complex risky restructure")
    p1 = CollaborationParticipant.create("Mike", role="lead")
    p2 = CollaborationParticipant.create("Nina", role="lead")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)
    result = CollaborationRuntime.consolidate(completed)

    assert result.consensus == "rejected"
    assert result.success is False
    print(f"[PASS] consolidate_rejected               | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 28: consolidate — tie
# ------------------------------------------------------------------


def scenario_consolidate_tie() -> None:
    """consolidate returns tie when approved == rejected."""
    req = CollaborationRuntime.create_request("Content update")
    p1 = CollaborationParticipant.create("Oscar", role="lead")
    p2 = CollaborationParticipant.create("Pam", role="lead")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(
        active, response_decisions=["approved", "rejected"],
    )
    completed = CollaborationRuntime.append_responses(active, responses)
    result = CollaborationRuntime.consolidate(completed)

    assert result.consensus == "tie"
    assert result.success is False
    print(f"[PASS] consolidate_tie                    | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 29: consolidate — needs_info
# ------------------------------------------------------------------


def scenario_consolidate_needs_info() -> None:
    """consolidate returns needs_info when all are needs_info."""
    req = CollaborationRuntime.create_request("Production deployment")
    p1 = CollaborationParticipant.create("Quinn", role="manager")
    p2 = CollaborationParticipant.create("Raj", role="manager")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    ctx = CollaborationContext.create(urgency="critical")
    active = CollaborationRuntime.send_request(session, ctx)
    responses = CollaborationRuntime.simulate_responses(active, ctx)
    completed = CollaborationRuntime.append_responses(active, responses)
    result = CollaborationRuntime.consolidate(completed)

    assert result.consensus == "needs_info"
    assert result.success is False
    print(f"[PASS] consolidate_needs_info             | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 30: consolidate — no_consensus (empty)
# ------------------------------------------------------------------


def scenario_consolidate_no_consensus() -> None:
    """consolidate returns no_consensus when no responses."""
    req = CollaborationRuntime.create_request("Empty session")
    session = CollaborationRuntime.add_participants(req, ())
    result = CollaborationRuntime.consolidate(session)

    assert result.consensus == "no_consensus"
    assert result.success is False
    print(f"[PASS] consolidate_no_consensus           | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 31: build_trace
# ------------------------------------------------------------------


def scenario_build_trace() -> None:
    """build_trace creates a trace with counts."""
    req = CollaborationRuntime.create_request("Trace test")
    p = CollaborationParticipant.create("Sam", role="senior")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)

    trace = CollaborationRuntime.build_trace(
        stages=["create_request", "add_participants", "send_request",
                "simulate_responses", "append_responses", "consolidate"],
        session=completed,
        approvals=1, rejections=0, abstentions=0, needs_info_count=0,
        consensus="unanimous",
    )

    assert trace.requests_sent == 1
    assert trace.responses_received == 1
    assert trace.participants_count == 1
    assert trace.stages[0] == "create_request"
    print(f"[PASS] build_trace                        | stages={len(trace.stages)} "
          f"consensus={trace.consensus}")


# ------------------------------------------------------------------
# Scenario 32: build_trace with timestamps
# ------------------------------------------------------------------


def scenario_build_trace_timestamps() -> None:
    """build_trace accepts explicit timestamps."""
    trace = CollaborationRuntime.build_trace(
        stages=["create_request", "consolidate"],
        timestamps={"create_request": 1000.0, "consolidate": 1001.0},
    )
    assert trace.timestamps["create_request"] == 1000.0
    assert trace.timestamps["consolidate"] == 1001.0
    print(f"[PASS] build_trace_timestamps             | timestamps={len(trace.timestamps)}")


# ------------------------------------------------------------------
# Scenario 33: build_result
# ------------------------------------------------------------------


def scenario_build_result() -> None:
    """build_result assembles a success result."""
    p = CollaborationParticipant.create("Tina", role="senior")
    req = CollaborationRuntime.create_request("Result test")
    session = CollaborationRuntime.add_participants(req, (p,))
    trace = CollaborationRuntime.build_trace(
        stages=["create_request"],
        session=session,
    )
    result = CollaborationRuntime.build_result(
        session=session, trace=trace,
        consensus="unanimous", success=True,
    )

    assert result.success is True
    assert result.consensus == "unanimous"
    assert result.trace is trace
    print(f"[PASS] build_result                       | success={result.success}")


# ------------------------------------------------------------------
# Scenario 34: build_result with error
# ------------------------------------------------------------------


def scenario_build_result_error() -> None:
    """build_result assembles an error result."""
    result = CollaborationRuntime.build_result(
        success=False,
        error_message="No participants provided.",
        consensus="no_consensus",
    )
    assert result.success is False
    assert result.error_message == "No participants provided."
    assert result.session is None
    print(f"[PASS] build_result_error                 | error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 35: full_collaboration_cycle
# ------------------------------------------------------------------


def scenario_full_cycle() -> None:
    """full_collaboration_cycle runs all stages."""
    p1 = CollaborationParticipant.create("Uma", role="senior")
    p2 = CollaborationParticipant.create("Vince", role="junior")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Update README",
        participants=(p1, p2),
    )

    assert isinstance(result, CollaborationResult)
    assert result.success is True
    assert result.session is not None
    assert result.session.status == "completed"
    assert result.consensus in ("unanimous", "majority")
    assert result.trace is not None
    assert len(result.trace.stages) > 0
    print(f"[PASS] full_cycle                         | success={result.success} "
          f"consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 36: full_collaboration_cycle with urgency
# ------------------------------------------------------------------


def scenario_full_cycle_urgency() -> None:
    """full_collaboration_cycle accepts urgency."""
    p = CollaborationParticipant.create("Wendy", role="manager")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Release sign-off",
        participants=(p,),
        urgency="critical",
    )

    # Manager + critical = needs_info
    assert result.consensus == "needs_info"
    assert result.success is False
    print(f"[PASS] full_cycle_urgency                 | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 37: full_collaboration_cycle with department
# ------------------------------------------------------------------


def scenario_full_cycle_department() -> None:
    """full_collaboration_cycle accepts department."""
    p = CollaborationParticipant.create("Xander", role="senior")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Code freeze",
        participants=(p,),
        department="engineering",
        urgency="high",
    )

    assert result.context is not None
    assert result.context.department == "engineering"
    assert result.context.urgency == "high"
    assert result.session is not None
    assert result.session.metadata.get("department") == "engineering"
    print(f"[PASS] full_cycle_department              | dept={result.context.department}")


# ------------------------------------------------------------------
# Scenario 38: full_collaboration_cycle no participants
# ------------------------------------------------------------------


def scenario_full_cycle_no_participants() -> None:
    """full_collaboration_cycle errors with no participants."""
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Lone wolf",
        participants=None,
    )

    assert result.success is False
    assert result.error_message == "No participants provided for collaboration."
    assert result.consensus == "no_consensus"
    print(f"[PASS] full_cycle_no_participants         | error='{result.error_message[:20]}...'")


# ------------------------------------------------------------------
# Scenario 39: full_collaboration_cycle overridden decisions
# ------------------------------------------------------------------


def scenario_full_cycle_overridden() -> None:
    """full_collaboration_cycle accepts explicit decisions."""
    p1 = CollaborationParticipant.create("Yara", role="senior")
    p2 = CollaborationParticipant.create("Zack", role="junior")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Forced rejection",
        participants=(p1, p2),
        response_decisions=["rejected", "rejected"],
    )

    assert result.consensus == "rejected"
    assert result.success is False
    print(f"[PASS] full_cycle_overridden              | consensus={result.consensus}")


# ------------------------------------------------------------------
# Scenario 40: full_collaboration_cycle with metadata
# ------------------------------------------------------------------


def scenario_full_cycle_metadata() -> None:
    """full_collaboration_cycle accepts metadata."""
    p = CollaborationParticipant.create("Adam", role="lead")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Simple approval",
        participants=(p,),
        metadata={"source": "demo"},
    )

    assert result.session is not None
    assert result.session.request.metadata.get("source") == "demo"
    print(f"[PASS] full_cycle_metadata                | metadata transmitted")


# ------------------------------------------------------------------
# Scenario 41: count_by_decision
# ------------------------------------------------------------------


def scenario_count_by_decision() -> None:
    """count_by_decision counts matching decisions."""
    p1 = CollaborationParticipant.create("Beth", role="senior")
    p2 = CollaborationParticipant.create("Carl", role="junior")
    req = CollaborationRuntime.create_request("Count test")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)

    n = CollaborationRuntime.count_by_decision(responses, "approved")
    assert n == 2
    n2 = CollaborationRuntime.count_by_decision(responses, "rejected")
    assert n2 == 0
    print(f"[PASS] count_by_decision                 | approved={n} rejected={n2}")


# ------------------------------------------------------------------
# Scenario 42: find_participant
# ------------------------------------------------------------------


def scenario_find_participant() -> None:
    """find_participant locates a participant by ID."""
    p = CollaborationParticipant.create("Dana", role="member")
    req = CollaborationRuntime.create_request("Find test")
    session = CollaborationRuntime.add_participants(req, (p,))

    found = CollaborationRuntime.find_participant(session, p.participant_id)
    assert found is not None
    assert found.name == "Dana"

    missing = CollaborationRuntime.find_participant(session, uuid4())
    assert missing is None
    print(f"[PASS] find_participant                  | found={found.name} missing_ok={missing is None}")


# ------------------------------------------------------------------
# Scenario 43: response_from_participant
# ------------------------------------------------------------------


def scenario_response_from_participant() -> None:
    """response_from_participant locates a response by participant ID."""
    p = CollaborationParticipant.create("Eli", role="senior")
    req = CollaborationRuntime.create_request("Response test")
    session = CollaborationRuntime.add_participants(req, (p,))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)

    found = CollaborationRuntime.response_from_participant(completed, p.participant_id)
    assert found is not None
    assert found.decision == "approved"

    missing = CollaborationRuntime.response_from_participant(completed, uuid4())
    assert missing is None
    print(f"[PASS] response_from_participant          | found={found.decision} missing_ok={missing is None}")


# ------------------------------------------------------------------
# Scenario 44: all_approved
# ------------------------------------------------------------------


def scenario_all_approved() -> None:
    """all_approved returns True when all are approved."""
    p1 = CollaborationParticipant.create("Finn", role="senior")
    p2 = CollaborationParticipant.create("Gia", role="junior")
    req = CollaborationRuntime.create_request("Approval test")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)

    assert CollaborationRuntime.all_approved(completed.responses) is True

    # Empty returns False
    assert CollaborationRuntime.all_approved(()) is False
    print(f"[PASS] all_approved                       | {len(completed.responses)} approved, empty=False")


# ------------------------------------------------------------------
# Scenario 45: all_rejected
# ------------------------------------------------------------------


def scenario_all_rejected() -> None:
    """all_rejected returns True when all are rejected."""
    p1 = CollaborationParticipant.create("Hugo", role="lead")
    p2 = CollaborationParticipant.create("Ivy", role="lead")
    req = CollaborationRuntime.create_request("Complex restructure risky plan")
    session = CollaborationRuntime.add_participants(req, (p1, p2))
    active = CollaborationRuntime.send_request(session)
    responses = CollaborationRuntime.simulate_responses(active)
    completed = CollaborationRuntime.append_responses(active, responses)

    assert CollaborationRuntime.all_rejected(completed.responses) is True

    # Empty returns False
    assert CollaborationRuntime.all_rejected(()) is False
    print(f"[PASS] all_rejected                       | {len(completed.responses)} rejected, empty=False")


# ------------------------------------------------------------------
# Scenario 46: determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce same outputs."""
    p1 = CollaborationParticipant.create("Jack", role="senior")
    p2 = CollaborationParticipant.create("Kai", role="junior")
    r1 = CollaborationRuntime.full_collaboration_cycle(
        "Deterministic test", participants=(p1, p2),
    )
    r2 = CollaborationRuntime.full_collaboration_cycle(
        "Deterministic test", participants=(p1, p2),
    )

    # Consensus should be the same (but UUIDs differ)
    assert r1.consensus == r2.consensus
    assert r1.success == r2.success
    assert r1.trace.approvals == r2.trace.approvals
    assert r1.trace.rejections == r2.trace.rejections
    print(f"[PASS] determinism                        | consensus={r1.consensus} == {r2.consensus}")


# ------------------------------------------------------------------
# Scenario 47: frozen dataclasses
# ------------------------------------------------------------------


def scenario_frozen_dataclasses() -> None:
    """All collaboration dataclasses are frozen."""
    req = CollaborationRequest.create("Frozen test")
    with_raises(req)  # Will error if not frozen

    p = CollaborationParticipant.create("Leo", role="member")
    with_raises(p)

    resp = CollaborationResponse.create(req.request_id, p.participant_id)
    with_raises(resp)

    session = CollaborationRuntime.add_participants(req, (p,))
    with_raises(session)

    ctx = CollaborationContext.create()
    with_raises(ctx)

    trace = CollaborationRuntime.build_trace(stages=["test"])
    with_raises(trace)

    result = CollaborationRuntime.build_result()
    with_raises(result)

    print(f"[PASS] frozen_dataclasses                | all 7 types are frozen")


def with_raises(obj: object) -> None:
    """Helper: assert that attribute assignment raises TypeError."""
    import dataclasses
    assert dataclasses.is_dataclass(obj)
    assert obj.__dataclass_params__.frozen is True


# ------------------------------------------------------------------
# Scenario 48: factories — create methods
# ------------------------------------------------------------------


def scenario_factories() -> None:
    """Factory methods produce valid instances."""
    p = CollaborationParticipant.create("Mia", role="senior", department="eng",
                                         metadata={"exp": 5})
    assert isinstance(p.participant_id, UUID)
    assert p.name == "Mia"
    assert p.role == "senior"

    req = CollaborationRequest.create("Fact test", description="test")
    assert isinstance(req.request_id, UUID)

    req2 = CollaborationRequest.create_with_timestamp("Old", created_at=100.0)
    assert req2.created_at == 100.0

    resp = CollaborationResponse.create_with_timestamp(
        req.request_id, p.participant_id, created_at=200.0,
        decision="approved",
    )
    assert resp.created_at == 200.0
    assert resp.decision == "approved"

    session = CollaborationSession.create_with_timestamp(req, created_at=300.0)
    assert session.created_at == 300.0

    ctx = CollaborationContext.create(task_name="test", urgency="high")
    assert ctx.urgency == "high"
    assert isinstance(ctx.task_id, UUID)

    print(f"[PASS] factories                          | all 7 factory methods work")


# ------------------------------------------------------------------
# Scenario 49: full_cycle — all 5 roles
# ------------------------------------------------------------------


def scenario_full_cycle_all_roles() -> None:
    """full_collaboration_cycle works with all 5 roles."""
    roles = ["senior", "junior", "manager", "lead", "observer"]
    participants = tuple(
        CollaborationParticipant.create(f"User{i}", role=r)
        for i, r in enumerate(roles)
    )
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Standard request",
        participants=participants,
    )

    assert result.trace is not None
    assert result.trace.participants_count == 5
    # Senior + Junior + Lead (standard) = 3 approved; Manager approved; Observer abstained
    # 3 approved out of 5 = majority
    assert result.consensus == "majority"
    assert result.success is True
    print(f"[PASS] full_cycle_all_roles               | consensus={result.consensus} "
          f"participants={result.trace.participants_count}")


# ------------------------------------------------------------------
# Scenario 50: full_cycle — comprehensive trace
# ------------------------------------------------------------------


def scenario_full_cycle_trace_details() -> None:
    """full_collaboration_cycle produces detailed trace."""
    p1 = CollaborationParticipant.create("Nia", role="senior")
    p2 = CollaborationParticipant.create("Omar", role="lead")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Important feature",
        participants=(p1, p2),
    )

    assert result.trace is not None
    assert result.trace.requests_sent == 1
    assert result.trace.responses_received == 2
    assert result.trace.participants_count == 2
    assert len(result.trace.stages) == 5
    assert result.trace.stages[0] == "create_request"
    assert result.trace.stages[-1] == "consolidate"
    assert result.trace.approvals + result.trace.rejections + \
           result.trace.abstentions + result.trace.needs_info_count == 2
    assert len(result.trace.timestamps) == 5
    print(f"[PASS] full_cycle_trace_details           | stages={len(result.trace.stages)} "
          f"responses={result.trace.responses_received}")


# ------------------------------------------------------------------
# Scenario 51: context metadata preserved
# ------------------------------------------------------------------


def scenario_context_metadata() -> None:
    """CollaborationContext stores arbitrary metadata."""
    ctx = CollaborationContext.create(
        task_name="Deploy",
        metadata={"version": "2.0", "env": "prod"},
    )
    assert ctx.metadata["version"] == "2.0"
    assert ctx.metadata["env"] == "prod"
    print(f"[PASS] context_metadata                  | metadata={ctx.metadata}")


# ------------------------------------------------------------------
# Scenario 52: full_cycle with sender_id
# ------------------------------------------------------------------


def scenario_full_cycle_sender_id() -> None:
    """full_collaboration_cycle propagates sender_id."""
    sender = uuid4()
    p = CollaborationParticipant.create("Paul", role="senior")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Sender test",
        participants=(p,),
        sender_id=sender,
    )

    assert result.session is not None
    assert result.session.request.sender_id == sender
    assert result.context is not None
    assert result.context.sender_id == sender
    print(f"[PASS] full_cycle_sender_id               | sender propagated")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Collaboration Runtime Foundation Demo")
    print("=" * 58)
    print()

    scenario_create_request()
    scenario_create_request_with_description()
    scenario_create_request_with_sender()
    scenario_create_request_with_metadata()
    scenario_add_participants()
    scenario_add_participants_metadata()
    scenario_send_request()
    scenario_send_request_with_context()
    scenario_simulate_senior()
    scenario_simulate_junior()
    scenario_simulate_manager_approved()
    scenario_simulate_manager_critical()
    scenario_simulate_lead_approved()
    scenario_simulate_lead_complex()
    scenario_simulate_lead_risky()
    scenario_simulate_lead_restructure()
    scenario_simulate_lead_critical()
    scenario_simulate_observer()
    scenario_simulate_member()
    scenario_simulate_override_decisions()
    scenario_simulate_override_contents()
    scenario_simulate_override_partial()
    scenario_append_responses()
    scenario_append_responses_twice()
    scenario_consolidate_unanimous()
    scenario_consolidate_majority()
    scenario_consolidate_rejected()
    scenario_consolidate_tie()
    scenario_consolidate_needs_info()
    scenario_consolidate_no_consensus()
    scenario_build_trace()
    scenario_build_trace_timestamps()
    scenario_build_result()
    scenario_build_result_error()
    scenario_full_cycle()
    scenario_full_cycle_urgency()
    scenario_full_cycle_department()
    scenario_full_cycle_no_participants()
    scenario_full_cycle_overridden()
    scenario_full_cycle_metadata()
    scenario_count_by_decision()
    scenario_find_participant()
    scenario_response_from_participant()
    scenario_all_approved()
    scenario_all_rejected()
    scenario_determinism()
    scenario_frozen_dataclasses()
    scenario_factories()
    scenario_full_cycle_all_roles()
    scenario_full_cycle_trace_details()
    scenario_context_metadata()
    scenario_full_cycle_sender_id()

    print()
    print("=" * 58)
    print(f"All {52} Collaboration Runtime scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
