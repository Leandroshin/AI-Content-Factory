"""Integration demo between Decision Engine and Skill Runtime.

Validates SkillMatcher, match_skills with real Skill Runtime snapshots,
fallback to legacy skill snapshots, and the complete pipeline:
Conversation -> Memory -> Knowledge -> Learning -> Skill Foundation ->
Skill Runtime -> Decision Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from core.decision.runtime import (
    DecisionContextBuilder,
    DecisionEngine,
    DecisionResult,
    SkillMatcher,
)
from core.policies.runtime import Constraint


# ------------------------------------------------------------------
# Snapshot-like objects
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    metadata: object = None


@dataclass
class TaskMetadata:
    tags: list[str] = field(default_factory=list)


@dataclass
class EmployeeSnapshot:
    employee_id: UUID
    name: str
    state: str = "idle"
    role: str = "generic"


@dataclass
class DepartmentSnapshot:
    department_id: UUID
    name: str
    employees: dict[UUID, object] = field(default_factory=dict)


@dataclass
class DepartmentEmployeeLink:
    employee_id: UUID
    state: str = "idle"


@dataclass
class LegacySkillSnapshot:
    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)


@dataclass
class RuntimeSkillSnapshot:
    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)
    state: str = "active"
    level: str = "basic"


# ------------------------------------------------------------------
# Scenario 1: Candidato sem skill
# ------------------------------------------------------------------


def scenario_candidate_no_skill() -> None:
    """Candidate without any skill gets score 0."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[candidate],
        department_snapshot=department,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.decision_code == "NO_SKILL_MATCH"
    assert result.approved is True
    assert list(result.trace.candidates_scored.values())[0] == 0.0
    print(f"[PASS] candidate_no_skill               | score=0.0 code={result.decision_code}")


# ------------------------------------------------------------------
# Scenario 2: Candidato com uma skill (runtime)
# ------------------------------------------------------------------


def scenario_candidate_one_skill() -> None:
    """Candidate with one matching Runtime skill gets score > 0."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python Development", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[candidate],
        department_snapshot=department,
        skill_runtime_snapshots=[skill],
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.decision_code == "BEST_SKILL_MATCH"
    assert result.approved is True
    assert list(result.trace.candidates_scored.values())[0] > 0.0
    print(f"[PASS] candidate_one_skill              | score={list(result.trace.candidates_scored.values())[0]:.2f} "
          f"code={result.decision_code}")


# ------------------------------------------------------------------
# Scenario 3: Múltiplas skills
# ------------------------------------------------------------------


def scenario_multiple_skills() -> None:
    """Candidate with multiple matching skills gets higher score."""
    cand_id = uuid4()
    task = TaskSnapshot(
        task_id=uuid4(), name="Full Stack",
        metadata=TaskMetadata(tags=["python", "javascript", "sql"]),
    )
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    skills = [
        RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id}),
        RuntimeSkillSnapshot(skill_id=uuid4(), name="JavaScript", employee_ids={cand_id}),
        RuntimeSkillSnapshot(skill_id=uuid4(), name="SQL", employee_ids={cand_id}),
    ]

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[candidate],
        department_snapshot=department,
        skill_runtime_snapshots=skills,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)
    score = list(result.trace.candidates_scored.values())[0]

    assert score == 1.0  # 3/3 = 1.0
    assert result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] multiple_skills                 | score={score:.2f} (3/3)")


# ------------------------------------------------------------------
# Scenario 4: Skill incompatível
# ------------------------------------------------------------------


def scenario_skill_incompatible() -> None:
    """Candidate has skill but it doesn't match required tags."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Rust Task", metadata=TaskMetadata(tags=["rust"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python Development", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[candidate],
        department_snapshot=department,
        skill_runtime_snapshots=[skill],
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.decision_code == "NO_SKILL_MATCH"
    print(f"[PASS] skill_incompatible              | code={result.decision_code}")


