# `sample_data/` — Tiny demo set

A **72 KB**, git-tracked snapshot of the buoyant-jet dataset so that the
repo can be smoke-tested immediately after cloning, without the full
CFD/rCFD output (which is gigabytes and lives outside git).

## Contents

```
sample_data/
├── demo_snapshots/
│   ├── CFD_T_path_0000.jpg          (cold tank, t = 0 s)
│   ├── CFD_T_path_0060.jpg          (early heating, t ≈ 60 s)
│   ├── CFD_T_path_0180.jpg          (mid-stratification, t ≈ 180 s)
│   ├── CFD_T_path_0315.jpg          (near jet shut-off, t ≈ 315 s)
│   ├── CFD_T_path_0450.jpg          (cooling, t ≈ 450 s)
│   ├── rCFD_BJet_0000.jpg
│   ├── rCFD_BJet_0060.jpg
│   ├── rCFD_BJet_0180.jpg
│   ├── rCFD_BJet_0315.jpg
│   └── rCFD_BJet_0450.jpg
├── cfd_temperature_first50.csv      (first 50 rows of CFD T_mean monitor)
└── rcfd_temperature_first50.csv     (first 50 rows of rCFD T_mean monitor)
```

All frames are **320 px wide** (downsampled from the full ~1200 px Fluent
export) so the entire demo set fits comfortably in one commit.

## How it was built

```powershell
python scripts\build_sample_data.py
```

Re-running the script overwrites the demo set in place. The script uses
the same `cfdio.parse_fluent_out` parser as the main pipeline.

## How to use

For a hello-world look at the dataset shape, point any notebook or script
at `sample_data/` instead of `data/`. The demo CSV columns match the full
dataset (`t_s, T_mean_K`).

## What it is **not**

- **Not** a substitute for the real CFD/rCFD output. The 5-frame slice is
  far too coarse for POD or any surrogate training. Reproduce the full
  validated Step 1 numbers (MAE 2.27 K) only from the full dataset under
  `data/`. See `data/README.md` for placement instructions.
