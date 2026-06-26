"""Backward-compatible re-exports — see :mod:`tav_resonance.core`."""

from tav_resonance.core import ResonanceScanResult, run_resonance_scan

FrbResonanceResult = ResonanceScanResult
run_frb_resonance_pipeline = run_resonance_scan

__all__ = [
    "FrbResonanceResult",
    "ResonanceScanResult",
    "run_frb_resonance_pipeline",
    "run_resonance_scan",
]
