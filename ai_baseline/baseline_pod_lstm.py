"""POD + small LSTM baseline — SKELETON.

Status: **not validated**. Provides the interface only.

Algorithm (planned):
1. Same POD compression as in ``baseline_pod_regression``.
2. Train a small LSTM on the temporal coefficients ``a(t)`` to predict
   ``a(t+1)`` autoregressively.
3. Lift back to the spatial domain and evaluate via
   :mod:`ai_baseline.metrics`.

The deep-learning backend (PyTorch or TensorFlow) is intentionally NOT
imported at module load time — uncomment the relevant dependency in
``requirements.txt`` first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PODLSTMConfig:
    rank: int = 32
    hidden_size: int = 64
    num_layers: int = 1
    window: int = 8
    horizon: int = 1
    lr: float = 1e-3
    epochs: int = 50
    batch_size: int = 32
    seed: int = 0


def build_model(cfg: PODLSTMConfig) -> Any:
    # TODO: instantiate torch.nn.LSTM with cfg.
    raise NotImplementedError("baseline_pod_lstm.build_model is a TODO")


def train(cfg: PODLSTMConfig, train_coeffs, val_coeffs) -> Any:
    # TODO: training loop with early stopping; save best checkpoint under runs/.
    raise NotImplementedError("baseline_pod_lstm.train is a TODO")


def main(*_args: Any, **_kwargs: Any) -> None:
    raise SystemExit(
        "baseline_pod_lstm is a skeleton — implement build_model/train, "
        "evaluate on the held-out window via evaluate_baseline.py, and "
        "only then add numbers to the README."
    )


if __name__ == "__main__":
    main()
