"""Integration demo between Skill Foundation and Skill Runtime (stateful).

Validates promote_record, promote_snapshot, create_from_foundation,
and the complete Conversation -> Memory -> Knowledge -> Learning ->
Skill Foundation -> Skill Runtime pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.knowledge.runtime import KnowledgeRuntime
from core.learning.foundation import (
    LearningRecommendation,
    LearningRuntime as FoundationLearningRuntime,
    LearningSnapshot,
)
from core.results.runtime import ResultRuntime
from core.skills.foundation import (
    SkillRecord,
    SkillRuntime as FoundationSkillRuntime,
    SkillSnapshot,
)
from core.skills.runtime import (
    SkillRuntime,
    SkillRuntimeSnapshot,
    SkillRuntimeState,
)
from core.skills.models import SkillLevel


# ------------------------------------------------------------------
# Minimal mock runtimes for SkillRuntime construction
# ------------------------------------------------------------------


@dataclass
class _MockEventBus:
    _events: list = field(default_factory=list)

    def publish(self, event: Any) -> None:
        self._events.append(event)

    def events(self) -> list[Any]:
        return list(self._events)


def _make_skill_runtime() -> tuple[SkillRuntime, _MockEventBus]:
    """Create a SkillRuntime with minimal mocked dependencies."""
    bus = _MockEventBus()
    result_runtime = ResultRuntime.__new__(ResultRuntime)
    result_runtime.event_bus = bus  # type: ignore[attr-defined]
    result_runtime._results = {}  # type: ignore[attr-defined]
    kr = KnowledgeRuntime.__new__(KnowledgeRuntime)
    kr.event_bus = bus  # type: ignore[attr-defined]
    kr._knowledge = {}  # type: ignore[attr-defined]
    kr.result_runtime = result_runtime  # type: ignore[attr-defined]
    sr = SkillRuntime.__new__(SkillRuntime)
    sr.knowledge_runtime = kr  # type: ignore[attr-defined]
    sr.event_bus = bus  # type: ignore[attr-defined]
    sr._skills = {}  # type: ignore[attr-defined]
    sr._events = []  # type: ignore[attr-defined]
    return sr, bus


# ------------------------------------------------------------------
# Scenario 1: promote_record — single skill
# ------------------------------------------------------------------


def scenario_promote_single_record() -> None:
    """A single SkillRecord is promoted to a stateful SkillRuntimeSnapshot."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        knowledge_id=UUID("00000000-0000-0000-0000-000000000001"),
        recommendation_type="study",
        title="Python Basics",
        description="Learn Python fundamentals.",
        timestamp=1000.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    snapshot = sr.promote_record(foundation_record)

    assert isinstance(snapshot, SkillRuntimeSnapshot)
    assert snapshot.skill_id == foundation_record.skill_id
    assert snapshot.name == "Python Basics"
    assert snapshot.state == SkillRuntimeState.LEARNING
    assert snapshot.level == SkillLevel.BASIC
    print(f"[PASS] promote_single_record           | id={snapshot.skill_id.hex[:8]} "
          f"name='{snapshot.name}' state={snapshot.state.value} level={snapshot.level.value}")


# ------------------------------------------------------------------
# Scenario 2: promote_record — multiple skills
# ------------------------------------------------------------------


def scenario_promote_multiple_records() -> None:
    """Multiple SkillRecords are promoted individually."""
    sr, _ = _make_skill_runtime()
    names = ["Skill A", "Skill B", "Skill C"]
    snapshots = []

    for name in names:
        rec = LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", name, f"Desc {name}", 1.0,
        )
        foundation_record = FoundationSkillRuntime.promote_learning(rec)
        snapshots.append(sr.promote_record(foundation_record))

    assert len(snapshots) == 3
    assert [s.name for s in snapshots] == names
    assert all(s.state == SkillRuntimeState.LEARNING for s in snapshots)
    print(f"[PASS] promote_multiple_records        | {len(snapshots)} promoted -> "
          f"names={[s.name for s in snapshots]}")


# ------------------------------------------------------------------
# Scenario 3: promote_snapshot — empty
# ------------------------------------------------------------------


def scenario_promote_snapshot_empty() -> None:
    """An empty SkillSnapshot produces an empty list of runtime snapshots."""
    sr, _ = _make_skill_runtime()
    empty_foundation_snap = FoundationSkillRuntime.create_snapshot()

    result = sr.promote_snapshot(empty_foundation_snap)

    assert result == []
    print(f"[PASS] promote_snapshot_empty          | {len(result)} runtime snapshots from empty foundation")


# ------------------------------------------------------------------
# Scenario 4: promote_snapshot — full
# ------------------------------------------------------------------


