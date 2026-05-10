# Higgsfield → Wan2GP image-to-video workflow

How Higgsfield is used to produce reference stills that feed Wan2GP's i2v pipeline. Higgsfield is **only** used for still-image generation; Wan2GP remains the video backend.

## Roles

- **Higgsfield (MCP)**: text (and optional reference) → still images. Stills saved under `assets/higgsfield_generations/`.
- **Wan2GP (`wgp.py --i2v`)**: still → video. Outputs saved under `outputs/wan2gp_videos/`.

## Default model

`marketing_studio_image` (Higgsfield) — one-click product/ad stills for social campaigns.

- Resolutions: `1k` / `2k` / `4k` (default `1k`).
- Aspect ratios: `auto`, `1:1`, `3:2`, `2:3`, `4:3`, `3:4`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`.
- Optional `medias[].role: image` for a brand reference.

Backup smoke-test model: `z_image` (fast, low-cost, text-only).

## Workspace

Private workspace: `71c1cbea-85fb-4d06-879d-c88a4cc0f966` (free plan, low credit budget — keep `count: 1` for tests).

## Prompt template (ad-style)

```
[subject] on/in [setting], [lighting cue], [camera/lens cue], commercial product photography,
[composition], [optional empty-space cue for ad copy]
```

## Procedure

1. `mcp__higgsfield__select_workspace` — one-time per session.
2. `mcp__higgsfield__balance` — confirm credits.
3. `mcp__higgsfield__generate_image` with `model: marketing_studio_image`, an aspect ratio, and `count: 1` for tests.
4. `mcp__higgsfield__job_status` — poll until terminal (image jobs are typically ~10-20s).
5. Download the result URL into `assets/higgsfield_generations/<campaign>/<slug>.png`.
6. Hand off to Wan2GP: launch `python wgp.py --i2v` (or `--i2v-14B` / `--i2v-1-3B`) and load the saved still as the i2v reference frame in the Gradio UI. Output lands in `outputs/wan2gp_videos/`.
7. Headless alternative: `python tools/run_i2v.py --image <path> --prompt "<motion>" --out outputs/wan2gp_videos` — wraps `shared.api` and writes `<image-stem>.<ext>` into the output dir (run with `--help` for all flags).

## Generation log

| Date | Job ID | Model | Aspect | Prompt summary | Saved to |
|------|--------|-------|--------|----------------|----------|
| 2026-05-10 | `bf03f52b-5606-4f7c-8d9d-0cb311199588` | `marketing_studio_image` | 1:1 / 1k (1024×1024) | matte-black ceramic coffee mug on sunlit wooden desk (smoke test) | `assets/higgsfield_generations/2026-05-10_smoke-test/coffee-mug-1k.png` |
