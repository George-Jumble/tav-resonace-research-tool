"""FRB resonance diagnostic plots (optional matplotlib)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tav_resonance.frb.pipeline import FrbResonanceResult


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for plots. Install with: pip install tav-resonance[viz]"
        ) from exc
    return plt


def plot_frb_resonance(
    result: FrbResonanceResult,
    *,
    output_dir: str | Path = ".",
    prefix: str = "frb_resonance",
    show: bool = False,
) -> list[Path]:
    """Save sky-path scatter and DM residual periodogram plots."""
    plt = _require_matplotlib()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    colors = {
        "void_center": "#00d2ff",
        "filament": "#ff0055",
        "boundary_cross": "#ffaa00",
    }

    fig1, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    ax0, ax1 = axes

    for path_type, group in result.frame.groupby("path_type"):
        ax0.scatter(
            group["ra"],
            group["dec"],
            s=28,
            alpha=0.85,
            c=colors.get(str(path_type), "#cccccc"),
            label=str(path_type),
        )
    ax0.set_xlabel("RA (deg)")
    ax0.set_ylabel("Dec (deg)")
    ax0.set_title("FRB Sightlines by Cosmic-Web Path")
    ax0.legend(fontsize=8)
    ax0.grid(True, alpha=0.3)

    if result.power.size:
        ax1.semilogy(result.freqs, result.power, color="#00d2ff", linewidth=1.2)
        for idx in result.harmonic_peaks:
            if 0 <= idx < len(result.freqs):
                ax1.axvline(result.freqs[idx], color="#ffaa00", linestyle="--", alpha=0.8)
    ax1.set_xlabel("Frequency")
    ax1.set_ylabel("Power")
    ax1.set_title("DM Residual Periodogram (1/7 Tav search)")
    ax1.grid(True, alpha=0.3)

    fig1.tight_layout()
    path1 = output_dir / f"{prefix}_paths_periodogram.png"
    fig1.savefig(path1, dpi=150, bbox_inches="tight")
    saved.append(path1)
    if show:
        plt.show()
    else:
        plt.close(fig1)

    return saved
