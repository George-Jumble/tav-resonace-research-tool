"""Pre-registration configuration for Tav resonance analyses."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tav_resonance.anchors import (
    IGM_DM_PER_Z,
    LADDER_ALPHA_CALIBRATED,
    LADDER_ELL_MAX,
    LADDER_ELL_MIN,
    LADDER_K_MAX_DEFAULT,
    M0_MEV,
    REFERENCE_LADDER_PEAKS,
    TAV_HARMONIC,
    TOPOLOGICAL_ANCHOR_NOTE,
)

# Geometric anchors — fixed by theory, never fitted or overridden at runtime.
FIXED_MASS_GAP_MEV: float = M0_MEV
FIXED_TAV_HARMONIC: float = TAV_HARMONIC
FIXED_LADDER_ALPHA: float = LADDER_ALPHA_CALIBRATED


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class TavResonanceConfig:
    """
    Analysis configuration for Tav resonance pipelines.

    Geometric anchors (313.1 MeV mass gap, 1/7 harmonic mode, α = 41.341) are
    **fixed constants** exposed as read-only properties — they are never fitted
    or mutated through this dataclass.

    Only operational search thresholds and IGM/path-classification parameters
    may be adjusted before :meth:`freeze` is called (pre-registration workflow).
    """

    # --- tunable operational parameters (pre-register these) ---
    harmonic_phase_tolerance: float = 0.04
    harmonic_min_peaks: int = 2
    void_center_fraction: float = 0.35
    boundary_shell_fraction: float = 0.25
    node_threshold_deg: float = 25.0
    igm_dm_per_z: float = IGM_DM_PER_Z
    ks_alpha: float = 0.05
    ladder_k_max: int = LADDER_K_MAX_DEFAULT
    recursion_depth: int = 28200
    void_kappa: float = 0.1
    reference_ladder_peaks: tuple[int, ...] = REFERENCE_LADDER_PEAKS

    # --- pre-registration state ---
    frozen: bool = False
    frozen_at: str | None = None
    schema_version: str = "1.0"

    # ------------------------------------------------------------------
    # Fixed anchors (read-only)
    # ------------------------------------------------------------------

    @property
    def mass_gap_mev(self) -> float:
        """Topological mass-gap anchor [MeV]. Fixed at 313.1 — not fittable."""
        return FIXED_MASS_GAP_MEV

    @property
    def tav_harmonic(self) -> float:
        """Fundamental 1/7 Tav resonance mode. Fixed — not fittable."""
        return FIXED_TAV_HARMONIC

    @property
    def ladder_alpha(self) -> float:
        """Analytic multipole ladder scale α. Fixed at 41.341 — not fittable."""
        return FIXED_LADDER_ALPHA

    @property
    def ladder_ell_min(self) -> int:
        return LADDER_ELL_MIN

    @property
    def ladder_ell_max(self) -> int:
        return LADDER_ELL_MAX

    @property
    def topological_anchor_note(self) -> str:
        return TOPOLOGICAL_ANCHOR_NOTE

    # ------------------------------------------------------------------
    # Factory / lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def from_defaults(cls) -> TavResonanceConfig:
        """Return the canonical default configuration."""
        return cls()

    @classmethod
    def from_json(cls, path: str | Path) -> TavResonanceConfig:
        """
        Load tunable parameters from a pre-registered JSON file.

        Anchor fields in the file are ignored if present — anchors remain fixed.
        """
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> TavResonanceConfig:
        """Build config from a dict, ignoring any anchor override attempts."""
        tunable = {
            k: v
            for k, v in payload.items()
            if k
            not in {
                "mass_gap_mev",
                "tav_harmonic",
                "ladder_alpha",
                "ladder_ell_min",
                "ladder_ell_max",
                "M0_MEV",
                "TAV_HARMONIC",
                "LADDER_ALPHA",
            }
        }
        peaks = tunable.pop("reference_ladder_peaks", REFERENCE_LADDER_PEAKS)
        cfg = cls(**{k: v for k, v in tunable.items() if k in cls.__dataclass_fields__})
        if peaks is not None:
            cfg.reference_ladder_peaks = tuple(int(p) for p in peaks)
        return cfg

    def _guard_mutation(self) -> None:
        if self.frozen:
            raise RuntimeError(
                "TavResonanceConfig is frozen for pre-registration; "
                "instantiate a new config to change parameters."
            )

    def __setattr__(self, name: str, value: object) -> None:
        if (
            name in self.__dataclass_fields__
            and name not in {"frozen", "frozen_at"}
            and getattr(self, "frozen", False)
        ):
            self._guard_mutation()
        super().__setattr__(name, value)

    def freeze(self) -> None:
        """Pin tunable parameters before data access (pre-registration step)."""
        self.frozen = True
        self.frozen_at = _utc_now()

    def unfreeze(self) -> None:
        self.frozen = False
        self.frozen_at = None

    def to_prereg_dict(self) -> dict[str, Any]:
        """
        Export config for OSF / pre-registration archives.

        Includes both tunable parameters and the fixed anchor snapshot.
        """
        payload = asdict(self)
        payload["anchors"] = {
            "mass_gap_mev": self.mass_gap_mev,
            "tav_harmonic": self.tav_harmonic,
            "ladder_alpha": self.ladder_alpha,
            "ladder_ell_min": self.ladder_ell_min,
            "ladder_ell_max": self.ladder_ell_max,
            "anchors_fixed": True,
            "topological_anchor_note": self.topological_anchor_note,
        }
        payload["_meta"] = {
            "frozen": self.frozen,
            "frozen_at": self.frozen_at,
            "exported_at": _utc_now(),
        }
        return payload

    def to_prereg_json(self, path: str | Path) -> Path:
        """Write pre-registration JSON to *path*."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_prereg_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target


# Backward-compatible alias used by earlier package revisions.
TavConfig = TavResonanceConfig
DEFAULT_CONFIG = TavResonanceConfig.from_defaults().to_prereg_dict()
