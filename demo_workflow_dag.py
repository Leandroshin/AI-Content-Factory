"""Demo: Workflow Runtime with DAG, Branching, Parallelism and Merge.

Validates the DAG extension of the stateful WorkflowRuntime:
- Linear workflows (backward compatible)
- Branching (simple and multiple)
- Parallelism
- Merge with multiple predecessors
- Complex DAGs
- Cycle detection and rejection
- Dependency validation
- Progress tracking
- Foundation integration
- Determinism
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.runtime import CompanyRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntime, TaskRuntimeState
from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowRuntime as FoundationWorkflowRuntime,
    WorkflowStep,
)
from core.workflows import Workflow
from core.workflows.runtime import (
    WorkflowRuntime,
    WorkflowRuntimeState,
)


def _setup() -> tuple[WorkflowRuntime, CompanyRuntime, OrchestratorRuntime, TaskRuntime, EventBus]:
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)
    workflow_runtime = WorkflowRuntime(company, orchestrator, task_runtime, event_bus)
    company.initialize_company()
    department = department_runtime.create_department("Engineering")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)
    return workflow_runtime, company, orchestrator, task_runtime, event_bus


def _make_task(name: str) -> Task:
    t = Task(name=name)
    t.id = uuid4()
    return t


def _register_tasks(wr: WorkflowRuntime, tr: TaskRuntime, wf_id: UUID, *tasks: Task) -> None:
    for t in tasks:
        tr.register_task(t)
        wr.add_task(wf_id, t.id)


def _find_wfid(wr: WorkflowRuntime, task_id: UUID) -> UUID:
    for wid, snap in wr._workflows.items():
        if task_id in snap.task_ids:
            return wid
    raise KeyError(f"Task {task_id} not found in any workflow")


def _complete_task(
    wr: WorkflowRuntime, tr: TaskRuntime, task_id: UUID,
    employee_id: UUID | None = None,
) -> None:
    snap = tr._tasks[task_id]
    if snap.state not in (TaskRuntimeState.ASSIGNED, TaskRuntimeState.RUNNING):
        if employee_id is None:
            employee_id = next(iter(tr.company_runtime._employees))
        tr.transition(task_id, TaskRuntimeState.ASSIGNED, employee_id=employee_id)
        tr.transition(task_id, TaskRuntimeState.RUNNING)
    wr.complete_task(_find_wfid(wr, task_id), task_id)


def _find_workflow_id(wr: WorkflowRuntime, name: str) -> UUID:
    for snap in wr.snapshot():
        if snap.name == name:
            return snap.workflow_id
    raise KeyError(f"Workflow '{name}' not found")


# ==================================================================
# 1. Workflow linear (backward compat)
# ==================================================================

def scenario_linear_workflow() -> None:
    """Linear workflow still works exactly like before."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="LinearWF")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.start(wf.id)
    snap = wr._require_workflow(wf.id)
    assert snap.current_task_id == a.id, "Linear: first task should be ready"

    _complete_task(wr, tr, a.id)
    assert wr.progress(wf.id) > 0

    _complete_task(wr, tr, b.id)
    _complete_task(wr, tr, c.id)
    assert wr.progress(wf.id) == 100.0
    assert wr._require_workflow(wf.id).state == WorkflowRuntimeState.COMPLETED
    print(f"[PASS] linear_workflow                   | progress=100% state=completed")


# ==================================================================
# 2. Branching simples: A -> [B, C]
# ==================================================================

def scenario_branching_simple() -> None:
    """Simple branching: one task fans out to two."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BranchSimple")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    wr.start(wf.id)
    assert wr._require_workflow(wf.id).current_task_id == a.id

    _complete_task(wr, tr, a.id)
    ready = wr.get_ready_tasks(wf.id)
    assert b.id in ready
    assert c.id in ready
    assert len(ready) == 2, f"Expected 2 ready tasks, got {len(ready)}"
    print(f"[PASS] branching_simple                  | A -> [B, C]: {len(ready)} ready after A")


# ==================================================================
# 3. Branching múltiplo: A -> [B, C, D]
# ==================================================================

def scenario_branching_multiple() -> None:
    """Multiple branching: one task fans out to three."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BranchMulti")
    wr.register_workflow(wf)

    a = _make_task("A")
    branches = [_make_task(f"B{i}") for i in range(3)]
    _register_tasks(wr, tr, wf.id, a, *branches)

    for b in branches:
        wr.add_dependency(wf.id, b.id, a.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)

    ready = wr.get_ready_tasks(wf.id)
    assert len(ready) == 3
    for b in branches:
        assert b.id in ready
    print(f"[PASS] branching_multiple                | A -> [B0,B1,B2]: {len(ready)} ready")


