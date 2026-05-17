# rCFD Replay Workflow

The recurrence-CFD (rCFD) workflow records a database of cell-to-cell shifts
from a short CFD reference and then replays the thermal transient by
re-applying that database.

This document describes the pipeline that produced the validated Step 1 rCFD
dataset used in this benchmark.

## 1. Stage 1 — Database preparation

- Scheme: `rCFD_prep.scm`
- Fluent console: `(rcfd_prep)` or `(rcfd_p1)` ... `(rcfd_p9)`.
- Outputs (placed under `./data/`):

| Directory     | Content                                                  |
|---------------|----------------------------------------------------------|
| `c2c/`        | cell-to-cell shift files (one per Fluent compute node)   |
| `rec/`        | recurrence info — `jump`, `jump_diff`, `rec_matrix`      |
| `tmp/`        | norm fields                                              |
| `topo/`       | topology files                                           |
| `vof/`        | volume-of-fluid auxiliaries                              |
| `user/`       | user-defined fields                                      |
| `local_diff/` | local diffusion auxiliaries                              |
| —             | `rcfd_db.meta.toml` describes the resulting database     |

## 2. Stage 2 — Replay run

- Scheme: `rCFD_run.scm`
- Fluent console: `(rcfd_run)` or `(rcfd_r1)` ... `(rcfd_r8)`.
- Set `(define post_on 0)` to disable graphical output for fast replay.
- Outputs (placed under `./post/rCFD/`):

| Artefact                            | Description                              |
|-------------------------------------|------------------------------------------|
| `rCFD_temperature.out`              | mean-temperature monitor                 |
| `rCFD_balance.out`                  | energy-balance diagnostic                |
| `rCFD_BJet_XXXX.jpg` (600 frames)   | rCFD replay snapshots, indices 0000–0599 |
| `rCFD_run.trn`                      | transcript                               |

The replay uses **600 episodes**, time-step **0.2 s**.

## 3. Compiled UDFs

- `libudf_rcfd_prep/` — UDFs compiled during stage 1.
- `libudf_rcfd_run/`  — UDFs compiled during stage 2.

These build artefacts are git-ignored.

## 4. Validated Step 1 accuracy

Against the CFD reference for the tank mean temperature:

| Metric                | Value     |
|-----------------------|-----------|
| Mean absolute error   | 2.27 K    |
| Max absolute error    | 6.92 K    |
| Mean relative error   | 0.74 %    |
| Max relative error    | 2.36 %    |

## 5. Performance

| Metric                          | Value   |
|---------------------------------|---------|
| rCFD replay speed-up vs. CFD    | 37.6×   |

These numbers are reproduced by
`python scripts/compare_cfd_rcfd.py` once the temperature monitors from both
runs are placed under `data/raw/`.

## 6. Consumers

| Artefact                                   | Consumer                              |
|--------------------------------------------|---------------------------------------|
| `rCFD_temperature.out`                     | `plot_temperature_series.py`, `compare_cfd_rcfd.py` |
| `rCFD_BJet_XXXX.jpg` (600 frames)          | `make_animation.py`, `prepare_ai_dataset.py`        |
| `rCFD_balance.out`                         | energy-conservation diagnostic        |
