"""Benchmark metrics shared by CFD/rCFD/AI evaluations.

All functions accept NumPy arrays of matched shape. Temperatures are in
Kelvin. ``T_AMB`` is the ambient initial tank temperature used as the
denominator for the relative-error definition.
"""

from __future__ import annotations

import numpy as np


T_AMB = 293.0  # K — initial tank temperature
T_DRIVE = 333.0 - 293.0  # K — driving temperature span (jet vs. tank)


def mae(y_hat: np.ndarray, y_ref: np.ndarray) -> float:
    """Mean absolute error in Kelvin."""
    return float(np.mean(np.abs(y_hat - y_ref)))


def max_abs_error(y_hat: np.ndarray, y_ref: np.ndarray) -> float:
    """Maximum absolute error in Kelvin."""
    return float(np.max(np.abs(y_hat - y_ref)))


def relative_mae(y_hat: np.ndarray, y_ref: np.ndarray,
                 t_amb: float = T_AMB) -> float:
    """Mean relative error of the temperature excess above ambient.

    Defined as ``mean(|y_hat - y_ref| / |y_ref - t_amb|)`` with a small
    floor to avoid division-by-zero at perfectly ambient cells.
    """
    denom = np.maximum(np.abs(y_ref - t_amb), 1e-9)
    return float(np.mean(np.abs(y_hat - y_ref) / denom))


def relative_max_error(y_hat: np.ndarray, y_ref: np.ndarray,
                       t_amb: float = T_AMB) -> float:
    denom = np.maximum(np.abs(y_ref - t_amb), 1e-9)
    return float(np.max(np.abs(y_hat - y_ref) / denom))


def energy_drift(T_seq: np.ndarray, cell_volume: float = 1.0,
                 rho_cp: float = 1.0) -> float:
    """Return the fractional drift of integrated thermal energy.

    Integrates ``rho_cp * cell_volume * (T - T_amb)`` over space at every
    time step and returns ``(E[-1] - E[0]) / max(|E[0]|, eps)``. For an
    adiabatic case with a constant-energy input, this is a quick sanity
    check: large drifts indicate the surrogate is creating or destroying
    energy.
    """
    if T_seq.ndim < 2:
        raise ValueError("T_seq must have at least 2 dims: (time, ...space).")
    excess = T_seq - T_AMB
    axes = tuple(range(1, T_seq.ndim))
    E = rho_cp * cell_volume * excess.sum(axis=axes)
    e0 = E[0] if abs(E[0]) > 1e-12 else 1e-12
    return float((E[-1] - E[0]) / e0)


def summary(y_hat: np.ndarray, y_ref: np.ndarray) -> dict[str, float]:
    """Return a dict bundling the standard scalar metrics."""
    return {
        "mae_K": mae(y_hat, y_ref),
        "max_ae_K": max_abs_error(y_hat, y_ref),
        "rel_mae": relative_mae(y_hat, y_ref),
        "rel_max": relative_max_error(y_hat, y_ref),
    }
