"""Plot mean-temperature monitors from CFD and rCFD runs.

Reads ``data/raw/CFD_temperature.out`` and ``data/raw/rCFD_temperature.out``
and writes a 2-panel figure with the temperature traces over time.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from cfdio import parse_fluent_out, ensure_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--out", default="assets/figures", type=Path)
    args = ap.parse_args()

    cfd_path = args.data_root / "raw" / "CFD_temperature.out"
    rcfd_path = args.data_root / "raw" / "rCFD_temperature.out"

    cfd = parse_fluent_out(cfd_path)
    rcfd = parse_fluent_out(rcfd_path)

    out_dir = ensure_dir(args.out)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)

    axes[0].plot(cfd[:, 0], cfd[:, 1], color="#1f77b4", lw=1.4)
    axes[0].set_title("CFD reference — tank mean temperature")
    axes[0].set_xlabel("time [s]")
    axes[0].set_ylabel("T_mean [K]")
    axes[0].grid(alpha=0.3)

    axes[1].plot(rcfd[:, 0], rcfd[:, 1], color="#d62728", lw=1.4)
    axes[1].set_title("rCFD replay — tank mean temperature")
    axes[1].set_xlabel("time [s]")
    axes[1].set_ylabel("T_mean [K]")
    axes[1].grid(alpha=0.3)

    out = out_dir / "fig_temperature_series.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
