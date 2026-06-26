"""Statistical null tests for resonance and harmonic claims."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import ks_2samp

from tav_resonance.harmonics.base import analyze_tav_harmonics


@dataclass(frozen=True)
class PermutationNullResult:
    observed_peak_count: int
    null_peak_counts: np.ndarray
    p_value: float
    n_trials: int
    detected_under_null_fraction: float


def harmonic_permutation_null(
    series: np.ndarray,
    *,
    n_trials: int = 1000,
    seed: int = 42,
    phase_tolerance: float = 0.04,
    min_peaks: int = 2,
) -> PermutationNullResult:
    """
    Permutation null for 1/7 harmonic peak count.

    Shuffles the input series and recounts harmonic peaks under each permutation.
    """
    clean = np.asarray(series, dtype=float)
    clean = clean[np.isfinite(clean)]
    if len(clean) < 8:
        return PermutationNullResult(0, np.array([]), 1.0, n_trials, 0.0)

    _freqs, _power, observed_peaks, _detected = analyze_tav_harmonics(
        clean,
        phase_tolerance=phase_tolerance,
        min_peaks=min_peaks,
    )
    observed_count = len(observed_peaks)

    rng = np.random.default_rng(seed)
    null_counts = np.empty(n_trials, dtype=int)
    for trial in range(n_trials):
        shuffled = rng.permutation(clean)
        _f, _p, peaks, _d = analyze_tav_harmonics(
            shuffled,
            phase_tolerance=phase_tolerance,
            min_peaks=min_peaks,
        )
        null_counts[trial] = len(peaks)

    p_value = float((null_counts >= observed_count).mean())
    return PermutationNullResult(
        observed_peak_count=observed_count,
        null_peak_counts=null_counts,
        p_value=p_value,
        n_trials=n_trials,
        detected_under_null_fraction=float((null_counts >= min_peaks).mean()),
    )


def ks_dm_near_far(
    near_dm: np.ndarray,
    far_dm: np.ndarray,
    *,
    alpha: float = 0.05,
) -> dict[str, float | bool]:
    """Kolmogorov–Smirnov two-sample test on DM distributions."""
    near = np.asarray(near_dm, dtype=float)
    far = np.asarray(far_dm, dtype=float)
    near = near[np.isfinite(near)]
    far = far[np.isfinite(far)]
    if len(near) < 2 or len(far) < 2:
        return {
            "ks_statistic": float("nan"),
            "p_value": float("nan"),
            "significant": False,
            "alpha": alpha,
        }
    stat, pval = ks_2samp(near, far)
    return {
        "ks_statistic": float(stat),
        "p_value": float(pval),
        "significant": bool(pval < alpha),
        "alpha": alpha,
    }


def resonance_ratio_null(
    ratios: np.ndarray,
    *,
    theory_target: float = 5.2,
    tolerance_fraction: float = 0.10,
) -> dict[str, float | bool]:
    """
    Assess whether observed shadow/baryon ratios cluster near the theory target.

    Reports mean ratio, delta from theory, and pass/fail under tolerance band.
    """
    values = np.asarray(ratios, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "mean_ratio": float("nan"),
            "delta_from_theory": float("nan"),
            "within_tolerance": False,
            "theory_target": theory_target,
        }
    mean_ratio = float(values.mean())
    delta = abs(mean_ratio - theory_target)
    within = delta <= theory_target * tolerance_fraction
    return {
        "mean_ratio": mean_ratio,
        "std_ratio": float(values.std(ddof=1)) if values.size > 1 else 0.0,
        "delta_from_theory": delta,
        "within_tolerance": bool(within),
        "theory_target": theory_target,
        "tolerance_fraction": tolerance_fraction,
    }
