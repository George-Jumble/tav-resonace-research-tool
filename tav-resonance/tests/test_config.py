"""Tests for TavResonanceConfig pre-registration workflow."""

from __future__ import annotations

import json

import numpy.testing as npt
import pytest

from tav_resonance import TavResonanceConfig, geometric_anchor_check
from tav_resonance.prereg import validate_prereg_config


class TestTavResonanceConfig:
    def test_defaults_expose_fixed_anchors(self, default_config: TavResonanceConfig):
        npt.assert_allclose(default_config.mass_gap_mev, 313.1)
        npt.assert_allclose(default_config.tav_harmonic, 1.0 / 7.0)
        npt.assert_allclose(default_config.ladder_alpha, 41.341)

    def test_freeze_blocks_mutation(self, default_config: TavResonanceConfig):
        default_config.freeze()
        with pytest.raises(RuntimeError, match="frozen"):
            default_config.harmonic_phase_tolerance = 0.1

    def test_freeze_and_export_json(self, default_config: TavResonanceConfig, tmp_path):
        default_config.freeze()
        out = default_config.to_prereg_json(tmp_path / "cfg.json")
        payload = json.loads(out.read_text(encoding="utf-8"))

        assert payload["anchors"]["ladder_alpha"] == 41.341
        assert payload["anchors"]["mass_gap_mev"] == 313.1
        assert payload["anchors"]["anchors_fixed"] is True
        assert payload["_meta"]["frozen"] is True
        assert validate_prereg_config(payload) == []

    def test_mapping_cannot_override_anchors(self):
        cfg = TavResonanceConfig.from_mapping(
            {"ladder_alpha": 99.0, "mass_gap_mev": 1.0, "tav_harmonic": 0.5}
        )
        npt.assert_allclose(cfg.ladder_alpha, 41.341)
        npt.assert_allclose(cfg.mass_gap_mev, 313.1)
        npt.assert_allclose(cfg.tav_harmonic, 1.0 / 7.0)

    def test_exported_anchors_pass_geometric_check(self, frozen_config: TavResonanceConfig):
        anchors = frozen_config.to_prereg_dict()["anchors"]
        report = geometric_anchor_check(
            mass_gap_mev=anchors["mass_gap_mev"],
            tav_harmonic=anchors["tav_harmonic"],
            ladder_alpha=anchors["ladder_alpha"],
        )
        assert report["ok"] is True

    def test_load_from_json_roundtrip(self, tmp_path, default_config: TavResonanceConfig):
        path = tmp_path / "roundtrip.json"
        default_config.harmonic_min_peaks = 3
        default_config.to_prereg_json(path)
        loaded = TavResonanceConfig.from_json(path)
        assert loaded.harmonic_min_peaks == 3
        npt.assert_allclose(loaded.ladder_alpha, 41.341)
