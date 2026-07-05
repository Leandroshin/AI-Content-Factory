# Engineering Blueprint — Conversation Runtime

## Purpose

This document is the engineering blueprint for the `Conversation Runtime` of the AI Company. It defines the architecture of the stateful conversation management layer responsible for all structured communication between users, employees, departments, workflows, and future AI providers. Every multi-turn interaction — whether between a human operator and an employee, between two employees, between a workflow and a department, or between the company and an LLM provider — must pass through the Conversation Runtime.

This blueprint translates the need for centralized conversation state into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

**Why a Conversation Runtime exists:**

The AI Company is fundamentally a multi-agent system. Employees communicate with each other, with departments, with workflows, and with external users. Without a Conversation Runtime, every component would need to independently manage message history, context windows, threading, participant tracking, and state persistence. This would:
- Duplicate conversation management logic across every runtime.
- Create inconsistent conversation state across the company.
- Make cross-component conversations (e.g., Employee → Department → LLM Provider) impossible to trace.
- Prevent centralized auditing, summarization, and context recovery.

**Why conversations must be first-class entities:**

Conversations are not ephemeral message streams. They represent the company's operational memory. Every decision, every handoff, every clarification, every execution trace lives inside a conversation. Treating conversations as first-class entities with explicit identity, lifecycle, versioning, and retention policies ensures that the company can:
- Recover context after interruptions (system restart, employee reassignment, workflow timeout).
- Audit why a specific decision was made by replaying the conversation that led to it.
- Isolate conversations from each other so a noisy workflow cannot pollute a user's session.
- Compress and summarize long-running conversations without losing critical context.

**How this fits with the LLM Gateway:**

The LLM Gateway blueprint (section 4.5) defines a `ConversationRuntime` as a sub-component responsible for managing multi-turn conversation state for provider communication. This blueprint supersedes and expands that definition. The LLM Gateway's `ConversationRuntime` becomes a thin integration point that delegates to this standalone Conversation Runtime. The Gateway never manages conversation state directly — it queries the Conversation Runtime for the history relevant to an LLM request, and stores the assistant's response back through it.

---

## 1. Scope and Boundaries

### In Scope (What Belongs to the Conversation Runtime)

- **Session Management**: Creating, maintaining, and terminating conversation sessions with explicit lifecycle.
- **Thread Management**: Supporting multiple logical threads within a single session for parallel sub-conversations.
- **Message Storage**: Storing and indexing every message with its sender, timestamp, type, content, and metadata.
- **Context Window Management**: Tracking token counts per thread and enforcing configurable context limits.
- **Context Compression**: Automatically summarizing or truncating old messages when the context window is exceeded.
- **Conversation Summarization**: Generating and maintaining running summaries of long conversations.
- **Memory Checkpoints**: Saving and restoring conversation state at explicit points for rollback or recovery.
- **Participant Tracking**: Maintaining the set of participants (users, employees, departments, workflows, systems) for each conversation.
- **Attachment Management**: Storing and indexing file attachments, data blobs, and media associated with messages.
- **Metadata Management**: Per-message and per-conversation metadata for categorization, priority, tags, and custom attributes.
- **Snapshot Production**: Producing immutable `ConversationSnapshot` objects for the Decision Engine and Policy Engine.
- **Isolation Enforcement**: Ensuring no conversation can read, modify, or influence another conversation's state.
- **Concurrent Conversation Support**: Managing thousands of simultaneous conversations without state conflicts.
- **Context Versioning**: Tracking changes to conversation context over time for audit and rollback.
- **Retention Policy Enforcement**: Applying configurable time-based and size-based retention policies.
- **Recovery After Interruption**: Reconstructing active conversations after system restart or component failure.

### Out of Scope (What Does NOT Belong to the Conversation Runtime)

- **Message Routing**: The Conversation Runtime stores and retrieves messages but does not decide who should receive them. Routing belongs to the Orchestrator and the Decision Engine.
- **Policy Evaluation**: The Conversation Runtime does not check whether a message is allowed (policy violation, profanity filter, PII leak). Policy checks belong to the Policy Engine.
- **LLM Provider Communication**: The Conversation Runtime does not send messages to or receive messages from LLM providers. This belongs to the LLM Gateway.
- **Task Execution**: The Conversation Runtime does not execute tasks, generate content, or run workflows. This belongs to the AI Execution Runtime.
- **Business Logic**: The Conversation Runtime does not interpret message content or make decisions based on what was said. It stores, organizes, and retrieves messages.
- **User Authentication**: The Conversation Runtime does not authenticate users or validate credentials. It receives authenticated participant identifiers.
- **Real-Time Transport**: The Conversation Runtime manages conversation state but does not handle WebSocket connections, SSE streams, or HTTP long-polling. Transport belongs to the API layer.
- **Permanent Archival**: The Conversation Runtime applies retention policies but does not manage long-term cold storage. Archival belongs to the Data Lake / Knowledge layer.

---

## 2. Separation of Concerns

Conversation management is split into four distinct layers to prevent conversation state management from leaking into business logic, provider communication, or policy evaluation:

```text
┌─────────────────────────────────────────────────────────────┐
│                Business Logic Layer                          │
│  (Employees, Orchestrator, Workflows, Users)                  │
│  Knows: what to say, who to say it to, when to say it        │
│  Does NOT know: context windows, token counts, snapshots     │
└───────────────────────────┬─────────────────────────────────┘
                            │ Sends messages, queries history
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Conversation Runtime Layer                     │
│  (ConversationRuntime, SessionManager, ThreadManager,        │
│   ContextWindow, MemoryCheckpoint, SnapshotProducer)          │
│  Knows: messages, threads, sessions, tokens, participants    │
│  Does NOT know: business decisions, policy rules, providers  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Provides context, stores responses
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Provider Communication Layer                  │
│  (LLM Gateway, AI Execution Runtime)                         │
│  Knows: how to ask, what format to expect                    │
│  Does NOT know: conversation lifecycle, participant state    │
└─────────────────────────────────────────────────────────────┘
```

### Business Logic Layer
- **Responsibility**: Employees, Orchestrator, and Workflows determine what needs to be communicated and to whom.
- **Knowledge**: Task requirements, participant identities, conversation purpose.
- **Interaction**: Calls `ConversationRuntime.send_message()` to send a message, `ConversationRuntime.get_history()` to retrieve conversation context.

### Conversation Runtime Layer
- **Responsibility**: Manages the full lifecycle of conversations: sessions, threads, messages, context windows, summaries, checkpoints, and snapshots.
- **Knowledge**: Message history, participant registry, token counts, compression policies, retention rules.
- **Interaction**: Stores messages, enforces context limits, produces snapshots, manages checkpoints.

### Provider Communication Layer
- **Responsibility**: LLM Gateway and AI Execution Runtime consume conversation context for prompt building and execution.
- **Knowledge**: Provider capabilities, prompt templates, execution plans.
- **Interaction**: Reads conversation state through `ConversationSnapshot`, writes LLM responses back through the Runtime.

---

## 3. Relationships and Interactions

The Conversation Runtime is a central hub. Every component that sends or receives messages interacts through it:

