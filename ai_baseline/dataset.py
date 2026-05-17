"""Snapshot dataset loader.

Currently this is a thin NumPy-backed loader for the tensors produced by
``scripts/prepare_ai_dataset.py``. PyTorch / TensorFlow ``Dataset`` wrappers
will be added when those backends are enabled in ``requirements.txt``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np


Split = Literal["train", "val", "test"]


@dataclass(frozen=True)
class SnapshotTensor:
    array: np.ndarray  # (N, H, W) float32 in [0, 1]
    source: str        # "cfd" | "rcfd"
    path: Path


def load_snapshot_tensor(path: str | Path) -> SnapshotTensor:
    """Load a ``.npy`` snapshot stack written by ``prepare_ai_dataset.py``."""
    path = Path(path)
    arr = np.load(path)
    if arr.ndim != 3:
        raise ValueError(
            f"Expected (N, H, W) tensor at {path}, got shape {arr.shape}"
        )
    source = "cfd" if "cfd_T_field" in path.name else (
        "rcfd" if "rcfd_T_field" in path.name else "unknown"
    )
    return SnapshotTensor(array=arr.astype(np.float32), source=source, path=path)


def time_split(n: int, train: float = 0.8, val: float = 0.1
               ) -> dict[Split, slice]:
    """Return contiguous time-axis slices for train/val/test.

    Splits are strictly chronological so the test window is unseen — this
    matches how a surrogate would be deployed on a continuing transient.
    """
    if not 0 < train < 1 or not 0 <= val < 1 or train + val >= 1:
        raise ValueError("Invalid split fractions.")
    i_train = int(n * train)
    i_val = i_train + int(n * val)
    return {
        "train": slice(0, i_train),
        "val": slice(i_train, i_val),
        "test": slice(i_val, n),
    }


# TODO: PyTorch Dataset / DataLoader wrapper, sliding-window sampling for
# autoregressive models, and on-the-fly augmentation (flip, noise).
