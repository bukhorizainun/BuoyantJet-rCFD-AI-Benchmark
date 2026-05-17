# Future AI Extension

This document is a **plan**, not a results sheet. Nothing in `ai_baseline/`
has been trained or validated as of this writing.

## 1. Why an AI surrogate at all

rCFD already delivers ~37× speed-up at <1 % mean relative error on this case.
An AI surrogate is worth pursuing only if it can plausibly:

- push speed-up another order of magnitude (e.g. real-time inference),
- generalize to perturbed boundary conditions (jet temperature, inlet flow,
  geometry), or
- produce a differentiable model for control / optimization loops.

If a candidate model cannot beat rCFD on at least one of those axes, it
should not be merged.

## 2. Candidate model families

| Family                  | Pros                                  | Cons                            |
|-------------------------|---------------------------------------|---------------------------------|
| POD + linear regression | Cheap, interpretable, fast baseline   | Limited expressivity            |
| POD + LSTM              | Captures temporal latent dynamics     | Sensitive to truncation rank    |
| Conv. autoencoder       | Nonlinear field compression           | No physics by default           |
| ConvLSTM                | Spatio-temporal predictor             | Memory heavy                    |
| Fourier Neural Operator | Mesh-flexible time-stepper            | Needs careful preprocessing     |
| Physics-informed NN     | Encodes conservation laws             | Hard to train, slow             |

## 3. Data plan

- **Training set** — first 80 % of the CFD time series.
- **Validation set** — next 10 %.
- **Held-out test set** — final 10 % (never used for tuning).
- **Spatial preprocessing** — temperature decoded from snapshot images via
  `ai_baseline/preprocessing.py`, normalized to `[0, 1]` using
  `T_min = 293 K`, `T_max = 333 K`.
- **Temporal preprocessing** — sliding windows of length `k` (configurable in
  `configs/benchmark_config.yaml`).

## 4. Metrics & honesty

A model can only be added to the README results table once it has been
evaluated by `ai_baseline/evaluate_baseline.py` on the held-out test set,
using the same metric definitions as the CFD/rCFD comparison.

Reporting should always include:

- MAE and max-AE in Kelvin
- Relative error vs. the 40 K driving temperature span
- Wall-clock cost of training **and** inference
- Speed-up vs. CFD **and** vs. rCFD

## 5. Out of scope (for now)

- Generative AI for case-design exploration.
- LLM-based PDE solving.
- Surrogates trained on data from a different geometry.

These belong to later thesis steps or follow-up work.
