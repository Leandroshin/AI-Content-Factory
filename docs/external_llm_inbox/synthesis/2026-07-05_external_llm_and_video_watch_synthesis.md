# External LLM Ideas + Video Watch Skill Synthesis

Date: 2026-07-05
Owner: Codex
Status: reviewed input, accepted sequence updated

## Inputs Reviewed

- `RespostaLLMS/DEEPSEEK.txt`
- `RespostaLLMS/Gemini 3.5.txt`
- `RespostaLLMS/GLM5.2.txt`
- `RespostaLLMS/METAAI.txt`
- Qwen proposal archived at `docs/external_llm_inbox/qwen/2026-07-05_hook_hitl_repurposing.md`
- `bradautomates/claude-video` local audit in `temp/external/claude-video`

## Convergence

The useful external responses converge on the same order:

1. Human approval before publishing.
2. Hook/opening specialist.
3. Publishing planner for channels and schedules.
4. Repurposing/video intake.
5. Dashboard/2.5D operational view.
6. Analytics and performance feedback.

MetaAI mostly echoed the prompt and did not add a concrete architecture proposal.

## Accepted Build Order

1. Implement HITL approval queue/gateway.
2. Connect Telegram publication to the approval gate.
3. Add Publishing Planner once approval is stable.
4. Add Hook Master as a Script Department specialist.
5. Add Video Intake/Repurposing after approval + publishing planner.
6. Feed analytics into dashboard and later optimization loops.

## `claude-video` Audit

The repository is useful but should not be copied into `core/`.

Useful concepts:

- Captions first to avoid unnecessary video download.
- `yt-dlp` for public video metadata/download when allowed.
- `ffmpeg` for frame extraction.
- Frame budgets by detail level to control token usage.
- Scene/keyframe sampling plus transcript-cue timestamps.
- Optional Whisper fallback only when captions are missing.

Recommended adaptation:

- Future adapter: `VideoIntakeAdapter` or `YtDlpVideoIngestAdapter`.
- Future adapter: `FFmpegFrameSamplerAdapter`.
- Future department: Repurposing Department or Video Research Employee.
- First product use: transform long videos into short scripts/clips with owner approval.

Constraints:

- Keep the external repo as reference/optional local skill, not a required dependency.
- Respect platform terms, copyright, and private/paid content boundaries.
- Do not mass-download or scrape.
- Provider/API use must remain opt-in, budget-limited, and approval-gated.

## Current Decision

Proceed with HITL Approval Gateway now. It protects Telegram publishing, future
video repurposing, paid providers, and automated content distribution.
