"""Integration tests for the FRB resonance pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tav_resonance import TavResonanceConfig, run_resonance_scan
from tav_resonance.core import analyze_dm_residuals, classify_paths


@pytest.mark.integration
def test_classify_paths_labels(toy_frb_catalog: pd.DataFrame, toy_void_catalog: pd.DataFrame):
    labels, sep = classify_paths(
        toy_frb_catalog["ra"].to_numpy(),
        toy_frb_catalog["dec"].to_numpy(),
        toy_void_catalog,
    )
    assert len(labels) == len(toy_frb_catalog)
    assert len(sep) == len(toy_frb_catalog)
    assert set(labels).issubset({"void_center", "filament", "boundary_cross"})


@pytest.mark.integration
def test_run_resonance_scan(toy_frb_catalog: pd.DataFrame, toy_void_catalog: pd.DataFrame):
    cfg = TavResonanceConfig.from_defaults()
    result = run_resonance_scan(toy_frb_catalog, toy_void_catalog, config=cfg)
    assert "path_type" in result.frame.columns
    assert "dm_residual" in result.frame.columns
    assert result.config.ladder_alpha == 41.341


def test_analyze_dm_residuals_columns():
    frame = pd.DataFrame({"DM": [400.0, 600.0], "ra": [1.0, 2.0], "dec": [3.0, 4.0]})
    out = analyze_dm_residuals(frame)
    assert "dm_residual" in out.columns
    assert "expected_dm" in out.columns
    assert np.all(np.isfinite(out["dm_residual"].to_numpy()))
