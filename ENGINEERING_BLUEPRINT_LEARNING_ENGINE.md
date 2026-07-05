# Engineering Blueprint — Learning Engine

## Purpose

This document is the engineering blueprint for the `Learning Engine` of the AI Company. It defines the architecture of the continuous improvement layer responsible for transforming organizational experience — execution results, feedback signals, pattern observations, and skill evolution data — into actionable recommendations that make the company more effective over time.

The Learning Engine is the company's **capacity for growth**. It does not execute tasks, make decisions, or evaluate policies. It observes outcomes, analyzes patterns, and proposes improvements that the Decision Engine, Policy Engine, AI Execution Runtime, and Skills Runtime may act upon.

This blueprint translates the need for a closed learning loop into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

**Why a Learning Engine exists:**

The AI Company produces vast amounts of operational data with every execution: which employees succeeded at which tasks, which departments completed work on time, which skills were most effective, which policies blocked legitimate actions, which LLM providers delivered the best results. Without a Learning Engine, this data is observed but never acted upon. The company would repeat the same mistakes, miss optimization opportunities, and fail to evolve its skill base as task complexity grows.

A Learning Engine closes the feedback loop by:
- Collecting execution outcomes, feedback, and performance data from every runtime.
- Detecting patterns — both positive (what works) and negative (what fails).
- Translating patterns into concrete recommendations for skill development, knowledge refinement, policy adjustment, and decision tuning.
- Coordinating with the Skills Runtime to evolve skill definitions based on observed performance.
- Coordinating with the Knowledge Runtime to identify knowledge gaps and refinement opportunities.
- Producing immutable `LearningSnapshot` objects that the Decision Engine and Orchestrator can query to inform future decisions.

**Why Learning is distinct from Knowledge:**

Knowledge represents validated organizational assets — completed results, stored documents, curated data, established policies. Knowledge is what the company **knows**.

Learning represents the continuous evolution of the company based on those assets. Learning is the process of deriving improvement from outcomes — identifying that a skill needs refinement, detecting that a policy is causing repeated failures, recognizing that a particular task type would benefit from a different approach. Learning is what the company **becomes better at**.

Knowledge is static between explicit updates. Learning is ongoing and never stops as long as the company operates.

---

## 1. Scope and Boundaries

### In Scope (What Belongs to the Learning Engine)

- **Learning Cycle Management**: Initiating, executing, and completing learning cycles. Each cycle represents a discrete improvement pass triggered by an execution completion, a feedback submission, or a scheduled review.
- **Feedback Analysis**: Collecting and analyzing structured feedback from users, employees, and automated validators. Transforming raw feedback into actionable signals.
- **Pattern Detection**: Analyzing execution history, skill performance, policy outcomes, and knowledge usage to identify recurring patterns — both positive (high-success patterns) and negative (failure modes).
- **Improvement Planning**: Translating detected patterns and feedback signals into concrete, prioritized improvement recommendations.
- **Skill Evolution Coordination**: Recommending skill definition changes (new skills, skill splits, skill merges, skill deprecation) based on observed performance data.
- **Knowledge Evolution Coordination**: Identifying knowledge gaps, outdated content, and refinement opportunities based on execution outcomes.
- **Learning Context Production**: Producing immutable `LearningContext` objects that capture the state of a learning cycle for audit and traceability.
- **Learning Snapshot Production**: Producing immutable `LearningSnapshot` objects containing current learning state, open recommendations, and improvement progress for the Decision Engine.
- **Learning History**: Maintaining a chronological record of all completed learning cycles, recommendations issued, and improvements applied.
- **Learning Metrics**: Collecting and exposing metrics on learning velocity (cycles per period), recommendation acceptance rate, improvement impact, and skill evolution frequency.
- **Policy Recommendation**: Identifying policies that cause frequent blocked actions or exceptions and recommending policy adjustments.

### Out of Scope (What Does NOT Belong to the Learning Engine)

- **Execution**: The Learning Engine does not execute tasks, run workflows, or generate content. Execution belongs to the AI Execution Runtime.
- **Decision Making**: The Learning Engine does not choose employees, route tasks, or resolve priorities. It produces recommendations; the Decision Engine consumes or ignores them.
- **Policy Evaluation**: The Learning Engine does not evaluate whether actions are allowed. Policy evaluation belongs to the Policy Engine.
- **Knowledge Creation**: The Learning Engine does not create, store, or validate knowledge assets. Knowledge creation belongs to the Knowledge Runtime and the AI Execution Runtime.
- **Skill Definition**: The Learning Engine recommends skill changes but does not define, store, or validate skill definitions. Skill management belongs to the Skills Runtime.
- **Provider Communication**: The Learning Engine does not call LLM providers. Provider communication belongs to the LLM Gateway.
- **Conversation Management**: The Learning Engine may read conversation context for feedback analysis but does not manage conversations. Conversation management belongs to the Conversation Runtime.
- **Real-Time Action**: The Learning Engine operates asynchronously. It does not block execution, decisions, or policy evaluation. All learning is advisory and non-blocking.

---

## 2. Separation of Concerns

Learning is split into four distinct layers that mirror the company's operational flow:

```text
+-------------------------------------------------------------+
|                 Operational Layer                            |
|  (AI Execution Runtime, Conversation Runtime,               |
|   Employees, Workflows)                                      |
|  Produces: execution results, feedback, conversation data    |
+---------------------------+---------------------------------+
                            | Events and Data
                            v
+-------------------------------------------------------------+
|                 Analysis Layer                               |
|  (FeedbackAnalyzer, PatternDetector)                         |
|  Produces: analyzed feedback, detected patterns, signals     |
+---------------------------+---------------------------------+
                            | Patterns and Signals
                            v
+-------------------------------------------------------------+
|                 Planning Layer                               |
|  (ImprovementPlanner, SkillEvolutionCoordinator,             |
|   KnowledgeEvolutionCoordinator)                              |
|  Produces: recommendations, evolution proposals              |
+---------------------------+---------------------------------+
                            | Recommendations
                            v
+-------------------------------------------------------------+
|                 Advisory Layer                               |
|  (LearningRuntime, LearningSnapshot, LearningHistory,        |
|   Decision Engine, Orchestrator)                              |
|  Consumes: recommendations, learning snapshots               |
|  Acts on: accepted recommendations via existing runtimes     |
+-------------------------------------------------------------+
```