def scenario_promote_snapshot_full() -> None:
    """A SkillSnapshot with records produces matching runtime snapshots."""
    sr, _ = _make_skill_runtime()
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "Alpha", "Desc A", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "practice", "Beta", "Desc B", 2.0,
        ),
    ]
    learn_snap = FoundationLearningRuntime.create_snapshot(recs)
    foundation_snap = FoundationSkillRuntime.promote_snapshot(learn_snap)

    result = sr.promote_snapshot(foundation_snap)

    assert len(result) == 2
    assert result[0].name == "Alpha"
    assert result[1].name == "Beta"
    assert all(isinstance(s, SkillRuntimeSnapshot) for s in result)
    print(f"[PASS] promote_snapshot_full           | {len(result)} runtime snapshots "
          f"names={[s.name for s in result]}")


# ------------------------------------------------------------------
# Scenario 5: IDs preserved
# ------------------------------------------------------------------


def scenario_ids_preserved() -> None:
    """SkillRecord.skill_id is preserved in the runtime snapshot."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "ID Test", "Content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)
    original_id = foundation_record.skill_id

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.skill_id == original_id
    print(f"[PASS] ids_preserved                   | skill_id={snapshot.skill_id.hex[:8]} "
          f"matches foundation")


# ------------------------------------------------------------------
# Scenario 6: Timestamps preserved
# ------------------------------------------------------------------


def scenario_timestamps_preserved() -> None:
    """Foundation record created_at is stored in runtime snapshot metadata."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Time Test", "Content", 42.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.skill is not None
    attrs = snapshot.skill.context.metadata.attributes if snapshot.skill.context else {}
    assert "created_at" in attrs
    print(f"[PASS] timestamps_preserved            | created_at stored in metadata: "
          f"{attrs.get('created_at')}")


# ------------------------------------------------------------------
# Scenario 7: Metadata preserved
# ------------------------------------------------------------------


def scenario_metadata_preserved() -> None:
    """Foundation record metadata is carried into runtime snapshot."""
    sr, _ = _make_skill_runtime()
    foundation_record = SkillRecord.create_with_timestamp(
        recommendation_id=UUID("00000000-0000-0000-0000-000000000001"),
        skill_name="Meta Test",
        description="Content",
        created_at=1.0,
        metadata={"source": "demo", "session": "s-001"},
    )

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.skill is not None
    attrs = snapshot.skill.context.metadata.attributes if snapshot.skill.context else {}
    assert "source" in attrs
    assert attrs["source"] == "demo"
    assert "session" in attrs
    assert attrs["session"] == "s-001"
    print(f"[PASS] metadata_preserved              | metadata attributes preserved: "
          f"{dict(attrs)}")


# ------------------------------------------------------------------
# Scenario 8: Complete integration pipeline
# ------------------------------------------------------------------


def scenario_full_integration_pipeline() -> None:
    """Conversation -> Memory -> Knowledge -> Learning -> Skill Foundation -> Skill Runtime."""
    from core.conversation import ConversationRuntime
    from core.knowledge.foundation import KnowledgeRuntime as FoundationKR
    from core.memory import MemoryRuntime

    sr, bus = _make_skill_runtime()

    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Explain transformers.")
    session = ConversationRuntime.append_message(session, "assistant",
        "Transformers are a neural network architecture.")
    session = ConversationRuntime.append_message(session, "user", "What is attention?")
    session = ConversationRuntime.append_message(session, "assistant",
        "Attention is a mechanism that weighs input importance.")

    # Conversation -> Memory
    mem_records = []
    for msg in session.messages:
        mem_records.append(ConversationRuntime.create_memory_record(session, msg))
    mem_snap = MemoryRuntime.create_snapshot(mem_records)
    assert len(mem_snap.records) == 4

    # Memory -> Knowledge
    know_records = MemoryRuntime.promote_records(mem_snap)
    know_snap = MemoryRuntime.promote_snapshot(mem_snap)

    # Knowledge -> Learning
    learn_records = []
    for kr in know_records:
        learn_records.append(FoundationLearningRuntime.promote_knowledge(kr))
    learn_snap = FoundationLearningRuntime.promote_snapshot(know_snap)
    assert len(learn_records) == 4

    # Learning -> Skill Foundation
    skill_records = []
    for rec in learn_records:
        skill_records.append(FoundationSkillRuntime.promote_learning(rec))
    foundation_snap = FoundationSkillRuntime.promote_snapshot(learn_snap)
    assert len(skill_records) == 4

    # Skill Foundation -> Skill Runtime (stateful)
    runtime_snapshots = sr.create_from_foundation(foundation_snap)

    assert len(runtime_snapshots) == 4
    assert all(s.state == SkillRuntimeState.LEARNING for s in runtime_snapshots)
    assert all(s.level == SkillLevel.BASIC for s in runtime_snapshots)

    # Verify events were emitted
    assert len(bus.events()) >= 4

    print(f"[PASS] full_integration_pipeline       | {len(session.messages)} msgs -> "
          f"{len(mem_records)} memory -> {len(know_records)} knowledge -> "
          f"{len(learn_records)} learning -> {len(skill_records)} foundation -> "
          f"{len(runtime_snapshots)} runtime | events={len(bus.events())}")


