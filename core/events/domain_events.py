"""Domain-specific event types for the event-driven architecture.

All events are frozen dataclasses published by runtimes after
successful operations. Events are only published when an EventBus
instance is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


# ==================================================================
# Workflow events
# ==================================================================


@dataclass(frozen=True, slots=True)
class WorkflowStarted:
    workflow_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowTaskStarted:
    workflow_id: UUID
    task_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowTaskCompleted:
    workflow_id: UUID
    task_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowCompleted:
    workflow_id: UUID
    progress: float = 100.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Execution events
# ==================================================================


@dataclass(frozen=True, slots=True)
class ExecutionStarted:
    execution_id: UUID
    task_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionCompleted:
    execution_id: UUID
    task_id: UUID | None = None
    output: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionFailed:
    execution_id: UUID
    task_id: UUID | None = None
    error_message: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Conversation events
# ==================================================================


@dataclass(frozen=True, slots=True)
class ConversationCreated:
    session_id: UUID
    participant_id: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MessageAdded:
    session_id: UUID
    message_id: UUID
    role: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Memory events
# ==================================================================


@dataclass(frozen=True, slots=True)
class MemoryRecordCreated:
    memory_id: UUID
    source: str = ""
    category: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Knowledge events
# ==================================================================


@dataclass(frozen=True, slots=True)
class KnowledgePromoted:
    knowledge_id: UUID
    source: str = ""
    records_count: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Learning events
# ==================================================================


@dataclass(frozen=True, slots=True)
class RecommendationCreated:
    recommendation_id: UUID
    knowledge_id: UUID | None = None
    title: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Skill events
# ==================================================================


@dataclass(frozen=True, slots=True)
class SkillCreated:
    skill_id: UUID
    name: str = ""
    level: str = ""
    knowledge_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SkillPromoted:
    skill_id: UUID
    name: str = ""
    level: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SkillLevelChanged:
    skill_id: UUID
    name: str = ""
    previous_level: str = ""
    new_level: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Decision events
# ==================================================================


@dataclass(frozen=True, slots=True)
class DecisionApproved:
    decision_id: UUID
    task_id: UUID | None = None
    chosen_candidate_id: UUID | None = None
    decision_code: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DecisionRejected:
    decision_id: UUID
    task_id: UUID | None = None
    decision_code: str = ""
    explanation: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Collaboration events
# ==================================================================


@dataclass(frozen=True, slots=True)
class CollaborationStarted:
    session_id: UUID
    title: str = ""
    participants_count: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParticipantResponded:
    session_id: UUID
    participant_id: UUID
    decision: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CollaborationCompleted:
    session_id: UUID
    consensus: str = ""
    success: bool = False
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Company events
# ==================================================================


@dataclass(frozen=True, slots=True)
class CompanyTaskReceived:
    task_id: UUID
    title: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CompanyTaskRouted:
    task_id: UUID
    department_id: UUID | None = None
    employee_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CompanyTaskCompleted:
    task_id: UUID
    success: bool = False
    duration: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Orchestrator events
# ==================================================================


@dataclass(frozen=True, slots=True)
class OrchestratorExecutionStarted:
    orchestrator_id: UUID
    task_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OrchestratorExecutionCompleted:
    orchestrator_id: UUID
    task_id: UUID | None = None
    success: bool = False
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Persistence / Session events
# ==================================================================


@dataclass(frozen=True, slots=True)
class SessionCreated:
    session_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SessionLoaded:
    session_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SessionSaved:
    session_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SnapshotCreated:
    session_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SnapshotLoaded:
    session_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPersisted:
    execution_id: UUID
    session_id: UUID
    action: str = ""
    component: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionRestored:
    execution_id: UUID
    session_id: UUID
    action: str = ""
    component: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Human Approval events
# ==================================================================


@dataclass(frozen=True, slots=True)
class ApprovalRequested:
    approval_id: UUID
    source: str = ""
    subject_type: str = ""
    subject_id: str = ""
    risk_level: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApprovalDecided:
    approval_id: UUID
    status: str = ""
    decided_by: str = ""
    reason: str = ""
    source: str = ""
    subject_type: str = ""
    subject_id: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Organizational Memory events
# ==================================================================


@dataclass(frozen=True, slots=True)
class MemoryDocumentCreated:
    document_id: UUID
    title: str = ""
    category: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryDocumentUpdated:
    document_id: UUID
    title: str = ""
    category: str = ""
    version: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryDocumentArchived:
    document_id: UUID
    title: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Production events — published by ProductionEmployee during pipeline execution
# ==================================================================


@dataclass(frozen=True, slots=True)
class ProductionStarted:
    """Published when a production pipeline starts executing."""
    employee_id: UUID
    task_id: UUID
    department: str = ""
    production_type: str = ""
    stage: str = "created"
    timestamp: float = 0.0


@dataclass(frozen=True, slots=True)
class ProductionStageAdvanced:
    """Published after each successful pipeline stage advancement."""
    employee_id: UUID
    task_id: UUID
    department: str = ""
    stage: str = ""
    progress: float = 0.0
    success: bool = True
    error: str = ""
    timestamp: float = 0.0
    stages_completed: int = 0
    stages_failed: int = 0


@dataclass(frozen=True, slots=True)
class ProductionCompleted:
    """Published when a production pipeline finishes (completed or failed)."""
    employee_id: UUID
    task_id: UUID
    department: str = ""
    success: bool = True
    summary: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    duration_minutes: float = 0.0
    timestamp: float = 0.0


# ==================================================================
# Quality events
# ==================================================================


@dataclass(frozen=True, slots=True)
class QualityValidationStarted:
    execution_id: UUID
    task_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityValidationFinished:
    execution_id: UUID
    task_id: UUID | None = None
    passed: bool = False
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