### Operational Layer
- **Responsibility**: Execute tasks, complete work, collect feedback. This layer produces the raw data that learning depends on.
- **Knowledge**: Task outcomes, execution traces, conversation transcripts, user feedback.

### Analysis Layer
- **Responsibility**: Transform raw operational data into analyzed signals. Detect patterns in success and failure across executions, skills, policies, and knowledge usage.
- **Knowledge**: Feedback taxonomy, pattern definitions, statistical methods, threshold configuration.

### Planning Layer
- **Responsibility**: Translate analyzed signals into concrete, prioritized recommendations. Coordinate with the Skills Runtime and Knowledge Runtime to propose specific evolution actions.
- **Knowledge**: Recommendation templates, evolution policies, priority formulas, impact estimation.

### Advisory Layer
- **Responsibility**: Expose recommendations and learning state to the Decision Engine and Orchestrator. The Decision Engine may incorporate learning recommendations into future decisions (e.g., route tasks to skills with higher success rates). The Orchestrator may schedule skill or knowledge evolution based on accepted recommendations.
- **Knowledge**: Current learning state, open recommendations, historical learning outcomes.

---

## 3. Relationships and Interactions

The Learning Engine is an asynchronous consumer of operational events and a producer of advisory data for strategic components:

```text
  AI Execution Runtime
        |
        +---> ExecutionCompleted event --------+
        |                                     |
  Conversation Runtime                        |
        |                                     |
        +---> FeedbackSubmitted event --------+
        |                                     |
  Policy Engine                               |
        |                                     |
        +---> PolicyBlocked event ------------+
        |                                     v
        |                          +---------------------+
        |                          |   Learning Engine    |
        |                          |                     |
        |                          |  1. Collect data    |
        |                          |  2. Analyze         |
        |                          |  3. Detect patterns |
        |                          |  4. Plan improv.    |
        |                          |  5. Produce reco.   |
        |                          +----------+----------+
        |                                     |
        |                          +----------+----------+
        |                          v                     v
        |                   +------------+      +--------------+
        |                   |  Decision  |      | Orchestrator |
        |                   |  Engine    |      |              |
        |                   +------------+      +--------------+
        |                          |                     |
        |                          v                     v
        |                   +------------+      +--------------+
        |                   |  Skills    |      |  Knowledge   |
        |                   |  Runtime   |      |  Runtime     |
        |                   +------------+      +--------------+
```

- **AI Execution Runtime**: Publishes `ExecutionCompleted` events containing outcome data (success/failure, duration, tokens used, provider used, skill used). The Learning Engine consumes these to detect skill performance patterns and execution quality trends.
- **Conversation Runtime**: Publishes feedback-related events and provides conversation context for qualitative analysis.
- **Policy Engine**: Publishes `PolicyBlocked` events containing the policy violated, the action attempted, and the employee involved. The Learning Engine consumes these to identify problematic policies.
- **Decision Engine**: Queries `LearningSnapshot` for skill performance data, department efficiency trends, and recommendation status. May incorporate learning data into candidate ranking and priority resolution.
- **Skills Runtime**: Receives skill evolution proposals from the `SkillEvolutionCoordinator`. May accept, reject, or modify proposals based on its own constraints.
- **Knowledge Runtime**: Receives knowledge evolution proposals from the `KnowledgeEvolutionCoordinator`. May accept, reject, or modify proposals based on its own constraints.
- **Orchestrator**: Reviews learning recommendations and may trigger execution of approved recommendations (e.g., schedule a skill refinement execution, trigger a knowledge audit).

---

## 4. Component Breakdown

The Learning Engine is organized as a set of logical sub-components with clearly separated responsibilities:

```text
                    +--------------------------------+
                    |        LearningRuntime          |
                    |  (Public Orchestration Entry)   |
                    +------+--------------+----------+
                           |              |
              +------------+------+  +----+------------+
              |   FeedbackAnalyzer|  |  PatternDetector |
              |  (Signal from     |  |  (Pattern from   |
              |   raw feedback)   |  |   history data)  |
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |        ImprovementPlanner           |
              |  (Recommendations from signals)     |
              +------------+--------------+--------+
                           |              |
              +------------+------+  +----+------------+
              |SkillEvolution    |  |KnowledgeEvolution|
              |Coordinator       |  |Coordinator       |
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |         LearningHistory             |
              |  (All cycles + recommendations)     |
              +------------+-----------------------+
                           |
              +------------+-----------------------+
              |         LearningSnapshot            |
              |  (Immutable state for consumers)    |
              +------------------------------------+
```

### 4.1 LearningRuntime (Orchestration Entry Point)

- **Purpose**: Single public entry point for all learning operations. Receives triggers (execution completed, feedback submitted, scheduled cycle), orchestrates the learning pipeline (collect, analyze, detect, plan, recommend), and publishes results.
- **Execution**: Asynchronous orchestrator. Learning cycles are non-blocking — they never delay execution or decision making. The Runtime manages cycle lifecycles and delegates to specialized sub-components.
- **Public Interface** (conceptual):
  - `trigger_cycle(trigger: LearningTrigger) -> CycleID`: Initiates a new learning cycle.
  - `get_cycle(cycle_id) -> LearningCycle`
  - `list_cycles(status, limit, offset) -> list[LearningCycle]`
  - `get_recommendations(status, priority, limit) -> list[LearningRecommendation]`
  - `get_snapshot() -> LearningSnapshot`
  - `acknowledge_recommendation(recommendation_id) -> bool`
  - `close_recommendation(recommendation_id, outcome) -> bool`
  - `get_patterns(pattern_type, limit) -> list[Pattern]`

### 4.2 LearningCycle

