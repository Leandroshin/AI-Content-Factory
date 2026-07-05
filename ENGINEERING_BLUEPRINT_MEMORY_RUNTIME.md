# Engineering Blueprint — Memory Runtime

## Purpose

This document is the engineering blueprint for the `Memory Runtime` of the AI Company. It defines the architecture of the episodic and operational memory layer responsible for recording, indexing, searching, and retaining the company's complete history of events, decisions, conversations, executions, and state changes.

The Memory Runtime is the company's **record of what happened**. It does not evaluate, decide, learn, or execute. It stores the past so that every other component — the Decision Engine, the Learning Engine, the Conversation Runtime, and the AI Execution Runtime — can query it for context, audit, analysis, and recovery.

This blueprint translates the need for a durable, queryable, and policy-governed memory layer into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

**Why a Memory Runtime exists:**

The AI Company operates continuously, producing a constant stream of events — tasks assigned and completed, conversations held and resolved, decisions made and acted upon, policies evaluated and enforced, executions started and finished. Without a Memory Runtime, this history exists only in the transient state of individual components:

- The Decision Engine knows which decision it just made but forgets everything before that.
- The Conversation Runtime knows the current conversation but loses it when the session closes.
- The AI Execution Runtime knows the current execution but discards it upon completion.
- The Learning Engine knows the current cycle but archives it after analysis.

A Memory Runtime solves this by providing a single, durable, indexed, and policy-governed store for all historical records. It is the company's **episodic memory** — a complete, ordered, searchable account of everything that has happened.

**Why Memory is distinct from Knowledge:**

Knowledge represents validated organizational assets — completed results, stored documents, curated data, established policies. Knowledge is what the company **knows** to be true, useful, and durable. Knowledge is curated, versioned, and explicitly managed.

Memory represents the raw history of events — decisions made, conversations held, executions run, state transitions occurred. Memory is what the company **has experienced**. Memory is voluminous, time-ordered, append-only, and subject to retention policies.

| Aspect | Knowledge | Memory |
|--------|-----------|--------|
| Content | Validated assets, documents, policies | Event records, traces, histories |
| Mutability | Versioned updates, curated | Append-only, immutable |
| Lifespan | Indefinite (explicit deprecation) | Retention-policy governed (TTL) |
| Granularity | Coarse (documents, policies) | Fine (individual events, records) |
| Purpose | "What we know" | "What happened" |
| Consumer | Decision Engine, Employees | Learning Engine, Audit, Analytics |

---

## 1. Scope and Boundaries

### In Scope (What Belongs to the Memory Runtime)

- **Event Recording**: Capturing and storing structured records of every significant event across all components: decisions, executions, conversations, policy evaluations, state transitions, and system events.
- **Memory Indexing**: Building and maintaining searchable indexes over memory records by time, type, source, entity, and metadata.
- **Memory Searching**: Providing a query interface for searching, filtering, and retrieving memory records across multiple dimensions.
- **Timeline Construction**: Producing ordered timelines of events for a given scope (entity, session, execution, department, time range).
- **Memory Classification**: Tagging and categorizing memory records by type, severity, domain, and custom taxonomies for efficient retrieval.
- **Memory Compaction**: Merging, compressing, or summarizing old memory records to reduce storage footprint while preserving queryability.
- **Memory Archival**: Moving old memory records to long-term, lower-cost storage according to configurable policies.
- **Memory Recovery**: Restoring archived or compacted memory records on demand for audit or analysis.
- **Retention Policy Enforcement**: Applying configurable time-based, size-based, and type-based retention policies to automatically expire or archive records.
- **Relationship Graph**: Tracking and querying relationships between memory records (e.g., a decision record linked to the execution records it produced, linked to the conversation records that preceded it).
- **Snapshot Production**: Producing immutable `MemorySnapshot` objects containing point-in-time memory state for external consumers.
- **Checkpoint Management**: Creating and managing memory checkpoints for consistent point-in-time views across related records.
- **Metadata Management**: Per-record metadata for categorization, priority, tags, classification level, and custom attributes.

### Out of Scope (What Does NOT Belong to the Memory Runtime)

- **Knowledge Curation**: The Memory Runtime does not curate, validate, or version knowledge assets. Knowledge management belongs to the Knowledge Runtime.
- **Decision Making**: The Memory Runtime does not evaluate historical data to make decisions. Decision making belongs to the Decision Engine.
- **Learning and Improvement**: The Memory Runtime does not analyze history to detect patterns or generate recommendations. Learning belongs to the Learning Engine.
- **Conversation Management**: The Memory Runtime records conversation events but does not manage conversation state. Conversation management belongs to the Conversation Runtime.
- **Execution Orchestration**: The Memory Runtime records execution events but does not orchestrate execution. Orchestration belongs to the AI Execution Runtime.
- **Policy Evaluation**: The Memory Runtime records policy evaluation results but does not evaluate policies. Policy evaluation belongs to the Policy Engine.
- **Real-Time Processing**: The Memory Runtime is not designed for real-time event processing or streaming. It is an append-only store optimized for durable recording and efficient retrieval.
- **Primary Data Storage**: The Memory Runtime is not the primary data store for any component. Components maintain their own working state and publish records to memory for historical purposes.

---

## 2. Separation of Concerns

Memory management is split into four distinct layers that reflect the lifecycle of memory data:

```text
+-------------------------------------------------------------+
|                 Recording Layer                              |
|  (MemoryRuntime, MemoryRecord)                               |
|  Produces: immutable event records from component emissions  |
+---------------------------+---------------------------------+
                            | Records
                            v
+-------------------------------------------------------------+
|                 Storage and Indexing Layer                   |
|  (MemoryStore, MemoryIndex, MemoryClassification)            |
|  Produces: indexed, categorized, searchable memory store     |
+---------------------------+---------------------------------+
                            | Indexed Records
                            v
+-------------------------------------------------------------+
|                 Retrieval Layer                              |
|  (MemorySearch, MemoryTimeline, MemoryRelationshipGraph)     |
|  Produces: query results, timelines, relationship maps       |
+---------------------------+---------------------------------+
                            | Queries and Results
                            v
+-------------------------------------------------------------+
|                 Lifecycle Management Layer                   |
|  (MemoryRetentionPolicy, MemoryCompaction,                  |
|   MemoryArchive, MemoryRecovery, MemoryCheckpoint)           |
|  Manages: retention, compaction, archival, recovery          |
+-------------------------------------------------------------+
```

### Recording Layer
- **Responsibility**: Receive events from all components, validate them, transform them into standardized `MemoryRecord` objects, and write them to the store.
- **Knowledge**: Event schemas, record validation rules, source authentication.

### Storage and Indexing Layer
- **Responsibility**: Persist memory records, build and maintain indexes, apply classification tags, and manage storage efficiency.
- **Knowledge**: Index structures, classification taxonomies, storage backend capabilities.

### Retrieval Layer
- **Responsibility**: Accept search queries, traverse indexes, construct timelines, and resolve relationship graphs. Return results in a consistent format.
- **Knowledge**: Query syntax, index schemas, relationship mapping rules.

### Lifecycle Management Layer
- **Responsibility**: Enforce retention policies, compact old records, archive to long-term storage, and recover archived records on demand.
- **Knowledge**: Policy definitions, compaction strategies, archive backend configuration, recovery procedures.

