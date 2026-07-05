# Creative Review Department

Creative Review decides whether an image, offer card, screenshot, or thumbnail reference is ready for use.
It exists to avoid wasting time rebuilding assets that are already good enough.

## Decision Actions

- `use_as_is`: asset is clear, safe, and ready for Affiliate Deals or publishing.
- `minor_cleanup`: asset is useful but needs light image cleanup.
- `rebuild_creative`: asset has the right idea but needs a new layout or generated creative.
- `find_alternative_image`: product is hard to see or source image is too weak.
- `human_review`: asset has rights, watermark, earnings-claim, or third-party-reference risk.

## Scoring Inputs

- visual quality
- product visibility
- resolution
- text clutter
- watermark/source risk
- brand safety
- face emotion and proof element for thumbnails
- explicit risk flags such as `third_party_thumbnail_reference` or `earnings_claim`

## Operating Rule

Good product images skip unnecessary editing. Risky or copied references become style guidance only.
