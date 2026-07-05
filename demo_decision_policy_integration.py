"""Integration demo: Decision Engine delegates policy to Policy Engine.

Demonstrates that evaluate_constraints() no longer contains internal
rules, but instead builds a PolicyContext and calls PolicyEngine.evaluate().

All scenarios use plain dataclasses — no Runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from core.decision.runtime import DecisionContextBuilder, DecisionEngine, DecisionTrace
from core.policies.runtime import Constraint, PolicyResult, Rule


# ------------------------------------------------------------------
# Plain snapshot-like objects (no Runtime involved)
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
class SkillSnapshot:
    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)


# ------------------------------------------------------------------
# Scenario 1: Candidate approved by Policy Engine
# ------------------------------------------------------------------


def scenario_candidate_approved() -> None:
    """One candidate, no constraints/rules — Policy Engine approves."""
    cand_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Simple Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    alice = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert result.approved is True
    assert result.chosen_candidate_id == cand_id
    assert result.decision_code == "NO_SKILL_MATCH"
    assert result.trace.policy_evaluations[str(cand_id)] is not None
    print(f"[PASS] candidate_approved            | approved={result.approved} "
          f"candidate={str(cand_id)[:8]} policy_result=approved")
    _print_trace_policy_summary(result.trace, cand_id)


# ------------------------------------------------------------------
# Scenario 2: Candidate blocked by hard constraint
# ------------------------------------------------------------------


def scenario_blocked_by_constraint() -> None:
    """Candidate is blocked by a hard Policy Engine constraint."""
    cand_id = uuid4()

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "All candidates blocked by hard constraint"

    task = TaskSnapshot(task_id=uuid4(), name="Restricted Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    alice = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle", role="analyst")

    constraint = Constraint(
        constraint_id="global_block",
        description="Block every candidate unconditionally",
        check=_block_all,
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        policy_constraints=[constraint],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert result.approved is False
    assert result.decision_code == "POLICY_DENIED"
    assert str(cand_id) in result.trace.rejection_reasons
    assert str(cand_id) in result.trace.policy_evaluations

    policy_result: PolicyResult = result.trace.policy_evaluations[str(cand_id)]
    assert policy_result.approved is False
    assert policy_result.violation_code == "global_block"
    print(f"[PASS] blocked_by_constraint          | approved={result.approved} "
          f"code={result.decision_code} violation={policy_result.violation_code}")
    _print_trace_policy_summary(result.trace, cand_id)


# ------------------------------------------------------------------
# Scenario 3: Candidate blocked by rule
# ------------------------------------------------------------------


def scenario_blocked_by_rule() -> None:
    """Candidate passes constraints but is blocked by a rule."""
    cand_id = uuid4()

    def _constraint_pass(ctx: object) -> tuple[bool, str]:
        return True, ""

    def _rule_block_analyst(ctx: object) -> tuple[bool, str]:
        role = ctx.actor_attributes.get("role", "")
        if role == "analyst":
            return False, "Analysts cannot be assigned to strategic tasks"
        return True, ""

    task = TaskSnapshot(task_id=uuid4(), name="Strategic Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Strategy",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    alice = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle", role="analyst")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        policy_constraints=[
            Constraint(constraint_id="always_ok", description="Pass-through", check=_constraint_pass),
        ],
        policy_rules=[
            Rule(rule_id="no_analyst_strategic", description="No analysts on strategic", check=_rule_block_analyst, on_fail="block"),
        ],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert result.approved is False
    assert result.decision_code == "POLICY_DENIED"
    assert str(cand_id) in result.trace.rejection_reasons
    assert "Analysts cannot be assigned" in result.trace.rejection_reasons[str(cand_id)]

    policy_result: PolicyResult = result.trace.policy_evaluations[str(cand_id)]
    assert policy_result.approved is False
    assert policy_result.violation_code == "no_analyst_strategic"
    print(f"[PASS] blocked_by_rule                | approved={result.approved} "
          f"code={result.decision_code} rule={policy_result.violation_code}")
    _print_trace_policy_summary(result.trace, cand_id)


# ------------------------------------------------------------------
# Scenario 4: Multiple candidates, some pass policies
# ------------------------------------------------------------------


def scenario_multiple_candidates_some_blocked() -> None:
    """Three candidates; two pass policy, one is blocked by constraint."""
    alice_id = uuid4()
    bob_id = uuid4()
    charlie_id = uuid4()

    def _block_charlie(ctx: object) -> tuple[bool, str]:
        cand = ctx.snapshots.get("candidate", {})
        cid = getattr(cand, "employee_id", None)
        if cid == charlie_id:
            return False, "Charlie is blocked"
        return True, ""

    skill_id = uuid4()
    task = TaskSnapshot(
        task_id=uuid4(), name="Python Review",
        metadata=TaskMetadata(tags=["python"]),
    )
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
            charlie_id: DepartmentEmployeeLink(charlie_id),
        },
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    charlie = EmployeeSnapshot(employee_id=charlie_id, name="Charlie", state="idle")
    skill = SkillSnapshot(skill_id=skill_id, name="Python Development", employee_ids={alice_id, bob_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob, charlie],
        department_snapshot=dept,
        skill_snapshots=[skill],
        policy_constraints=[
            Constraint(constraint_id="block_charlie", description="Block Charlie", check=_block_charlie),
        ],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert result.approved is True
    assert result.chosen_candidate_id in (alice_id, bob_id)
    assert str(charlie_id) in result.trace.rejection_reasons
    assert str(charlie_id) in result.trace.policy_evaluations
    assert str(alice_id) in result.trace.policy_evaluations
    assert str(bob_id) in result.trace.policy_evaluations

    charlie_policy: PolicyResult = result.trace.policy_evaluations[str(charlie_id)]
    assert charlie_policy.approved is False

    alice_policy: PolicyResult = result.trace.policy_evaluations[str(alice_id)]
    assert alice_policy.approved is True

    print(f"[PASS] multiple_candidates_some_blocked | approved={result.approved} "
          f"chosen={str(result.chosen_candidate_id)[:8]} "
          f"rejected={len(result.trace.rejection_reasons)} candidates")
    _print_trace_policy_summary(result.trace, alice_id)


# ------------------------------------------------------------------
# Scenario 5: Best candidate chosen correctly after policy passes
# ------------------------------------------------------------------


def scenario_best_candidate_chosen() -> None:
    """Two candidates pass policy; the one with better skill match is chosen."""
    alice_id = uuid4()
    bob_id = uuid4()
    python_skill_id = uuid4()
    rust_skill_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(), name="Full Stack Review",
        metadata=TaskMetadata(tags=["python", "rust"]),
    )
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )
    # Alice knows Python, Bob knows Rust, task requires both
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    python_skill = SkillSnapshot(skill_id=python_skill_id, name="Python Development", employee_ids={alice_id})
    rust_skill = SkillSnapshot(skill_id=rust_skill_id, name="Rust Development", employee_ids={bob_id})

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=dept,
        skill_snapshots=[python_skill, rust_skill],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert result.approved is True
    assert result.chosen_candidate_id in (alice_id, bob_id)
    assert result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] best_candidate_chosen           | approved={result.approved} "
          f"chosen={str(result.chosen_candidate_id)[:8]} "
          f"code={result.decision_code} score={result.trace.candidates_scored}")


# ------------------------------------------------------------------
# Scenario 6: DecisionTrace contains Policy Engine evaluation data
# ------------------------------------------------------------------


def scenario_trace_contains_policy_data() -> None:
    """Verify DecisionTrace.policy_evaluations is correctly populated."""
    cand_id = uuid4()

    def _pass_ok(ctx: object) -> tuple[bool, str]:
        return True, "Everything OK"

    task = TaskSnapshot(task_id=uuid4(), name="Trace Check Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={cand_id: DepartmentEmployeeLink(cand_id)},
    )
    alice = EmployeeSnapshot(employee_id=cand_id, name="Alice", state="idle")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        policy_constraints=[
            Constraint(constraint_id="c1", description="Check OK", check=_pass_ok),
        ],
        policy_rules=[
            Rule(rule_id="r1", description="Rule OK", check=_pass_ok),
        ],
    )

    result = DecisionEngine().choose_best_candidate(context)

    assert isinstance(result.trace, DecisionTrace)
    assert "evaluate_constraints" in result.trace.stages_evaluated
    assert str(cand_id) in result.trace.policy_evaluations

    pr: PolicyResult = result.trace.policy_evaluations[str(cand_id)]
    assert pr.approved is True
    assert pr.policy_id == "decision_policy"
    assert pr.trace.execution_order == ["constraints", "rules"]
    assert pr.trace.constraints_checked["c1"] is True
    assert pr.trace.rules_evaluated["r1"] is True
    assert pr.trace.execution_time_ms >= 0

    print(f"[PASS] trace_contains_policy_data      | stages={result.trace.stages_evaluated} "
          f"candidates_in_trace={len(result.trace.policy_evaluations)} "
          f"constraints={len(pr.trace.constraints_checked)} rules={len(pr.trace.rules_evaluated)}")


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _print_trace_policy_summary(trace: DecisionTrace, cand_id: UUID) -> None:
    key = str(cand_id)
    if key in trace.policy_evaluations:
        pr: PolicyResult = trace.policy_evaluations[key]
        print(f"  Policy trace: approved={pr.approved} "
              f"violation={pr.violation_code} "
              f"order={pr.trace.execution_order}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("Decision Engine + Policy Engine Integration Demo")
    print("=" * 62)
    print()

    scenario_candidate_approved()
    scenario_blocked_by_constraint()
    scenario_blocked_by_rule()
    scenario_multiple_candidates_some_blocked()
    scenario_best_candidate_chosen()
    scenario_trace_contains_policy_data()

    print()
    print("=" * 62)
    print("All integration scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
