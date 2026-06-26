# Changelog

All notable changes to **tav-resonance** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- (placeholder) New features land here before a release tag.

### Changed

- (placeholder) Behaviour changes without breaking the public API.

### Fixed

- (placeholder) Bug fixes.

### Deprecated

- (placeholder) Features scheduled for removal.

### Removed

- (placeholder) Removed features.

### Security

- (placeholder) Vulnerability fixes.

---

## [0.1.0] - 2026-06-25

### Added

- Initial PyPI release of the Tav resonance analysis toolkit.
- Core FRB × void pipeline: `classify_paths`, `analyze_dm_residuals`, `analyze_tav_harmonics`, `run_resonance_scan`.
- Fixed geometric anchors (313.1 MeV, 1/7 harmonic, α = 41.341) via `TavResonanceConfig` and `geometric_anchor_check`.
- Analytic multipole ladder: `analytic_tav_ladder`, `evaluate_ladder_vs_observed`, `photon_redshift_step`.
- Pre-registration export (`to_prereg_json`) and schema validation.
- Optional healpy dispersion test (`FRBDispersionTavTest`).
- CLI entry point `tav-resonance`.
- Example notebooks under `examples/`.
- CI (pytest, ruff, mypy) and trusted-publishing workflow for PyPI.

[Unreleased]: https://github.com/tav-superblock/tav-resonance/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/tav-superblock/tav-resonance/releases/tag/v0.1.0