---

## 3. Relationships and Interactions

The Memory Runtime is a passive consumer of events from all components and a queryable data source for analysis and audit:

```text
  AI Execution Runtime
        |
        +---> ExecutionCompleted event -------+
        |                                     |
  Conversation Runtime                        |
        |                                     |
        +---> SessionClosed event ------------+
        |                                     |
  Decision Engine                             |
        |                                     |
        +---> DecisionMade event -------------+
        |                                     |
  Policy Engine                               |
        |                                     |
        +---> PolicyEvaluated event ----------+
        |                                     |
  Learning Engine                             |
        |                                     |
        +---> CycleCompleted event -----------+
        |                                     v
        |                          +---------------------+
        |                          |    Memory Runtime    |
        |                          |                     |
        |                          |  Store, Index,      |
        |                          |  Classify, Compact   |
        +------------------------->|  Archive, Recover    |
                                   +----------+----------+
                                              |
                    +-------------------------+-------------------------+
                    |                         |                         |
                    v                         v                         v
          +-------------------+    +-------------------+    +-------------------+
          |  Learning Engine  |    |  Decision Engine  |    |  Observability    |
          |  (query history)  |    |  (query context)  |    |  (metrics/audit)  |
          +-------------------+    +-------------------+    +-------------------+
```

- **AI Execution Runtime**: Publishes execution lifecycle events (started, completed, failed). Memory records them for post-mortem analysis and audit.
- **Conversation Runtime**: Publishes conversation lifecycle events (session created, message sent, session closed). Memory records them for conversation history queries.
- **Decision Engine**: Publishes `DecisionMade` events with the decision context and outcome. Memory records them for decision audit trails.
- **Policy Engine**: Publishes `PolicyEvaluated` events with the policy context and verdict. Memory records them for policy effectiveness analysis.
- **Learning Engine**: Publishes learning cycle events. Also queries memory for historical patterns during the COLLECT and DETECT stages.
- **LLM Gateway**: Publishes provider communication events (request sent, response received, error occurred). Memory records them for cost tracking and provider performance analysis.
- **Observability Projector**: Consumes memory lifecycle events to track storage metrics, query latency, and retention efficiency.

---

## 4. Component Breakdown

The Memory Runtime is organized as a set of logical sub-components with clearly separated responsibilities:

```text
                    +--------------------------------+
                    |         MemoryRuntime           |
                    |  (Public Orchestration Entry)   |
                    +------+--------------+----------+
                           |              |
              +------------+------+  +----+------------+
              |  MemoryRecord     |  |  MemoryStore    |
              |  (Event → Record) |  |  (Persistence)  |
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |          MemoryIndex                |
              |  (Searchable Indexes)               |
              +------------+--------------+--------+
                           |              |
              +------------+------+  +----+------------+
              |  MemorySearch     |  |  MemoryTimeline |
              |  (Query Engine)   |  |  (Time-Ordered) |
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |    MemoryRelationshipGraph           |
              |  (Entity Relationship Mapping)       |
              +------------+--------------+--------+
                           |              |
              +------------+------+  +----+------------+
              |MemoryClassification|  |MemoryCheckpoint|
              | (Taxonomy Tags)    |  | (Point-in-Time)|
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |  MemoryRetentionPolicy              |
              |  (Lifecycle Rules)                   |
              +------------+--------------+--------+
                           |              |
              +------------+------+  +----+------------+
              |  MemoryCompaction |  |  MemoryArchive  |
              |  (Compression)    |  |  (Long-Term)    |
              +------------+------+  +----+------------+
                           |              |
              +------------+--------------+-------+
              |  MemoryRecovery      |  MemoryTrace  |
              |  (Restore from      |  (Audit Trail) |
              |   archive)           |                |
              +---------------------+----------------+
```

### 4.1 MemoryRuntime (Orchestration Entry Point)

- **Purpose**: Single public entry point for all memory operations. Receives events from all components, orchestrates recording, indexing, classification, and lifecycle enforcement.
- **Execution**: Stateless orchestrator for writes; delegates to sub-components for reads, search, and lifecycle management.
- **Public Interface** (conceptual):
  - `record(event: MemoryEvent) -> MemoryRecordID`: Receives an event from any component, validates it, transforms it into a `MemoryRecord`, and persists it.
  - `record_batch(events: list[MemoryEvent]) -> list[MemoryRecordID]`: Batch record for high-volume scenarios.
  - `get_record(record_id) -> MemoryRecord`: Retrieves a single record by ID.
  - `search(query: MemoryQuery) -> MemorySearchResult`: Executes a search against the memory index.
  - `get_timeline(entity_id, time_range, record_types) -> MemoryTimeline`: Constructs a time-ordered list of records for a given scope.
  - `get_relationships(record_id, depth) -> MemoryRelationshipGraph`: Returns the relationship graph for a record.
  - `get_snapshot(point_in_time) -> MemorySnapshot`: Returns a point-in-time snapshot of memory state.
  - `create_checkpoint(label, scope) -> CheckpointID`: Creates a memory checkpoint.
  - `compact(scope, strategy) -> CompactionResult`: Triggers compaction for old records.
  - `archive(scope) -> ArchiveResult`: Triggers archival for eligible records.
  - `recover(archive_id) -> RecoverResult`: Recovers archived records.
  - `get_metadata(record_id) -> MemoryMetadata`: Returns metadata for a record.

### 4.2 MemoryContext

- **Purpose**: Immutable snapshot of the contextual information surrounding a memory operation. Carries the reason, source, and environment for a record or query.
- **Structure** (conceptual):
  - `operation_id`: Unique identifier for the operation.
  - `source_component`: The component that triggered the operation (e.g., `AI_EXECUTION`, `CONVERSATION`, `DECISION_ENGINE`).
  - `source_entity_id`: The specific entity within the source component.
  - `correlation_id`: Links this memory operation to a broader workflow or execution.
  - `timestamp`: When the operation was initiated.
  - `metadata`: Additional context key-value pairs.
- **Immutability**: `MemoryContext` is fully frozen once created. It is attached to records and traces for audit.

### 4.3 MemoryRecord

- **Purpose**: The fundamental unit of memory. Every significant event in the company is captured as a `MemoryRecord`. Records are immutable, append-only, and uniquely identified.
- **Structure** (conceptual):
  - `record_id`: Unique identifier (UUID).
  - `record_type`: The type of event being recorded. See classification section for defined types.
  - `source_component`: The originating component.
  - `source_entity_id`: The entity within the source component that produced the event.
  - `timestamp`: ISO 8601 timestamp of when the event occurred.
  - `correlation_id`: Links this record to related records across components.
  - `parent_record_id`: Optional reference to a related record.
  - `payload`: The structured event data. Schema varies by `record_type`.
  - `classification`: `MemoryClassification` tags.
  - `metadata`: `MemoryMetadata` object.
  - `checksum`: SHA-256 hash of the payload for integrity verification.
