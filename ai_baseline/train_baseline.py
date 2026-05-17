"""Dispatch entry-point for AI baselines.

Reads ``configs/benchmark_config.yaml`` plus ``configs/dataset_config.yaml``
and routes to the requested baseline's ``run()``.

Currently implemented:
- ``pod_regression`` → :func:`ai_baseline.baseline_pod_regression.run`

Still skeleton (raises ``NotImplementedError``):
- ``pod_lstm``
- ``autoencoder``

Usage::

    python -m ai_baseline.train_baseline --model pod_regression
    python -m ai_baseline.train_baseline --model pod_regression --rank 64
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from . import (
    baseline_autoencoder,
    baseline_pod_lstm,
    baseline_pod_regression,
)


def _dispatch_pod_regression(args: argparse.Namespace) -> Any:
    return baseline_pod_regression.run(
        benchmark_cfg_path=args.benchmark_config,
        dataset_cfg_path=args.dataset_config,
        rank=args.rank,
        run_id=args.run_id,
    )


def _dispatch_pod_lstm(args: argparse.Namespace) -> Any:
    return baseline_pod_lstm.main()  # raises NotImplementedError-equivalent


def _dispatch_autoencoder(args: argparse.Namespace) -> Any:
    return baseline_autoencoder.main()  # raises NotImplementedError-equivalent


_REGISTRY = {
    "pod_regression": _dispatch_pod_regression,
    "pod_lstm":       _dispatch_pod_lstm,
    "autoencoder":    _dispatch_autoencoder,
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, choices=sorted(_REGISTRY))
    ap.add_argument("--rank", type=int, default=None,
                    help="POD truncation rank (pod_regression / pod_lstm only)")
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--benchmark-config", type=Path,
                    default=Path("configs/benchmark_config.yaml"))
    ap.add_argument("--dataset-config", type=Path,
                    default=Path("configs/dataset_config.yaml"))
    args = ap.parse_args()
    _REGISTRY[args.model](args)


if __name__ == "__main__":
    main()