# ==================================================================
# 4. Merge: [A, B] -> C
# ==================================================================

def scenario_merge_two_predecessors() -> None:
    """Merge: two predecessors converge into one."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="Merge")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    wr.start(wf.id)
    ready = wr.get_ready_tasks(wf.id)
    assert a.id in ready and b.id in ready
    assert c.id not in ready

    _complete_task(wr, tr, a.id)
    assert c.id not in wr.get_ready_tasks(wf.id), "C needs B still"

    _complete_task(wr, tr, b.id)
    assert c.id in wr.get_ready_tasks(wf.id), "C should be ready now"
    print(f"[PASS] merge_two_predecessors            | [A,B] -> C: C ready after both")


# ==================================================================
# 5. Paralelismo: A -> [B, C] -> D
# ==================================================================

def scenario_parallel_then_merge() -> None:
    """Parallel execution then merge: A -> [B, C] -> D."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ParallelMerge")
    wr.register_workflow(wf)

    a, b, c, d = _make_task("A"), _make_task("B"), _make_task("C"), _make_task("D")
    _register_tasks(wr, tr, wf.id, a, b, c, d)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, d.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)

    assert b.id in wr.get_ready_tasks(wf.id)
    assert c.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, b.id)
    assert d.id not in wr.get_ready_tasks(wf.id), "D needs C too"

    _complete_task(wr, tr, c.id)
    assert d.id in wr.get_ready_tasks(wf.id)
    _complete_task(wr, tr, d.id)

    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] parallel_then_merge               | A->[B,C]->D: parallel exec + merge sync")


# ==================================================================
# 6. DAG complexo — 3 camadas
# ==================================================================

def scenario_complex_dag() -> None:
    """Complex DAG with 3 layers of dependencies."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ComplexDAG")
    wr.register_workflow(wf)

    a, b, c, d, e, f = [_make_task(n) for n in ["A", "B", "C", "D", "E", "F"]]
    _register_tasks(wr, tr, wf.id, a, b, c, d, e, f)

    # Layer 1: A -> B, A -> C
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)
    # Layer 2: B -> D, C -> D, C -> E
    wr.add_dependency(wf.id, d.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)
    wr.add_dependency(wf.id, e.id, c.id)
    # Layer 3: D -> F, E -> F
    wr.add_dependency(wf.id, f.id, d.id)
    wr.add_dependency(wf.id, f.id, e.id)

    wr.start(wf.id)
    assert wr._require_workflow(wf.id).current_task_id == a.id

    _complete_task(wr, tr, a.id)
    assert len(wr.get_ready_tasks(wf.id)) == 2  # B, C

    _complete_task(wr, tr, b.id)
    ready = wr.get_ready_tasks(wf.id)
    assert d.id not in ready  # D needs C too

    _complete_task(wr, tr, c.id)
    ready = wr.get_ready_tasks(wf.id)
    assert d.id in ready and e.id in ready

    _complete_task(wr, tr, d.id)
    _complete_task(wr, tr, e.id)
    assert f.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, f.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] complex_dag                        | 3-layer DAG: 6 tasks, layered deps")


# ==================================================================
# 7. Ciclo inválido — rejeitado por add_dependency
# ==================================================================

def scenario_cycle_detection() -> None:
    """Cycle detection: add_dependency rejects cycles."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="CycleWF")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    try:
        wr.add_dependency(wf.id, a.id, c.id)
        assert False, "Should have raised ValueError for cycle"
    except ValueError as e:
        assert "cycle" in str(e).lower()
    print(f"[PASS] cycle_detection                   | A->B->C->A rejected")


# ==================================================================
# 8. Self-dependency rejeitada
# ==================================================================

def scenario_self_dependency() -> None:
    """Self-dependency is rejected."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="SelfDepWF")
    wr.register_workflow(wf)

    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    try:
        wr.add_dependency(wf.id, a.id, a.id)
        assert False, "Should have raised ValueError for self-dependency"
    except ValueError as e:
        assert "cannot depend on itself" in str(e).lower()
    print(f"[PASS] self_dependency                   | A->A rejected")


# ==================================================================
# 9. Dependência inexistente
# ==================================================================

def scenario_dependency_nonexistent() -> None:
    """Dependency on non-existent task raises KeyError."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BadDepWF")
    wr.register_workflow(wf)

    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    fake_id = uuid4()
    try:
        wr.add_dependency(wf.id, a.id, fake_id)
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
    print(f"[PASS] dependency_nonexistent            | A -> nonexistent rejected")


# ==================================================================
# 10. Múltiplos predecessores via query
# ==================================================================

