"""Aggregate POD-regression rank-sweep summaries into a CSV and a plot.

Reads every ``data/processed/benchmark/pod_regression_*.summary.yaml`` and
emits:

- ``data/processed/benchmark/pod_regression_rank_sweep.csv`` — tidy table
- ``assets/figures/fig_pod_rank_sweep.png`` — reconstruction vs. prediction
  MAE as a function of POD truncation rank, in normalized intensity units
  AND in approximate Kelvin.

Usage::

    python -m ai_baseline.rank_sweep
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--benchmark-dir", type=Path,
                    default=Path("data/processed/benchmark"))
    ap.add_argument("--figure-dir", type=Path,
                    default=Path("assets/figures"))
    args = ap.parse_args()

    rows: list[dict] = []
    for f in sorted(args.benchmark_dir.glob("pod_regression_*.summary.yaml")):
        s = yaml.safe_load(f.read_text(encoding="utf-8"))
        s["source_file"] = f.name
        rows.append(s)
    if not rows:
        raise SystemExit(f"No summaries found under {args.benchmark_dir}")

    df = pd.DataFrame(rows).sort_values("rank").reset_index(drop=True)
    # Deduplicate by rank, keeping the latest summary for each rank.
    df = df.drop_duplicates(subset="rank", keep="last").reset_index(drop=True)
    out_csv = args.benchmark_dir / "pod_regression_rank_sweep.csv"
    df.to_csv(out_csv, index=False)
    print(f"Aggregated {len(df)} ranks -> {out_csv}")
    print(df[["rank", "recon_mae_norm", "pred_mae_norm",
              "recon_mae_K_approx", "pred_mae_K_approx",
              "train_seconds", "inference_seconds"]].to_string(index=False))

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    axes[0].plot(df["rank"], df["recon_mae_norm"], "o-",
                 label="reconstruction", color="#1f77b4", lw=1.8)
    axes[0].plot(df["rank"], df["pred_mae_norm"], "s--",
                 label="prediction (autoregressive)", color="#d62728", lw=1.8)
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("POD truncation rank")
    axes[0].set_ylabel("MAE (normalized intensity)")
    axes[0].set_title("Held-out test MAE vs POD rank")
    axes[0].grid(alpha=0.3, which="both")
    axes[0].legend(loc="best")

    axes[1].plot(df["rank"], df["recon_mae_K_approx"], "o-",
                 label="reconstruction", color="#1f77b4", lw=1.8)
    axes[1].plot(df["rank"], df["pred_mae_K_approx"], "s--",
                 label="prediction (autoregressive)", color="#d62728", lw=1.8)
    axes[1].set_xscale("log", base=2)
    axes[1].set_xlabel("POD truncation rank")
    axes[1].set_ylabel("MAE (approx. K, intensity × 40 K span)")
    axes[1].set_title("Same metric, scaled to approximate Kelvin")
    axes[1].grid(alpha=0.3, which="both")
    axes[1].legend(loc="best")

    fig_path = args.figure_dir / "fig_pod_rank_sweep.png"
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)
    print(f"Figure -> {fig_path}")


if __name__ == "__main__":
    main()
