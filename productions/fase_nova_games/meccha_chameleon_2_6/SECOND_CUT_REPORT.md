# Second cut report

Generated on 2026-07-12 after owner review of the first cut.

## What changed

- Replaced the screenshot slideshow with eight short excerpts from the official
  Steam gameplay trailer.
- Added three micro-cuts in the opening hook, five short scene wipes, varied
  camera movement, evidence cards, animated facts and a cleaner CTA.
- Removed public technical identifiers such as Steam news IDs.
- Rewrote the narration for pauses, emphasis and more conversational rhythm.
- Replaced the temporary Windows voice with local Kokoro `pm_alex` narration.
- Mixed low-volume official trailer ambience beneath the narration.

## Result

- Duration: 40.90 seconds.
- Resolution: 1080x1920 at 30 fps.
- Video: H.264; audio: AAC at 48 kHz.
- Six editorial scenes, eight gameplay clips and five transitions.
- HyperFrames lint: 0 errors, 0 warnings.
- HyperFrames strict runtime, layout, motion and contrast check: passed.
- Contrast: 43/43 text checks passed WCAG AA.
- Media QA: no black frame interval and no unexpected audio silence.
- Freeze QA found one 1.8-second hold inherited from the official trailer; it
  is a short evidence hold rather than a slideshow structure.

Local review file:

`output/fase_nova_games/meccha-chameleon-2-6-second-cut-normalized.mp4`

Contact sheet:

`output/fase_nova_games/meccha-chameleon-2-6-second-cut-contact-sheet.jpg`

## Voice strategy

Kokoro now provides the zero-cost local baseline for Brazilian Portuguese
narration. It runs in an isolated environment through `KokoroTTSAdapter`, so
employees can request speech through `Capability.SPEECH_GENERATION` without
loading the model in the main runtime. ElevenLabs remains an optional premium
provider after its billing issue is resolved.

## Publication state

`HOLD_FOR_OWNER_REVIEW`
