"""Build a GIF (or MP4) animation from a folder of snapshot frames.

Examples
--------
    python scripts/make_animation.py --src data/cfd_snapshots  --out assets/animations/cfd.gif
    python scripts/make_animation.py --src data/rcfd_snapshots --out assets/animations/rcfd.gif --fps 25
"""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v2 as imageio

from cfdio import ensure_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--pattern", default="*.jpg")
    ap.add_argument("--stride", type=int, default=1,
                    help="Keep every Nth frame to reduce file size.")
    args = ap.parse_args()

    frames = sorted(args.src.glob(args.pattern))[::args.stride]
    if not frames:
        raise SystemExit(f"No frames matching {args.pattern} in {args.src}")

    ensure_dir(args.out.parent)
    print(f"Encoding {len(frames)} frames -> {args.out}")

    writer = imageio.get_writer(args.out, fps=args.fps)
    try:
        for f in frames:
            writer.append_data(imageio.imread(f))
    finally:
        writer.close()

    print(f"Done: {args.out}")


if __name__ == "__main__":
    main()
