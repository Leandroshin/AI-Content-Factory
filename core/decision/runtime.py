"""Runtime implementation for the Decision Engine foundation.

Stateless, deterministic decision engine that receives a context
and returns a decision without mutating any runtime state.

Policy constraint evaluation is delegated to the Policy Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4
import time

from core.policies.runtime import Constraint, PolicyContext, PolicyEngine, PolicyResult, Rule


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Immutable input context for deterministic decision making.

    Contains only snapshots — never runtime objects.
    All fields use generic Any type to remain runtime-agnostic.
    """

    task_snapshot: Any
    candidate_snapshots: list[Any]
    department_snapshot: Any = None
    skill_snapshots: list[Any] = field(default_factory=list)
    skill_runtime_snapshots: list[Any] = field(default_factory=list)
    active_policies: dict[str, Any] = field(default_factory=dict)
    policy_constraints: list[Any] = field(default_factory=list)
    policy_rules: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Structured execution trace representing steps, scores, and rules evaluated."""

    stages_evaluated: list[str] = field(default_factory=list)
    candidates_selected: list[UUID] = field(default_factory=list)
    candidates_scored: dict[str, float] = field(default_factory=dict)
    constraints_checked: dict[str, bool] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    policy_evaluations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Outcome of a Decision Engine evaluation."""

    decision_id: UUID
    approved: bool
    chosen_candidate_id: UUID | None
    decision_code: str
    trace: DecisionTrace
    explanation: str


