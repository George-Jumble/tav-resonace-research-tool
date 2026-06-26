"""
tav-resonance — Tav-Superblock resonance analysis toolkit.

Primary API
-----------
- :mod:`tav_resonance.core` — FRB resonance scan (paths, harmonics, pipeline)
- :mod:`tav_resonance.config` — :class:`~tav_resonance.config.TavResonanceConfig`
- :mod:`tav_resonance.analytic` — fixed ladder, digamma steps, void disconnection
- :mod:`tav_resonance.dispersion` — optional healpy Tav-node KS test

Geometric anchors (313.1 MeV, 1/7 mode, α = 41.341) are fixed constants —
never fitted at runtime.
"""

from tav_resonance.__version__ import __version__
from tav_resonance.analytic import (
    analytic_tav_ladder,
    analytic_void_disconnection,
    check_void_scale_and_fractal_signatures,
    evaluate_ladder_vs_observed,
    photon_redshift_step,
)
from tav_resonance.anchors import (
    LADDER_ALPHA_CALIBRATED,
    M0_MEV,
    PATH_TYPES,
    REFERENCE_LADDER_PEAKS,
    TAV_HARMONIC,
    TOPOLOGICAL_ANCHOR_NOTE,
    geometric_anchor_check,
)
from tav_resonance.config import TavConfig, TavResonanceConfig
from tav_resonance.core import (
    ResonanceScanResult,
    analyze_dm_residuals,
    analyze_tav_harmonics,
    classify_paths,
    load_frb_catalog,
    load_void_catalog,
    run_resonance_scan,
)
from tav_resonance.dispersion import FRBDispersionTavTest, run_dispersion_test

__all__ = [
    "__version__",
    "TavResonanceConfig",
    "TavConfig",
    "M0_MEV",
    "TAV_HARMONIC",
    "LADDER_ALPHA_CALIBRATED",
    "REFERENCE_LADDER_PEAKS",
    "PATH_TYPES",
    "TOPOLOGICAL_ANCHOR_NOTE",
    "geometric_anchor_check",
    "ResonanceScanResult",
    "load_frb_catalog",
    "load_void_catalog",
    "classify_paths",
    "analyze_dm_residuals",
    "analyze_tav_harmonics",
    "run_resonance_scan",
    "analytic_tav_ladder",
    "evaluate_ladder_vs_observed",
    "analytic_void_disconnection",
    "check_void_scale_and_fractal_signatures",
    "photon_redshift_step",
    "FRBDispersionTavTest",
    "run_dispersion_test",
]