```text
  User (External)
        │
        ├─► API Layer ──► ConversationRuntime.send_message()
        │
  Employee (Internal)
        │
        ├─► ConversationRuntime.send_message()
        │
  Workflow (Internal)
        │
        ├─► ConversationRuntime.send_message()
        │
  Department (Internal)
        │
        ├─► ConversationRuntime.send_message()
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │                  Conversation Runtime                    │
  │                                                         │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
  │  │ Session  │  │ Thread   │  │ Context Window        │  │
  │  │ Manager  │──│ Manager  │──│ Manager               │  │
  │  └──────────┘  └──────────┘  └──────────────────────┘  │
  │       │              │                  │               │
  │       ▼              ▼                  ▼               │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
  │  │ Message  │  │ Memory   │  │ Snapshot             │  │
  │  │ Store    │  │ Checkpoint│  │ Producer             │  │
  │  └──────────┘  └──────────┘  └──────────────────────┘  │
  └──────────────────────┬──────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
  ┌────────────┐ ┌────────────┐ ┌────────────────┐
  │  Knowledge │ │  EventBus  │ │  Observability │
  │  Runtime   │ │            │ │  Projector     │
  └────────────┘ └────────────┘ └────────────────┘
```

- **Users**: Send and receive messages through the API layer, which delegates to the Conversation Runtime.
- **Employees**: Send messages as part of task execution (e.g., requesting clarification, reporting progress).
- **Workflows**: Send automated messages (e.g., notifications, status updates, escalation prompts).
- **Departments**: Participate in conversations involving cross-department coordination.
- **LLM Gateway**: Requests conversation context for prompt assembly; stores provider responses.
- **AI Execution Runtime**: Requests conversation context during task execution; stores execution-related messages.
- **Knowledge Runtime**: Receives conversation data for long-term storage and retrieval.
- **EventBus**: Receives conversation events for observability and cross-component notification.
- **Observability Projector**: Consumes conversation events to track metrics, latency, and usage patterns.

---

## 4. Component Breakdown

The Conversation Runtime is organized as a set of logical sub-components with clearly separated responsibilities:

```text
                    ┌─────────────────────────────┐
                    │    ConversationRuntime       │
                    │  (Public Orchestration Entry)│
                    └──────┬──────────────┬───────┘
                           │              │
              ┌────────────┴──────┐  ┌────┴────────────┐
              │  SessionManager   │  │   ThreadManager  │
              │  (Session CRUD)   │  │ (Thread CRUD)    │
              └────────────┬──────┘  └────┬────────────┘
                           │              │
              ┌────────────┴──────────────┴───────┐
              │          MessageStore              │
              │  (Messages + Attachments + Meta)   │
              └────────────┬──────────────┬───────┘
                           │              │
              ┌────────────┴──────┐  ┌────┴────────────┐
              │  ContextWindow    │  │ContextCompression│
              │  (Token Tracking) │  │(Summarization)   │
              └────────────┬──────┘  └────┬────────────┘
                           │              │
              ┌────────────┴──────────────┴───────┐
              │       MemoryCheckpoint             │
              │  (Save / Restore / Rollback)       │
              └────────────┬───────────────────────┘
                           │
              ┌────────────┴───────────────────────┐
              │      SnapshotProducer               │
              │  (Immutable Context for Engines)    │
              └────────────────────────────────────┘
```

### 4.1 ConversationRuntime (Orchestration Entry Point)

- **Purpose**: Single public entry point for all conversation operations. Receives commands (send message, create thread, query history, save checkpoint) and orchestrates the appropriate sub-components.
- **Execution**: Stateful orchestrator. The Runtime itself delegates to stateless sub-components for most operations. Session and message state lives within the sub-components.
- **Public Interface** (conceptual):
  - `create_session(participants, metadata) -> SessionID`
  - `get_session(session_id) -> ConversationSession`
  - `close_session(session_id)`
  - `create_thread(session_id, metadata) -> ThreadID`
  - `send_message(session_id, thread_id, message) -> MessageID`
  - `get_history(session_id, thread_id, limit, before_id) -> list[ConversationMessage]`
  - `get_context(session_id, thread_id) -> ConversationContext`
  - `create_snapshot(session_id) -> ConversationSnapshot`
  - `save_checkpoint(session_id, label) -> CheckpointID`
  - `restore_checkpoint(session_id, checkpoint_id)`
  - `summarize(session_id, thread_id) -> ConversationSummary`
  - `query_participants(session_id) -> Participants`
  - `apply_retention(session_id)`

### 4.2 SessionManager

- **Purpose**: Manages the lifecycle of conversation sessions. A session represents a top-level conversation container with a fixed set of participants, creation time, status, and metadata.
- **Execution**: Stateful. Maintains a registry of active sessions. Sessions transition through states: `CREATED` → `ACTIVE` → `CLOSED` → `ARCHIVED`. Sessions may be ephemeral (volatile, no persistence) or durable (persisted to Knowledge).
- **Key Operations**:
  - `create_session(participants, session_type, metadata) -> ConversationSession`: Creates a new session, assigns a unique ID, registers participants, sets status to CREATED.
  - `get_session(session_id) -> ConversationSession`: Returns the session object with current status and metadata.
  - `close_session(session_id)`: Sets status to CLOSED, triggers any configured retention/archival policy, publishes SessionClosed event.
  - `list_active_sessions() -> list[ConversationSession]`: Returns all sessions with ACTIVE status.
  - `get_sessions_by_participant(participant_id) -> list[ConversationSession]`: Returns all sessions involving a given participant.

### 4.3 ThreadManager

- **Purpose**: Manages logical threads within a session. A thread represents a single conversational flow — a sequence of messages sharing the same topic, context, or purpose. Sessions may have multiple threads for parallel sub-conversations.
- **Execution**: Stateful per session. Threads are uniquely identified within a session. Each thread has its own message sequence, context window, and participant subset.
- **Key Operations**:
  - `create_thread(session_id, name, thread_type, metadata) -> ThreadID`: Creates a new thread, assigns a sequential ID within the session.
  - `get_thread(session_id, thread_id) -> ConversationThread`: Returns thread metadata and status.
  - `close_thread(session_id, thread_id)`: Marks the thread as CLOSED, prevents further messages.
  - `list_threads(session_id) -> list[ConversationThread]`: Returns all threads in a session.
  - `get_thread_messages(session_id, thread_id, limit, offset) -> list[ConversationMessage]`: Paginated message retrieval.
- **Thread Types**: `STANDARD` (normal conversation), `COLLABORATION` (multi-participant work), `EXECUTION` (task execution trace), `CLARIFICATION` (request for additional information), `NOTIFICATION` (system-generated updates).

### 4.4 ConversationMessage

- **Purpose**: Represents a single unit of communication within a thread. Every message has a sender, content, type, timestamp, and unique ID.
- **Structure** (conceptual):
  - `message_id`: Unique identifier (UUID).
  - `session_id`: Parent session.
  - `thread_id`: Parent thread.
  - `sender_id`: Identifier of the sending participant (employee, user, workflow, system).
  - `sender_type`: Type of sender (`USER`, `EMPLOYEE`, `WORKFLOW`, `DEPARTMENT`, `SYSTEM`, `LLM_PROVIDER`).
  - `message_type`: Type of message (`TEXT`, `COMMAND`, `RESULT`, `ERROR`, `CLARIFICATION`, `SYSTEM`, `TOOL_CALL`, `TOOL_RESULT`).
  - `content`: Message content (plain text, structured data, or serialized object).
  - `attachments`: List of `Attachment` objects.
  - `metadata`: `MessageMetadata` object.
  - `parent_message_id`: Optional reference to the message this is a reply to.
  - `correlation_id`: Optional identifier linking this message to a broader workflow or execution.
  - `timestamp`: ISO 8601 timestamp of message creation.
  - `edited_at`: Optional timestamp of last edit.
  - `tokens`: Estimated or actual token count for context window management.
- **Immutability**: Once stored, messages are immutable. Edits are represented as new messages with an `edited_message_id` reference.

### 4.5 ConversationSession

