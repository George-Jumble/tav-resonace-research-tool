"""Canonical Tav-Superblock geometric and resonance anchors."""

from __future__ import annotations

from typing import Any

TAV_HARMONIC: float = 1.0 / 7.0
"""Fundamental Tav resonance harmonic (1/7)."""

M0_MEV: float = 313.1
"""Topological mass-gap anchor (MeV). Independent of domain-specific search parameters."""

LADDER_ALPHA_REFINED: float = 41.34
LADDER_ALPHA_CALIBRATED: float = 41.341
"""Calibrated multipole ladder scale α (June 2026 fit)."""

ALLOWED_LADDER_RESIDUES: tuple[int, ...] = (0, 2, 3, 6)
LADDER_ELL_MIN: int = 150
LADDER_ELL_MAX: int = 2200
LADDER_K_MAX_DEFAULT: int = 30

THEORY_SPARC_RATIO: float = 5.2
"""Target shadow/baryon velocity-squared resonance ratio."""

IGM_DM_PER_Z: float = 855.0
"""Macquart-style mean IGM contribution (pc cm⁻³ per unit z)."""

REFERENCE_LADDER_PEAKS: tuple[int, ...] = (
    289,
    325,
    538,
    558,
    602,
    821,
    1178,
    1397,
    1441,
    1462,
    1674,
    1710,
)
"""Observed CMB multipole peaks used for ladder validation."""

PATH_TYPES: tuple[str, ...] = ("void_center", "filament", "boundary_cross")
"""FRB sightline classifications relative to cosmic voids."""

TOPOLOGICAL_ANCHOR_NOTE: str = (
    "313.1 MeV mass-gap signal is independent of domain-specific search parameters"
)

# Expected fixed anchor values (single source of truth for validation).
EXPECTED_MASS_GAP_MEV: float = M0_MEV
EXPECTED_TAV_HARMONIC: float = TAV_HARMONIC
EXPECTED_LADDER_ALPHA: float = LADDER_ALPHA_CALIBRATED


def geometric_anchor_check(
    *,
    mass_gap_mev: float | None = None,
    tav_harmonic: float | None = None,
    ladder_alpha: float | None = None,
    rtol: float = 1e-9,
    atol: float = 0.0,
) -> dict[str, Any]:
    """
    Verify that anchor values match the fixed Tav geometric constants.

    When arguments are omitted, the canonical package constants are checked
    against themselves (a runtime integrity guard). When arguments are supplied,
    they are validated against the fixed expected values — useful for
    pre-registration audits and config export verification.

    Parameters
    ----------
    mass_gap_mev, tav_harmonic, ladder_alpha:
        Optional values to validate. ``None`` means "check canonical constant".
    rtol, atol:
        Tolerances passed to floating-point comparisons.

    Returns
    -------
    dict
        ``ok`` (bool), per-anchor ``checks``, and ``expected`` snapshot.
    """
    import numpy as np

    candidates = {
        "mass_gap_mev": mass_gap_mev if mass_gap_mev is not None else M0_MEV,
        "tav_harmonic": tav_harmonic if tav_harmonic is not None else TAV_HARMONIC,
        "ladder_alpha": ladder_alpha if ladder_alpha is not None else LADDER_ALPHA_CALIBRATED,
    }
    expected = {
        "mass_gap_mev": EXPECTED_MASS_GAP_MEV,
        "tav_harmonic": EXPECTED_TAV_HARMONIC,
        "ladder_alpha": EXPECTED_LADDER_ALPHA,
    }
    checks = {
        key: bool(np.isclose(candidates[key], expected[key], rtol=rtol, atol=atol))
        for key in candidates
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "candidates": candidates,
        "expected": expected,
        "topological_anchor_note": TOPOLOGICAL_ANCHOR_NOTE,
    }