def scenario_multiple_predecessors_query() -> None:
    """get_predecessors returns all ancestors of a task."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="PredQuery")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    preds = wr.get_predecessors(wf.id, c.id)
    assert len(preds) == 2
    assert a.id in preds and b.id in preds
    print(f"[PASS] multiple_predecessors_query       | C predecessors: {len(preds)}")


# ==================================================================
# 11. Múltiplos sucessores via query
# ==================================================================

def scenario_multiple_successors_query() -> None:
    """get_dependents returns all successors of a task."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="SuccQuery")
    wr.register_workflow(wf)

    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    deps = wr.get_dependents(wf.id, a.id)
    assert len(deps) == 2
    assert b.id in deps and c.id in deps
    print(f"[PASS] multiple_successors_query         | A dependents: {len(deps)}")


# ==================================================================
# 12. has_dag — detecção de modo
# ==================================================================

def scenario_has_dag() -> None:
    """has_dag correctly detects DAG vs linear workflows."""
    wr, _, _, tr, _ = _setup()
    wf_lin = Workflow(name="Linear")
    wr.register_workflow(wf_lin)
    assert wr.has_dag(wf_lin.id) is False, "Linear has no DAG"

    wf_dag = Workflow(name="DAG")
    wr.register_workflow(wf_dag)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf_dag.id, a, b)
    wr.add_dependency(wf_dag.id, b.id, a.id)
    assert wr.has_dag(wf_dag.id) is True, "DAG should be detected"
    print(f"[PASS] has_dag                            | linear=False, dag=True")


# ==================================================================
# 13. validate_dag — DAG válido
# ==================================================================

def scenario_validate_dag_valid() -> None:
    """validate_dag returns True for valid DAGs."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ValidDAG")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    assert wr.validate_dag(wf.id) is True
    print(f"[PASS] validate_dag_valid                | valid DAG = True")


# ==================================================================
# 14. validate_dag — DAG inválido (ciclo)
# ==================================================================

def scenario_validate_dag_invalid() -> None:
    """validate_dag returns False for cyclic DAGs."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="InvalidDAG")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    # Manually inject a cycle to test validation
    deps = wr._dag_dependencies[wf.id]
    deps.setdefault(a.id, set()).add(c.id)
    wr._dag_dependents[wf.id].setdefault(c.id, set()).add(a.id)

    assert wr.validate_dag(wf.id) is False
    print(f"[PASS] validate_dag_invalid              | cyclic DAG = False")


# ==================================================================
# 15. validate_dependency
# ==================================================================

def scenario_validate_dependency() -> None:
    """validate_dependency checks existence of specific edge."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="DepCheck")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.add_dependency(wf.id, b.id, a.id)

    assert wr.validate_dependency(wf.id, b.id, a.id) is True
    assert wr.validate_dependency(wf.id, a.id, b.id) is False
    assert wr.validate_dependency(wf.id, b.id, uuid4()) is False
    print(f"[PASS] validate_dependency               | edge exists=True, reverse=False")


# ==================================================================
# 16. get_ready_tasks — vazio no início
# ==================================================================

def scenario_ready_tasks_initially() -> None:
    """get_ready_tasks returns root tasks initially."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ReadyInit")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    ready = wr.get_ready_tasks(wf.id)
    assert len(ready) == 1
    assert ready[0] == a.id
    print(f"[PASS] ready_tasks_initially             | root task A ready")


# ==================================================================
# 17. get_blocked_tasks
# ==================================================================

def scenario_blocked_tasks() -> None:
    """get_blocked_tasks returns tasks with unmet deps."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="Blocked")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    blocked = wr.get_blocked_tasks(wf.id)
    assert b.id in blocked
    assert c.id in blocked
    assert a.id not in blocked
    print(f"[PASS] blocked_tasks                     | [B,C] blocked, A not")


# ==================================================================
# 18. Progresso em DAG
# ==================================================================

def scenario_dag_progress() -> None:
    """Progress calculation works correctly for DAGs."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="DagProgress")
    wr.register_workflow(wf)
    a, b, c, d = _make_task("A"), _make_task("B"), _make_task("C"), _make_task("D")
    _register_tasks(wr, tr, wf.id, a, b, c, d)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, d.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)

    wr.start(wf.id)
    assert wr.progress(wf.id) == 0.0

    _complete_task(wr, tr, a.id)
    assert wr.progress(wf.id) == 25.0  # 1/4

    _complete_task(wr, tr, b.id)
    assert wr.progress(wf.id) == 50.0  # 2/4

    _complete_task(wr, tr, c.id)
    assert wr.progress(wf.id) == 75.0  # 3/4

    _complete_task(wr, tr, d.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] dag_progress                       | 25->50->75->100%")


# ==================================================================
# 19. remove_dependency
# ==================================================================

