# Engineering Blueprint — LLM Gateway

## Purpose

This document is the engineering blueprint for the `LLM Gateway` of the AI Company. It defines the architecture of the sole communication channel between the company and any external language model provider. No internal component — Employee, Department, Orchestrator, or Engine — may communicate directly with OpenAI, Gemini, Claude, Ollama, OpenRouter, Groq, DeepSeek, Mistral, or any other LLM provider. Every prompt, every response, every stream, and every tool call must pass through the LLM Gateway.

This blueprint translates the conceptual need for provider isolation into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

**Why a Gateway exists:**

The AI Company depends on LLMs for execution. Without a Gateway, every Employee would need to know which provider to call, which API key to use, which model is available, how to format the prompt, and how to parse the response. This creates tight coupling between business logic and provider-specific concerns. A single provider change would ripple through every Employee. A new provider would require changes to every runtime.

**Why Employees must never know providers:**

An Employee's responsibility is to execute tasks using its skills. It must not know whether the underlying model is GPT-4o, Gemini 2.5 Pro, Claude 4 Sonnet, or a local Ollama instance. This knowledge would:
- Violate the separation of concerns.
- Make Employees unportable across company configurations.
- Require code changes when providers change pricing, deprecate models, or introduce new capabilities.
- Prevent the company from switching providers without retraining or reconfiguring every Employee.

**Why Providers must never know Employees:**

A provider receives a prompt and returns a response. It must not know about company internals — department structure, employee identities, task routing, or policy constraints. Leaking this information would:
- Create a security and privacy risk.
- Tie provider selection to internal company structure.
- Prevent the Gateway from sanitizing prompts and normalizing responses.

**How this reduces coupling:**

The Gateway introduces a single seam between the company and the outside world. All provider-specific logic lives inside `ProviderAdapter` implementations. All prompt construction lives inside `PromptBuilder`. All response normalization lives inside `ResponseParser`. When a provider changes, only the corresponding adapter changes. When a new provider joins, a new adapter is added. The rest of the company remains unaware.

---

## 1. Scope and Boundaries

### In Scope (What Belongs to the LLM Gateway)

- **Provider Routing**: Directing a request to the appropriate provider based on capability requirements, cost, and availability.
- **Capability Discovery**: Exposing what each connected provider can do (model list, context window, supported features, pricing).
- **Model Selection**: Choosing the optimal model for a given request based on prompt complexity, required output format, cost budget, and latency targets.
- **Conversation Management**: Maintaining conversation history, context windows, and message ordering for multi-turn interactions.
- **Streaming**: Handling server-sent events and partial token delivery from streaming-capable providers.
- **Retry**: Automatically retrying failed requests with configurable backoff, max attempts, and error classification.
- **Fallback**: Routing to an alternative provider or model when the primary is unavailable, rate-limited, or returning errors.
- **Timeout**: Enforcing request-level, connection-level, and total conversation timeouts.
- **Token Counting**: Estimating and counting input and output tokens for cost projection and context window management.
- **Cost Tracking**: Recording per-request, per-provider, and per-employee token usage and cost.
- **Rate Limiting**: Enforcing per-provider, per-model, and per-employee rate limits.
- **Provider Health**: Monitoring provider availability, error rates, and latency; maintaining a live health registry.
- **Prompt Dispatch**: Sending the final rendered prompt to the selected provider over the appropriate protocol (HTTP, WebSocket, gRPC).
- **Response Normalization**: Converting provider-specific response formats into a uniform internal representation.
- **Tool Calling**: Translating internal tool definitions to provider-specific formats and parsing provider-specific tool call responses back to a uniform representation.
- **Structured Output**: Ensuring the provider returns output in the requested format (JSON, Markdown, typed objects) regardless of provider-specific constraints.

### Out of Scope (What Does NOT Belong to the LLM Gateway)

- **Business Logic**: The Gateway does not decide what to ask an LLM. It receives a prompt and returns a response.
- **Task Execution**: The Gateway does not execute workflows, generate content, or produce knowledge assets.
- **Policy Evaluation**: The Gateway does not check whether a request is allowed. Policy checks belong to the Policy Engine.
- **State Mutation**: The Gateway does not update runtime state, employee state, or task state.
- **Persistence**: The Gateway does not store conversation history, prompt templates, or cost data. Persistence is delegated to the Knowledge/Result layers.
- **Employee Management**: The Gateway does not know about employee identities, roles, or capabilities beyond what is passed in the request context.

---

## 2. Separation of Concerns

Communication with LLM providers is split into three distinct layers to prevent provider coupling from leaking into company logic:

```text
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                       │
│  (Employees, Decision Engine, Orchestrator)                  │
│  Knows: what to ask, what format to expect                    │
│  Does NOT know: which provider, which model, which API key   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Sends RequestContext
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM Gateway Layer                         │
│  (LLMGateway, ProviderRegistry, PromptBuilder,               │
│   ConversationRuntime, ResponseParser)                       │
│  Knows: providers, models, prompts, formats, costs, health   │
│  Does NOT know: business logic, employee internals           │
└───────────────────────────┬─────────────────────────────────┘
                            │ Dispatches via Adapter
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Provider Adapter Layer                    │
│  (ProviderAdapter, ProviderCapabilities)                     │
│  Knows: provider-specific API, auth, protocol, format        │
│  Does NOT know: company structure, business logic            │
└─────────────────────────────────────────────────────────────┘
```

### Business Logic Layer
- **Responsibility**: Employees and Decision Engine determine what needs to be asked and what format the response should take.
- **Knowledge**: Task requirements, skill profiles, output expectations.

### LLM Gateway Layer
- **Responsibility**: Routes the request to the best provider, constructs the prompt, manages conversation state, normalizes the response.
- **Knowledge**: Provider registry, model capabilities, pricing, health status, prompt templates.