# ------------------------------------------------------------------
# Scenario 9: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same SkillRecord produces identical runtime content."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study",
        "Deterministic Skill", "Same content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    s1 = SkillRuntime._foundation_level_to_skill_level(foundation_record.level)
    s2 = SkillRuntime._foundation_level_to_skill_level(foundation_record.level)

    assert s1 == s2
    assert foundation_record.skill_name == "Deterministic Skill"
    assert foundation_record.description == "Same content"
    print(f"[PASS] determinism                     | name='{foundation_record.skill_name}' "
          f"level_mapping={s1.value} (deterministic)")


# ------------------------------------------------------------------
# Scenario 10: create_from_foundation
# ------------------------------------------------------------------


def scenario_create_from_foundation() -> None:
    """create_from_foundation promotes all records from a SkillSnapshot."""
    sr, _ = _make_skill_runtime()
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "F1", "D1", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "practice", "F2", "D2", 2.0,
        ),
    ]
    learn_snap = FoundationLearningRuntime.create_snapshot(recs)
    foundation_snap = FoundationSkillRuntime.promote_snapshot(learn_snap)

    result = sr.create_from_foundation(foundation_snap)

    assert len(result) == 2
    assert result[0].name == "F1"
    assert result[1].name == "F2"
    print(f"[PASS] create_from_foundation          | {len(result)} runtime snapshots "
          f"names={[s.name for s in result]}")


# ------------------------------------------------------------------
# Scenario 11: Level mapping (1 -> BASIC)
# ------------------------------------------------------------------


def scenario_level_mapping_basic() -> None:
    """Foundation level 1 maps to SkillLevel.BASIC."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Basic Skill", "B", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.level == SkillLevel.BASIC
    print(f"[PASS] level_mapping_basic             | level={foundation_record.level} -> {snapshot.level.value}")


# ------------------------------------------------------------------
# Scenario 12: Level mapping (2 -> INTERMEDIATE)
# ------------------------------------------------------------------


def scenario_level_mapping_intermediate() -> None:
    """Foundation level 2 maps to SkillLevel.INTERMEDIATE."""
    sr, _ = _make_skill_runtime()
    record = SkillRecord.create_with_timestamp(
        recommendation_id=UUID("00000000-0000-0000-0000-000000000001"),
        skill_name="Intermediate Skill",
        description="I",
        created_at=1.0,
        level=2,
    )

    snapshot = sr.promote_record(record)

    assert snapshot.level == SkillLevel.INTERMEDIATE
    print(f"[PASS] level_mapping_intermediate      | level={record.level} -> {snapshot.level.value}")


# ------------------------------------------------------------------
# Scenario 13: Level mapping (3 -> ADVANCED)
# ------------------------------------------------------------------


def scenario_level_mapping_advanced() -> None:
    """Foundation level 3 maps to SkillLevel.ADVANCED."""
    sr, _ = _make_skill_runtime()
    record = SkillRecord.create_with_timestamp(
        recommendation_id=UUID("00000000-0000-0000-0000-000000000001"),
        skill_name="Advanced Skill",
        description="A",
        created_at=1.0,
        level=3,
    )

    snapshot = sr.promote_record(record)

    assert snapshot.level == SkillLevel.ADVANCED
    print(f"[PASS] level_mapping_advanced           | level={record.level} -> {snapshot.level.value}")


# ------------------------------------------------------------------
# Scenario 14: Level mapping (4+ -> EXPERT)
# ------------------------------------------------------------------


def scenario_level_mapping_expert() -> None:
    """Foundation level 4+ maps to SkillLevel.EXPERT."""
    sr, _ = _make_skill_runtime()
    record = SkillRecord.create_with_timestamp(
        recommendation_id=UUID("00000000-0000-0000-0000-000000000001"),
        skill_name="Expert Skill",
        description="E",
        created_at=1.0,
        level=5,
    )

    snapshot = sr.promote_record(record)

    assert snapshot.level == SkillLevel.EXPERT
    print(f"[PASS] level_mapping_expert             | level={record.level} -> {snapshot.level.value}")


# ------------------------------------------------------------------
# Scenario 15: Runtime events emitted
# ------------------------------------------------------------------


def scenario_runtime_events_emitted() -> None:
    """promote_record emits SkillStateChangedEvent through the bus."""
    sr, bus = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Event Test", "Content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    sr.promote_record(foundation_record)

    assert len(bus.events()) >= 1
    print(f"[PASS] runtime_events_emitted           | {len(bus.events())} event(s) emitted")


# ------------------------------------------------------------------
# Scenario 16: Foundation independence (regression)
# ------------------------------------------------------------------


def scenario_foundation_independence() -> None:
    """Foundation SkillRuntime remains stateless and unchanged."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study",
        "Independent", "Foundation still works standalone", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    assert isinstance(foundation_record, SkillRecord)
    assert foundation_record.skill_name == "Independent"
    assert foundation_record.level == 1
    assert foundation_record.experience_points == 0

    snap = FoundationSkillRuntime.create_snapshot([foundation_record])
    assert len(snap.skills) == 1

    filtered = FoundationSkillRuntime.filter_by_level(snap)
    assert len(filtered) == 1

    print(f"[PASS] foundation_independence          | Foundation operates standalone "
          f"(record={foundation_record.skill_name}, snapshot={len(snap.skills)} skills)")