- **Purpose**: Represents a single discrete learning pass. Each cycle is triggered by an event (execution completion, feedback submission, scheduled interval) and produces zero or more recommendations.
- **Structure** (conceptual):
  - `cycle_id`: Unique identifier.
  - `trigger_type`: `EXECUTION_COMPLETED`, `FEEDBACK_SUBMITTED`, `SCHEDULED_REVIEW`, `POLICY_BLOCKED`.
  - `trigger_id`: Identifier of the triggering entity.
  - `status`: `COLLECTING`, `ANALYZING`, `DETECTING`, `PLANNING`, `COMPLETED`, `FAILED`.
  - `context`: `LearningContext` object with cycle-specific data.
  - `patterns_detected`: List of pattern references found in this cycle.
  - `recommendations_produced`: List of recommendation references produced by this cycle.
  - `created_at`, `completed_at`, `duration_ms`.
- **Lifecycle**: `COLLECTING` > `ANALYZING` > `DETECTING` > `PLANNING` > `COMPLETED`. Transitions are sequential and linear. If any step fails, the cycle moves to `FAILED` and retains partial results for diagnostic purposes.

### 4.3 LearningContext

- **Purpose**: Immutable snapshot of all data collected for a single learning cycle. Captures the inputs that drive analysis and planning. Used for audit, traceability, and reproducibility of learning outcomes.
- **Structure** (conceptual):
  - `cycle_id`: Parent cycle.
  - `trigger_type`: The type of event that triggered this cycle.
  - `trigger_data`: The raw triggering event data (execution result, feedback payload, schedule config).
  - `execution_history`: Recent execution outcomes relevant to this cycle (limited to configurable window).
  - `feedback_data`: Feedback entries collected since the last cycle.
  - `policy_block_events`: Recent policy block events relevant to this cycle.
  - `skill_snapshots`: Current state of relevant skill definitions.
  - `knowledge_snapshots`: Current state of relevant knowledge assets.
  - `context_version`: Version number for tracking.
  - `created_at`: Timestamp of context creation.
- **Immutability**: `LearningContext` is fully frozen once produced. No component may modify it during or after the learning cycle.

### 4.4 LearningObjective

- **Purpose**: Defines what a learning cycle aims to achieve. Objectives are derived from the trigger type and configured learning priorities. They guide the analysis and planning phases by focusing attention on specific areas.
- **Structure** (conceptual):
  - `objective_id`: Unique identifier.
  - `cycle_id`: Parent cycle.
  - `objective_type`: `SKILL_PERFORMANCE`, `KNOWLEDGE_GAP`, `POLICY_EFFECTIVENESS`, `EXECUTION_QUALITY`, `FEEDBACK_ANALYSIS`.
  - `target`: The specific entity being evaluated (skill ID, knowledge category, policy ID).
  - `criteria`: Evaluation criteria and success thresholds.
  - `weight`: Relative importance of this objective within the cycle.
  - `status`: `PENDING`, `EVALUATING`, `ACHIEVED`, `NOT_ACHIEVED`.
- **Examples**:
  - "Evaluate whether `ContentWriting` skill performance has degraded below 80% success rate."
  - "Identify knowledge categories with zero usage in the last 30 days."
  - "Analyze whether `MaxTokenBudget` policy is blocking an excessive proportion of valid executions."

### 4.5 LearningOutcome

- **Purpose**: Represents the result of evaluating a single `LearningObjective`. Contains the analysis findings, supporting evidence, and a verdict on whether the objective was achieved or requires action.
- **Structure** (conceptual):
  - `outcome_id`: Unique identifier.
  - `objective_id`: Parent objective.
  - `cycle_id`: Parent cycle.
  - `verdict`: `MET`, `NOT_MET`, `INCONCLUSIVE`, `ERROR`.
  - `evidence`: Supporting data (statistics, sample executions, pattern references).
  - `confidence`: Confidence score (0.0 to 1.0) in the verdict.
  - `analysis_summary`: Human-readable summary of the analysis.
  - `produced_at`: Timestamp.

### 4.6 LearningRecommendation

- **Purpose**: A concrete, actionable proposal produced by a learning cycle. Recommendations are the primary output of the Learning Engine. They are consumed by the Decision Engine, Orchestrator, Skills Runtime, and Knowledge Runtime.
- **Structure** (conceptual):
  - `recommendation_id`: Unique identifier.
  - `cycle_id`: Parent cycle.
  - `recommendation_type`: `SKILL_CREATE`, `SKILL_REFINE`, `SKILL_DEPRECATE`, `KNOWLEDGE_CREATE`, `KNOWLEDGE_REFRESH`, `KNOWLEDGE_DEPRECATE`, `POLICY_ADJUST`, `DECISION_TUNE`, `PROCESS_IMPROVE`.
  - `target`: The specific entity the recommendation applies to.
  - `priority`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
  - `impact_estimate`: Estimated positive impact if adopted.
  - `risk_estimate`: Estimated risk if not adopted.
  - `supporting_evidence`: References to outcomes, patterns, and data supporting this recommendation.
  - `proposed_action`: Description of the recommended action.
  - `status`: `OPEN`, `ACKNOWLEDGED`, `ACCEPTED`, `REJECTED`, `SUPERSEDED`, `IMPLEMENTED`.
  - `acknowledged_by`: Optional identifier of who acknowledged.
  - `closed_at`: Optional timestamp of resolution.
  - `resolution_outcome`: Optional outcome description.
- **Priority Matrix**:

| Impact | Urgency | Priority |
|--------|---------|----------|
| High | High | CRITICAL |
| High | Low | HIGH |
| Low | High | MEDIUM |
| Low | Low | LOW |

### 4.7 LearningHistory

- **Purpose**: Chronological record of all completed learning cycles, recommendations issued, and outcomes achieved.
- **Structure** (conceptual):
  - `entries`: Ordered list of history entries with cycle_id, trigger_type, recommendations_count, recommendations_accepted, recommendations_implemented, duration_ms, completed_at.
  - `summary_stats`: Aggregate statistics (total cycles, avg duration, acceptance rate, implementation rate).
- **Access Patterns**: Chronological listing, filtered by trigger type or date range, aggregated by time period.

### 4.8 LearningMetrics

