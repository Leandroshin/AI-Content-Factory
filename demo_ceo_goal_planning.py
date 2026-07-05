"""Demonstration script for the CEORuntime — first intelligent employee.

Scenarios:
  1. Receive a goal with missing information -> clarifying questions
  2. Answer questions -> receive ExecutivePlan
  3. Different objective: video production
  4. Different objective: sales/affiliate
  5. Generic keyword matching with English objective
  6. Goal with no department keywords -> defaults to Management
  7. Event verification
  8. Multiple concurrent goals
  9. Unknown priority fallback
  10. Edge cases: empty answers, repeated fields
"""

from __future__ import annotations

from uuid import UUID

from core.company.ceo import CEORuntime, ClarificationAsked, GoalReceived, PlanGenerated
from core.events.bus import EventBus
from core.runtime import CompanyRuntime


def _answer_all(ceo: CEORuntime, goal_id: UUID, answers: dict[str, str]) -> object:
    """Answer all questions, then trigger plan generation."""
    for field, value in answers.items():
        ceo.answer_question(goal_id, field, value)
    last_field = list(answers.keys())[-1]
    last_value = answers[last_field]
    r = ceo.answer_question(goal_id, last_field, last_value)
    return r.plan if r.success else None


def _print_plan(plan: object, label: str = "ExecutivePlan") -> None:
    print(f"\n  {label}:")
    print(f"    Objective: {plan.objective}")
    print(f"    Departments: {', '.join(plan.departments)}")
    print(f"    Priority: {plan.priority}")
    print(f"    Est. duration: {plan.estimated_duration_days} days")
    print(f"    Risks ({len(plan.risks)}):")
    for r in plan.risks:
        print(f"      - {r}")
    print(f"    Deliverables ({len(plan.deliverables)}):")
    for d in plan.deliverables:
        print(f"      - {d}")
    print(f"    Success metrics ({len(plan.success_metrics)}):")
    for m in plan.success_metrics:
        print(f"      - {m}")
    print(f"    Completion criteria ({len(plan.completion_criteria)}):")
    for c in plan.completion_criteria:
        print(f"      - {c}")


