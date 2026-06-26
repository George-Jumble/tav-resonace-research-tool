"""Tests for 1/7 Tav harmonic detection."""

from __future__ import annotations

import numpy as np

from tav_resonance import analyze_tav_harmonics
from tav_resonance.anchors import TAV_HARMONIC
from tav_resonance.harmonics import harmonic_phase_match


class TestHarmonicPhaseMatch:
    def test_exact_seventh_multiple(self):
        assert harmonic_phase_match(2 * TAV_HARMONIC, tolerance=0.05)

    def test_rejects_off_harmonic_phase(self):
        assert not harmonic_phase_match(0.25, tolerance=0.02)


class TestAnalyzeTavHarmonics:
    def test_short_series_returns_empty(self):
        freqs, power, peaks, detected = analyze_tav_harmonics(np.array([1.0, 2.0, 3.0]))
        assert freqs.size == 0
        assert power.size == 0
        assert peaks == []
        assert detected is False

    def test_detects_seventh_harmonic_modulation(self, seventh_harmonic_series: np.ndarray):
        freqs, power, peaks, detected = analyze_tav_harmonics(
            seventh_harmonic_series,
            phase_tolerance=0.06,
            min_peaks=1,
        )
        assert freqs.size > 0
        assert power.size == freqs.size
        assert np.all(np.isfinite(freqs))
        assert np.all(np.isfinite(power))
        assert len(peaks) >= 1
        assert detected is True

    def test_white_noise_usually_not_detected(self):
        rng = np.random.default_rng(99)
        _, _, peaks, detected = analyze_tav_harmonics(
            rng.standard_normal(64),
            min_peaks=3,
            phase_tolerance=0.02,
        )
        assert len(peaks) < 3 or not detected

    def test_nan_values_are_stripped(self):
        series = np.array([1.0, np.nan, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        freqs, power, _, _ = analyze_tav_harmonics(series)
        assert freqs.size > 0
        assert power.size > 0
