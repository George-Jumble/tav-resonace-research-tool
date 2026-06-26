"""Backward-compatible re-exports — see :mod:`tav_resonance.dispersion`."""

from tav_resonance.dispersion import (
    build_tav_node_directions,
    min_angular_separations_deg,
    radec_to_vec,
)

radec_to_unit_vectors = radec_to_vec

__all__ = [
    "build_tav_node_directions",
    "min_angular_separations_deg",
    "radec_to_vec",
    "radec_to_unit_vectors",
]
