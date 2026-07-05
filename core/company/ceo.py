"""CEORuntime — first intelligent employee of AI Company.

Transforms business objectives into strategic executive plans.
The CEO does not execute tasks — it plans, decides, and delegates.

Generic and vertical-agnostic: knows nothing about specific domains.
Only understands the flow: objectives -> strategies -> departments -> execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.runtime import CompanyRuntime

# ------------------------------------------------------------------
# CEO-specific event types
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GoalReceived:
    """Published when a new business objective is received by the CEO."""
    goal_id: UUID
    objective: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ClarificationAsked:
    """Published when the CEO needs more information to proceed."""
    goal_id: UUID
    question: str
    field: str
    timestamp: float = 0.0


@dataclass(frozen=True, slots=True)
class PlanGenerated:
    """Published when the CEO produces an ExecutivePlan."""
    goal_id: UUID
    plan_id: UUID
    departments: tuple[str, ...]
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Department involvement heuristics
# ------------------------------------------------------------------

_DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "Content Production": [
        "conteudo", "content", "artigo", "article", "post", "blog",
        "texto", "text", "roteiro", "script", "copy", "legenda",
        "caption", "descricao", "description",
    ],
    "Video Editing": [
        "corte", "cut", "edit", "video", "film", "gravacao",
        "recording", "producao", "production", "stream", "live",
        "short", "reel", "tiktok", "youtube",
    ],
    "Audio Production": [
        "audio", "podcast", "music", "musica", "song",
        "narracao", "narration", "voz", "voice", "sound", "som",
        "trilha", "soundtrack",
    ],
    "Marketing": [
        "marketing", "divulgacao", "promotion", "promover", "promote",
        "anuncio", "ad", "campaign", "campanha", "midia",
        "media", "alcance", "reach", "engajamento", "engagement",
        "crescimento", "growth", "seo", "trafego", "traffic",
    ],
    "Sales": [
        "venda", "sell", "produto", "product", "afiliado", "affiliate",
        "curso", "course", "ebook", "receita", "revenue", "monetizar",
        "monetize", "assinatura", "subscription", "preco", "price",
    ],
    "Research": [
        "pesquisa", "research", "analise", "analysis", "mercado",
        "market", "concorrencia", "competition", "dados", "data",
        "metrica", "metric", "relatorio", "report", "tendencia",
        "trend",
    ],
    "Quality Assurance": [
        "revisao", "review", "qualidade", "quality", "aprovacao",
        "approval", "validacao", "validation", "teste", "test",
        "check", "verificacao", "verification",
    ],
    "Management": [
        "gerencia", "management", "coordenacao", "coordination",
        "planejamento", "planning", "estrategia", "strategy",
        "direcao", "direction", "lideranca", "leadership",
    ],
}

_DEFAULT_DEPARTMENT = "Management"

_QUESTION_TEMPLATES: dict[str, list[tuple[str, str, str]]] = {
    "Content Production": [
        ("content_type", "What type of content?", "e.g., article, blog post, social media copy"),
        ("quantity", "How many pieces?", "e.g., 10 articles"),
        ("language", "What language?", "e.g., Portuguese, English"),
        ("tone", "What tone?", "e.g., formal, casual, educational"),
        ("word_count", "Approximate length per piece?", "e.g., 1000-2000 words"),
    ],
    "Video Editing": [
        ("duration", "Desired duration per video?", "e.g., 30 seconds, 5-10 minutes"),
        ("quantity", "How many videos?", "e.g., 10 shorts"),
        ("format", "What format?", "e.g., vertical, horizontal, square"),
        ("platform", "Target platform?", "e.g., YouTube, TikTok, Instagram"),
        ("subtitles", "Need subtitles or captions?", "e.g., auto-generated, manual"),
    ],
    "Audio Production": [
        ("duration", "Desired duration per episode?", "e.g., 30-60 minutes"),
        ("frequency", "Release frequency?", "e.g., weekly, daily, monthly"),
        ("format", "Audio format?", "e.g., podcast episode, narration, music"),
        ("guests", "Guests per episode?", "e.g., 0, 1-2"),
    ],
    "Marketing": [
        ("platform", "Target platforms?", "e.g., Instagram, YouTube, LinkedIn, TikTok"),
        ("budget", "Campaign budget?", "e.g., $500 monthly"),
        ("target_audience", "Target audience?", "e.g., beginners, professionals, enterprises"),
        ("goals", "Primary marketing goals?", "e.g., awareness, engagement, conversion, retention"),
    ],
    "Sales": [
        ("product", "What product or service?", "e.g., course, ebook, software, consulting"),
        ("pricing", "Pricing model?", "e.g., one-time, subscription, freemium, free"),
        ("channel", "Sales channel?", "e.g., affiliate, direct, marketplace, partnership"),
        ("target_audience", "Target audience?", "e.g., B2B, B2C, creators, enterprises"),
    ],
    "Research": [
        ("scope", "Research scope?", "e.g., competitors, market trends, audience behavior"),
        ("depth", "Depth of analysis?", "e.g., overview, detailed report, deep dive"),
        ("deadline", "Research deadline?", "e.g., 1 week, 1 month"),
    ],
    "Quality Assurance": [
        ("standards", "Quality standards to follow?", "e.g., brand guidelines, style guide, checklist"),
        ("reviewers", "Who performs the review?", "e.g., team lead, senior editor, client"),
        ("rounds", "Maximum review rounds?", "e.g., 2, 3"),
    ],
    "Management": [
        ("timeline", "Overall project timeline?", "e.g., 1 month, 3 months, 6 months"),
        ("team_size", "How many people?", "e.g., 3, 5, 10"),
        ("priority", "Priority level?", "e.g., low, medium, high, critical"),
    ],
}

# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClarifyingQuestion:
    """A question the CEO needs answered before producing a plan."""
    field: str
    question: str
    example: str


@dataclass(frozen=True, slots=True)
class ExecutivePlan:
    """Complete strategic plan produced by the CEO for a business objective."""

    plan_id: UUID
    objective: str
    departments: tuple[str, ...]
    risks: tuple[str, ...]
    deliverables: tuple[str, ...]
    success_metrics: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    estimated_duration_days: int = 30
    priority: str = "MEDIUM"
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CEOTrace:
    """Execution trace for a single goal processing cycle."""
    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    questions_asked: int = 0


@dataclass(frozen=True, slots=True)
class CEOGoalResult:
    """Output of a CEO goal processing operation."""
    success: bool
    goal_id: UUID = field(default_factory=uuid4)
    plan: ExecutivePlan | None = None
    questions: tuple[ClarifyingQuestion, ...] = field(default_factory=tuple)
    trace: CEOTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _infer_departments(objective: str) -> list[str]:
    """Determine which departments should be involved based on objective keywords."""
    objective_lower = objective.lower()
    matched: list[str] = []
    for dept, keywords in _DEPARTMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in objective_lower:
                matched.append(dept)
                break
    if not matched:
        matched = [_DEFAULT_DEPARTMENT]
    ordered = [d for d in _DEPARTMENT_KEYWORDS if d in matched]
    for d in matched:
        if d not in ordered:
            ordered.append(d)
    return ordered


def _find_missing_info(
    objective: str,
    departments: list[str],
    answers: dict[str, str],
) -> list[ClarifyingQuestion]:
    """Identify what information is still missing for the given objective and departments."""
    questions: list[ClarifyingQuestion] = []
    for dept in departments:
        templates = _QUESTION_TEMPLATES.get(dept, [])
        for field_name, question, example in templates:
            if field_name not in answers:
                questions.append(ClarifyingQuestion(
                    field=field_name,
                    question=question,
                    example=example,
                ))
    return questions


def _build_deliverables(departments: list[str], answers: dict[str, str]) -> list[str]:
    """Generate deliverables list based on involved departments and gathered answers."""
    deliverables: list[str] = []
    for dept in departments:
        quantity = answers.get("quantity", "required")
        if dept == "Content Production":
            deliverables.append(f"{quantity} content pieces")
        elif dept == "Video Editing":
            deliverables.append(f"{quantity} edited videos")
        elif dept == "Audio Production":
            deliverables.append("Audio production files")
        elif dept == "Marketing":
            deliverables.append("Marketing strategy and campaign materials")
        elif dept == "Sales":
            deliverables.append("Sales materials and conversion funnel")
        elif dept == "Research":
            deliverables.append("Research report with analysis")
        elif dept == "Quality Assurance":
            deliverables.append("Quality review and sign-off")
        elif dept == "Management":
            deliverables.append("Project coordination and status reports")
    return deliverables if deliverables else ["Strategic plan execution"]


def _build_plan(
    objective: str,
    departments: list[str],
    answers: dict[str, str],
) -> ExecutivePlan:
    """Build an ExecutivePlan from a processed objective and gathered information."""
    priority = answers.get("priority", "MEDIUM").upper()
    if priority not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        priority = "MEDIUM"

    timeline_str = answers.get("timeline", "30 days")
    try:
        estimated_duration = int(timeline_str.split()[0])
    except (ValueError, IndexError):
        estimated_duration = 30

    deliverables = _build_deliverables(departments, answers)

    risks = [
        "Insufficient resource allocation for scope",
        "Timeline overrun due to complexity",
        "Quality inconsistency across departments",
        "Scope creep from unclear requirements",
    ]

    quantity = answers.get("quantity", "planned")
    success_metrics = [
        f"All {quantity} deliverables completed on schedule",
        "Quality standards met per department review",
        "Stakeholder approval obtained",
        "Within estimated budget and timeline",
    ]

    platform = answers.get("platform", "")
    if platform:
        success_metrics.append(f"Published and active on {platform}")

    completion_criteria = [
        f"All {quantity} items delivered and accepted",
        "Cross-departmental QA approval obtained",
        "Final report and metrics submitted",
        "Handover documentation completed",
    ]

    return ExecutivePlan(
        plan_id=uuid4(),
        objective=objective,
        departments=tuple(departments),
        risks=tuple(risks),
        deliverables=tuple(deliverables),
        success_metrics=tuple(success_metrics),
        completion_criteria=tuple(completion_criteria),
        estimated_duration_days=estimated_duration,
        priority=priority,
        created_at=_now(),
        metadata={"answers": dict(answers)},
    )


# ------------------------------------------------------------------
# CEORuntime
# ------------------------------------------------------------------


class CEORuntime:
    """First intelligent employee of AI Company.

    The CEO receives business objectives and transforms them into
    strategic executive plans. It does not execute tasks — it plans,
    decides, and delegates execution to departments and employees.

    Generic and vertical-agnostic: understands only the flow
    objectives -> strategies -> departments -> execution.

    Args:
        company_runtime: The low-level CompanyRuntime instance.
        event_bus: Optional EventBus for publishing events.
    """

    def __init__(
        self,
        company_runtime: CompanyRuntime,
        event_bus: EventBus | None = None,
    ) -> None:
        self._company = company_runtime
        self._event_bus = event_bus or company_runtime.event_bus
        self._goals: dict[UUID, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def receive_goal(
        self,
        objective: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> CEOGoalResult:
        """Receive a new business objective and begin processing.

        Args:
            objective: The business objective (e.g. \"create podcast clips\").
            metadata: Optional metadata for the goal.

        Returns:
            A CEOGoalResult with clarifying questions or the final plan.
        """
        start = _now()
        goal_id = uuid4()
        self._goals[goal_id] = {
            "objective": objective,
            "answers": {},
            "stage": "received",
            "metadata": dict(metadata) if metadata else {},
        }

        self._publish(GoalReceived(
            goal_id=goal_id,
            objective=objective,
            timestamp=start,
            metadata=dict(metadata) if metadata else {},
        ))

        return self._process_goal(goal_id)

    def answer_question(self, goal_id: UUID, field: str, value: str) -> CEOGoalResult:
        """Provide an answer to a clarifying question.

        Args:
            goal_id: The goal being processed.
            field: Which question field is being answered.
            value: The answer value.

        Returns:
            Updated CEOGoalResult with more questions or the final plan.
        """
        goal = self._goals.get(goal_id)
        if goal is None:
            return CEOGoalResult(
                success=False,
                goal_id=goal_id,
                error_message=f"Goal {goal_id} not found.",
            )

        goal["answers"][field] = value
        return self._process_goal(goal_id)

    def goal_state(self, goal_id: UUID) -> dict[str, Any] | None:
        """Get the current processing state of a goal."""
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        return {
            "goal_id": goal_id,
            "objective": goal["objective"],
            "answers": dict(goal["answers"]),
            "stage": goal["stage"],
        }

    def list_goals(self) -> list[dict[str, Any]]:
        """List all goals and their current processing stage."""
        return [
            {
                "goal_id": gid,
                "objective": g["objective"],
                "stage": g["stage"],
            }
            for gid, g in self._goals.items()
        ]

    def events(self) -> list[Any]:
        """Return all events published on the internal event bus."""
        if self._event_bus is None:
            return []
        return self._event_bus.events()

    # ------------------------------------------------------------------
    # Internal processing
    # ------------------------------------------------------------------

    def _process_goal(self, goal_id: UUID) -> CEOGoalResult:
        """Process a goal: infer departments, check for missing info, build plan."""
        start = _now()
        stages: list[str] = []
        goal = self._goals[goal_id]
        objective = goal["objective"]
        answers = goal["answers"]

        stages.append("infer_departments")
        departments = _infer_departments(objective)

        stages.append("check_missing_info")
        questions = _find_missing_info(objective, departments, answers)

        if questions:
            goal["stage"] = "awaiting_info"
            self._publish(ClarificationAsked(
                goal_id=goal_id,
                question=questions[0].question,
                field=questions[0].field,
                timestamp=_now(),
            ))
            elapsed = (_now() - start) * 1000.0
            return CEOGoalResult(
                success=True,
                goal_id=goal_id,
                questions=tuple(questions),
                trace=CEOTrace(
                    stages=tuple(stages),
                    duration_ms=elapsed,
                    questions_asked=len(questions),
                ),
            )

        stages.append("build_plan")
        plan = _build_plan(objective, departments, answers)
        goal["stage"] = "planned"
        goal["plan"] = plan

        self._publish(PlanGenerated(
            goal_id=goal_id,
            plan_id=plan.plan_id,
            departments=plan.departments,
            timestamp=_now(),
            metadata={"objective": objective, "priority": plan.priority},
        ))

        elapsed = (_now() - start) * 1000.0
        return CEOGoalResult(
            success=True,
            goal_id=goal_id,
            plan=plan,
            trace=CEOTrace(
                stages=tuple(stages),
                duration_ms=elapsed,
                questions_asked=0,
            ),
        )

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
