"""
Core Tav resonance scan functions.

Ported from ``frb_cosmic_web_tav.py``: FRB × void path classification,
DM residual analysis, and 1/7 periodogram harmonic detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, periodogram
from scipy.spatial import cKDTree

from tav_resonance.anchors import IGM_DM_PER_Z, PATH_TYPES, TOPOLOGICAL_ANCHOR_NOTE
from tav_resonance.config import TavResonanceConfig


@dataclass
class ResonanceScanResult:
    """Output of a full FRB × void Tav resonance scan."""

    frame: pd.DataFrame
    group_stats: pd.DataFrame
    freqs: np.ndarray
    power: np.ndarray
    harmonic_peaks: list[int]
    tav_resonance_detected: bool
    config: TavResonanceConfig

    def summary_lines(self) -> list[str]:
        """Human-readable summary for logs and reports."""
        lines = [
            "Tav-resonance FRB × cosmic-web scan",
            f"Bursts analyzed: {len(self.frame)}",
            f"Path mix: {self.frame['path_type'].value_counts().to_dict()}",
            f"Harmonic peaks (periodogram modes): {self.harmonic_peaks or 'none'}",
            f"Anchors: M₀={self.config.mass_gap_mev} MeV, 1/7 mode, α={self.config.ladder_alpha}",
        ]
        if self.tav_resonance_detected:
            lines.append(
                "[TAV RESONANCE] 7-fold periodic structure detected in DM residual periodogram."
            )
        else:
            lines.append("[INCONCLUSIVE] No strong 1/7 harmonic peak pattern in DM residuals.")
        lines.append(f"[TOPOLOGICAL ANCHOR] {TOPOLOGICAL_ANCHOR_NOTE}.")
        return lines


# ---------------------------------------------------------------------------
# Catalog loaders
# ---------------------------------------------------------------------------


def load_frb_catalog(path: str | Path) -> pd.DataFrame:
    """
    Load a CHIME-style FRB CSV with normalized ``ra``, ``dec``, and ``DM`` columns.

    Rows with ``excluded_flag != 0`` are dropped when that column is present.
    """
    frame = pd.read_csv(path, low_memory=False)
    lower = {col: col.lower() for col in frame.columns}
    frame = frame.rename(columns=lower)

    if "ra" not in frame.columns or "dec" not in frame.columns:
        raise ValueError(f"{path} must contain ra and dec columns.")

    dm_col = None
    for candidate in ("dm_exc_ne2001", "bonsai_dm", "dm_fitb", "dm"):
        if candidate in frame.columns:
            dm_col = candidate
            break
    if dm_col is None:
        raise ValueError(f"{path} must contain a DM column.")

    frame = frame.copy()
    frame["DM"] = pd.to_numeric(frame[dm_col], errors="coerce")
    frame["ra"] = pd.to_numeric(frame["ra"], errors="coerce")
    frame["dec"] = pd.to_numeric(frame["dec"], errors="coerce")

    if "excluded_flag" in frame.columns:
        flag = pd.to_numeric(frame["excluded_flag"], errors="coerce").fillna(0)
        frame = frame[flag == 0]

    frame = frame.dropna(subset=["ra", "dec", "DM"])
    frame = frame[(frame["DM"] > 0) & (frame["DM"] < 5000)]
    frame = frame[(frame["dec"] >= -90.0) & (frame["dec"] <= 90.0)]
    frame["ra"] = frame["ra"] % 360.0
    return frame.reset_index(drop=True)


def load_void_catalog(path: str | Path) -> pd.DataFrame:
    """Load an SDSS-style void catalog with ``ra``, ``dec``, ``reff_mpc``, ``z_void``."""
    frame = pd.read_csv(path, low_memory=False)
    lower = {col: col.lower() for col in frame.columns}
    frame = frame.rename(columns=lower)

    ra_col = "ra" if "ra" in frame.columns else "radeg"
    dec_col = "dec" if "dec" in frame.columns else "dedeg"
    if ra_col not in frame.columns or dec_col not in frame.columns:
        raise ValueError(f"{path} must contain RA/Dec columns.")

    radius_col = None
    for candidate in ("reff_mpc", "reff", "radius_mpc", "radius"):
        if candidate in frame.columns:
            radius_col = candidate
            break
    if radius_col is None:
        frame["reff_mpc"] = 15.0
        radius_col = "reff_mpc"

    z_col = "z_void" if "z_void" in frame.columns else "z"
    if z_col not in frame.columns:
        frame["z_void"] = 0.05

    frame = frame.copy()
    frame["ra"] = pd.to_numeric(frame[ra_col], errors="coerce")
    frame["dec"] = pd.to_numeric(frame[dec_col], errors="coerce")
    frame["reff_mpc"] = pd.to_numeric(frame[radius_col], errors="coerce")
    frame["z_void"] = pd.to_numeric(frame[z_col], errors="coerce")
    frame = frame.dropna(subset=["ra", "dec", "reff_mpc"])
    frame = frame[frame["reff_mpc"] > 0]
    return frame.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _cartesian_unit_vectors(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra = np.radians(np.asarray(ra_deg, dtype=float))
    dec = np.radians(np.asarray(dec_deg, dtype=float))
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    return np.column_stack([x, y, z])


def _angular_separation_deg(
    ra1: np.ndarray,
    dec1: np.ndarray,
    ra2: np.ndarray,
    dec2: np.ndarray,
) -> np.ndarray:
    v1 = _cartesian_unit_vectors(ra1, dec1)
    v2 = _cartesian_unit_vectors(ra2, dec2)
    dot = np.sum(v1 * v2, axis=1)
    return np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))


def _angular_diameter_distance_mpc(z: np.ndarray) -> np.ndarray:
    """Low-z analytic approximation (flat ΛCDM, H₀ = 70 km s⁻¹ Mpc⁻¹)."""
    z = np.asarray(z, dtype=float)
    h0 = 70.0
    c_km_s = 299792.458
    return (c_km_s / h0) * z / (1.0 + z)


# ---------------------------------------------------------------------------
# Path classification
# ---------------------------------------------------------------------------


def classify_paths(
    frb_ra: np.ndarray,
    frb_dec: np.ndarray,
    voids: pd.DataFrame,
    *,
    config: TavResonanceConfig | None = None,
    void_center_fraction: float | None = None,
    boundary_shell_fraction: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Classify each FRB sightline relative to the nearest cosmic void.

    Labels are one of ``void_center``, ``filament``, or ``boundary_cross``
    (see :data:`~tav_resonance.anchors.PATH_TYPES`).

    Parameters
    ----------
    frb_ra, frb_dec:
        FRB sky positions [deg].
    voids:
        Void catalog with ``ra``, ``dec``, ``reff_mpc``, ``z_void``.
    config:
        Optional :class:`~tav_resonance.config.TavResonanceConfig`.

    Returns
    -------
    labels, separations
        Path-type label per burst and angular separation to nearest void [deg].
    """
    cfg = config or TavResonanceConfig.from_defaults()
    center_frac = (
        void_center_fraction if void_center_fraction is not None else cfg.void_center_fraction
    )
    boundary_frac = (
        boundary_shell_fraction
        if boundary_shell_fraction is not None
        else cfg.boundary_shell_fraction
    )

    void_xyz = _cartesian_unit_vectors(voids["ra"].to_numpy(), voids["dec"].to_numpy())
    frb_xyz = _cartesian_unit_vectors(frb_ra, frb_dec)
    _dist, idx = cKDTree(void_xyz).query(frb_xyz, k=1)

    void_ra = voids["ra"].to_numpy()[idx]
    void_dec = voids["dec"].to_numpy()[idx]
    sep = _angular_separation_deg(frb_ra, frb_dec, void_ra, void_dec)

    z_void = voids["z_void"].to_numpy()[idx]
    reff_mpc = voids["reff_mpc"].to_numpy()[idx]
    da_mpc = _angular_diameter_distance_mpc(z_void)
    theta_void_deg = np.degrees(np.arctan2(reff_mpc, da_mpc))

    labels = np.full(len(frb_ra), "filament", dtype=object)
    center_mask = sep <= center_frac * theta_void_deg
    boundary_mask = (~center_mask) & (sep <= (1.0 + boundary_frac) * theta_void_deg)
    labels[center_mask] = "void_center"
    labels[boundary_mask] = "boundary_cross"
    return labels, sep


