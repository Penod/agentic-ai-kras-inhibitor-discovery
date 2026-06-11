from __future__ import annotations

import csv
import json
from pathlib import Path


ASSAY_QUALITY_FIELDS = [
    "passes_assay_quality",
    "assay_quality_notes",
]

PRIORITY_STANDARD_TYPES = {"IC50", "KI", "KD", "EC50", "GI50", "INHIBITION"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_assay_quality_flags(row: dict[str, str]) -> dict[str, str]:
    notes = []
    if row.get("target_organism", "").lower() != "homo sapiens":
        notes.append("non-human target organism")
    if row.get("assay_type") != "B":
        notes.append("not a binding assay")
    if row.get("standard_type", "").upper() not in PRIORITY_STANDARD_TYPES:
        notes.append("non-priority activity type")
    if row.get("data_validity_comment"):
        notes.append("ChEMBL validity comment present")
    if row.get("activity_class") not in {"active", "inactive"}:
        notes.append("not clean active/inactive label")
    if not row.get("canonical_smiles"):
        notes.append("missing SMILES")

    return {
        **row,
        "passes_assay_quality": str(not notes),
        "assay_quality_notes": " | ".join(notes),
    }


def summarize_assay_quality(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "curated_activity_records": len(rows),
        "passes_assay_quality": sum(1 for row in rows if row["passes_assay_quality"] == "True"),
        "fails_assay_quality": sum(1 for row in rows if row["passes_assay_quality"] != "True"),
        "binding_assay_records": sum(1 for row in rows if row.get("assay_type") == "B"),
        "records_with_validity_comment": sum(1 for row in rows if bool(row.get("data_validity_comment"))),
        "clean_labeled_records": sum(1 for row in rows if row.get("activity_class") in {"active", "inactive"}),
    }


def run_assay_quality_report(curated_path: Path, output_dir: Path) -> dict[str, int]:
    if not curated_path.exists():
        raise FileNotFoundError(
            f"Curated ChEMBL file not found: {curated_path}. Run `python -m kras_discovery.data_curation.chembl_pipeline` first."
        )

    rows = read_csv(curated_path)
    flagged_rows = [add_assay_quality_flags(row) for row in rows]
    quality_rows = [row for row in flagged_rows if row["passes_assay_quality"] == "True"]
    summary = summarize_assay_quality(flagged_rows)

    fieldnames = list(flagged_rows[0].keys()) if flagged_rows else []
    write_csv(output_dir / "kras_assay_quality_report.csv", flagged_rows, fieldnames)
    write_csv(output_dir / "kras_assay_quality_subset.csv", quality_rows, fieldnames)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kras_assay_quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