class DecisionContextBuilder:
    """Helper component to assemble DecisionContext from arbitrary snapshots.

    This builder is runtime-agnostic — it accepts plain Python objects
    or dataclass instances as long as they have the expected attributes.
    """

    def build_assignment_context(
        self,
        task_snapshot: Any,
        candidate_snapshots: list[Any],
        department_snapshot: Any = None,
        skill_snapshots: list[Any] | None = None,
        skill_runtime_snapshots: list[Any] | None = None,
        active_policies: dict[str, Any] | None = None,
        policy_constraints: list[Any] | None = None,
        policy_rules: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DecisionContext:
        """Constructs a DecisionContext from the given snapshots."""
        return DecisionContext(
            task_snapshot=task_snapshot,
            candidate_snapshots=list(candidate_snapshots),
            department_snapshot=department_snapshot,
            skill_snapshots=list(skill_snapshots) if skill_snapshots is not None else [],
            skill_runtime_snapshots=list(skill_runtime_snapshots) if skill_runtime_snapshots is not None else [],
            active_policies=dict(active_policies) if active_policies is not None else {},
            policy_constraints=list(policy_constraints) if policy_constraints is not None else [],
            policy_rules=list(policy_rules) if policy_rules is not None else [],
            metadata=dict(metadata) if metadata is not None else {},
        )


class SkillMatcher:
    """Stateless skill matcher for the Decision Engine.

    Matches candidates against required skills using real Skill Runtime
    snapshots when available, falling back to legacy skill snapshots.

    No AI, no inference, no embeddings — purely deterministic.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def match_candidate(
        candidate: Any,
        required_skills: set[str],
        skill_runtime_snapshots: list[Any],
        context_skill_snapshots: list[Any],
    ) -> float:
        """Score a single candidate against required skills.

        Priority:
        1. Real skills from Skill Runtime (skill_runtime_snapshots)
        2. Legacy fallback (context_skill_snapshots)

        Args:
            candidate: The candidate snapshot to evaluate.
            required_skills: Set of normalized required skill names.
            skill_runtime_snapshots: Snapshots from Skill Runtime (stateful).
            context_skill_snapshots: Legacy skill snapshots from context.

        Returns:
            A float score (0.0 = no match).
        """
        cand_id = SkillMatcher._extract_id(candidate)
        if cand_id is None:
            return 0.0

        real_skills = SkillMatcher._get_candidate_skills(
            cand_id, skill_runtime_snapshots,
        )
        if real_skills:
            return SkillMatcher.calculate_score(
                cand_id, required_skills, real_skills,
            )

        return SkillMatcher._legacy_score(
            cand_id, required_skills, context_skill_snapshots,
        )

    @staticmethod
    def calculate_score(
        candidate_id: UUID,
        required_skills: set[str],
        candidate_skills: list[Any],
    ) -> float:
        """Calculate deterministic match score from a list of skills.

        Args:
            candidate_id: The candidate's UUID (unused, kept for API consistency).
            required_skills: Set of normalized required skill names.
            candidate_skills: List of skill snapshots belonging to the candidate.

        Returns:
            Normalized score between 0.0 and 1.0.
        """
        if not required_skills:
            return 0.0

        match_count = 0.0
        for skill in candidate_skills:
            skill_name = getattr(skill, "name", "") or ""
            skill_id = getattr(skill, "skill_id", None)

            skill_name_lower = str(skill_name).strip().lower()
            for req in required_skills:
                if req in skill_name_lower or skill_name_lower in req:
                    match_count += 1.0
                    break

            if skill_id is not None and str(skill_id) in required_skills:
                match_count += 1.0

        return SkillMatcher.normalize_score(match_count, float(len(required_skills)))

    @staticmethod
    def normalize_score(raw_score: float, max_possible: float) -> float:
        """Normalize a raw score to a 0.0–1.0 range.

        Args:
            raw_score: The raw match count.
            max_possible: Maximum possible score (denominator).

        Returns:
            Normalized score between 0.0 and 1.0.
        """
        if max_possible <= 0.0:
            return 0.0
        return min(raw_score / max_possible, 1.0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_id(candidate: Any) -> UUID | None:
        """Safely extract the UUID identifier from a candidate snapshot."""
        if hasattr(candidate, "employee_id"):
            val = getattr(candidate, "employee_id")
            if isinstance(val, UUID):
                return val
        if hasattr(candidate, "id"):
            val = getattr(candidate, "id")
            if isinstance(val, UUID):
                return val
        return None

    @staticmethod
    def _get_candidate_skills(
        candidate_id: UUID,
        skill_runtime_snapshots: list[Any],
    ) -> list[Any]:
        """Collect real skills for a candidate from Skill Runtime snapshots."""
        if not skill_runtime_snapshots:
            return []
        return [
            snap for snap in skill_runtime_snapshots
            if hasattr(snap, "employee_ids")
            and candidate_id in getattr(snap, "employee_ids")
        ]

    @staticmethod
    def _legacy_score(
        candidate_id: UUID,
        required_skills: set[str],
        context_skill_snapshots: list[Any],
    ) -> float:
        """Fallback: score using legacy skill snapshots."""
        if not context_skill_snapshots:
            return 0.0

        candidate_skills: list[Any] = []
        for snap in context_skill_snapshots:
            emp_ids = getattr(snap, "employee_ids", set())
            if candidate_id in emp_ids:
                skill_name = getattr(snap, "name", "") or ""
                skill_id = getattr(snap, "skill_id", None)
                candidate_skills.append(
                    _SkillRef(
                        name=str(skill_name),
                        skill_id=skill_id,
                    )
                )

        if not candidate_skills:
            return 0.0

        return SkillMatcher.calculate_score(
            candidate_id, required_skills, candidate_skills,
        )


@dataclass(frozen=True, slots=True)
class _SkillRef:
    """Minimal skill reference for legacy scoring."""
    name: str
    skill_id: UUID | None


class DecisionEngine:
    """Stateless, deterministic decision evaluation engine.

    The engine never mutates runtime state, never executes tasks,
    never publishes events, never persists data, and never uses AI.
    """

    # ------------------------------------------------------------------
    # Pipeline step 1: select_candidates
    # ------------------------------------------------------------------

    def select_candidates(self, context: DecisionContext) -> list[Any]:
        """Filter raw candidate list based on department membership and availability."""
        selected = []
        for candidate in context.candidate_snapshots:
            cand_id = self._get_id(candidate)
            if cand_id is None:
                continue

            # Department filter
            if context.department_snapshot is not None:
                dept_employees = getattr(context.department_snapshot, "employees", {})
                if cand_id not in dept_employees:
                    continue

            # Availability filter — only idle candidates
            state = getattr(candidate, "state", None)
            if state is not None and str(state).lower() != "idle":
                continue

            selected.append(candidate)
        return selected

    # ------------------------------------------------------------------
    # Pipeline step 2: evaluate_constraints
    # ------------------------------------------------------------------

    def evaluate_constraints(self, context: DecisionContext, candidate: Any) -> PolicyResult:
        """Delegate constraint and rule evaluation to the Policy Engine.

        Constructs a PolicyContext from the DecisionContext and candidate,
        then calls PolicyEngine.evaluate() with the configured constraints and rules.
        """
        cand_id = self._get_id(candidate)

        actor_attrs: dict[str, object] = {}
        role = getattr(candidate, "role", None)
        if role is not None:
            actor_attrs["role"] = str(role)
        state = getattr(candidate, "state", None)
        if state is not None:
            actor_attrs["state"] = str(state)

        target_attrs: dict[str, object] = {}
        task_id = getattr(context.task_snapshot, "task_id", None)
        if task_id is not None:
            target_attrs["task_id"] = str(task_id)
        task_name = getattr(context.task_snapshot, "name", None)
        if task_name is not None:
            target_attrs["task_name"] = str(task_name)

        policy_ctx = PolicyContext(
            action=str(context.metadata.get("decision_action", "assign_task")),
            actor_id=str(cand_id) if cand_id else "",
            actor_attributes=actor_attrs,
            target_id=str(task_id) if task_id else "",
            target_attributes=target_attrs,
            snapshots={
                "task": context.task_snapshot,
                "candidate": candidate,
                "active_policies": context.active_policies,
            },
            metadata=context.metadata,
        )

        return PolicyEngine.evaluate(
            context=policy_ctx,
            constraints=list(context.policy_constraints),
            rules=list(context.policy_rules),
            policy_id=str(context.metadata.get("policy_id", "decision_policy")),
        )

    # ------------------------------------------------------------------
    # Pipeline step 3: match_skills
    # ------------------------------------------------------------------

    def match_skills(self, context: DecisionContext, candidates: list[Any]) -> list[tuple[Any, float]]:
        """Score candidates based on skill match intersection.

        Delegates to SkillMatcher which uses real Skill Runtime skills
        when available, falling back to legacy context skill snapshots.
        """
        required_skills: list[str] = []

        task_metadata = getattr(context.task_snapshot, "metadata", None)
        if task_metadata is not None:
            if hasattr(task_metadata, "tags"):
                required_skills.extend(getattr(task_metadata, "tags", []))
            elif isinstance(task_metadata, dict):
                required_skills.extend(task_metadata.get("tags", []))

        policy_skills = context.active_policies.get("required_skills", [])
        required_skills.extend(policy_skills)

        required_skills_set = {str(skill).strip().lower() for skill in required_skills}

        scored_candidates = []
        for candidate in candidates:
            score = SkillMatcher.match_candidate(
                candidate=candidate,
                required_skills=required_skills_set,
                skill_runtime_snapshots=context.skill_runtime_snapshots,
                context_skill_snapshots=context.skill_snapshots,
            )
            scored_candidates.append((candidate, score))
        return scored_candidates

    # ------------------------------------------------------------------
    # Pipeline step 4: resolve_priority
    # ------------------------------------------------------------------

    def resolve_priority(
        self, context: DecisionContext, candidate_scores: list[tuple[Any, float]]
    ) -> list[tuple[Any, float]]:
        """Sort candidates descending by score, deterministically by UUID on ties."""
        return sorted(
            candidate_scores,
            key=lambda item: (-item[1], str(self._get_id(item[0]))),
        )

    # ------------------------------------------------------------------
    # Pipeline step 5: choose_best_candidate (full orchestration)
    # ------------------------------------------------------------------

    def choose_best_candidate(self, context: DecisionContext) -> DecisionResult:
        """Orchestrate the decision pipeline and return the final DecisionResult."""
        start_time = time.perf_counter()

        stages: list[str] = []
        trace_selected: list[UUID] = []
        trace_scored: dict[str, float] = {}
        trace_checked: dict[str, bool] = {}
        trace_rejections: dict[str, str] = {}

        # 1. select_candidates
        stages.append("select_candidates")
        selected = self.select_candidates(context)
        for cand in selected:
            cand_id = self._get_id(cand)
            if cand_id is not None:
                trace_selected.append(cand_id)

        if not selected:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return DecisionResult(
                decision_id=uuid4(),
                approved=False,
                chosen_candidate_id=None,
                decision_code="NO_AVAILABLE_CANDIDATE",
                trace=DecisionTrace(
                    stages_evaluated=stages,
                    execution_time_ms=elapsed,
                ),
                explanation="No available candidates matched the department and availability criteria.",
            )

        # 2. evaluate_constraints — delegated to Policy Engine
        stages.append("evaluate_constraints")
        passed_constraints: list[Any] = []
        policy_evaluations: dict[str, Any] = {}
        for cand in selected:
            cand_id = self._get_id(cand)
            cand_id_str = str(cand_id)
            policy_result = self.evaluate_constraints(context, cand)
            policy_evaluations[cand_id_str] = policy_result
            trace_checked[cand_id_str] = policy_result.approved
            if policy_result.approved:
                passed_constraints.append(cand)
            else:
                trace_rejections[cand_id_str] = policy_result.violation_detail

        if not passed_constraints:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return DecisionResult(
                decision_id=uuid4(),
                approved=False,
                chosen_candidate_id=None,
                decision_code="POLICY_DENIED",
                trace=DecisionTrace(
                    stages_evaluated=stages,
                    candidates_selected=trace_selected,
                    constraints_checked=trace_checked,
                    rejection_reasons=trace_rejections,
                    execution_time_ms=elapsed,
                    policy_evaluations=policy_evaluations,
                ),
                explanation="All available candidates failed policy constraint checks.",
            )

        # 3. match_skills
        stages.append("match_skills")
        candidate_scores = self.match_skills(context, passed_constraints)
        for cand, score in candidate_scores:
            cand_id_str = str(self._get_id(cand))
            trace_scored[cand_id_str] = score

        # 4. resolve_priority
        stages.append("resolve_priority")
        ranked = self.resolve_priority(context, candidate_scores)

        # 5. choose best
        best_candidate, best_score = ranked[0]
        chosen_id = self._get_id(best_candidate)

        elapsed = (time.perf_counter() - start_time) * 1000.0

        max_score = max(score for _, score in ranked)
        if max_score <= 0.0:
            decision_code = "NO_SKILL_MATCH"
            explanation = (
                f"No candidate has a matching skill. "
                f"Selected {chosen_id} with score {best_score} as fallback."
            )
        else:
            decision_code = "BEST_SKILL_MATCH"
            explanation = f"Selected candidate {chosen_id} with skill match score {best_score}."

        trace = DecisionTrace(
            stages_evaluated=stages,
            candidates_selected=trace_selected,
            candidates_scored=trace_scored,
            constraints_checked=trace_checked,
            rejection_reasons=trace_rejections,
            execution_time_ms=elapsed,
            policy_evaluations=policy_evaluations,
        )

        return DecisionResult(
            decision_id=uuid4(),
            approved=True,
            chosen_candidate_id=chosen_id,
            decision_code=decision_code,
            trace=trace,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_id(self, candidate: Any) -> UUID | None:
        """Safely extract the UUID identifier from a candidate snapshot."""
        if hasattr(candidate, "employee_id"):
            val = getattr(candidate, "employee_id")
            if isinstance(val, UUID):
                return val
        if hasattr(candidate, "id"):
            val = getattr(candidate, "id")
            if isinstance(val, UUID):
                return val
        return None
