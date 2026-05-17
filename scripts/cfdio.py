"""Shared I/O helpers for parsing Fluent monitor outputs.

Fluent ``.out`` files typically have a few header lines beginning with ``(``
or ``"``, then whitespace- or comma-separated columns. For the CFD/rCFD
monitors in this project the layout is::

    flow_time_s   value   mass_flow_or_other

so by default we read column 0 as time and column 1 as the value.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np


_SPLIT = re.compile(r"[,\s]+")


def parse_fluent_out(
    path: Path | str,
    time_col: int = 0,
    value_col: int = 1,
    dt: float | None = None,
    t_offset: float | None = None,
) -> np.ndarray:
    """Parse a Fluent monitor file into a ``(N, 2)`` array of ``[t, value]``.

    Parameters
    ----------
    path : Path | str
        Path to the ``.out`` file.
    time_col, value_col : int
        Column indices for time and value (default 0, 1).
    dt : float | None
        If provided, the time column is multiplied by ``dt`` — useful for
        files whose first column is a step index, not seconds.
    t_offset : float | None
        If provided, subtract this from time. Useful to shift CFD time so
        ``t=0`` coincides with the start of the jet injection.
    """
    path = Path(path)
    rows: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("(") or line.startswith('"'):
                continue
            parts = [p for p in _SPLIT.split(line) if p]
            if len(parts) <= max(time_col, value_col):
                continue
            try:
                t = float(parts[time_col])
                v = float(parts[value_col])
            except ValueError:
                continue
            rows.append((t, v))
    if not rows:
        raise ValueError(f"No numeric rows parsed from {path}")
    arr = np.asarray(rows, dtype=np.float64)
    if dt is not None:
        arr[:, 0] *= dt
    if t_offset is not None:
        arr[:, 0] -= t_offset
    return arr


def list_snapshots(folder: Path | str, pattern: str) -> list[Path]:
    """Sorted list of snapshot files matching ``pattern`` in ``folder``."""
    folder = Path(folder)
    return sorted(folder.glob(pattern))


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
