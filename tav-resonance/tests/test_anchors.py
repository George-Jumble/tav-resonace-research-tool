"""Tests for fixed geometric anchors and geometric_anchor_check."""

from __future__ import annotations

import numpy.testing as npt

from tav_resonance import geometric_anchor_check
from tav_resonance.anchors import (
    EXPECTED_LADDER_ALPHA,
    EXPECTED_MASS_GAP_MEV,
    EXPECTED_TAV_HARMONIC,
    LADDER_ALPHA_CALIBRATED,
    M0_MEV,
    TAV_HARMONIC,
)


class TestGeometricAnchorCheck:
    def test_canonical_constants_pass(self):
        report = geometric_anchor_check()
        assert report["ok"] is True
        assert all(report["checks"].values())

    def test_expected_values_match_module_constants(self):
        report = geometric_anchor_check()
        npt.assert_allclose(report["expected"]["mass_gap_mev"], M0_MEV)
        npt.assert_allclose(report["expected"]["tav_harmonic"], TAV_HARMONIC)
        npt.assert_allclose(report["expected"]["ladder_alpha"], LADDER_ALPHA_CALIBRATED)

    def test_wrong_mass_gap_fails(self):
        report = geometric_anchor_check(mass_gap_mev=100.0)
        assert report["ok"] is False
        assert report["checks"]["mass_gap_mev"] is False
        assert report["checks"]["tav_harmonic"] is True
        assert report["checks"]["ladder_alpha"] is True

    def test_wrong_harmonic_fails(self):
        report = geometric_anchor_check(tav_harmonic=0.2)
        assert report["ok"] is False
        assert report["checks"]["tav_harmonic"] is False

    def test_wrong_alpha_fails(self):
        report = geometric_anchor_check(ladder_alpha=40.0)
        assert report["ok"] is False
        assert report["checks"]["ladder_alpha"] is False

    def test_explicit_correct_values_pass(self):
        report = geometric_anchor_check(
            mass_gap_mev=EXPECTED_MASS_GAP_MEV,
            tav_harmonic=EXPECTED_TAV_HARMONIC,
            ladder_alpha=EXPECTED_LADDER_ALPHA,
        )
        assert report["ok"] is True

    def test_includes_topological_anchor_note(self):
        report = geometric_anchor_check()
        assert "313.1 MeV" in str(report["topological_anchor_note"])
