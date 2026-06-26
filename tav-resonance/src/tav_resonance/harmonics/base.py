"""Harmonic utilities — delegates to :mod:`tav_resonance.core`."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

from tav_resonance.anchors import TAV_HARMONIC
from tav_resonance.config import TavResonanceConfig
from tav_resonance.core import analyze_tav_harmonics as _analyze_tav_harmonics


@dataclass(frozen=True)
class HarmonicScanResult:
    freqs: np.ndarray
    power: np.ndarray
    harmonic_peaks: list[int]
    detected: bool
    min_peaks_required: int
    phase_tolerance: float


def harmonic_phase_match(
    phase: float,
    *,
    harmonic: float = TAV_HARMONIC,
    tolerance: float = 0.04,
) -> bool:
    nearest = round(phase / harmonic) * harmonic
    delta = abs(phase - nearest)
    delta = min(delta, abs(phase - nearest - 1.0), abs(phase - nearest + 1.0))
    return delta < tolerance


def peaks_near_harmonic(
    power: np.ndarray,
    *,
    harmonic: float = TAV_HARMONIC,
    tolerance: float = 0.04,
    peak_height_percentile: float = 90.0,
    peak_distance: int = 2,
) -> list[int]:
    if power.size < 2:
        return []
    peak_idx, _props = find_peaks(
        power,
        height=np.percentile(power, peak_height_percentile),
        distance=peak_distance,
    )
    harmonic_peaks: list[int] = []
    n = len(power)
    for idx in peak_idx:
        phase = idx / (n - 1)
        if harmonic_phase_match(phase, harmonic=harmonic, tolerance=tolerance):
            harmonic_peaks.append(int(idx))
    return harmonic_peaks


def analyze_tav_harmonics(
    series: np.ndarray,
    *,
    harmonic: float = TAV_HARMONIC,
    phase_tolerance: float = 0.04,
    min_peaks: int = 2,
    detrend: str | bool = "linear",
) -> tuple[np.ndarray, np.ndarray, list[int], bool]:
    cfg = TavResonanceConfig.from_defaults()
    return _analyze_tav_harmonics(
        series,
        config=cfg,
        phase_tolerance=phase_tolerance,
        min_peaks=min_peaks,
    )


def analyze_tav_harmonics_result(
    series: np.ndarray,
    *,
    phase_tolerance: float = 0.04,
    min_peaks: int = 2,
) -> HarmonicScanResult:
    freqs, power, peaks, detected = analyze_tav_harmonics(
        series,
        phase_tolerance=phase_tolerance,
        min_peaks=min_peaks,
    )
    return HarmonicScanResult(
        freqs=freqs,
        power=power,
        harmonic_peaks=peaks,
        detected=detected,
        min_peaks_required=min_peaks,
        phase_tolerance=phase_tolerance,
    )