- **Purpose**: Top-level container for a conversation. Holds participants, threads, lifecycle state, and session-level metadata.
- **Structure** (conceptual):
  - `session_id`: Unique identifier (UUID).
  - `participants`: `Participants` object listing all participants.
  - `status`: `CREATED`, `ACTIVE`, `CLOSED`, `ARCHIVED`.
  - `session_type`: `USER_TO_EMPLOYEE`, `EMPLOYEE_TO_EMPLOYEE`, `WORKFLOW`, `SYSTEM`, `LLM_QUERY`.
  - `created_at`: ISO 8601 timestamp.
  - `closed_at`: Optional timestamp.
  - `metadata`: Session-level key-value metadata.
  - `retention_policy`: Reference to the retention policy applied to this session.
  - `context_version`: Monotonically increasing version number incremented on each state change.

### 4.6 ConversationThread

- **Purpose**: A single logical conversational flow within a session. Has its own message list, context window, compression state, and summary.
- **Structure** (conceptual):
  - `thread_id`: Unique identifier within the session.
  - `session_id`: Parent session.
  - `name`: Human-readable label.
  - `thread_type`: `STANDARD`, `COLLABORATION`, `EXECUTION`, `CLARIFICATION`, `NOTIFICATION`.
  - `status`: `ACTIVE`, `CLOSED`.
  - `message_count`: Number of messages in the thread.
  - `token_count`: Running total of tokens in the active context window.
  - `compression_state`: Current compression status (`UNCOMPRESSED`, `PARTIALLY_COMPRESSED`, `FULLY_COMPRESSED`).
  - `summary`: Optional `ConversationSummary`.
  - `created_at`: ISO 8601 timestamp.
  - `metadata`: Thread-level key-value metadata.

### 4.7 ConversationContext

- **Purpose**: Immutable snapshot of a conversation's state at a given point in time. Used by the Decision Engine, Policy Engine, LLM Gateway, and AI Execution Runtime to understand the conversation's current state without accessing live state.
- **Structure** (conceptual):
  - `session_id`: Parent session.
  - `thread_id`: Parent thread.
  - `session_snapshot`: Frozen `ConversationSession` state (status, participants, type, metadata).
  - `thread_snapshot`: Frozen `ConversationThread` state (name, type, status, token count, compression state).
  - `messages`: List of recent `ConversationMessage` objects within the context window.
  - `summary`: Current `ConversationSummary`, if any.
  - `participants`: Current `Participants` list.
  - `context_version`: Version number of the conversation at snapshot time.
  - `compression_status`: Whether any messages have been compressed.
  - `token_utilization`: Current tokens / max tokens ratio.
  - `created_at`: Snapshot creation timestamp.
- **Immutability**: `ConversationContext` is fully frozen. No component may modify it. It is produced by the `ConversationRuntime.get_context()` method.

### 4.8 ContextWindow

- **Purpose**: Manages the token-aware window of active messages within a thread. Enforces configurable maximum token limits and determines which messages are evicted or compressed when the limit is exceeded.
- **Execution**: Stateless per operation. Receives a thread's message list and current token count, determines the active window based on configured limits.
- **Key Operations**:
  - `calculate_window(messages, max_tokens) -> list[ConversationMessage]`: Returns the subset of messages that fit within the token limit, ordered from oldest to newest.
  - `estimate_tokens(content) -> int`: Estimates token count for a given message content.
  - `window_utilization(messages, max_tokens) -> float`: Returns utilization as a ratio (0.0 to 1.0+).
  - `should_compress(messages, max_tokens, threshold) -> bool`: Returns True if utilization exceeds the compression threshold.
- **Eviction Strategy**: When the window is exceeded, messages are evicted oldest-first. Evicted messages are either compressed (summarized) or discarded based on the thread's compression policy. System messages and checkpoint markers are never evicted.

### 4.9 ContextCompression

- **Purpose**: Compresses old messages when the context window is exceeded. Supports multiple compression strategies configurable per thread or session.
- **Execution**: Stateful per compression operation. May delegate summarization to a configured provider (LLM Gateway, local algorithm) or use token truncation.
- **Compression Strategies**:
  1. **Summarization**: Uses an LLM to generate a concise summary of evicted messages. The summary replaces the evicted messages in the context window.
  2. **Truncation**: Drops old messages beyond a minimum retention count. No summary is generated. Use for low-importance threads.
  3. **Selective Retention**: Retains messages matching configurable criteria (e.g., contains a command, has attachments, was sent by a specific participant) while discarding others.
  4. **Rolling Window**: Keeps the last N messages regardless of token count. Use for high-throughput notification threads where only the latest state matters.
- **Key Operations**:
  - `compress(messages, strategy, parameters) -> CompressionResult`: Applies the specified compression strategy to a list of messages. Returns the compressed representation and metadata about what was removed.
  - `decompress(compression_result) -> list[ConversationMessage]`: Attempts to reconstruct original messages from a compression result (only possible for Summarization strategy if full message store is available).

### 4.10 ConversationSummary

- **Purpose**: A compressed representation of a conversation thread's content. Summaries are generated by ContextCompression or on-demand for long-running conversations. Used to provide context without loading the full message history.
- **Structure** (conceptual):
  - `summary_id`: Unique identifier.
  - `session_id`: Parent session.
  - `thread_id`: Parent thread.
  - `content`: The summary text (generated by LLM or algorithm).
  - `message_range`: The range of messages covered (start_message_id to end_message_id).
  - `token_count`: Token count of the summary.
  - `compression_ratio`: Original tokens / summary tokens ratio.
  - `generated_at`: Timestamp of summary generation.
  - `generated_by`: Identifier of the component that generated the summary (`SYSTEM`, `LLM_GATEWAY`, `SCHEDULER`).
  - `metadata`: Key-value metadata (confidence, model used, temperature).

### 4.11 MemoryCheckpoint

- **Purpose**: Saves and restores the state of a conversation at an explicit point. Enables rollback, recovery after interruption, and branching exploration.
- **Execution**: Stateful per checkpoint. Each checkpoint captures the full state of a session and its threads at a point in time.
- **Key Operations**:
  - `save_checkpoint(session_id, label, metadata) -> CheckpointID`: Captures the current state of all threads, messages, context windows, and summaries. Returns a unique checkpoint ID.
  - `restore_checkpoint(session_id, checkpoint_id)`: Restores the session to the captured state. All messages and threads after the checkpoint are preserved (soft restore) or discarded (hard restore), depending on the restore mode.
  - `list_checkpoints(session_id) -> list[CheckpointMetadata]`: Lists all checkpoints for a session with timestamps and labels.
  - `delete_checkpoint(session_id, checkpoint_id)`: Removes a checkpoint.
- **Restore Modes**:
  - `SOFT`: Restores state but preserves subsequent messages as a branch. The original timeline remains accessible.
  - `HARD`: Restores state and discards all messages and state changes after the checkpoint. Irreversible.
- **Storage**: Checkpoints may be stored in-memory (for active sessions) or persisted via the Knowledge Runtime (for long-term recovery).

### 4.12 ConversationSnapshot

- **Purpose**: Immutable, versioned, fully frozen representation of a conversation session at a specific point. Used by the Decision Engine, Policy Engine, and external consumers that need a consistent view of conversation state without accessing live objects.
- **Structure** (conceptual):
  - `snapshot_id`: Unique identifier.
  - `session_id`: Source session.
  - `context_version`: Version of the conversation at snapshot time.
  - `session_status`: Status of the session at snapshot time.
  - `threads`: Frozen list of thread snapshots (name, status, message_count, token_count, compression_state).
  - `participants`: Frozen `Participants` object.
  - `context_window_messages`: Frozen list of messages currently in the context window.
  - `summaries`: Frozen list of active summaries.
  - `metadata`: Frozen session metadata.
  - `created_at`: Snapshot creation timestamp.
  - `checksum`: Content hash for integrity verification.