### Provider Adapter Layer
- **Responsibility**: Translates the Gateway's uniform request into the provider's specific API format and parses the provider's response back into a uniform representation.
- **Knowledge**: Provider API version, authentication method, streaming protocol, structured output mechanism.

---

## 3. Relationships and Interactions

The LLM Gateway acts as a mediated communication layer. No internal component bypasses it:

```text
 Employee (Skill Execution)
        │
        ├─► 1. Submits RequestContext (prompt, format, tools, conversation_id)
        │
        ▼
  LLM Gateway
        │
        ├─► 2. PromptBuilder renders the prompt from template + variables
        │
        ├─► 3. ModelSelector chooses best provider + model
        │
        ├─► 4. ProviderAdapter sends request to LLM provider
        │
        ├─◄ 5. Provider returns raw response (stream or complete)
        │
        ├─► 6. ResponseParser normalizes to ResponseContext
        │
        ├─► 7. TokenCounter + CostTracker record usage
        │
        └─◄ 8. Returns ResponseContext (content, tokens, cost, trace)
                 │
                 ▼
           Employee continues execution
```

- **Employees**: Submit prompts through the Gateway as part of skill execution. Receive normalized responses.
- **Decision Engine**: May query the Gateway for capability discovery (e.g., "which providers support structured JSON output?") before routing a task.
- **Orchestrator**: May query the Gateway for health and cost information to inform strategic routing decisions.
- **Policy Engine**: Validates the request before it reaches the Gateway (e.g., "is this employee authorized to use provider X?").
- **Providers**: External services that the Gateway adapters communicate with. Never directly accessed.

---

## 4. Component Breakdown

The LLM Gateway is organized as a set of logical, stateless or stateful sub-components:

```text
                       RequestContext
                            │
                            ▼
              ┌─────────────┴─────────────┐
              │       LLMGateway           │
              │  (Orchestration Entry)     │
              └──────┬──────────────┬──────┘
                     │              │
             ┌───────┴──────┐  ┌───┴──────────┐
             │ PromptBuilder│  │Conversation  │
             │ + Templates  │  │ Runtime      │
             └───────┬──────┘  └──────┬───────┘
                     │                │
                     └───────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  ModelSelector  │
                    │  + RetryPolicy  │
                    │  + FallbackPolicy│
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ ProviderRegistry│
                    │  (Adapter Map)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │OpenAI        │ │Gemini        │ │Claude        │
     │Adapter       │ │Adapter       │ │Adapter       │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            ▼                ▼                ▼
      OpenAI API         Gemini API       Claude API
                            │
                            ▼
                    ┌────────────────┐
                    │ ResponseParser │
                    └───────┬────────┘
                            │
                    ┌───────┴────────┐
                    │ ResponseContext│
                    └────────────────┘
```

### 4.1 LLMGateway (Orchestrator Entry Point)
- **Purpose**: Single public entry point for all LLM requests. Receives a `RequestContext`, orchestrates the full pipeline (prompt building → model selection → provider dispatch → response parsing → cost tracking), and returns a `ResponseContext`.
- **Execution**: Stateless orchestrator. All stateful conversation data lives in `ConversationRuntime`. The Gateway itself holds no mutable state.

### 4.2 ProviderRegistry
- **Purpose**: Registry of all connected provider adapters. Maps provider identifiers (e.g., `"openai"`, `"gemini"`, `"claude"`) to their corresponding `ProviderAdapter` instances.
- **Execution**: Populated at startup from configuration. Supports dynamic registration for hot-plugging new providers without restart.

### 4.3 ProviderAdapter
- **Purpose**: Abstract interface that every provider-specific implementation must satisfy. Translates the Gateway's uniform request into the provider's native API format and parses the provider's raw response back into a uniform `ProviderResponse`.
- **Execution**: Each provider has one adapter. Adapters are stateless and thread-safe. They handle authentication, protocol (HTTP/WebSocket/gRPC), streaming, and error mapping.

### 4.4 ProviderCapabilities
- **Purpose**: Describes what a given provider and model can do. Used by `ModelSelector` to decide whether a provider is suitable for a given request.
- **Structure** (conceptual):
  - `provider_id`: Unique provider identifier.
  - `models`: List of available models with their context window, supported features, pricing, and status.
  - `supported_features`: Streaming, structured output, tool calling, function calling, vision, audio, file upload.
  - `pricing`: Per-token input/output cost for each model.
  - `rate_limits`: Requests per minute, tokens per minute, concurrent connections.
  - `health`: Current availability status, error rate, average latency.

### 4.5 ConversationRuntime
- **Purpose**: Manages multi-turn conversation state. Maintains message history, enforces context window limits, and provides conversation-level context for prompt building.
- **Execution**: Stateful per conversation. Each conversation has a unique `conversation_id`. The runtime stores system prompts, user messages, assistant responses, and tool messages in order. It truncates or summarizes older messages when the context window is exceeded.
- **Lifecycle**: Created when a conversation starts. Messages are appended after each turn. The runtime may be persisted by the Knowledge layer for long-running conversations.

### 4.6 PromptBuilder
- **Purpose**: Constructs the final prompt string or message list from a `PromptTemplate` and a set of variables. Handles template rendering, variable substitution, and formatting.
- **Execution**: Stateless. Receives a template identifier or inline template and a variable dictionary. Returns a list of messages in the provider-agnostic format (system, user, assistant, tool).

