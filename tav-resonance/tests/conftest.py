"""Shared pytest fixtures for tav-resonance."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tav_resonance import TavResonanceConfig


@pytest.fixture
def default_config() -> TavResonanceConfig:
    return TavResonanceConfig.from_defaults()


@pytest.fixture
def frozen_config(default_config: TavResonanceConfig) -> TavResonanceConfig:
    default_config.freeze()
    return default_config


@pytest.fixture
def toy_frb_catalog() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 32
    return pd.DataFrame(
        {
            "ra": rng.uniform(0, 360, n),
            "dec": rng.uniform(-5, 75, n),
            "DM": rng.uniform(250, 850, n),
        }
    )


@pytest.fixture
def toy_void_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ra": [30.0, 150.0, 280.0],
            "dec": [25.0, 5.0, 60.0],
            "reff_mpc": [18.0, 20.0, 16.0],
            "z_void": [0.05, 0.06, 0.04],
        }
    )


@pytest.fixture
def seventh_harmonic_series() -> np.ndarray:
    """Residual-like series with strong 1/7 phase modulation (128 samples)."""
    t = np.linspace(0, 1, 128, endpoint=False)
    rng = np.random.default_rng(7)
    return np.sin(2 * np.pi * 7 * t) + 0.05 * rng.standard_normal(128)
