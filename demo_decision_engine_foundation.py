"""Foundation demo for the Decision Engine — no Runtime dependencies.

This demonstration uses only plain Python dataclasses to simulate
snapshots. No CompanyRuntime, DepartmentRuntime, EmployeeRuntime,
TaskRuntime, or SkillRuntime is instantiated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from core.decision.runtime import DecisionContextBuilder, DecisionEngine
from core.policies.runtime import Constraint, Rule


# ------------------------------------------------------------------
# Plain snapshot-like objects (no Runtime involved)
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    """Simple task representation for demo purposes."""

    task_id: UUID
    name: str
    metadata: object = None


@dataclass
class TaskMetadata:
    """Minimal task metadata carrying skill requirement tags."""

    tags: list[str] = field(default_factory=list)


@dataclass
class EmployeeSnapshot:
    """Simple employee representation for demo purposes."""

    employee_id: UUID
    name: str
    state: str = "idle"
    role: str = "generic"
    task_id: str | None = None


@dataclass
class DepartmentSnapshot:
    """Simple department representation for demo purposes."""

    department_id: UUID
    name: str
    employees: dict[UUID, object] = field(default_factory=dict)


@dataclass
class DepartmentEmployeeLink:
    """Minimal link used inside department.employees."""

    employee_id: UUID
    state: str = "idle"


@dataclass
class SkillSnapshot:
    """Simple skill representation for demo purposes."""

    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)


# ------------------------------------------------------------------
# Demo scenarios
# ------------------------------------------------------------------


def run_scenario_best_skill_match() -> None:
    """Scenario 1: Two candidates, one has the required skill."""
    print("=" * 60)
    print("SCENARIO 1: BEST_SKILL_MATCH")
    print("=" * 60)

    alice_id = uuid4()
    bob_id = uuid4()
    skill_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(),
        name="Code Review",
        metadata=TaskMetadata(tags=["python"]),
    )

    department = DepartmentSnapshot(
        department_id=uuid4(),
        name="Engineering",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )

    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    skill = SkillSnapshot(
        skill_id=skill_id,
        name="Python Development",
        employee_ids={alice_id},
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_snapshots=[skill],
        active_policies={},
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    print(f"Decision Code : {result.decision_code}")
    print(f"Approved      : {result.approved}")
    print(f"Chosen        : {result.chosen_candidate_id}")
    print(f"Explanation   : {result.explanation}")
    print(f"Stages        : {result.trace.stages_evaluated}")
    print(f"Candidates    : {len(result.trace.candidates_selected)} selected")
    print(f"Scores        : {result.trace.candidates_scored}")
    for uid_str, score in result.trace.candidates_scored.items():
        if score > 0:
            name = "Alice" if UUID(uid_str) == alice_id else "Bob"
            print(f"  -> {name} matched with score {score}")

    assert result.approved is True
    assert result.chosen_candidate_id == alice_id
    assert result.decision_code == "BEST_SKILL_MATCH"
    print("[PASS] Alice correctly chosen for her Python skill.\n")


def run_scenario_no_skill_match() -> None:
    """Scenario 2: Two candidates, neither has any matching skill."""
    print("=" * 60)
    print("SCENARIO 2: NO_SKILL_MATCH")
    print("=" * 60)

    alice_id = uuid4()
    bob_id = uuid4()
    skill_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(),
        name="Rust Code Review",
        metadata=TaskMetadata(tags=["rust"]),
    )

    department = DepartmentSnapshot(
        department_id=uuid4(),
        name="Engineering",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )

    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")

    # Only Python skill — does not match "rust" requirement
    skill = SkillSnapshot(
        skill_id=skill_id,
        name="Python Development",
        employee_ids={alice_id},
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=department,
        skill_snapshots=[skill],
        active_policies={},
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    print(f"Decision Code : {result.decision_code}")
    print(f"Approved      : {result.approved}")
    print(f"Chosen        : {result.chosen_candidate_id}")
    print(f"Explanation   : {result.explanation}")
    print(f"Scores        : {result.trace.candidates_scored}")

    assert result.approved is True  # still approves, just no skill match
    assert result.decision_code == "NO_SKILL_MATCH"
    print("[PASS] No skill match detected, fallback candidate chosen.\n")


def run_scenario_policy_denied() -> None:
    """Scenario 3: Candidate is blocked by policy."""
    print("=" * 60)
    print("SCENARIO 3: POLICY_DENIED")
    print("=" * 60)

    alice_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(),
        name="Sensitive Task",
        metadata=TaskMetadata(),
    )

    department = DepartmentSnapshot(
        department_id=uuid4(),
        name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )

    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    def _block_if_blocklisted(ctx: object) -> tuple[bool, str]:
        pol_ctx = ctx  # PolicyContext
        cand = pol_ctx.snapshots.get("candidate", {})
        cand_id = getattr(cand, "employee_id", None)
        if cand_id is not None and cand_id == alice_id:
            return False, "Candidate is in the policy blocklist."
        return True, ""

    blocked_constraint = Constraint(
        constraint_id="blocked_employee",
        description="Block employees in the blocklist",
        check=_block_if_blocklisted,
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=department,
        policy_constraints=[blocked_constraint],
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    print(f"Decision Code : {result.decision_code}")
    print(f"Approved      : {result.approved}")
    print(f"Explanation   : {result.explanation}")
    print(f"Rejections    : {result.trace.rejection_reasons}")

    assert result.approved is False
    assert result.decision_code == "POLICY_DENIED"
    print("[PASS] Alice correctly denied by blocklist constraint via Policy Engine.\n")


def run_scenario_no_available_candidate() -> None:
    """Scenario 4: No candidates are idle."""
    print("=" * 60)
    print("SCENARIO 4: NO_AVAILABLE_CANDIDATE")
    print("=" * 60)

    alice_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(),
        name="Urgent Task",
        metadata=TaskMetadata(),
    )

    department = DepartmentSnapshot(
        department_id=uuid4(),
        name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )

    # Alice is busy, not idle
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="busy")

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=department,
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    print(f"Decision Code : {result.decision_code}")
    print(f"Approved      : {result.approved}")
    print(f"Explanation   : {result.explanation}")

    assert result.approved is False
    assert result.decision_code == "NO_AVAILABLE_CANDIDATE"
    print("[PASS] No idle candidate detected.\n")


def run_scenario_role_mismatch() -> None:
    """Scenario 5: Candidate fails role requirement constraint."""
    print("=" * 60)
    print("SCENARIO 5: ROLE CONSTRAINT FAILURE")
    print("=" * 60)

    alice_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(),
        name="Strategic Planning",
        metadata=TaskMetadata(),
    )

    department = DepartmentSnapshot(
        department_id=uuid4(),
        name="Strategy",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )

    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle", role="analyst")

    def _role_must_be_strategist(ctx: object) -> tuple[bool, str]:
        role = ctx.actor_attributes.get("role", "")
        if role != "strategist":
            return False, f"Role mismatch: requires strategist, has {role}."
        return True, ""

    role_rule = Rule(
        rule_id="required_role",
        description="Candidate must have role strategist",
        check=_role_must_be_strategist,
        on_fail="block",
    )

    context = DecisionContextBuilder().build_assignment_context(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=department,
        policy_rules=[role_rule],
    )

    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    print(f"Decision Code : {result.decision_code}")
    print(f"Approved      : {result.approved}")
    print(f"Explanation   : {result.explanation}")
    print(f"Rejections    : {result.trace.rejection_reasons}")

    assert result.approved is False
    assert result.decision_code == "POLICY_DENIED"
    print("[PASS] Alice correctly denied due to role mismatch (Rule via Policy Engine).\n")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    run_scenario_best_skill_match()
    run_scenario_no_skill_match()
    run_scenario_policy_denied()
    run_scenario_no_available_candidate()
    run_scenario_role_mismatch()
    print("=" * 60)
    print("ALL SCENARIOS PASSED — Decision Engine foundation is sound.")
    print("=" * 60)


if __name__ == "__main__":
    main()
