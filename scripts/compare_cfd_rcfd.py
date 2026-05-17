"""Quantitative CFD vs. rCFD comparison.

Replicates the metric definition used by ``analysis_complete.m`` in the
upstream MATLAB post-processing (see ``docs/benchmark_design.md``):

1. Load column 2 of ``*_temperature.out`` — this is the mass-weighted /
   centre-of-gravity temperature ``T_CoG`` reported by Fluent.
2. Deduplicate rCFD time-zero rows (rCFD writes ``t=0`` twice at startup).
3. Interpolate both curves linearly onto a 500-point common time grid
   ``t_common = linspace(max(t_cfd[0], t_rcfd[0]), min(t_cfd[-1], t_rcfd[-1]), 500)``.
4. ``abs_err = |T_cfd - T_rcfd|`` (in Kelvin).
5. ``rel_err = abs_err / T_cfd * 100`` (in percent, denominator in Kelvin).

This matches the validated Step 1 numbers (≈ 2.27 K MAE, 6.92 K max, 0.74 %
mean rel., 2.36 % max rel.).

The script also prints a "re-based" MAE in which the CFD time axis is
shifted so its first sample lines up with rCFD ``t=0``. This is the
physically aligned comparison — useful as a sanity check, but the official
metric is the MATLAB-style one above.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfdio import parse_fluent_out, ensure_dir


def _dedupe_by_time(t: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Keep the first occurrence of each unique time. Equivalent to MATLAB
    ``[~, ia] = unique(t, 'first'); t = t(ia); v = v(ia);``."""
    _, ia = np.unique(t, return_index=True)
    ia.sort()
    return t[ia], v[ia]


def _compare(
    t_cfd: np.ndarray, T_cfd: np.ndarray,
    t_rcfd: np.ndarray, T_rcfd: np.ndarray,
    n_common: int = 500,
) -> dict:
    """Return MATLAB-style comparison metrics + the interpolated curves."""
    t0 = max(t_cfd[0], t_rcfd[0])
    t1 = min(t_cfd[-1], t_rcfd[-1])
    t_common = np.linspace(t0, t1, n_common)
    T_cfd_i = np.interp(t_common, t_cfd, T_cfd)
    T_rcfd_i = np.interp(t_common, t_rcfd, T_rcfd)
    abs_err = np.abs(T_cfd_i - T_rcfd_i)
    rel_err_pct = abs_err / T_cfd_i * 100.0
    return {
        "t_common": t_common,
        "T_cfd_interp": T_cfd_i,
        "T_rcfd_interp": T_rcfd_i,
        "abs_err": abs_err,
        "rel_err_pct": rel_err_pct,
        "mae": float(abs_err.mean()),
        "max_ae": float(abs_err.max()),
        "rel_mae_pct": float(rel_err_pct.mean()),
        "rel_max_pct": float(rel_err_pct.max()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data", type=Path)
    ap.add_argument("--out", default="assets/figures", type=Path)
    args = ap.parse_args()

    cfd = parse_fluent_out(args.data_root / "raw" / "CFD_temperature.out")
    rcfd = parse_fluent_out(args.data_root / "raw" / "rCFD_temperature.out")

    t_cfd, T_cfd = cfd[:, 0], cfd[:, 1]
    t_rcfd, T_rcfd = _dedupe_by_time(rcfd[:, 0], rcfd[:, 1])

    # MATLAB-style: no time re-basing.
    matlab = _compare(t_cfd, T_cfd, t_rcfd, T_rcfd)

    # Physically aligned: re-base CFD so its first sample = 0 s (== rCFD t=0).
    rebased = _compare(t_cfd - t_cfd[0], T_cfd, t_rcfd, T_rcfd)

    print("=== CFD vs. rCFD on T_CoG (MATLAB-style, matches Step 1 validated numbers) ===")
    print(f"  N common samples : {len(matlab['t_common'])}")
    print(f"  MAE              : {matlab['mae']:8.4f} K")
    print(f"  Max abs. error   : {matlab['max_ae']:8.4f} K")
    print(f"  Mean rel. error  : {matlab['rel_mae_pct']:8.4f} %")
    print(f"  Max  rel. error  : {matlab['rel_max_pct']:8.4f} %")
    print()
    print("=== Same comparison after re-basing CFD time to t=0 (sanity check) ===")
    print(f"  MAE              : {rebased['mae']:8.4f} K")
    print(f"  Max abs. error   : {rebased['max_ae']:8.4f} K")
    print(f"  Mean rel. error  : {rebased['rel_mae_pct']:8.4f} %")
    print(f"  Max  rel. error  : {rebased['rel_max_pct']:8.4f} %")

    out_dir = ensure_dir(args.out)
    processed = ensure_dir(args.data_root / "processed")

    df = pd.DataFrame({
        "t_s":        matlab["t_common"],
        "T_cfd_K":    matlab["T_cfd_interp"],
        "T_rcfd_K":   matlab["T_rcfd_interp"],
        "abs_err_K":  matlab["abs_err"],
        "rel_err_pct": matlab["rel_err_pct"],
    })
    csv_path = processed / "cfd_vs_rcfd_errors.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  CSV               : {csv_path}")

    fig, axes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True,
                             constrained_layout=True)
    axes[0].plot(matlab["t_common"], matlab["T_cfd_interp"],
                 label="CFD reference", color="#1f77b4", lw=1.6)
    axes[0].plot(matlab["t_common"], matlab["T_rcfd_interp"],
                 label="rCFD replay", color="#d62728", lw=1.3,
                 linestyle="--")
    axes[0].set_ylabel(r"$T_\mathrm{CoG}$ [K]")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="best")
    axes[0].set_title(
        f"CFD vs rCFD (MATLAB-style) — "
        f"MAE = {matlab['mae']:.2f} K  ({matlab['rel_mae_pct']:.2f} % rel)"
    )

    axes[1].plot(matlab["t_common"], matlab["abs_err"], color="#444", lw=1.3)
    axes[1].set_xlabel("flow time [s]")
    axes[1].set_ylabel(r"$|T_\mathrm{rCFD} - T_\mathrm{CFD}|$ [K]")
    axes[1].grid(alpha=0.3)

    fig_path = out_dir / "fig_cfd_vs_rcfd.png"
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)
    print(f"  Figure            : {fig_path}")


if __name__ == "__main__":
    main()
