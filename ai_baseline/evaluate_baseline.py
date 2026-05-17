"""Evaluate an AI baseline against the CFD reference.

Currently this thin wrapper re-runs the chosen baseline's full pipeline
(fit + held-out evaluation) and writes the result CSV. For POD-regression
that is cheap; for future DL models it will load a saved checkpoint
instead of re-training.

Output
------
``data/processed/benchmark/<model>_<run_id>.csv`` plus a matching
``.summary.yaml``.

Usage::

    python -m ai_baseline.evaluate_baseline --model pod_regression
    python -m ai_baseline.evaluate_baseline --model pod_regression --rank 64
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import baseline_pod_regression


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    choices=["pod_regression"])  # only one trained model for now
    ap.add_argument("--rank", type=int, default=None)
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--benchmark-config", type=Path,
                    default=Path("configs/benchmark_config.yaml"))
    ap.add_argument("--dataset-config", type=Path,
                    default=Path("configs/dataset_config.yaml"))
    args = ap.parse_args()

    if args.model == "pod_regression":
        baseline_pod_regression.run(
            benchmark_cfg_path=args.benchmark_config,
            dataset_cfg_path=args.dataset_config,
            rank=args.rank,
            run_id=args.run_id,
        )
        return

    raise SystemExit(
        f"evaluate_baseline does not yet support '{args.model}'. "
        "Implement the baseline's run() first, then add a branch here."
    )


if __name__ == "__main__":
    main()
