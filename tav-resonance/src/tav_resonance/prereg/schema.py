"""Lightweight validation for pre-registered Tav analysis configs."""

from __future__ import annotations

from typing import Any

REQUIRED_SECTIONS: tuple[str, ...] = (
    "schema_version",
    "harmonic_phase_tolerance",
    "anchors",
)


def validate_prereg_config(payload: dict[str, Any]) -> list[str]:
    """Return validation errors (empty when well-formed)."""
    errors: list[str] = []
    if "schema_version" not in payload:
        errors.append("Missing schema_version")

    anchors = payload.get("anchors", {})
    if anchors.get("anchors_fixed") is not True:
        errors.append("anchors.anchors_fixed must be true for pre-registered runs")
    if anchors.get("ladder_alpha") != 41.341:
        errors.append("anchors.ladder_alpha must remain 41.341 (fixed constant)")
    if anchors.get("mass_gap_mev") != 313.1:
        errors.append("anchors.mass_gap_mev must remain 313.1 (fixed constant)")

    tol = payload.get("harmonic_phase_tolerance")
    if tol is not None and not (0 < float(tol) < 0.5):
        errors.append("harmonic_phase_tolerance must lie in (0, 0.5)")

    return errors