### 4.7 PromptTemplate
- **Purpose**: Defines a reusable prompt structure with named variables, expected output format, and metadata. Templates are stored in the `PromptBuilder` registry.
- **Structure** (conceptual):
  - `template_id`: Unique identifier.
  - `version`: Semantic version for change tracking.
  - `messages`: List of message templates (system, user, assistant) with `{{variable}}` placeholders.
  - `variables`: Schema defining required and optional variables with types and validation rules.
  - `output_format`: Expected response format (JSON schema, Markdown structure, plain text).
  - `metadata`: Tags, category, author, description.

### 4.8 PromptRenderer
- **Purpose**: Renders a `PromptTemplate` with concrete variable values into the provider-agnostic message format. Handles escaping, formatting, and structural composition.
- **Execution**: Stateless. May use Jinja2, string.Template, or a custom renderer. The renderer is pluggable so different template engines can be used without changing the Gateway core.

### 4.9 ResponseParser
- **Purpose**: Normalizes provider-specific responses into a uniform `ResponseContext`. Handles JSON extraction, Markdown parsing, tool call interpretation, and error mapping.
- **Execution**: Stateless. Each provider adapter may have a specialized parser, but the `ResponseParser` provides the common interface. Structured outputs (JSON, typed objects) are validated against the expected schema.

### 4.10 TokenCounter
- **Purpose**: Estimates and counts tokens for prompts and responses. Supports multiple tokenization strategies (provider-specific, general-purpose).
- **Execution**: Stateless. May use provider-specific tokenizers (tiktoken for OpenAI, sentencepiece for Gemini) or a general counter. Returns token counts broken down by input, output, and total.

### 4.11 CostTracker
- **Purpose**: Records per-request token usage and cost. Aggregates cost by provider, model, employee, department, and time period.
- **Execution**: Stateless per request. Each call returns cost data that the caller may persist. The `CostTracker` does not store data — it computes and returns.

### 4.12 ModelSelector
- **Purpose**: Chooses the optimal provider and model for a given request based on capability requirements, cost constraints, latency targets, and provider health.
- **Execution**: Stateless. Evaluates all available providers against the request's requirements and returns a ranked list. The first available and suitable provider is selected.
- **Selection criteria**: Required capabilities (streaming, structured output, tool calling), max budget, max latency, preferred providers, excluded providers.

### 4.13 RetryPolicy
- **Purpose**: Defines when and how to retry a failed request. Handles transient errors (rate limits, timeouts, server errors) differently from permanent errors (auth failure, invalid request).
- **Execution**: Stateless configuration object. Defines max retries, base delay, backoff multiplier, and which error codes are retryable. The `LLMGateway` applies the policy during dispatch.

### 4.14 FallbackPolicy
- **Purpose**: Defines which alternative provider or model to use when the primary is unavailable or fails after exhausting retries.
- **Execution**: Stateless configuration object. Defines a prioritized list of fallback providers/models and the conditions under which each fallback is attempted.

### 4.15 StreamingController
- **Purpose**: Manages streaming responses from providers that support server-sent events or chunked transfer. Receives partial tokens and assembles them into the final response.
- **Execution**: Stateful per stream. The controller yields tokens as they arrive and assembles the complete message once the stream ends. If structured output is requested, partial JSON is buffered until a complete valid object is formed.

### 4.16 RequestContext
- **Purpose**: Immutable input containing everything the Gateway needs to process a request.
- **Structure** (conceptual):
  - `conversation_id`: Identifier for multi-turn conversations.
  - `prompt`: The prompt text or template identifier.
  - `variables`: Template variables for rendering.
  - `output_format`: Expected format (json, markdown, text, tool_calls).
  - `output_schema`: JSON Schema for structured output validation.
  - `tools`: List of tool definitions for tool-calling-capable providers.
  - `max_tokens`: Maximum output tokens.
  - `temperature`: Sampling temperature.
  - `provider_hints`: Preferred providers or models (optional).
  - `budget_max_cost`: Maximum acceptable cost for this request.
  - `employee_id`: Identifier for cost tracking and authorization.

### 4.17 ResponseContext
- **Purpose**: Immutable output containing the normalized response and metadata.
- **Structure** (conceptual):
  - `conversation_id`: Echoed from request.
  - `content`: The normalized response content (string, JSON object, or typed object).
  - `format`: The format of the content (text, json, markdown, tool_calls).
  - `tool_calls`: List of parsed tool calls, if applicable.
  - `tokens`: Token usage breakdown (input, output, total).
  - `cost`: Cost breakdown per provider.
  - `provider`: The provider and model that served the request.
  - `trace`: Execution trace (stages, timing, retries, fallback).

### 4.18 ProviderHealthMonitor
- **Purpose**: Continuously monitors provider availability, error rates, and latency. Maintains a live health registry that the `ModelSelector` consults before dispatching.
- **Execution**: Background (async in future). Updates provider health status based on request outcomes and optional health-check pings. Provides a synchronous query method: `is_available(provider_id) -> bool`.

---

## 5. Architectural Flow

```text
 Employee / Engine
        │
        ▼
 ┌──────────────────────────────────────────────────┐
 │ 1. Policy Engine (Authorization)                 │
 │    "Is this employee allowed to use LLM?"         │
 └──────────────────────┬───────────────────────────┘
                        │ Approved
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 2. LLM Gateway.ask(RequestContext)               │
 │    a. ConversationRuntime.get_or_create()         │
 │    b. PromptBuilder.render(template, variables)   │
 │    c. ModelSelector.select(capabilities, budget)  │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 3. ProviderRegistry.get(provider).dispatch()     │
 │    a. RetryPolicy.apply() if needed               │
 │    b. StreamingController.start() if stream       │
 │    c. ProviderAdapter.send(request)               │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 4. Provider (OpenAI / Gemini / Claude / etc.)    │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 5. ResponseParser.parse(raw_response)            │
 │    a. Validate against output schema             │
 │    b. Extract tool calls                          │
 │    c. Normalize to ResponseContext                │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 6. TokenCounter.count() + CostTracker.compute()  │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────┐
 │ 7. Return ResponseContext                        │
 └──────────────────────┬───────────────────────────┘
                        │
                        ▼
           Employee continues execution
```

