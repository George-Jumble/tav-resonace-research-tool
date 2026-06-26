"""Command-line interface for tav-resonance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tav_resonance import __version__
from tav_resonance.config import TavResonanceConfig
from tav_resonance.core import load_frb_catalog, load_void_catalog, run_resonance_scan
from tav_resonance.dispersion import run_dispersion_test
from tav_resonance.prereg import validate_prereg_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tav-resonance",
        description="Tav-Superblock resonance analysis toolkit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export-config", help="Export pre-registration config JSON")
    export.add_argument("-o", "--output", default="prereg_config.json")

    run = sub.add_parser("run-frb", help="Run FRB × void resonance scan")
    run.add_argument("--frb", required=True, help="FRB catalog CSV path")
    run.add_argument("--void", required=True, help="Void catalog CSV path")
    run.add_argument("--config", help="Optional pre-reg config JSON to load")
    run.add_argument("--freeze", action="store_true", help="Freeze config before run")

    disp = sub.add_parser("run-dispersion", help="Run healpy Tav-node KS dispersion test")
    disp.add_argument("--frb", required=True, help="FRB catalog CSV path")
    disp.add_argument("--config", help="Optional pre-reg config JSON")
    disp.add_argument("--threshold", type=float, help="Node proximity threshold [deg]")

    args = parser.parse_args(argv)

    if args.command == "export-config":
        cfg = TavResonanceConfig.from_defaults()
        cfg.freeze()
        out = cfg.to_prereg_json(args.output)
        errors = validate_prereg_config(cfg.to_prereg_dict())
        if errors:
            print("Config validation warnings:")
            for err in errors:
                print(f"  - {err}")
        print(f"Exported pre-registration config: {out}")
        return 0

    if args.command == "run-frb":
        cfg = (
            TavResonanceConfig.from_json(args.config)
            if args.config
            else TavResonanceConfig.from_defaults()
        )
        if args.freeze:
            cfg.freeze()
        frb = load_frb_catalog(args.frb)
        voids = load_void_catalog(args.void)
        result = run_resonance_scan(frb, voids, config=cfg)
        for line in result.summary_lines():
            print(line)
        print(json.dumps(result.config.to_prereg_dict(), indent=2))
        return 0

    if args.command == "run-dispersion":
        cfg = (
            TavResonanceConfig.from_json(args.config)
            if args.config
            else TavResonanceConfig.from_defaults()
        )
        results = run_dispersion_test(
            Path(args.frb),
            config=cfg,
            node_threshold_deg=args.threshold,
        )
        print(json.dumps(results, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
