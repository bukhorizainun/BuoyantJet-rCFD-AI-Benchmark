"""POD + linear regression baseline — SKELETON.

Status: **not validated**. This module defines the interface only. The
training loop and evaluation must be implemented before any results from this
file appear in the benchmark.

Algorithm (planned):
1. Standardize the snapshot tensor along the time axis.
2. Compute a truncated SVD (POD) of ``(N, H*W)`` to get modes and temporal
   coefficients ``a(t)``.
3. Fit a linear regressor ``a(t+1) = A @ a(t) + b`` on the training window.
4. Roll out predictions on the held-out test window.
5. Lift back to the spatial domain and report metrics via
   :mod:`ai_baseline.metrics`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PODRegressionModel:
    rank: int
    # Filled by `fit`:
    modes: np.ndarray | None = None      # (rank, H*W)
    mean: np.ndarray | None = None       # (H*W,)
    A: np.ndarray | None = None          # (rank, rank) linear time-stepper
    b: np.ndarray | None = None          # (rank,)

    def fit(self, X: np.ndarray) -> "PODRegressionModel":
        """Fit POD modes and a one-step linear stepper on ``X``: ``(N, H*W)``."""
        # TODO: implement truncated SVD + least-squares for A, b.
        raise NotImplementedError("baseline_pod_regression.fit is a TODO")

    def predict(self, x0: np.ndarray, n_steps: int) -> np.ndarray:
        """Autoregressively roll out ``n_steps`` snapshots from ``x0`` (H*W)."""
        # TODO: lift x0 into mode space, iterate, lift back.
        raise NotImplementedError("baseline_pod_regression.predict is a TODO")


def main(*_args: Any, **_kwargs: Any) -> None:
    raise SystemExit(
        "baseline_pod_regression is a skeleton — implement fit/predict, "
        "wire it through train_baseline.py, and only then add it to the "
        "README results table."
    )


if __name__ == "__main__":
    main()
