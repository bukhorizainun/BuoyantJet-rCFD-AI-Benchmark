"""Export scalar monitors (CFD / rCFD temperature, energy, balance) as CSV/NumPy.

Produces under ``data/processed/``:
- ``cfd_T_mean.csv``   columns: ``t_s,T_mean_K``
- ``rcfd_T_mean.csv``  columns: ``t_s,T_mean_K``
- ``cfd_energy.csv``   if ``CFD_start_energy.out`` is available
- ``rcfd_balance.csv`` if ``rCFD_balance.out`` is available
- A matching ``.npy`` for each CSV.

This is the lightweight monitor exporter. The 2D field exporter that decodes
node-values from Fluent is future work (see ``docs/future_ai_extension.md``).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from cfdio import parse_fluent_out, ensure_dir


# (src_name, stem, value_label, time_col, value_col, dt)
# rCFD_balance.out is comma-separated and the time column is a step index,
# so we scale it by the global dt = 0.2 s.
_TASKS = (
    ("CFD_temperature.out",   "cfd_T_mean",   "T_mean_K", 0, 1, None),
    ("rCFD_temperature.out",  "rcfd_T_mean",  "T_mean_K", 0, 1, None),
    ("CFD_start_energy.out",  "cfd_energy",   "energy",   0, 1, None),
    ("rCFD_balance.out",      "rcfd_balance", "balance",  0, 3, 0.2),
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    args = ap.parse_args()

    raw = args.data_root / "raw"
    out = ensure_dir(args.out)

    for src_name, stem, value_label, tcol, vcol, dt in _TASKS:
        src = raw / src_name
        if not src.exists():
            print(f"[skip] {src_name} not found")
            continue
        try:
            arr = parse_fluent_out(src, time_col=tcol, value_col=vcol, dt=dt)
        except ValueError as e:
            print(f"[skip] {src_name}: {e}")
            continue
        df = pd.DataFrame(arr, columns=["t_s", value_label])
        df.to_csv(out / f"{stem}.csv", index=False)
        np.save(out / f"{stem}.npy", arr.astype(np.float32))
        print(f"[ok ] {src_name} -> {stem}.csv / {stem}.npy   ({len(arr)} rows)")


if __name__ == "__main__":
    main()