- **Purpose**: Quantitative metrics about the learning process itself. Enables the company to measure how well it is learning.
- **Metrics**:
  - `learning_velocity`: Cycles per time period.
  - `recommendation_acceptance_rate`: Proportion accepted vs. issued.
  - `recommendation_implementation_rate`: Proportion implemented vs. accepted.
  - `average_cycle_duration`: Mean completion time.
  - `pattern_detection_rate`: Patterns detected per cycle.
  - `skill_evolution_frequency`: Skill changes driven by learning.
  - `knowledge_evolution_frequency`: Knowledge changes driven by learning.
  - `improvement_impact`: Measurable improvement attributed to implemented recommendations.
- **Computation**: Derived from `LearningHistory` and current state. Not stored separately.

### 4.9 LearningSnapshot

- **Purpose**: Immutable, versioned, fully frozen representation of the Learning Engine's current state.
- **Structure** (conceptual):
  - `snapshot_id`: Unique identifier.
  - `version`: Monotonically increasing version number.
  - `open_recommendations`: Frozen list of open `LearningRecommendation` objects.
  - `recent_cycles`: Frozen list of recent completed cycles.
  - `active_patterns`: Frozen list of currently tracked patterns.
  - `metrics`: Frozen `LearningMetrics` snapshot.
  - `skill_evolution_status`: Current state of skill evolution proposals.
  - `knowledge_evolution_status`: Current state of knowledge evolution proposals.
  - `created_at`: Snapshot creation timestamp.
  - `checksum`: SHA-256 hash for integrity verification.

### 4.10 FeedbackAnalyzer

- **Purpose**: Collects and analyzes structured feedback from multiple sources. Transforms raw feedback into normalized signals.
- **Execution**: Stateless per analysis operation.
- **Feedback Sources**:
  - **User Feedback**: Ratings and comments from human users.
  - **Employee Feedback**: Self-assessment data from employees.
  - **Automated Quality Scores**: Objective metrics from `OutputValidator`.
  - **Execution Outcome Feedback**: Derived signals from execution success/failure data.
- **Key Operations**:
  - `analyze(feedback_entries, context) -> list[FeedbackSignal]`
  - `aggregate_by_category(signals) -> dict[Category, AggregatedSignal]`
  - `compute_satisfaction_trend(signals, window) -> Trend`
- **Feedback Signal Structure**:
  - `signal_id`, `source_type` (USER, EMPLOYEE, AUTOMATED, DERIVED), `category` (QUALITY, SPEED, ACCURACY, CLARITY, USEFULNESS, COST), `sentiment` (POSITIVE, NEUTRAL, NEGATIVE), `severity` (LOW, MEDIUM, HIGH, CRITICAL), `score` (0.0 to 1.0), `comment`, `origin`.

### 4.11 PatternDetector

- **Purpose**: Analyzes execution history, feedback signals, policy outcomes, and skill performance data to identify recurring patterns.
- **Execution**: Stateless per detection operation.
- **Pattern Types**:
  1. **Skill Performance Degradation**: Success rate declined below threshold.
  2. **Skill Performance Excellence**: Consistently exceeds expectations.
  3. **Recurring Failure Mode**: Specific error type appears repeatedly.
  4. **Policy Blocking Pattern**: Policy blocks at elevated rate.
  5. **Knowledge Gap Pattern**: Executions fail on topics with incomplete knowledge.
  6. **Cost Inefficiency Pattern**: Provider/skill combination exceeds budgets.
  7. **Feedback Trend Pattern**: Sustained feedback trend for an entity.
  8. **Execution Duration Anomaly**: Times deviate from baselines.
  9. **Underutilization Pattern**: Skill or knowledge asset has low or zero usage.
- **Key Operations**:
  - `detect_patterns(execution_history, feedback_signals, policy_events, config) -> list[Pattern]`
  - `get_pattern_definitions() -> list[PatternDefinition]`
- **Pattern Structure**:
  - `pattern_id`, `pattern_type`, `severity` (INFO, WARNING, CRITICAL), `target`, `evidence`, `confidence` (0.0 to 1.0), `first_detected_at`, `last_detected_at`, `occurrence_count`, `description`.

### 4.12 ImprovementPlanner

- **Purpose**: Translates detected patterns and feedback signals into concrete, prioritized `LearningRecommendation` objects.
- **Execution**: Stateless per planning operation.
- **Key Operations**:
  - `plan_improvements(patterns, signals, context) -> list[LearningRecommendation]`
  - `estimate_impact(recommendation, historical_data) -> ImpactEstimate`
  - `prioritize(recommendations) -> list[LearningRecommendation]`
- **Recommendation Rules** (conceptual):
  - Skill degradation > threshold: `SKILL_REFINE`.
  - Knowledge gap > threshold: `KNOWLEDGE_REFRESH` or `KNOWLEDGE_CREATE`.
  - Policy blocking > threshold: `POLICY_ADJUST`.
  - Cost inefficiency > threshold: `DECISION_TUNE`.
  - Skill underutilized > 30 days: `SKILL_DEPRECATE`.
  - Knowledge zero usage > 60 days: `KNOWLEDGE_DEPRECATE`.
- **Deduplication**: Multiple patterns leading to the same recommendation are merged with combined evidence.

### 4.13 SkillEvolutionCoordinator

- **Purpose**: Coordinates with the Skills Runtime to propose and track skill definition changes.
- **Execution**: Stateful per proposal.
- **Key Operations**:
  - `propose_skill_creation(name, description, category, based_on) -> ProposalID`
  - `propose_skill_refinement(skill_id, changes, rationale) -> ProposalID`
  - `propose_skill_deprecation(skill_id, rationale, replacement) -> ProposalID`
  - `submit_proposal(proposal_id) -> bool`
  - `get_proposal_status(proposal_id) -> ProposalStatus`
  - `cancel_proposal(proposal_id) -> bool`
- **Proposal Lifecycle**: `DRAFT` > `SUBMITTED` > `UNDER_REVIEW` > `ACCEPTED` / `REJECTED` > `IMPLEMENTED`.
- **Proposal Structure**:
  - `proposal_id`, `cycle_id`, `proposal_type` (CREATE, REFINE, DEPRECATE), `target_skill_id`, `proposed_changes`, `supporting_evidence`, `status`, `skills_runtime_response`, `created_at`, `updated_at`, `implemented_at`.

