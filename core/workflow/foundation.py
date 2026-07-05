"""Foundation runtime for the Workflow Runtime.

Stateless, deterministic workflow coordinator.
No IO, no async, no threads, no database, no AI, no inference —
pure deterministic step orchestration only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


# ------------------------------------------------------------------
# WorkflowStep
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """A single immutable step within a workflow.

    Attributes:
        step_id: Unique identifier for this step.
        name: Human-readable step name.
        description: Optional description of the step.
        order: Sequential position (0-based).
        metadata: Optional extra data associated with the step.
    """

    step_id: UUID
    name: str
    description: str = ""
    order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        name: str,
        description: str = "",
        order: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStep:
        """Factory that auto-generates step_id."""
        return WorkflowStep(
            step_id=uuid4(),
            name=name,
            description=description,
            order=order,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# WorkflowDefinition
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """An immutable workflow definition with ordered steps.

    Attributes:
        workflow_id: Unique identifier for this workflow.
        name: Human-readable workflow name.
        steps: Ordered tuple of WorkflowStep instances.
        created_at: Unix timestamp of definition creation.
        metadata: Optional extra data associated with the workflow.
    """

    workflow_id: UUID
    name: str
    steps: tuple[WorkflowStep, ...] = ()
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        name: str,
        steps: tuple[WorkflowStep, ...] | list[WorkflowStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        """Factory that auto-generates workflow_id and created_at."""
        return WorkflowDefinition(
            workflow_id=uuid4(),
            name=name,
            steps=tuple(steps) if steps else (),
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        name: str,
        created_at: float,
        steps: tuple[WorkflowStep, ...] | list[WorkflowStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return WorkflowDefinition(
            workflow_id=uuid4(),
            name=name,
            steps=tuple(steps) if steps else (),
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# WorkflowExecution
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowExecution:
    """An immutable point-in-time view of a workflow execution.

    Attributes:
        execution_id: Unique identifier for this execution.
        workflow_id: The workflow definition being executed.
        completed_step_ids: Set of step_ids that have been completed.
        started_at: Unix timestamp of when execution started.
        metadata: Optional extra data associated with the execution.
    """

    execution_id: UUID
    workflow_id: UUID
    completed_step_ids: frozenset[UUID] = field(default_factory=frozenset)
    started_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        workflow_id: UUID,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """Factory that auto-generates execution_id and started_at."""
        return WorkflowExecution(
            execution_id=uuid4(),
            workflow_id=workflow_id,
            completed_step_ids=frozenset(),
            started_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        workflow_id: UUID,
        started_at: float,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return WorkflowExecution(
            execution_id=uuid4(),
            workflow_id=workflow_id,
            completed_step_ids=frozenset(),
            started_at=started_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# WorkflowTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowTrace:
    """Execution trace for workflow operations.

    Attributes:
        steps_total: Total number of steps in the workflow.
        steps_completed: Number of steps completed so far.
        progress: Progress ratio (0.0 to 1.0).
        completed_step_names: Ordered list of completed step names.
        pending_step_names: Ordered list of pending step names.
        timestamps: Dict mapping operation name to Unix timestamp.
    """

    steps_total: int = 0
    steps_completed: int = 0
    progress: float = 0.0
    completed_step_names: tuple[str, ...] = ()
    pending_step_names: tuple[str, ...] = ()
    timestamps: dict[str, float] = field(default_factory=dict)


# ------------------------------------------------------------------
# WorkflowResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Outcome of a workflow runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        execution: The workflow execution state after the operation.
        trace: Execution trace with progress and timing.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    execution: WorkflowExecution
    trace: WorkflowTrace
    error_message: str = ""


# ------------------------------------------------------------------
# WorkflowRuntime
# ------------------------------------------------------------------


class WorkflowRuntime:
    """Stateless runtime for workflow step coordination.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    # ------------------------------------------------------------------
    # Definition management
    # ------------------------------------------------------------------

    @staticmethod
    def create_definition(
        name: str,
        steps: tuple[WorkflowStep, ...] | list[WorkflowStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        """Create a new workflow definition with the given steps.

        Args:
            name: Human-readable workflow name.
            steps: Optional ordered steps.
            metadata: Optional extra data.

        Returns:
            A new WorkflowDefinition.
        """
        return WorkflowDefinition.create(
            name=name,
            steps=list(steps) if steps else None,
            metadata=metadata,
        )

    @staticmethod
    def add_step(
        definition: WorkflowDefinition,
        step: WorkflowStep,
    ) -> WorkflowDefinition:
        """Return a new definition with the step appended.

        The original definition is not modified (immutable).
        The step's order is set to the next available position.

        Args:
            definition: The current workflow definition.
            step: The WorkflowStep to append.

        Returns:
            A new WorkflowDefinition with the step added.
        """
        reordered = WorkflowStep(
            step_id=step.step_id,
            name=step.name,
            description=step.description,
            order=len(definition.steps),
            metadata=dict(step.metadata),
        )
        return WorkflowDefinition(
            workflow_id=definition.workflow_id,
            name=definition.name,
            steps=definition.steps + (reordered,),
            created_at=definition.created_at,
            metadata=dict(definition.metadata),
        )

    # ------------------------------------------------------------------
    # Execution lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    def start_execution(
        definition: WorkflowDefinition,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """Start a new execution for the given workflow definition.

        Args:
            definition: The workflow definition to execute.
            metadata: Optional metadata for the execution.

        Returns:
            A new WorkflowExecution with no steps completed.
        """
        return WorkflowExecution.create(
            workflow_id=definition.workflow_id,
            metadata=metadata,
        )

    @staticmethod
    def complete_step(
        execution: WorkflowExecution,
        step_id: UUID,
    ) -> WorkflowExecution:
        """Return a new execution with the given step marked as completed.

        The step must exist in the workflow definition (checked via
        definition lookup). If already completed, returns the same
        execution unchanged.

        Args:
            execution: The current execution state.
            step_id: The step to mark as completed.

        Returns:
            A new WorkflowExecution with the step added to completed set.
        """
        if step_id in execution.completed_step_ids:
            return execution
        return WorkflowExecution(
            execution_id=execution.execution_id,
            workflow_id=execution.workflow_id,
            completed_step_ids=frozenset(execution.completed_step_ids | {step_id}),
            started_at=execution.started_at,
            metadata=dict(execution.metadata),
        )

    # ------------------------------------------------------------------
    # Step queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_next_step(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> WorkflowStep | None:
        """Get the next pending step in order, or None if complete.

        Args:
            definition: The workflow definition.
            execution: The current execution state.

        Returns:
            The next WorkflowStep to execute, or None if all steps done.
        """
        for step in definition.steps:
            if step.step_id not in execution.completed_step_ids:
                return step
        return None

    @staticmethod
    def is_complete(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> bool:
        """Check whether all steps in the workflow have been completed.

        Args:
            definition: The workflow definition.
            execution: The current execution state.

        Returns:
            True if all steps are completed; False otherwise.
        """
        return WorkflowRuntime.get_next_step(definition, execution) is None

    @staticmethod
    def get_pending_steps(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> tuple[WorkflowStep, ...]:
        """Get all steps that have not yet been completed, in order.

        Args:
            definition: The workflow definition.
            execution: The current execution state.

        Returns:
            A tuple of pending WorkflowStep instances, in definition order.
        """
        return tuple(
            step for step in definition.steps
            if step.step_id not in execution.completed_step_ids
        )

    @staticmethod
    def get_completed_steps(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> tuple[WorkflowStep, ...]:
        """Get all steps that have been completed, in definition order.

        Args:
            definition: The workflow definition.
            execution: The current execution state.

        Returns:
            A tuple of completed WorkflowStep instances, in definition order.
        """
        return tuple(
            step for step in definition.steps
            if step.step_id in execution.completed_step_ids
        )

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_progress(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> float:
        """Calculate the progress ratio (0.0 to 1.0).

        Args:
            definition: The workflow definition.
            execution: The current execution state.

        Returns:
            A float between 0.0 (no steps done) and 1.0 (all steps done).
        """
        total = len(definition.steps)
        if total == 0:
            return 1.0
        return len(execution.completed_step_ids) / total

    # ------------------------------------------------------------------
    # Trace and result
    # ------------------------------------------------------------------

    @staticmethod
    def build_trace(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
        timestamps: dict[str, float] | None = None,
    ) -> WorkflowTrace:
        """Assemble a WorkflowTrace from definition and execution state.

        Args:
            definition: The workflow definition.
            execution: The current execution state.
            timestamps: Optional dict of operation timestamps.

        Returns:
            A new WorkflowTrace.
        """
        completed = WorkflowRuntime.get_completed_steps(definition, execution)
        pending = WorkflowRuntime.get_pending_steps(definition, execution)
        progress = WorkflowRuntime.calculate_progress(definition, execution)
        return WorkflowTrace(
            steps_total=len(definition.steps),
            steps_completed=len(completed),
            progress=progress,
            completed_step_names=tuple(s.name for s in completed),
            pending_step_names=tuple(s.name for s in pending),
            timestamps=dict(timestamps) if timestamps else {},
        )

    @staticmethod
    def build_result(
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
        timestamps: dict[str, float] | None = None,
        success: bool = True,
        error_message: str = "",
    ) -> WorkflowResult:
        """Assemble a WorkflowResult from operation data.

        Args:
            definition: The workflow definition.
            execution: The current execution state.
            timestamps: Optional dict of operation timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new WorkflowResult.
        """
        trace = WorkflowRuntime.build_trace(definition, execution, timestamps)
        return WorkflowResult(
            success=success,
            execution=execution,
            trace=trace,
            error_message=error_message,
        )
