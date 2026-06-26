"""
FRB dispersion Tav-node test (optional healpy).

Ported from ``frb_dispersion_test.py``. Healpy is imported **lazily** — only
when spherical geometry helpers or :class:`FRBDispersionTavTest` are used.
Install with ``pip install tav-resonance[healpy]``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from tav_resonance.analytic import analytic_tav_ladder, ell_to_theta_phi
from tav_resonance.config import TavResonanceConfig
from tav_resonance.core import load_frb_catalog

GEOMETRY_MODEL = "healpy_spherical"
_hp: Any | None = None


def _get_healpy():
    """Lazy import healpy on first use."""
    global _hp
    if _hp is None:
        try:
            import healpy as hp
        except ImportError as exc:
            raise ImportError(
                "healpy is required for the Tav-node dispersion test. "
                "Install with: pip install tav-resonance[healpy]"
            ) from exc
        _hp = hp
    return _hp


def build_tav_node_directions(
    tav_peaks: list[int],
) -> np.ndarray:
    """
    Unit 3-vectors (N, 3) for Tav ladder nodes on the celestial sphere.

    Requires healpy (lazy import).
    """
    if not tav_peaks:
        return np.empty((0, 3), dtype=float)

    hp = _get_healpy()
    thetas: list[float] = []
    phis: list[float] = []
    for ell in tav_peaks:
        theta, phi = ell_to_theta_phi(int(ell))
        thetas.append(theta)
        phis.append(phi)
    return np.asarray(hp.ang2vec(np.asarray(thetas), np.asarray(phis)), dtype=float)


def radec_to_vec(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    """FRB (RA, Dec) [deg] → unit vectors (N, 3). Requires healpy."""
    hp = _get_healpy()
    ra = np.asarray(ra_deg, dtype=float)
    dec = np.asarray(dec_deg, dtype=float)
    theta = np.radians(90.0 - dec)
    phi = np.radians(ra % 360.0)
    return np.asarray(hp.ang2vec(theta, phi), dtype=float)


def min_angular_separations_deg(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    node_dirs: np.ndarray,
) -> np.ndarray:
    """
    Minimum great-circle separation [deg] from each sightline to any Tav node.

    Uses healpy unit vectors; separation via arccos(clipped dot product).
    """
    n_burst = len(ra_deg)
    if node_dirs.size == 0:
        return np.full(n_burst, 180.0, dtype=float)

    burst_dirs = radec_to_vec(ra_deg, dec_deg)
    node_dirs = np.asarray(node_dirs, dtype=float)
    if node_dirs.ndim == 1:
        node_dirs = node_dirs.reshape(1, 3)

    max_dot = np.max(burst_dirs @ node_dirs.T, axis=1)
    return np.degrees(np.arccos(np.clip(max_dot, -1.0, 1.0)))


class FRBDispersionTavTest:
    """
    Classify FRB sightlines near/far from analytic Tav ladder nodes; KS-test DM.

    The analytic ladder uses the fixed α = 41.341 scale. Healpy is loaded on
    first instantiation or geometry call.
    """

    def __init__(
        self,
        frb_catalog: str | Path | pd.DataFrame,
        tav_peaks: list[int] | None = None,
        *,
        config: TavResonanceConfig | None = None,
        node_threshold_deg: float | None = None,
    ):
        cfg = config or TavResonanceConfig.from_defaults()
        self.config = cfg
        self.node_threshold_deg = float(
            node_threshold_deg if node_threshold_deg is not None else cfg.node_threshold_deg
        )
        self.ks_alpha = cfg.ks_alpha
        self.ladder_alpha = cfg.ladder_alpha

        if isinstance(frb_catalog, pd.DataFrame):
            self.frb = frb_catalog.copy()
            self.catalog_path = None
        else:
            self.catalog_path = Path(frb_catalog)
            self.frb = load_frb_catalog(self.catalog_path)

        self.tav_peaks = list(tav_peaks or analytic_tav_ladder(config=cfg))
        self.node_directions = build_tav_node_directions(self.tav_peaks)
        self.node_sky_coords = self._node_sky_coords_table()
        self.results: dict[str, Any] = {}

    @classmethod
    def from_catalog_path(
        cls,
        path: str | Path,
        *,
        config: TavResonanceConfig | None = None,
        node_threshold_deg: float | None = None,
    ) -> FRBDispersionTavTest:
        """Construct from a CSV path using default fixed ladder peaks."""
        return cls(
            path,
            config=config,
            node_threshold_deg=node_threshold_deg,
        )

    def _node_sky_coords_table(self) -> list[dict[str, float]]:
        coords: list[dict[str, float]] = []
        for ell in self.tav_peaks:
            theta, phi = ell_to_theta_phi(int(ell))
            coords.append(
                {
                    "ell": int(ell),
                    "ra_deg": round(float(np.degrees(phi) % 360.0), 3),
                    "dec_deg": round(float(90.0 - np.degrees(theta)), 3),
                }
            )
        return coords

    def classify_sightline(self, ra: float, dec: float) -> str:
        """Label a single sightline as ``near_node`` or ``far_from_node``."""
        sep = float(
            min_angular_separations_deg(
                np.asarray([ra]),
                np.asarray([dec]),
                self.node_directions,
            )[0]
        )
        return "near_node" if sep < self.node_threshold_deg else "far_from_node"

    def classify_all_sightlines(self) -> tuple[np.ndarray, np.ndarray]:
        """Vectorized zone labels and minimum node separations [deg]."""
        separations = min_angular_separations_deg(
            self.frb["ra"].to_numpy(),
            self.frb["dec"].to_numpy(),
            self.node_directions,
        )
        zones = np.where(
            separations < self.node_threshold_deg,
            "near_node",
            "far_from_node",
        )
        return zones, separations

    def run_test(self) -> dict[str, Any]:
        """
        Kolmogorov–Smirnov test: DM near Tav nodes vs far from nodes.

        Returns a results dict with ``ks_statistic``, ``p_value``, and
        ``significant`` (p < config.ks_alpha).
        """
        self.frb = self.frb.copy()
        zones, separations = self.classify_all_sightlines()
        self.frb["tav_zone"] = zones
        self.frb["node_sep_deg"] = separations

        near = self.frb.loc[self.frb["tav_zone"] == "near_node", "DM"].dropna()
        far = self.frb.loc[self.frb["tav_zone"] == "far_from_node", "DM"].dropna()
        n_near = int(len(near))
        n_far = int(len(far))

        if n_near < 2 or n_far < 2:
            self.results = {
                "ks_statistic": float("nan"),
                "p_value": float("nan"),
                "n_near_node": n_near,
                "n_far_from_node": n_far,
                "significant": False,
                "geometry_model": GEOMETRY_MODEL,
                "ladder_alpha": self.ladder_alpha,
                "interpretation": (
                    f"Insufficient bursts for KS test (need ≥2 per group; "
                    f"near={n_near}, far={n_far})."
                ),
            }
            return self.results

        stat, pval = ks_2samp(near, far)
        significant = bool(pval < self.ks_alpha)
        self.results = {
            "ks_statistic": round(float(stat), 4),
            "p_value": round(float(pval), 6),
            "n_near_node": n_near,
            "n_far_from_node": n_far,
            "dm_near_mean": round(float(near.mean()), 2),
            "dm_far_mean": round(float(far.mean()), 2),
            "node_threshold_deg": self.node_threshold_deg,
            "geometry_model": GEOMETRY_MODEL,
            "ladder_alpha": self.ladder_alpha,
            "tav_peak_count": len(self.tav_peaks),
            "significant": significant,
            "interpretation": (
                "Significant DM difference near vs far Tav nodes."
                if significant
                else "No significant DM difference at current threshold."
            ),
        }
        return self.results


def run_dispersion_test(
    frb_catalog: str | Path | pd.DataFrame,
    *,
    config: TavResonanceConfig | None = None,
    node_threshold_deg: float | None = None,
    tav_peaks: list[int] | None = None,
) -> dict[str, Any]:
    """
    Convenience wrapper: build test, run KS, return results dict.
    """
    test = FRBDispersionTavTest(
        frb_catalog,
        tav_peaks=tav_peaks,
        config=config,
        node_threshold_deg=node_threshold_deg,
    )
    return test.run_test()
