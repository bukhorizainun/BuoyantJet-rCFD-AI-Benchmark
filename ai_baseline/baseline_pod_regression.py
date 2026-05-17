"""POD + linear regression baseline.

Pipeline
--------
1. Load the snapshot tensor written by ``scripts/prepare_ai_dataset.py``.
2. Chronologically split into train / val / test (default 80 / 10 / 10).
3. Subtract the train-set mean field; truncated SVD (POD) on the residual
   to get spatial modes ``Phi`` (shape ``r x d``) and temporal coefficients
   ``a(t)`` (shape ``N x r``).
4. Fit a one-step linear regressor ``a(t+1) = A a(t) + c`` on the training
   coefficients via least squares.
5. **Reconstruction error** on test = project test fields onto train POD,
   reconstruct, measure residual. This bounds any surrogate by the
   compression quality.
6. **Prediction error** on test = autoregressive rollout from the last
   train coefficient, lifted back to the spatial domain.

Honesty note
------------
The input tensor produced by ``prepare_ai_dataset.py`` is **grayscale image
intensity in [0, 1]**, not Kelvin (Fluent JPGs use a rainbow colormap with
non-linear mapping). Errors are reported in normalized space and also
scaled by ``driving_span_K`` from ``configs/dataset_config.yaml`` to give
an order-of-magnitude Kelvin number. The K numbers here are **not** directly
comparable to the CFD-vs-rCFD MAE of 2.27 K, which was computed on the true
Kelvin ``T_CoG`` monitor.

This will be tightened once a direct node-value exporter is added (see
``docs/future_ai_extension.md``).
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


@dataclass
class PODRegressionModel:
    rank: int
    # Filled by `fit`:
    mean: np.ndarray | None = None              # (d,)
    modes: np.ndarray | None = None             # (r, d)  rows are basis vectors
    A: np.ndarray | None = None                 # (r, r)
    c: np.ndarray | None = None                 # (r,)
    singular_values: np.ndarray | None = None   # (min(N, d),)

    # --- POD compression ---

    def fit_pod(self, X: np.ndarray) -> "PODRegressionModel":
        """Fit POD on ``X`` of shape ``(N, d)``. Stores mean, modes, S."""
        if X.ndim != 2:
            raise ValueError(f"Expected (N, d), got {X.shape}")
        self.mean = X.mean(axis=0)
        Xc = X - self.mean
        # Thin SVD: U (N x k), S (k,), Vt (k x d), with k = min(N, d).
        _U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        self.singular_values = S
        r = min(self.rank, Vt.shape[0])
        self.modes = Vt[:r]
        return self

    def encode(self, X: np.ndarray) -> np.ndarray:
        """Project ``X`` of shape ``(N, d)`` onto POD modes, returning (N, r)."""
        return (X - self.mean) @ self.modes.T

    def decode(self, A_coeffs: np.ndarray) -> np.ndarray:
        """Lift coefficients ``(N, r)`` back to the spatial domain ``(N, d)``."""
        return A_coeffs @ self.modes + self.mean

    # --- Linear time-stepper ---

    def fit_stepper(self, coeffs: np.ndarray) -> "PODRegressionModel":
        """Fit ``a(t+1) = A a(t) + c`` on coefficient time-series ``(N, r)``."""
        if coeffs.ndim != 2:
            raise ValueError(f"Expected (N, r), got {coeffs.shape}")
        a_in = coeffs[:-1]
        a_out = coeffs[1:]
        # Augment with a constant column for the bias term.
        X_aug = np.hstack([a_in, np.ones((len(a_in), 1))])  # (N-1, r+1)
        # Solve (X_aug) @ W = a_out  with W of shape (r+1, r).
        W, *_ = np.linalg.lstsq(X_aug, a_out, rcond=None)
        self.A = W[:-1].T              # (r, r)
        self.c = W[-1]                 # (r,)
        return self

    def predict_coeffs(self, a0: np.ndarray, n_steps: int) -> np.ndarray:
        """Autoregressively roll out ``n_steps`` from ``a0`` of shape ``(r,)``.

        Returns an ``(n_steps, r)`` array of predicted coefficients
        ``a(1), a(2), ..., a(n_steps)`` (i.e. the result does *not* include
        the initial state ``a0``).
        """
        out = np.empty((n_steps, self.A.shape[0]), dtype=a0.dtype)
        a = a0.astype(a0.dtype, copy=True)
        for k in range(n_steps):
            a = self.A @ a + self.c
            out[k] = a
        return out


# --------------------------------------------------------------------------
# Run pipeline
# --------------------------------------------------------------------------


@dataclass
class RunResult:
    rank: int
    n_train: int
    n_val: int
    n_test: int
    recon_mae_norm: float
    recon_max_norm: float
    pred_mae_norm: float
    pred_max_norm: float
    driving_span_K: float
    train_seconds: float
    inference_seconds: float
    csv_path: Path
    per_step: pd.DataFrame = field(repr=False, default_factory=pd.DataFrame)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "n_train": self.n_train,
            "n_val": self.n_val,
            "n_test": self.n_test,
            "recon_mae_norm": self.recon_mae_norm,
            "recon_max_norm": self.recon_max_norm,
            "recon_mae_K_approx": self.recon_mae_norm * self.driving_span_K,
            "recon_max_K_approx": self.recon_max_norm * self.driving_span_K,
            "pred_mae_norm": self.pred_mae_norm,
            "pred_max_norm": self.pred_max_norm,
            "pred_mae_K_approx": self.pred_mae_norm * self.driving_span_K,
            "pred_max_K_approx": self.pred_max_norm * self.driving_span_K,
            "train_seconds": self.train_seconds,
            "inference_seconds": self.inference_seconds,
        }


def _load_cfg(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _split_indices(n: int, train: float, val: float) -> tuple[slice, slice, slice]:
    i_train = int(n * train)
    i_val = i_train + int(n * val)
    return slice(0, i_train), slice(i_train, i_val), slice(i_val, n)


def run(
    benchmark_cfg_path: str | Path = "configs/benchmark_config.yaml",
    dataset_cfg_path: str | Path = "configs/dataset_config.yaml",
    rank: int | None = None,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
) -> RunResult:
    """Full fit-and-evaluate pipeline. Returns a ``RunResult``."""
    bench_cfg = _load_cfg(Path(benchmark_cfg_path))
    data_cfg = _load_cfg(Path(dataset_cfg_path))

    if rank is None:
        rank = int(bench_cfg["models"]["pod_regression"]["rank"])
    if output_dir is None:
        output_dir = Path(bench_cfg["output"]["benchmark_dir"])
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if run_id is None:
        run_id = f"r{rank}_{int(time.time())}"

    tensor_path = Path(bench_cfg["data"]["cfd_tensor"])
    print(f"Loading {tensor_path} ...")
    X = np.load(tensor_path).astype(np.float32)
    if X.ndim != 3:
        raise ValueError(f"Expected (N, H, W) tensor, got {X.shape}")
    n, h, w = X.shape
    d = h * w
    X_flat = X.reshape(n, d)

    split = data_cfg.get("split", {"train": 0.8, "val": 0.1, "test": 0.1})
    s_train, s_val, s_test = _split_indices(n, split["train"], split["val"])
    X_train = X_flat[s_train]
    X_val = X_flat[s_val]
    X_test = X_flat[s_test]
    print(f"Tensor   : {X.shape}  (d = {d})")
    print(f"Splits   : train={X_train.shape[0]}  val={X_val.shape[0]}  test={X_test.shape[0]}")
    print(f"Rank     : {rank}")

    model = PODRegressionModel(rank=rank)

    t0 = time.perf_counter()
    model.fit_pod(X_train)
    coeffs_train = model.encode(X_train)
    model.fit_stepper(coeffs_train)
    train_seconds = time.perf_counter() - t0
    print(f"POD+stepper fit in {train_seconds:.3f} s")

    # Reconstruction-only error on the test set: project, reconstruct.
    Y_recon = model.decode(model.encode(X_test))
    recon_err = np.abs(Y_recon - X_test)

    # Autoregressive prediction error on test: start from last train coeff.
    a0 = coeffs_train[-1]
    t1 = time.perf_counter()
    coeffs_pred = model.predict_coeffs(a0, n_steps=X_test.shape[0])
    Y_pred = model.decode(coeffs_pred)
    inference_seconds = time.perf_counter() - t1
    pred_err = np.abs(Y_pred - X_test)

    span_K = float(data_cfg["temperature"]["driving_span_K"])
    result = RunResult(
        rank=rank,
        n_train=int(X_train.shape[0]),
        n_val=int(X_val.shape[0]),
        n_test=int(X_test.shape[0]),
        recon_mae_norm=float(recon_err.mean()),
        recon_max_norm=float(recon_err.max()),
        pred_mae_norm=float(pred_err.mean()),
        pred_max_norm=float(pred_err.max()),
        driving_span_K=span_K,
        train_seconds=train_seconds,
        inference_seconds=inference_seconds,
        csv_path=output_dir / f"pod_regression_{run_id}.csv",
    )

    # Per-step CSV — one row per test frame.
    recon_per_step = recon_err.reshape(X_test.shape[0], -1).mean(axis=1)
    pred_per_step = pred_err.reshape(X_test.shape[0], -1).mean(axis=1)
    df = pd.DataFrame({
        "test_frame_idx": np.arange(X_test.shape[0]),
        "recon_mae_norm": recon_per_step,
        "recon_mae_K_approx": recon_per_step * span_K,
        "pred_mae_norm": pred_per_step,
        "pred_mae_K_approx": pred_per_step * span_K,
    })
    df.to_csv(result.csv_path, index=False)
    result.per_step = df

    # Also write a JSON-ish summary alongside.
    summary_path = result.csv_path.with_suffix(".summary.yaml")
    summary_path.write_text(yaml.safe_dump(result.as_dict(), sort_keys=False),
                            encoding="utf-8")

    print()
    print("=== POD + linear regression — TEST window (held out) ===")
    print(f"  rank                  : {rank}")
    print(f"  reconstruction MAE    : {result.recon_mae_norm:.5f}  "
          f"(~ {result.recon_mae_norm*span_K:.3f} K approx)")
    print(f"  reconstruction max AE : {result.recon_max_norm:.5f}  "
          f"(~ {result.recon_max_norm*span_K:.3f} K approx)")
    print(f"  prediction    MAE    : {result.pred_mae_norm:.5f}  "
          f"(~ {result.pred_mae_norm*span_K:.3f} K approx)")
    print(f"  prediction    max AE : {result.pred_max_norm:.5f}  "
          f"(~ {result.pred_max_norm*span_K:.3f} K approx)")
    print(f"  fit time              : {train_seconds*1000:.1f} ms")
    print(f"  inference time        : {inference_seconds*1000:.1f} ms "
          f"({X_test.shape[0]} steps)")
    print(f"  CSV                   : {result.csv_path}")
    print(f"  Summary               : {summary_path}")

    return result


def main(*_args: Any, **_kwargs: Any) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rank", type=int, default=None,
                    help="POD truncation rank (default: from benchmark_config.yaml)")
    ap.add_argument("--run-id", type=str, default=None,
                    help="Run identifier appended to the output filename")
    ap.add_argument("--benchmark-config", type=Path,
                    default=Path("configs/benchmark_config.yaml"))
    ap.add_argument("--dataset-config", type=Path,
                    default=Path("configs/dataset_config.yaml"))
    args = ap.parse_args()
    run(
        benchmark_cfg_path=args.benchmark_config,
        dataset_cfg_path=args.dataset_config,
        rank=args.rank,
        run_id=args.run_id,
    )


if __name__ == "__main__":
    main()
