# `ai_baseline/` — Infrastructure only

> **Read this first.** Nothing in this folder is a validated model.

This package provides the **scaffolding** for future Scientific ML baselines
on the buoyant-jet dataset. Every module here is intentionally minimal — it
defines the interfaces, the data path, and the metric module that any future
surrogate has to plug into. None of the baselines below has been trained or
validated.

## Contents

| File                          | Status         | Purpose                                    |
|-------------------------------|----------------|--------------------------------------------|
| `dataset.py`                  | skeleton       | snapshot tensor loader                     |
| `preprocessing.py`            | skeleton       | normalization, train/val/test splitting    |
| `metrics.py`                  | implemented    | MAE / maxAE / relative MAE / energy drift  |
| `baseline_pod_regression.py`  | **implemented** | POD + linear regression                    |
| `baseline_pod_lstm.py`        | skeleton       | POD + small LSTM                           |
| `baseline_autoencoder.py`     | skeleton       | conv. autoencoder                          |
| `train_baseline.py`           | wired          | dispatch (POD live; others raise)          |
| `evaluate_baseline.py`        | wired          | run eval (POD live; others raise)          |
| `rank_sweep.py`               | implemented    | aggregate POD sweep summaries → CSV + plot |

First baseline results (POD + linear time-stepper, held-out 10 % test
window) live in `data/processed/benchmark/pod_regression_*.{csv,summary.yaml}`
and the rank-sweep plot at `assets/figures/fig_pod_rank_sweep.png`.
The repository README shows the headline numbers and the honesty caveats.

## Honesty contract

Any pull request that adds a model to this folder **must**:

1. Train on the actual `data/processed/cfd_T_field.npy` tensor.
2. Run `evaluate_baseline.py` on a strictly held-out time window.
3. Write the resulting CSV under `data/processed/benchmark/`.
4. Update the README results table **only after** all of the above.

Do not submit numbers cherry-picked from training loss, partial windows, or
toy data.
