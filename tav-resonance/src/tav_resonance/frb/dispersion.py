"""Backward-compatible re-export — see :mod:`tav_resonance.dispersion`."""

from tav_resonance.dispersion import (
    FRBDispersionTavTest,
    build_tav_node_directions,
    min_angular_separations_deg,
    radec_to_vec,
    run_dispersion_test,
)

__all__ = [
    "FRBDispersionTavTest",
    "build_tav_node_directions",
    "min_angular_separations_deg",
    "radec_to_vec",
    "run_dispersion_test",
]
