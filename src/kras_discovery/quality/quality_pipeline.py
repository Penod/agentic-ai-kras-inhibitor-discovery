from __future__ import annotations

import argparse
import json
from pathlib import Path

from kras_discovery.quality.assay_quality import run_assay_quality_report
from kras_discovery.quality.druglikeness import run_druglikeness_report


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Generate KRAS drug-likeness and assay-quality reports.")
    parser.add_argument(
        "--model-matrix",
        type=Path,
        default=root / "data" / "processed" / "kras_model_matrix.csv",
    )
    parser.add_argument(
        "--curated-activities",
        type=Path,
        default=root / "data" / "processed" / "kras_chembl_curated_activities.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "processed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    druglikeness = run_druglikeness_report(args.model_matrix, args.output_dir)
    assay_quality = run_assay_quality_report(args.curated_activities, args.output_dir)
    print(
        json.dumps(
            {
                "druglikeness": druglikeness,
                "assay_quality": assay_quality,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
