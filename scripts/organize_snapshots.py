"""Copy Fluent CFD/rCFD outputs into the canonical ``data/`` layout.

Usage
-----
    python scripts/organize_snapshots.py --src ..\\bouyant_jet_replay\\post --dst data\\

Source layout (from the upstream tutorial)::

    post/
        CFD_reference/CFD_T_path_XXXX.jpg
        CFD_reference/CFD_temperature.out
        CFD_start/CFD_start_energy.out
        rCFD/rCFD_BJet_XXXX.jpg
        rCFD/rCFD_temperature.out
        rCFD/rCFD_balance.out

Destination layout::

    data/
        cfd_snapshots/CFD_T_path_XXXX.jpg
        rcfd_snapshots/rCFD_BJet_XXXX.jpg
        raw/<all .out files>

Only files; no Fluent ``.cas.h5`` / ``.dat.h5`` are copied. The script is
idempotent — re-running it overwrites existing destinations.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from cfdio import ensure_dir


CFD_GLOB = "CFD_T_path_*.jpg"
RCFD_GLOB = "rCFD_BJet_*.jpg"
RAW_GLOBS = ("*.out",)


def _copy_glob(src_dir: Path, dst_dir: Path, pattern: str) -> int:
    if not src_dir.exists():
        return 0
    ensure_dir(dst_dir)
    n = 0
    for f in sorted(src_dir.glob(pattern)):
        shutil.copy2(f, dst_dir / f.name)
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path,
                    help="Path to the upstream 'post' folder.")
    ap.add_argument("--dst", required=True, type=Path,
                    help="Path to this repo's data/ folder.")
    args = ap.parse_args()

    src: Path = args.src
    dst: Path = args.dst

    n_cfd = _copy_glob(src / "CFD_reference", dst / "cfd_snapshots", CFD_GLOB)
    n_rcfd = _copy_glob(src / "rCFD", dst / "rcfd_snapshots", RCFD_GLOB)

    raw_dst = ensure_dir(dst / "raw")
    n_raw = 0
    for sub in ("CFD_reference", "CFD_start", "rCFD"):
        for pat in RAW_GLOBS:
            n_raw += _copy_glob(src / sub, raw_dst, pat)

    print(f"CFD snapshots copied : {n_cfd}")
    print(f"rCFD snapshots copied: {n_rcfd}")
    print(f"raw monitor files    : {n_raw}")
    print(f"destination          : {dst.resolve()}")


if __name__ == "__main__":
    main()
