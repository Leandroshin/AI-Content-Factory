# Qwen Proposal - Hook Master, HITL Gateway, Repurposing Department

Status: external proposal, not accepted source of truth.

Source: pasted into Codex by Shin on 2026-07-05.

Codex note: the concepts are useful, but several suggested paths from the
external answer need adaptation to the current architecture. Future
implementation should prefer `core/departments/<name>/` for departments and
should keep provider calls approval-gated and budget-limited.

## 1. Hook Master

### Objective

Hook Master is a specialized employee focused on the first 3 to 5 seconds of a
video script. It analyzes topic and audience to produce multiple opening hooks
using different triggers such as curiosity, fear, promise, contrast, or
identification before the main script is generated.

### Why It Matters

Initial retention is critical for TikTok, Reels, and Shorts. A strong video can
fail if the opening is weak. Centralizing hook generation allows fast iteration
without rewriting the whole script.

### Type

Employee.

### Architecture Fit

- Should extend `ProductionEmployee`.
- Should likely live under a Script or Content Strategy department.
- Can run before `ScriptWriterEmployee`.
- Should output a `StageResult` containing selected and alternative hooks.
- Can be measured by `ObservabilityProjector`.
- Can later use provider-backed LLM generation through `ProviderControlCenter`.

### Suggested Files

Preferred adapted structure:

```text
core/departments/script/hooks.py
core/departments/script/hook_master.py
demo_hook_master_employee.py
```

Alternative if it becomes its own department:

```text
core/departments/hooks/models.py
core/departments/hooks/pipeline.py
core/departments/hooks/employee.py
core/departments/hooks/__init__.py
demo_hooks_department.py
```

### Proposed Pipeline

1. Receive topic and audience.
2. Select hook strategies.
3. Generate hook candidates.
4. Validate length and relevance.
5. Score candidates.
6. Select winner.
7. Deliver selected hook and alternatives.

### Inputs

- `topic`
- `audience_profile`
- `platform`
- `raw_research_data`
- `tone`
- `content_promise`

### Outputs

- `selected_hook`
- `hook_strategy_used`
- `alternative_hooks`
- `estimated_retention_score`
- `validation_issues`

### Quality Rules

- Hook should be speakable in less than 5 seconds.
- Hook should contain at least one relevant topic keyword.
- Hook should clearly use one configured strategy.
- Hook should not promise something the content does not deliver.
- Recent hook patterns should be checked to avoid repetition.

### Risks and Compliance

- Risk: misleading clickbait.
- Mitigation: compare hook promise to script/content summary.
- Risk: repetitive hooks.
- Mitigation: keep recent hook history and penalize repeated patterns.

### MVP

Template-based generation of 3 hooks:

- Question hook.
- Contrarian statement hook.
- List/promise hook.

No real provider call required for the first version.

### Future

- Learn from analytics and retention data.
- Suggest opening visuals alongside the verbal hook.
- Adapt strategy by channel and niche.

## 2. HITL Gateway

### Objective

HITL Gateway is a human-in-the-loop approval layer that pauses automated
pipelines at sensitive points and waits for explicit approval, rejection, or
future edits before continuing.

### Why It Matters

Full automation can publish factual errors, weak copy, policy-risky claims, or
off-brand content. Human approval preserves trust while allowing the factory to
scale.

### Type

Gateway / Infrastructure.

### Architecture Fit

- Should connect naturally to `TelegramAdapter`.
- Should initially focus on approval queue for `AffiliateDealsEmployee`
  publishing.
- Should persist approval state.
- Should emit events for `ObservabilityProjector`.
- Should integrate with `QualityRuntime` as an approval/compliance stage.

### Suggested Files

Preferred adapted structure:

```text
core/approval/models.py
core/approval/runtime.py
core/approval/telegram_gateway.py
demo_hitl_approval_gateway.py
```

If kept narrower at first:

```text
core/content_factory/approval_queue.py
demo_telegram_approval_queue.py
```

### Proposed Pipeline

1. Receive content item from previous stage.
2. Create approval request.
3. Send preview through Telegram or dashboard.
4. Enter pending state.
5. Receive approve/reject/edit decision.
6. Store immutable decision log.
7. Resume, block, or return content for correction.

### Inputs

- `content_item`
- `context_message`
- `allowed_actions`
- `timeout_config`
- `reviewer`
- `destination_channel`

### Outputs

- `approval_status`
- `modified_content`
- `reviewer_id`
- `review_timestamp`
- `decision_reason`

### Quality Rules

- Pipeline must not proceed after timeout.
- Decision log should preserve original and final content.
- Approval must include reviewer and timestamp.
- Sensitive data must not be exposed in approval previews.
- Publishing adapters must still require explicit approval flags.

### Risks and Compliance

- Risk: approval bottleneck.
- Mitigation: batch approvals for low-risk items later.
- Risk: context loss during review.
- Mitigation: include task context and quality summary with the preview.

### MVP

Telegram message with two actions:

- Approve.
- Reject with reason.

No editing in the MVP. Approval result can be simulated deterministically in a
demo before real callback handling.

### Future

- Web dashboard with diff viewer.
- Multi-level approvals.
- Learning loop based on recurring edits.

## 3. Repurposing Department

### Objective

Repurposing Department takes a parent content asset such as a long video,
podcast, or article and produces multiple child assets: short clips, posts,
captions, carousel outlines, and platform-specific variants.

### Why It Matters

Original content is expensive. Repurposing increases output and ROI from one
master asset, allowing the factory to produce more without starting from zero.

### Type

Department.

### Architecture Fit

- Should use `ProductionEmployee` and `ProductionPipeline`.
- Should coordinate existing Script, Video, Image, and future Subtitle
  employees.
- Should use provider controls for transcription/video processing.
- Should report parent-child asset metrics through `ObservabilityProjector`.
- Can later integrate with `TelegramAdapter` and publishing approvals.

### Suggested Files

```text
core/departments/repurposing/models.py
core/departments/repurposing/pipeline.py
core/departments/repurposing/employee.py
core/departments/repurposing/__init__.py
demo_repurposing_department.py
```

Potential future helpers:

```text
core/content_factory/asset_tree.py
core/departments/video/clip_cutter.py
```

### Proposed Pipeline

1. Ingest parent asset and transcript.
2. Validate rights and source metadata.
3. Identify candidate moments.
4. Score moments.
5. Select top clips.
6. Create child asset plans.
7. Generate captions/context.
8. Prepare render instructions.
9. Package output and mapping report.

### Inputs

- `parent_asset_id`
- `parent_transcript`
- `timestamped_segments`
- `target_platforms`
- `clip_criteria`
- `rights_metadata`

### Outputs

- `child_assets`
- `mapping_report`
- `metadata_tags`
- `render_instructions`
- `approval_queue_items`

### Quality Rules

- Each clip should make sense without the full parent context.
- Duration should fit target platform, usually 15 to 59 seconds for shorts.
- Format should match 9:16 for vertical platforms.
- Source rights should allow derivative content.
- Abrupt cuts should be flagged.

### Risks and Compliance

- Risk: losing context and creating misleading clips.
- Mitigation: context validation and optional intro caption.
- Risk: high processing cost.
- Mitigation: score and select only top candidates before rendering.
- Risk: rights misuse.
- Mitigation: require license/source metadata.

### MVP

Manual-trigger workflow:

1. User provides transcript with timestamps.
2. System selects 3 moments using deterministic heuristics.
3. System creates child asset plans and simple cut instructions.

Rendering and advanced subtitles can come later.

### Future

- Audio/visual viral moment detection.
- Scheduled publishing drip.
- Cross-linking from short clips to long-form content.
