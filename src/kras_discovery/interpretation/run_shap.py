from __future__ import annotations

import argparse
import json
from pathlib import Path

from kras_discovery.interpretation.shap_analysis import SHAPDependencyError, run_shap_analysis


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate SHAP interpretation outputs for a trained KRAS model.")
    parser.add_argument("--model-path", type=Path, default=root / "artifacts" / "models" / "kras_best_model.pkl")
    parser.add_argument("--model-matrix", type=Path, default=root / "data" / "processed" / "kras_model_matrix.csv")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "processed" / "interpretation" / "shap")
    parser.add_argument("--sample-size", type=int, default=250)
    parser.add_argument("--top-n", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        summary = run_shap_analysis(
            model_path=args.model_path,
            model_matrix_path=args.model_matrix,
            output_dir=args.output_dir,
            sample_size=args.sample_size,
            top_n=args.top_n,
        )
    except (SHAPDependencyError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