### 4.13 Participants

- **Purpose**: Manages the set of participants in a conversation session. Participants may join and leave during the session lifecycle.
- **Structure** (conceptual):
  - `participants`: List of participant entries, each containing:
    - `participant_id`: Unique identifier.
    - `participant_type`: `USER`, `EMPLOYEE`, `DEPARTMENT`, `WORKFLOW`, `SYSTEM`, `LLM_PROVIDER`.
    - `display_name`: Human-readable name.
    - `role`: `OWNER`, `MEMBER`, `OBSERVER`, `RESPONDER`.
    - `joined_at`: Timestamp of entry.
    - `left_at`: Optional timestamp of departure.
    - `metadata`: Participant-specific metadata (e.g., employee department, user email).
  - `owner`: The participant that created the session. Only the owner may close the session or modify participant roles.
- **Role Enforcement**:
  - `OWNER`: Full control — can close session, add/remove participants, modify metadata.
  - `MEMBER`: Can send messages, create threads, view history.
  - `OBSERVER`: Can view history and receive messages but cannot send.
  - `RESPONDER`: Can only send messages in response to direct queries. Used for survey-style interactions.

### 4.14 Attachments

- **Purpose**: Represents files, data blobs, or structured data associated with a message. Attachments are stored and indexed but not interpreted by the Conversation Runtime.
- **Structure** (conceptual):
  - `attachment_id`: Unique identifier.
  - `message_id`: Parent message.
  - `filename`: Original filename.
  - `content_type`: MIME type.
  - `size_bytes`: File size.
  - `storage_url`: URL or reference to the stored content.
  - `metadata`: Key-value metadata (e.g., document type, page count, checksum).
  - `processed`: Whether the attachment has been processed by a consumer (e.g., Knowledge Runtime for indexing).
- **Storage Delegation**: Attachments are not stored directly in the Conversation Runtime. The Runtime stores metadata and a reference; the actual content is stored by the Knowledge Runtime or a dedicated Storage Runtime.

### 4.15 MessageMetadata

- **Purpose**: Per-message metadata that provides context, routing hints, and categorization without affecting message content.
- **Structure** (conceptual):
  - `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
  - `tags`: List of string tags for categorization and search.
  - `locale`: Language/locale of the message content.
  - `client_info`: Information about the client that sent the message (client type, version, IP).
  - `custom`: Dictionary of arbitrary key-value pairs for extensibility.
  - `references`: List of reference IDs linking this message to external entities (tasks, executions, workflows, decisions).
  - `security_classification`: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.

### 4.16 SnapshotProducer

- **Purpose**: Produces immutable `ConversationSnapshot` and `ConversationContext` objects on demand. Ensures that consumers always receive a consistent, frozen view of conversation state.
- **Execution**: Stateless. Reads current state from SessionManager and MessageStore, freezes it into immutable objects, and returns them. Never modifies live state.
- **Key Operations**:
  - `produce_snapshot(session_id) -> ConversationSnapshot`: Captures full session state.
  - `produce_context(session_id, thread_id) -> ConversationContext`: Captures thread-focused state with context window messages.
  - `produce_context_for_decision(session_id) -> ConversationContext`: Captures decision-relevant context (participants, active threads, latest summaries).

---

## 5. Architectural Flow

### 5.1 Message Lifecycle

```text
  Sender (User / Employee / Workflow / System)
        │
        ▼
  1. ConversationRuntime.send_message(session_id, thread_id, content)
        │
        ├─► 2. Validate session exists and is ACTIVE
        │
        ├─► 3. Validate thread exists and is ACTIVE
        │
        ├─► 4. Validate sender is a participant with appropriate role
        │
        ├─► 5. Create ConversationMessage (immutable, with ID, timestamp, metadata)
        │
        ├─► 6. MessageStore.store(message)
        │
        ├─► 7. ContextWindow.should_compress(thread)
        │      │
        │      ├─► YES ──► ContextCompression.compress() ──► Update summary
        │      │
        │      └─► NO
        │
        ├─► 8. Update thread token_count + message_count
        │
        ├─► 9. Publish MessageSent event to EventBus
        │
        └─► 10. Return message_id to sender
```

### 5.2 Context Retrieval for LLM Gateway

```text
  LLM Gateway.ask(RequestContext)
        │
        ▼
  1. ConversationRuntime.get_context(session_id, thread_id)
        │
        ├─► 2. SnapshotProducer.produce_context(session_id, thread_id)
        │      │
        │      ├─► Read thread's active messages from MessageStore
        │      │
        │      ├─► ContextWindow.calculate_window(messages, max_tokens)
        │      │
        │      ├─► Attach thread's current summary (if any)
        │      │
        │      └─► Freeze into ConversationContext
        │
        ├─► 3. Return ConversationContext to LLM Gateway
        │
        ▼
  LLM Gateway uses ConversationContext for prompt assembly
        │
        ▼
  LLM Gateway receives ResponseContext from provider
        │
        ▼
  4. ConversationRuntime.send_message(
         session_id, thread_id,
         Message(LLM_PROVIDER, response.content)
     )
        │
        └─► Normal message lifecycle (section 5.1)
```

### 5.3 Checkpoint and Recovery Flow

```text
  Before critical operation (e.g., execution start):
        │
        ▼
  ConversationRuntime.save_checkpoint(session_id, "before:task-123")
        │
        ├─► Capture all thread states, messages, summaries
        ├─► Assign CheckpointID
        ├─► Store checkpoint (in-memory or Knowledge)
        └─► Publish CheckpointCreated event
        │
  ... operation proceeds ...
        │
  If operation fails:
        │
        ▼
  ConversationRuntime.restore_checkpoint(session_id, checkpoint_id)
        │
        ├─► HARD restore: discard all messages after checkpoint
        │   (or SOFT restore: preserve as branch)
        ├─► Restore thread states, summaries, context windows
        ├─► Publish CheckpointRestored event
        └─► Conversation is ready for retry
```

### 5.4 Context Compression Flow

```text
  Message sent → token_count exceeds threshold
        │
        ▼
  ContextCompression.compress(evicted_messages, strategy="summarize")
        │
        ├─► Collect evicted messages (oldest-first beyond window)
        ├─► Send to configured summarizer (LLM Gateway or local)
        ├─► Receive summary text
        ├─► Store ConversationSummary (message_range, content, tokens)
        ├─► Replace evicted messages with summary in context window
        ├─► Update thread compression_state
        └─► Publish ContextCompressed event
