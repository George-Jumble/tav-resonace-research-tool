"""Backward-compatible re-exports — see :mod:`tav_resonance.core`."""

from tav_resonance.core import (
    analyze_dm_residuals,
    classify_paths,
    estimate_redshift,
    expected_dm_igm,
    group_dm_statistics,
)

__all__ = [
    "analyze_dm_residuals",
    "classify_paths",
    "estimate_redshift",
    "expected_dm_igm",
    "group_dm_statistics",
]
