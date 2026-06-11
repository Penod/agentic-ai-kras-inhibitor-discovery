from __future__ import annotations

import argparse
from pathlib import Path

from kras_discovery.interpretation.report import build_report, read_json, write_report


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate a Markdown model interpretation report.")
    parser.add_argument("--output", type=Path, default=root / "reports" / "model_interpretation_report.md")
    parser.add_argument("--full-comparison", type=Path, default=root / "data" / "processed" / "model_comparison.json")
    parser.add_argument("--druglike-comparison", type=Path, default=root / "data" / "processed" / "druglike_modeling" / "model_comparison.json")
    parser.add_argument("--full-importance", type=Path, default=root / "data" / "processed" / "interpretation" / "feature_importance_summary.json")
    parser.add_argument("--druglike-importance", type=Path, default=root / "data" / "processed" / "druglike_modeling" / "interpretation" / "feature_importance_summary.json")
    parser.add_argument("--full-shap", type=Path, default=root / "data" / "processed" / "interpretation" / "shap" / "shap_summary.json")
    parser.add_argument("--druglike-shap", type=Path, default=root / "data" / "processed" / "druglike_modeling" / "interpretation" / "shap" / "shap_summary.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    content = build_report(
        full_comparison=read_json(args.full_comparison),
        druglike_comparison=read_json(args.druglike_comparison),
        full_importance=read_json(args.full_importance),
        druglike_importance=read_json(args.druglike_importance),
        full_shap=read_json(args.full_shap),
        druglike_shap=read_json(args.druglike_shap),
    )
    write_report(args.output, content)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