### Why the Gateway Never Executes Actions

The Gateway is a pass-through with augmentation. It receives a prompt and returns a response. It does not:
- Decide what task to execute.
- Modify employee or task state.
- Publish events to the EventBus.
- Persist data.
- Evaluate policies.

Its sole responsibility is reliable, observable, and cost-controlled communication with LLM providers.

---

## 6. Provider Abstraction

Every provider is accessed through a `ProviderAdapter` that implements a uniform interface. Adding a new provider means writing one adapter class, registering it in the `ProviderRegistry`, and declaring its capabilities. No Employee, no Engine, and no Runtime changes.

### Adapter Interface (Conceptual)

```python
class ProviderAdapter(ABC):
    @abstractmethod
    def dispatch(self, request: ProviderRequest) -> ProviderResponse: ...
    @abstractmethod
    def dispatch_stream(self, request: ProviderRequest) -> Iterator[ProviderChunk]: ...
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...
```

### Provider-Specific Adapters

| Provider | Adapter Responsibility |
|----------|----------------------|
| **OpenAI** | Maps messages to ChatCompletion format, handles tiktoken tokenization, extracts JSON from `response_format`, maps tool definitions to `tools` parameter. |
| **Gemini** | Maps messages to `gemini-2.5-pro` content format, handles `response_mime_type` for structured output, maps function declarations. |
| **Claude** | Maps messages to Messages API format, handles tool_use blocks, extracts content from text and tool_use content blocks. |
| **OpenRouter** | Passes through to the underlying provider via OpenRouter's unified API. Adapter adds OpenRouter-specific headers (referer, title) and handles model routing. |
| **Ollama** | Maps messages to Ollama's chat format, handles streaming via NDJSON, maps tools to Ollama's tool format. No API key required. |
| **Groq** | Maps to Groq's OpenAI-compatible API. Adapter mainly configures the base URL and rate limit handling. |
| **DeepSeek** | Maps to DeepSeek's OpenAI-compatible API. Adapter handles different model naming and rate limits. |
| **Mistral** | Maps to Mistral's chat completion format, handles function calling via Mistral's `tools` syntax. |
| **Azure OpenAI** | Same as OpenAI adapter but with Azure-specific endpoint, API version header, and Entra ID authentication. |
| **Vertex AI** | Maps to Vertex AI's Gemini format, handles Google Cloud authentication via service account credentials. |

Each adapter is responsible for:
1. **Authentication**: Injecting the correct API key, token, or credential.
2. **Request Mapping**: Translating the uniform `ProviderRequest` into the provider's native format.
3. **Response Parsing**: Extracting content, tool calls, and metadata from the provider's native response.
4. **Error Mapping**: Converting provider-specific errors into uniform error codes.
5. **Streaming**: Yielding tokens as they arrive and signaling stream completion.

```text
ProviderAdapter (uniform interface)
    │
    ├── OpenAIAdapter    ──── OpenAI API
    ├── GeminiAdapter    ──── Gemini API
    ├── ClaudeAdapter    ──── Claude API
    ├── OpenRouterAdapter ─── OpenRouter API
    ├── OllamaAdapter    ──── Ollama Local
    ├── GroqAdapter      ──── Groq API
    ├── DeepSeekAdapter  ──── DeepSeek API
    ├── MistralAdapter   ──── Mistral API
    ├── AzureOpenAIAdapter ── Azure OpenAI
    └── VertexAIAdapter  ──── Vertex AI
```

---

## 7. Prompt System

The Prompt System isolates prompt construction from provider-specific formatting and from business logic.

### Prompt Templates

Templates are stored in a registry and referenced by `template_id`. They define the prompt structure without hardcoding content.

```text
Template: "code_review"
  System: "You are a senior code reviewer. Review the following code for {{language}}.
           Focus on: {{focus_areas}}. Respond in {{output_format}}."
  User: "{{code}}"
  Variables:
    - language: string, required
    - focus_areas: list[string], required
    - output_format: enum[json, markdown, text]
    - code: string, required
```

### Prompt Rendering

The `PromptBuilder` receives a `template_id` and a `variables` dictionary. It:
1. Loads the template from the registry.
2. Validates that all required variables are present.
3. Renders each message template with the variable values.
4. Returns a provider-agnostic message list.

### Prompt Variables

Variables are named placeholders in templates. They are validated against a schema at render time:
- **Required variables**: Must be present; error if missing.
- **Optional variables**: May be omitted; default value or empty string used.
- **Typed variables**: Enforced at render time (string, number, list, object).

### Prompt Versioning

Each template has a semantic version. When a template is updated, previous versions remain accessible. The `RequestContext` may specify a version constraint:
- `template_id = "code_review"` → latest version.
- `template_id = "code_review@1.2.0"` → specific version.
- `template_id = "code_review@^1.0.0"` → compatible range.

### Prompt Assets

Assets are reusable prompt fragments (few-shot examples, instruction blocks, format specifications) that can be composed into templates. They live in the registry alongside templates.

### Prompt Validation

Before rendering, the `PromptBuilder` validates:
- Template exists and is enabled.
- All required variables are provided and correctly typed.
- Total estimated tokens do not exceed the target model's context window.
- Output format is compatible with the template definition.

### Prompt Contracts

A prompt contract defines the formal interface between a caller and the prompt system:
```text
PromptContract:
  template_id: str
  input_schema: JSON Schema (validates variables)
  output_schema: JSON Schema (validates response)
  max_tokens: int
  required_capabilities: list[str] (e.g., streaming, structured_output)
```

