"""Sanity-check the local dataset.

Verifies that:
- ``data/cfd_snapshots/`` and ``data/rcfd_snapshots/`` exist and contain
  the expected number of frames,
- frame names match the canonical pattern,
- indices are contiguous,
- key monitor files exist under ``data/raw/``.

Exits with a non-zero status if any check fails.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CFD_RE = re.compile(r"CFD_T_path_(\d{4})\.jpg$")
RCFD_RE = re.compile(r"rCFD_BJet_(\d{4})\.jpg$")

EXPECTED_CFD = 630
EXPECTED_RCFD = 600

REQUIRED_RAW = (
    "CFD_temperature.out",
    "rCFD_temperature.out",
)
RECOMMENDED_RAW = (
    "CFD_start_energy.out",
    "rCFD_balance.out",
)


def _check_indices(folder: Path, regex: re.Pattern, expected: int, label: str) -> list[str]:
    msgs: list[str] = []
    if not folder.exists():
        msgs.append(f"[FAIL] {label}: folder missing: {folder}")
        return msgs
    files = sorted(folder.iterdir())
    matched = [(int(m.group(1)), f.name) for f in files if (m := regex.search(f.name))]
    if not matched:
        msgs.append(f"[FAIL] {label}: no frames matching pattern in {folder}")
        return msgs
    indices = sorted(i for i, _ in matched)
    msgs.append(
        f"[ OK ] {label}: {len(indices)} frames "
        f"(index {indices[0]:04d}..{indices[-1]:04d})"
    )
    if len(indices) != expected:
        msgs.append(
            f"[WARN] {label}: expected {expected} frames, found {len(indices)}"
        )
    gaps = [b for a, b in zip(indices, indices[1:]) if b - a != 1]
    if gaps:
        msgs.append(f"[WARN] {label}: {len(gaps)} index gaps, first at {gaps[0]:04d}")
    return msgs


def _check_files(folder: Path, names: tuple[str, ...], label: str) -> list[str]:
    msgs: list[str] = []
    for n in names:
        p = folder / n
        if p.exists():
            msgs.append(f"[ OK ] {label}: {n} ({p.stat().st_size} bytes)")
        else:
            msgs.append(f"[FAIL] {label}: {n} missing in {folder}")
    return msgs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    args = ap.parse_args()
    root: Path = args.data_root

    print(f"Checking dataset under: {root.resolve()}")
    msgs: list[str] = []
    msgs += _check_indices(root / "cfd_snapshots", CFD_RE, EXPECTED_CFD, "CFD snapshots")
    msgs += _check_indices(root / "rcfd_snapshots", RCFD_RE, EXPECTED_RCFD, "rCFD snapshots")
    msgs += _check_files(root / "raw", REQUIRED_RAW, "required monitors")
    msgs += _check_files(root / "raw", RECOMMENDED_RAW, "recommended monitors")

    for m in msgs:
        print(m)

    failed = any(m.startswith("[FAIL]") for m in msgs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