### 4.14 KnowledgeEvolutionCoordinator

- **Purpose**: Coordinates with the Knowledge Runtime to propose and track knowledge asset changes.
- **Execution**: Stateful per proposal.
- **Key Operations**:
  - `propose_knowledge_creation(category, content_outline, based_on) -> ProposalID`
  - `propose_knowledge_refresh(knowledge_id, changes, rationale) -> ProposalID`
  - `propose_knowledge_deprecation(knowledge_id, rationale) -> ProposalID`
  - `submit_proposal(proposal_id) -> bool`
  - `get_proposal_status(proposal_id) -> ProposalStatus`
  - `cancel_proposal(proposal_id) -> bool`
- **Proposal Lifecycle**: Same as `SkillEvolutionCoordinator`.

### 4.15 LearningPolicy

- **Purpose**: Defines rules and constraints that govern how the Learning Engine operates.
- **Structure** (conceptual):
  - `policy_id`, `scope` (GLOBAL, BY_SKILL, BY_DEPARTMENT, BY_EXECUTION_TYPE), `condition`, `action`, `parameters`, `enabled`, `created_at`, `updated_at`.
- **Built-in Policies**:
  - **Minimum Viable Performance**: Success rate < 70% over 7 days -> HIGH priority skill refinement.
  - **Excessive Policy Blocking**: Policy blocks > 10% of actions in 24h -> MEDIUM policy review.
  - **Knowledge Staleness**: Zero reads for 60 days -> LOW deprecation review.
  - **Cost Anomaly**: Cost > 150% of baseline over 7 days -> MEDIUM cost optimization.
  - **Feedback Overload**: Negative feedback > 30% for a skill in 24h -> HIGH skill refinement.

### 4.16 LearningTrace

- **Purpose**: Records every step of a learning cycle for audit, debugging, and reproducibility.
- **Structure** (conceptual):
  - `trace_id`, `cycle_id`.
  - `stages`: Ordered list with `stage_name`, `started_at`, `completed_at`, `duration_ms`, `input_summary`, `output_summary`, `errors`.
  - `final_status`: `COMPLETED`, `FAILED`, `PARTIAL`.
  - `recommendations_produced`, `patterns_detected`.
- **Visibility**: Available for debugging, not exposed in public API. May be persisted via Knowledge Runtime.

---

## 5. Learning Cycle Lifecycle

Every learning cycle follows a fixed pipeline of stages. Each stage has specific responsibilities and produces well-defined outputs.

### Stage Diagram

```text
  Trigger
     |
     v
+------------+     +------------+     +------------+     +------------+
|  COLLECT   |---->|  ANALYZE   |---->|  DETECT    |---->|  PLAN      |
|  Data      |     |  Feedback  |     |  Patterns  |     |  Improve.  |
+------------+     +------------+     +------------+     +------------+
                                                              |
                                                              v
                                                       +------------+
                                                       | COORDINATE |
                                                       | Evolution  |
                                                       +------------+
                                                              |
                                                              v
                                                       +------------+
                                                       | COMPLETED  |
                                                       +------------+
```

### Stage 1: COLLECT
- **Trigger**: An execution completes, feedback is submitted, a scheduled review fires, or a policy blocks an action.
- **Action**: The LearningRuntime gathers all relevant data: triggering event payload, recent execution history, open feedback entries, relevant policy events, current skill definitions, and current knowledge asset metadata.
- **Output**: A populated `LearningContext` frozen for the duration of the cycle.
- **Failure Mode**: If data collection fails, the cycle is marked FAILED and may be retried on the next trigger.
- **Performance Target**: < 50 ms.

### Stage 2: ANALYZE
- **Trigger**: COLLECT completes.
- **Action**: The `FeedbackAnalyzer` processes feedback entries. Raw feedback is categorized, scored, and normalized into `FeedbackSignal` objects.
- **Output**: A list of `FeedbackSignal` objects.
- **Performance Target**: < 100 ms for up to 100 feedback entries.

### Stage 3: DETECT
- **Trigger**: ANALYZE completes.
- **Action**: The `PatternDetector` evaluates collected data and feedback signals against all active pattern definitions. Results are deduplicated and prioritized.
- **Output**: A prioritized list of `Pattern` objects.
- **Performance Target**: < 200 ms.

### Stage 4: PLAN
- **Trigger**: DETECT completes.
- **Action**: The `ImprovementPlanner` evaluates each pattern against recommendation rules. Patterns are translated into `LearningRecommendation` objects, deduplicated, prioritized, and enriched with impact estimates.
- **Output**: A prioritized list of `LearningRecommendation` objects.
- **Performance Target**: < 100 ms.

### Stage 5: COORDINATE
- **Trigger**: PLAN completes and at least one recommendation requires evolution.
- **Action**: `SkillEvolutionCoordinator` and `KnowledgeEvolutionCoordinator` create and submit evolution proposals. Best-effort: if a runtime is unavailable, proposals are retained.
- **Output**: Submitted evolution proposals (if any).
- **Performance Target**: < 200 ms.

### Stage 6: COMPLETED
- **Trigger**: All previous stages complete.
- **Action**: Cycle marked COMPLETED. `LearningTrace` finalized. `LearningHistory` updated. `CycleCompleted` event published.
- **Output**: Finalized cycle state and published event.

### Stage: FAILED
- **Entry**: Any stage throws an unhandled error or exceeds time budget.
- **Action**: Cycle marked FAILED with error details in `LearningTrace`. Partial results retained. `CycleFailed` event published.

---

## 6. Event Model

The Learning Engine publishes events to the EventBus for observability, cross-component notification, and persistence triggers.

### 6.1 Event Catalog