Contracts enable compile-time or runtime validation that the caller and the prompt are compatible.

---

## 8. Structured Output

The Gateway must return structured data without requiring Employees to parse raw provider responses.

### Supported Output Formats

| Format | Mechanism | Providers |
|--------|-----------|-----------|
| **JSON** | `response_format={ "type": "json_object" }` or `response_mime_type="application/json"` | OpenAI, Gemini, Claude, OpenRouter, Groq, DeepSeek, Mistral |
| **JSON Schema** | `response_format={ "type": "json_schema", "schema": {...} }` | OpenAI, Gemini (via `response_mime_type` + `response_schema`) |
| **Markdown** | No special parameter; content extracted and passed as-is | All |
| **Text** | No special parameter | All |
| **Tool Calls** | Provider-specific tool/function calling format | OpenAI, Claude, Gemini, Mistral, Groq |

### Structured Output Pipeline

```text
RequestContext.output_schema (JSON Schema)
    │
    ▼
PromptBuilder includes schema in system prompt
    │
    ▼
ProviderAdapter sets provider-specific structured output params
    │
    ▼
Provider returns structured response (JSON or tool call)
    │
    ▼
ResponseParser validates against JSON Schema
    │
    ▼
ResponseParser converts to python object or typed dataclass
    │
    ▼
ResponseContext.content = typed object
```

### Benefits

- **Employee never parses raw JSON**: The Gateway validates and converts before returning.
- **Schema enforcement**: Invalid responses are caught at the Gateway level, not in Employee code.
- **Provider independence**: JSON Schema works across all providers that support structured output. For providers that do not, the `ResponseParser` falls back to extracting JSON from the text response.
- **Tool Calling as structured output**: When tools are provided, the Gateway can request the provider to call a tool instead of returning free-form text, guaranteeing a structured response.

---

## 9. Conversation Runtime

The `ConversationRuntime` maintains the state required for multi-turn interactions with an LLM.

### State per Conversation

- `conversation_id`: UUID identifying the conversation.
- `system_prompt`: The base system instruction, set at conversation creation.
- `messages`: Ordered list of messages (user, assistant, tool, system).
- `context_window`: Maximum token count for the target model.
- `token_count`: Running total of tokens in the conversation.
- `metadata`: Tags, employee_id, task_id, workflow_id for tracing.

### Context Window Management

When the running token count approaches the context window limit:

1. **Summarization**: Older messages are summarized into a condensed representation, preserving key information.
2. **Sliding Window**: The oldest messages are dropped when the window is exceeded. Configurable retention policy (keep system prompt + last N messages).
3. **Truncation**: If summarization and sliding window are insufficient, the system prompt is preserved and older messages are discarded.

### Memory

Beyond the current conversation, the `ConversationRuntime` may reference a `MemoryStore` (future) for cross-conversation recall. This is not implemented in the first version but is designed as an optional extension point.

### Message Types

- **System Prompt**: Set once at conversation creation. Not counted against the conversation budget for summarization.
- **User Messages**: Input from the Employee or system.
- **Assistant Messages**: Previous responses from the LLM.
- **Tool Messages**: Results of tool calls, fed back to the LLM for further processing.

---

## 10. Costs

### TokenCounter

The `TokenCounter` estimates and counts tokens for any text or message list.

- **Provider-specific tokenizers**: Uses tiktoken for OpenAI models, sentencepiece for Gemini, claude-tokenizer for Anthropic.
- **General-purpose estimator**: Approximates tokens as `len(text) / 4` when no provider-specific tokenizer is available.
- **Counting modes**: `estimate` (fast, before dispatch) and `count` (accurate, after response).

### CostTracker

The `CostTracker` computes cost from token counts and provider pricing.

```text
cost = (input_tokens * input_price_per_token) + (output_tokens * output_price_per_token)
```

- **Provider Pricing**: Loaded from `ProviderCapabilities.pricing`.
- **Per-request cost**: Returned in `ResponseContext.cost`.
- **Aggregation**: The caller (or a projector) may aggregate costs by employee, department, provider, or time period.

### Provider Pricing Model (Conceptual)

```python
@dataclass
class ModelPricing:
    model_id: str
    input_price_per_1k_tokens: Decimal
    output_price_per_1k_tokens: Decimal
    currency: str = "USD"
```

### Budget Policies

- **Per-request budget**: `RequestContext.budget_max_cost` caps individual request cost.
- **Per-employee budget** (future): Aggregate daily/weekly/monthly limits.
- **Per-provider budget** (future): Maximum spend per provider in a billing cycle.

### Cost Projection

Before dispatching a request, the `TokenCounter` estimates input tokens and the `CostTracker` projects the expected cost. If the projected cost exceeds the budget, the request is rejected before any provider API call.

---

## 11. Observability

The Gateway emits structured events that the Observability layer consumes via projectors. These events are not published directly by the Gateway — they are emitted by the caller or captured by an `EventBus` subscriber that wraps the Gateway call.

### Events

| Event | Payload | Trigger |
|-------|---------|---------|
| `LLMRequestStarted` | `conversation_id`, `provider`, `model`, `estimated_tokens`, `employee_id`, `task_id` | Before provider dispatch |
| `LLMRequestFinished` | `conversation_id`, `provider`, `model`, `tokens`, `cost`, `duration_ms`, `success` | After response parsed |
| `ProviderSelected` | `provider_id`, `model_id`, `selection_reason` | After `ModelSelector` decision |
| `RetryExecuted` | `conversation_id`, `provider`, `attempt`, `error_code`, `delay_ms` | On retry |
| `FallbackExecuted` | `conversation_id`, `from_provider`, `to_provider`, `reason` | On fallback |
| `StreamingStarted` | `conversation_id`, `provider`, `model` | Stream start |
| `StreamingFinished` | `conversation_id`, `total_tokens`, `duration_ms` | Stream end |
| `TokenUsageCalculated` | `conversation_id`, `input_tokens`, `output_tokens`, `total_tokens` | After token count |
| `CostCalculated` | `conversation_id`, `cost`, `currency`, `provider` | After cost computation |
| `ProviderUnavailable` | `provider_id`, `model_id`, `error_code`, `duration_seconds` | On provider error |

