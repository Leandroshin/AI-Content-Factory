"""Specialist Employee — first intelligent worker of AI Company.

Modelo oficial de funcionário especializado, baseado em Skills e
Capabilities. Todos os futuros funcionários (Editor, Pesquisador,
Redator, Revisor, Designer, etc.) devem seguir este comportamento.
Não criar subclasses por profissão.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from core.company.department_manager import DepartmentManager
from core.events.bus import EventBus
from core.runtime import CompanyRuntime
from core.tools import (
    Capability,
    CapabilityUnavailable as RegistryCapabilityUnavailable,
    ToolRegistry,
    ToolRuntime,
    ToolSelected,
    ToolUnavailable,
)


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class EmployeeStatus(StrEnum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    AWAITING_INFO = "awaiting_info"
    AWAITING_TOOL = "awaiting_tool"
    WORKING = "working"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class TaskDecision(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ------------------------------------------------------------------
# Events — published on shared EventBus
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TaskAccepted:
    employee_id: UUID
    task_id: UUID
    title: str
    difficulty: float
    estimated_time_minutes: int
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskRejected:
    employee_id: UUID
    task_id: UUID
    title: str
    reason: str
    missing_skills: tuple[str, ...] = field(default_factory=tuple)
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskStarted:
    employee_id: UUID
    task_id: UUID
    title: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskBlocked:
    employee_id: UUID
    task_id: UUID
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolRequested:
    employee_id: UUID
    task_id: UUID
    tool_name: str
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InformationRequested:
    employee_id: UUID
    task_id: UUID
    field: str
    question: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskFinished:
    employee_id: UUID
    task_id: UUID
    success: bool
    summary: str
    output: dict[str, Any]
    duration_minutes: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EmployeeSkill:
    """A skill the employee possesses with proficiency level."""

    name: str
    proficiency: float       # 0.0 (none) to 1.0 (expert)
    experience_years: float = 0.0


@dataclass(frozen=True, slots=True)
class ReceivedTask:
    """A task received for processing."""

    task_id: UUID
    title: str
    description: str
    department: str
    required_skills: tuple[str, ...] = field(default_factory=tuple)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskEstimate:
    """Analysis result for a task."""

    difficulty: float                   # 0.0 to 1.0
    estimated_time_minutes: int
    skill_match_pct: float              # 0.0 to 100.0
    missing_skills: tuple[str, ...] = field(default_factory=tuple)
    can_execute: bool = True


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Internal result produced after executing a task."""

    success: bool
    summary: str
    output: dict[str, Any] = field(default_factory=dict)
    duration_minutes: float = 0.0
    error: str = ""


# ------------------------------------------------------------------
# Helpers — deterministic execution
# ------------------------------------------------------------------

_SIGNATURES: dict[str, str] = {
    "video": "Video processing completed: source assets transcoded, edited, reviewed, and exported.",
    "audio": "Audio processing completed: source captured, mixed, mastered, and finalized.",
    "content": "Content piece produced: outline drafted, written, reviewed, and published.",
    "edit": "Editing pipeline executed: raw media organized, cut sequence assembled, color graded, audio synced, and final render delivered.",
    "article": "Article produced: topic researched, structure outlined, draft written, reviewed, and formatted for publication.",
    "market": "Marketing materials completed: strategy defined, creative assets produced, campaign ready for launch.",
    "sale": "Sales materials prepared: product positioned, pricing defined, outreach collateral created, funnel mapped.",
    "research": "Research conducted: data collected, analyzed, and report written with findings and recommendations.",
    "report": "Report generated: data aggregated, analyzed, formatted, and delivered with key insights.",
    "quality": "Quality review executed: criteria defined, deliverables inspected, results documented with sign-off status.",
    "coordination": "Coordination completed: schedule created, stakeholders aligned, execution monitored, status delivered.",
    "data": "Data task executed: source validated, transformation applied, output verified and delivered.",
    "default": "Task executed successfully: requirements processed, work completed, output prepared for review.",
}


def _deterministic_execute(
    task: ReceivedTask,
    skills: tuple[EmployeeSkill, ...],
) -> ExecutionResult:
    """Execute a task deterministically based on content keywords."""
    description_lower = f"{task.title} {task.description}".lower()
    all_keywords = " ".join([task.title.lower(), task.description.lower(), task.department.lower()])

    signature = _SIGNATURES.get("default")
    for keyword, sig in _SIGNATURES.items():
        if keyword in all_keywords:
            signature = sig
            break

    skill_names = [s.name.lower() for s in skills]
    matched_skills = [s for s in skill_names if s in all_keywords]

    output = {
        "task_id": str(task.task_id),
        "title": task.title,
        "department": task.department,
        "skills_applied": matched_skills,
        "result_type": task.department.lower().replace(" ", "_"),
        "artifacts": [
            f"{task.department} — {task.title}: primary output",
            f"{task.department} — {task.title}: supporting materials",
        ],
    }

    return ExecutionResult(
        success=True,
        summary=signature,
        output=output,
        duration_minutes=round(len(task.title) * 0.5 + len(task.description) * 0.3, 1),
    )


