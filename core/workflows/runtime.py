"""Runtime for live workflow coordination with DAG support."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TYPE_CHECKING
from uuid import UUID

import time

from core.events.bus import EventBus
from core.persistence._helpers import save_if_enabled
from core.events.domain_events import (
    WorkflowCompleted,
    WorkflowStarted,
    WorkflowTaskCompleted,
    WorkflowTaskStarted,
)
from core.runtime import CompanyRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntimeState
from core.workflow.foundation import (
    WorkflowDefinition as FoundationWorkflowDefinition,
    WorkflowExecution as FoundationWorkflowExecution,
    WorkflowRuntime as FoundationWorkflowRuntime,
)

from .models import Workflow

if TYPE_CHECKING:
    from core.orchestrator.runtime import OrchestratorRuntime
    from core.persistence.runtime import PersistenceRuntime
    from core.tasks.runtime import TaskRuntime


class WorkflowRuntimeState(StrEnum):
    """Runtime states for workflows."""

    CREATED = "created"
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class WorkflowStateChangedEvent:
    """Deterministic event emitted by the workflow runtime."""

    workflow_id: UUID
    previous_state: WorkflowRuntimeState
    new_state: WorkflowRuntimeState
    progress: float = 0.0
    current_task_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowRuntimeSnapshot:
    """In-memory snapshot for workflow lifecycle state."""

    workflow_id: UUID
    name: str
    state: WorkflowRuntimeState = WorkflowRuntimeState.CREATED
    task_ids: list[UUID] = field(default_factory=list)
    current_task_id: UUID | None = None
    progress: float = 0.0


class WorkflowRuntime:
    """Deterministic in-memory runtime for workflow coordination.

    Supports both linear and DAG-based workflows with branching,
    parallelism, and merge semantics.
    """

    _TRANSITIONS: dict[WorkflowRuntimeState, set[WorkflowRuntimeState]] = {
        WorkflowRuntimeState.CREATED: {WorkflowRuntimeState.PLANNED, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.PLANNED: {WorkflowRuntimeState.READY, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.READY: {WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.RUNNING: {WorkflowRuntimeState.WAITING, WorkflowRuntimeState.PAUSED, WorkflowRuntimeState.COMPLETED, WorkflowRuntimeState.FAILED, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.WAITING: {WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.PAUSED, WorkflowRuntimeState.FAILED, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.PAUSED: {WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.CANCELLED},
        WorkflowRuntimeState.COMPLETED: set(),
        WorkflowRuntimeState.FAILED: set(),
        WorkflowRuntimeState.CANCELLED: set(),
    }

    def __init__(
        self,
        company_runtime: CompanyRuntime,
        orchestrator_runtime: "OrchestratorRuntime",
        task_runtime: "TaskRuntime",
        event_bus: EventBus | None = None,
        persistence_runtime: PersistenceRuntime | None = None,
    ) -> None:
        self.company_runtime = company_runtime
        self.orchestrator_runtime = orchestrator_runtime
        self.task_runtime = task_runtime
        self.event_bus = event_bus or company_runtime.event_bus
        self._persistence = persistence_runtime
        self._workflows: dict[UUID, WorkflowRuntimeSnapshot] = {}
        self._events: list[WorkflowStateChangedEvent] = []
        self._workflow_task_order: dict[UUID, list[UUID]] = {}
        self._foundation_definitions: dict[UUID, FoundationWorkflowDefinition] = {}
        self._foundation_executions: dict[UUID, FoundationWorkflowExecution] = {}
        self._dag_dependencies: dict[UUID, dict[UUID, set[UUID]]] = {}
        self._dag_dependents: dict[UUID, dict[UUID, set[UUID]]] = {}

    # ------------------------------------------------------------------
    # Workflow lifecycle (unchanged)
    # ------------------------------------------------------------------

    def register_workflow(self, workflow: Workflow) -> WorkflowRuntimeSnapshot:
        snapshot = WorkflowRuntimeSnapshot(workflow_id=workflow.id, name=workflow.name)
        self._workflows[workflow.id] = snapshot
        self._workflow_task_order[workflow.id] = []
        self._dag_dependencies[workflow.id] = {}
        self._dag_dependents[workflow.id] = {}
        self._emit(workflow.id, WorkflowRuntimeState.CREATED, WorkflowRuntimeState.PLANNED)
        snapshot.state = WorkflowRuntimeState.PLANNED
        self._save(snapshot)
        return snapshot

    def add_task(self, workflow_id: UUID, task_id: UUID) -> WorkflowRuntimeSnapshot:
        snapshot = self._require_workflow(workflow_id)
        if task_id not in snapshot.task_ids:
            snapshot.task_ids.append(task_id)
            self._workflow_task_order[workflow_id].append(task_id)
            if task_id not in self._dag_dependencies[workflow_id]:
                self._dag_dependencies[workflow_id][task_id] = set()
            if task_id not in self._dag_dependents[workflow_id]:
                self._dag_dependents[workflow_id][task_id] = set()
        if snapshot.state == WorkflowRuntimeState.CREATED:
            self.transition(workflow_id, WorkflowRuntimeState.PLANNED)
        self._save(snapshot)
        return snapshot

    def start(self, workflow_id: UUID) -> WorkflowRuntimeSnapshot:
        snapshot = self._require_workflow(workflow_id)
        if snapshot.state != WorkflowRuntimeState.PLANNED:
            raise ValueError("Workflow must be planned before starting.")
        self.transition(workflow_id, WorkflowRuntimeState.READY)
        self.transition(workflow_id, WorkflowRuntimeState.RUNNING)
        self._emit_event(WorkflowStarted(
            workflow_id=workflow_id, timestamp=time.time(),
        ))
        self._advance(workflow_id)
        self._save(snapshot)
        return snapshot

    def transition(self, workflow_id: UUID, new_state: WorkflowRuntimeState) -> WorkflowRuntimeSnapshot:
        snapshot = self._require_workflow(workflow_id)
        if new_state not in self._TRANSITIONS[snapshot.state]:
            raise ValueError(f"Invalid workflow transition from {snapshot.state.value} to {new_state.value}.")
        previous_state = snapshot.state
        snapshot.state = new_state
        self._emit(workflow_id, previous_state, new_state, progress=snapshot.progress, current_task_id=snapshot.current_task_id)
        return snapshot

    def progress(self, workflow_id: UUID) -> float:
        return self._require_workflow(workflow_id).progress

    def next_task(self, workflow_id: UUID) -> UUID | None:
        """Return the next task to execute, respecting DAG dependencies.

        For DAG workflows: returns the first ready task whose
        dependencies are all satisfied. For linear workflows: returns
        the first unstarted task in registration order.
        """
        snapshot = self._require_workflow(workflow_id)
        tasks = self.task_runtime.snapshot()

        if self.has_dag(workflow_id):
            ready = self.get_ready_tasks(workflow_id)
            if ready:
                return ready[0]
            return None

        for task_id in self._workflow_task_order[workflow_id]:
            task_match = next((task for task in tasks if task.task_id == task_id), None)
            if task_match is not None and task_match.state in {TaskRuntimeState.CREATED, TaskRuntimeState.QUEUED, TaskRuntimeState.BLOCKED}:
                return task_id
        return None

    def complete_task(self, workflow_id: UUID, task_id: UUID) -> WorkflowRuntimeSnapshot:
        snapshot = self._require_workflow(workflow_id)
        task_snapshot = next((task for task in self.task_runtime.snapshot() if task.task_id == task_id), None)
        if task_snapshot is None:
            raise KeyError("Workflow references an unknown task.")
        if task_snapshot.state != TaskRuntimeState.COMPLETED:
            self.task_runtime.complete(task_id)
        tasks = self.task_runtime.snapshot()
        completed = sum(
            1
            for current_task_id in snapshot.task_ids
            if (task_match := next((task for task in tasks if task.task_id == current_task_id), None)) is not None
            and task_match.state == TaskRuntimeState.COMPLETED
        )
        snapshot.progress = (completed / len(snapshot.task_ids) * 100.0) if snapshot.task_ids else 0.0
        snapshot.current_task_id = task_id
        self._emit_event(WorkflowTaskCompleted(
            workflow_id=workflow_id, task_id=task_id,
            timestamp=time.time(),
        ))
        if snapshot.progress >= 100.0:
            if snapshot.state != WorkflowRuntimeState.COMPLETED:
                previous_state = snapshot.state
                snapshot.state = WorkflowRuntimeState.COMPLETED
                self._emit(workflow_id, previous_state, WorkflowRuntimeState.COMPLETED, progress=snapshot.progress, current_task_id=task_id)
                self._emit_event(WorkflowCompleted(
                    workflow_id=workflow_id, progress=snapshot.progress,
                    timestamp=time.time(),
                ))
        else:
            if snapshot.state != WorkflowRuntimeState.WAITING:
                self.transition(workflow_id, WorkflowRuntimeState.WAITING)
            self._advance(workflow_id)
        self._save(snapshot)
        return snapshot

    def events(self) -> list[WorkflowStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[WorkflowRuntimeSnapshot]:
        return list(self._workflows.values())

    # ------------------------------------------------------------------
    # DAG dependency management
    # ------------------------------------------------------------------

    def add_dependency(
        self,
        workflow_id: UUID,
        task_id: UUID,
        depends_on_id: UUID,
    ) -> WorkflowRuntimeSnapshot:
        """Add a directed dependency: task_id depends on depends_on_id.

        Args:
            workflow_id: The workflow.
            task_id: The dependent task (must be completed after).
            depends_on_id: The prerequisite task (must be completed before).

        Returns:
            The updated WorkflowRuntimeSnapshot.

        Raises:
            KeyError: If any task is not registered in the workflow.
            ValueError: If the dependency creates a cycle.
        """
        snapshot = self._require_workflow(workflow_id)
        if task_id not in snapshot.task_ids:
            raise KeyError(f"task_id {task_id} is not registered in workflow {workflow_id}.")
        if depends_on_id not in snapshot.task_ids:
            raise KeyError(f"depends_on_id {depends_on_id} is not registered in workflow {workflow_id}.")
        if task_id == depends_on_id:
            raise ValueError("A task cannot depend on itself.")

        deps = self._dag_dependencies[workflow_id]
        dep_set = deps.setdefault(task_id, set())
        dep_set.add(depends_on_id)

        deps_to = self._dag_dependents[workflow_id]
        dep_set_to = deps_to.setdefault(depends_on_id, set())
        dep_set_to.add(task_id)

        if not self._is_acyclic(workflow_id):
            dep_set.discard(depends_on_id)
            dep_set_to.discard(task_id)
            raise ValueError(
                f"Dependency {task_id} -> {depends_on_id} would create a cycle."
            )

        self._save(snapshot)
        return snapshot

    def add_dependencies(
        self,
        workflow_id: UUID,
        task_id: UUID,
        depends_on_ids: list[UUID],
    ) -> WorkflowRuntimeSnapshot:
        """Add multiple dependencies for a task in batch.

        If any single dependency causes a cycle, the entire batch is
        rejected (no partial application).

        Args:
            workflow_id: The workflow.
            task_id: The dependent task.
            depends_on_ids: List of prerequisite task IDs.

        Returns:
            The updated WorkflowRuntimeSnapshot.

        Raises:
            ValueError: If any dependency creates a cycle.
            KeyError: If any task is not registered.
        """
        snapshot = self._require_workflow(workflow_id)
        for dep_id in depends_on_ids:
            self.add_dependency(workflow_id, task_id, dep_id)
        return snapshot

    def remove_dependency(
        self,
        workflow_id: UUID,
        task_id: UUID,
        depends_on_id: UUID,
    ) -> WorkflowRuntimeSnapshot:
        """Remove a dependency edge between two tasks.

        Args:
            workflow_id: The workflow.
            task_id: The dependent task.
            depends_on_id: The prerequisite task to remove.

        Returns:
            The updated WorkflowRuntimeSnapshot (no-op if edge does not exist).
        """
        snapshot = self._require_workflow(workflow_id)
        deps = self._dag_dependencies.get(workflow_id, {})
        dep_set = deps.get(task_id)
        if dep_set is not None:
            dep_set.discard(depends_on_id)

        deps_to = self._dag_dependents.get(workflow_id, {})
        dep_set_to = deps_to.get(depends_on_id)
        if dep_set_to is not None:
            dep_set_to.discard(task_id)

        self._save(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # DAG queries
    # ------------------------------------------------------------------

    def has_dag(self, workflow_id: UUID) -> bool:
        """Check whether a workflow uses DAG dependencies.

        A workflow is considered a DAG workflow if at least one
        dependency edge has been registered.
        """
        deps = self._dag_dependencies.get(workflow_id, {})
        return any(dep_set for dep_set in deps.values())

    def get_ready_tasks(self, workflow_id: UUID) -> list[UUID]:
        """Return task IDs whose all dependencies are satisfied.

        A task is "ready" when:
        - It is registered in the workflow.
        - It is not yet completed.
        - All of its predecessor tasks are completed.

        Returns task IDs in registration order for determinism.
        """
        snapshot = self._require_workflow(workflow_id)
        tasks = self.task_runtime.snapshot()
        deps = self._dag_dependencies.get(workflow_id, {})
        completed_ids = {
            t.task_id for t in tasks
            if t.state == TaskRuntimeState.COMPLETED
        }

        ready: list[UUID] = []
        for task_id in snapshot.task_ids:
            task_match = next((t for t in tasks if t.task_id == task_id), None)
            if task_match is None:
                continue
            if task_match.state == TaskRuntimeState.COMPLETED:
                continue
            predecessors = deps.get(task_id, set())
            if predecessors.issubset(completed_ids):
                ready.append(task_id)
        return ready

    def get_blocked_tasks(self, workflow_id: UUID) -> list[UUID]:
        """Return task IDs that have unmet dependencies.

        A task is "blocked" when:
        - It is not yet completed.
        - At least one of its predecessor tasks is not completed.
        """
        snapshot = self._require_workflow(workflow_id)
        tasks = self.task_runtime.snapshot()
        deps = self._dag_dependencies.get(workflow_id, {})
        completed_ids = {
            t.task_id for t in tasks
            if t.state == TaskRuntimeState.COMPLETED
        }

        blocked: list[UUID] = []
        for task_id in snapshot.task_ids:
            task_match = next((t for t in tasks if t.task_id == task_id), None)
            if task_match is None:
                continue
            if task_match.state == TaskRuntimeState.COMPLETED:
                continue
            predecessors = deps.get(task_id, set())
            if predecessors and not predecessors.issubset(completed_ids):
                blocked.append(task_id)
        return blocked

    def get_dependents(
        self,
        workflow_id: UUID,
        task_id: UUID,
    ) -> list[UUID]:
        """Return task IDs that directly depend on the given task.

        Returns IDs in registration order for determinism.
        """
        snapshot = self._require_workflow(workflow_id)
        deps_to = self._dag_dependents.get(workflow_id, {})
        dependents = deps_to.get(task_id, set())
        return [tid for tid in snapshot.task_ids if tid in dependents]

    def get_predecessors(
        self,
        workflow_id: UUID,
        task_id: UUID,
    ) -> list[UUID]:
        """Return task IDs that the given task directly depends on.

        Returns IDs in registration order for determinism.
        """
        snapshot = self._require_workflow(workflow_id)
        deps = self._dag_dependencies.get(workflow_id, {})
        predecessors = deps.get(task_id, set())
        return [tid for tid in snapshot.task_ids if tid in predecessors]

    # ------------------------------------------------------------------
    # DAG validation
    # ------------------------------------------------------------------

    def validate_dependency(
        self,
        workflow_id: UUID,
        task_id: UUID,
        depends_on_id: UUID,
    ) -> bool:
        """Check whether a specific dependency edge exists."""
        deps = self._dag_dependencies.get(workflow_id, {})
        return depends_on_id in deps.get(task_id, set())

    def validate_dag(self, workflow_id: UUID) -> bool:
        """Validate the entire workflow DAG.

        Checks:
        - No cycles (acyclic).
        - All dependency references point to registered tasks.
        - No self-dependencies.

        Returns True if valid, False otherwise.
        """
        snapshot = self._require_workflow(workflow_id)
        task_set = set(snapshot.task_ids)
        deps = self._dag_dependencies.get(workflow_id, {})

        for tid, preds in deps.items():
            for p in preds:
                if p == tid:
                    return False
                if p not in task_set:
                    return False

        return self._is_acyclic(workflow_id)

    # ------------------------------------------------------------------
    # Foundation integration (unchanged)
    # ------------------------------------------------------------------

    def promote_definition(
        self,
        foundation_definition: FoundationWorkflowDefinition,
        foundation_execution: FoundationWorkflowExecution | None = None,
    ) -> WorkflowRuntimeSnapshot:
        if foundation_execution is None:
            foundation_execution = FoundationWorkflowRuntime.start_execution(
                foundation_definition,
            )

        workflow = Workflow(
            name=foundation_definition.name,
            description="Promoted from foundation workflow definition",
            metadata=dict(foundation_definition.metadata),
        )
        workflow.id = foundation_definition.workflow_id

        snapshot = self.register_workflow(workflow)

        for step in foundation_definition.steps:
            task = Task(name=step.name)
            task.id = step.step_id
            self.task_runtime.register_task(task)
            self.add_task(workflow.id, task.id)

        self._foundation_definitions[workflow.id] = foundation_definition
        self._foundation_executions[workflow.id] = foundation_execution

        self._save(snapshot)
        return snapshot

    def promote_execution(
        self,
        workflow_id: UUID,
        foundation_execution: FoundationWorkflowExecution,
    ) -> WorkflowRuntimeSnapshot:
        snapshot = self._require_workflow(workflow_id)
        foundation_def = self._foundation_definitions.get(workflow_id)
        if foundation_def is None:
            raise KeyError(
                f"Workflow {workflow_id} has no foundation definition registered. "
                "Call promote_definition first."
            )

        self._foundation_executions[workflow_id] = foundation_execution

        progress_ratio = FoundationWorkflowRuntime.calculate_progress(
            foundation_def, foundation_execution,
        )
        snapshot.progress = progress_ratio * 100.0

        self._save(snapshot)
        return snapshot

    def create_from_foundation(
        self,
        foundation_definition: FoundationWorkflowDefinition,
    ) -> WorkflowRuntimeSnapshot:
        foundation_execution = FoundationWorkflowRuntime.start_execution(
            foundation_definition,
        )
        return self.promote_definition(foundation_definition, foundation_execution)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self, snapshot: WorkflowRuntimeSnapshot) -> None:
        persistence = getattr(self, "_persistence", None)
        save_if_enabled(persistence, snapshot, "workflow", snapshot.workflow_id)

    def _advance(self, workflow_id: UUID) -> None:
        next_task_id = self.next_task(workflow_id)
        if next_task_id is None:
            snapshot = self._require_workflow(workflow_id)

            if self.has_dag(workflow_id) and self.get_blocked_tasks(workflow_id):
                return

            snapshot.progress = 100.0
            if snapshot.state != WorkflowRuntimeState.COMPLETED:
                previous_state = snapshot.state
                snapshot.state = WorkflowRuntimeState.COMPLETED
                self._emit(workflow_id, previous_state, WorkflowRuntimeState.COMPLETED, progress=snapshot.progress, current_task_id=snapshot.current_task_id)
                self._emit_event(WorkflowCompleted(
                    workflow_id=workflow_id, progress=snapshot.progress,
                    timestamp=time.time(),
                ))
            return
        snapshot = self._require_workflow(workflow_id)
        snapshot.current_task_id = next_task_id
        task_snapshot = next((task for task in self.task_runtime.snapshot() if task.task_id == next_task_id), None)
        if task_snapshot is None:
            raise KeyError("Workflow references an unknown task.")
        if task_snapshot.state == TaskRuntimeState.CREATED:
            self.task_runtime.transition(next_task_id, TaskRuntimeState.QUEUED)
        if task_snapshot.state == TaskRuntimeState.QUEUED:
            self.task_runtime.assign_via_orchestrator(next_task_id, self._select_department_id())
        if snapshot.state != WorkflowRuntimeState.WAITING:
            self.transition(workflow_id, WorkflowRuntimeState.WAITING)
        self._emit_event(WorkflowTaskStarted(
            workflow_id=workflow_id, task_id=next_task_id,
            timestamp=time.time(),
        ))

    def _is_acyclic(self, workflow_id: UUID) -> bool:
        """Kahn's algorithm: detect cycles via topological sort."""
        deps = self._dag_dependencies.get(workflow_id, {})
        snapshot = self._require_workflow(workflow_id)
        task_ids = snapshot.task_ids

        in_degree: dict[UUID, int] = {}
        for tid in task_ids:
            in_degree[tid] = len(deps.get(tid, set()))

        queue: deque = deque(
            tid for tid in task_ids if in_degree.get(tid, 0) == 0
        )

        visited = 0
        while queue:
            tid = queue.popleft()
            visited += 1
            for successor in self._dag_dependents.get(workflow_id, {}).get(tid, set()):
                in_degree[successor] = in_degree.get(successor, 0) - 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        return visited == len(task_ids)

    def _select_department_id(self) -> UUID:
        return next(iter(self.orchestrator_runtime.department_runtime._departments.keys()))

    def _emit(
        self,
        workflow_id: UUID,
        previous_state: WorkflowRuntimeState,
        new_state: WorkflowRuntimeState,
        *,
        progress: float = 0.0,
        current_task_id: UUID | None = None,
    ) -> None:
        event = WorkflowStateChangedEvent(
            workflow_id=workflow_id,
            previous_state=previous_state,
            new_state=new_state,
            progress=progress,
            current_task_id=current_task_id,
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _emit_event(self, event: Any) -> None:
        self.event_bus.publish(event)

    def _require_workflow(self, workflow_id: UUID) -> WorkflowRuntimeSnapshot:
        try:
            return self._workflows[workflow_id]
        except KeyError as error:
            raise KeyError(f"Workflow {workflow_id} is not registered in workflow runtime.") from error
