# `udf/` — Fluent UDF scaffolds

Status: **staged, not yet validated**. Code in this folder has not been
compiled by the Fluent UDF compiler against the buoyant-jet case as of
this writing. Treat it as a starting point for the Kelvin field exporter
described in `docs/future_ai_extension.md` — section "Direct Kelvin
exporter".

## Contents

| File                   | Purpose                                                   | Status |
|------------------------|-----------------------------------------------------------|--------|
| `CFD_export_field.c`   | `DEFINE_EXECUTE_AT_END` macro writing per-timestep CSV of `(t, x, y, z, T)` | scaffold |

## What this unlocks

The current AI baselines (`ai_baseline/baseline_pod_regression.py`) operate
on the **grayscale JPG snapshots** Fluent renders directly. That tensor is
in `[0, 1]` image-intensity space, not Kelvin, and the JPG colormap is
non-linear — so AI MAE numbers cannot be directly compared to the CFD-vs-rCFD
MAE of 2.27 K computed on the true `T_mean` Kelvin monitor.

A per-cell `T_K` CSV exporter resolves that mismatch:

1. The UDF writes one CSV per timestep with the real Kelvin temperature
   at every cell centroid.
2. A new Python script `scripts/import_temperature_field.py` (see below)
   converts the CSVs into a `(N, n_cells)` float32 tensor in true Kelvin
   — or, when interpolated onto a regular grid, into `(N, H, W)` Kelvin.
3. POD / LSTM / autoencoder baselines can then be retrained against true
   Kelvin data, and their MAE becomes directly comparable to rCFD.

## How to use (planned workflow)

1. **Copy** `CFD_export_field.c` into
   `bouyant_jet_replay/user_src/` and append its contents to
   `CFD_user.c`, OR compile it into its own libudf alongside the existing
   ones. Either way, Fluent must see the macro at UDF-load time.
2. **Create the output directory** before starting Fluent:
   ```
   mkdir bouyant_jet_replay/post/CFD_reference/field
   ```
3. **Hook the macro** into the CFD reference run. In Fluent:
   - Define → User-Defined → Function Hooks → Execute At End →
     add `CFD_export_field`.
   - This is the same hook used by the existing `CFD_write_temperature`.
4. **Run** the CFD reference simulation as before (`(cfd_run)` scheme
   command). With `EXPORT_STRIDE = 5` and `dt = 0.2 s`, you get one CSV
   per second of physical time — ~630 files matching the existing JPG
   snapshot cadence.
5. **Parse** with `scripts/import_temperature_field.py` (still to be
   written — see `docs/future_ai_extension.md`).

## Important caveats

- **Mesh size impact.** The case has 85 625 cells. Each CSV is roughly
  `85625 * 50 bytes ≈ 4.3 MB`. Over 630 timesteps that's ~2.7 GB. Plan
  storage accordingly; consider raising `EXPORT_STRIDE` if disk is
  tight.
- **Serial append is naïve.** The current write strategy synchronises
  all nodes through one file. Fine for ~4 partitions and ~100 k cells,
  but quadratic-feeling for large meshes. Future improvement: per-node
  files + a Python merge step.
- **Compile-time `#define`s.** Adjust `EXPORT_STRIDE` / `EXPORT_DIR` /
  `EXPORT_PREFIX` in `CFD_export_field.c` before compiling.
- **No CSV header validation in the Python parser yet.** Once
  `import_temperature_field.py` exists, it should verify the header
  line and fail loudly if the schema drifts.

## License

GPL-3.0, matching the rest of this repository and the upstream rCFD
tutorial.