# ---------------------------------------------------------------------------
# DM residuals
# ---------------------------------------------------------------------------


def estimate_redshift(
    dm_pc_cm3: np.ndarray,
    *,
    igm_dm_per_z: float = IGM_DM_PER_Z,
) -> np.ndarray:
    """Approximate redshift from excess DM (MW contribution already removed)."""
    dm = np.asarray(dm_pc_cm3, dtype=float)
    return np.clip((dm - 50.0) / igm_dm_per_z, 0.001, 3.0)


def expected_dm_igm(
    z: np.ndarray,
    *,
    igm_dm_per_z: float = IGM_DM_PER_Z,
) -> np.ndarray:
    """Macquart-style expected IGM contribution."""
    return igm_dm_per_z * np.asarray(z, dtype=float) + 50.0


def analyze_dm_residuals(
    frame: pd.DataFrame,
    *,
    config: TavResonanceConfig | None = None,
) -> pd.DataFrame:
    """Add ``z``, ``expected_dm``, and ``dm_residual`` columns to an FRB frame."""
    cfg = config or TavResonanceConfig.from_defaults()
    result = frame.copy()
    if "z" not in result.columns or result["z"].isna().all():
        result["z"] = estimate_redshift(result["DM"].to_numpy(), igm_dm_per_z=cfg.igm_dm_per_z)
    else:
        result["z"] = pd.to_numeric(result["z"], errors="coerce")
        missing = result["z"].isna()
        result.loc[missing, "z"] = estimate_redshift(
            result.loc[missing, "DM"].to_numpy(),
            igm_dm_per_z=cfg.igm_dm_per_z,
        )

    result["expected_dm"] = expected_dm_igm(result["z"].to_numpy(), igm_dm_per_z=cfg.igm_dm_per_z)
    result["dm_residual"] = result["DM"] - result["expected_dm"]
    return result