def _estimate_task(
    task: ReceivedTask,
    skills: tuple[EmployeeSkill, ...],
    current_workload: int,
) -> TaskEstimate:
    """Estimate difficulty and fit for a task based on skills."""
    all_task_text = f"{task.title} {task.description} {task.department}".lower()

    task_skills_required = set()
    if task.required_skills:
        task_skills_required = set(s.lower() for s in task.required_skills)
    else:
        for skill_name in [s.name for s in skills]:
            if skill_name.lower() in all_task_text:
                task_skills_required.add(skill_name.lower())
        if not task_skills_required:
            for word in all_task_text.split():
                if len(word) > 3:
                    task_skills_required.add(word)
                    break

    matching_skills = []
    missing_skills = []
    for req_skill in task_skills_required:
        found = False
        for emp_skill in skills:
            if emp_skill.name.lower() == req_skill:
                matching_skills.append(emp_skill)
                found = True
                break
        if not found:
            missing_skills.append(req_skill)

    total_needed = max(len(task_skills_required), 1)
    matched_count = len(matching_skills)
    skill_match_pct = round(matched_count / total_needed * 100.0, 1)

    avg_proficiency = 0.5
    if matching_skills:
        avg_proficiency = sum(s.proficiency for s in matching_skills) / len(matching_skills)

    base_complexity = len(task.title) / 50.0 + len(task.description) / 200.0
    skill_gap = 1.0 - (matched_count / max(total_needed, 1))
    workload_factor = current_workload * 0.15
    difficulty = min(1.0, base_complexity + skill_gap * 0.3 + workload_factor)

    base_time = int(10 + len(task.title) * 0.5 + len(task.description) * 0.2)
    adjusted_time = int(base_time * (1.0 + difficulty * 0.5) * (1.0 + workload_factor))
    adjusted_time = max(5, adjusted_time)

    can_execute = skill_match_pct >= 30.0 or matched_count > 0

    return TaskEstimate(
        difficulty=round(difficulty, 2),
        estimated_time_minutes=adjusted_time,
        skill_match_pct=skill_match_pct,
        missing_skills=tuple(missing_skills),
        can_execute=can_execute,
    )


# ------------------------------------------------------------------
# SpecialistEmployee
# ------------------------------------------------------------------

