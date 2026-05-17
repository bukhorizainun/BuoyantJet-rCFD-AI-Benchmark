"""Build a side-by-side CFD vs. rCFD comparison GIF.

For each rCFD frame at index ``i`` the script picks the CFD frame at index
``i + cfd_offset`` (default 30, matching the CFD spin-up frames not present
in rCFD), stacks the two horizontally with a small caption, and writes the
result as a single GIF.

Examples
--------
    python scripts/make_comparison_animation.py \
        --data-root data \
        --out assets/animations/cfd_vs_rcfd.gif \
        --stride 10 --fps 12 --target-width 480
"""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from cfdio import ensure_dir, list_snapshots


def _resize(img: Image.Image, target_w: int) -> Image.Image:
    if target_w is None or img.width == target_w:
        return img
    ratio = target_w / img.width
    return img.resize((target_w, int(img.height * ratio)), Image.BILINEAR)


def _annotate(img: Image.Image, text: str) -> Image.Image:
    img = img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", max(12, img.width // 28))
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, img.width, 28], fill=(0, 0, 0))
    draw.text((6, 4), text, fill=(255, 255, 255), font=font)
    return img


def _pair(cfd: Image.Image, rcfd: Image.Image, t_s: float,
          target_w: int) -> np.ndarray:
    cfd = _annotate(_resize(cfd, target_w),  f"CFD   t = {t_s:6.1f} s")
    rcfd = _annotate(_resize(rcfd, target_w), f"rCFD  t = {t_s:6.1f} s")
    h = max(cfd.height, rcfd.height)
    canvas = Image.new("RGB", (cfd.width + rcfd.width + 4, h), (32, 32, 32))
    canvas.paste(cfd, (0, 0))
    canvas.paste(rcfd, (cfd.width + 4, 0))
    return np.asarray(canvas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--cfd-offset", type=int, default=30,
                    help="Skip the first N CFD frames so CFD frame N matches "
                         "rCFD frame 0 (the spin-up tail).")
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--dt-s", type=float, default=1.0,
                    help="Physical time per rCFD frame (s).")
    ap.add_argument("--target-width", type=int, default=480,
                    help="Resize each panel to this width before stacking.")
    args = ap.parse_args()

    cfd_frames = list_snapshots(args.data_root / "cfd_snapshots",
                                "CFD_T_path_*.jpg")
    rcfd_frames = list_snapshots(args.data_root / "rcfd_snapshots",
                                 "rCFD_BJet_*.jpg")
    if not cfd_frames or not rcfd_frames:
        raise SystemExit("Missing CFD or rCFD snapshots — see data/README.md.")

    n_pairs = min(len(cfd_frames) - args.cfd_offset, len(rcfd_frames))
    indices = range(0, n_pairs, args.stride)
    print(f"Encoding {len(list(indices))} pairs -> {args.out}")

    ensure_dir(args.out.parent)
    writer = imageio.get_writer(args.out, fps=args.fps)
    try:
        for j in range(0, n_pairs, args.stride):
            cfd = Image.open(cfd_frames[j + args.cfd_offset]).convert("RGB")
            rcfd = Image.open(rcfd_frames[j]).convert("RGB")
            writer.append_data(_pair(cfd, rcfd, j * args.dt_s, args.target_width))
    finally:
        writer.close()

    size_mb = args.out.stat().st_size / 1e6
    print(f"Done: {args.out}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