def group_dm_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate DM residual mean/std/count by ``path_type``."""
    return (
        frame.groupby("path_type")["dm_residual"].agg(["mean", "std", "count"]).reindex(PATH_TYPES)
    )


# ---------------------------------------------------------------------------
# 1/7 harmonic detection
# ---------------------------------------------------------------------------


def analyze_tav_harmonics(
    residuals: np.ndarray,
    *,
    config: TavResonanceConfig | None = None,
    phase_tolerance: float | None = None,
    min_peaks: int | None = None,
) -> tuple[np.ndarray, np.ndarray, list[int], bool]:
    """
    Periodogram-based 1/7 Tav harmonic search on a residual series.

    Peaks whose normalized phase lies within ``phase_tolerance`` of a multiple
    of the fixed 1/7 mode are flagged as harmonic candidates. Detection requires
    at least ``min_peaks`` such candidates.

    Returns
    -------
    freqs, power, harmonic_peak_indices, detected
    """
    cfg = config or TavResonanceConfig.from_defaults()
    harmonic = cfg.tav_harmonic
    tol = phase_tolerance if phase_tolerance is not None else cfg.harmonic_phase_tolerance
    required = min_peaks if min_peaks is not None else cfg.harmonic_min_peaks

    clean = np.asarray(residuals, dtype=float)
    clean = clean[np.isfinite(clean)]
    if len(clean) < 8:
        return np.array([]), np.array([]), [], False

    freqs, power = periodogram(clean, detrend="linear")
    peak_idx, _props = find_peaks(
        power,
        height=np.percentile(power, 90),
        distance=2,
    )
    harmonic_peaks: list[int] = []
    n = len(power)
    for idx in peak_idx:
        if n <= 1:
            continue
        phase = idx / (n - 1)
        nearest = round(phase / harmonic) * harmonic
        delta = abs(phase - nearest)
        delta = min(delta, abs(phase - nearest - 1.0), abs(phase - nearest + 1.0))
        if delta < tol:
            harmonic_peaks.append(int(idx))

    detected = len(harmonic_peaks) >= required
    return freqs, power, harmonic_peaks, detected


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_resonance_scan(
    frb_frame: pd.DataFrame,
    void_frame: pd.DataFrame,
    *,
    config: TavResonanceConfig | None = None,
) -> ResonanceScanResult:
    """
    Full Tav resonance scan: path classify → DM residuals → 1/7 harmonic test.

    Parameters
    ----------
    frb_frame:
        FRB catalog with ``ra``, ``dec``, ``DM``.
    void_frame:
        Void catalog with ``ra``, ``dec``, ``reff_mpc``, ``z_void``.
    config:
        Pre-registered :class:`~tav_resonance.config.TavResonanceConfig`.

    Returns
    -------
    ResonanceScanResult
    """
    cfg = config or TavResonanceConfig.from_defaults()
    working = frb_frame.copy()

    labels, sep = classify_paths(
        working["ra"].to_numpy(),
        working["dec"].to_numpy(),
        void_frame,
        config=cfg,
    )
    working["path_type"] = labels
    working["void_sep_deg"] = sep
    working = analyze_dm_residuals(working, config=cfg)
    group_stats = group_dm_statistics(working)

    freqs, power, harmonic_peaks, detected = analyze_tav_harmonics(
        working["dm_residual"].to_numpy(),
        config=cfg,
    )

    return ResonanceScanResult(
        frame=working,
        group_stats=group_stats,
        freqs=freqs,
        power=power,
        harmonic_peaks=harmonic_peaks,
        tav_resonance_detected=detected,
        config=cfg,
    )