### Observability Consumption

The `ObservabilityProjector` (or a dedicated `LLMGatewayProjector`) subscribes to these events and updates:
- Provider health dashboard.
- Cost dashboard per employee/department.
- Token usage trends.
- Average latency per provider.
- Error rates and retry frequency.

---

## 12. Security

### Secrets and API Keys

- **No secrets in code**: All API keys and credentials are loaded from environment variables or a secrets manager at startup.
- **No secrets in logs**: The Gateway must redact API keys, bearer tokens, and credentials from all log output, error messages, and trace data.
- **Per-provider credentials**: Each `ProviderAdapter` receives its credentials at construction time, not at request time.

### Credential Providers (Conceptual)

```python
class CredentialProvider(ABC):
    @abstractmethod
    def get_credentials(self, provider_id: str) -> dict[str, str]: ...
```

Implementations may read from environment variables, a `.env` file, Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault. The Gateway core does not know which implementation is in use.

### Provider Isolation

- Each provider adapter operates in isolation. A credential leak in one adapter does not affect others.
- Provider adapters do not share network connections, sessions, or connection pools by default.

### PII and Prompt Sanitization

The Gateway may optionally sanitize prompts before sending them to external providers:
- Strip or mask email addresses, phone numbers, and other PII patterns.
- Replace employee names with anonymous identifiers.
- Remove internal URLs, IP addresses, and hostnames.

Sanitization is implemented as an optional pre-processing step in the `PromptBuilder` pipeline. It is disabled by default and enabled per-request via `RequestContext.sanitize_pii`.

### Prompt Isolation

Prompts from different employees or departments must be isolated. The `ConversationRuntime` enforces isolation by:
- Never sharing conversation state between different `conversation_id` values.
- Never leaking one employee's conversation history to another.
- Clearing conversation state when a conversation ends.

---

## 13. Future AI Capabilities

The Gateway architecture anticipates several intelligent features without requiring core changes.

### Intelligent Model Routing

A future `ModelSelector` implementation may use ML to predict the best provider for a given prompt based on:
- Historical success rates per provider per task type.
- Current provider latency and availability.
- Cost optimization across multiple providers.
- Prompt complexity estimation.

### Ensemble of Models

The Gateway may send the same prompt to multiple providers and aggregate results:
- **Voting**: Select the most common answer across models.
- **Confidence weighting**: Weight responses by each model's confidence score.
- **Complementary answers**: Use different models for different parts of a complex task.

### Auto Selection

When `RequestContext.provider_hints` is empty, the `ModelSelector` automatically selects the best provider based on:
1. Capability requirements (structured output, tool calling, streaming).
2. Cost constraints (budget_max_cost).
3. Provider health (availability, error rate, latency).
4. Historical performance for similar requests.

### A/B Testing

The Gateway may support provider-level A/B testing:
- A percentage of requests for a given template are routed to a candidate provider.
- Response quality, cost, and latency are compared.
- The better performer is promoted to production.

### Multi-model Responses

A single request may be answered by multiple models in parallel. The Gateway:
1. Dispatches to N providers simultaneously.
2. Collects all responses.
3. Returns the best response (by configurable criteria) or a composite answer.

### Caching

- **Exact cache**: If the exact same prompt was sent before, return the cached response.
- **Semantic cache**: If a semantically similar prompt was sent before (within a similarity threshold), return the cached response. Requires an embedding model and vector store.

### Semantic Cache

```text
Prompt
  │
  ▼
Embedding (vector representation)
  │
  ▼
Vector DB lookup
  │
  ├── Hit: return cached response
  └── Miss: dispatch to provider → cache response + embedding
```

---

## 14. Relationship with Existing Architecture

### ARCHITECTURE.md

This blueprint adds the `LLM Gateway` as a new architectural component. It should be indexed under section 8 (Blueprints de Engenharia), within a new subsection "8.5 LLM and Provider Integration" alongside the AI Director and Platform Director blueprints.

### COMPANY_RUNTIME_ARCHITECTURE.md

The Company Runtime maintains operational state that the Gateway references:
- Company lifecycle state (is the company in maintenance mode? If so, disable expensive providers).
- Employee availability (is the requesting employee active?).

The Gateway does not modify runtime state. It reads from snapshots at request time.

### MESSAGE_SYSTEM_ARCHITECTURE.md

The Message System may carry LLM-related signals:
- LLM request completion notifications.
- Cost alerts ("Department X has exceeded 80% of its monthly LLM budget").
- Provider availability warnings ("OpenAI is currently degraded").

Messages never carry prompt content or API keys. They represent operational awareness of the Gateway's status.

### OBSERVABILITY_ARCHITECTURE.md

Observability provides visibility into:
- Per-provider token usage and cost.
- Request latency by model and provider.
- Error rates and retry frequency.
- Cache hit rates (future).
- Provider health status.

The Gateway emits events (via the caller) that the `ObservabilityProjector` consumes. A dedicated `LLMGatewayProjector` may update observability snapshots with cost and usage data.

### ENGINEERING_BLUEPRINT_DECISION_ENGINE.md