- **Immutability**: Once written, a `MemoryRecord` is never modified, deleted, or overwritten. Corrections are written as new records with a reference to the corrected record via `parent_record_id`.
- **Record Types**:
  - `EXECUTION_STARTED`, `EXECUTION_COMPLETED`, `EXECUTION_FAILED`
  - `DECISION_MADE`, `DECISION_SKIPPED`
  - `POLICY_EVALUATED`, `POLICY_BLOCKED`
  - `CONVERSATION_CREATED`, `MESSAGE_SENT`, `CONVERSATION_CLOSED`
  - `LEARNING_CYCLE_STARTED`, `LEARNING_CYCLE_COMPLETED`
  - `LEARNING_RECOMMENDATION_ISSUED`, `LEARNING_RECOMMENDATION_CLOSED`
  - `LLM_REQUEST_SENT`, `LLM_RESPONSE_RECEIVED`, `LLM_ERROR`
  - `SKILL_EVOLVED`, `KNOWLEDGE_EVOLVED`
  - `STATE_TRANSITION`, `SYSTEM_EVENT`, `ERROR`

### 4.4 MemorySnapshot

- **Purpose**: Immutable, versioned, point-in-time frozen representation of the memory store's state. Used by the Decision Engine, Learning Engine, and Observability for consistent historical views.
- **Structure** (conceptual):
  - `snapshot_id`: Unique identifier.
  - `point_in_time`: The timestamp this snapshot represents.
  - `record_count`: Total number of records in the snapshot.
  - `time_range`: The time range covered (oldest and newest record timestamps).
  - `included_types`: List of record types included.
  - `checkpoint_id`: The checkpoint this snapshot is based on (if any).
  - `checksum`: SHA-256 hash for integrity.
  - `created_at`: When the snapshot was produced.
- **Immutability**: `MemorySnapshot` is fully frozen. It represents a consistent view of memory at a specific point in time.

### 4.5 MemoryIndex

- **Purpose**: Maintains searchable indexes over memory records to enable fast retrieval by time, type, source, entity, correlation_id, classification, and custom metadata.
- **Execution**: Updated asynchronously after records are written. Indexes are eventually consistent with the record store.
- **Index Types**:
  - **Time Index**: Ordered by timestamp. Supports range queries (before, after, between).
  - **Type Index**: Partitioned by `record_type`. Supports filtering by event type.
  - **Source Index**: Partitioned by `source_component`. Supports queries scoped to a component.
  - **Entity Index**: Partitioned by `source_entity_id`. Supports queries for a specific entity's history.
  - **Correlation Index**: Partitioned by `correlation_id`. Supports tracing a workflow across components.
  - **Classification Index**: Partitioned by classification tags. Supports queries by domain, severity, or custom labels.
  - **Full-Text Index**: Over `payload` content for text search (where applicable).
- **Key Operations**:
  - `index_record(record: MemoryRecord)`: Adds a record to all relevant indexes.
  - `index_batch(records: list[MemoryRecord])`: Batch indexing.
  - `rebuild_index(index_type)`: Rebuilds a specific index from the record store.
  - `query_index(query: IndexQuery) -> list[MemoryRecordID]`: Queries an index and returns matching record IDs.

### 4.6 MemoryStore (Conceptual Persistence)

- **Purpose**: The conceptual persistence layer for memory records. Defines the storage contract without committing to a specific backend. The store is append-only, immutable, and designed for write-heavy, read-occasional workloads.
- **Conceptual Interface**:
  - `write(record: MemoryRecord)`: Appends a record to the store.
  - `write_batch(records: list[MemoryRecord])`: Batch append.
  - `read(record_id) -> MemoryRecord`: Retrieves a record by ID.
  - `read_batch(record_ids) -> list[MemoryRecord]`: Batch retrieval.
  - `exists(record_id) -> bool`: Checks if a record exists.
  - `count(time_range, record_types) -> int`: Counts records matching criteria.
- **Backend Options** (not part of this blueprint):
  - Append-only log (e.g., Apache BookKeeper, Kafka).
  - Time-series database (e.g., InfluxDB, TimescaleDB).
  - Object store (e.g., S3, GCS) with index in a queryable database.
  - Embedded store (e.g., SQLite) for single-node deployments.
- **Storage Characteristics**:
  - Write-optimized: Writes must be fast and never block readers.
  - Append-only: Records are never updated or deleted.
  - Durable: Acknowledged writes survive process crashes.
  - Ordered: Records within a partition maintain insertion order.

### 4.7 MemoryCheckpoint

- **Purpose**: Creates a consistent, named point-in-time marker in the memory store. Checkpoints enable granular recovery, consistent snapshots, and bounded compaction.
- **Structure** (conceptual):
  - `checkpoint_id`: Unique identifier.
  - `label`: Human-readable label.
  - `point_in_time`: The timestamp of the checkpoint.
  - `record_count`: Number of records up to this checkpoint.
  - `last_record_id`: The ID of the last record included in this checkpoint.
  - `scope`: The scope of this checkpoint (GLOBAL, or scoped to a component or entity).
  - `metadata`: Key-value metadata.
  - `created_at`: When the checkpoint was created.
- **Key Operations**:
  - `create_checkpoint(label, scope, metadata) -> CheckpointID`
  - `get_checkpoint(checkpoint_id) -> MemoryCheckpoint`
  - `list_checkpoints(scope, limit) -> list[MemoryCheckpoint]`
  - `delete_checkpoint(checkpoint_id)`
- **Usage**: Checkpoints are used by the `MemoryCompaction` component to define compaction boundaries (only records before a checkpoint may be compacted). They are also used by `MemorySnapshot` to define consistent point-in-time views.

### 4.8 MemoryTimeline

- **Purpose**: Constructs time-ordered sequences of memory records for a given scope. Timelines are the primary mechanism for understanding "what happened" in a specific context.
- **Execution**: Stateless per query. Reads from indexes and assembles records into ordered sequences.
- **Key Operations**:
  - `get_timeline(entity_id, time_range, record_types, limit, offset) -> MemoryTimeline`
  - `get_timeline_by_correlation(correlation_id, record_types) -> MemoryTimeline`
  - `aggregate_timeline(timeline, interval, aggregation_fn) -> AggregatedTimeline`
- **Timeline Structure**:
  - `entity_id`: The scope of this timeline.
  - `time_range`: The covered time range.
  - `records`: Ordered list of `MemoryRecord` objects (oldest first).
  - `total_count`: Total matching records (for pagination).
  - `aggregations`: Optional aggregated data (count by type, interval, etc.).

### 4.9 MemorySearch

- **Purpose**: Provides a flexible query interface for searching memory records across multiple dimensions.
- **Execution**: Stateless per query. Translates query predicates into index lookups and returns matching records.
- **Query Capabilities**:
  - **Time Range**: `before`, `after`, `between`.
  - **Record Type**: Filter by one or more record types.
  - **Source**: Filter by source component and entity.
  - **Correlation**: Filter by correlation_id.
  - **Classification**: Filter by classification tags, domain, severity.
  - **Metadata**: Filter by metadata key-value pairs.
  - **Full-Text**: Search within record payloads (where indexed).
  - **Pagination**: `limit`, `offset`, `sort_order` (ascending, descending).
  - **Aggregation**: `group_by`, `count`, `histogram` over time.
- **Query Structure** (conceptual):
  - `query`: Query predicates.
  - `filters`: Combined filter criteria.
  - `sort`: Sort field and order.
  - `pagination`: Limit and offset.
  - `aggregations`: Optional aggregation specifications.
- **Result Structure**:
  - `total_matches`: Total records matching the query.
  - `records`: List of matching records (paginated).
  - `aggregations`: Aggregated results (if requested).
  - `query_duration_ms`: Query execution time.

