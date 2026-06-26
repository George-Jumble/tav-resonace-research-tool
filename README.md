# tav-resonance

[![PyPI version](https://img.shields.io/pypi/v/tav-resonance.svg)](https://pypi.org/project/tav-resonance/)
[![Python](https://img.shields.io/pypi/pyversions/tav-resonance.svg)](https://pypi.org/project/tav-resonance/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.TBD.svg)](https://doi.org/10.5281/zenodo.TBD)

**tav-resonance** is a Python library for detecting and testing **7-fold (1/7) Tav harmonic structure** in astronomical datasets. It implements the resonance-analysis toolchain from the [Tav-Superblock](https://github.com/tav-superblock/TauSuperblock) / **Tau Universe** research framework: periodogram-based harmonic searches, cosmic-web path classification for fast radio bursts (FRBs), analytic multipole ladders, and pre-registration-friendly configuration.

The package treats key geometric anchors as **fixed constants** (never fitted at runtime):

| Anchor | Value | Role |
|--------|-------|------|
| Tav harmonic mode | **1/7** (≈ 0.142857…) | Fundamental resonance phase; the “142857” cyclic signature |
| Mass gap *M*₀ | **313.1 MeV** | Topological mass-gap anchor (independent of search parameters) |
| Ladder scale α | **41.341** | Analytic CMB multipole ladder ℓ = round(7·k·α + *r*) |
| Void scale τ₀ | **≈ 7 h⁻¹ Mpc** | Characteristic disconnection scale in the cosmic web |

---

## What this package does

`tav-resonance` searches astronomical time series and sightline catalogs for **periodic structure aligned with the Tav 1/7 mode**. Typical workflows:

1. **Harmonic scan** — compute a periodogram on DM residuals (or any residual series), find peaks whose phase matches multiples of 1/7.
2. **FRB × void classification** — label each burst sightline as `void_center`, `filament`, or `boundary_cross` relative to the nearest SDSS-style void.
3. **Analytic ladder** — predict CMB multipole peaks from the fixed α = 41.341 ladder and compare against observations.
4. **Tav-node dispersion test** *(optional healpy)* — Kolmogorov–Smirnov comparison of FRB DM distributions near vs far from ladder-derived sky nodes.

Core functionality requires only **NumPy, pandas, and SciPy**. Spherical geometry and plotting are optional extras.

---

## Key scientific concepts

### τ ≈ 7 h⁻¹ Mpc and the cosmic web

In the Tav framework, large-scale structure organizes around a characteristic conformal scale **τ₀ ≈ 7 h⁻¹ Mpc**. FRB sightlines are classified relative to void effective radii on the sky; void **disconnection** (suppression of matter correlations) is modeled analytically via a recursion-stabilization depth and coupling parameter κ.

### The 142857 mode (1/7 harmonic)

The repeating decimal **0.142857…** is the signature of seventh-harmonic (cyclotomic) structure. `tav-resonance` flags periodogram peaks whose normalized phase lies near integer multiples of **1/7**, using fixed tolerances declared before data access.

### Geometric mass gap at 313.1 MeV

**M₀ = 313.1 MeV** is a topological anchor in the Tav-Superblock framework — a mass-gap scale that is **declared independent** of domain-specific search parameters (FRB DM harmonics, CMB multipoles, rotation-curve ratios). It appears in config exports and analytic validation reports but is **never fitted** by this library.

### Dynamic Refresh and digamma redshift steps

**Dynamic Refresh** models discrete energy loss as FRB/cosmological signals cross Tav harmonic nodes. The package exposes `photon_redshift_step(n)` using digamma differences ψ((n+1)/2) − ψ(n/2) — the analytic “impedance step” at node *n*.

### Analytic multipole ladder (α = 41.341)

Predicted CMB multipoles follow:

```
ℓ = round(7 · k · α + residue)     residues ∈ {0, 2, 3, 6},   α = 41.341
```

with 150 < ℓ < 2200. Use `evaluate_ladder_vs_observed()` to compare against reference peaks or Planck residuals.

---

## Installation

### PyPI (recommended)

```bash
pip install tav-resonance
```

### From source

```bash
git clone https://github.com/tav-superblock/tav-resonance.git
cd tav-resonance
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Optional dependency groups

| Extra | Install command | Provides |
|-------|-----------------|----------|
| `healpy` | `pip install tav-resonance[healpy]` | Spherical Tav-node geometry, KS dispersion test |
| `astropy` | `pip install tav-resonance[astropy]` | Enhanced sky-coordinate utilities |
| `matplotlib` | `pip install tav-resonance[viz]` | Diagnostic plots (`tav_resonance.viz`) |
| `sphere` | `pip install tav-resonance[sphere]` | healpy + astropy |
| `all` | `pip install tav-resonance[all]` | All optional runtime dependencies |
| `dev` | `pip install tav-resonance[dev]` | pytest, ruff, mypy, coverage |

**Minimal install** (harmonics, ladder, path classification, pre-registration):

```bash
pip install tav-resonance
```

**Full FRB spherical analysis**:

```bash
pip install tav-resonance[sphere]
```

---

## Quickstart

### Toy FRB × void resonance scan

No catalog files required — build minimal DataFrames and run the pipeline:

```python
import numpy as np
import pandas as pd

from tav_resonance import TavResonanceConfig, run_resonance_scan, analyze_tav_harmonics

# --- toy FRB catalog (8 bursts) ---
rng = np.random.default_rng(42)
n = 48
frb = pd.DataFrame({
    "ra": rng.uniform(0, 360, n),
    "dec": rng.uniform(-10, 80, n),
    "DM": rng.uniform(200, 900, n),
})

# --- toy void catalog ---
voids = pd.DataFrame({
    "ra": [45.0, 180.0, 300.0],
    "dec": [30.0, 10.0, 55.0],
    "reff_mpc": [18.0, 22.0, 15.0],
    "z_void": [0.05, 0.06, 0.04],
})

# --- pre-register tunable thresholds (anchors stay fixed) ---
cfg = TavResonanceConfig.from_defaults()
cfg.harmonic_phase_tolerance = 0.04
cfg.freeze()

result = run_resonance_scan(frb, voids, config=cfg)
print("\n".join(result.summary_lines()))
print(f"Path mix: {result.frame['path_type'].value_counts().to_dict()}")
print(f"1/7 harmonic detected: {result.tav_resonance_detected}")
```

### 1/7 harmonic search on a residual series

```python
import numpy as np
from tav_resonance import analyze_tav_harmonics, analytic_tav_ladder

# Synthetic residuals with weak 1/7 modulation
t = np.linspace(0, 1, 128, endpoint=False)
residuals = 0.5 * np.sin(2 * np.pi * 7 * t) + 0.1 * np.random.randn(128)

freqs, power, peaks, detected = analyze_tav_harmonics(residuals)
print(f"Harmonic peak indices: {peaks}")
print(f"Tav resonance detected: {detected}")

# Fixed analytic ladder (α = 41.341, never fitted)
print(f"First ladder multipoles: {analytic_tav_ladder()[:8]}")
```

### CLI

```bash
# Export pre-registration config
tav-resonance export-config -o prereg_config.json

# Run FRB × void scan on CSV catalogs
tav-resonance run-frb --frb chime_frb_catalog.csv --void sdss_void_catalog.csv --freeze

# Tav-node KS dispersion test (requires healpy)
tav-resonance run-dispersion --frb chime_frb_catalog.csv --threshold 25
```

---

## Pre-registration workflow

`tav-resonance` separates **fixed geometric anchors** from **tunable operational parameters** so analyses can be pre-registered on OSF or similar platforms before data access.

### Fixed (recorded, never changed)

- Mass gap *M*₀ = **313.1 MeV**
- Harmonic mode **1/7**
- Ladder scale **α = 41.341**

### Tunable (declare before unblinding)

- `harmonic_phase_tolerance`, `harmonic_min_peaks`
- `void_center_fraction`, `boundary_shell_fraction`
- `node_threshold_deg`, `ks_alpha`
- `recursion_depth`, `void_kappa`

### Recommended steps

```python
from tav_resonance import TavResonanceConfig, run_resonance_scan

# 1. Instantiate defaults and adjust only operational parameters
cfg = TavResonanceConfig.from_defaults()
cfg.node_threshold_deg = 25.0
cfg.harmonic_phase_tolerance = 0.04

# 2. Freeze before touching data
cfg.freeze()

# 3. Export JSON for your pre-registration record
cfg.to_prereg_json("prereg_config.json")

# 4. Run analysis — config snapshot travels with results
result = run_resonance_scan(frb_frame, void_frame, config=cfg)
assert result.config.frozen
```

Validation helper:

```python
from tav_resonance.prereg import validate_prereg_config

errors = validate_prereg_config(cfg.to_prereg_dict())
assert errors == [], f"Config validation failed: {errors}"
```

---

## Package structure

```
src/tav_resonance/
├── core.py          # Resonance scan: paths, DM residuals, periodogram harmonics
├── config.py        # TavResonanceConfig (pre-registration)
├── analytic.py      # Fixed ladder, digamma steps, void disconnection
├── dispersion.py    # Optional healpy Tav-node KS test (lazy import)
├── anchors.py       # Fixed constants (M₀, 1/7, α, reference peaks)
├── frb/             # Backward-compatible re-exports
├── geometry/        # Ladder & sphere helpers
├── harmonics/       # Harmonic utilities
├── null/            # Permutation & KS null tests
└── viz/             # Optional matplotlib plots
```

---

## Tav-Superblock / Tau Universe framework

This package is the portable analysis layer of the broader **Tav-Superblock** program — a cross-domain resonance framework linking:

- **FRB × cosmic-web** sightline statistics ([TauSuperblock](https://github.com/tav-superblock/TauSuperblock))
- **CMB multipole** harmonic structure
- **SPARC** rotation-curve shadow/baryon ratios
- **Particle-physics** mass-gap anchors (313.1 MeV)

`tav-resonance` extracts the reusable Python core so pipelines can be installed via pip, cited independently, and integrated into notebooks or HPC workflows without the full research monolith.

---

## Citation

If you use `tav-resonance` in published research, please cite the package and the Tav-Superblock framework. A Zenodo DOI will be assigned at first release.

**Software (placeholder — update DOI after Zenodo deposit):**

```bibtex
@software{tav_resonance2026,
  author       = {{Tav-Superblock Contributors}},
  title        = {tav-resonance: Tav 7-fold harmonic analysis for astronomical data},
  year         = {2026},
  url          = {https://github.com/tav-superblock/tav-resonance},
  doi          = {10.5281/zenodo.TBD},
  version      = {0.1.0}
}
```

**Framework:**

```bibtex
@software{tausuperblock2026,
  author       = {{Tav-Superblock Contributors}},
  title        = {TauSuperblock: Cross-domain Tav resonance research toolchain},
  year         = {2026},
  url          = {https://github.com/tav-superblock/TauSuperblock}
}
```

Report the exact version in prose: `import tav_resonance; print(tav_resonance.__version__)`.

---

## Development & contributing

### Setup

```bash
git clone https://github.com/tav-superblock/tav-resonance.git
cd tav-resonance
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,all]"
```

### Tests & lint

```bash
pytest                    # unit tests
pytest --cov=tav_resonance  # with coverage
ruff check src tests
```

### Contributing guidelines

1. **Do not fit geometric anchors** — *M*₀, 1/7, and α = 41.341 must remain fixed constants.
2. **Pre-registration first** — new tunable parameters belong in `TavResonanceConfig` with defaults and schema validation.
3. **Optional deps stay optional** — healpy, astropy, and matplotlib must lazy-import or live behind extras.
4. **Tests required** — add pytest coverage for new public API in `tests/`.
5. Open a PR against `main` with a concise description and link to any related TauSuperblock issue.

Bug reports and feature requests: [GitHub Issues](https://github.com/tav-superblock/tav-resonance/issues).

---

## License

MIT License — see [LICENSE](LICENSE).

Copyright © 2026 Tav-Superblock Contributors.
