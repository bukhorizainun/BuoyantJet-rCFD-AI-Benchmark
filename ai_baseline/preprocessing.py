"""Preprocessing utilities for AI baselines.

For Step 1 the snapshots are grayscale intensities in ``[0, 1]`` — see the
note in ``scripts/prepare_ai_dataset.py``. Once a true physical-temperature
exporter is wired in, the helpers below will be extended to handle Kelvin
values directly.
"""

from __future__ import annotations

import numpy as np


def standardize(x: np.ndarray, mean: float | None = None,
                std: float | None = None) -> tuple[np.ndarray, float, float]:
    """Standardize ``x`` to zero mean / unit std along the time axis.

    Returns the standardized array along with the (mean, std) used, so the
    same transform can be applied to val/test sets.
    """
    if mean is None:
        mean = float(x.mean())
    if std is None:
        std = float(x.std()) or 1.0
    return (x - mean) / std, mean, std


def flatten_fields(x: np.ndarray) -> np.ndarray:
    """Flatten ``(N, H, W) -> (N, H*W)`` for POD / regression models."""
    if x.ndim != 3:
        raise ValueError(f"Expected 3D tensor, got {x.shape}")
    n, h, w = x.shape
    return x.reshape(n, h * w)


def sliding_windows(x: np.ndarray, window: int, horizon: int = 1
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Produce ``(X, Y)`` sliding windows for autoregressive models.

    ``X`` has shape ``(M, window, ...)`` and ``Y`` has shape
    ``(M, horizon, ...)``. ``M = N - window - horizon + 1``.
    """
    n = x.shape[0]
    m = n - window - horizon + 1
    if m <= 0:
        raise ValueError(f"Too short: n={n}, window={window}, horizon={horizon}")
    X = np.stack([x[i : i + window] for i in range(m)])
    Y = np.stack([x[i + window : i + window + horizon] for i in range(m)])
    return X, Y


# TODO: physical-temperature decoder once the colormap calibration or the
# direct node-value export is available.
