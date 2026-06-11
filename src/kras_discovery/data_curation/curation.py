from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from kras_discovery.data_curation.targets import ChEMBLTargetConfig, TARGETS_BY_ID


RAW_FIELDS = [
    "molecule_chembl_id",
    "canonical_smiles",
    "standard_type",
    "standard_relation",
    "standard_value",
    "standard_units",
    "pchembl_value",
    "assay_chembl_id",
    "assay_type",
    "assay_description",
    "target_chembl_id",
    "target_pref_name",
    "target_organism",
    "document_chembl_id",
    "document_year",
    "src_id",
    "bao_label",
    "data_validity_comment",
]

CURATED_FIELDS = RAW_FIELDS + [
    "target_label",
    "variant_or_node",
    "activity_label",
    "activity_class",
    "curation_notes",
]

TRAINING_FIELDS = [
    "molecule_chembl_id",
    "canonical_smiles",
    "target_label",
    "variant_or_node",
    "activity_class",
    "best_pchembl_value",
    "assay_count",
    "source_target_chembl_id",
]

POTENCY_TYPES = {"IC50", "KI", "KD", "EC50", "GI50", "INHIBITION"}
MUTATION_KEYWORDS = ("G12C", "G12D", "G12V")


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_raw_record(activity: dict[str, Any]) -> dict[str, str]:
    return {field: safe_str(activity.get(field)) for field in RAW_FIELDS}


def infer_variant_or_node(record: dict[str, str], target_config: ChEMBLTargetConfig | None = None) -> str:
    if target_config and target_config.label == "SOS1":
        return "SOS1"

    haystack = " ".join(
        [
            record.get("assay_description", ""),
            record.get("target_pref_name", ""),
            record.get("bao_label", ""),
        ]
    ).upper()
    for keyword in MUTATION_KEYWORDS:
        if keyword in haystack:
            return keyword
    if "KRAS" in haystack:
        return "KRAS_UNSPECIFIED"
    return "UNKNOWN"


def classify_activity(
    pchembl_value: float | None,
    *,
    active_threshold: float = 7.0,
    inactive_threshold: float = 5.0,
) -> tuple[str, str]:
    if pchembl_value is None:
        return "unlabeled", "missing pChEMBL value"
    if pchembl_value >= active_threshold:
        return "active", f"pChEMBL >= {active_threshold}"
    if pchembl_value <= inactive_threshold:
        return "inactive", f"pChEMBL <= {inactive_threshold}"
    return "ambiguous", f"{inactive_threshold} < pChEMBL < {active_threshold}"


def curate_activity(
    activity: dict[str, Any],
    *,
    active_threshold: float = 7.0,
    inactive_threshold: float = 5.0,
) -> dict[str, str]:
    record = extract_raw_record(activity)
    target_config = TARGETS_BY_ID.get(record["target_chembl_id"])
    standard_type = record["standard_type"].upper()
    pchembl_value = safe_float(record["pchembl_value"])
    activity_class, label_note = classify_activity(
        pchembl_value,
        active_threshold=active_threshold,
        inactive_threshold=inactive_threshold,
    )

    notes = []
    if not record["canonical_smiles"]:
        notes.append("missing SMILES")
    if record["target_organism"] and record["target_organism"].lower() != "homo sapiens":
        notes.append("non-human target organism")
    if standard_type and standard_type not in POTENCY_TYPES:
        notes.append(f"non-priority activity type: {standard_type}")
    if record["data_validity_comment"]:
        notes.append(f"validity comment: {record['data_validity_comment']}")

    record.update(
        {
            "target_label": target_config.label if target_config else "UNKNOWN",
            "variant_or_node": infer_variant_or_node(record, target_config),
            "activity_label": label_note,
            "activity_class": activity_class,
            "curation_notes": " | ".join(notes),
        }
    )
    return record


def is_training_candidate(record: dict[str, str]) -> bool:
    if not record["canonical_smiles"]:
        return False
    if record["activity_class"] not in {"active", "inactive"}:
        return False
    if record["target_organism"] and record["target_organism"].lower() != "homo sapiens":
        return False
    if record["data_validity_comment"]:
        return False
    standard_type = record["standard_type"].upper()
    return standard_type in POTENCY_TYPES


def build_training_set(curated_records: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for record in curated_records:
        if not is_training_candidate(record):
            continue
        key = (record["molecule_chembl_id"], record["target_label"], record["variant_or_node"])
        grouped.setdefault(key, []).append(record)

    training_rows: list[dict[str, str]] = []
    for (molecule_id, target_label, variant), records in grouped.items():
        active_records = [record for record in records if record["activity_class"] == "active"]
        inactive_records = [record for record in records if record["activity_class"] == "inactive"]
        if active_records and inactive_records:
            continue

        chosen_class = "active" if active_records else "inactive"
        pchembl_values = [safe_float(record["pchembl_value"]) for record in records]
        numeric_values = [value for value in pchembl_values if value is not None]
        if not numeric_values:
            continue
        best_pchembl = max(numeric_values)
        first = records[0]
        training_rows.append(
            {
                "molecule_chembl_id": molecule_id,
                "canonical_smiles": first["canonical_smiles"],
                "target_label": target_label,
                "variant_or_node": variant,
                "activity_class": chosen_class,
                "best_pchembl_value": f"{best_pchembl:.3f}",
                "assay_count": str(len(records)),
                "source_target_chembl_id": first["target_chembl_id"],
            }
        )

    return sorted(
        training_rows,
        key=lambda row: (row["target_label"], row["variant_or_node"], row["molecule_chembl_id"]),
    )


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_records(curated_records: list[dict[str, str]], training_rows: list[dict[str, str]]) -> dict[str, int]:
    summary = {
        "raw_records": len(curated_records),
        "training_rows": len(training_rows),
        "active_training_rows": sum(1 for row in training_rows if row["activity_class"] == "active"),
        "inactive_training_rows": sum(1 for row in training_rows if row["activity_class"] == "inactive"),
        "ambiguous_records": sum(1 for row in curated_records if row["activity_class"] == "ambiguous"),
        "unlabeled_records": sum(1 for row in curated_records if row["activity_class"] == "unlabeled"),
    }
    for variant in ("G12C", "G12D", "G12V", "SOS1", "KRAS_UNSPECIFIED", "UNKNOWN"):
        summary[f"{variant.lower()}_training_rows"] = sum(
            1 for row in training_rows if row["variant_or_node"] == variant
        )
    return summary
