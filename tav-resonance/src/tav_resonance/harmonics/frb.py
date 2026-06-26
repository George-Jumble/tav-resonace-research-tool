"""FRB DM residual harmonic scan helpers."""

from __future__ import annotations

import pandas as pd

from tav_resonance.harmonics.base import HarmonicScanResult, analyze_tav_harmonics_result


def scan_dm_residual_harmonics(
    frame: pd.DataFrame,
    *,
    residual_column: str = "dm_residual",
    phase_tolerance: float = 0.04,
    min_peaks: int = 2,
) -> HarmonicScanResult:
    """Run 1/7 harmonic scan on FRB DM residuals."""
    if residual_column not in frame.columns:
        raise KeyError(f"Column '{residual_column}' not found in FRB frame.")
    return analyze_tav_harmonics_result(
        frame[residual_column].to_numpy(),
        phase_tolerance=phase_tolerance,
        min_peaks=min_peaks,
    )
