"""Evaluate an AI baseline against the CFD reference — SKELETON.

Plan
----
1. Load the trained checkpoint named by ``--model`` and ``--run-id``.
2. Predict the held-out test window.
3. Compute MAE / max-AE / relative MAE / max relative error via
   :mod:`ai_baseline.metrics`.
4. Persist a CSV under ``data/processed/benchmark/<model>_<run_id>.csv``.

Until a baseline is actually trained, this module just refuses to invent
numbers.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", default="data/processed/benchmark", type=Path)
    args = ap.parse_args()

    raise SystemExit(
        f"evaluate_baseline is a skeleton. To evaluate '{args.model}/"
        f"{args.run_id}', first implement training in ai_baseline/baseline_*.py "
        "and save a checkpoint. Faking numbers in this script would violate "
        "the honesty contract in ai_baseline/README.md."
    )


if __name__ == "__main__":
    main()
