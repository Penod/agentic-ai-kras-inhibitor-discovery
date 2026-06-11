from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


METADATA_COLUMNS = {
    "molecule_chembl_id",
    "canonical_smiles",
    "target_label",
    "variant_or_node",
    "activity_class",
    "activity_label",
    "best_pchembl_value",
    "lipinski_violations",
    "passes_lipinski",
    "passes_veber",
    "passes_project_druglike",
    "druglike_notes",
    "passes_assay_quality",
    "assay_quality_notes",
}


@dataclass
class ModelMatrix:
    rows: list[dict[str, str]]
    feature_columns: list[str]
    labels: list[int]


def is_numeric_feature_column(rows: list[dict[str, str]], column: str) -> bool:
    for row in rows:
        value = row.get(column, "")
        if value == "":
            continue
        try:
            float(value)
        except ValueError:
            return False
    return True


def read_model_matrix(path: Path) -> ModelMatrix:
    if not path.exists():
        raise FileNotFoundError(
            f"Model matrix not found: {path}. Run `python -m kras_discovery.feature_engineering.rdkit_pipeline` first."
        )

    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError(f"Model matrix is empty: {path}")

    if "activity_label" not in rows[0]:
        raise ValueError("Model matrix must include an `activity_label` column.")

    feature_columns = [
        column
        for column in rows[0].keys()
        if column not in METADATA_COLUMNS and is_numeric_feature_column(rows, column)
    ]
    if not feature_columns:
        raise ValueError("Model matrix does not contain any numeric feature columns.")
    labels = [int(row["activity_label"]) for row in rows]
    return ModelMatrix(rows=rows, feature_columns=feature_columns, labels=labels)


def class_counts(labels: list[int]) -> dict[str, int]:
    return {
        "inactive": sum(1 for label in labels if label == 0),
        "active": sum(1 for label in labels if label == 1),
    }
