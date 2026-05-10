# assets/

Static media used by the Higgsfield → Wan2GP image-to-video workflow.

- `reference_ads/` — curated brand/ad reference stills you supply by hand (tracked in git).
- `higgsfield_generations/` — Higgsfield-generated stills saved locally (gitignored).

Pipeline:

1. Brief is captured, optionally pointing at a still in `reference_ads/`.
2. Higgsfield MCP `generate_image` produces a still that lands in `higgsfield_generations/`.
3. That still is fed to `python wgp.py --i2v` as the first-frame reference; the resulting video is written to `outputs/wan2gp_videos/`.

See `tools/higgsfield_to_wan2gp.md` for the full procedure, default model, prompt template, and run log.
