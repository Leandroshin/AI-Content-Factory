# Engineering Blueprint — AI Execution Runtime

## Purpose

This document is the engineering blueprint for the `AI Execution Runtime` of the AI Company. It defines the architecture of the execution layer responsible for bridging the gap between a decision and its outcome — transforming an approved task assignment into a completed result, updated knowledge, and evolved skills.

The AI Execution Runtime is the **operational heart** of the company. It is where the decision to assign a task becomes the reality of a finished deliverable. It coordinates the Decision Engine, Policy Engine, LLM Gateway, Result Runtime, Knowledge Runtime, and Skill Runtime into a single, traceable, and resilient execution pipeline.

This blueprint translates the conceptual flow described in [EXECUTION_FLOW_ARCHITECTURE.md](file:///c:/Users/Shin/Documents/Novo_projeto_Ai_Content_Factory/EXECUTION_FLOW_ARCHITECTURE.md) into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

The AI Execution Runtime does **not** replace Employees. It **orchestrates** the environment in which Employees execute. Employees still perform the work — the Execution Runtime ensures they have the right context, the right tools, the right policies, and the right communication channels to complete it.

---

## 1. Scope and Boundaries

### In Scope (What Belongs to the AI Execution Runtime)

- **Execution Orchestration**: Managing the lifecycle of a single task execution from assignment to completion.
- **Context Assembly**: Gathering task metadata, employee profile, department context, skill requirements, and policy constraints into a unified execution context.
- **Prompt Preparation**: Translating task requirements and context into structured prompts using the Prompt System.
- **Input Validation**: Ensuring the assembled execution context is complete, consistent, and valid before dispatching to the LLM Gateway.
- **Output Validation**: Ensuring the LLM response conforms to expected format, schema, and quality criteria.
- **Retry and Recovery**: Handling transient failures, rate limits, and partial completions with configurable retry policies.
- **Failure Handling**: Classifying failures (transient vs. permanent), executing fallback strategies, and ensuring the task reaches a terminal state (COMPLETED, FAILED, or BLOCKED).
- **Result Production**: Transforming the validated LLM response into a structured Result, publishing it to the Result Runtime, and propagating it to Knowledge and Skills.
- **Execution Metrics**: Collecting timing, token usage, cost, and outcome data for each execution.
- **Audit Trail**: Recording every step of the execution pipeline for traceability and debugging.

### Out of Scope (What Does NOT Belong to the AI Execution Runtime)

- **Decision Making**: The Execution Runtime does not choose which employee gets a task or which department owns it. This belongs to the Decision Engine.
- **Policy Evaluation**: The Execution Runtime does not check whether an action is allowed. This belongs to the Policy Engine.
- **Provider Communication**: The Execution Runtime does not call LLM providers directly. This belongs to the LLM Gateway.
- **State Mutation**: The Execution Runtime does not directly update employee state, task state, or workflow state. It requests transitions through the appropriate runtimes.
- **Prompt Template Authoring**: The Execution Runtime uses prompt templates but does not create or maintain them.
- **Skill Definition**: The Execution Runtime triggers skill evolution but does not define what skills are or how they are categorized.

---

## 2. Separation of Concerns

Execution is split into four distinct layers that mirror the company's architectural stack:

```text
┌─────────────────────────────────────────────────────────────┐
│                 Strategic Layer                             │
│  (Orchestrator / Decision Engine / Policy Engine)            │
│  Decides: who, what, when, whether                          │
└───────────────────────────┬─────────────────────────────────┘
                            │ Approved Task Assignment
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Execution Runtime Layer                        │
│  (ExecutionRuntime, ExecutionContext, ExecutionPlan)         │
│  Orchestrates: preparation → prompt → gateway → result      │
└───────────────────────────┬─────────────────────────────────┘
                            │ Dispatches to
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Communication Layer                            │
│  (LLM Gateway / Prompt System / Response Parser)             │
│  Handles: provider routing, prompt dispatch, response        │
└───────────────────────────┬─────────────────────────────────┘
                            │ Returns Result
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Persistence & Learning Layer                   │
│  (Result Runtime / Knowledge Runtime / Skill Runtime)        │
│  Persists: results, knowledge, evolved skills               │
└─────────────────────────────────────────────────────────────┘
```

### Strategic Layer
- **Responsibility**: Decides which task goes to which employee, under which policies.
- **Components**: Orchestrator, Decision Engine, Policy Engine.
- **Output**: An approved decision with a chosen employee, task, and department.

### Execution Runtime Layer
- **Responsibility**: Transforms the approved decision into a completed execution.
- **Components**: ExecutionRuntime, ExecutionContext, ExecutionPlan, PromptPreparation, InputValidator, OutputValidator, RetryController, FailureHandler.
- **Output**: A completed Result with attached metrics and trace.

### Communication Layer
- **Responsibility**: Handles all LLM provider communication.
- **Components**: LLM Gateway, PromptBuilder, ResponseParser.
- **Output**: A normalized response from the chosen provider.

### Persistence & Learning Layer
- **Responsibility**: Stores results, extracts knowledge, evolves skills.
- **Components**: Result Runtime, Knowledge Runtime, Skill Runtime.
- **Output**: Persisted artifacts that improve future executions.

---

## 3. Relationships and Interactions

The AI Execution Runtime is the central coordinator between all other layers:

```text
 Task (ASSIGNED)
        │
        ▼
 ExecutionRuntime.execute(execution_context)
        │
  ┌─────┼────────────────────────────────────────────┐
  │     │                                            │
  │     ▼                                            │
  │  ContextAssembler ───► Decision Context          │
  │     │                 Task Snapshot              │
  │     │                 Employee Snapshot           │
  │     │                 Department Snapshot         │
  │     │                 Skill Snapshots             │
  │     │                                            │
  │     ▼                                            │
  │  InputValidator ───► Validates context            │
  │     │                                            │
  │     ▼                                            │
  │  PromptPreparation ──► PromptBuilder             │
  │     │                   (PromptGateway)           │
  │     ▼                                            │
  │  LLM Gateway ───────► ProviderAdapter            │
  │     │                   (OpenAI / Gemini / etc.)  │
  │     ▼                                            │
  │  ResponseParser ────► Normalized response        │
  │     │                                            │
  │     ▼                                            │
  │  OutputValidator ───► Schema + quality check     │
  │     │                                            │
  │     ▼                                            │
  │  ResultRuntime ─────► create_result()            │
  │     │                 approve_result()            │
  │     ▼                                            │
  │  KnowledgeRuntime ──► create_from_result()       │
  │     │                 validate()                  │
  │     │                 publish()                   │
  │     ▼                                            │
  │  SkillRuntime ──────► create_from_knowledge()    │
  │                       associate_employee()        │
  │                       evolve()                    │
  │                                                    │
  └─────┬────────────────────────────────────────────┘
        │
        ▼
 Task (COMPLETED / FAILED)
```

- **Task Runtime**: Provides the task snapshot. Receives state transitions (ASSIGNED → RUNNING → COMPLETED/FAILED).
- **Employee Runtime**: Provides the employee snapshot. Employee state is set to BUSY during execution and IDLE on completion.
- **Decision Engine**: Provides the decision that selected the employee for this task. May be re-queried if retry requires reassignment.
- **Policy Engine**: Validates each step. May be queried before LLM dispatch.
- **LLM Gateway**: The sole communication channel for all LLM calls during execution.
- **Result Runtime**: Receives the validated execution output and creates a result entry.
- **Knowledge Runtime**: Receives the result and extracts knowledge from it.
- **Skill Runtime**: Receives knowledge and evolves employee skills.
- **EventBus**: Carries execution events for observability and coordination.
- **ObservabilityProjector**: Consumes execution events for dashboards and traces.

---

## 4. Component Breakdown

```text
                        ExecutionContext
                              │
                              ▼
                    ┌─────────┴─────────┐
                    │  ExecutionRuntime  │
                    │  (Orchestrator)    │
                    └──┬─────────────┬───┘
                       │             │
              ┌────────┴───┐  ┌──────┴──────┐
              │ Execution  │  │ Execution   │
              │ Plan       │  │ Metrics     │
              └────────┬───┘  └──────┬──────┘
                       │             │
                       ▼             │
              ┌────────────────┐     │
              │ Context        │     │
              │ Assembler      │     │
              └───────┬────────┘     │
                      │              │
              ┌───────┴────────┐     │
              │ InputValidator │     │
              └───────┬────────┘     │
                      │              │
              ┌───────┴────────┐     │
              │ Prompt         │     │
              │ Preparation    │     │
              └───────┬────────┘     │
                      │              │
                      ▼              │
              ┌────────────────┐     │
              │ LLM Gateway    │     │
              └───────┬────────┘     │
                      │              │
              ┌───────┴────────┐     │
              │ OutputValidator│     │
              └──┬─────────┬───┘     │
                 │         │        │
           ┌─────┴──┐  ┌──┴──────┐ │
           │ Retry  │  │Failure  │ │
           │Control │  │Handler  │ │
           └───┬────┘  └───┬─────┘ │
               │           │       │
               └─────┬─────┘       │
                     ▼             │
              ┌──────────────┐     │
              │ Execution    │     │
              │ Result       │     │
              └──────┬───────┘     │
                     │             │
                     ▼             │
              ResultRuntime ──── KnowledgeRuntime ──── SkillRuntime
```

### 4.1 ExecutionRuntime
- **Purpose**: Central orchestrator for a single task execution. Receives an `ExecutionContext`, executes the full pipeline, handles failures, and returns an `ExecutionResult`.
- **Execution**: Stateful per execution. Created when a task transitions to RUNNING. Destroyed when the task reaches COMPLETED, FAILED, or CANCELLED. For each execution, the runtime:
  1. Calls `ContextAssembler` to build the full context.
  2. Calls `InputValidator` to validate the context.
  3. Calls `PromptPreparation` to build the prompt.
  4. Calls `LLMGateway.ask()` to dispatch the prompt.
  5. Calls `OutputValidator` to validate the response.
  6. On validation failure: calls `RetryController` for retry or `FailureHandler` for permanent failure.
  7. On success: produces an `ExecutionResult` and propagates it to Result, Knowledge, and Skill runtimes.
- **State**: Each execution has a lifecycle: `PREPARING → VALIDATING_INPUT → PROMPTING → AWAITING_LLM → VALIDATING_OUTPUT → PERSISTING → COMPLETED | FAILED`.

### 4.2 ExecutionContext
- **Purpose**: Immutable input containing everything the Execution Runtime needs to process a single task execution.
- **Structure** (conceptual):
  - `execution_id`: UUID uniquely identifying this execution.
  - `task_snapshot`: Snapshot of the task being executed.
  - `employee_snapshot`: Snapshot of the executing employee.
  - `department_snapshot`: Snapshot of the owning department.
  - `skill_snapshots`: List of relevant skill snapshots.
  - `decision_result`: The `DecisionResult` that approved this assignment.
  - `active_policies`: Policies that apply to this execution.
  - `prompt_template_id`: Identifier of the prompt template to use.
  - `prompt_variables`: Variables for prompt template rendering.
  - `output_schema`: Expected output format and schema.
  - `max_retries`: Maximum retry attempts.
  - `max_duration_ms`: Maximum wall-clock time for the execution.
  - `metadata`: Tags, workflow_id, orchestration_id for tracing.

### 4.3 ExecutionPlan
- **Purpose**: Defines the ordered sequence of steps for an execution. Each step has a type, handler, and success/failure transitions.
- **Structure** (conceptual):
  - `steps`: Ordered list of step definitions.
  - `current_step`: Index of the currently executing step.
  - `transitions`: Mapping of step + outcome → next step.
  - `fallback_plan`: Alternative plan to use if the primary plan fails.
- **Execution**: Stateless configuration. The `ExecutionRuntime` consumes the plan to know what to do next. Plans may be defined globally or per task type.

### 4.4 ContextAssembler
- **Purpose**: Gathers all snapshots required for execution into a single, validated `ExecutionContext`. Resolves task requirements against employee skills, department context, and active policies.
- **Execution**: Stateless. Receives raw snapshots and returns a complete `ExecutionContext`. Validates that all required data is present (task is not null, employee is not null, etc.).

### 4.5 InputValidator
- **Purpose**: Validates the assembled `ExecutionContext` before any LLM call is made. Ensures the context is complete, consistent, and ready for prompt construction.
- **Validation rules**:
  - Task snapshot is present and in a valid state.
  - Employee snapshot is present and the employee is IDLE.
  - Prompt template exists in the registry.
  - All required prompt variables are present and correctly typed.
  - Output schema is valid JSON Schema (if applicable).
  - Required capabilities are satisfied by available skills.
  - Active policies do not block execution.

### 4.6 PromptPreparation
- **Purpose**: Translates the `ExecutionContext` into a `RequestContext` for the LLM Gateway. Selects the correct prompt template, renders variables, and configures output format.
- **Execution**: Stateless. Delegates template loading and rendering to `PromptBuilder`. Returns a fully formed `RequestContext` ready for dispatch.

### 4.7 OutputValidator
- **Purpose**: Validates the LLM Gateway's `ResponseContext` against the expected output schema and quality criteria before the result is persisted.
- **Validation rules**:
  - Response is not empty.
  - Response conforms to the expected format (JSON, Markdown, text).
  - Response validates against the output JSON Schema (if applicable).
  - Response meets minimum quality thresholds (configurable per task type).
  - Response does not contain prohibited content (PII, internal data leakage).
- **Execution**: Stateless. Returns a validation result with pass/fail status and detailed reasons. On failure, the `RetryController` decides whether to retry or escalate.

### 4.8 ExecutionResult
- **Purpose**: Immutable output of a single execution. Contains the validated LLM response, execution metadata, and trace information.
- **Structure** (conceptual):
  - `execution_id`: UUID of the execution.
  - `task_id`: UUID of the executed task.
  - `employee_id`: UUID of the executing employee.
  - `success`: Whether the execution completed successfully.
  - `response_content`: The validated LLM response content.
  - `response_format`: Format of the response (json, markdown, text).
  - `provider`: Provider and model used.
  - `tokens`: Token usage (input, output, total).
  - `cost`: Total cost of the execution.
  - `duration_ms`: Wall-clock duration.
  - `retry_attempts`: Number of retry attempts.
  - `failure_reason`: If failed, the reason for failure.
  - `trace`: Ordered list of execution stages with timing.
  - `metrics`: ExecutionMetrics object.

### 4.9 RetryController
- **Purpose**: Determines whether a failed step should be retried, and if so, with what delay and configuration.
- **Execution**: Stateless per invocation. Consumes a `RetryPolicy` that defines:
  - `max_retries`: Maximum number of retry attempts.
  - `base_delay_ms`: Initial delay before first retry.
  - `backoff_multiplier`: Exponential backoff factor (e.g., 2.0).
  - `max_delay_ms`: Maximum delay between retries.
  - `retryable_errors`: List of error codes that warrant a retry.
  - `non_retryable_errors`: List of error codes that trigger immediate failure.
- **Decision logic**:
  1. If error is non-retryable → return permanent failure.
  2. If retry count exceeded → return permanent failure.
  3. If max duration exceeded → return permanent failure.
  4. Otherwise → compute delay, return retry with delay.

### 4.10 FailureHandler
- **Purpose**: Handles permanent execution failures. Ensures the task reaches a terminal FAILED or BLOCKED state with a complete explanation.
- **Execution**: Stateless. Receives the execution context, the error, and the retry history. Returns a structured failure `ExecutionResult` with:
  - `failure_reason`: Human-readable explanation.
  - `failure_code`: Machine-readable error code.
  - `failure_stage`: Which pipeline stage failed.
  - `retry_history`: List of all retry attempts and their outcomes.
  - `partial_result`: Any partial output produced before failure (if applicable).

### 4.11 ExecutionMetrics
- **Purpose**: Collects and structures performance and cost data for a single execution.
- **Structure** (conceptual):
  - `duration_ms`: Total execution duration.
  - `context_assembly_ms`: Time spent in ContextAssembler.
  - `input_validation_ms`: Time spent in InputValidator.
  - `prompt_preparation_ms`: Time spent in PromptPreparation.
  - `llm_dispatch_ms`: Time spent waiting for the LLM Gateway response.
  - `output_validation_ms`: Time spent in OutputValidator.
  - `persistence_ms`: Time spent persisting to Result/Knowledge/Skill runtimes.
  - `retry_count`: Number of retries performed.
  - `total_retry_delay_ms`: Total time spent waiting between retries.
  - `input_tokens`: Input token count.
  - `output_tokens`: Output token count.
  - `total_tokens`: Total token count.
  - `cost`: Total monetary cost of the execution.
  - `provider`: Provider and model used.

---

## 5. Execution Lifecycle

Every execution follows a strict lifecycle. Each state maps to a stage in the pipeline.

```text
                  ┌──────────────┐
                  │  ASSIGNED    │  (from Decision Engine)
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  PREPARING   │  ContextAssembler + InputValidator
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  PROMPTING   │  PromptPreparation
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ AWAITING_LLM │  LLM Gateway dispatch
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ VALIDATING   │  OutputValidator
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              │ Pass     │ Fail     │
              ▼          ▼          │
       ┌──────────┐ ┌──────────┐    │
       │PERSISTING│ │  RETRY   │◄───┘
       └────┬─────┘ │  or      │
            │       │  FAIL    │
            │       └──────────┘
            │
      ┌─────▼──────┐
      │ COMPLETED  │
      └─────┬──────┘
            │
      ┌─────▼──────┐
      │ PROPAGATE  │  → Result → Knowledge → Skill
      └────────────┘
```

### State Descriptions

| State | Description | Transitions To |
|-------|-------------|----------------|
| `ASSIGNED` | Task is assigned to an employee. Execution not yet started. | `PREPARING` |
| `PREPARING` | ContextAssembler gathers snapshots. InputValidator validates. | `PROMPTING`, `FAILED` |
| `PROMPTING` | PromptPreparation builds the prompt. | `AWAITING_LLM`, `FAILED` |
| `AWAITING_LLM` | LLM Gateway is processing the request. | `VALIDATING`, `FAILED` |
| `VALIDATING` | OutputValidator checks the response. | `PERSISTING`, `RETRYING`, `FAILED` |
| `RETRYING` | RetryController initiates a retry with backoff. | `PROMPTING`, `FAILED` |
| `PERSISTING` | ExecutionResult is persisted to Result Runtime. | `COMPLETED`, `FAILED` |
| `COMPLETED` | Execution succeeded. Results are propagated. | `PROPAGATING` |
| `PROPAGATING` | Result → Knowledge → Skill runtimes are updated. | Terminal |
| `FAILED` | Execution failed permanently. Task is marked FAILED. | Terminal |

---

## 6. Error Handling

Errors are classified into categories. Each category determines whether retry is possible and which handler is invoked.

### Error Classification

| Category | Examples | Retryable? | Handler |
|----------|----------|------------|---------|
| **Transient** | Rate limit exceeded, provider timeout, network error, temporary provider outage | Yes | RetryController with backoff |
| **Permanent** | Invalid API key, unsupported model, bad request schema, authentication failure | No | FailureHandler → task FAILED |
| **Business** | Output validation failed, insufficient quality, missing required fields | Configurable | RetryController or FailureHandler |
| **System** | Internal error, snapshot missing, runtime unavailable | No (recover) | FailureHandler → task BLOCKED for manual intervention |

### Error Propagation

```text
 LLM Gateway Error
        │
        ▼
 OutputValidator catches
        │
        ├── Transient ──► RetryController
        │                      │
        │                      ├── Retry ──► Prompting (with backoff)
        │                      │
        │                      └── Max retries exceeded ──► FailureHandler
        │
        └── Permanent ──► FailureHandler
                               │
                               ▼
                       ExecutionResult (success=False)
                               │
                               ▼
                       TaskRuntime.transition(FAILED)
```

### Partial Results

If an execution produces a partial result before failing (e.g., the LLM responded but validation failed), the partial content is preserved in `ExecutionResult.partial_result` for debugging and potential manual salvage.

---

## 7. Retry Strategies

### 7.1 Fixed Interval
```text
Retry 1: wait 1s
Retry 2: wait 1s
Retry 3: wait 1s
```
Use case: Rate limit with known reset interval.

### 7.2 Exponential Backoff
```text
Retry 1: wait 1s
Retry 2: wait 2s
Retry 3: wait 4s
Retry 4: wait 8s
```
Use case: Transient server errors, temporary outages.

### 7.3 Exponential Backoff with Jitter
```text
Retry 1: wait 1.2s (1s + random 0-0.4s)
Retry 2: wait 2.3s (2s + random 0-0.6s)
Retry 3: wait 4.1s (4s + random 0-1.2s)
```
Use case: Preventing thundering herd on shared provider rate limits.

### 7.4 Fallback Retry
```text
Primary provider fails → Fallback to secondary provider
Retry 1: wait 1s (secondary)
Retry 2: wait 2s (secondary)
Retry 3: Fallback to tertiary provider
```
Use case: Provider outage, not just rate limiting.

### 7.5 Retry Budget

Each execution has a `max_duration_ms` and `max_retries`. The `RetryController` computes the total delay budget and stops retrying if the budget is exhausted, even if `max_retries` has not been reached.

```text
total_delay = sum of all retry delays
if total_delay + elapsed > max_duration_ms → stop retrying, fail permanently
```

---

## 8. Idempotency

The AI Execution Runtime must ensure that the same execution is never processed twice, even in the presence of retries, timeouts, or system restarts.

### idempotency Key

Each execution has a unique `execution_id` (UUID v4) generated at the moment the task transitions to RUNNING. This key is:
- Passed through the entire pipeline.
- Included in the LLM Gateway request (as a header or field, if supported).
- Used to deduplicate Result, Knowledge, and Skill runtime entries.

### Deduplication Strategy

```text
Before creating a Result:
  1. Check if result with execution_id already exists.
  2. If yes → return existing result (idempotent).
  3. If no → create new result.
```

### At-Least-Once Delivery

The pipeline guarantees at-least-once delivery:
- If the LLM Gateway responds but the OutputValidator crashes before persisting, the retry re-dispatches to the Gateway.
- The Gateway must handle duplicate requests gracefully (idempotency on the provider side is provider-dependent; the Gateway logs duplicates but cannot prevent them).
- The Result/Knowledge/Skill runtimes must handle duplicate creation requests idempotently (check existence by `execution_id`).

### Exactly-Once within the Runtime

Within a single runtime instance, execution is exactly-once:
- The `ExecutionRuntime` locks the execution_id on first processing.
- Concurrent processing of the same execution_id is prevented.
- If the runtime restarts mid-execution, the task returns to ASSIGNED state and a new execution_id is generated.

---

## 9. Observability

The Execution Runtime emits structured events at each stage of the pipeline. These events are published to the EventBus and consumed by projectors for dashboards, metrics, and alerting.

### Events

| Event | Stage | Payload |
|-------|-------|---------|
| `ExecutionStarted` | PREPARING | `execution_id`, `task_id`, `employee_id`, `department_id`, `timestamp` |
| `ContextAssembled` | PREPARING | `execution_id`, `snapshot_summary`, `duration_ms` |
| `InputValidated` | PREPARING | `execution_id`, `valid`, `validation_details` |
| `PromptPrepared` | PROMPTING | `execution_id`, `template_id`, `estimated_tokens` |
| `LLMRequestStarted` | AWAITING_LLM | `execution_id`, `provider`, `model`, `estimated_cost` |
| `LLMRequestCompleted` | AWAITING_LLM | `execution_id`, `provider`, `model`, `tokens`, `cost`, `duration_ms` |
| `OutputValidated` | VALIDATING | `execution_id`, `valid`, `schema_compliant`, `quality_score` |
| `RetryAttempted` | RETRYING | `execution_id`, `attempt`, `delay_ms`, `error_code`, `error_message` |
| `FallbackExecuted` | RETRYING | `execution_id`, `from_provider`, `to_provider`, `reason` |
| `ResultPersisted` | PERSISTING | `execution_id`, `result_id`, `duration_ms` |
| `KnowledgeCreated` | PROPAGATING | `execution_id`, `knowledge_id` |
| `SkillEvolved` | PROPAGATING | `execution_id`, `skill_id`, `new_level` |
| `ExecutionCompleted` | COMPLETED | `execution_id`, `duration_ms`, `total_cost`, `total_tokens` |
| `ExecutionFailed` | FAILED | `execution_id`, `failure_stage`, `failure_code`, `failure_reason`, `retry_count` |

### Observability Consumption

An `ExecutionProjector` (or extension of the existing `ObservabilityProjector`) subscribes to these events and maintains:
- **Execution dashboard**: Active executions, completion rate, failure rate, average duration.
- **Provider dashboard**: Per-provider latency, error rate, cost, token usage.
- **Employee dashboard**: Per-employee execution count, success rate, average cost.
- **Task type dashboard**: Per-type execution metrics.
- **Failure analysis**: Most common failure codes, stages, and retry patterns.

---

## 10. Metrics

Beyond events, the Execution Runtime maintains numeric counters and gauges for performance monitoring.

### Counters

- `executions_started_total`: Total executions initiated.
- `executions_completed_total`: Total successful completions.
- `executions_failed_total`: Total permanent failures.
- `executions_retried_total`: Total retry attempts.
- `executions_fallback_total`: Total fallback executions.
- `tokens_input_total`: Total input tokens across all executions.
- `tokens_output_total`: Total output tokens across all executions.
- `cost_total`: Total monetary cost across all executions.

### Histograms

- `execution_duration_ms`: Distribution of total execution duration.
- `llm_dispatch_duration_ms`: Distribution of LLM Gateway response time.
- `retry_delay_ms`: Distribution of retry delays.

### Gauges

- `active_executions`: Currently executing tasks.
- `executions_last_minute`: Execution rate.

### Metric Dimensions

All metrics can be sliced by:
- `provider`: Which LLM provider served the request.
- `model`: Which model was used.
- `employee_id`: Which employee executed.
- `department_id`: Which department owns the task.
- `task_type`: The type of task executed.
- `template_id`: Which prompt template was used.
- `success`: Whether the execution succeeded.
- `retry`: Whether a retry occurred.

---

## 11. Audit Trail

Every execution produces an immutable audit log that records:

```text
execution_id: uuid
task_id: uuid
employee_id: uuid
department_id: uuid
decision_id: uuid
policy_results: list of PolicyResult
timeline:
  - timestamp: T1, stage: PREPARING, detail: "Context assembled"
  - timestamp: T2, stage: PROMPTING, detail: "Template 'code_review@1.2.0' rendered"
  - timestamp: T3, stage: AWAITING_LLM, detail: "Dispatched to openai/gpt-4o"
  - timestamp: T4, stage: VALIDATING, detail: "Output validated against schema v3"
  - timestamp: T5, stage: PERSISTING, detail: "Result abc-123 persisted"
  - timestamp: T6, stage: PROPAGATING, detail: "Skill xyz-789 evolved to INTERMEDIATE"
outcome: COMPLETED
final_duration_ms: 4523
final_cost_usd: 0.0023
```

The audit trail is not stored by the Execution Runtime. It is assembled from events by the `ObservabilityProjector` and persisted by the Knowledge Runtime for future querying.

---

## 12. Security

### Execution Isolation

Each execution is isolated from every other execution:
- No shared mutable state between concurrent executions.
- No cross-execution data leakage.
- Each execution has its own `ExecutionContext` and `ExecutionResult`.
- Different employees' executions never share conversation history.

### Prompt Sanitization

Before the prompt reaches the LLM Gateway, the `PromptPreparation` component may sanitize:
- Remove internal employee names and identifiers.
- Strip internal URLs and IP addresses.
- Mask PII (email, phone, government IDs).
- Replace department names with generic identifiers.

Sanitization is controlled by a policy flag and is disabled by default for internal providers (Ollama) and enabled by default for external providers.

### Credential Isolation

The Execution Runtime never handles provider credentials directly. All credentials are managed by the LLM Gateway's `ProviderAdapter` layer. The Execution Runtime only specifies which provider to use (or delegates selection to the `ModelSelector`).

### Access Control

The Execution Runtime must verify that:
- The employee is authorized to execute the assigned task (checked by Policy Engine before execution starts).
- The employee is authorized to use the selected provider (checked by Policy Engine).
- The department is authorized to access the selected prompt templates.

---

## 13. Integration with Existing Blueprints

### ENGINEERING_BLUEPRINT_DECISION_ENGINE.md

The Decision Engine produces the decision that triggers execution. The `DecisionResult` is consumed by the `ExecutionContext`:
- `DecisionResult.chosen_candidate_id` → `ExecutionContext.employee_snapshot`.
- `DecisionResult.decision_code` → logged in audit trail.
- `DecisionResult.trace` → attached to execution metadata.

The Decision Engine is queried before execution starts. It may also be re-queried during retry if the execution requires reassignment (e.g., original employee is no longer available).

### ENGINEERING_BLUEPRINT_POLICY_ENGINE.md

The Policy Engine is queried at multiple points during execution:
1. **Before execution**: Is the employee authorized to execute this task?
2. **Before LLM dispatch**: Is the employee authorized to use the selected provider?
3. **Before result persistence**: Is the result within policy boundaries (size, content, cost)?
4. **Before knowledge publication**: Does the extracted knowledge comply with governance policies?

Policy violations during execution trigger the `FailureHandler` with a `POLICY_DENIED` failure code.

### ENGINEERING_BLUEPRINT_LLM_GATEWAY.md

The LLM Gateway is the sole communication channel during execution:
- `PromptPreparation` builds `RequestContext` from the `ExecutionContext`.
- `LLMGateway.ask()` dispatches the request.
- `ResponseParser` returns `ResponseContext` to the `OutputValidator`.

The Execution Runtime never calls a provider directly. It always goes through the Gateway.

### ENGINEERING_BLUEPRINT_EMPLOYEE.md

The Employee blueprint describes the employee's role in the company. The AI Execution Runtime is the mechanism that enables an Employee to execute tasks:
- The Employee provides its skills, which the `ContextAssembler` uses to determine prompt templates and expected output.
- The Employee's `state` transitions to BUSY when execution starts and IDLE when it completes.
- The Employee's skills evolve after execution via the Skill Runtime.

### EXECUTION_FLOW_ARCHITECTURE.md

The conceptual flow described in `EXECUTION_FLOW_ARCHITECTURE.md` is the high-level view. This blueprint (`AI_EXECUTION`) is the technical specification of steps 5 through 13 (Execution Context Preparation through Employee Skills Update).

### ARCHITECTURE.md

This blueprint adds the `AI Execution Runtime` as a new architectural component. It should be indexed under section 8 (Blueprints de Engenharia), within a new subsection "8.6 AI Execution Runtime".

### COMPANY_RUNTIME_ARCHITECTURE.md

The Company Runtime maintains the operational state that the Execution Runtime reads and transitions:
- Task state: ASSIGNED → RUNNING → COMPLETED / FAILED.
- Employee state: IDLE → BUSY → IDLE.
- Department state: IDLE → WORKING → IDLE.

### MESSAGE_SYSTEM_ARCHITECTURE.md

The Message System may carry execution-related signals:
- Execution completion notifications.
- Execution failure alerts.
- Cost threshold warnings.
- Provider unavailability notifications during execution.

Messages are informational; they never carry execution control logic.

### OBSERVABILITY_ARCHITECTURE.md

The Observability layer consumes all execution events (section 9 of this document). An `ExecutionProjector` maintains:
- Live execution dashboard.
- Historical execution trends.
- Cost and token usage analytics.
- Failure pattern analysis.

---

## 14. Architectural Risks

### 14.1 Execution Runtime as a Single Point of Coordination
- **Risk**: Every execution passes through the Execution Runtime. If it fails, no work gets done.
- **Mitigation**: The Execution Runtime is stateless for orchestration — each execution is independent. Multiple instances can run in parallel. The runtime only reads snapshots and delegates to other components.

### 14.2 Long-Running Executions
- **Risk**: Some LLM calls may take minutes (long prompts, complex reasoning). The Execution Runtime must not block other executions while waiting.
- **Mitigation**: Each execution runs in a lightweight, isolated context. The `max_duration_ms` budget prevents runaway executions. Timeouts are enforced at the LLM Gateway level.

### 14.3 State Drift Between Snapshots and Reality
- **Risk**: The `ExecutionContext` is assembled from snapshots that may be stale by the time execution completes.
- **Mitigation**: Critical checks (employee availability, policy validity) are performed by the Policy Engine immediately before the LLM Gateway call, not only at context assembly time.

### 14.4 Orphaned Executions
- **Risk**: An execution may be interrupted (runtime restart, network partition) and leave the task in RUNNING state with no active processing.
- **Mitigation**: The Task Runtime should implement a heartbeat mechanism. If an execution does not report progress within a configurable window, the task returns to ASSIGNED and a new execution_id is generated.

### 14.5 Cascading Failures
- **Risk**: A failure in one execution (e.g., persistent provider error) may cause retries that consume the retry budget and delay other executions.
- **Mitigation**: Each execution has its own `max_retries` and `max_duration_ms`. Provider-level rate limiting is enforced by the LLM Gateway. Executions do not share retry budgets.

### 14.6 Cost Explosion
- **Risk**: A bug in prompt construction may cause the LLM to produce excessively long responses, driving up cost.
- **Mitigation**: `max_tokens` is set in `RequestContext`. The `CostTracker` computes projected cost before dispatch. If projected cost exceeds budget, the request is rejected at the Gateway level.

---

## 15. Benefits

### 15.1 End-to-End Traceability
Every execution produces a complete audit trail from decision to skill evolution. Any result can be traced back to the task, employee, decision, policies, prompt, and LLM response.

### 15.2 Clear Separation of Concerns
The Execution Runtime is the only component that knows the execution pipeline. The Decision Engine does not know how execution happens. The LLM Gateway does not know why the request was made. The Employee does not know which provider served the request.

### 15.3 Pluggable Execution Strategies
Because the `ExecutionPlan` is a first-class concept, different task types can have different execution strategies: some may require multiple LLM calls, some may skip the LLM entirely, some may require human review before completion.

### 15.4 Resilience
Retry policies, fallback providers, timeouts, and failure classification ensure that transient errors do not result in permanent task failures. The system recovers automatically from most failure modes.

### 15.5 Cost Visibility
Every execution records its cost. This enables per-employee, per-department, per-task-type, and per-provider cost analysis. The `CostTracker` projection before dispatch prevents budget violations.

### 15.6 Deterministic Retry
The `RetryPolicy` is explicit and configurable. Every retry is logged. No silent retries. No infinite retry loops.

### 15.7 Evolution Feedback Loop
Every successful execution feeds back into the company's knowledge and skills. The company improves with each task completed.

---

## 16. Future Roadmap

### Phase 1: Foundation

```
ExecutionContext ─── ExecutionRuntime ─── ExecutionResult
```

- Implement `ExecutionContext` and `ExecutionResult` as frozen dataclasses.
- Implement `ExecutionRuntime` with a linear pipeline (no retry, no fallback).
- Integrate with Task Runtime for state transitions (ASSIGNED → RUNNING → COMPLETED).
- Integrate with LLM Gateway for the single LLM call.

### Phase 2: Validation

```
InputValidator ─── OutputValidator
```

- Implement `InputValidator` with basic completeness checks.
- Implement `OutputValidator` with schema validation.
- Wire validators into the pipeline.
- Add failure classification (transient vs. permanent).

### Phase 3: Resilience

```
RetryController ─── FailureHandler
```

- Implement `RetryController` with configurable `RetryPolicy`.
- Implement `FailureHandler` with structured failure output.
- Add exponential backoff with jitter.
- Add fallback provider support via the LLM Gateway.

### Phase 4: Context and Prompt

```
ContextAssembler ─── PromptPreparation
```

- Implement `ContextAssembler` to gather snapshots from all runtimes.
- Implement `PromptPreparation` with template rendering via `PromptBuilder`.
- Add prompt variable validation.

### Phase 5: Observability

```
Execution Events ─── Metrics ─── Audit Trail
```

- Implement all execution events.
- Implement `ExecutionMetrics` collection.
- Implement audit trail assembly from events.
- Integrate with `ObservabilityProjector`.

### Phase 6: Result → Knowledge → Skill Propagation

```
Result Persistence ─── Knowledge Creation ─── Skill Evolution
```

- Automate the propagation of successful results through the Result, Knowledge, and Skill runtimes.
- Implement idempotent propagation (deduplicate by execution_id).

### Phase 7: Execution Plans

```
ExecutionPlan ─── Multi-step Executions
```

- Implement `ExecutionPlan` for complex, multi-step task types.
- Support conditional branching in plans (if retry → different plan).
- Support parallel execution steps.

### Phase 8: Human-in-the-Loop

```
Manual Review ─── Approval Gates ─── Escalation
```

- Add support for executions that require human review before completion.
- Add approval gates that pause execution until a manual signal is received.
- Add escalation paths for executions that exceed retry budgets.

---

## 17. Validation

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| ExecutionRuntime is stateful per execution, stateless globally | Enables parallel execution without shared state conflicts |
| ContextAssembler gathers snapshots at execution start | Ensures a consistent snapshot of the company state for the duration of execution |
| OutputValidator runs before persistence | Prevents invalid LLM responses from being stored as results |
| RetryController is configurable per task type | Different tasks have different tolerance for latency and failure |
| Failures are classified (transient/permanent/business/system) | Enables appropriate handling strategy for each failure mode |
| Propagation to Knowledge and Skills is automated | Creates a closed feedback loop: every execution improves the company |
| All execution events are published to the EventBus | Provides a single source of truth for observability, without coupling the runtime to any specific projector |

### Technical Justification

The AI Execution Runtime bridges the gap between the company's **decision layer** (who does what) and its **execution layer** (how the work gets done). Without this bridge, each Employee would need to independently orchestrate Decision Engine queries, Policy Engine checks, LLM Gateway calls, Result creation, Knowledge extraction, and Skill evolution. This would duplicate orchestration logic across every Employee implementation.

By centralizing execution orchestration into a dedicated runtime, the company gains:
- **Consistent error handling**: All executions fail the same way.
- **Consistent observability**: All executions emit the same events.
- **Consistent retry**: All executions retry by the same policies.
- **Consistent propagation**: All successful executions feed back into Knowledge and Skills.
- **Testability**: The entire execution pipeline can be tested with mock runtimes and gateways.

### Risks

1. **Over-centralization**: The Execution Runtime becomes a bottleneck if not designed for parallel execution. Mitigation: each execution is fully isolated.
2. **Complex state management**: The lifecycle has 8+ states. Mitigation: states are linear with clear transitions; no branching complexity in v1.
3. **Event volume**: Each execution emits 10+ events. At scale, this may pressure the EventBus. Mitigation: events are small structured payloads; the EventBus is in-memory and fast.
4. **Cascading failures in propagation**: A failure in Knowledge Runtime should not revert the Result. Mitigation: each propagation step is independent; a failure in one does not undo previous steps.

### Future Opportunities

1. **Parallel execution steps**: An `ExecutionPlan` that sends independent sub-tasks to different providers simultaneously and aggregates results.
2. **Adaptive retry**: A `RetryController` that learns from historical retry success rates and adjusts backoff parameters automatically.
3. **Execution simulation**: Replay historical `ExecutionContext` objects through the pipeline to test new prompts, policies, or providers without live execution.
4. **Quality scoring**: An `OutputValidator` that uses a secondary LLM call to score response quality before persisting the result.
5. **Self-healing executions**: If an execution fails due to provider unavailability, the `FailureHandler` may re-queue the task with a different provider preference.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/` (new module) | A new `core/execution/` package containing `runtime.py`, `context.py`, `plan.py`, `validators.py`, `retry.py`, `metrics.py`, `events.py` |
| `core/tasks/runtime.py` | Must expose a `transition(RUNNING)` and `transition(COMPLETED/FAILED)` that the Execution Runtime calls |
| `core/employees/runtime.py` | Execution Runtime sets employee to BUSY on start, IDLE on completion |
| `core/results/runtime.py` | Must handle idempotent creation by `execution_id` |
| `core/knowledge/runtime.py` | Must handle idempotent creation by `execution_id` |
| `core/skills/runtime.py` | Must handle idempotent creation by `execution_id` |
| `core/decision/runtime.py` | Unchanged. Execution Runtime consumes `DecisionResult`, does not modify the engine |
| `core/llm/` (future) | LLM Gateway is called by the Execution Runtime; no changes needed |
| `EventBus` | Unchanged. Execution events are new event types, but the bus remains the same |
| `ObservabilityProjector` | May add an `ExecutionProjector` to consume the new execution events |
| `ARCHITECTURE.md` | Should index this blueprint under a new "8.6 AI Execution Runtime" section |

---

## 18. Architectural Principles

- **Separation of Responsibilities**: The Execution Runtime orchestrates. It does not decide, evaluate policies, or call providers directly.
- **Immutability of Inputs**: ExecutionContext and ExecutionResult are immutable. The runtime never mutates caller data.
- **Fail-Fast with Explanation**: Invalid inputs, policy violations, and permanent errors are detected early and reported with full context.
- **Resilience by Default**: Every execution has retry, timeout, and fallback configured. No execution hangs forever.
- **Observability by Default**: Every execution produces structured events and metrics. No silent failures.
- **Idempotency**: Every execution guarantees at-least-once delivery without duplicate side effects.
- **Closed Feedback Loop**: Every successful execution improves the company's knowledge and skills. The company learns from every task.
- **Safety First**: Policy Engine checks are performed before every critical step. Non-deterministic (LLM) output is validated before persistence.

---

## 19. Final Blueprint Statement

This blueprint defines the future implementation shape of the AI Execution Runtime layer while preserving the contract-first architecture of the AI Company. The Execution Runtime is the operational bridge between the company's strategic decisions and its tangible outcomes.

When fully implemented, every task execution will follow a consistent, observable, resilient, and auditable pipeline. Decisions flow from the Decision Engine, pass through the Policy Engine, are executed via the LLM Gateway, and produce results, knowledge, and skills that continuously improve the company's capabilities.