def scenario_remove_dependency() -> None:
    """remove_dependency removes an edge correctly."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="RemoveDep")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)

    wr.add_dependency(wf.id, b.id, a.id)
    assert wr.validate_dependency(wf.id, b.id, a.id) is True

    wr.remove_dependency(wf.id, b.id, a.id)
    assert wr.validate_dependency(wf.id, b.id, a.id) is False
    assert wr.has_dag(wf.id) is False
    print(f"[PASS] remove_dependency                 | edge removed, has_dag=False")


# ==================================================================
# 20. add_dependencies batch
# ==================================================================

def scenario_add_dependencies_batch() -> None:
    """add_dependencies adds multiple edges at once."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BatchDep")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.add_dependencies(wf.id, c.id, [a.id, b.id])
    assert wr.validate_dependency(wf.id, c.id, a.id) is True
    assert wr.validate_dependency(wf.id, c.id, b.id) is True
    assert len(wr.get_predecessors(wf.id, c.id)) == 2
    print(f"[PASS] add_dependencies_batch            | C deps on [A,B]: 2 predecessors")


# ==================================================================
# 21. add_dependencies batch com ciclo rejeita tudo
# ==================================================================

def scenario_add_dependencies_batch_cycle() -> None:
    """add_dependencies rejects entire batch if one edge creates cycle."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BatchCycle")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    # Trying A -> C would create A->B->C->A cycle
    try:
        wr.add_dependencies(wf.id, a.id, [c.id])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print(f"[PASS] add_dependencies_batch_cycle      | batch with cycle rejected")


# ==================================================================
# 22. Determinismo — mesmo DAG, mesma ordem
# ==================================================================

def scenario_determinism_dag() -> None:
    """DAG execution order is deterministic for same inputs."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="DetDAG")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    wr.start(wf.id)
    order: list[UUID] = []
    while wr._require_workflow(wf.id).state != WorkflowRuntimeState.COMPLETED:
        nt = wr.next_task(wf.id) if not wr.next_task(wf.id) else wr._require_workflow(wf.id).current_task_id
        if nt is None:
            break
        _complete_task(wr, tr, nt)
        order.append(nt)

    # A should be first, B and C should follow
    assert order[0] == a.id
    # B and C are in registration order (deterministic)
    assert order[1] == b.id
    assert order[2] == c.id
    print(f"[PASS] determinism_dag                   | order deterministic: A->B->C")


# ==================================================================
# 23. DAG com todas as tarefas independentes (paralelismo puro)
# ==================================================================

def scenario_all_independent() -> None:
    """All tasks independent: all ready at start."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="AllIndep")
    wr.register_workflow(wf)
    tasks = [_make_task(f"T{i}") for i in range(5)]
    _register_tasks(wr, tr, wf.id, *tasks)

    wr.start(wf.id)
    ready = wr.get_ready_tasks(wf.id)
    assert len(ready) == 5
    print(f"[PASS] all_independent                   | 5 tasks all ready at start")


# ==================================================================
# 24. DAG com dependência encadeada longa
# ==================================================================

def scenario_long_chain() -> None:
    """Long chain of dependencies: A -> B -> C -> D -> E."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="LongChain")
    wr.register_workflow(wf)
    tasks = [_make_task(f"S{i}") for i in range(10)]
    _register_tasks(wr, tr, wf.id, *tasks)

    for i in range(1, len(tasks)):
        wr.add_dependency(wf.id, tasks[i].id, tasks[i - 1].id)

    wr.start(wf.id)
    for t in tasks:
        ready = wr.get_ready_tasks(wf.id)
        assert len(ready) == 1
        assert ready[0] == t.id
        _complete_task(wr, tr, t.id)

    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] long_chain                         | 10-chain: sequential, 100%")


# ==================================================================
# 25. DAG com diamond: A -> [B, C] -> D
# ==================================================================

def scenario_diamond_dag() -> None:
    """Diamond DAG: A -> B, A -> C, B -> D, C -> D."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="Diamond")
    wr.register_workflow(wf)
    a, b, c, d = _make_task("A"), _make_task("B"), _make_task("C"), _make_task("D")
    _register_tasks(wr, tr, wf.id, a, b, c, d)

    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, d.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)
    assert b.id in wr.get_ready_tasks(wf.id)
    assert c.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, b.id)
    assert d.id not in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, c.id)
    assert d.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, d.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] diamond_dag                        | A->[B,C]->D: 4 tasks, sync at D")


# ==================================================================
# 26. DAG progress — blocked tasks prevent premature completion
# ==================================================================

def scenario_dag_blocked_no_premature_complete() -> None:
    """_advance does not mark completed when blocked tasks exist."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="NoPremature")
    wr.register_workflow(wf)

    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.add_dependency(wf.id, b.id, a.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)

    assert wr._require_workflow(wf.id).state != WorkflowRuntimeState.COMPLETED
    print(f"[PASS] dag_blocked_no_premature_complete  | not completed with blocked task")