### 4.10 MemoryRetentionPolicy

- **Purpose**: Defines rules governing how long memory records are retained, when they are compacted, and when they are archived or deleted.
- **Structure** (conceptual):
  - `policy_id`: Unique identifier.
  - `scope`: `GLOBAL`, `BY_RECORD_TYPE`, `BY_SOURCE`, `BY_CLASSIFICATION`.
  - `conditions`: The conditions that trigger policy evaluation.
  - `actions`: The actions to take when conditions are met.
  - `priority`: Evaluation priority when multiple policies match.
  - `enabled`: Whether this policy is active.
  - `created_at`, `updated_at`.
- **Built-in Policies**:
  - **Default Retention**: All records retained for 90 days, then eligible for archival.
  - **Execution Records**: Retained for 30 days in primary store, then compacted.
  - **Decision Records**: Retained for 365 days for audit purposes.
  - **Conversation Records**: Retained for 90 days, then archived.
  - **Error Records**: Retained for 180 days for debugging.
  - **System Events**: Retained for 30 days, then eligible for deletion.
  - **Learning Records**: Retained for 365 days for trend analysis.
- **Retention Actions**:
  - `NONE`: No action (retain indefinitely).
  - `COMPACT`: Compress or summarize the record.
  - `ARCHIVE`: Move to long-term storage.
  - `DELETE`: Permanently remove (only for low-value system events).
  - `NOTIFY`: Alert an operator that retention limits are approaching.

### 4.11 MemoryClassification

- **Purpose**: Categorizes and tags memory records with a consistent taxonomy for efficient filtering, search, and lifecycle management.
- **Structure** (conceptual):
  - `domain`: The operational domain (`EXECUTION`, `DECISION`, `CONVERSATION`, `POLICY`, `LEARNING`, `SYSTEM`, `LLM`).
  - `severity`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
  - `category`: Domain-specific category (e.g., for EXECUTION: `STARTED`, `COMPLETED`, `FAILED`, `RETRIED`).
  - `tags`: Custom string tags for flexible categorization.
  - `security_level`: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.
- **Key Operations**:
  - `classify(record: MemoryRecord) -> MemoryClassification`: Auto-classifies a record based on its type, source, and payload.
  - `reclassify(record_id, new_classification)`: Updates a record's classification (rare, used for corrections).
  - `get_classification_schema() -> dict`: Returns the classification taxonomy.

### 4.12 MemoryRelationshipGraph

- **Purpose**: Tracks and queries relationships between memory records. Enables tracing causality across components: which decision led to which execution, which conversation preceded which policy evaluation.
- **Execution**: Relationships are inferred at record time based on `correlation_id`, `parent_record_id`, and payload references. The graph is queryable at any depth.
- **Relationship Types**:
  - `CAUSED`: Record A caused Record B (e.g., a decision caused an execution).
  - `PRECEDED`: Record A happened before Record B in the same workflow.
  - `RESPONDED_TO`: Record B is a response to Record A (e.g., LLM response to a request).
  - `REFERENCES`: Record A references Record B (e.g., a learning recommendation references an execution record).
  - `CORRELATED`: Records A and B share the same correlation_id.
  - `CORRECTS`: Record B corrects Record A (via parent_record_id).
- **Key Operations**:
  - `get_relationships(record_id, depth, relationship_types) -> MemoryRelationshipGraph`: Returns the graph of relationships for a record up to a configurable depth.
  - `traverse(start_record_id, relationship_type, direction, max_depth) -> list[MemoryRecord]`: Traverses the graph along a specific relationship type.
  - `get_related_records(correlation_id) -> list[MemoryRecord]`: Returns all records sharing a correlation_id.

### 4.13 MemoryTrace

- **Purpose**: Records every operation performed by the Memory Runtime for audit, debugging, and observability. Each trace captures the operation, its inputs, outputs, duration, and any errors.
- **Structure** (conceptual):
  - `trace_id`: Unique identifier.
  - `operation`: The operation performed (`RECORD`, `SEARCH`, `TIMELINE`, `COMPACT`, `ARCHIVE`, `RECOVER`, `CHECKPOINT`).
  - `context`: The `MemoryContext` for this operation.
  - `input_summary`: Summary of operation inputs.
  - `output_summary`: Summary of operation outputs.
  - `duration_ms`: Operation duration.
  - `record_count`: Number of records affected.
  - `errors`: List of errors encountered.
  - `started_at`, `completed_at`.
- **Visibility**: Traces are stored in-memory for active debugging and may be persisted as memory records for long-term audit.

### 4.14 MemoryMetadata

- **Purpose**: Per-record metadata providing context, routing hints, and categorization without affecting the record payload.
- **Structure** (conceptual):
  - `source_version`: Version of the source component that produced the record.
  - `environment`: Deployment environment (`PRODUCTION`, `STAGING`, `DEVELOPMENT`).
  - `tags`: Custom string tags for flexible categorization.
  - `custom`: Dictionary of arbitrary key-value pairs for extensibility.
  - `references`: List of external reference IDs.
  - `ttl_extension`: Optional extension to the default retention period.
  - `immutable_flag`: Always True for standard records. Set False only for transient metadata records.

### 4.15 MemoryCompaction

- **Purpose**: Reduces storage footprint of old memory records by merging, compressing, or summarizing them while preserving queryability.
- **Execution**: Asynchronous. Triggered by retention policy or manual request. Operates on records before a checkpoint boundary.
- **Compaction Strategies**:
  1. **Summarization**: Replaces a sequence of related records (e.g., 100 execution progress events) with a single summary record containing aggregate statistics (count, duration, outcome distribution).
  2. **Merging**: Combines multiple related records into a single record with merged payloads. Useful for records with the same correlation_id and type.
  3. **Payload Truncation**: Removes verbose payload fields while retaining metadata, timestamps, and classification. Useful for debug-level records.
  4. **Rollup**: Aggregates records by time interval (hourly, daily) and stores only the aggregate. Original records are archived.
- **Key Operations**:
  - `compact(scope, strategy, checkpoint_id) -> CompactionResult`: Compacts records before the specified checkpoint using the specified strategy.
  - `get_compaction_status(compaction_id) -> CompactionStatus`
  - `undo_compaction(compaction_id)`: Reverses a compaction (only possible if source records were archived, not deleted).
- **Compaction Result**:
  - `compaction_id`, `strategy`, `records_before`, `records_after`, `bytes_freed`, `duration_ms`, `checkpoint_id`, `original_records_archived`.

### 4.16 MemoryRecovery

- **Purpose**: Restores memory records from archival storage or reverses compaction when records are needed for audit, analysis, or debugging.
- **Execution**: On-demand. Triggered by user request or automated query that requires archived data.
- **Key Operations**:
  - `recover(archive_reference) -> RecoverResult`: Recovers a specific archived record or batch.
  - `recover_by_query(query: MemoryQuery) -> RecoverResult`: Recovers all records matching a query from archival.
  - `get_recover_status(recover_id) -> RecoverStatus`
- **Recovery Modes**:
  - `FULL`: Recovers the complete original records.
  - `METADATA_ONLY`: Recovers only metadata and classification (not payload). Faster.
  - `SUMMARY`: Recovers only the summary version (if compaction used summarization).
