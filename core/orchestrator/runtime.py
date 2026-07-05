"""Orchestrator runtime for AI Content Factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4

import time

from core.events.bus import EventBus
from core.events.domain_events import (
    DecisionApproved,
    DecisionRejected,
    ExecutionCompleted,
    ExecutionFailed,
    ExecutionStarted,
    OrchestratorExecutionCompleted,
    OrchestratorExecutionStarted,
)
from core.results.models import Result, ResultOutcome, ResultStatus, ResultSummary, ResultType
from core.runtime import CompanyRuntime, TaskRecord

from core.conversation import ConversationRuntime, ConversationSession
from core.decision.runtime import DecisionContextBuilder, DecisionEngine, DecisionResult
from core.execution.runtime import ExecutionResult, ExecutionRuntime
from core.learning.pipeline import LearningPipeline
from core.llm.models import LLMRequest

if TYPE_CHECKING:
    from core.departments.runtime import DepartmentRuntime
    from core.employees import EmployeeRuntimeSnapshot
    from core.employees import EmployeeRuntimeState
else:
    from core.employees import EmployeeRuntimeState


@dataclass(frozen=True, slots=True)
class OrchestratorTaskEvent:
    """Deterministic orchestrator event."""

    task_id: UUID
    stage: str
    department_id: UUID | None = None
    employee_id: UUID | None = None
    result_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrchestratorTaskSnapshot:
    """In-memory snapshot for orchestrated tasks."""

    task: TaskRecord
    department_id: UUID | None = None
    employee_id: UUID | None = None
    result: Result | None = None
    stage: str = "received"


@dataclass(frozen=True, slots=True)
class OrchestratorExecutionResult:
    """Outcome of an orchestrated task execution cycle.

    Contains the decision result, execution result, and automatic
    learning pipeline results from the Conversation → Skills flow.
    """

    orchestrator_id: UUID
    decision_result: DecisionResult
    execution_result: ExecutionResult | None = None
    success: bool = False
    error_message: str = ""
    updated_conversation: ConversationSession | None = None
    learning_pipeline_result: Any = None
    knowledge_snapshot: Any = None
    learning_snapshot: Any = None
    skill_snapshot: Any = None
    runtime_skill_snapshots: list[Any] | None = None


class OrchestratorRuntime:
    """Minimal in-memory orchestrator."""

    def __init__(
        self,
        company_runtime: CompanyRuntime,
        department_runtime: "DepartmentRuntime",
        event_bus: EventBus | None = None,
    ) -> None:
        self.company_runtime = company_runtime
        self.department_runtime = department_runtime
        self.event_bus = event_bus or company_runtime.event_bus
        self._tasks: dict[UUID, OrchestratorTaskSnapshot] = {}
        self._events: list[OrchestratorTaskEvent] = []

    def receive_task(self, title: str) -> OrchestratorTaskSnapshot:
        task = self.company_runtime.register_task(title)
        snapshot = OrchestratorTaskSnapshot(task=task)
        self._tasks[task.task_id] = snapshot
        self._emit(task.task_id, "received")
        return snapshot

    def route_task(self, task_id: UUID, department_id: UUID, employee_id: UUID) -> OrchestratorTaskSnapshot:
        snapshot = self._require_task(task_id)
        snapshot.department_id = department_id
        snapshot.employee_id = employee_id
        snapshot.stage = "routed"
        self._emit(task_id, "routed", department_id=department_id, employee_id=employee_id)
        self.company_runtime.assign_task(employee_id, task_id)
        self.department_runtime.sync_employee_state(department_id, self.company_runtime.employee_runtime.events()[-1])
        return snapshot

    def complete_task(self, task_id: UUID) -> OrchestratorTaskSnapshot:
        snapshot = self._require_task(task_id)
        if snapshot.employee_id is None:
            raise KeyError("Task is not assigned to an employee.")
        self.company_runtime.complete_task(snapshot.employee_id, task_id)
        if snapshot.department_id is not None:
            self.department_runtime.sync_employee_state(
                snapshot.department_id,
                self.company_runtime.employee_runtime.events()[-1],
            )
        result = Result(
            name=f"Result for {snapshot.task.title}",
            type=ResultType.ORGANIZATIONAL,
            status=ResultStatus.GENERATED,
            outcome=ResultOutcome.SUCCESS,
            summary=ResultSummary(title=snapshot.task.title, description="Completed task cycle"),
        )
        snapshot.result = result
        snapshot.stage = "completed"
        self._emit(task_id, "completed", department_id=snapshot.department_id, employee_id=snapshot.employee_id, result_id=result.id)
        self.event_bus.publish(result)
        return snapshot

    @staticmethod
    def _session_metadata(task_snapshot: Any) -> dict[str, str]:
        """Extract minimal metadata from a task snapshot."""
        meta: dict[str, str] = {}
        tid = getattr(task_snapshot, "task_id", None)
        if tid is not None:
            meta["task_id"] = str(tid)
        tname = getattr(task_snapshot, "name", None)
        if tname is not None:
            meta["task_name"] = str(tname)
        return meta

    @staticmethod
    def execute_task(
        task_snapshot: Any,
        candidate_snapshots: list[Any],
        department_snapshot: Any = None,
        skill_snapshots: list[Any] | None = None,
        skill_runtime: Any | None = None,
        policy_constraints: list[Any] | None = None,
        policy_rules: list[Any] | None = None,
        llm_request: LLMRequest | None = None,
        gateway: Any = None,
        gateway_provider: str | None = None,
        metadata: dict[str, Any] | None = None,
        conversation_session: ConversationSession | None = None,
        event_bus: EventBus | None = None,
    ) -> OrchestratorExecutionResult:
        """Full orchestration cycle: decide -> execute -> learn.

        Delegates candidate selection to DecisionEngine and, if approved,
        delegates AI execution to ExecutionRuntime.

        After successful execution, automatically runs the LearningPipeline
        on the updated conversation to produce knowledge, learning
        recommendations, and skills — without any manual caller intervention.

        Automatically manages a ConversationSession:
        - Creates one if none is provided.
        - Propagates it to ExecutionRuntime for auto-logging.
        - Feeds the updated session into LearningPipeline.
        - Returns the updated session so the caller can continue it.

        Args:
            task_snapshot: Snapshot of the task to execute.
            candidate_snapshots: Candidates eligible for the task.
            department_snapshot: Department context for candidate filtering.
            skill_snapshots: Legacy skills available for matching.
            skill_runtime: Optional SkillRuntime for real skill snapshots
                           and automatic pipeline promotion.
            policy_constraints: Hard constraints for the Policy Engine.
            policy_rules: Declarative rules for the Policy Engine.
            llm_request: Pre-built LLMRequest (required if gateway is provided).
            gateway: Object compatible with ExecutionRuntime.execute_with_gateway.
            gateway_provider: Optional provider name override.
            metadata: Optional metadata forwarded to decision and execution.
            conversation_session: Optional session to continue. Created
                automatically if not provided.

        Returns:
            An OrchestratorExecutionResult wrapping decision, execution,
            and learning outcomes, including all intermediate snapshots.
        """
        orchestrator_id = uuid4()
        merged_metadata = dict(metadata) if metadata else {}
        ts = time.time()
        task_id = getattr(task_snapshot, "task_id", None)

        def _pub(e: Any) -> None:
            if event_bus is not None:
                event_bus.publish(e)

        _pub(OrchestratorExecutionStarted(
            orchestrator_id=orchestrator_id, task_id=task_id, timestamp=ts,
        ))

        # --- Extract runtime skill snapshots if skill_runtime is provided ---
        skill_runtime_snapshots = skill_runtime.snapshot() if skill_runtime is not None else None

        # --- Auto-create conversation session if needed ---
        if conversation_session is None:
            conversation_session = ConversationRuntime.create_session(
                participant_id="orchestrator",
                metadata=OrchestratorRuntime._session_metadata(task_snapshot),
            )

        # --- Step 1: Build DecisionContext ---
        context = DecisionContextBuilder().build_assignment_context(
            task_snapshot=task_snapshot,
            candidate_snapshots=list(candidate_snapshots),
            department_snapshot=department_snapshot,
            skill_snapshots=list(skill_snapshots) if skill_snapshots else None,
            skill_runtime_snapshots=skill_runtime_snapshots,
            policy_constraints=list(policy_constraints) if policy_constraints else None,
            policy_rules=list(policy_rules) if policy_rules else None,
            metadata=merged_metadata,
        )

        # --- Step 2: Decide ---
        decision = DecisionEngine().choose_best_candidate(context)

        if decision.approved:
            _pub(DecisionApproved(
                decision_id=decision.decision_id, task_id=task_id,
                chosen_candidate_id=decision.chosen_candidate_id,
                decision_code=decision.decision_code, timestamp=time.time(),
            ))
        else:
            _pub(DecisionRejected(
                decision_id=decision.decision_id, task_id=task_id,
                decision_code=decision.decision_code,
                explanation=decision.explanation, timestamp=time.time(),
            ))

        if not decision.approved:
            _pub(OrchestratorExecutionCompleted(
                orchestrator_id=orchestrator_id, task_id=task_id,
                success=False, timestamp=time.time(),
            ))
            return OrchestratorExecutionResult(
                orchestrator_id=orchestrator_id,
                decision_result=decision,
                success=False,
                error_message=decision.explanation,
                updated_conversation=conversation_session,
            )

        if llm_request is None or gateway is None:
            _pub(OrchestratorExecutionCompleted(
                orchestrator_id=orchestrator_id, task_id=task_id,
                success=False, timestamp=time.time(),
            ))
            return OrchestratorExecutionResult(
                orchestrator_id=orchestrator_id,
                decision_result=decision,
                success=False,
                error_message="LLM request or gateway not provided for execution.",
                updated_conversation=conversation_session,
            )

        # --- Step 3: Execute ---
        employee_snapshot = _find_candidate(candidate_snapshots, decision.chosen_candidate_id)
        if employee_snapshot is None:
            _pub(OrchestratorExecutionCompleted(
                orchestrator_id=orchestrator_id, task_id=task_id,
                success=False, timestamp=time.time(),
            ))
            return OrchestratorExecutionResult(
                orchestrator_id=orchestrator_id,
                decision_result=decision,
                success=False,
                error_message=f"Chosen candidate {decision.chosen_candidate_id} not found in snapshots.",
                updated_conversation=conversation_session,
            )

        exec_id = uuid4()
        _pub(ExecutionStarted(
            execution_id=exec_id, task_id=task_id, timestamp=time.time(),
        ))

        execution = ExecutionRuntime.execute_with_gateway(
            task_snapshot=task_snapshot,
            employee_snapshot=employee_snapshot,
            llm_request=llm_request,
            gateway=gateway,
            provider_name=gateway_provider,
            metadata=merged_metadata,
            conversation_session=conversation_session,
        )

        if execution.success:
            _pub(ExecutionCompleted(
                execution_id=exec_id, task_id=task_id,
                output=execution.output, timestamp=time.time(),
            ))
        else:
            _pub(ExecutionFailed(
                execution_id=exec_id, task_id=task_id,
                error_message=execution.error_message, timestamp=time.time(),
            ))

        # --- Step 4: Learn (automatic pipeline) ---
        pipeline_result = None
        if execution.success:
            updated_conv = execution.updated_conversation or conversation_session
            pipeline_result = LearningPipeline.run(
                updated_conv,
                skill_runtime=skill_runtime,
                event_bus=event_bus,
            )

        result = OrchestratorExecutionResult(
            orchestrator_id=orchestrator_id,
            decision_result=decision,
            execution_result=execution,
            success=execution.success,
            error_message=execution.error_message,
            updated_conversation=execution.updated_conversation or conversation_session,
            learning_pipeline_result=pipeline_result,
            knowledge_snapshot=pipeline_result.knowledge_snapshot if pipeline_result else None,
            learning_snapshot=pipeline_result.learning_snapshot if pipeline_result else None,
            skill_snapshot=pipeline_result.skill_snapshot if pipeline_result else None,
            runtime_skill_snapshots=pipeline_result.runtime_skill_snapshots if pipeline_result else None,
        )

        _pub(OrchestratorExecutionCompleted(
            orchestrator_id=orchestrator_id, task_id=task_id,
            success=result.success, timestamp=time.time(),
        ))

        return result

    def choose_employee(self, department_id: UUID) -> "EmployeeRuntimeSnapshot":
        department = self.department_runtime.department(department_id)
        candidates = [link for link in department.employees.values() if link.state == EmployeeRuntimeState.IDLE]
        if not candidates:
            raise KeyError("No available employee found.")
        chosen = sorted(candidates, key=lambda link: str(link.employee_id))[0]
        for snapshot in self.company_runtime.employee_runtime.snapshot():
            if snapshot.employee_id == chosen.employee_id:
                return snapshot
        raise KeyError(f"Employee {chosen.employee_id} is not registered in company runtime.")

    def events(self) -> list[OrchestratorTaskEvent]:
        return list(self._events)

    def _emit(
        self,
        task_id: UUID,
        stage: str,
        department_id: UUID | None = None,
        employee_id: UUID | None = None,
        result_id: UUID | None = None,
    ) -> None:
        event = OrchestratorTaskEvent(
            task_id=task_id,
            stage=stage,
            department_id=department_id,
            employee_id=employee_id,
            result_id=result_id,
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_task(self, task_id: UUID) -> OrchestratorTaskSnapshot:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise KeyError(f"Task {task_id} is not registered in orchestrator.") from error


def _find_candidate(candidates: list[Any], candidate_id: UUID | None) -> Any | None:
    """Locate a candidate snapshot by its UUID identifier."""
    if candidate_id is None:
        return None
    for cand in candidates:
        cand_uuid = getattr(cand, "employee_id", None) or getattr(cand, "id", None)
        if cand_uuid == candidate_id:
            return cand
    return None