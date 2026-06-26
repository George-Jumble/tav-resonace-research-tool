"""Backward-compatible FRB submodule — see :mod:`tav_resonance.core`."""

from tav_resonance.core import (
    ResonanceScanResult,
    analyze_dm_residuals,
    classify_paths,
    estimate_redshift,
    expected_dm_igm,
    group_dm_statistics,
    load_frb_catalog,
    load_void_catalog,
    run_resonance_scan,
)
from tav_resonance.dispersion import FRBDispersionTavTest, run_dispersion_test

FrbResonanceResult = ResonanceScanResult
run_frb_resonance_pipeline = run_resonance_scan

__all__ = [
    "FRBDispersionTavTest",
    "FrbResonanceResult",
    "ResonanceScanResult",
    "analyze_dm_residuals",
    "classify_paths",
    "estimate_redshift",
    "expected_dm_igm",
    "group_dm_statistics",
    "load_frb_catalog",
    "load_void_catalog",
    "run_dispersion_test",
    "run_frb_resonance_pipeline",
    "run_resonance_scan",
]