def main() -> None:
    print("=" * 60)
    print("CEO — First Intelligent Employee of AI Company")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    ceo = CEORuntime(company, event_bus)

    # ==================================================================
    # Scenario 1: Receive a goal -> clarifying questions
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 1: Receive a podcast clips goal")
    print("=" * 60)

    result = ceo.receive_goal("criar cortes de um podcast")
    assert result.success
    assert result.plan is None, "Plan should be None when questions remain"
    assert len(result.questions) > 0, "Should have clarifying questions"
    assert result.trace is not None
    assert "infer_departments" in result.trace.stages
    assert "check_missing_info" in result.trace.stages

    print(f"\n  Goal ID: {result.goal_id}")
    print(f"  Questions asked: {result.trace.questions_asked}")

    # Show the first few questions
    print("\n  Clarifying questions:")
    for i, q in enumerate(result.questions[:5], 1):
        print(f"    {i}. [{q.field}] {q.question}")
        print(f"       {q.example}")

    # Verify departments were inferred (should include Video Editing, Audio Production)
    goal_state = ceo.goal_state(result.goal_id)
    assert goal_state is not None
    assert goal_state["stage"] == "awaiting_info"
    print(f"\n  Goal stage: {goal_state['stage']}")
    print(f"  Answers so far: {goal_state['answers']}")

    # ==================================================================
    # Scenario 2: Answer questions -> receive plan
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 2: Answer questions and receive ExecutivePlan")
    print("=" * 60)

    goal_id = result.goal_id

    final_plan = _answer_all(ceo, goal_id, {
        "duration": "30-60 seconds",
        "quantity": "20",
        "format": "vertical",
        "platform": "TikTok, Instagram Reels",
        "subtitles": "auto-generated",
        "frequency": "daily",
        "guests": "0",
        "content_type": "short clips",
        "language": "Portuguese",
        "tone": "entertaining",
        "word_count": "N/A",
        "timeline": "2 weeks",
        "priority": "high",
    })
    assert final_plan is not None, "Should have a plan now"

    _print_plan(final_plan)

    assert final_plan.priority == "HIGH"
    assert "Video Editing" in final_plan.departments
    assert "Audio Production" in final_plan.departments
    assert len(final_plan.deliverables) > 0
    assert len(final_plan.risks) > 0
    assert len(final_plan.success_metrics) > 0

    # ==================================================================
    # Scenario 3: Different objective — video production
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 3: 'produzir videos para o YouTube'")
    print("=" * 60)

    r3 = ceo.receive_goal("produzir videos para o YouTube")
    assert r3.success
    assert len(r3.questions) > 0

    plan3 = _answer_all(ceo, r3.goal_id, {
        "duration": "10-15 minutes",
        "quantity": "12",
        "format": "horizontal",
        "platform": "YouTube",
        "subtitles": "manual",
        "timeline": "3 months",
        "priority": "medium",
    })
    assert plan3 is not None
    _print_plan(plan3, "Plan 3")
    assert "YouTube" in str(plan3.success_metrics)

    # ==================================================================
    # Scenario 4: Sales / affiliate objective
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 4: 'vender produtos por afiliado'")
    print("=" * 60)

    r4 = ceo.receive_goal("vender produtos por afiliado")
    assert r4.success
    assert len(r4.questions) > 0

    plan4 = _answer_all(ceo, r4.goal_id, {
        "product": "digital course on video editing",
        "pricing": "one-time $97",
        "channel": "affiliate networks",
        "target_audience": "content creators",
        "platform": "Instagram, YouTube",
        "budget": "$500",
        "goals": "sales and conversions",
        "timeline": "2 months",
        "priority": "critical",
    })
    assert plan4 is not None
    _print_plan(plan4, "Plan 4")
    assert "Sales" in plan4.departments
    assert plan4.priority == "CRITICAL"

    # ==================================================================
    # Scenario 5: English objective
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 5: 'launch a new ebook'")
    print("=" * 60)

    r5 = ceo.receive_goal("launch a new ebook")
    assert r5.success
    assert len(r5.questions) > 0
    print(f"  Departments inferred: {len(r5.questions)} questions needed")

    plan5 = _answer_all(ceo, r5.goal_id, {
        "content_type": "ebook",
        "quantity": "1",
        "language": "English",
        "product": "ebook on leadership",
        "pricing": "$9.99",
        "channel": "Amazon Kindle",
        "target_audience": "professionals",
        "timeline": "3 months",
        "priority": "high",
    })
    assert plan5 is not None
    _print_plan(plan5, "Plan 5")

    # ==================================================================
    # Scenario 6: No department keywords -> defaults to Management
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 6: Vague objective defaults to Management")
    print("=" * 60)

    r6 = ceo.receive_goal("quero melhorar a empresa")
    assert r6.success
    assert len(r6.questions) > 0
    print(f"  Questions: {len(r6.questions)}")

    plan6 = _answer_all(ceo, r6.goal_id, {
        "timeline": "6 months",
        "team_size": "5",
        "priority": "medium",
    })
    assert plan6 is not None
    _print_plan(plan6, "Plan 6")
    assert "Management" in plan6.departments
    assert len(plan6.departments) == 1, "Only Management should be inferred"

    # ==================================================================
    # Scenario 7: Event verification
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 7: Event verification")
    print("=" * 60)

    all_events = event_bus.events()
    goal_events = [e for e in all_events if isinstance(e, GoalReceived)]
    clarification_events = [e for e in all_events if isinstance(e, ClarificationAsked)]
    plan_events = [e for e in all_events if isinstance(e, PlanGenerated)]

    print(f"  GoalReceived events: {len(goal_events)}")
    print(f"  ClarificationAsked events: {len(clarification_events)}")
    print(f"  PlanGenerated events: {len(plan_events)}")

    assert len(goal_events) >= 5, f"Expected >=5 GoalReceived, got {len(goal_events)}"
    assert len(clarification_events) > 0, "Should have clarification events"
    assert len(plan_events) >= 4, f"Expected >=4 PlanGenerated, got {len(plan_events)}"

    for ev in goal_events[:2]:
        print(f"    - Goal: {ev.objective[:50]}...")

    for ev in plan_events[:2]:
        print(f"    - Plan for: {ev.metadata.get('objective', '?')[:50]}...")
        print(f"      Departments: {', '.join(ev.departments)}")

    # ==================================================================
    # Scenario 8: Multiple concurrent goals
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 8: Multiple concurrent goals")
    print("=" * 60)

    g1 = ceo.receive_goal("criar artigos para blog")
    g2 = ceo.receive_goal("produzir podcasts semanais")
    g3 = ceo.receive_goal("campanha de marketing no instagram")

    goals = ceo.list_goals()
    total_goals = len(goals)
    print(f"  Total goals tracked: {total_goals}")
    assert total_goals >= 8, f"Expected >=8, got {total_goals}"

    for g in goals:
        print(f"    - {g['objective'][:40]:40s} | stage: {g['stage']}")

    # Answer one of the new goals to completion
    plan_g1 = _answer_all(ceo, g1.goal_id, {
        "content_type": "blog post", "quantity": "20", "language": "Portuguese",
        "tone": "educational", "word_count": "1500",
        "timeline": "2 months", "priority": "high",
    })
    assert plan_g1 is not None
    assert plan_g1.priority == "HIGH"
    print(f"\n  Completed blog goal: {plan_g1.deliverables[0]}")

    # ==================================================================
    # Scenario 9: Unknown priority fallback
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 9: Unknown priority defaults to MEDIUM")
    print("=" * 60)

    r9 = ceo.receive_goal("testar fallback de prioridade")
    plan9 = _answer_all(ceo, r9.goal_id, {
        "content_type": "test", "quantity": "1", "language": "English",
        "platform": "internal", "budget": "$0", "target_audience": "devs", "goals": "test",
        "standards": "internal", "reviewers": "1", "rounds": "1",
        "timeline": "1 day", "priority": "urgent",
    })
    assert plan9 is not None
    assert plan9.priority == "MEDIUM", f"Expected MEDIUM fallback, got {plan9.priority}"
    print(f"  Priority 'urgent' -> fallback to {plan9.priority}")

    # ==================================================================
    # Scenario 10: Answer unknown goal
    # ==================================================================
    print("\n" + "=" * 60)
    print("Scenario 10: Answering an unknown goal")
    print("=" * 60)

    fake_id = UUID("00000000-0000-0000-0000-000000000000")
    bad = ceo.answer_question(fake_id, "test", "value")
    assert not bad.success
    assert bad.error_message != ""
    print(f"  Expected error: {bad.error_message}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print("CEO DEMONSTRATION SUMMARY")
    print("=" * 60)

    all_events = event_bus.events()
    passed = 0
    failed = 0

    checks = [
        ("S1: goal received", result.success, True),
        ("S1: clarifying questions returned", len(result.questions) > 0, True),
        ("S1: plan is None when questions remain", result.plan is None, True),
        ("S2: questions answered -> plan ready", final_plan is not None, True),
        ("S2: plan has departments", len(final_plan.departments) > 0, True),
        ("S2: plan has deliverables", len(final_plan.deliverables) > 0, True),
        ("S2: plan has risks", len(final_plan.risks) > 0, True),
        ("S2: plan has success metrics", len(final_plan.success_metrics) > 0, True),
        ("S2: plan has completion criteria", len(final_plan.completion_criteria) > 0, True),
        ("S3: YouTube video plan", plan3 is not None, True),
        ("S4: Sales/affiliate plan", plan4 is not None, True),
        ("S4: CRITICAL priority", plan4.priority == "CRITICAL", True),
        ("S5: English objective plan", plan5 is not None, True),
        ("S6: Management default department", "Management" in plan6.departments, True),
        ("S6: Only Management", len(plan6.departments) == 1, True),
        ("S9: Unknown priority fallback", plan9.priority == "MEDIUM", True),
        ("S10: Unknown goal error", not bad.success, True),
        ("S10: Error message not empty", bad.error_message != "", True),
        ("goal_state returns None for unknown", ceo.goal_state(fake_id) is None, True),
    ]

    for label, result_val, expected in checks:
        if result_val == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label} (expected {expected}, got {result_val})")

    print(f"\n  Total: {passed}/{passed + failed} passed, {failed} failed")
    print(f"  Demo scenarios: 10")
    print(f"  Assertions: {passed + failed}")
    print(f"  Events published: {len(all_events)}")
    print(f"  Goals tracked: {len(ceo.list_goals())}")
    print(f"  CEO is generic: knows no specific domain\n")


if __name__ == "__main__":
    main()
