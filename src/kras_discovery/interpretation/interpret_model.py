from __future__ import annotations

import argparse
import json
from pathlib import Path

from kras_discovery.interpretation.feature_importance import (
    FeatureImportanceUnavailableError,
    InterpretationDependencyError,
    run_feature_importance,
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate feature-importance outputs for a trained KRAS model.")
    parser.add_argument("--model-path", type=Path, default=root / "artifacts" / "models" / "kras_best_model.pkl")
    parser.add_argument("--feature-columns", type=Path, default=root / "artifacts" / "models" / "feature_columns.json")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "processed" / "interpretation")
    parser.add_argument("--top-n", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        summary = run_feature_importance(
            model_path=args.model_path,
            feature_columns_path=args.feature_columns,
            output_dir=args.output_dir,
            top_n=args.top_n,
        )
    except (InterpretationDependencyError, FeatureImportanceUnavailableError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