| Event | Trigger | Payload |
|-------|---------|---------|
| `CycleStarted` | `trigger_cycle()` | cycle_id, trigger_type, trigger_id, context_version, started_at |
| `CycleCompleted` | cycle reaches COMPLETED | cycle_id, duration_ms, patterns_count, recommendations_count, completed_at |
| `CycleFailed` | cycle reaches FAILED | cycle_id, failed_stage, error_message, partial_results |
| `PatternDetected` | DETECT stage | pattern_id, pattern_type, severity, target, confidence, cycle_id |
| `RecommendationIssued` | PLAN stage | recommendation_id, recommendation_type, target, priority, cycle_id |
| `RecommendationAcknowledged` | acknowledge_recommendation() | recommendation_id, acknowledged_by |
| `RecommendationClosed` | close_recommendation() | recommendation_id, outcome |
| `EvolutionProposalSubmitted` | COORDINATE stage | proposal_id, proposal_type, target_runtime, target_entity, cycle_id |
| `LearningSnapshotUpdated` | significant state change | snapshot_id, version, open_recommendations_count, active_patterns_count |
| `FeedbackAnalyzed` | ANALYZE stage | cycle_id, feedback_count, positive_count, negative_count, top_categories |

### 6.2 Event Publishing Rules

- Events are published **after** the state change is committed.
- Events are **fire-and-forget**. The Learning Engine does not wait for consumers.
- Events are **immutable** and **idempotent**.
- Events carry enough context for consumers to act without querying the Learning Engine.

### 6.3 Event Consumers

| Consumer | Subscribes To | Purpose |
|----------|--------------|---------|
| Observability Projector | All learning events | Track learning metrics, cycle duration, recommendation outcomes |
| Knowledge Runtime | EvolutionProposalSubmitted | Receive and process knowledge evolution proposals |
| Skills Runtime | EvolutionProposalSubmitted | Receive and process skill evolution proposals |
| Orchestrator | RecommendationIssued, RecommendationClosed | Review recommendations, trigger implementation |
| Decision Engine | LearningSnapshotUpdated | Refresh cached learning data for decision inputs |

---

## 7. Integration with Knowledge Runtime

### 7.1 Knowledge as Input

The Learning Engine queries the Knowledge Runtime during COLLECT to retrieve:
- Recent execution results and outcomes.
- Current knowledge asset metadata (categories, timestamps, usage statistics).
- Knowledge usage patterns (reads, references, queries).

### 7.2 Knowledge Evolution Proposals

The `KnowledgeEvolutionCoordinator` submits proposals to the Knowledge Runtime:
- `KNOWLEDGE_CREATE`: New knowledge asset.
- `KNOWLEDGE_REFRESH`: Update existing asset.
- `KNOWLEDGE_DEPRECATE`: Mark asset as deprecated.

Each proposal includes supporting evidence for evaluation.

### 7.3 Knowledge Runtime Response

The Knowledge Runtime may respond with:
- `ACCEPTED`: Proposal accepted and scheduled.
- `REJECTED`: Proposal rejected with reason.
- `MODIFIED`: Accepted with modifications.
- `DEFERRED`: Noted but not scheduled.

### 7.4 Bidirectional Flow

```text
  Learning Engine                    Knowledge Runtime
        |                                    |
        |  1. Query knowledge metadata       |
        |----------------------------------->|
        |                                    |
        |  2. Knowledge usage stats          |
        |<-----------------------------------|
        |                                    |
        |  3. Submit evolution proposal      |
        |----------------------------------->|
        |                                    |
        |  4. ACCEPTED / REJECTED / MODIFIED |
        |<-----------------------------------|
```

---

## 8. Integration with Skills Runtime

### 8.1 Skills as Input

The Learning Engine queries the Skills Runtime during COLLECT to retrieve:
- Current skill definitions and categories.
- Skill assignment and usage statistics.
- Skill performance history per employee.

### 8.2 Skill Evolution Proposals

The `SkillEvolutionCoordinator` submits proposals:
- `SKILL_CREATE`: New skill from observed patterns.
- `SKILL_REFINE`: Adjust skill definition based on performance.
- `SKILL_DEPRECATE`: Remove underperforming or unused skill.

### 8.3 Skill Runtime Response

Same response model as Knowledge Runtime.

### 8.4 Bidirectional Flow

```text
  Learning Engine                    Skills Runtime
        |                                    |
        |  1. Query skill definitions        |
        |----------------------------------->|
        |                                    |
        |  2. Skill usage stats              |
        |<-----------------------------------|
        |                                    |
        |  3. Submit evolution proposal      |
        |----------------------------------->|
        |                                    |
        |  4. ACCEPTED / REJECTED / MODIFIED |
        |<-----------------------------------|
```

---

## 9. Integration with Decision Engine

### 9.1 Learning Snapshot as Decision Input

The Decision Engine queries `LearningSnapshot` during decision making:
- **Skill performance data**: Prefer high-performing skills.
- **Department efficiency trends**: Faster or more cost-effective departments.
- **Open recommendations**: Avoid recommending skills flagged for deprecation.
- **Policy effectiveness signals**: Anticipate potential policy blocks.

### 9.2 Decision Engine Integration Points

| Decision Engine Step | Learning Data Used | Impact |
|---------------------|-------------------|--------|
| select_candidates | Skill performance rankings | Prefer candidates with higher success rates |
| evaluate_constraints | Policy effectiveness data | Anticipate blocks, adjust routing |
| match_skills | Skill evolution recommendations | Avoid skills flagged for deprecation |
| resolve_priority | Department efficiency trends | Adjust priority weights |
| choose_best_candidate | Combined learning data | Final selection informed by learning |

### 9.3 No Direct Coupling

The Decision Engine reads `LearningSnapshot` data. The snapshot is always stale (bounded by last learning cycle), which is acceptable because learning data changes slowly compared to decision frequency.

---

## 10. Integration with AI Execution Runtime

### 10.1 Execution Results as Learning Input

The AI Execution Runtime publishes `ExecutionCompleted` events containing:
- `execution_id`, `task_id`, `employee_id`, `skill_id`.
- `outcome`: SUCCESS, FAILURE, PARTIAL.
- `duration_ms`, `tokens_used`, `cost`, `provider_id`.
- `error_reason`, `quality_score`.

### 10.2 Learning-Driven Execution Tuning

When patterns affect execution quality, the Learning Engine may issue a `DECISION_TUNE` recommendation. If accepted, this adjusts provider selection, skill assignment, or priority weights.

### 10.3 No Execution Feedback Loop Blocking

Learning never blocks or delays execution. The AI Execution Runtime is completely unaware of ongoing learning.

---

## 11. Integration with Conversation Runtime