The Decision Engine does not use the Gateway directly for decision making. However, the `Recommendation Layer` (future AI) described in the Decision Engine blueprint may use the Gateway to obtain LLM-based ranking suggestions. In that scenario:
1. The `Recommendation Layer` submits a prompt via the Gateway.
2. The Gateway routes, dispatches, and returns a normalized response.
3. The `Recommendation Layer` passes the suggestion to the `ConstraintValidator` before approval.
4. The Policy Engine validates the action before any state change.

### ENGINEERING_BLUEPRINT_POLICY_ENGINE.md

The Policy Engine validates actions before they reach the Gateway:
- "Is this employee authorized to use provider X?"
- "Is this department allowed to use model Y?"
- "Has this employee exceeded the daily LLM budget?"

The Gateway does not evaluate policies. It receives the `RequestContext` after policy approval.

### ENGINEERING_BLUEPRINT_EMPLOYEE.md

The Employee blueprint describes how Employees use skills to execute tasks. When a skill requires an LLM call, the Employee:
1. Constructs a `RequestContext` with the prompt, variables, and expected output format.
2. Calls `LLMGateway.ask(request_context)`.
3. Receives a `ResponseContext`.
4. Extracts the content and continues execution.

The Employee never knows which provider served the request, how much it cost, or whether a retry or fallback occurred.

---

## 15. Architectural Risks

### 15.1 Single Point of Failure
- **Risk**: Every LLM call passes through the Gateway. If the Gateway is down, the entire company loses LLM access.
- **Mitigation**: The Gateway is stateless for individual requests. Multiple instances can run behind a load balancer. The `ProviderHealthMonitor` detects provider outages independently.

### 15.2 Latency Overhead
- **Risk**: The Gateway adds processing time (template rendering, token counting, response parsing) to every LLM call.
- **Mitigation**: All Gateway components are designed to be fast (microseconds for rendering, O(1) for provider lookup). Streaming responses begin before parsing is complete. Token counting uses cached tokenizers.

### 15.3 Cost Tracking Accuracy
- **Risk**: Token counts may differ between the Gateway's counters and the provider's billing.
- **Mitigation**: Provider-specific tokenizers are used where available. The `CostTracker` records the Gateway's computed cost; the provider's invoice is the source of truth. Discrepancies are logged for reconciliation.

### 15.4 Provider API Drift
- **Risk**: Providers may change their API without notice, breaking adapters.
- **Mitigation**: Each adapter is version-pinned to a specific API version. Integration tests run against each provider's API. The `ProviderHealthMonitor` detects breaking changes from error patterns.

### 15.5 Prompt Injection
- **Risk**: User-controlled content in prompts may cause the LLM to ignore instructions or leak system prompts.
- **Mitigation**: The `PromptBuilder` enforces template structure. User content is placed in designated variables, not interpolated into system prompts. The `RequestContext` supports a `sanitize_pii` option. Future versions may add prompt injection detection.

### 15.6 Vendor Lock-in Avoidance
- **Risk**: Skills may be written to depend on a specific provider's behavior (e.g., a specific JSON format, a specific reasoning style).
- **Mitigation**: All output is normalized by the `ResponseParser`. Skills should not depend on provider-specific behavior. The `ModelSelector` rotates providers transparently.

---

## 16. Benefits

### 16.1 Complete Provider Isolation
No internal component knows which provider is serving its requests. Providers can be added, removed, or swapped without changing a single line of business logic.

### 16.2 Unified Observability
All LLM usage — across all providers, all departments, all employees — is visible from a single point. Cost, tokens, latency, and errors are aggregated automatically.

### 16.3 Centralized Security
API keys live in one place. Credential rotation affects all providers simultaneously. Prompt sanitization and PII protection are applied consistently.

### 16.4 Cost Control
Per-request budgets, per-employee limits, and provider-level cost tracking prevent cost surprises. The `CostTracker` projects cost before dispatch, rejecting over-budget requests before they reach the provider.

### 16.5 Provider Agnosticism
Skills are written once and work with any provider. The company can use GPT-4o for complex reasoning, Gemini for long context, Claude for safety, and Ollama for local development — all without Employee changes.

### 16.6 Resilience
Retry policies, fallback chains, and health monitoring ensure that provider outages do not block the company. Transient errors are handled automatically.

### 16.7 Evolutionary Path
The Gateway architecture supports intelligent routing, caching, ensembling, and A/B testing without core changes. These features are additive.

---

## 17. Future Roadmap

The LLM Gateway should be implemented incrementally. Each phase adds capabilities while remaining backward-compatible.

### Phase 1: Foundation

```
ProviderRegistry ─── ProviderAdapter (OpenAI) ─── PromptBuilder ─── TokenCounter
```

- Implement the core interfaces (`ProviderAdapter`, `ProviderRegistry`, `PromptBuilder`).
- Implement a single adapter (OpenAI) to validate the architecture.
- Implement basic `TokenCounter` and `CostTracker`.
- Implement `LLMGateway.ask()` without streaming, retry, or fallback.

### Phase 2: Provider Expansion

```
Add adapters: Gemini, Claude, OpenRouter, Ollama
```

- Implement `ProviderCapabilities` for each provider.
- Implement `ModelSelector` with basic selection logic.
- Validate that the same prompt produces equivalent results across providers.

### Phase 3: Prompt System

```
PromptTemplate ─── PromptRenderer ─── PromptVersioning ─── PromptValidation
```

- Implement the template registry with versioning.
- Implement `PromptRenderer` with variable substitution and validation.
- Create initial prompt contracts for common skill types.

### Phase 4: Conversation Runtime

```
ConversationRuntime ─── ContextWindow ─── Message History
```

- Implement multi-turn conversation support.
- Implement context window management.
- Implement conversation lifecycle (create, append, end).

### Phase 5: Resilience

```
RetryPolicy ─── FallbackPolicy ─── ProviderHealthMonitor ─── Timeout
```