# ==================================================================
# 27. Foundation integration with DAG
# ==================================================================

def scenario_foundation_integration() -> None:
    """Promoted foundation workflows can still use DAG extensions."""
    wr, _, _, tr, _ = _setup()
    step_a = WorkflowStep.create("A")
    step_b = WorkflowStep.create("B")
    step_c = WorkflowStep.create("C")
    fd = FoundationWorkflowRuntime.create_definition(
        "FoundationDAG", steps=[step_a, step_b, step_c],
    )
    snap = wr.create_from_foundation(fd)
    wf_id = snap.workflow_id

    wr.add_dependency(wf_id, step_b.step_id, step_a.step_id)
    wr.add_dependency(wf_id, step_c.step_id, step_b.step_id)
    assert wr.validate_dag(wf_id) is True

    wr.start(wf_id)
    _complete_task(wr, tr, step_a.step_id)
    assert step_b.step_id in wr.get_ready_tasks(wf_id)

    _complete_task(wr, tr, step_b.step_id)
    assert step_c.step_id in wr.get_ready_tasks(wf_id)

    _complete_task(wr, tr, step_c.step_id)
    assert wr.progress(wf_id) == 100.0
    print(f"[PASS] foundation_integration            | promoted foundation + DAG = OK")


# ==================================================================
# 28. Empty workflow still works
# ==================================================================

def scenario_empty_workflow() -> None:
    """Empty workflow (no tasks) starts and completes immediately."""
    wr, _, _, _, _ = _setup()
    wf = Workflow(name="EmptyWF")
    wr.register_workflow(wf)
    wr.start(wf.id)

    snap = wr._require_workflow(wf.id)
    assert snap.state == WorkflowRuntimeState.COMPLETED
    assert snap.progress == 100.0
    print(f"[PASS] empty_workflow                     | no tasks, immediate complete")


# ==================================================================
# 29. Single task DAG
# ==================================================================

def scenario_single_task_dag() -> None:
    """Single task with no dependencies works as expected."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="SingleTask")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    wr.start(wf.id)
    assert wr._require_workflow(wf.id).current_task_id == a.id
    _complete_task(wr, tr, a.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] single_task_dag                    | single task completes")


# ==================================================================
# 30. DAG — ordem de ready tasks segue registro
# ==================================================================

def scenario_ready_order_deterministic() -> None:
    """get_ready_tasks returns tasks in registration order."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ReadyOrder")
    wr.register_workflow(wf)

    tasks = [_make_task(f"T{i}") for i in range(4)]
    _register_tasks(wr, tr, wf.id, *tasks)

    # All independent — all ready
    ready = wr.get_ready_tasks(wf.id)
    for i, t in enumerate(tasks):
        assert ready[i] == t.id
    print(f"[PASS] ready_order_deterministic          | ready tasks follow reg order")


# ==================================================================
# 31. DAG com 2 tarefas enfileiradas
# ==================================================================

def scenario_two_independent_tasks() -> None:
    """Two independent tasks: both are ready after start."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="TwoIndep")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)

    wr.start(wf.id)
    ready = wr.get_ready_tasks(wf.id)
    assert len(ready) == 2
    print(f"[PASS] two_independent_tasks             | [A,B] both ready")


# ==================================================================
# 32. DAG — suporte a next_task com DAG
# ==================================================================

def scenario_next_task_dag() -> None:
    """next_task returns ready tasks for DAG workflows."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="NextTaskDAG")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.add_dependency(wf.id, b.id, a.id)

    wr.start(wf.id)
    assert wr.next_task(wf.id) == a.id or wr._require_workflow(wf.id).current_task_id == a.id

    _complete_task(wr, tr, a.id)
    assert wr.next_task(wf.id) == b.id
    print(f"[PASS] next_task_dag                      | next_task respects DAG")


# ==================================================================
# 33. DAG — progresso 0% antes de começar
# ==================================================================

def scenario_progress_zero() -> None:
    """Progress is 0 before workflow starts."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="ZeroProgress")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.add_dependency(wf.id, b.id, a.id)

    assert wr.progress(wf.id) == 0.0
    print(f"[PASS] progress_zero                      | before start: 0%")


# ==================================================================
# 34. DAG — validação de DAG no workflow linear
# ==================================================================

def scenario_validate_linear_dag() -> None:
    """validate_dag returns True for linear workflows (no deps = valid)."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="LinearValid")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    assert wr.validate_dag(wf.id) is True
    print(f"[PASS] validate_linear_dag               | linear (no deps) = valid")


