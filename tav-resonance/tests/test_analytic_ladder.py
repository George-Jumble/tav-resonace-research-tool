"""Tests for analytic Tav multipole ladder generation."""

from __future__ import annotations

import numpy as np
import numpy.testing as npt

from tav_resonance.analytic import (
    analytic_tav_ladder,
    decompose_ladder_ell,
    evaluate_ladder_vs_observed,
    photon_redshift_step,
)
from tav_resonance.anchors import (
    ALLOWED_LADDER_RESIDUES,
    LADDER_ALPHA_CALIBRATED,
    LADDER_ELL_MAX,
    LADDER_ELL_MIN,
    REFERENCE_LADDER_PEAKS,
)


class TestAnalyticTavLadder:
    def test_generates_sorted_unique_multipoles(self):
        peaks = analytic_tav_ladder(k_max=15)
        assert len(peaks) > 0
        assert peaks == sorted(peaks)
        assert len(peaks) == len(set(peaks))

    def test_multipoles_within_ell_window(self):
        peaks = analytic_tav_ladder(k_max=30)
        assert all(LADDER_ELL_MIN < ell < LADDER_ELL_MAX for ell in peaks)

    def test_first_peak_near_reference_band(self):
        peaks = analytic_tav_ladder(k_max=5)
        assert min(peaks) > LADDER_ELL_MIN

    def test_k_max_controls_count(self):
        small = analytic_tav_ladder(k_max=5)
        large = analytic_tav_ladder(k_max=20)
        assert len(large) >= len(small)

    def test_decompose_ladder_ell_residues(self):
        peaks = analytic_tav_ladder(k_max=8)
        for ell in peaks[:6]:
            _k, residue = decompose_ladder_ell(ell)
            assert residue in ALLOWED_LADDER_RESIDUES


class TestEvaluateLadderVsObserved:
    def test_uses_fixed_alpha(self):
        report = evaluate_ladder_vs_observed(REFERENCE_LADDER_PEAKS[:5])
        npt.assert_allclose(report["alpha_used"], LADDER_ALPHA_CALIBRATED)
        assert report["n_peaks_compared"] == 5
        assert report["predicted_count"] > 0

    def test_comparison_table_shape(self):
        report = evaluate_ladder_vs_observed(REFERENCE_LADDER_PEAKS[:3])
        table = report["comparison_table"]
        assert len(table) == 3
        for row in table:
            assert "observed" in row
            assert "predicted" in row
            assert "residual" in row

    def test_empty_observed_handled(self):
        report = evaluate_ladder_vs_observed([])
        assert report["n_peaks_compared"] == 0
        assert np.isnan(report["mean_absolute_residual"])


class TestAnalyticDerivatives:
    def test_photon_redshift_step_positive(self):
        step = photon_redshift_step(7)
        assert step["node"] == 7
        assert step["delta_E_fraction"] > 0
