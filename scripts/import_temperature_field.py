"""Import per-timestep Kelvin field CSVs produced by ``udf/CFD_export_field.c``.

Expects one CSV per timestep with columns ``t_s, x_m, y_m, z_m, T_K`` and
filenames ``field_TXXXX.csv``. Two output modes are supported:

1. **Raw per-cell tensor** (``--mode raw``) — preserves the original
   unstructured cell ordering. Writes ``(N_steps, n_cells)`` float32
   plus a ``(n_cells, 3)`` coordinate file. Honest but requires keeping
   the mesh handy for any visualization.

2. **Interpolated regular grid** (``--mode grid``) — slices the field at
   a chosen ``z`` (default 0), then interpolates the 2D scatter
   ``(x, y) -> T`` onto a regular ``H x W`` grid using SciPy. Writes
   ``(N_steps, H, W)`` float32 in true Kelvin. Drops the dependency on
   the mesh and is what the existing POD / LSTM / autoencoder baselines
   expect (they already accept ``(N, H, W)`` tensors via
   ``scripts/prepare_ai_dataset.py``).

This script is the Python counterpart to the staged UDF in ``udf/``.
**It has not yet been exercised on real exporter output** because the
UDF has not been compiled or run as of this writing. Treat the parser as
scaffolding and validate end-to-end against a small test export first.

Honesty contract
----------------
Any POD / LSTM / autoencoder result that lands in
``data/processed/benchmark/`` after this script comes online must say
explicitly whether it was trained on grayscale or true-Kelvin data.
Don't blur the two.

Usage
-----
::

    # Raw per-cell export (mesh-faithful):
    python scripts/import_temperature_field.py \
        --src bouyant_jet_replay/post/CFD_reference/field \
        --out data/processed/cfd_T_field_kelvin.npy \
        --mode raw

    # Regular-grid export at z=0, 128x128 (drop-in for existing baselines):
    python scripts/import_temperature_field.py \
        --src bouyant_jet_replay/post/CFD_reference/field \
        --out data/processed/cfd_T_field_kelvin.npy \
        --mode grid --H 128 --W 128 --z-slice 0.0
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from cfdio import ensure_dir


_NAME_RE = re.compile(r"field_T(\d{4})\.csv$")


def _list_field_csvs(src: Path) -> list[Path]:
    files = []
    for f in src.glob("field_T*.csv"):
        m = _NAME_RE.search(f.name)
        if m:
            files.append((int(m.group(1)), f))
    files.sort(key=lambda x: x[0])
    return [f for _, f in files]


def _read_csv(path: Path) -> tuple[float, np.ndarray, np.ndarray]:
    """Return ``(t_s, coords_xyz, T_K)`` for one timestep file."""
    df = pd.read_csv(path)
    expected = {"t_s", "x_m", "y_m", "z_m", "T_K"}
    if not expected.issubset(df.columns):
        missing = expected - set(df.columns)
        raise ValueError(f"{path}: missing columns {missing}")
    t_s = float(df["t_s"].iloc[0])
    coords = df[["x_m", "y_m", "z_m"]].to_numpy(dtype=np.float64)
    T = df["T_K"].to_numpy(dtype=np.float32)
    return t_s, coords, T


def _interp_to_grid(coords_xy: np.ndarray, T: np.ndarray,
                    H: int, W: int) -> np.ndarray:
    """Interpolate scattered ``(x, y) -> T`` onto an ``H x W`` regular grid.

    Uses scipy linear interpolation if available, falling back to nearest
    neighbours through ``numpy`` for the corners.
    """
    try:
        from scipy.interpolate import griddata
    except ImportError as e:
        raise SystemExit(
            "scipy is required for --mode grid. Install with "
            "`pip install scipy` or run with --mode raw."
        ) from e

    x = coords_xy[:, 0]
    y = coords_xy[:, 1]
    x_lin = np.linspace(x.min(), x.max(), W)
    y_lin = np.linspace(y.min(), y.max(), H)
    grid_x, grid_y = np.meshgrid(x_lin, y_lin)

    T_grid = griddata((x, y), T, (grid_x, grid_y), method="linear")
    # Fill any NaNs (outside convex hull) with nearest-neighbour.
    if np.isnan(T_grid).any():
        T_nn = griddata((x, y), T, (grid_x, grid_y), method="nearest")
        mask = np.isnan(T_grid)
        T_grid[mask] = T_nn[mask]
    return T_grid.astype(np.float32)


def run_raw(src: Path, out: Path) -> None:
    files = _list_field_csvs(src)
    if not files:
        raise SystemExit(f"No field_T*.csv files under {src}")
    print(f"Found {len(files)} CSVs in {src}")

    t0, coords, T0 = _read_csv(files[0])
    n_cells = T0.shape[0]
    print(f"First step: t = {t0:.3f} s, n_cells = {n_cells}")

    field = np.empty((len(files), n_cells), dtype=np.float32)
    times = np.empty(len(files), dtype=np.float64)
    field[0] = T0
    times[0] = t0

    for i, f in enumerate(files[1:], start=1):
        t_i, coords_i, T_i = _read_csv(f)
        if T_i.shape[0] != n_cells:
            raise ValueError(
                f"{f}: cell count {T_i.shape[0]} != {n_cells} (first file). "
                "Ensure the mesh has not been refined mid-run."
            )
        field[i] = T_i
        times[i] = t_i

    ensure_dir(out.parent)
    np.save(out, field)
    np.save(out.with_name(out.stem + "_coords.npy"), coords.astype(np.float32))
    np.save(out.with_name(out.stem + "_times.npy"), times.astype(np.float64))

    manifest = {
        "mode": "raw",
        "shape": list(field.shape),
        "dtype": str(field.dtype),
        "n_cells": int(n_cells),
        "t_first_s": float(times[0]),
        "t_last_s":  float(times[-1]),
        "units":     "K",
        "source":    str(src),
    }
    out.with_name(out.stem + ".manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"Wrote {out}  ({field.shape})")
    print(f"Wrote {out.with_name(out.stem + '_coords.npy')}")
    print(f"Wrote {out.with_name(out.stem + '_times.npy')}")


def run_grid(src: Path, out: Path, H: int, W: int, z_slice: float,
             z_tol: float) -> None:
    files = _list_field_csvs(src)
    if not files:
        raise SystemExit(f"No field_T*.csv files under {src}")
    print(f"Found {len(files)} CSVs in {src}")
    print(f"Grid: {H}x{W} at z = {z_slice} (tolerance {z_tol})")

    grid = np.empty((len(files), H, W), dtype=np.float32)
    times = np.empty(len(files), dtype=np.float64)

    for i, f in enumerate(files):
        t_i, coords_i, T_i = _read_csv(f)
        # Slice cells whose z is within z_tol of z_slice.
        mask = np.abs(coords_i[:, 2] - z_slice) <= z_tol
        if not mask.any():
            raise ValueError(
                f"{f}: no cells within z={z_slice} ± {z_tol}. "
                "Re-check z_slice / z_tol against your mesh."
            )
        grid[i] = _interp_to_grid(coords_i[mask, :2], T_i[mask], H, W)
        times[i] = t_i

    ensure_dir(out.parent)
    np.save(out, grid)
    np.save(out.with_name(out.stem + "_times.npy"), times.astype(np.float64))

    manifest = {
        "mode": "grid",
        "shape": list(grid.shape),
        "dtype": str(grid.dtype),
        "H": H, "W": W,
        "z_slice": float(z_slice),
        "z_tol": float(z_tol),
        "t_first_s": float(times[0]),
        "t_last_s":  float(times[-1]),
        "units":     "K",
        "source":    str(src),
        "note": (
            "Drop-in for ai_baseline pipelines that expect (N, H, W) float32. "
            "Unlike scripts/prepare_ai_dataset.py output, these values ARE "
            "true Kelvin, not [0, 1] image intensity."
        ),
    }
    out.with_name(out.stem + ".manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"Wrote {out}  ({grid.shape})")
    print(f"Range : {grid.min():.2f} .. {grid.max():.2f} K")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path,
                    help="Folder containing field_TXXXX.csv files")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output .npy path")
    ap.add_argument("--mode", choices=["raw", "grid"], default="raw")
    ap.add_argument("--H", type=int, default=128)
    ap.add_argument("--W", type=int, default=128)
    ap.add_argument("--z-slice", type=float, default=0.0,
                    help="Z value of the slicing plane (m)")
    ap.add_argument("--z-tol", type=float, default=5e-4,
                    help="Half-width of the z slab to include (m)")
    args = ap.parse_args()

    if args.mode == "raw":
        run_raw(args.src, args.out)
    else:
        run_grid(args.src, args.out, args.H, args.W, args.z_slice, args.z_tol)


if __name__ == "__main__":
    main()
