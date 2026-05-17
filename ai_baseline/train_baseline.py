"""Dispatch entry-point for AI baselines — SKELETON.

Reads ``configs/benchmark_config.yaml`` and routes to the requested baseline
(``pod_regression`` / ``pod_lstm`` / ``autoencoder``). Each underlying
training function is a TODO.

Usage (future)::

    python ai_baseline/train_baseline.py --model pod_lstm
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from . import (
    baseline_autoencoder,
    baseline_pod_lstm,
    baseline_pod_regression,
)


_REGISTRY = {
    "pod_regression": baseline_pod_regression.main,
    "pod_lstm":       baseline_pod_lstm.main,
    "autoencoder":    baseline_autoencoder.main,
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, choices=sorted(_REGISTRY))
    ap.add_argument("--config", default="configs/benchmark_config.yaml",
                    type=Path)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    print(f"Loaded config: {args.config}")
    print(f"Dispatching model: {args.model}")
    # TODO: pass `cfg` into the chosen baseline's training entry-point.
    _REGISTRY[args.model](cfg)


if __name__ == "__main__":
    main()