# ==================================================================
# 35. add_task inicializa estruturas DAG
# ==================================================================

def scenario_add_task_initializes_dag() -> None:
    """add_task initializes DAG structures for the new task."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="InitDAG")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    deps = wr._dag_dependencies[wf.id]
    assert a.id in deps
    assert deps[a.id] == set()

    deps_to = wr._dag_dependents[wf.id]
    assert a.id in deps_to
    assert deps_to[a.id] == set()
    print(f"[PASS] add_task_initializes_dag           | DAG structures initialized")


# ==================================================================
# 36. DAG — duas camadas com fan-in
# ==================================================================

def scenario_fan_in_multiple() -> None:
    """Fan-in: 3 tasks merge into 1."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="FanIn")
    wr.register_workflow(wf)
    a, b, c, d = _make_task("A"), _make_task("B"), _make_task("C"), _make_task("D")
    _register_tasks(wr, tr, wf.id, a, b, c, d)
    wr.add_dependency(wf.id, d.id, a.id)
    wr.add_dependency(wf.id, d.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)
    _complete_task(wr, tr, b.id)
    assert d.id not in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, c.id)
    assert d.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, d.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] fan_in_multiple                    | [A,B,C]->D: 3-to-1 fan-in")


# ==================================================================
# 37. DAG — DAG complexo com 8 tarefas
# ==================================================================

def scenario_complex_dag_8tasks() -> None:
    """Complex 8-task DAG with multiple layers."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="Complex8")
    wr.register_workflow(wf)

    t = {n: _make_task(n) for n in ["A", "B", "C", "D", "E", "F", "G", "H"]}
    _register_tasks(wr, tr, wf.id, *t.values())

    # A -> [B, C]
    wr.add_dependency(wf.id, t["B"].id, t["A"].id)
    wr.add_dependency(wf.id, t["C"].id, t["A"].id)
    # B -> [D, E]
    wr.add_dependency(wf.id, t["D"].id, t["B"].id)
    wr.add_dependency(wf.id, t["E"].id, t["B"].id)
    # C -> [E, F]
    wr.add_dependency(wf.id, t["E"].id, t["C"].id)
    wr.add_dependency(wf.id, t["F"].id, t["C"].id)
    # [D, E] -> G
    wr.add_dependency(wf.id, t["G"].id, t["D"].id)
    wr.add_dependency(wf.id, t["G"].id, t["E"].id)
    # [F, G] -> H
    wr.add_dependency(wf.id, t["H"].id, t["F"].id)
    wr.add_dependency(wf.id, t["H"].id, t["G"].id)

    assert wr.validate_dag(wf.id) is True

    wr.start(wf.id)
    _complete_task(wr, tr, t["A"].id)
    assert len(wr.get_ready_tasks(wf.id)) == 2

    _complete_task(wr, tr, t["B"].id)
    _complete_task(wr, tr, t["C"].id)
    ready = wr.get_ready_tasks(wf.id)
    assert t["D"].id in ready and t["F"].id in ready

    _complete_task(wr, tr, t["D"].id)
    _complete_task(wr, tr, t["F"].id)
    _complete_task(wr, tr, t["E"].id)
    assert t["G"].id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, t["G"].id)
    assert t["H"].id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, t["H"].id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] complex_dag_8tasks                 | 8-task DAG executes fully")


# ==================================================================
# 38. Backward compat: task_runtime.snapshot() unchanged
# ==================================================================

def scenario_backward_compat_snapshot() -> None:
    """snapshot() still returns all workflows correctly."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="CompatSnap")
    wr.register_workflow(wf)

    snaps = wr.snapshot()
    assert any(s.name == "CompatSnap" for s in snaps)
    print(f"[PASS] backward_compat_snapshot           | snapshot() works as before")


# ==================================================================
# 39. Backward compat: events() unchanged
# ==================================================================

