# HyperFrames editorial standard

Updated on 2026-07-11 from the supplied transcript and verified HyperFrames
documentation.

## Decision

Adopt HyperFrames as a deterministic motion/editorial engine alongside FFmpeg.
FFmpeg remains the reliable local encoder and fallback. HyperFrames composes
HTML, CSS, captions, motion graphics, media and repeatable layouts.

Installed Codex skills:

- hyperframes-core;
- hyperframes-cli;
- hyperframes-animation;
- hyperframes-creative;
- embedded-captions;
- general-video;
- faceless-explainer;
- talking-head-recut.

They become available to Codex from the next task/session.

## Knowledge accepted from the transcript

1. Transcribe first and preserve word/sentence timestamps.
2. Create a beat map tied to exact narration rather than adding random effects.
3. Use real, verified source screenshots when the narration cites news.
4. Use contextual B-roll with provenance; generated media is optional.
5. Keep narration as the primary audio track.
6. Use word-level captions with selective keyword emphasis.
7. Reframe talking heads for split screen instead of cropping faces blindly.
8. Apply controlled camera changes at sentence/idea boundaries.
9. Avoid reusing the same generated image sequence repeatedly.
10. Render a contact sheet and inspect the whole timeline.
11. Check overflow, safe zones, caption grouping and face/evidence occlusion.
12. Revise by exact timestamp and screenshot, then rerender.
13. Produce 9:16 TikTok/Shorts from the same factual master.

## Claims not accepted as architecture

- Kairogen is useful but not required. Provider selection remains cost,
  quality, license and budget based.
- Disabling all permissions is not an acceptable production practice.
- "English prompts are always cheaper/better" is not treated as a rule.
- A first render is not considered final merely because it looks dynamic.
- Generated visuals without provenance or commercial rights are not accepted.
- Long videos should be processed chapter by chapter, not trusted as one
  unreviewed monolithic generation.

## Quality gate

`core/departments/video/editorial_quality.py` enforces:

- timed narration-to-visual beats;
- maximum uninterrupted visual holds;
- minimum contextual B-roll coverage;
- source provenance;
- caption timing, safe zone and keyword emphasis;
- bounded asset reuse;
- narration/audio priority;
- contact-sheet, overflow, occlusion and preview evidence.

`core/tools/adapters/hyperframes_adapter.py` provides MOCK/REAL rendering. REAL
requires an audited `index.html` project composition and uses the local
HyperFrames CLI. It runs `lint` and `check --strict` before rendering. The
physical smoke composition passed both gates and produced a 1080x1920 MP4.

## Long-form to Shorts

1. Transcribe the long master with timestamps.
2. Divide it into factual chapters.
3. Edit each chapter with its own beat map and visual evidence.
4. Assemble and review the long master.
5. Score self-contained moments for hook, clarity and payoff.
6. Create 30-60 second Shorts from the original timestamps.
7. Reframe and redesign captions for 9:16; never merely center-crop 16:9.
8. Publish only after separate quality checks for each output.

`LongFormRepurposingValidator` enforces valid chapter boundaries, factual
source IDs, exact master timestamps, a 15-60 second duration and a standalone
hook/payoff arc for every short candidate.
