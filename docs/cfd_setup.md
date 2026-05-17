# CFD Reference Setup

This document describes the high-fidelity CFD baseline used as ground truth in
the benchmark. It is inherited from the upstream `bouyant_jet_replay` tutorial
(JKU Linz, PFM) and adapted for Windows 11 + ANSYS Fluent.

## 1. Physical case

Adiabatic buoyant jet in a closed water tank.

| Property                | Value      |
|-------------------------|------------|
| Working fluid           | water      |
| Wall condition          | adiabatic  |
| Initial tank temperature| 293 K      |
| Jet inlet temperature   | 333 K      |
| Turbulence model        | inherited from upstream Fluent setup |
| Time-step size          | 0.2 s      |
| CFD physical time       | ≈ 658 s    |

## 2. Mesh

| Quantity | Value   |
|----------|---------|
| Cells    | 85 625  |
| Nodes    | 94 216  |

The mesh file is shipped with the Fluent case archives
(`BouyantJet_*.cas.h5`) in the upstream tutorial. These large binaries are
**not** committed to this repository (see `.gitignore`).

## 3. Solver bootstrap

The reference workflow has two stages:

### 3.1 Spin-up to pseudo-steady state

- Scheme file: `CFD_start.scm`
- In Fluent console run `(cfd_start)` (or the numbered sequence
  `(cfd_1)` ... `(cfd_7)`).
- Outputs:
  - `./post/CFD_start/CFD_start_energy.out`
  - `./post/CFD_start/fluent_*.trn`
  - `./ansys_fluent/BouyantJet_START.cas.h5`
  - `./ansys_fluent/BouyantJet_START.dat.h5`

### 3.2 Reference transient

- Scheme file: `CFD_run.scm`
- In Fluent console run `(cfd_run)` (or the numbered sequence).
- Outputs:
  - `./post/CFD_reference/CFD_temperature.out`
  - `./post/CFD_reference/CFD_T_path_XXXX.jpg`  (630 frames, indices 0000–0629)
  - `./post/CFD_reference/fluent_*.trn`
  - `./ansys_fluent/BouyantJet_END_CFD_RUN.cas.h5`
  - `./ansys_fluent/BouyantJet_END_CFD_RUN.dat.h5`

## 4. UDF compilation

The CFD user code is compiled by Fluent into `./libudf_cfd/`. On Windows 11,
ensure the matching Visual Studio Build Tools are installed and that the
Fluent shell inherits the Visual Studio environment (see
`docs/windows11_adaptation.md`).

## 5. Outputs consumed by this repository

The Python tooling in `scripts/` consumes the following CFD artefacts:

| Artefact                                       | Consumer                              |
|------------------------------------------------|---------------------------------------|
| `CFD_temperature.out`                          | `plot_temperature_series.py`, `compare_cfd_rcfd.py` |
| `CFD_T_path_XXXX.jpg` (630 frames)             | `make_animation.py`, `prepare_ai_dataset.py`        |
| `CFD_start_energy.out`                         | `plot_temperature_series.py`          |

## 6. Reproducibility note

The repository does **not** attempt to commit Fluent case/data files. To
re-run the CFD reference from scratch, follow the upstream tutorial in
`bouyant_jet_replay/README.md`, then run
`python scripts/organize_snapshots.py` to copy the produced files into
`data/cfd_snapshots/` and `data/raw/`.
