# Benchmark Design

This benchmark compares three levels of simulation fidelity for the adiabatic
buoyant jet case.

## 1. Three-tier ladder

| Tier            | Method                                        | Cost          | Accuracy           | Step  |
|-----------------|-----------------------------------------------|---------------|--------------------|-------|
| **CFD ref.**    | Full transient ANSYS Fluent simulation        | High          | Ground truth       | ✅ 1 |
| **rCFD replay** | Recurrence-CFD reduced-order replay           | ≈ CFD / 37.6  | 2.27 K MAE         | ✅ 1 |
| **AI surrogate**| Data-driven model trained on CFD/rCFD data    | TBD           | TBD                | 🛠️ 2 |

## 2. Reference quantities

All comparisons are anchored to the CFD reference using:

- **Centre-of-gravity temperature** `T_CoG(t)` — primary scalar benchmark
  (column 2 of `*_temperature.out`).
- **Full 2D temperature field** `T(x, y, t)` — used for spatial errors and
  for AI training.
- **Energy balance** — sanity check that energy is (approximately) conserved.

## 3. Metric conventions

This benchmark intentionally reports **two MAE numbers** so the reader can
distinguish a documentation-grade metric from a physically aligned one.

### 3.1 MATLAB-style (canonical Step 1 metric)

This is the convention used by `analysis_complete.m` and reproduced by
`scripts/compare_cfd_rcfd.py`. It is the number that appears in the README
results table and in the Step 1 progress report.

Definition:

1. Read CFD and rCFD `*_temperature.out` files; column 2 is `T_CoG`.
2. Drop the duplicate `t=0` row that rCFD writes at startup.
3. Form a 500-point common grid
   `t_common = linspace(max(t_cfd[0], t_rcfd[0]), min(t_cfd[-1], t_rcfd[-1]), 500)`.
4. Interpolate both traces onto `t_common` (linear).
5. Per-point `abs_err = |T_cfd - T_rcfd|`, `rel_err = abs_err / T_cfd * 100`.

The CFD time axis is **not** re-based. Because the CFD monitor's first
column is the simulator's flow-time (starts at the end of the spin-up,
≈ 30 s) and rCFD's first column starts at 0 s, this comparison contains a
constant 30 s offset between the two physical states. The largest absolute
errors (≈ 6.9 K) are concentrated in the early window where the offset
matters most. Keeping this convention is what reproduces the validated
Step 1 numbers exactly:

| Metric                | Value     |
|-----------------------|-----------|
| MAE                   | 2.27 K    |
| Max abs. error        | 6.92 K    |
| Mean relative error   | 0.74 %    |
| Max  relative error   | 2.36 %    |

### 3.2 Physically aligned (sanity-check metric)

Reported as a secondary line by `scripts/compare_cfd_rcfd.py`. CFD time is
shifted by `t_cfd - t_cfd[0]` so its first sample coincides with rCFD `t=0`
(both representing "start of jet injection"). Same interpolation, same
`abs_err / T_cfd * 100`. With the offset removed the agreement is tighter:

| Metric                | Value     |
|-----------------------|-----------|
| MAE                   | 1.30 K    |
| Max abs. error        | 3.16 K    |
| Mean relative error   | 0.41 %    |
| Max  relative error   | 1.00 %    |

This is **not** a competing metric — it is a sanity check that the rCFD
replay reproduces CFD when compared at matched physical states.

### 3.3 Additional metrics defined in `ai_baseline/metrics.py`

For AI surrogates evaluated against the CFD reference:

- **MAE** and **Max AE** — same definitions as above.
- **Excess-temperature relative error** —
  `|T_hat - T_ref| / max(|T_ref - T_amb|, 1e-9)`, with `T_amb = 293 K`.
  This is meaningful for buoyancy-driven cases because it relates the error
  to the thermal driving span rather than to the absolute Kelvin scale.
- **Energy drift** — fractional drift of the integrated thermal energy
  `rho_cp * V * (T - T_amb)` from `t=0` to `t=end`.
- **Wall-clock speed-up** — `t_cfd / t_method` at matched physical time.

AI surrogates should report MAE and excess-T relative error side by side
with the canonical MATLAB-style number so reviewers can compare to both
conventions.

## 4. Honesty rules for adding a new method

A new method (e.g. POD-LSTM, FNO, ...) is allowed into the benchmark **only**
when it produces, on a held-out time interval:

1. `T_hat` arrays of matched shape with the CFD reference,
2. a measured wall-clock cost from `evaluate_baseline.py`,
3. all metrics above, written into a CSV under `data/processed/benchmark/`.

Until a method has produced those numbers on the **real** dataset, it must
not be claimed as part of the benchmark. Placeholder results, hand-picked
visualizations, or numbers from other test cases must not be merged.

## 5. Comparison protocol

1. Parse CFD and rCFD `*_temperature.out` files (column 2 = `T_CoG`).
2. Apply the MATLAB-style interpolation onto `t_common` of 500 points.
3. Compute MAE, max AE, mean / max relative error.
4. Also report the physically aligned MAE as a sanity check.
5. Plot overlay, error evolution, and snapshot grids at matched indices.
6. Persist metrics into `data/processed/cfd_vs_rcfd_errors.csv`.
7. Repeat 2–6 for every AI surrogate, replacing rCFD with the surrogate.

`scripts/compare_cfd_rcfd.py` implements steps 1–6 for the rCFD baseline.
`ai_baseline/evaluate_baseline.py` will reuse the same metric definitions
for AI methods once implemented.
