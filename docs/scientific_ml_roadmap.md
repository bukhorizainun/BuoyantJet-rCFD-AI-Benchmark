# Scientific ML Roadmap

A long-horizon view of where this repository is heading. Each item is
deliberately scoped so it can be finished, written up, and validated against
the CFD/rCFD baselines already in this repo.

## Phase A — Reduced-order baselines (next)

1. **POD on `cfd_T_field.npy`**
   - SVD of the snapshot tensor, energy spectrum, optimal rank.
   - Reconstruction MAE vs. truncation rank.
2. **POD + linear regression of temporal coefficients**
   - Predict `a(t+Δt)` from `a(t)`.
3. **POD + small LSTM**
   - Replace the linear time-stepper with a learnable one.

## Phase B — Nonlinear field compression

4. **Convolutional autoencoder** of the 2D temperature snapshot.
   - Compression-quality / latent-size sweep.
5. **Latent-space time stepper** (linear / GRU / Transformer).

## Phase C — Operator learning

6. **Fourier Neural Operator** as a one-step temperature operator.
7. **Conditional FNO** with jet temperature as an input parameter, enabling
   parameter sweeps the CFD can no longer afford.

## Phase D — Physics-aware learning

8. Add **energy-conservation losses** and check the `rCFD_balance.out`
   diagnostic on AI predictions.
9. Investigate **physics-informed neural operators** as a hybrid path.

## Phase E — Transfer & aerospace cases

10. Transfer learning to a propellant-tank thermal stratification case.
11. Surrogate-in-the-loop control toy problem (set-point regulation of
    stratification height).

## Cross-cutting concerns

- **Reproducibility** — every result must come with a run manifest in
  `data/metadata/` and a deterministic seed.
- **Honesty** — no fabricated benchmarks. A method enters the README table
  only after `evaluate_baseline.py` writes its CSV.
- **Documentation** — every phase yields one notebook in `notebooks/` and an
  appendix-grade section in `docs/`.