# ------------------------------------------------------------------
# Scenario 5: Empate
# ------------------------------------------------------------------


def scenario_tie() -> None:
    """Two candidates with same score produce a tie."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id), bob_id: DepartmentEmployeeLink(bob_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    skills = [
        RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id, bob_id}),
    ]

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_runtime_snapshots=skills,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.decision_code == "BEST_SKILL_MATCH"
    assert result.approved is True
    scores = result.trace.candidates_scored
    assert len(set(scores.values())) == 1  # same score
    print(f"[PASS] tie                             | scores={scores} (both equal)")


# ------------------------------------------------------------------
# Scenario 6: Desempate determinístico
# ------------------------------------------------------------------


def scenario_tiebreak_deterministic() -> None:
    """Tiebreak is deterministic — same input yields same chosen candidate."""
    alice_id = UUID("00000000-0000-0000-0000-000000000001")
    bob_id = UUID("00000000-0000-0000-0000-000000000002")
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id), bob_id: DepartmentEmployeeLink(bob_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    skills = [
        RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id, bob_id}),
    ]

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_runtime_snapshots=skills,
    )

    engine = DecisionEngine()
    r1 = engine.choose_best_candidate(context)
    r2 = engine.choose_best_candidate(context)

    chosen_str = str(r1.chosen_candidate_id)
    # Deterministic: lower UUID str wins tiebreak
    assert str(r1.chosen_candidate_id) == str(r2.chosen_candidate_id)
    assert chosen_str == "00000000-0000-0000-0000-000000000001"
    print(f"[PASS] tiebreak_deterministic           | chosen={chosen_str[:8]} (deterministic)")


# ------------------------------------------------------------------
# Scenario 7: Múltiplos candidatos
# ------------------------------------------------------------------


def scenario_multiple_candidates() -> None:
    """Three candidates with different scores are ranked correctly."""
    alice_id = uuid4()
    bob_id = uuid4()
    carol_id = uuid4()
    task = TaskSnapshot(
        task_id=uuid4(), name="Full Stack",
        metadata=TaskMetadata(tags=["python", "javascript"]),
    )
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
            carol_id: DepartmentEmployeeLink(carol_id),
        },
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    carol = EmployeeSnapshot(employee_id=carol_id, name="Carol", state="idle")

    skills = [
        RuntimeSkillSnapshot(skill_id=uuid4(), name="Python Development", employee_ids={alice_id}),
        RuntimeSkillSnapshot(skill_id=uuid4(), name="JavaScript", employee_ids={alice_id, bob_id}),
    ]

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob, carol],
        department_snapshot=department,
        skill_runtime_snapshots=skills,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    scores = result.trace.candidates_scored
    assert result.chosen_candidate_id == alice_id  # Alice has 2/2 = 1.0
    assert result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] multiple_candidates             | chosen={result.chosen_candidate_id.hex[:8]} "
          f"scores={scores}")


# ------------------------------------------------------------------
# Scenario 8: Fallback antigo (legacy skill snapshots)
# ------------------------------------------------------------------


def scenario_fallback_legacy() -> None:
    """When no skill_runtime_snapshots, uses context_skill_snapshots."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id), bob_id: DepartmentEmployeeLink(bob_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    legacy_skill = LegacySkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_snapshots=[legacy_skill],
        skill_runtime_snapshots=[],  # explicit empty — forces fallback
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.chosen_candidate_id == alice_id
    assert list(result.trace.candidates_scored.values())[0] > 0.0
    print(f"[PASS] fallback_legacy                 | chosen={result.chosen_candidate_id.hex[:8]} "
          f"(via context_skill_snapshots)")


# ------------------------------------------------------------------
# Scenario 9: Runtime + fallback misturado
# ------------------------------------------------------------------


