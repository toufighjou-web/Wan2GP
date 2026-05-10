#!/usr/bin/env python3
"""Headless image-to-video runner that hands a still (e.g. a Higgsfield
generation) to Wan2GP via shared.api and saves the resulting clip.

Example:
    python tools/run_i2v.py \
        --image assets/higgsfield_generations/2026-05-10_smoke-test/coffee-mug-1k.png \
        --prompt "slow camera push-in, gentle steam rising, soft window light" \
        --out outputs/wan2gp_videos

The still is fed to the Wan i2v model as the start frame (image_start).
Output goes to --out (default: outputs/wan2gp_videos/) and is renamed to
<image-stem>.<ext>. If that target already exists, the script asks before
overwriting (skip the prompt with --overwrite).
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MODEL = "i2v_2_2"
DEFAULT_RESOLUTION = "832x480"
DEFAULT_STEPS = 30
DEFAULT_VIDEO_LENGTH = 81
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "wan2gp_videos"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Headless Wan2GP image-to-video runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example:\n"
            "  python tools/run_i2v.py \\\n"
            "      --image assets/higgsfield_generations/2026-05-10_smoke-test/coffee-mug-1k.png \\\n"
            '      --prompt "slow camera push-in, gentle steam rising, soft window light" \\\n'
            "      --out outputs/wan2gp_videos\n"
        ),
    )
    p.add_argument("--image", required=True, type=Path,
                   help="Path to the start-frame still (PNG/JPG).")
    p.add_argument("--prompt", required=True,
                   help="Motion description; the still already defines the look.")
    p.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR.relative_to(REPO_ROOT)}).")
    p.add_argument("--model-type", default=DEFAULT_MODEL,
                   help=f"Wan2GP model_type (filename stem in defaults/). Default: {DEFAULT_MODEL}.")
    p.add_argument("--resolution", default=DEFAULT_RESOLUTION,
                   help=f"Output WxH (default: {DEFAULT_RESOLUTION}).")
    p.add_argument("--steps", type=int, default=DEFAULT_STEPS,
                   help=f"num_inference_steps (default: {DEFAULT_STEPS}).")
    p.add_argument("--video-length", type=int, default=DEFAULT_VIDEO_LENGTH,
                   help=f"Frame count (default: {DEFAULT_VIDEO_LENGTH}).")
    p.add_argument("--out-name",
                   help="Final filename stem under --out. Defaults to the image stem.")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite an existing target file without prompting.")
    p.add_argument("--cli-args", default="",
                   help='Wan2GP startup flags forwarded to shared.api.init(cli_args=[...]). '
                        'Pass as a single shell-quoted string, e.g. '
                        '--cli-args "--attention sdpa --profile 4".')
    return p.parse_args()


def confirm(msg: str) -> bool:
    try:
        return input(f"{msg} [y/N]: ").strip().lower() in {"y", "yes"}
    except EOFError:
        return False


def main() -> int:
    args = parse_args()

    image_path = args.image.resolve()
    if not image_path.is_file():
        print(f"error: image not found: {image_path}", file=sys.stderr)
        return 2

    out_dir: Path = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    target_stem = args.out_name or image_path.stem
    # Pre-flight check uses .mp4 (Wan's standard container); the post-generation
    # rename uses the actual produced extension.
    reserved = out_dir / f"{target_stem}.mp4"
    if reserved.exists() and not args.overwrite:
        if not confirm(f"{reserved} already exists. Overwrite?"):
            print("aborted: target exists; rerun with --overwrite or --out-name NAME.")
            return 1

    settings = {
        "model_type": args.model_type,
        "prompt": args.prompt,
        "image_start": str(image_path),
        "resolution": args.resolution,
        "num_inference_steps": args.steps,
        "video_length": args.video_length,
    }

    cli_args = shlex.split(args.cli_args) if args.cli_args else []

    print(f"[run_i2v] image:    {image_path}")
    print(f"[run_i2v] out_dir:  {out_dir}")
    print(f"[run_i2v] settings: {settings}")
    if cli_args:
        print(f"[run_i2v] cli_args: {cli_args}")

    from shared.api import init

    session = init(root=REPO_ROOT, output_dir=out_dir, cli_args=cli_args)
    job = session.submit_task(settings)

    for event in job.events.iter(timeout=0.5):
        if event.kind == "progress":
            pr = event.data
            print(f"[run_i2v] {pr.phase} {pr.progress}% "
                  f"step={pr.current_step}/{pr.total_steps}")
        elif event.kind == "stream":
            line = event.data
            text = line.text if line.text.endswith("\n") else line.text + "\n"
            sys.stdout.write(f"[{line.stream}] {text}")
        elif event.kind == "error":
            err = event.data
            print(f"[run_i2v] error [{err.stage}] {err.message}", file=sys.stderr)

    result = job.result()
    if not result.success or not result.generated_files:
        print("[run_i2v] generation failed:", file=sys.stderr)
        for err in result.errors:
            print(f"  - [{err.stage}] {err.message}", file=sys.stderr)
        return 1

    produced = Path(result.generated_files[0])
    final = out_dir / f"{target_stem}{produced.suffix}"
    if final.exists() and final.resolve() != produced.resolve() and not args.overwrite:
        if not confirm(f"{final} already exists. Overwrite?"):
            print(f"[run_i2v] kept generated file at: {produced}")
            return 0

    if produced.resolve() != final.resolve():
        shutil.move(str(produced), str(final))
    print(f"[run_i2v] saved: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