```

---

## 6. Data Model

The Conversation Runtime's data model is designed for immutable message storage, efficient context window calculation, and snapshot production. All entities use UUIDs for global uniqueness.

```text
  ┌──────────────────────┐
  │  ConversationSession  │
  ├──────────────────────┤
  │  session_id: UUID    │
  │  participants: []     │───► Participants
  │  status: Enum        │
  │  session_type: Enum  │
  │  created_at: ISO8601 │
  │  closed_at: ISO8601  │
  │  metadata: dict      │
  │  retention_policy:   │
  │  context_version: int│
  └──────────┬───────────┘
             │ 1:N
             ▼
  ┌──────────────────────┐      ┌──────────────────────┐
  │  ConversationThread   │      │  MemoryCheckpoint    │
  ├──────────────────────┤      ├──────────────────────┤
  │  thread_id: UUID     │      │  checkpoint_id: UUID │
  │  session_id: UUID    │───►  │  session_id: UUID    │
  │  name: string        │      │  state_snapshot: ... │
  │  thread_type: Enum   │      │  label: string       │
  │  status: Enum        │      │  created_at: ISO8601 │
  │  message_count: int  │      └──────────────────────┘
  │  token_count: int    │
  │  compression_state   │
  │  summary_id: UUID    │───► ConversationSummary
  └──────────┬───────────┘
             │ 1:N
             ▼
  ┌──────────────────────────────┐
  │  ConversationMessage          │
  ├──────────────────────────────┤
  │  message_id: UUID            │
  │  session_id: UUID            │
  │  thread_id: UUID             │
  │  sender_id: UUID             │
  │  sender_type: Enum           │
  │  message_type: Enum          │
  │  content: string/bytes       │
  │  attachments: []             │───► Attachments
  │  metadata: MessageMetadata   │
  │  parent_message_id: UUID?    │
  │  correlation_id: UUID?       │
  │  timestamp: ISO8601          │
  │  tokens: int                 │
  └──────────────────────────────┘
```

---

## 7. State Management

The Conversation Runtime is stateful by design. This is a deliberate architectural decision — conversations are inherently stateful. However, state is carefully scoped and isolated.

### 7.1 State Ownership

| State | Owner | Scope | Persistence |
|-------|-------|-------|-------------|
| Session metadata | SessionManager | In-memory | Optional (Knowledge) |
| Thread metadata | ThreadManager | In-memory | Optional (Knowledge) |
| Messages | MessageStore | In-memory / Durable | Recommended |
| Context windows | ContextWindow | Derived (stateless) | Not stored |
| Summaries | ContextCompression | In-memory | Recommended |
| Checkpoints | MemoryCheckpoint | In-memory / Durable | Optional |
| Snapshots | SnapshotProducer | Transient | Not stored |

### 7.2 Consistency Guarantees

- **Session-Level Consistency**: All operations within a session are serialized. Concurrent operations on different sessions proceed in parallel.
- **Thread-Level Isolation**: Operations on different threads within the same session are independent. A slow message write on Thread A does not block Thread B.
- **Snapshot Consistency**: `ConversationSnapshot` always represents a consistent point-in-time view. No partial updates are visible.
- **Read-Your-Writes**: After `send_message()` returns, `get_history()` is guaranteed to include the sent message.

### 7.3 Concurrency Model

- **Per-Session Lock**: Each session has a lightweight read-write lock. Write operations (send message, save checkpoint) acquire the write lock. Read operations (get history, get context) acquire the read lock.
- **Deadlock Prevention**: The lock hierarchy is session → thread. No operation ever acquires locks in reverse order. Cross-session operations are forbidden.
- **Performance Target**: < 1ms overhead per operation for the locking layer. At high concurrency (10,000+ sessions), the lock granularity may be reduced to per-thread.

---

## 8. Context Management

### 8.1 Context Window Strategy

The context window is the set of messages considered "active" for a given thread. It is a sliding window with token-aware eviction:

```
  Time ──────────────────────────────────────────────────────►
  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
  │ Message 1  │ │ Message 2  │ │ Message 3  │ │ Message 4  │
  │ (oldest)   │ │            │ │            │ │ (newest)   │
  └────────────┘ └────────────┘ └────────────┘ └────────────┘
       │               │              │              │
       ▼               ▼              │              │
  ┌────────────┐ ┌────────────┐       │              │
  │ Summary    │ │ Summary    │       │              │
  │ (msg 1-2)  │ │ (msg 1-2)  │       │              │
  └────────────┘ └────────────┘       │              │
       │               │              │              │
       └───────────────┴──────────────┴──────────────┘
                          │
                          ▼
              ┌──────────────────────────┐
              │   Active Context Window  │
              │   (Summary + Msg 3 + 4)  │
              │   Total tokens ≤ max     │
              └──────────────────────────┘
```

### 8.2 Token Budget Allocation

The context window's token budget is configurable per session or per thread. The budget is allocated as follows:

| Component | Budget Share | Notes |
|-----------|-------------|-------|
| System prompt / session instructions | 10% | Never evicted |
| Active messages (newest) | 60% | Evicted oldest-first |
| Summaries of evicted messages | 20% | Replaced when stale |
| Current task/execution context | 10% | Injected by AI Execution Runtime |

### 8.3 Compression Thresholds

- **WARN**: 70% utilization — log warning, flag for monitoring.
- **COMPRESS**: 85% utilization — trigger automatic compression of evicted messages.
- **CRITICAL**: 95% utilization — block new messages until compression completes.
- **BLOCKED**: 100% utilization — reject new messages with CONTEXT_OVERFLOW error.

---

## 9. Events

The Conversation Runtime publishes events to the EventBus for observability, cross-component notification, and persistence triggers. Events are published after state changes are committed.

### 9.1 Event Catalog

| Event | Trigger | Payload |
|-------|---------|---------|
| `SessionCreated` | `create_session()` | session_id, participants, session_type, created_at |
| `SessionClosed` | `close_session()` | session_id, closed_at, message_count, reason |
| `ThreadCreated` | `create_thread()` | session_id, thread_id, thread_type, name |
| `ThreadClosed` | `close_thread()` | session_id, thread_id, message_count |
| `MessageSent` | `send_message()` | message_id, session_id, thread_id, sender_id, sender_type, message_type, timestamp, token_count, correlation_id |
| `ContextWindowWarning` | utilization > 70% | session_id, thread_id, utilization, token_count |
| `ContextCompressed` | `compression` completes | session_id, thread_id, messages_evicted, summary_token_count, compression_ratio |
| `CheckpointCreated` | `save_checkpoint()` | session_id, checkpoint_id, label, created_at |
| `CheckpointRestored` | `restore_checkpoint()` | session_id, checkpoint_id, restore_mode, restored_at |
| `SessionArchived` | retention policy applied | session_id, archived_at, retention_reason |
| `ParticipantAdded` | participant joins | session_id, participant_id, participant_type, role |
| `ParticipantRemoved` | participant leaves | session_id, participant_id, reason |
| `SessionMigrated` | session moved to Knowledge | session_id, knowledge_id, context_version |
| `Error` | operation failure | session_id, operation, error_code, error_message |

### 9.2 Event Publishing Rules

- Events are published **after** the state change is committed (post-publish).
- Events are **fire-and-forget**. The Conversation Runtime does not wait for event consumers.
- Events are **immutable** and **idempotent**. The same event may be delivered multiple times without side effects.
- Events carry enough context for consumers to act without querying the Conversation Runtime. For example, `MessageSent` includes `message_id` and `correlation_id` so the AI Execution Runtime can correlate a message to an ongoing execution without an additional query.

---

## 10. Integration with EventBus

### 10.1 Publisher Role

The Conversation Runtime is a publisher. It emits events whenever conversation state changes. It never subscribes to events from other components.

### 10.2 Event Format

```python
@dataclass(frozen=True)
class ConversationEvent:
    event_id: UUID
    event_type: str
    session_id: UUID
    timestamp: datetime
    payload: dict[str, Any]
