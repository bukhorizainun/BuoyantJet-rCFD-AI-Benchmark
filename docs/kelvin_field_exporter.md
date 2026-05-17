# Kelvin Field Exporter (staged)

## Why

All AI baselines so far operate on the **grayscale JPG snapshots** Fluent
renders directly (`data/cfd_snapshots/CFD_T_path_XXXX.jpg`). That tensor
lives in `[0, 1]` image-intensity space, and the rainbow colormap Fluent
uses is non-linear — so the MAE numbers reported by
`ai_baseline/baseline_pod_regression.py` cannot be compared directly to
the validated CFD-vs-rCFD MAE of `2.27 K` computed on the **true Kelvin**
`T_mean` monitor.

This exporter closes that gap by writing the cell-centred temperature
field as CSV at every (sub-sampled) timestep, in true Kelvin.

## Pipeline summary

```
┌──────────────────────┐    UDF       ┌──────────────────────┐    Python
│  ANSYS Fluent run    │ ──────────▶ │  field_TXXXX.csv     │ ──────────▶
│  (CFD or rCFD case)  │             │  (per-step, Kelvin)  │
└──────────────────────┘             └──────────────────────┘

  ┌────────────────────────────────┐     baselines
─▶│ data/processed/cfd_T_field_     │ ────────────────▶  POD / LSTM / AE
  │ kelvin.npy   (N, H, W)  float32 │                    on TRUE Kelvin
  └────────────────────────────────┘
```

## Components in this repository

| Component                              | Status     | Notes                                         |
|----------------------------------------|------------|-----------------------------------------------|
| `udf/CFD_export_field.c`               | scaffold   | `DEFINE_EXECUTE_AT_END` macro, ready to compile |
| `udf/README.md`                        | scaffold   | Compile + hook instructions                   |
| `scripts/import_temperature_field.py`  | scaffold   | `--mode raw` and `--mode grid` (scipy)        |
| Re-evaluated AI baselines               | TODO       | Re-run after Kelvin data is in `data/processed/` |

> ⚠️ Nothing here has been compiled or executed against a real Fluent
> case as of this writing. The UDF mirrors the validated pattern of
> `CFD_write_temperature` in the upstream tutorial; the Python script
> mirrors the existing `prepare_ai_dataset.py` shape so AI baselines
> remain backward-compatible.

## Step-by-step (planned)

### 1. Copy the UDF into the Fluent project

The simplest path is to compile a **separate** libudf so the existing
`libudf_cfd` is untouched:

```powershell
# In your bouyant_jet_replay folder:
mkdir libudf_export
copy "..\BuoyantJet-rCFD-AI-Benchmark\udf\CFD_export_field.c" libudf_export\
```

Alternatively, append the macro source to `user_src/CFD_user.c` and
recompile the existing libudf.

### 2. Create the output directory

```powershell
mkdir bouyant_jet_replay\post\CFD_reference\field
```

If the directory does not exist when the macro fires for the first time,
Fluent will log a warning and the file open will fail silently.

### 3. Hook the macro

In the Fluent GUI:

`Define → User-Defined → Function Hooks → Execute At End`

Add `CFD_export_field`. This is the same hook that drives the validated
`CFD_write_temperature` scalar monitor.

### 4. Run the CFD reference

Run the case as before:

```scheme
(cfd_run)
```

With `EXPORT_STRIDE = 5` and `dt = 0.2 s`, you get **one CSV per second**
of physical time — about **630 files** at ~4 MB each ≈ **2.7 GB total**.
Make sure the target volume has room before kicking off the run.

If 2.7 GB is too much:

- Raise `EXPORT_STRIDE` (e.g. `10` → 1.4 GB, `25` → 540 MB).
- Or call the macro `CFD_export_field_slice` (variant TODO) that only
  writes a single z-plane.

### 5. Convert to NumPy

**Raw per-cell tensor** (mesh-faithful, no spatial interpolation):

```powershell
python scripts\import_temperature_field.py `
  --src "bouyant_jet_replay\post\CFD_reference\field" `
  --out "data\processed\cfd_T_field_kelvin.npy" `
  --mode raw
```

Outputs:

- `data/processed/cfd_T_field_kelvin.npy` — `(N_steps, n_cells)` float32, Kelvin
- `data/processed/cfd_T_field_kelvin_coords.npy` — `(n_cells, 3)` float32
- `data/processed/cfd_T_field_kelvin_times.npy` — `(N_steps,)` float64
- `data/processed/cfd_T_field_kelvin.manifest.yaml`

**Regular-grid tensor** (drop-in for the existing AI baselines):

```powershell
python scripts\import_temperature_field.py `
  --src "bouyant_jet_replay\post\CFD_reference\field" `
  --out "data\processed\cfd_T_field_kelvin.npy" `
  --mode grid --H 128 --W 128 --z-slice 0.0
```

Outputs `(N_steps, H, W)` float32 in true Kelvin, same shape as the
existing grayscale tensor — so `ai_baseline/baseline_pod_regression.py`
runs unchanged once the config points at it.

### 6. Re-evaluate AI baselines

Update `configs/benchmark_config.yaml`:

```yaml
data:
  cfd_tensor:  data/processed/cfd_T_field_kelvin.npy
```

Then re-run the existing baselines and rank-sweep:

```powershell
python -m ai_baseline.train_baseline --model pod_regression --rank 64
python -m ai_baseline.rank_sweep
```

The reported MAE will now be in **true Kelvin** and directly comparable
to the validated CFD-vs-rCFD MAE of 2.27 K. The "≈ K" qualifier in the
current README results table can be dropped.

## Open questions / future improvements

- **Per-node files vs. serial append.** The current UDF serialises all
  compute nodes through one file. For the 85 k-cell case with 4 nodes
  this is fine, but for larger meshes it should be rewritten so each
  node writes its own file and a Python merge step reassembles the
  global ordering.
- **Direct binary export.** ASCII CSV is convenient for debugging but
  ~5x slower and ~4x larger than binary. A `DEFINE_EXECUTE_AT_END`
  writing `.npy`-compatible little-endian floats would be a
  worthwhile follow-up.
- **rCFD field export.** The same macro can be added to the rCFD case
  (`rCFD_user_run.h`), giving the second ground truth needed for
  surrogate ≈ rCFD comparisons in honest Kelvin.

## Honesty note

Once the Kelvin baseline numbers exist, the README results table will
need an honest update — the "≈ K" qualifier on the POD numbers should
be replaced by the real measured value, and any difference between
the grayscale-trained and Kelvin-trained baselines should be reported
side by side rather than silently overwritten.