- **Recover Result**:
  - `recover_id`, `records_recovered`, `bytes_restored`, `duration_ms`, `archive_source`.

### 4.17 MemoryArchive

- **Purpose**: Manages the lifecycle of archived memory records. Moves eligible records from the primary store to long-term, lower-cost storage according to retention policies.
- **Execution**: Asynchronous. Triggered by retention policy or manual request.
- **Key Operations**:
  - `archive(scope, checkpoint_id) -> ArchiveResult`: Archives all records before the specified checkpoint that are eligible for archival.
  - `get_archive_status(archive_id) -> ArchiveStatus`
  - `list_archives(scope, limit) -> list[ArchiveMetadata]`
  - `delete_archive(archive_id)`: Permanently removes an archive.
- **Archive Storage**: Archives are stored in a separate backend (conceptual). Each archive contains:
  - `archive_id`, `scope`, `checkpoint_id`, `record_count`, `size_bytes`, `time_range`, `compression_format`, `storage_location`, `created_at`, `checksum`.

---

## 5. Memory Lifecycle

Every memory record follows a fixed lifecycle from creation to eventual deletion or indefinite retention:

### Lifecycle Diagram

```text
  Event Published
        |
        v
  +----------+       +-----------+       +----------+
  | RECORDED |------>| INDEXED   |------>| CLASSIFIED|
  | (written |       | (added to |       | (tagged)  |
  |  to store)|       |  indexes) |       |           |
  +----------+       +-----------+       +----------+
        |
        | (retention policy evaluation)
        v
  +----------+       +-----------+       +----------+
  | COMPACT  |<------| ACTIVE    |------>| ARCHIVED |
  | (if elig)|       | (default) |       | (if elig)|
  +----------+       +-----------+       +----------+
        |                                    |
        v                                    v
  +----------+       +-----------+       +----------+
  | DELETED  |       | RECOVERED |<------| ARCHIVED |
  | (permanent)|     | (on demand)|       | (storage)|
  +----------+       +-----------+       +----------+
```

### Stage 1: RECORDED
- **Trigger**: An event is published by any component and received by `MemoryRuntime.record()`.
- **Action**: The event payload is validated, transformed into a `MemoryRecord`, assigned a unique ID, timestamped, and written to the `MemoryStore`.
- **Failure Mode**: If writing fails, the error is logged and the component that published the event is notified via the EventBus.
- **Performance Target**: < 10 ms per record, < 100 ms for batch of 100.

### Stage 2: INDEXED
- **Trigger**: Record written successfully.
- **Action**: The record is added to all relevant `MemoryIndex` instances (time, type, source, entity, correlation, classification).
- **Consistency**: Index updates are eventually consistent. There is a configurable delay between write and index availability (default: < 100 ms).
- **Failure Mode**: If indexing fails, the record is still available by direct ID lookup. Index rebuild can be triggered manually.

### Stage 3: CLASSIFIED
- **Trigger**: Record indexed.
- **Action**: The `MemoryClassification` component applies taxonomy tags based on record type, source, and payload. Tags are added to the classification index.
- **Performance Target**: < 5 ms per record.

### Stage 4: ACTIVE
- **Trigger**: Classification complete.
- **Action**: The record remains in the primary store and all indexes. It is queryable by all retrieval components.
- **Duration**: Until a retention policy triggers compaction, archival, or deletion.

### Stage 5: COMPACT (if eligible)
- **Trigger**: A retention policy with `COMPACT` action matches the record, and a compaction checkpoint has been created.
- **Action**: The `MemoryCompaction` component applies the configured strategy. Original records are either archived or replaced by a summary.
- **Output**: Compaction result with metrics.

### Stage 6: ARCHIVED (if eligible)
- **Trigger**: A retention policy with `ARCHIVE` action matches the record.
- **Action**: The `MemoryArchive` component moves the record to long-term storage. The record is removed from the primary store but remains queryable through the archive index.
- **Output**: Archive result with storage location.

### Stage 7: DELETED (if eligible)
- **Trigger**: A retention policy with `DELETE` action matches the record (only for low-value system events).
- **Action**: The record is permanently removed from the primary store and all indexes. It is NOT recoverable.
- **Warning**: Deletion is irreversible and only applies to explicitly configured record types.

### Stage 8: RECOVERED (on demand)
- **Trigger**: A user or component requests recovery of archived records via `MemoryRecovery.recover()`.
- **Action**: The archived records are located, decompressed (if needed), and loaded into the primary store. They are re-indexed and become queryable again.
- **Output**: Recovery result with metrics.

---

## 6. Event Model

The Memory Runtime both consumes events from other components and publishes its own lifecycle events.

### 6.1 Consumed Events

| Source Event | Source Component | Record Type |
|-------------|-----------------|-------------|
| `ExecutionStarted` | AI Execution Runtime | `EXECUTION_STARTED` |
| `ExecutionCompleted` | AI Execution Runtime | `EXECUTION_COMPLETED` |
| `ExecutionFailed` | AI Execution Runtime | `EXECUTION_FAILED` |
| `DecisionMade` | Decision Engine | `DECISION_MADE` |
| `DecisionSkipped` | Decision Engine | `DECISION_SKIPPED` |
| `PolicyEvaluated` | Policy Engine | `POLICY_EVALUATED` |
| `PolicyBlocked` | Policy Engine | `POLICY_BLOCKED` |
| `SessionCreated` | Conversation Runtime | `CONVERSATION_CREATED` |
| `MessageSent` | Conversation Runtime | `MESSAGE_SENT` |
| `SessionClosed` | Conversation Runtime | `CONVERSATION_CLOSED` |
| `CycleStarted` | Learning Engine | `LEARNING_CYCLE_STARTED` |
| `CycleCompleted` | Learning Engine | `LEARNING_CYCLE_COMPLETED` |
| `RecommendationIssued` | Learning Engine | `RECOMMENDATION_ISSUED` |
| `RecommendationClosed` | Learning Engine | `RECOMMENDATION_CLOSED` |
| `LLMRequestSent` | LLM Gateway | `LLM_REQUEST_SENT` |
| `LLMResponseReceived` | LLM Gateway | `LLM_RESPONSE_RECEIVED` |
| `LLMError` | LLM Gateway | `LLM_ERROR` |

### 6.2 Published Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `MemoryRecordWritten` | record() completes | record_id, record_type, source_component, timestamp |
| `MemoryBatchWritten` | record_batch() completes | record_count, first_id, last_id, duration_ms |
| `MemorySearchCompleted` | search() completes | query_hash, total_matches, duration_ms |
| `MemoryTimelineConstructed` | get_timeline() completes | entity_id, record_count, time_range, duration_ms |
| `MemoryCheckpointCreated` | create_checkpoint() | checkpoint_id, label, scope, record_count |
| `MemoryCheckpointDeleted` | delete_checkpoint() | checkpoint_id |
| `MemoryCompactStarted` | compact() starts | compaction_id, strategy, records_targeted |
| `MemoryCompactCompleted` | compact() completes | compaction_id, records_before, records_after, bytes_freed |
| `MemoryArchiveStarted` | archive() starts | archive_id, scope, records_targeted |
| `MemoryArchiveCompleted` | archive() completes | archive_id, record_count, size_bytes, storage_location |
| `MemoryRecoverStarted` | recover() starts | recover_id, records_targeted |
| `MemoryRecoverCompleted` | recover() completes | recover_id, records_recovered, duration_ms |
| `MemoryRetentionEnforced` | policy evaluation | policy_id, records_affected, action_taken |
| `MemorySnapshotCreated` | get_snapshot() | snapshot_id, point_in_time, record_count |
| `MemoryError` | operation failure | operation, error_code, error_message |