```

### 10.3 Consumers

| Consumer | Subscribes To | Purpose |
|----------|--------------|---------|
| Observability Projector | All conversation events | Track metrics, latency, usage |
| Knowledge Runtime | SessionArchived, MessageSent | Persistent storage |
| AI Execution Runtime | MessageSent | Correlate messages to executions |
| Orchestrator | SessionCreated, SessionClosed | Workflow lifecycle management |
| Notification System | MessageSent | Push notifications to users |

### 10.4 EventBus Contract

- The Conversation Runtime expects the EventBus to provide at-least-once delivery.
- The Conversation Runtime does not retry failed event publications. The caller must handle bus failures.
- Events must be delivered in order per session. Cross-session ordering is not required.

---

## 11. Integration with Observability

### 11.1 Observable Metrics

The Conversation Runtime exposes the following metrics through the Observability Projector:

| Metric | Type | Labels |
|--------|------|--------|
| `conversation.sessions.active` | Gauge | session_type |
| `conversation.sessions.created` | Counter | session_type |
| `conversation.sessions.closed` | Counter | session_type, reason |
| `conversation.threads.active` | Gauge | thread_type |
| `conversation.messages.sent` | Counter | sender_type, message_type |
| `conversation.messages.token_count` | Histogram | sender_type |
| `conversation.context.compression_ratio` | Histogram | strategy |
| `conversation.context.utilization` | Gauge | session_id |
| `conversation.checkpoint.created` | Counter | — |
| `conversation.checkpoint.restored` | Counter | restore_mode |
| `conversation.operation.latency` | Histogram | operation |
| `conversation.operation.errors` | Counter | operation, error_code |
| `conversation.sessions.token_count` | Histogram | — |

### 11.2 Traceability

Every operation exposes a trace context that is propagated through events and logged for debugging. The trace context includes:
- `operation_id`: Unique identifier for the operation.
- `session_id`: The session being operated on.
- `thread_id`: The thread being operated on (if applicable).
- `message_id`: The message being created (if applicable).
- `timestamp`: Start and end timestamps.
- `duration_ms`: Total operation duration.
- `error`: Error message if the operation failed.

### 11.3 Audit Trail

The Conversation Runtime maintains an in-memory audit trail of state-changing operations. This trail is not a persistence mechanism — it is a runtime debugging aid. For permanent audit, the Knowledge Runtime persists conversation events.

---

## 12. Integration with Knowledge

### 12.1 Persistence Delegation

The Conversation Runtime does not persist data directly. It delegates persistence to the Knowledge Runtime in two ways:

1. **Event-Driven Persistence**: The Knowledge Runtime subscribes to `MessageSent`, `SessionArchived`, and `CheckpointCreated` events and persists the associated data.
2. **On-Demand Persistence**: The caller may explicitly request conversation persistence: `ConversationRuntime.export_to_knowledge(session_id) -> KnowledgeID`.

### 12.2 Retrieval from Knowledge

When a session is not in active memory (e.g., after system restart), the Conversation Runtime loads session state from the Knowledge Runtime:

```text
  1. ConversationRuntime.get_session(session_id)
  2.   ├─► Check in-memory registry
  3.   ├─► If not found, query Knowledge Runtime
  4.   ├─► Deserialize ConversationSession from Knowledge data
  5.   ├─► Load recent messages (configurable limit)
  6.   └─► Return ConversationSession
```

### 12.3 Synchronization Strategy

- **Write-Through**: Messages are written to the in-memory store and published as events immediately. The Knowledge Runtime persists asynchronously.
- **Read-Repair**: If the in-memory state is lost (restart), the Knowledge Runtime is the source of truth for recovery.
- **Conflict Resolution**: Last-write-wins. Since messages are immutable, conflicts are rare. Timestamps determine ordering.

---

## 13. Integration with Skills

### 13.1 Conversation as a Skill Input

Skills may consume conversation context as input. For example, a "Negotiation" skill may analyze the conversation history to determine the best approach.

- Skills request conversation context via `ConversationRuntime.get_context(session_id, thread_id)`.
- The context is delivered as an immutable `ConversationContext` — the skill may not modify it.

### 13.2 Conversation as a Skill Output

Skills may produce messages as output. For example, a "ReportGeneration" skill may send a formatted report to the conversation thread.

- Skills call `ConversationRuntime.send_message()` with appropriate session and thread IDs.
- The skill must be a registered participant in the session with at least `MEMBER` role.

### 13.3 Skill-Triggered Checkpoints

Skills may request checkpoints before and after critical operations:

```python
  checkpoint_id = runtime.save_checkpoint(session_id, "before:skill:report_gen")
  try:
      result = skill.execute(context)
      runtime.send_message(session_id, thread_id, result)
  except Exception:
      runtime.restore_checkpoint(session_id, checkpoint_id, mode="HARD")
```

---

## 14. Future Integration with LLM Gateway

### 14.1 Context Provider

The LLM Gateway will request conversation context through the Conversation Runtime instead of managing it internally. The `ConversationRuntime.get_context(session_id, thread_id)` method provides the Gateway with the exact message window needed for prompt assembly.

### 14.2 Response Storage

After the LLM Gateway receives a response from a provider, it stores the response by calling:

```python
  runtime.send_message(
      session_id=request.conversation_id,
      thread_id=request.thread_id,
      message=ConversationMessage(
          sender_id=response.provider_id,
          sender_type="LLM_PROVIDER",
          message_type="TEXT",
          content=response.content,
          metadata=MessageMetadata(
              tokens=response.tokens,
              references=[request.correlation_id]
          )
      )
  )
```

### 14.3 Conversation Runtime → LLM Gateway Flow

```text
  LLM Gateway                      Conversation Runtime
        │                                    │
        │  1. get_context(session_id,        │
        │     thread_id)                     │
        │───────────────────────────────────►│
        │                                    │
        │  2. ConversationContext            │
        │◄───────────────────────────────────│
        │                                    │
        │  3. Ask provider with context      │
        │                                    │
        │  4. send_message(response)         │
        │───────────────────────────────────►│
        │                                    │
        │  5. message_id                     │
        │◄───────────────────────────────────│
```

---

## 15. Future Integration with AI Execution Runtime

### 15.1 Execution Context

When the AI Execution Runtime starts an execution, it may create a dedicated thread for that execution:

```python
  thread_id = runtime.create_thread(
      session_id=task.session_id,
      name=f"execution:{task.task_id}",
      thread_type="EXECUTION",
      metadata={"task_id": task.task_id, "employee_id": task.assigned_employee}
  )
```

### 15.2 Execution Messages

The Execution Runtime sends progress, status, and result messages to the execution thread:

```python
  runtime.send_message(session_id, thread_id, Message(
      sender_id=execution_runtime_id,
      sender_type="SYSTEM",
      message_type="RESULT",
      content=execution_result.to_dict(),
      metadata=MessageMetadata(references=[task.task_id])
  ))
```

### 15.3 Pre-Execution Checkpoint

Before dispatching to the LLM Gateway, the Execution Runtime creates a checkpoint:

```python
  checkpoint_id = runtime.save_checkpoint(session_id, f"before:execution:{task.task_id}")