class SpecialistEmployee:
    """First intelligent employee of the AI Company.

    Modelo genérico baseado em Skills e Capabilities.
    Todos os futuros funcionários seguem este comportamento.

    O funcionário recebe tarefas, analisa se possui capacidade,
    aceita ou recusa, executa, e reporta resultados.
    """

    def __init__(
        self,
        company_runtime: CompanyRuntime,
        employee_id: UUID,
        skills: tuple[EmployeeSkill, ...] = (),
        *,
        event_bus: EventBus | None = None,
        department_manager: DepartmentManager | None = None,
        tool_runtime: ToolRuntime | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self._company = company_runtime
        self._employee_id = employee_id
        self._skills = skills
        self._department_manager = department_manager
        self._tool_runtime = tool_runtime
        self._tool_registry = tool_registry
        self._event_bus = event_bus or company_runtime.event_bus

        self._status: EmployeeStatus = EmployeeStatus.IDLE
        self._tasks: dict[UUID, ReceivedTask] = {}
        self._current_task_id: UUID | None = None
        self._workload: int = 0
        self._performance_score: float = 1.0
        self._confidence: float = 0.8
        self._total_tasks_completed: int = 0
        self._total_tasks_rejected: int = 0
        self._awaiting_tool_id: UUID | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def employee_id(self) -> UUID:
        return self._employee_id

    @property
    def status(self) -> EmployeeStatus:
        return self._status

    @property
    def skills(self) -> tuple[EmployeeSkill, ...]:
        return self._skills

    @property
    def workload(self) -> int:
        return self._workload

    @property
    def performance_score(self) -> float:
        return self._performance_score

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def total_tasks_completed(self) -> int:
        return self._total_tasks_completed

    @property
    def total_tasks_rejected(self) -> int:
        return self._total_tasks_rejected

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        """Receive and analyze a task. Accept or reject based on skills."""
        self._tasks[task.task_id] = task
        self._status = EmployeeStatus.ANALYZING

        estimate = _estimate_task(task, self._skills, self._workload)

        if not estimate.can_execute:
            self._status = EmployeeStatus.IDLE
            self._total_tasks_rejected += 1
            self._publish(TaskRejected(
                employee_id=self._employee_id,
                task_id=task.task_id,
                title=task.title,
                reason=f"Skill match too low ({estimate.skill_match_pct}%). "
                       f"Missing skills: {', '.join(estimate.missing_skills) if estimate.missing_skills else 'none matched'}.",
                missing_skills=estimate.missing_skills,
                timestamp=time.time(),
            ))
            return TaskDecision.REJECTED

        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.WORKING

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=estimate.difficulty,
            estimated_time_minutes=estimate.estimated_time_minutes,
            timestamp=time.time(),
        ))

        return TaskDecision.ACCEPTED

    def request_information(self, task_id: UUID, field: str, question: str) -> bool:
        """Request additional information before proceeding."""
        if task_id not in self._tasks:
            return False
        self._status = EmployeeStatus.AWAITING_INFO
        self._publish(InformationRequested(
            employee_id=self._employee_id,
            task_id=task_id,
            field=field,
            question=question,
            timestamp=time.time(),
        ))
        return True

    def request_tool(self, task_id: UUID, tool_name: str, reason: str) -> bool:
        """Request a tool needed for the task.

        If a ToolRuntime is connected, checks availability and
        publishes ToolUnavailable if the tool is missing config,
        credentials, or permissions.
        """
        if task_id not in self._tasks:
            return False

        self._status = EmployeeStatus.AWAITING_TOOL

        if self._tool_runtime is not None:
            tool_def = self._tool_runtime.find_by_name(tool_name)
            if tool_def is not None:
                self._awaiting_tool_id = tool_def.tool_id
                result = self._tool_runtime.request_tool(
                    tool_def.tool_id, self._employee_id, task_id=task_id,
                )
                if isinstance(result, ToolUnavailable):
                    missing = "; ".join(result.missing_items) if result.missing_items else result.reason
                    reason_with_info = f"{reason} [tool:{tool_name} unavailable: {missing}]"
                else:
                    reason_with_info = f"{reason} [tool:{tool_name} ready]"
            else:
                reason_with_info = f"{reason} [tool:{tool_name} not registered]"
        else:
            reason_with_info = reason

        self._publish(ToolRequested(
            employee_id=self._employee_id,
            task_id=task_id,
            tool_name=tool_name,
            reason=reason_with_info,
            timestamp=time.time(),
        ))
        return True

    def request_capability(self, task_id: UUID, capability: Capability | str, reason: str) -> bool:
        """Request a capability — the registry finds the best tool.

        The employee does NOT name a specific tool. The ToolRegistry
        resolves the capability to the best available tool.

        Args:
            task_id: The task that needs the capability.
            capability: The Capability enum value or string name.
            reason: Why the capability is needed.

        Returns:
            True if the request was accepted (tool may still be
            unavailable — check employee status or events).
        """
        if task_id not in self._tasks:
            return False

        cap_str = capability.value if isinstance(capability, Capability) else capability
        self._status = EmployeeStatus.AWAITING_TOOL

        if self._tool_registry is not None:
            cap_enum = Capability(cap_str)
            result = self._tool_registry.resolve(
                cap_enum, self._employee_id, task_id=task_id,
            )
            if isinstance(result, ToolSelected):
                self._awaiting_tool_id = result.tool_id
                reason_with_info = (
                    f"{reason} [capability:{cap_str} "
                    f"resolved to {result.tool_name}]"
                )
            else:
                reason_with_info = (
                    f"{reason} [capability:{cap_str} unavailable: "
                    f"{result.reason}]"
                )
        else:
            reason_with_info = f"{reason} [capability:{cap_str} — no registry]"

        self._publish(ToolRequested(
            employee_id=self._employee_id,
            task_id=task_id,
            tool_name=cap_str,
            reason=reason_with_info,
            timestamp=time.time(),
        ))
        return True

    def report_blocker(self, task_id: UUID, reason: str) -> bool:
        """Report a blocking issue that prevents progress."""
        if task_id not in self._tasks:
            return False
        self._status = EmployeeStatus.BLOCKED
        self._publish(TaskBlocked(
            employee_id=self._employee_id,
            task_id=task_id,
            reason=reason,
            timestamp=time.time(),
        ))
        return True

    def execute_task(self, task_id: UUID) -> ExecutionResult:
        """Execute a previously accepted task and produce a result."""
        task = self._tasks.get(task_id)
        if task is None:
            return ExecutionResult(success=False, summary="", error=f"Task {task_id} not found.")

        if self._current_task_id != task_id:
            return ExecutionResult(
                success=False, summary="",
                error=f"Task {task_id} is not the current task.",
            )

        self._publish(TaskStarted(
            employee_id=self._employee_id,
            task_id=task_id,
            title=task.title,
            timestamp=time.time(),
        ))

        self._status = EmployeeStatus.WORKING

        start = time.time()
        result = _deterministic_execute(task, self._skills)
        elapsed = time.time() - start

        duration = result.duration_minutes if result.duration_minutes > 0 else max(0.1, elapsed / 60.0)

        self._status = EmployeeStatus.COMPLETED

        self._publish(TaskFinished(
            employee_id=self._employee_id,
            task_id=task_id,
            success=result.success,
            summary=result.summary,
            output=result.output,
            duration_minutes=round(duration, 1),
            timestamp=time.time(),
        ))

        self._total_tasks_completed += 1
        self._confidence = min(1.0, self._confidence + 0.02)
        self._performance_score = round(
            (self._performance_score * (self._total_tasks_completed - 1) + (1.0 if result.success else 0.3))
            / max(self._total_tasks_completed, 1),
            3,
        )

        self._current_task_id = None
        self._status = EmployeeStatus.IDLE

        if self._department_manager is not None:
            self._department_manager.complete_task(task_id, self._employee_id, success=result.success)

        return result

    def provide_information(self, task_id: UUID, field: str, value: str) -> bool:
        """Receive requested information and resume working."""
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]
        new_context = dict(task.context)
        new_context[f"_info_{field}"] = value
        self._tasks[task_id] = ReceivedTask(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            department=task.department,
            required_skills=task.required_skills,
            context=new_context,
        )
        if self._status == EmployeeStatus.AWAITING_INFO:
            self._status = EmployeeStatus.WORKING
        return True

    def provide_tool(self, task_id: UUID, tool_name: str, available: bool) -> bool:
        """Receive a tool response and resume working or report blocker."""
        if task_id not in self._tasks:
            return False
        if not available:
            self._status = EmployeeStatus.BLOCKED
            self._publish(TaskBlocked(
                employee_id=self._employee_id,
                task_id=task_id,
                reason=f"Requested tool '{tool_name}' is not available.",
                timestamp=time.time(),
            ))
            return True
        if self._status in (EmployeeStatus.AWAITING_TOOL, EmployeeStatus.BLOCKED):
            self._status = EmployeeStatus.WORKING
            if self._tool_runtime is not None and self._awaiting_tool_id is not None:
                self._tool_runtime.release_tool(self._awaiting_tool_id, self._employee_id)
                self._awaiting_tool_id = None
        return True

    def request_review(self, task_id: UUID, reviewer_id: UUID) -> bool:
        """Submit the current task for peer review via the DepartmentManager."""
        if task_id not in self._tasks:
            return False
        if self._department_manager is None:
            return False
        result = self._department_manager.submit_for_review(task_id, self._employee_id, reviewer_id)
        if result.success:
            self._status = EmployeeStatus.IDLE
            self._current_task_id = None
        return result.success

    def hand_off(self, task_id: UUID, handoff_type: str, reason: str, to_employee_id: UUID | None = None) -> bool:
        """Request a hand-off via the DepartmentManager.

        handoff_type: \"forward\", \"review\", \"return\", \"awaiting_info\",
                      \"awaiting_tool\", \"awaiting_credentials\", \"awaiting_api\"
        """
        if task_id not in self._tasks:
            return False
        if self._department_manager is None:
            return False

        if handoff_type == "return":
            result = self._department_manager.return_task(task_id, self._employee_id, reason)
        elif handoff_type == "forward" and to_employee_id is not None:
            result = self._department_manager.route_task(task_id, self._employee_id, to_employee_id, reason)
        elif handoff_type.startswith("awaiting_"):
            await_type = handoff_type.replace("awaiting_", "")
            result = self._department_manager.mark_awaiting(task_id, self._employee_id, await_type, reason)
        else:
            return False

        if result.success:
            self._status = EmployeeStatus.IDLE
            self._current_task_id = None
        return result.success

    def state(self) -> dict[str, Any]:
        """Return the current state of this employee."""
        return {
            "employee_id": self._employee_id,
            "status": self._status,
            "current_task_id": self._current_task_id,
            "workload": self._workload,
            "skills": [(s.name, s.proficiency) for s in self._skills],
            "confidence": self._confidence,
            "performance_score": self._performance_score,
            "tasks_completed": self._total_tasks_completed,
            "tasks_rejected": self._total_tasks_rejected,
        }

    def events(self) -> list[Any]:
        if self._event_bus is None:
            return []
        return self._event_bus.events()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