---

## 7. Integration with Conversation Runtime

### 7.1 Memory as Conversation History

The Conversation Runtime publishes session and message events that the Memory Runtime records. This provides a durable, queryable history of every conversation:
- `CONVERSATION_CREATED`: Session metadata, participants, session type.
- `MESSAGE_SENT`: Message content, sender, type, timestamp, token count.
- `CONVERSATION_CLOSED`: Session duration, message count, outcome.

### 7.2 Conversation Timeline Queries

The Conversation Runtime may query memory for conversation timelines:
- "Show me all messages in session X in chronological order."
- "Show me all conversations involving employee Y in the last 7 days."
- "Show me all conversations that led to an execution of task type Z."

### 7.3 No Conversation State Duplication

The Memory Runtime stores conversation history as memory records but does not maintain conversation state. Active conversation state belongs to the Conversation Runtime. Memory is a historical record, not a live state store.

---

## 8. Integration with Learning Engine

### 8.1 Memory as Learning Input

The Learning Engine queries memory during the COLLECT and DETECT stages:
- **COLLECT**: The Learning Engine queries memory for historical execution outcomes, past pattern occurrences, and recommendation history.
- **DETECT**: The PatternDetector queries memory for time-series data to detect trends, anomalies, and recurring patterns.

### 8.2 Learning Recommendations as Memory Records

Every learning recommendation issued by the Learning Engine is recorded as a memory record (`RECOMMENDATION_ISSUED`). When recommendations are acknowledged or closed, those events are also recorded (`RECOMMENDATION_CLOSED`). This creates a complete audit trail of the learning process.

### 8.3 Memory-Based Pattern Detection Support

The `PatternDetector` in the Learning Engine relies on memory for:
- **Execution History**: Past execution outcomes for skill performance analysis.
- **Policy Block History**: Past policy blocks for blocking pattern analysis.
- **Feedback History**: Past feedback submissions for trend analysis.
- **Cost History**: Past execution costs for cost anomaly detection.

---

## 9. Integration with Knowledge Runtime

### 9.1 Knowledge Evolution as Memory Records

When the Knowledge Runtime creates, updates, or deprecates knowledge assets, it publishes events that the Memory Runtime records as `KNOWLEDGE_EVOLVED` records. This creates a complete history of knowledge evolution.

### 9.2 Knowledge Usage Tracking

Memory records of execution events and conversation events can be queried to determine which knowledge assets were referenced, how often, and in what context. This data feeds into the Learning Engine's knowledge gap detection.

### 9.3 Complementary Roles

Memory and Knowledge serve complementary roles:
- **Memory** records that knowledge asset X was referenced in execution Y at time Z.
- **Knowledge** stores the actual content of knowledge asset X.
- Memory provides the usage context; Knowledge provides the content.

---

## 10. Integration with Decision Engine

### 10.1 Memory as Decision Context

The Decision Engine may optionally query memory for historical context when making decisions:
- "What happened the last time we assigned a task of this type to this employee?"
- "What was the outcome of similar decisions made last week?"
- "Which providers were used for similar tasks and what were their success rates?"

### 10.2 Decision Records as Audit Trail

Every decision made by the Decision Engine is recorded as a `DECISION_MADE` memory record. The record includes:
- The decision context (task, candidates considered, constraints evaluated).
- The decision outcome (selected candidate, priority, routing path).
- The decision code (`BEST_SKILL_MATCH`, `NO_SKILL_MATCH`, etc.).

This creates a complete, queryable audit trail of every decision the company has ever made.

### 10.3 No Decision Engine Modification

The Decision Engine never writes to memory directly. It publishes events that the Memory Runtime consumes. The Decision Engine does not need to know about the Memory Runtime's existence.

---

## 11. Integration with AI Execution Runtime

### 11.1 Execution Records

Every execution lifecycle event is recorded:
- `EXECUTION_STARTED`: Task ID, employee ID, skill used, provider selected.
- `EXECUTION_COMPLETED`: Outcome, duration, tokens, cost, quality score.
- `EXECUTION_FAILED`: Error reason, retry count, failure stage.

### 11.2 Execution Timeline Reconstruction

Memory enables full execution timeline reconstruction:
- The `EXECUTION_STARTED` record establishes the beginning.
- Interleaved `MESSAGE_SENT` records capture communications during execution.
- `LLM_REQUEST_SENT` and `LLM_RESPONSE_RECEIVED` records capture provider interactions.
- `EXECUTION_COMPLETED` or `EXECUTION_FAILED` records mark the end.

### 11.3 Post-Mortem Analysis

After an execution failure, the complete timeline can be reconstructed from memory records for post-mortem analysis without requiring the AI Execution Runtime to retain any state about the completed execution.

---

## 12. Integration with LLM Gateway

### 12.1 Provider Communication Records

Every LLM request and response is recorded:
- `LLM_REQUEST_SENT`: Provider, model, prompt summary, token count, cost estimate, timestamp.
- `LLM_RESPONSE_RECEIVED`: Response summary, token count, actual cost, latency, timestamp.
- `LLM_ERROR`: Provider, error type, error message, retry count, timestamp.

### 12.2 Cost and Performance Analysis

Memory records of LLM communications enable:
- Per-provider cost aggregation.
- Per-model latency analysis.
- Per-employee LLM usage tracking.
- Error rate monitoring per provider.

### 12.3 No LLM Gateway Modification

The LLM Gateway publishes events that the Memory Runtime consumes. The Gateway does not need to know about the Memory Runtime.

---

## 13. Integration with EventBus

### 13.1 Consumer Role

The Memory Runtime is a consumer of events published by all other components. It subscribes to event types listed in section 6.1.

### 13.2 Publisher Role

The Memory Runtime publishes lifecycle events (section 6.2) for observability, monitoring, and cross-component notification.

### 13.3 Event Consumption Contract