```

If the execution fails, the runtime may restore the checkpoint and retry with a different provider or approach.

---

## 16. Policies

### 16.1 Retention Policy

Retention policies define how long conversation data is kept before archival or deletion. Policies are configurable per session type.

| Policy | Scope | Action | Default |
|--------|-------|--------|---------|
| Time-based TTL | Per session | Archive to Knowledge after TTL expires | 30 days for ACTIVE, 7 days for CLOSED |
| Size-based cap | Per session | Compress oldest messages when total exceeds cap | 100 MB per session |
| Hard-delete after archival | Per session | Delete from in-memory store after Knowledge confirms persistence | Enabled for CLOSED sessions |
| Minimum retention | Global | Never delete sessions newer than this threshold | 24 hours |

### 16.2 Context Retention Policy

Context retention governs how long messages remain in the active context window before compression:

| Policy | Value | Rationale |
|--------|-------|-----------|
| Max tokens per thread | 8,192 (configurable) | Matches typical LLM context window (may vary by model) |
| Max messages per thread | 500 (configurable) | Prevents unbounded memory growth |
| System message retention | Always in window | Session instructions must never be evicted |
| Checkpoint retention | Until explicitly deleted | Checkpoints are user-managed |
| Summary retention | Until superseded | Replaced when new compression cycle completes |

### 16.3 Isolation Policy

- **No cross-session access**: A component may never read messages from a session it does not participate in.
- **No cross-thread leakage**: Thread visibility is restricted to participants of that thread.
- **Participant transparency**: A participant may always see its own messages and the messages addressed to it.
- **Observer read-only**: `OBSERVER` role participants may read but never write.

### 16.4 Recovery Policy

- **Automatic Recovery**: On system restart, sessions with `DURABLE` flag are loaded from Knowledge Runtime.
- **Lazy Loading**: Sessions are loaded on first access, not on startup. Startup loads only session metadata (IDs, participants, status).
- **Graceful Degradation**: If Knowledge Runtime is unavailable, the Conversation Runtime operates in memory-only mode. New messages are accepted and stored in memory but not persisted.
- **Timeout Recovery**: If a session is idle for more than the configured timeout, it is automatically closed. The timeout is configurable per session type (default: 1 hour for USER sessions, 24 hours for WORKFLOW sessions).

---

## 17. Versioning and Auditability

### 17.1 Context Versioning

Every state change to a session increments `context_version`. This version number is:
- Included in every `ConversationSnapshot` and `ConversationContext`.
- Monotonically increasing (never resets).
- Used by consumers to detect stale context.
- Included in all events for correlation.

### 17.2 Message Versioning

Messages are immutable. If a message needs to be corrected:
1. A new message is sent with `message_type = CORRECTION`.
2. The correction message references the original via `parent_message_id`.
3. The original message is never modified or deleted.

### 17.3 Audit Trail

The following data is always available for audit:
- Full message history (immutable by design).
- Checkpoint creation and restoration events.
- Session lifecycle events (create, close, archive).
- Participant changes (add, remove, role change).
- Compression events (what was compressed, ratio, strategy).

### 17.4 Checksum Integrity

Every `ConversationSnapshot` includes a `checksum` field (SHA-256 of the serialized snapshot content). Consumers may verify integrity by recomputing the checksum and comparing.

---

## 18. Scalability Considerations

### 18.1 Horizontal Scaling

The Conversation Runtime is designed for horizontal scaling through session sharding:
- **Session Sharding**: Each `session_id` maps to a shard. All operations for a session are handled by the same shard node.
- **Stateless Gateways**: The ConversationRuntime entry point is stateless from the caller's perspective. Callers do not need to know which node handles a session.
- **Shared-Nothing Architecture**: Each node manages its own sessions. No distributed state synchronization is required for v1.

### 18.2 Memory Management

- **Session Pool**: Active sessions are held in a bounded pool. When the pool is full, the least recently used CLOSED session is evicted (persisted to Knowledge first).
- **Message Batching**: Messages are batched for bulk operations (e.g., loading thread history).
- **Lazy Summary Generation**: Summaries are generated on demand or during idle periods, never during critical message-sending paths.

### 18.3 Performance Targets

| Operation | Target Latency (p99) | Target Throughput |
|-----------|---------------------|-------------------|
| `send_message` | < 5 ms | 10,000 / second |
| `get_history` | < 3 ms (cached), < 20 ms (uncached) | 20,000 / second |
| `get_context` | < 10 ms | 5,000 / second |
| `save_checkpoint` | < 15 ms | 1,000 / second |
| `restore_checkpoint` | < 50 ms | 500 / second |
| `compress` | < 100 ms (with LLM summarization) | 100 / second |

---

## 19. Risks and Limitations

### 19.1 Risks

1. **In-Memory State Loss**: The Conversation Runtime holds active sessions in memory. A process crash loses unpersisted messages. Mitigation: Durable sessions persist to Knowledge Runtime asynchronously. Ephemeral sessions accept this risk.
2. **Memory Pressure**: 10,000 concurrent sessions with 500 messages each could consume significant memory. Mitigation: bounded session pool, automatic compression, size-based eviction.
3. **Per-Session Lock Contention**: High-frequency message sends on the same session could create a bottleneck. Mitigation: light-weight read-write locks; most operations are reads.
4. **Knowledge Runtime Dependency**: Recovery and persistence depend on Knowledge Runtime availability. Mitigation: graceful degradation to memory-only mode.
5. **LLM Summarization Latency**: Context compression using an LLM may take seconds. Mitigation: compression runs asynchronously; the context window is not blocked during compression.

### 19.2 Limitations

1. **No Cross-Session Search**: The Conversation Runtime does not support searching across sessions. Cross-session search belongs to the Knowledge Runtime.
2. **No Real-Time Transport**: The Conversation Runtime manages state but does not handle WebSocket connections or push notifications.
3. **No Message Transformation**: The Runtime stores messages as-is. Content transformation (PII redaction, format conversion) belongs to the LLM Gateway or a dedicated transform layer.
4. **No Built-In Encryption**: Message content is stored in-memory as plaintext. Encryption is the responsibility of the storage layer (Knowledge Runtime) and transport layer (API).

---

## 20. Architectural Decisions and Justifications

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| ConversationRuntime is stateful (per session) | Conversations are inherently stateful. Attempting to make them stateless would require externalizing all state to a database, adding latency and complexity with no architectural benefit. |
| Messages are immutable | Immutable messages simplify auditing, enable idempotent event processing, prevent data corruption, and make the message store append-only (fast writes). |
| Context window is token-aware, not count-based | Token-aware windows match how LLMs actually process context. A 500-token message is not the same as a 5000-token message. |
| Compression is automatic at threshold | Automatic compression prevents the context window from overflowing silently. The sender does not need to know about context limits. |
| Checkpoints are explicit, not automatic | Automatic checkpoints would create unbounded storage growth. Explicit checkpoints give callers control over what is worth saving. |
| Events are post-publish and fire-and-forget | Fire-and-forget keeps the message-sending path fast (no waiting for consumers). Post-publish ensures events are only emitted after state is committed. |
| SnapshotProducer is a separate component | Separating snapshot production from the Runtime keeps the Runtime focused on state management and the Producer focused on freezing state without side effects. |
| Sessions, threads, and messages are separate concepts | Separation enables parallel sub-conversations (threads), lifecycle management (sessions), and searchable message stores (messages) without conflating responsibilities. |
| Attachments are reference-only | Storing only attachment references keeps the Conversation Runtime lightweight and delegates storage concerns to the appropriate runtime. |

### Technical Justification

The Conversation Runtime exists because no other component in the architecture is responsible for managing conversation state. The Decision Engine makes decisions, the Policy Engine evaluates policies, the LLM Gateway communicates with providers, and the AI Execution Runtime executes tasks — but none of them track messages, manage context windows, or maintain session lifecycles. Without a dedicated Conversation Runtime, conversation state would be scattered across components, duplicated in multiple places, and inconsistent between consumers.

The key insight is that **conversations are cross-cutting**. A single conversation may involve a user, an employee, a department, a workflow, and an LLM provider. Without a central runtime, each of these participants would need to independently manage the conversation's state — leading to inconsistency, duplication, and lost context.

By centralizing conversation management, the architecture gains:
- **Consistent context**: Every participant sees the same conversation state.
- **Efficient context windowing**: Token counting and compression happen once, not N times.
- **Centralized audit**: Every message is recorded in one place.
- **Simpler participants**: Employees, workflows, and Gateways do not need to manage conversation state.
- **Recovery**: Checkpoints and persistence enable conversation recovery after failure.

### Risks

1. **Centralization bottleneck**: All conversation traffic passes through the Runtime. Mitigation: per-session locking and thread-level isolation ensure that high-traffic sessions do not block other sessions.
2. **Memory footprint**: Large conversations with many attachments consume memory. Mitigation: configurable token limits, automatic compression, size-based eviction.
3. **Event volume**: AI Execution Runtime and LLM Gateway may generate high-frequency messages. Mitigation: message batching and asynchronous event publishing.
4. **Cold start recovery**: Loading a large session from Knowledge Runtime may be slow. Mitigation: lazy loading; only session metadata is loaded on startup; messages are loaded on demand.

### Future Opportunities

1. **Conversation Branching**: Allow a conversation to fork into multiple branches at a checkpoint. Each branch explores a different path. Useful for "what if" analysis and parallel negotiation.
2. **Automated Summarization Scheduling**: Periodically summarize long-running conversations even if the context window is not full. Provides always-available summaries for new participants.
3. **Sentiment and Intent Analysis**: Annotate messages with sentiment scores and intent classifications as metadata. Enables proactive escalation and routing.
4. **Conversation Templates**: Predefined session configurations (participant roles, thread structure, retention policy) for common conversation patterns (e.g., support ticket, code review, execution trace).
5. **Multi-Modal Messages**: Support for images, audio, video, and binary attachments as first-class message content (not just references).
6. **Conversation Replay**: Replay a conversation by iterating through messages in chronological order. Useful for debugging, training, and auditing.
7. **Global Search Over Active Conversations**: Index active conversation messages for full-text search. Useful for operators monitoring multiple sessions.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/conversation/` (new module) | A new `core/conversation/` package containing `runtime.py`, `session.py`, `thread.py`, `message.py`, `context.py`, `window.py`, `compression.py`, `summary.py`, `checkpoint.py`, `snapshot.py`, `participants.py`, `attachments.py`, `events.py`, `policies.py` |
| `core/llm/runtime.py` (future) | The LLM Gateway's internal `ConversationRuntime` (section 4.5 of the LLM Gateway blueprint) delegates to this standalone Conversation Runtime instead of managing conversation state internally |
| `core/execution/runtime.py` (future) | AI Execution Runtime uses the Conversation Runtime for task execution threads, progress messages, and pre-execution checkpoints |
| `core/knowledge/runtime.py` | Must expose a `store_conversation()` and `load_conversation()` interface for conversation persistence and recovery |
| `core/skills/runtime.py` | Skills may request `ConversationContext` as input and produce messages as output; no structural changes needed |
| `core/decision/runtime.py` | Unchanged. Decision Engine may receive `ConversationSnapshot` as part of decision context, but does not interact with Conversation Runtime directly |
| `core/policies/runtime.py` | Unchanged. Policy Engine may receive `ConversationContext` for policy evaluation, but does not interact with Conversation Runtime directly |
| `EventBus` | Unchanged. New conversation event types are added, but the bus contract remains the same |
| `ObservabilityProjector` | May add a `ConversationProjector` to consume conversation events and update observability metrics |
| `ARCHITECTURE.md` | Should index this blueprint under a new section for Core Communication |
| `ENGINEERING_BLUEPRINT_LLM_GATEWAY.md` | Section 4.5 (ConversationRuntime) must be updated to reflect delegation to this standalone Conversation Runtime at implementation time |