### 11.1 Feedback Collection

The Conversation Runtime publishes feedback-related events:
- `FeedbackSubmitted`: Structured feedback from users or employees.
- `ConversationEnded`: Conversation transcript for qualitative analysis.

### 11.2 Conversation Context for Qualitative Analysis

The `FeedbackAnalyzer` may retrieve conversation threads surrounding feedback. The `PatternDetector` may analyze transcripts for recurring themes not captured by structured feedback.

### 11.3 No Conversation Modification

The Learning Engine reads conversation data but never writes to conversations. It is an observer, not a participant.

---

## 12. Data Model

```text
  +--------------------------+
  |     LearningCycle         |
  +--------------------------+
  | cycle_id: UUID           |
  | trigger_type: Enum       |
  | trigger_id: UUID         |
  | status: Enum             |
  | context: LearningContext |
  | patterns_detected: []    |
  | recommendations: []      |
  | created_at: ISO8601      |
  | completed_at: ISO8601    |
  | duration_ms: int         |
  +--------------------------+
            | 1:N
            v
  +--------------------------+      +----------------------------+
  |   LearningRecommendation  |      |      Pattern               |
  +--------------------------+      +----------------------------+
  | recommendation_id: UUID  |      | pattern_id: UUID           |
  | cycle_id: UUID           |      | pattern_type: Enum         |
  | recommendation_type: Enum|      | severity: Enum             |
  | target: string           |      | target: string             |
  | priority: Enum           |      | evidence: list             |
  | impact_estimate: float   |      | confidence: float (0-1)    |
  | risk_estimate: float     |      | first_detected_at: ISO8601 |
  | supporting_evidence: []  |      | last_detected_at: ISO8601  |
  | proposed_action: string  |      | occurrence_count: int      |
  | status: Enum             |      | description: string        |
  | acknowledged_by: UUID    |      +----------------------------+
  | closed_at: ISO8601       |
  | resolution_outcome: Enum |
  +--------------------------+

  +--------------------------+      +----------------------------+
  |   LearningSnapshot        |      |      LearningHistory       |
  +--------------------------+      +----------------------------+
  | snapshot_id: UUID        |      | entries: list              |
  | version: int             |      | summary_stats: dict        |
  | open_recommendations: [] |      +----------------------------+
  | recent_cycles: []        |
  | active_patterns: []      |
  | metrics: LearningMetrics |
  | created_at: ISO8601      |
  | checksum: string         |
  +--------------------------+
```

---

## 13. Policies

### 13.1 Learning Cycle Frequency

| Trigger Type | Min Interval | Max Frequency | Rationale |
|-------------|-------------|---------------|-----------|
| EXECUTION_COMPLETED | Every completion | Real-time | Each execution contains valuable learning data |
| FEEDBACK_SUBMITTED | Every submission | Real-time | Feedback is time-sensitive |
| SCHEDULED_REVIEW | Configurable | Every 6 hours minimum | Prevents excessive cycles during idle periods |
| POLICY_BLOCKED | Per block event | Max 100 cycles/min | Throttled to prevent feedback loops |

### 13.2 Recommendation Retention

- **OPEN**: Indefinitely until acknowledged or closed.
- **ACKNOWLEDGED**: 30 days after acknowledgment.
- **ACCEPTED**: 90 days after implementation for impact tracking.
- **REJECTED**: 30 days, then archived.
- **SUPERSEDED**: 30 days after being superseded.

### 13.3 Pattern Tracking

- Patterns retained 90 days since last detection.
- If not detected again within 90 days, archived.
- Archived patterns may be reactivated.

### 13.4 Cycle History Retention

- Completed cycles retained in-memory for 7 days.
- Cycle metadata and recommendations retained indefinitely.
- Full cycle data may be persisted via Knowledge Runtime.

### 13.5 Isolation Policy

- Cycles triggered by different departments are isolated.
- Cycles for different execution types are independent.
- `LearningSnapshot` is scoped to the requesting context.

---

## 14. Versioning and Auditability

### 14.1 Context Versioning

`context_version` in `LearningContext` is incremented on every state change. Included in all events and snapshots for correlation.

### 14.2 Snapshot Versioning

Each `LearningSnapshot` has a monotonically increasing `version`. Consumers detect stale snapshots by comparing versions.

### 14.3 Audit Trail

- Every cycle produces a `LearningTrace` with stage-by-stage records.
- Every recommendation status change is logged.
- Every event published to the EventBus is recorded.
- `LearningHistory` provides a summary view for high-level audit.

### 14.4 Checksum Integrity

Every `LearningSnapshot` includes a `checksum` (SHA-256). Consumers may verify integrity.

---

## 15. Implementation Roadmap

### Phase 1: Core Learning Cycle

- LearningRuntime with `trigger_cycle` and basic pipeline orchestration.
- LearningCycle, LearningContext, LearningObjective, LearningOutcome data structures.
- LearningTrace for audit.
- Basic COLLECT, ANALYZE, DETECT, PLAN stages (synchronous first).
- **Dependency**: None (self-contained).

### Phase 2: Feedback and Pattern Analysis

- FeedbackAnalyzer with feedback signal normalization.
- PatternDetector with initial pattern definitions.
- Pattern definitions as configuration (YAML/JSON).
- **Dependency**: EventBus (for consuming execution and feedback events).

### Phase 3: Improvement Planning and Recommendations

- ImprovementPlanner with recommendation rules.
- LearningRecommendation lifecycle management.
- LearningSnapshot production.
- **Dependency**: None (internal).

### Phase 4: Skill and Knowledge Evolution Coordination

- SkillEvolutionCoordinator with proposal lifecycle.
- KnowledgeEvolutionCoordinator with proposal lifecycle.
- **Dependency**: Skills Runtime, Knowledge Runtime.

### Phase 5: Event Publishing and Observability

- Full event catalog implementation.
- Integration with Observability Projector.
- LearningMetrics computation.
- **Dependency**: EventBus, Observability Projector.

### Phase 6: Decision Engine Integration

- LearningSnapshot queries from Decision Engine.
- Learning-informed decision tuning.
- **Dependency**: Decision Engine.

