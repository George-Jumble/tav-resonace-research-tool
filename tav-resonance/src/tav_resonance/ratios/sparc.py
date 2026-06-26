"""SPARC-style shadow/baryon resonance ratio."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tav_resonance.anchors import THEORY_SPARC_RATIO


@dataclass(frozen=True)
class ResonanceRatioResult:
    mean_ratio: float
    std_ratio: float
    theory_target: float
    delta_from_theory: float
    within_tolerance: bool
    n_points: int


def calculate_shadow_baryon_ratio(frame: pd.DataFrame) -> float:
    """
    Mean V²_shadow / V²_baryon along a rotation curve.

    Expects columns: Vobs, Vgas, Vdisk, and optionally Vbulge.
    """
    required = {"Vobs", "Vgas", "Vdisk"}
    missing = required - set(frame.columns)
    if missing:
        raise KeyError(f"Rotation curve frame missing columns: {sorted(missing)}")

    v_sq_obs = frame["Vobs"].to_numpy(dtype=float) ** 2
    v_sq_baryon = (
        frame["Vgas"].to_numpy(dtype=float) ** 2 + frame["Vdisk"].to_numpy(dtype=float) ** 2
    )
    if "Vbulge" in frame.columns:
        v_sq_baryon = v_sq_baryon + frame["Vbulge"].to_numpy(dtype=float) ** 2

    v_sq_shadow = np.maximum(0.0, v_sq_obs - v_sq_baryon)
    ratio = v_sq_shadow / np.maximum(v_sq_baryon, 1e-6)
    return float(np.nanmean(ratio))


def ratio_report(
    frame: pd.DataFrame,
    *,
    theory_target: float = THEORY_SPARC_RATIO,
    tolerance_fraction: float = 0.10,
    label: str = "galaxy",
) -> ResonanceRatioResult:
    mean_ratio = calculate_shadow_baryon_ratio(frame)
    v_sq_obs = frame["Vobs"].to_numpy(dtype=float) ** 2
    v_sq_baryon = (
        frame["Vgas"].to_numpy(dtype=float) ** 2 + frame["Vdisk"].to_numpy(dtype=float) ** 2
    )
    if "Vbulge" in frame.columns:
        v_sq_baryon = v_sq_baryon + frame["Vbulge"].to_numpy(dtype=float) ** 2
    v_sq_shadow = np.maximum(0.0, v_sq_obs - v_sq_baryon)
    ratios = v_sq_shadow / np.maximum(v_sq_baryon, 1e-6)
    delta = abs(mean_ratio - theory_target)
    return ResonanceRatioResult(
        mean_ratio=mean_ratio,
        std_ratio=float(np.nanstd(ratios, ddof=1)) if len(ratios) > 1 else 0.0,
        theory_target=theory_target,
        delta_from_theory=delta,
        within_tolerance=delta <= theory_target * tolerance_fraction,
        n_points=int(len(frame)),
    )