def scenario_backward_compat_events() -> None:
    """events() still returns all emitted events."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="CompatEvents")
    wr.register_workflow(wf)

    evts = wr.events()
    assert len(evts) >= 1  # CREATED -> PLANNED
    print(f"[PASS] backward_compat_events             | events() works as before")


# ==================================================================
# 40. Backward compat: linear workflow from foundation
# ==================================================================

def scenario_backward_compat_foundation() -> None:
    """Foundation promotion with linear steps still works."""
    wr, _, _, tr, _ = _setup()
    s1 = WorkflowStep.create("Alpha")
    s2 = WorkflowStep.create("Beta")
    fd = FoundationWorkflowRuntime.create_definition("CompatFD", steps=[s1, s2])
    snap = wr.create_from_foundation(fd)

    assert snap.name == "CompatFD"
    assert len(snap.task_ids) == 2
    print(f"[PASS] backward_compat_foundation         | create_from_foundation OK")


# ==================================================================
# 41. DAG com 2 roots independentes
# ==================================================================

def scenario_two_roots() -> None:
    """Two root tasks with no dependencies between them."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="TwoRoots")
    wr.register_workflow(wf)
    a, b, c, d = _make_task("A"), _make_task("B"), _make_task("C"), _make_task("D")
    _register_tasks(wr, tr, wf.id, a, b, c, d)

    wf_id = wf.id
    wr.add_dependency(wf_id, c.id, a.id)
    wr.add_dependency(wf_id, d.id, b.id)

    wr.start(wf_id)
    ready = wr.get_ready_tasks(wf_id)
    assert a.id in ready and b.id in ready
    assert c.id not in ready and d.id not in ready
    print(f"[PASS] two_roots                          | A,B roots; C,D blocked")


# ==================================================================
# 42. Determinismo com next_task em DAG
# ==================================================================

def scenario_dag_next_task_determinism() -> None:
    """next_task returns same order for same DAG structure."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="DAGDetNext")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    wr.start(wf.id)
    # Before completing A, next_task should return a.id (current)
    _complete_task(wr, tr, a.id)
    nt = wr.next_task(wf.id)
    assert nt == b.id, f"Expected B first, got {nt}"
    print(f"[PASS] dag_next_task_determinism          | next_task=B (registration order)")


# ==================================================================
# 43. DAG completo com múltiplos níveis de merge
# ==================================================================

def scenario_multi_level_merge() -> None:
    """Multi-level merge: tasks merge at two different layers."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="MultiMerge")
    wr.register_workflow(wf)
    a, b, c, d, e = [_make_task(n) for n in ["A", "B", "C", "D", "E"]]
    _register_tasks(wr, tr, wf.id, a, b, c, d, e)

    wr.add_dependency(wf.id, c.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)
    wr.add_dependency(wf.id, d.id, c.id)
    wr.add_dependency(wf.id, e.id, d.id)

    wr.start(wf.id)
    _complete_task(wr, tr, a.id)
    _complete_task(wr, tr, b.id)
    assert c.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, c.id)
    assert d.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, d.id)
    assert e.id in wr.get_ready_tasks(wf.id)

    _complete_task(wr, tr, e.id)
    assert wr.progress(wf.id) == 100.0
    print(f"[PASS] multi_level_merge                  | [A,B]->C->D->E: multi-layer merge")


# ==================================================================
# 44. DAG — get_blocked_tasks com DAG complexo
# ==================================================================

def scenario_blocked_complex() -> None:
    """get_blocked_tasks on complex DAG returns correctly."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="BlockedComplex")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)

    wr.start(wf.id)
    blocked = wr.get_blocked_tasks(wf.id)
    assert b.id in blocked and c.id in blocked
    assert a.id not in blocked

    _complete_task(wr, tr, a.id)
    assert len(wr.get_blocked_tasks(wf.id)) == 0

    _complete_task(wr, tr, b.id)
    _complete_task(wr, tr, c.id)
    assert len(wr.get_blocked_tasks(wf.id)) == 0
    print(f"[PASS] blocked_complex                    | blocked count correct after exec")


# ==================================================================
# 45. DAG — workflow registrado duas vezes inicializa DAG
# ==================================================================

def scenario_register_initializes_dag() -> None:
    """register_workflow initializes DAG data structures."""
    wr, _, _, _, _ = _setup()
    wf = Workflow(name="InitCheck")
    wr.register_workflow(wf)

    assert wf.id in wr._dag_dependencies
    assert wf.id in wr._dag_dependents
    assert wr._dag_dependencies[wf.id] == {}
    assert wr._dag_dependents[wf.id] == {}
    print(f"[PASS] register_initializes_dag           | DAG dicts created on register")


# ==================================================================
# 46. DAG — progresso parcial com DAG
# ==================================================================

def scenario_dag_partial_progress() -> None:
    """Partial progress works during DAG execution."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="PartialProg")
    wr.register_workflow(wf)
    tasks = [_make_task(f"T{i}") for i in range(4)]
    _register_tasks(wr, tr, wf.id, *tasks)

    for i in range(1, 4):
        wr.add_dependency(wf.id, tasks[i].id, tasks[i - 1].id)

    wr.start(wf.id)
    _complete_task(wr, tr, tasks[0].id)
    assert wr.progress(wf.id) == 25.0

    _complete_task(wr, tr, tasks[1].id)
    assert wr.progress(wf.id) == 50.0

    _complete_task(wr, tr, tasks[2].id)
    assert wr.progress(wf.id) == 75.0
    print(f"[PASS] dag_partial_progress               | progress=25->50->75%")