### Phase 7: Scheduled Reviews and Advanced Patterns

- SCHEDULED_REVIEW trigger type.
- Advanced pattern detection (cross-department, trend analysis, duration anomalies).
- **Dependency**: None (extension).

### Phase 8: Asynchronous and Scalable Processing

- Asynchronous cycle execution.
- Configurable cycle frequency and throttling.
- Horizontal scaling for high-volume environments.
- **Dependency**: Infrastructure.

---

## 16. Validation

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Learning Engine is separate from Execution, Decision, and Policy | Learning observes instead of acts, recommends instead of decides, evolves instead of evaluates. Combining it with any other engine would violate SRP. |
| Learning cycles are asynchronous and non-blocking | Learning must never delay execution or decision making. If the Learning Engine is slow, the company still operates. |
| Recommendations are advisory, not mandatory | The Decision Engine and Orchestrator must always have the final say. Learning may be wrong. |
| Snapshots are immutable and versioned | Consumers need a consistent view. Versioning detects stale data. |
| Skill and Knowledge evolution is coordinated through proposals | The Learning Engine does not have authority to modify skills or knowledge directly. |
| Feedback is analyzed, not stored | Storage belongs to the Knowledge Runtime. |
| Pattern detection is configuration-driven | Enables tuning without code changes. |

### Technical Justification

The Learning Engine exists because the AI Company would otherwise operate without a mechanism for continuous improvement. Every execution produces data, but data alone does not produce improvement. Improvement requires observation, analysis, planning, and coordination.

Without a dedicated Learning Engine, each runtime would implement its own observation-analysis-planning loop, leading to:
- Duplicated pattern detection logic.
- Inconsistent learning policies and thresholds.
- No centralized view of improvement trajectory.
- No cross-domain pattern correlation.

Centralizing learning gives the company:
- **Consistent pattern detection**: Same methodologies and thresholds everywhere.
- **Cross-domain correlation**: A skill performance pattern may correlate with a knowledge gap pattern. Only a centralized engine can detect this.
- **Holistic improvement planning**: Recommendations are prioritized across domains.
- **Measurable learning velocity**: The company tracks how quickly it improves.

### Risks

1. **False Pattern Detection**: Statistical noise flagged as patterns. Mitigation: confidence scores and minimum thresholds.
2. **Recommendation Overload**: Every execution triggers a recommendation. Mitigation: priority-based triage; LOW priority recommendations grouped and reviewed periodically.
3. **Stale Recommendations**: Recommendations remain OPEN indefinitely. Mitigation: automatic archival after 30 days.
4. **Feedback Loop**: A policy adjustment leads to more blocks, leading to more recommendations. Mitigation: deduplication prevents repeated recommendations for the same pattern.
5. **Knowledge Runtime Dependency**: COLLECT depends on Knowledge Runtime. Mitigation: graceful degradation using event data alone.

### Future Opportunities

1. **Predictive Learning**: Predict underperformance before it happens based on trend analysis.
2. **A/B Testing for Recommendations**: Implement as test, measure impact, auto-accept or reject.
3. **Cross-Company Learning**: Share anonymized pattern data across instances.
4. **Learning-Driven Workforce Planning**: Identify skill gaps at organizational level.
5. **Automated Recommendation Implementation**: For CRITICAL, low-risk recommendations, automate without manual review.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/` (new module) | A new `core/learning/` package containing runtime.py, cycle.py, context.py, objective.py, outcome.py, recommendation.py, history.py, metrics.py, snapshot.py, feedback.py, patterns.py, planner.py, skill_evolution.py, knowledge_evolution.py, policy.py, trace.py, events.py |
| `core/decision/runtime.py` | May optionally query `LearningSnapshot` for skill performance and department efficiency data |
| `core/skills/runtime.py` | Must expose a `receive_proposal()` interface for skill evolution proposals |
| `core/knowledge/runtime.py` | Must expose a `receive_proposal()` interface for knowledge evolution proposals |
| `core/execution/runtime.py` | Unchanged. Publishes events consumed by Learning Engine |
| `core/conversation/runtime.py` | Unchanged. Publishes feedback events consumed by Learning Engine |
| `core/policies/runtime.py` | Unchanged. Publishes policy events consumed by Learning Engine |
| `EventBus` | Unchanged. New learning event types, same bus contract |
| `ObservabilityProjector` | May add a `LearningProjector` to consume learning events |
| `ARCHITECTURE.md` | Should index this blueprint under a new Continuous Improvement section |

---

## 17. Architectural Principles

- **Advisory by Default**: The Learning Engine recommends. It never mandates, blocks, or bypasses authority boundaries. Every recommendation can be ignored.
- **Asynchronous and Non-Blocking**: Learning cycles run in the background. No operation ever waits for learning.
- **Immutability of Inputs**: `LearningContext` and `LearningSnapshot` are fully frozen.
- **Observability by Default**: Every cycle, pattern, and recommendation produces events.
- **Configuration-Driven Analysis**: Pattern definitions, thresholds, and policies are configuration, not code.
- **Evidence-Based Recommendations**: Every recommendation includes supporting evidence and confidence scores.
- **Cross-Domain Correlation**: The Learning Engine connects dots across skills, knowledge, policies, and execution.
- **Graceful Degradation**: If any dependency is unavailable, the Learning Engine continues with reduced capability.
- **Feedback Closure**: Every recommendation has a feedback path. The Learning Engine observes impact and learns from its own recommendations.

---

## 18. Final Blueprint Statement

This blueprint defines the future implementation shape of the Learning Engine layer while preserving the contract-first architecture of the AI Company. The Learning Engine is the company's capacity for continuous improvement — it transforms raw operational data into actionable insights that make every subsequent execution, decision, and policy more effective than the last.

When fully implemented, the AI Company will never repeat the same mistake twice. Every execution completion, every feedback submission, every policy block becomes an input to a cycle that produces recommendations for skill refinement, knowledge evolution, policy adjustment, and decision tuning. The company does not just execute — it learns, adapts, and improves with every operation.

The Learning Engine does not replace any existing component. It observes what they produce, analyzes what they reveal, and recommends what they could do better. It is the difference between a company that operates and a company that evolves.

---
