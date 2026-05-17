"""Build the tracked ``sample_data/demo_snapshots/`` set.

Copies a handful of representative CFD/rCFD frames at reduced resolution
and writes a tiny CSV snippet of the temperature monitor — small enough
to commit (target: < 1 MB total) so the repo is smoke-testable without
the full dataset.

Re-runnable: overwrites any previous demo set under ``sample_data/``.

Usage::

    python scripts/build_sample_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image

from cfdio import ensure_dir, parse_fluent_out


# Representative timesteps (in frame indices, dt ≈ 1 s per snapshot):
#   0   — initial cold tank
#   60  — early jet heating
#   180 — mid-stratification
#   315 — near jet shut-off
#   450 — early cooling
DEMO_INDICES = (0, 60, 180, 315, 450)
DEMO_WIDTH = 320  # pixels — keeps each JPG well under 60 KB


def _copy_resized(src: Path, dst: Path, width: int) -> int:
    with Image.open(src) as im:
        if im.width > width:
            h = int(im.height * width / im.width)
            im = im.resize((width, h), Image.BILINEAR)
        im.save(dst, "JPEG", quality=82, optimize=True)
    return dst.stat().st_size


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--sample-root", default="sample_data", type=Path)
    args = ap.parse_args()

    demo_dir = ensure_dir(args.sample_root / "demo_snapshots")
    total = 0

    print(f"Writing demo frames (resized to {DEMO_WIDTH}px wide) -> {demo_dir}")
    for i in DEMO_INDICES:
        for label, src_dir, pat in (
            ("CFD",  args.data_root / "cfd_snapshots",  f"CFD_T_path_{i:04d}.jpg"),
            ("rCFD", args.data_root / "rcfd_snapshots", f"rCFD_BJet_{i:04d}.jpg"),
        ):
            src = src_dir / pat
            if not src.exists():
                print(f"  [skip] {src}")
                continue
            dst = demo_dir / src.name
            size = _copy_resized(src, dst, DEMO_WIDTH)
            total += size
            print(f"  {label} idx {i:4d}  ->  {dst.name}  ({size//1024} KB)")

    cfd_out = args.data_root / "raw" / "CFD_temperature.out"
    rcfd_out = args.data_root / "raw" / "rCFD_temperature.out"
    if cfd_out.exists() and rcfd_out.exists():
        cfd = parse_fluent_out(cfd_out)
        rcfd = parse_fluent_out(rcfd_out)
        # First 50 rows from each — tiny CSV for smoke tests.
        pd.DataFrame(cfd[:50], columns=["t_s", "T_mean_K"]).to_csv(
            args.sample_root / "cfd_temperature_first50.csv", index=False)
        pd.DataFrame(rcfd[:50], columns=["t_s", "T_mean_K"]).to_csv(
            args.sample_root / "rcfd_temperature_first50.csv", index=False)
        total += (args.sample_root / "cfd_temperature_first50.csv").stat().st_size
        total += (args.sample_root / "rcfd_temperature_first50.csv").stat().st_size
        print(f"  CSV snippets (first 50 rows each)  ({2*50} rows total)")

    print(f"\nDemo set total: {total/1024:.1f} KB  (target < 1024 KB)")


if __name__ == "__main__":
    main()