- The Memory Runtime expects at-least-once delivery. Duplicate events are handled via idempotency checks on `record_id` (derived from the source event's ID).
- Events are consumed asynchronously. The Memory Runtime does not block event publishers.
- Event processing order is guaranteed per source entity (events from the same entity are processed in order).

### 13.4 Event Publishing Contract

- Events are published after state changes are committed.
- Events are fire-and-forget.
- Events are immutable and idempotent.

---

## 14. Integration with Observability

### 14.1 Observable Metrics

The Memory Runtime exposes the following metrics through the Observability Projector:

| Metric | Type | Labels |
|--------|------|--------|
| `memory.records.written` | Counter | record_type, source_component |
| `memory.records.written.batch_size` | Histogram | — |
| `memory.records.total` | Gauge | record_type |
| `memory.search.executed` | Counter | — |
| `memory.search.latency` | Histogram | — |
| `memory.search.total_matches` | Histogram | — |
| `memory.timeline.executed` | Counter | — |
| `memory.timeline.latency` | Histogram | — |
| `memory.compaction.executed` | Counter | strategy |
| `memory.compaction.bytes_freed` | Histogram | strategy |
| `memory.archive.executed` | Counter | — |
| `memory.archive.record_count` | Histogram | — |
| `memory.recovery.executed` | Counter | — |
| `memory.recovery.duration` | Histogram | — |
| `memory.retention.enforced` | Counter | action |
| `memory.store.size_bytes` | Gauge | — |
| `memory.store.record_count` | Gauge | — |
| `memory.operation.errors` | Counter | operation, error_code |

### 14.2 Traceability

Every memory operation produces a trace context that is propagated through events and logged:
- `operation_id`: Unique operation identifier.
- `operation`: The operation type.
- `duration_ms`: Operation duration.
- `record_count`: Number of records affected.
- `error`: Error details if the operation failed.

### 14.3 Audit Trail

The Memory Runtime itself produces audit records (`MemoryTrace`) for all write operations (record, compact, archive, recover). These traces are stored in-memory for active debugging and may be persisted as memory records for long-term audit.

---

## 15. Data Model

```text
  +------------------------------------+
  |          MemoryRecord               |
  +------------------------------------+
  | record_id: UUID                    |
  | record_type: Enum                  |
  | source_component: string           |
  | source_entity_id: string           |
  | timestamp: ISO8601                 |
  | correlation_id: UUID (optional)    |
  | parent_record_id: UUID (optional)  |
  | payload: dict (schema by type)     |
  | classification: MemoryClassification|
  | metadata: MemoryMetadata           |
  | checksum: string (SHA-256)         |
  +------------------------------------+

  +------------------------------------+
  |       MemoryClassification          |
  +------------------------------------+
  | domain: Enum                       |
  | severity: Enum                     |
  | category: string                   |
  | tags: list[string]                 |
  | security_level: Enum               |
  +------------------------------------+

  +------------------------------------+
  |         MemoryMetadata              |
  +------------------------------------+
  | source_version: string             |
  | environment: string                |
  | tags: list[string]                 |
  | custom: dict                       |
  | references: list[string]           |
  | ttl_extension: int (optional)      |
  +------------------------------------+

  +------------------------------------+
  |        MemoryCheckpoint             |
  +------------------------------------+
  | checkpoint_id: UUID                |
  | label: string                      |
  | point_in_time: ISO8601             |
  | record_count: int                  |
  | last_record_id: UUID               |
  | scope: Enum                        |
  | metadata: dict                     |
  | created_at: ISO8601                |
  +------------------------------------+

  +------------------------------------+
  |        MemorySnapshot               |
  +------------------------------------+
  | snapshot_id: UUID                  |
  | point_in_time: ISO8601             |
  | record_count: int                  |
  | time_range: (ISO8601, ISO8601)     |
  | included_types: list[Enum]         |
  | checkpoint_id: UUID (optional)     |
  | checksum: string (SHA-256)         |
  | created_at: ISO8601                |
  +------------------------------------+
```

---

## 16. Policies

### 16.1 Retention Policies

| Policy | Scope | Action | Default |
|--------|-------|--------|---------|
| Standard Retention | All records | ARCHIVE after 90 days | Enabled |
| Execution Trace | EXECUTION_* | COMPACT after 30 days | Enabled |
| Decision Audit | DECISION_* | ARCHIVE after 365 days | Enabled |
| Conversation History | CONVERSATION_*, MESSAGE_* | ARCHIVE after 90 days | Enabled |
| Error Records | * with severity = ERROR | ARCHIVE after 180 days | Enabled |
| System Events | SYSTEM_* | DELETE after 30 days | Enabled |
| Learning History | LEARNING_*, RECOMMENDATION_* | ARCHIVE after 365 days | Enabled |
| LLM Communication | LLM_* | COMPACT after 60 days | Enabled |

### 16.2 Write Policies

- **Durability**: All writes must be acknowledged by the storage backend before returning to the caller.
- **Ordering**: Records from the same source entity must be written in the order they were produced.
- **Idempotency**: Duplicate events (same event_id) must not create duplicate records. Deduplication is based on the source event ID.
- **Rate Limiting**: Per-component write rate limits prevent any single component from overwhelming the store.

### 16.3 Query Policies

- **Pagination**: All search queries must support pagination with configurable page size (default: 100, max: 1000).
- **Time Bounds**: Queries without time bounds are rejected if they would scan more than 1,000,000 records.
- **Rate Limiting**: Per-consumer query rate limits prevent abusive queries from degrading store performance.

### 16.4 Isolation Policy

- Memory records are globally visible. Any component may query any record. Classification and security_level tags enable consumer-side filtering.
- Retention policies apply globally by default but can be scoped to specific record types or source components.

---

## 17. Versioning and Auditability

### 17.1 Record Versioning

Memory records are immutable. There is no version number — each record is written once and never modified. Corrections are created as new records with a `parent_record_id` referencing the corrected record.

### 17.2 Checkpoint Versioning

Checkpoints are versioned per scope. Each new checkpoint for a given scope has a monotonically increasing sequence number.

### 17.3 Snapshot Versioning

Each `MemorySnapshot` has a unique `snapshot_id` and a `point_in_time`. Consumers can compare snapshots by their `point_in_time` to determine which is more recent.

### 17.4 Audit Trail

- Every record write is logged in `MemoryTrace`.
- Every compaction, archive, and recovery operation is logged.
- Every checkpoint creation and deletion is logged.
- The trace store itself is queryable for debugging and compliance.

### 17.5 Checksum Integrity

Every `MemoryRecord` includes a `checksum` (SHA-256 of the serialized payload). Every `MemorySnapshot` includes a `checksum` of its contents. Consumers may verify integrity by recomputing the checksum.

---

## 18. Implementation Roadmap

### Phase 1: Core Recording

- MemoryRuntime with `record()` and basic event consumption.
- MemoryRecord data structure and validation.
- MemoryStore conceptual implementation (in-memory first).
- Basic indexing by record_id and timestamp.
- **Dependency**: EventBus (for consuming events).

### Phase 2: Search and Retrieval

- MemoryIndex with time, type, source, and entity indexes.
- MemorySearch with filter and pagination support.
- MemoryTimeline construction.
- **Dependency**: MemoryStore (Phase 1).

### Phase 3: Classification and Relationships

- MemoryClassification with taxonomy definition and auto-tagging.
- MemoryRelationshipGraph with correlation-based relationship inference.
- MemoryMetadata support.
- **Dependency**: MemoryIndex (Phase 2).

### Phase 4: Checkpoints and Snapshots

- MemoryCheckpoint creation and management.
- MemorySnapshot production.
- **Dependency**: MemoryStore (Phase 1).

### Phase 5: Retention and Lifecycle

- MemoryRetentionPolicy definition and evaluation engine.
- Automated policy enforcement on a scheduled basis.
- **Dependency**: MemoryCheckpoint (Phase 4).

### Phase 6: Compaction and Archival

- MemoryCompaction with summarization and merging strategies.
- MemoryArchive with configurable storage backend.
- **Dependency**: MemoryRetentionPolicy (Phase 5).

### Phase 7: Recovery

- MemoryRecovery for on-demand record restoration.
- Recovery from archive with re-indexing.
- **Dependency**: MemoryArchive (Phase 6).

### Phase 8: Event Publishing and Observability

- Full event catalog implementation.
- Integration with Observability Projector.
- Metrics, tracing, and audit trail completeness.
- **Dependency**: EventBus, Observability Projector.

---

## 19. Validation

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Memory is separate from Knowledge | Knowledge is curated, versioned, and semantically meaningful. Memory is raw, voluminous, and time-ordered. Different storage characteristics, access patterns, and lifecycle requirements. Combining them would optimize for neither. |
| Records are immutable and append-only | Immutability guarantees audit integrity, simplifies concurrency (no locks on writes), and enables idempotent event consumption. |
| Indexes are eventually consistent | Prioritizes write speed over read consistency. Memory is queried less often than it is written. Eventual consistency (sub-second) is acceptable for historical queries. |
| Retention is policy-driven and automated | Manual memory management does not scale. Automated policies with configurable rules ensure predictable storage usage without operator intervention. |
| Compaction preserves queryability | Summarized records retain the key information needed for analysis. Full detail is archived for on-demand recovery. |
| The Memory Runtime never blocks event producers | Memory is a passive consumer. Components continue operating whether or not memory is available. |
| Classification uses a flat taxonomy with tags | Flat taxonomies are simpler to maintain and query than deep hierarchies. Tags provide flexible categorization without schema changes. |

### Technical Justification

The Memory Runtime exists because no other component provides durable, queryable, policy-governed storage for the company's operational history. Each component focuses on its primary responsibility:

- The **AI Execution Runtime** focuses on executing tasks. It discards execution state upon completion.
- The **Conversation Runtime** focuses on live conversation state. It closes and discards sessions.
- The **Decision Engine** focuses on making decisions. It retains only the current decision context.
- The **Learning Engine** focuses on pattern analysis. It retains cycles temporarily for analysis.

Without a Memory Runtime, historical data exists only in ephemeral component state and scattered log files. This prevents:
- **Cross-component audit**: Tracing a decision through its execution, conversations, and outcomes requires records from three components that do not share a common store.
- **Historical analysis**: Detecting long-term trends requires data spanning days or weeks, which no component retains.
- **Post-mortem debugging**: Understanding a failure requires reconstructing events that occurred across multiple components, none of which retain the full picture.
- **Compliance and governance**: Many use cases require proving what happened at a specific point in time. Without an immutable, queryable record, this is impossible.

By centralizing operational history in a dedicated Memory Runtime, the architecture gains:
- **Single source of truth for history**: Every event from every component is recorded in one place.
- **Consistent retention governance**: All records follow the same policy framework.
- **Cross-component queries**: A single query can span execution, decision, conversation, and policy records.
- **Immutable audit trail**: Records cannot be modified or deleted (except by explicit, audited lifecycle policies).

### Risks

1. **Storage Growth**: Memory records accumulate continuously. Without proper compaction and archival, storage costs grow unbounded. Mitigation: aggressive default retention policies, automated compaction at configurable thresholds.
2. **Write Throughput Bottleneck**: All components write to the same store. At high event volumes (10,000+ events/second), the store may become a bottleneck. Mitigation: batch writes, asynchronous indexing, shardable store design.
3. **Query Performance Degradation**: As the record count grows, queries may become slow. Mitigation: targeted indexes, time-bounded queries, pagination limits, compaction of old records.
4. **Event Loss on Bus Failure**: If the EventBus fails, events may be lost before the Memory Runtime consumes them. Mitigation: components should retain events until acknowledged; the Memory Runtime should support catch-up on reconnection.
5. **Inconsistent Indexes**: If indexing fails silently, some records may be invisible to search. Mitigation: periodic index consistency checks, manual index rebuild capability.

### Future Opportunities

1. **Memory Replay**: Replay a sequence of memory records to reconstruct and simulate past company state. Useful for debugging, training, and "what if" analysis.
2. **Anomaly Detection in Memory**: Analyze memory write patterns to detect operational anomalies (unusual event frequency, unexpected state transitions).
3. **Automatic Relationship Discovery**: Use ML to discover implicit relationships between records that are not captured by explicit correlation_ids.
4. **Cross-Instance Memory Federation**: If multiple company instances exist, federate memory queries across instances for global audit and analysis.
5. **Time-Travel Debugging**: Use memory checkpoints and snapshots to reconstruct the exact state of the company at any point in the past, enabling precise debugging of historical failures.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/memory/` (new module) | A new `core/memory/` package containing runtime.py, record.py, context.py, snapshot.py, index.py, store.py, checkpoint.py, timeline.py, search.py, classification.py, graph.py, trace.py, metadata.py, compaction.py, archive.py, recovery.py, retention.py, events.py |
| `core/conversation/runtime.py` | Unchanged. Publishes events consumed by Memory Runtime |
| `core/decision/runtime.py` | Unchanged (per requirement). Publishes decision events consumed by Memory Runtime |
| `core/execution/runtime.py` | Unchanged. Publishes execution events consumed by Memory Runtime |
| `core/learning/runtime.py` | Unchanged. Publishes learning events consumed by Memory Runtime |
| `core/policies/runtime.py` | Unchanged. Publishes policy events consumed by Memory Runtime |
| `core/llm/` (future) | Unchanged. Publishes LLM communication events consumed by Memory Runtime |
| `EventBus` | Unchanged. New memory event types are added, but the bus contract remains the same |
| `ObservabilityProjector` | May add a `MemoryProjector` to consume memory lifecycle events and track storage metrics |
| `ARCHITECTURE.md` | Should index this blueprint under a new section for Operational Memory |

---

## 20. Architectural Principles

- **Immutable Record**: Every memory record is written once and never modified. The past is fixed.
- **Append-Only**: New records are appended. Old records are never deleted (except by audited lifecycle policies).
- **Passive Consumer**: The Memory Runtime never blocks, delays, or modifies the behavior of event producers. Components operate whether or not memory is available.
- **Eventual Consistency**: Indexes may lag behind the record store. Queries may not see the most recent records immediately.
- **Policy-Governed Lifecycle**: Every record has a lifecycle governed by configurable policies. No record lives forever by default.
- **Preserve Queryability**: Compaction and archival must not destroy the ability to answer historical questions. Summarized records retain key information; full records are recoverable.
- **Correlation Across Components**: The Memory Runtime is the only component that can connect events across all other components. Correlation_ids are the mechanism for this cross-component tracing.
- **Checksum Integrity**: Every record and snapshot includes a checksum for verification. Memory is tamper-evident.
- **Separation of Write and Read Paths**: The write path is optimized for speed and durability. The read path is optimized for flexibility and performance. They scale independently.

---

## 21. Final Blueprint Statement

This blueprint defines the future implementation shape of the Memory Runtime layer while preserving the contract-first architecture of the AI Company. The Memory Runtime is the company's episodic memory — a durable, indexed, policy-governed record of everything that has ever happened.

When fully implemented, every event from every component — every execution, every decision, every conversation, every policy evaluation, every LLM request — is recorded in a single, queryable, immutable store. The company can answer any question about its past: "What happened?", "When did it happen?", "What led to it?", "What followed from it?", "What patterns exist across time?"

The Memory Runtime does not replace Knowledge, Learning, or Conversation management. It complements them. Knowledge answers "what we know". Learning answers "how we improve". Conversation answers "what we are saying". Memory answers "what we have experienced". Together, they give the company a complete understanding of its past, present, and path to improvement.

---