---

## 21. Implementation Roadmap

### Phase 1 — Core Session and Message Management
- `ConversationSession`, `ConversationThread`, `ConversationMessage` data structures.
- `SessionManager`: create, get, close, list sessions.
- `ThreadManager`: create, get, close, list threads.
- `MessageStore`: store messages, paginated retrieval.
- `Participants`: registration, role management.
- `ConversationRuntime`: public entry point with `create_session`, `send_message`, `get_history`.
- **Dependency**: None (self-contained).

### Phase 2 — Context Window and Compression
- `ContextWindow`: token estimation, window calculation, utilization tracking.
- `ContextCompression`: summarization strategy (using local algorithm first, LLM Gateway later).
- `ConversationSummary`: storage and retrieval.
- Automatic compression on threshold.
- **Dependency**: May use LLM Gateway for summarization (optional in Phase 2).

### Phase 3 — Snapshots and Events
- `SnapshotProducer`: `ConversationSnapshot` and `ConversationContext` production.
- Event publishing to EventBus.
- Integration with Observability Projector.
- **Dependency**: EventBus, ObservabilityProjector.

### Phase 4 — Checkpoints and Recovery
- `MemoryCheckpoint`: save, restore, list, delete.
- Restore modes (SOFT, HARD).
- Session recovery after system restart.
- **Dependency**: Knowledge Runtime for persistence.

### Phase 5 — Knowledge Integration
- Event-driven persistence via Knowledge Runtime.
- On-demand export (`export_to_knowledge`).
- Lazy loading from Knowledge Runtime.
- **Dependency**: Knowledge Runtime.

### Phase 6 — LLM Gateway and AI Execution Runtime Integration
- LLM Gateway delegates conversation management to Conversation Runtime.
- AI Execution Runtime creates execution threads and checkpoints.
- **Dependency**: LLM Gateway, AI Execution Runtime.

### Phase 7 — Advanced Features
- Conversation branching at checkpoints.
- Automated periodic summarization.
- Multi-modal message support.
- Global search over active conversations.

---

## 22. Architectural Principles

- **Centralized State, Decentralized Access**: All conversation state lives in one runtime. All components access it through the same interface. No component manages its own conversation history.
- **Immutability of Messages**: Once stored, a message is never modified or deleted. Corrections are new messages with references to the original.
- **Immutable Snapshots**: `ConversationContext` and `ConversationSnapshot` are fully frozen. Consumers never see partial or in-flight state.
- **Fire-and-Forget Events**: State changes are committed before events are published. Consumers never block the state-changing path.
- **Isolation by Default**: Conversations are fully isolated from each other. No cross-conversation reads without explicit authorization.
- **Fail-Fast with Explanation**: Invalid operations (wrong session, wrong role, overflow) are detected early and reported with full context.
- **Graceful Degradation**: The Runtime operates in reduced-capability mode when dependencies (Knowledge Runtime, LLM Gateway) are unavailable.
- **Configurable Context**: Context window limits, compression strategies, and retention policies are configurable per session type, never hardcoded.
- **Audit by Default**: Every state change produces an event and increments the context version. No silent state changes.
- **Token Awareness**: All context management is token-aware, not message-count-aware. A 10-message thread with 10,000 tokens is treated differently from a 10-message thread with 100 tokens.

---

## 23. Final Blueprint Statement

This blueprint defines the future implementation shape of the Conversation Runtime layer while preserving the contract-first architecture of the AI Company. The Conversation Runtime is the central nervous system for all communication — it ensures that every message, every context, every checkpoint, and every snapshot is managed consistently, auditably, and efficiently.

When fully implemented, every component that sends or receives messages — users, employees, departments, workflows, the LLM Gateway, and the AI Execution Runtime — will interact through a single, consistent, observable, and recoverable conversation layer. Conversations become first-class architectural entities with explicit identity, lifecycle, versioning, and retention.

The Conversation Runtime does not replace the LLM Gateway. It enables it. The Gateway focuses on provider communication; the Runtime focuses on conversation state. Separating these concerns ensures that each component has exactly one reason to change: the Gateway changes when providers change, and the Runtime changes when conversation management changes.