- Implement retry with exponential backoff.
- Implement fallback chains.
- Implement request and connection timeouts.

### Phase 6: Streaming

```
StreamingController ─── SSE ─── Chunk Assembly
```

- Implement streaming for all providers that support it.
- Implement partial content delivery to callers.
- Implement stream-level token counting.

### Phase 7: Structured Output

```
JSON Schema ─── Response Validation ─── Typed Objects
```

- Implement `output_schema` validation.
- Implement typed object deserialization.
- Implement fallback parsing for providers without native structured output.

### Phase 8: Advanced Providers

```
Add adapters: Groq, DeepSeek, Mistral, Azure OpenAI, Vertex AI
```

- Implement remaining adapters.
- Validate that all adapters produce consistent `ResponseContext` output.

### Phase 9: Tool Calling

```
Tool Definitions ─── Tool Call Parsing ─── Tool Result Injection
```

- Implement tool definition translation.
- Implement tool call extraction and parsing.
- Implement tool result injection into conversation flow.

### Phase 10: Employee Integration

```
Employee Skill Bridge ─── RequestContext Construction ─── Response Consumption
```

- Integrate the Gateway with Employee skill execution.
- Replace direct provider calls in existing skills with Gateway calls.
- Remove all provider-specific code from Employee implementations.

### Future (Post-Phase 10)

```
Intelligent Routing ─── Caching ─── Semantic Cache ─── Ensemble ─── A/B Testing
```

- ML-based `ModelSelector`.
- Exact and semantic caching.
- Multi-model ensemble.
- Provider A/B testing framework.

---

## 18. Validation

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Gateway is the sole LLM entry point | Prevents provider coupling from spreading across the codebase |
| ProviderAdapter is the only provider-aware component | Adding a new provider requires no changes outside the adapter |
| PromptBuilder separates template from rendering | Templates can be versioned, tested, and audited independently |
| ResponseParser normalizes all output | Employees receive uniform responses regardless of provider |
| ConversationRuntime is stateful; Gateway is stateless | Conversations need state; the orchestration layer should not |
| CostTracker computes but does not persist | Separation of concerns: the Gateway processes, the Knowledge layer stores |
| No provider secrets in Gateway core | Security: credentials are injected, not hardcoded |

### Technical Justification

The Gateway follows the **Dependency Inversion Principle**: High-level components (Employees) depend on abstractions (the Gateway interface), not on concrete implementations (provider-specific API calls). Low-level components (Adapters) implement those abstractions. This allows both to evolve independently.

The layered architecture (Business Logic → Gateway → Adapter → Provider) ensures that:
- Business logic never imports provider SDKs.
- Provider API changes affect only the adapter.
- Prompt template changes affect only the template registry.
- Response format changes affect only the parser.

### Risks

1. **Over-engineering for initial needs**: The first version may only need OpenAI. The blueprint should be treated as a guide; implement only what Phase 1 requires.
2. **Provider API instability**: Adapters may break when providers update their APIs. Mitigation: pin API versions, run integration tests.
3. **Cost tracking complexity**: Provider pricing is non-standard (some charge by token, others by character, others by request). The `CostTracker` must normalize these.
4. **Streaming state management**: Streaming requires maintaining state across multiple callbacks. The `StreamingController` must handle partial responses, errors during stream, and stream cancellation.

### Future Opportunities

1. **Multi-modal support**: Extend the Gateway to handle image, audio, and video inputs for multimodal models.
2. **Federated routing**: Route requests to private (on-premise) or public providers based on data sensitivity.
3. **LLM benchmarking**: Use the Gateway's observability data to compare provider quality, cost, and latency over time.
4. **Auto-generated prompt contracts**: Infer prompt contracts from template usage patterns.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/` (new module) | A new `core/llm/` package containing `gateway.py`, `adapters/`, `prompts/`, `conversation/`, `cost/` |
| `core/policies/` | Policy Engine may add `llm_authorization` and `llm_budget` policies |
| `core/observability.py` | May add an `LLMGatewayProjector` to consume Gateway events |
| `EventBus` | Unchanged. Gateway-related events are published by the caller or an `EventBus` subscriber wrapping the Gateway |
| `engines/` | All engine scripts and providers currently have direct LLM calls. These must be replaced with Gateway calls in Phase 10 |
| `core/decision/` | Unchanged. The Decision Engine does not call the Gateway directly |
| `core/knowledge/` | May persist conversation history and cost data from the Gateway |
| `ARCHITECTURE.md` | Should index this blueprint under a new "8.5 LLM and Provider Integration" section |

---

## 19. Architectural Principles

- **Provider Agnosticism**: The Gateway must treat all providers equally. No provider-specific logic outside its adapter.
- **Immutability of Inputs**: `RequestContext` and `ResponseContext` are immutable. The Gateway never mutates caller data.
- **Fail-Fast**: Over-budget requests, invalid templates, and unauthorized providers are rejected before any provider API call.
- **Observability by Default**: Every request produces trace data. Cost, tokens, and latency are always recorded.
- **Security by Isolation**: Credentials are injected, not hardcoded. Provider adapters are isolated from each other.
- **Backward Compatibility**: New providers, models, and features must not break existing callers. The `ResponseContext` schema is extensible via metadata fields.

---

## 20. Final Blueprint Statement

This blueprint defines the future implementation shape of the LLM Gateway layer while preserving the contract-first architecture of the AI Company. The Gateway is not an engine, not a runtime, and not a decision layer. It is the company's single, secure, observable, and cost-controlled window to the world of language models.

When fully implemented, no Employee, no Department, no Engine, and no Runtime will know or care which provider serves their requests. The Gateway absorbs all provider complexity, leaving the rest of the company free to focus on business logic.