def scenario_mixed_runtime_and_fallback() -> None:
    """Candidates with runtime skills use them; others fallback."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id), bob_id: DepartmentEmployeeLink(bob_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    runtime_skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id})
    legacy_skill = LegacySkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={bob_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_snapshots=[legacy_skill],
        skill_runtime_snapshots=[runtime_skill],
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    scores = result.trace.candidates_scored
    assert list(scores.values())[0] > 0.0
    print(f"[PASS] mixed_runtime_and_fallback       | scores={scores}")


# ------------------------------------------------------------------
# Scenario 10: Pipeline completo
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """Conversation -> Memory -> Knowledge -> Learning -> Skill Foundation -> Skill Runtime -> Decision."""
    from core.conversation import ConversationRuntime
    from core.knowledge.foundation import KnowledgeRuntime as FoundationKR
    from core.learning.foundation import LearningRuntime as FoundationLearningRuntime
    from core.memory import MemoryRuntime
    from core.skills.foundation import SkillRuntime as FoundationSkillRuntime

    cand_id = uuid4()
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Explain transformers.")
    session = ConversationRuntime.append_message(session, "assistant",
        "Transformers are a neural network architecture.")

    mem_records = [ConversationRuntime.create_memory_record(session, msg) for msg in session.messages]
    mem_snap = MemoryRuntime.create_snapshot(mem_records)

    know_records = MemoryRuntime.promote_records(mem_snap)
    know_snap = MemoryRuntime.promote_snapshot(mem_snap)

    learn_records = [FoundationLearningRuntime.promote_knowledge(kr) for kr in know_records]
    learn_snap = FoundationLearningRuntime.promote_snapshot(know_snap)

    skill_records = [FoundationSkillRuntime.promote_learning(rec) for rec in learn_records]
    # Manually attach cand_id to simulate employee association
    runtime_skills = [
        RuntimeSkillSnapshot(
            skill_id=r.skill_id,
            name=r.skill_name,
            employee_ids={cand_id},
        )
        for r in skill_records
    ]

    task = TaskSnapshot(
        task_id=uuid4(), name="AI Task",
        metadata=TaskMetadata(tags=["memory", "knowledge"]),
    )
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[candidate],
        department_snapshot=department,
        skill_runtime_snapshots=runtime_skills,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.decision_code == "BEST_SKILL_MATCH"
    assert result.approved is True
    assert result.chosen_candidate_id == cand_id
    print(f"[PASS] full_pipeline                   | {len(session.messages)} msgs -> "
          f"{len(mem_records)} mem -> {len(know_records)} know -> "
          f"{len(learn_records)} learn -> {len(skill_records)} skill -> "
          f"code={result.decision_code}")


# ------------------------------------------------------------------
# Scenario 11: Score crescente
# ------------------------------------------------------------------


def scenario_score_increasing() -> None:
    """More matching skills yield higher scores."""
    cand_id = uuid4()
    task = TaskSnapshot(
        task_id=uuid4(), name="Web Dev",
        metadata=TaskMetadata(tags=["html", "css", "javascript"]),
    )
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    # One match out of 3
    s1 = RuntimeSkillSnapshot(skill_id=uuid4(), name="HTML", employee_ids={cand_id})
    ctx1 = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[s1],
    )
    score1 = list(DecisionEngine().choose_best_candidate(ctx1).trace.candidates_scored.values())[0]

    # Two matches out of 3
    s2 = RuntimeSkillSnapshot(skill_id=uuid4(), name="CSS", employee_ids={cand_id})
    ctx2 = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[s1, s2],
    )
    score2 = list(DecisionEngine().choose_best_candidate(ctx2).trace.candidates_scored.values())[0]

    assert score2 > score1
    print(f"[PASS] score_increasing                | 1 skill={score1:.2f} 2 skills={score2:.2f}")


# ------------------------------------------------------------------
# Scenario 12: Score zero
# ------------------------------------------------------------------


def scenario_score_zero() -> None:
    """No matching skills yields score 0."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Rust Task", metadata=TaskMetadata(tags=["rust"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[skill],
    )

    result = DecisionEngine().choose_best_candidate(context)
    score = list(result.trace.candidates_scored.values())[0]

    assert score == 0.0
    print(f"[PASS] score_zero                      | score={score:.2f}")


# ------------------------------------------------------------------
# Scenario 13: Ranking correto
# ------------------------------------------------------------------


def scenario_correct_ranking() -> None:
    """Candidates are ranked by score descending."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(
        task_id=uuid4(), name="Python+JS",
        metadata=TaskMetadata(tags=["python", "javascript"]),
    )
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id), bob_id: DepartmentEmployeeLink(bob_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    skills = [
        RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id, bob_id}),
        RuntimeSkillSnapshot(skill_id=uuid4(), name="JavaScript", employee_ids={alice_id}),
    ]

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[alice, bob],
        department_snapshot=department, skill_runtime_snapshots=skills,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    assert result.chosen_candidate_id == alice_id  # Alice: 2/2=1.0, Bob: 1/2=0.5
    print(f"[PASS] correct_ranking                 | chosen=Alice score={result.trace.candidates_scored[str(alice_id)]:.2f}")


# ------------------------------------------------------------------
# Scenario 14: Compatibilidade reversa
# ------------------------------------------------------------------


def scenario_backward_compatibility() -> None:
    """Existing demo_decision_engine_foundation scenarios still pass."""
    # Uses old API: only skill_snapshots, no skill_runtime_snapshots
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Code Review", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = LegacySkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={alice_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[alice],
        department_snapshot=department, skill_snapshots=[skill],
    )

    result = DecisionEngine().choose_best_candidate(context)
    assert result.approved is True
    assert result.chosen_candidate_id == alice_id
    assert result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] backward_compatibility           | code={result.decision_code} "
          f"(no skill_runtime_snapshots needed)")


# ------------------------------------------------------------------
# Scenario 15: Determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce identical DecisionResult fields."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[skill],
    )

    r1 = DecisionEngine().choose_best_candidate(context)
    r2 = DecisionEngine().choose_best_candidate(context)

    assert r1.decision_code == r2.decision_code
    assert r1.approved == r2.approved
    assert r1.chosen_candidate_id == r2.chosen_candidate_id
    assert r1.trace.candidates_scored == r2.trace.candidates_scored
    print(f"[PASS] determinism                     | code={r1.decision_code} "
          f"score={list(r1.trace.candidates_scored.values())[0]:.2f} (identical)")


# ------------------------------------------------------------------
# Scenario 16: Trace correto
# ------------------------------------------------------------------


def scenario_trace_correct() -> None:
    """DecisionResult trace contains all expected stages and scores."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[skill],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert "select_candidates" in result.trace.stages_evaluated
    assert "evaluate_constraints" in result.trace.stages_evaluated
    assert "match_skills" in result.trace.stages_evaluated
    assert "resolve_priority" in result.trace.stages_evaluated
    assert len(result.trace.candidates_scored) > 0
    assert result.trace.execution_time_ms >= 0.0
    print(f"[PASS] trace_correct                   | stages={result.trace.stages_evaluated} "
          f"scores={result.trace.candidates_scored}")


# ------------------------------------------------------------------
# Scenario 17: DecisionResult correto
# ------------------------------------------------------------------


def scenario_decision_result_correct() -> None:
    """DecisionResult has all fields populated correctly."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department, skill_runtime_snapshots=[skill],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert isinstance(result, DecisionResult)
    assert result.decision_id is not None
    assert result.approved is True
    assert result.chosen_candidate_id == cand_id
    assert result.decision_code == "BEST_SKILL_MATCH"
    assert len(result.explanation) > 0
    print(f"[PASS] decision_result_correct          | id={result.decision_id.hex[:8]} "
          f"approved={result.approved} code={result.decision_code}")


# ------------------------------------------------------------------
# Scenario 18: SkillMatcher.calculate_score normalizado
# ------------------------------------------------------------------


def test_calculate_score_normalized() -> None:
    """calculate_score returns normalized 0.0-1.0 values."""
    cand_id = uuid4()
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    # 1 match out of 2 required = 0.5
    score = SkillMatcher.calculate_score(cand_id, {"python", "java"}, [skill])
    assert score == 0.5
    print(f"[PASS] calculate_score_normalized       | score={score} (1/2)")


# ------------------------------------------------------------------
# Scenario 19: SkillMatcher.normalize_score edge cases
# ------------------------------------------------------------------


def test_normalize_score_edges() -> None:
    """normalize_score handles edge cases."""
    assert SkillMatcher.normalize_score(0.0, 0.0) == 0.0
    assert SkillMatcher.normalize_score(5.0, 0.0) == 0.0
    assert SkillMatcher.normalize_score(0.0, 5.0) == 0.0
    assert SkillMatcher.normalize_score(3.0, 5.0) == 0.6
    assert SkillMatcher.normalize_score(10.0, 5.0) == 1.0  # capped
    print(f"[PASS] normalize_score_edges            | all edge cases correct")


# ------------------------------------------------------------------
# Scenario 20: Empty required skills
# ------------------------------------------------------------------


def test_empty_required_skills() -> None:
    """Empty required skills set returns score 0."""
    cand_id = uuid4()
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    score = SkillMatcher.calculate_score(cand_id, set(), [skill])
    assert score == 0.0
    print(f"[PASS] empty_required_skills            | score={score}")


# ------------------------------------------------------------------
# Scenario 21: SkillMatcher.match_candidate with no candidate_id
# ------------------------------------------------------------------


def test_match_candidate_no_id() -> None:
    """Candidate without extractable ID gets score 0."""
    score = SkillMatcher.match_candidate(
        candidate="not_a_snapshot",
        required_skills={"python"},
        skill_runtime_snapshots=[],
        context_skill_snapshots=[],
    )
    assert score == 0.0
    print(f"[PASS] match_candidate_no_id            | score={score}")


# ------------------------------------------------------------------
# Scenario 22: Policy constraint via Decision Engine with runtime skills
# ------------------------------------------------------------------


def scenario_policy_with_runtime_skills() -> None:
    """Policy constraint rejects candidate even with matching runtime skills."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    candidate = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")
    skill = RuntimeSkillSnapshot(skill_id=uuid4(), name="Python", employee_ids={cand_id})

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "All candidates blocked."

    block_constraint = Constraint(
        constraint_id="block_all",
        description="Block everyone",
        check=_block_all,
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task, candidate_snapshots=[candidate],
        department_snapshot=department,
        skill_runtime_snapshots=[skill],
        policy_constraints=[block_constraint],
    )

    result = DecisionEngine().choose_best_candidate(context)
    assert result.approved is False
    assert result.decision_code == "POLICY_DENIED"
    print(f"[PASS] policy_with_runtime_skills       | code={result.decision_code}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Decision Engine + Skill Integration Demo")
    print("=" * 58)
    print()

    scenario_candidate_no_skill()
    scenario_candidate_one_skill()
    scenario_multiple_skills()
    scenario_skill_incompatible()
    scenario_tie()
    scenario_tiebreak_deterministic()
    scenario_multiple_candidates()
    scenario_fallback_legacy()
    scenario_mixed_runtime_and_fallback()
    scenario_full_pipeline()
    scenario_score_increasing()
    scenario_score_zero()
    scenario_correct_ranking()
    scenario_backward_compatibility()
    scenario_determinism()
    scenario_trace_correct()
    scenario_decision_result_correct()
    test_calculate_score_normalized()
    test_normalize_score_edges()
    test_empty_required_skills()
    test_match_candidate_no_id()
    scenario_policy_with_runtime_skills()

    print()
    print("=" * 58)
    print("All Decision Skill Integration scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
