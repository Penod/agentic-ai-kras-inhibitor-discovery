from __future__ import annotations

import argparse
import json
from pathlib import Path

from kras_discovery.data_curation.chembl_client import ChEMBLClient
from kras_discovery.data_curation.curation import (
    CURATED_FIELDS,
    RAW_FIELDS,
    TRAINING_FIELDS,
    build_training_set,
    curate_activity,
    extract_raw_record,
    summarize_records,
    write_csv,
)
from kras_discovery.data_curation.targets import CHEMBL_TARGETS


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_chembl_curation(
    *,
    output_dir: Path,
    max_records_per_target: int | None = None,
    active_threshold: float = 7.0,
    inactive_threshold: float = 5.0,
) -> dict[str, int]:
    client = ChEMBLClient()
    raw_records: list[dict[str, str]] = []
    curated_records: list[dict[str, str]] = []

    for target in CHEMBL_TARGETS:
        activities = client.iter_activities(
            target.target_chembl_id,
            max_records=max_records_per_target,
        )
        raw_records.extend(extract_raw_record(activity) for activity in activities)
        curated_records.extend(
            curate_activity(
                activity,
                active_threshold=active_threshold,
                inactive_threshold=inactive_threshold,
            )
            for activity in activities
        )

    training_rows = build_training_set(curated_records)

    write_csv(output_dir / "kras_chembl_raw_activities.csv", raw_records, RAW_FIELDS)
    write_csv(output_dir / "kras_chembl_curated_activities.csv", curated_records, CURATED_FIELDS)
    write_csv(output_dir / "kras_training_set.csv", training_rows, TRAINING_FIELDS)

    summary = summarize_records(curated_records, training_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kras_curation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    default_output = project_root() / "data" / "processed"
    parser = argparse.ArgumentParser(description="Download and curate KRAS/SOS1 ChEMBL activity data.")
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--max-records-per-target", type=int, default=None)
    parser.add_argument("--active-threshold", type=float, default=7.0)
    parser.add_argument("--inactive-threshold", type=float, default=5.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_chembl_curation(
        output_dir=args.output_dir,
        max_records_per_target=args.max_records_per_target,
        active_threshold=args.active_threshold,
        inactive_threshold=args.inactive_threshold,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