# ==================================================================
# 47. DAG — get_dependents with multiple
# ==================================================================

def scenario_get_dependents_multiple() -> None:
    """get_dependents returns all successors even for complex DAG."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="DepMulti")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, b.id)

    deps_a = wr.get_dependents(wf.id, a.id)
    assert b.id in deps_a
    assert c.id not in deps_a  # c depends on B, not directly on A

    deps_b = wr.get_dependents(wf.id, b.id)
    assert c.id in deps_b
    print(f"[PASS] get_dependents_multiple            | A->[B], B->[C]: direct only")


# ==================================================================
# 48. DAG — self-dependency also via add_dependencies batch
# ==================================================================

def scenario_self_dependency_batch() -> None:
    """Self-dependency in batch add is rejected."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="SelfDepBatch")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    try:
        wr.add_dependencies(wf.id, a.id, [a.id])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot depend on itself" in str(e).lower()
    print(f"[PASS] self_dependency_batch              | A->A via batch rejected")


# ==================================================================
# 49. DAG — empty workflow has_dag=False
# ==================================================================

def scenario_empty_has_dag() -> None:
    """Empty workflow has has_dag=False."""
    wr, _, _, _, _ = _setup()
    wf = Workflow(name="EmptyHasDAG")
    wr.register_workflow(wf)
    assert wr.has_dag(wf.id) is False
    print(f"[PASS] empty_has_dag                      | empty workflow: has_dag=False")


# ==================================================================
# 50. DAG — remove_dependency no-op for non-existent edge
# ==================================================================

def scenario_remove_nonexistent() -> None:
    """remove_dependency is a no-op for non-existent edge."""
    wr, _, _, _, _ = _setup()
    wf = Workflow(name="RemoveNonex")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a) if 'tr' in dir() else None

    # Just verify it doesn't crash
    fake = uuid4()
    wr.remove_dependency(wf.id, a.id if 'a' in dir() else uuid4(), fake)
    print(f"[PASS] remove_nonexistent                 | no-op for non-existent edge")


# Need tr in remove_nonexistent scope
def scenario_remove_nonexistent_ok() -> None:
    """remove_dependency is no-op for non-existent edge (with task)."""
    wr, _, _, tr, _ = _setup()
    wf = Workflow(name="RemoveNonex2")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)

    wr.remove_dependency(wf.id, a.id, uuid4())
    assert wr.validate_dag(wf.id) is True
    assert wr.has_dag(wf.id) is False
    print(f"[PASS] remove_nonexistent_ok              | no-op, no crash")


# ==================================================================
# Main
# ==================================================================

def main() -> None:
    print("=" * 62)
    print("Workflow Runtime DAG Extension Demo")
    print("=" * 62)
    print()

    scenario_linear_workflow()
    scenario_branching_simple()
    scenario_branching_multiple()
    scenario_merge_two_predecessors()
    scenario_parallel_then_merge()
    scenario_complex_dag()
    scenario_cycle_detection()
    scenario_self_dependency()
    scenario_dependency_nonexistent()
    scenario_multiple_predecessors_query()
    scenario_multiple_successors_query()
    scenario_has_dag()
    scenario_validate_dag_valid()
    scenario_validate_dag_invalid()
    scenario_validate_dependency()
    scenario_ready_tasks_initially()
    scenario_blocked_tasks()
    scenario_dag_progress()
    scenario_remove_dependency()
    scenario_add_dependencies_batch()
    scenario_add_dependencies_batch_cycle()
    scenario_determinism_dag()
    scenario_all_independent()
    scenario_long_chain()
    scenario_diamond_dag()
    scenario_dag_blocked_no_premature_complete()
    scenario_foundation_integration()
    scenario_empty_workflow()
    scenario_single_task_dag()
    scenario_ready_order_deterministic()
    scenario_two_independent_tasks()
    scenario_next_task_dag()
    scenario_progress_zero()
    scenario_validate_linear_dag()
    scenario_add_task_initializes_dag()
    scenario_fan_in_multiple()
    scenario_complex_dag_8tasks()
    scenario_backward_compat_snapshot()
    scenario_backward_compat_events()
    scenario_backward_compat_foundation()
    scenario_two_roots()
    scenario_dag_next_task_determinism()
    scenario_multi_level_merge()
    scenario_blocked_complex()
    scenario_register_initializes_dag()
    scenario_dag_partial_progress()
    scenario_get_dependents_multiple()
    scenario_self_dependency_batch()
    scenario_empty_has_dag()
    scenario_remove_nonexistent_ok()

    print()
    print("=" * 62)
    print(f"All 50 Workflow DAG scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
