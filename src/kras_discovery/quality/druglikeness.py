from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DRUGLIKE_FIELDS = [
    "lipinski_violations",
    "passes_lipinski",
    "passes_veber",
    "passes_project_druglike",
    "druglike_notes",
]


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    numeric = safe_float(value)
    if numeric is None:
        return None
    return int(numeric)


def lipinski_violations(row: dict[str, str]) -> list[str]:
    violations: list[str] = []
    mol_wt = safe_float(row.get("mol_wt"))
    logp = safe_float(row.get("mol_logp"))
    donors = safe_int(row.get("h_bond_donors"))
    acceptors = safe_int(row.get("h_bond_acceptors"))

    if mol_wt is None or mol_wt > 500:
        violations.append("MW > 500")
    if logp is None or logp > 5:
        violations.append("LogP > 5")
    if donors is None or donors > 5:
        violations.append("HBD > 5")
    if acceptors is None or acceptors > 10:
        violations.append("HBA > 10")
    return violations


def passes_veber(row: dict[str, str]) -> bool:
    tpsa = safe_float(row.get("tpsa"))
    rotatable_bonds = safe_int(row.get("rotatable_bonds"))
    return tpsa is not None and rotatable_bonds is not None and tpsa <= 140 and rotatable_bonds <= 10


def passes_project_druglike(row: dict[str, str]) -> bool:
    mol_wt = safe_float(row.get("mol_wt"))
    logp = safe_float(row.get("mol_logp"))
    tpsa = safe_float(row.get("tpsa"))
    donors = safe_int(row.get("h_bond_donors"))
    acceptors = safe_int(row.get("h_bond_acceptors"))
    rotatable_bonds = safe_int(row.get("rotatable_bonds"))

    values_present = all(value is not None for value in [mol_wt, logp, tpsa, donors, acceptors, rotatable_bonds])
    if not values_present:
        return False

    return (
        150 <= mol_wt <= 650
        and -1 <= logp <= 6
        and tpsa <= 160
        and donors <= 5
        and acceptors <= 12
        and rotatable_bonds <= 12
    )


def add_druglikeness_flags(row: dict[str, str]) -> dict[str, str]:
    violations = lipinski_violations(row)
    veber = passes_veber(row)
    project = passes_project_druglike(row)
    notes = []
    if violations:
        notes.append("; ".join(violations))
    if not veber:
        notes.append("Veber filter not passed")
    if not project:
        notes.append("Project drug-like window not passed")

    return {
        **row,
        "lipinski_violations": str(len(violations)),
        "passes_lipinski": str(len(violations) <= 1),
        "passes_veber": str(veber),
        "passes_project_druglike": str(project),
        "druglike_notes": " | ".join(notes),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_druglikeness(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "rows": len(rows),
        "passes_lipinski": sum(1 for row in rows if row["passes_lipinski"] == "True"),
        "passes_veber": sum(1 for row in rows if row["passes_veber"] == "True"),
        "passes_project_druglike": sum(1 for row in rows if row["passes_project_druglike"] == "True"),
        "active_project_druglike": sum(
            1 for row in rows if row.get("activity_label") == "1" and row["passes_project_druglike"] == "True"
        ),
        "inactive_project_druglike": sum(
            1 for row in rows if row.get("activity_label") == "0" and row["passes_project_druglike"] == "True"
        ),
    }


def run_druglikeness_report(model_matrix_path: Path, output_dir: Path) -> dict[str, int]:
    if not model_matrix_path.exists():
        raise FileNotFoundError(
            f"Model matrix not found: {model_matrix_path}. Run `python -m kras_discovery.feature_engineering.rdkit_pipeline` first."
        )

    rows = read_csv(model_matrix_path)
    flagged_rows = [add_druglikeness_flags(row) for row in rows]
    druglike_rows = [row for row in flagged_rows if row["passes_project_druglike"] == "True"]
    summary = summarize_druglikeness(flagged_rows)

    fieldnames = list(flagged_rows[0].keys()) if flagged_rows else []
    write_csv(output_dir / "kras_model_matrix_druglikeness_report.csv", flagged_rows, fieldnames)
    write_csv(output_dir / "kras_model_matrix_druglike_subset.csv", druglike_rows, fieldnames)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kras_druglikeness_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