# ------------------------------------------------------------------
# Scenario 17: promote_snapshot returns list with correct types
# ------------------------------------------------------------------


def scenario_promote_snapshot_types() -> None:
    """promote_snapshot returns a list of SkillRuntimeSnapshot instances."""
    sr, _ = _make_skill_runtime()
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "T1", "D1", 1.0,
        ),
    ]
    learn_snap = FoundationLearningRuntime.create_snapshot(recs)
    foundation_snap = FoundationSkillRuntime.promote_snapshot(learn_snap)

    result = sr.promote_snapshot(foundation_snap)

    assert isinstance(result, list)
    assert all(isinstance(s, SkillRuntimeSnapshot) for s in result)
    print(f"[PASS] promote_snapshot_types           | list[{len(result)}] all SkillRuntimeSnapshot")


# ------------------------------------------------------------------
# Scenario 18: State transition to LEARNING
# ------------------------------------------------------------------


def scenario_state_transition_learning() -> None:
    """After promote_record, state is LEARNING and skill status is DRAFT."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study",
        "State Test", "Content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.state == SkillRuntimeState.LEARNING
    assert snapshot.skill is not None
    assert snapshot.skill.status.value == "draft"
    print(f"[PASS] state_transition_learning        | state={snapshot.state.value} "
          f"status={snapshot.skill.status.value}")


# ------------------------------------------------------------------
# Scenario 19: recommendation_id preserved in metadata
# ------------------------------------------------------------------


def scenario_recommendation_id_preserved() -> None:
    """recommendation_id is preserved in the Skill metadata attributes."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("11111111-1111-1111-1111-111111111111"), "study",
        "RecID Test", "Content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    snapshot = sr.promote_record(foundation_record)

    assert snapshot.skill is not None
    assert snapshot.skill.metadata is not None
    attrs = snapshot.skill.metadata.attributes
    assert "recommendation_id" in attrs
    rec_id_str = str(rec.recommendation_id)
    assert attrs["recommendation_id"] == rec_id_str
    print(f"[PASS] recommendation_id_preserved      | recommendation_id={attrs['recommendation_id']}")


# ------------------------------------------------------------------
# Scenario 20: Runtime snapshot list includes promoted skills
# ------------------------------------------------------------------


def scenario_runtime_snapshot_list() -> None:
    """After promotion, sr.snapshot() includes the newly created snapshots."""
    sr, _ = _make_skill_runtime()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study",
        "List Test", "Content", 1.0,
    )
    foundation_record = FoundationSkillRuntime.promote_learning(rec)

    sr.promote_record(foundation_record)

    all_snapshots = sr.snapshot()
    assert len(all_snapshots) == 1
    assert all_snapshots[0].name == "List Test"
    print(f"[PASS] runtime_snapshot_list            | sr.snapshot() contains {len(all_snapshots)} "
          f"skill(s)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Skill Runtime Integration Demo")
    print("=" * 58)
    print()

    scenario_promote_single_record()
    scenario_promote_multiple_records()
    scenario_promote_snapshot_empty()
    scenario_promote_snapshot_full()
    scenario_ids_preserved()
    scenario_timestamps_preserved()
    scenario_metadata_preserved()
    scenario_full_integration_pipeline()
    scenario_determinism()
    scenario_create_from_foundation()
    scenario_level_mapping_basic()
    scenario_level_mapping_intermediate()
    scenario_level_mapping_advanced()
    scenario_level_mapping_expert()
    scenario_runtime_events_emitted()
    scenario_foundation_independence()
    scenario_promote_snapshot_types()
    scenario_state_transition_learning()
    scenario_recommendation_id_preserved()
    scenario_runtime_snapshot_list()

    print()
    print("=" * 58)
    print("All Skill Runtime Integration scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
