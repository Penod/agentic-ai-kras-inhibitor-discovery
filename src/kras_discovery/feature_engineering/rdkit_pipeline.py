from __future__ import annotations

import argparse
import json
from pathlib import Path

from kras_discovery.feature_engineering.rdkit_features import RDKitUnavailableError, run_rdkit_feature_pipeline


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate RDKit features for curated KRAS training data.")
    parser.add_argument(
        "--training-path",
        type=Path,
        default=root / "data" / "processed" / "kras_training_set.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "data" / "processed",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        summary = run_rdkit_feature_pipeline(args.training_path, args.output_dir)
    except RDKitUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
