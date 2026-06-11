from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DESCRIPTOR_FIELDS = [
    "mol_wt",
    "mol_logp",
    "tpsa",
    "h_bond_donors",
    "h_bond_acceptors",
    "rotatable_bonds",
    "ring_count",
    "aromatic_ring_count",
    "fraction_csp3",
    "heavy_atom_count",
    "nhoh_count",
    "no_count",
]

MACCS_FIELDS = [f"maccs_{index}" for index in range(1, 167)]
MORGAN_FIELDS = [f"morgan_{index}" for index in range(2048)]
METADATA_FIELDS = [
    "molecule_chembl_id",
    "canonical_smiles",
    "target_label",
    "variant_or_node",
    "activity_class",
    "activity_label",
    "best_pchembl_value",
]


class RDKitUnavailableError(RuntimeError):
    """Raised when RDKit is required but not installed."""


def import_rdkit() -> dict[str, Any]:
    try:
        from rdkit import Chem
        from rdkit.Chem import Crippen, Descriptors, Lipinski, MACCSkeys, rdMolDescriptors
        from rdkit.Chem import rdFingerprintGenerator
    except ImportError as exc:
        raise RDKitUnavailableError(
            "RDKit is required for feature engineering. Install it with `pip install rdkit` "
            "or use a conda environment with `conda install -c conda-forge rdkit`."
        ) from exc
    return {
        "Chem": Chem,
        "Crippen": Crippen,
        "Descriptors": Descriptors,
        "Lipinski": Lipinski,
        "MACCSkeys": MACCSkeys,
        "rdMolDescriptors": rdMolDescriptors,
        "rdFingerprintGenerator": rdFingerprintGenerator,
    }


def activity_class_to_label(activity_class: str) -> str:
    normalized = activity_class.strip().lower()
    if normalized == "active":
        return "1"
    if normalized == "inactive":
        return "0"
    raise ValueError(f"Unsupported activity class for model matrix: {activity_class}")


def read_training_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def descriptor_row(mol: Any, rdkit: dict[str, Any]) -> dict[str, str]:
    descriptors = rdkit["Descriptors"]
    lipinski = rdkit["Lipinski"]
    crippen = rdkit["Crippen"]
    rd_mol_descriptors = rdkit["rdMolDescriptors"]
    values = {
        "mol_wt": descriptors.MolWt(mol),
        "mol_logp": crippen.MolLogP(mol),
        "tpsa": rd_mol_descriptors.CalcTPSA(mol),
        "h_bond_donors": lipinski.NumHDonors(mol),
        "h_bond_acceptors": lipinski.NumHAcceptors(mol),
        "rotatable_bonds": lipinski.NumRotatableBonds(mol),
        "ring_count": rd_mol_descriptors.CalcNumRings(mol),
        "aromatic_ring_count": rd_mol_descriptors.CalcNumAromaticRings(mol),
        "fraction_csp3": rd_mol_descriptors.CalcFractionCSP3(mol),
        "heavy_atom_count": descriptors.HeavyAtomCount(mol),
        "nhoh_count": lipinski.NHOHCount(mol),
        "no_count": lipinski.NOCount(mol),
    }
    return {key: f"{value:.6f}" if isinstance(value, float) else str(value) for key, value in values.items()}


def maccs_row(mol: Any, rdkit: dict[str, Any]) -> dict[str, str]:
    bit_vector = rdkit["MACCSkeys"].GenMACCSKeys(mol)
    return {f"maccs_{index}": str(int(bit_vector.GetBit(index))) for index in range(1, 167)}


def morgan_row(mol: Any, rdkit: dict[str, Any], *, radius: int = 2, n_bits: int = 2048) -> dict[str, str]:
    generator = rdkit["rdFingerprintGenerator"].GetMorganGenerator(radius=radius, fpSize=n_bits)
    bit_vector = generator.GetFingerprint(mol)
    return {f"morgan_{index}": str(int(bit_vector.GetBit(index))) for index in range(n_bits)}


def metadata_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "molecule_chembl_id": row.get("molecule_chembl_id", ""),
        "canonical_smiles": row.get("canonical_smiles", ""),
        "target_label": row.get("target_label", ""),
        "variant_or_node": row.get("variant_or_node", ""),
        "activity_class": row.get("activity_class", ""),
        "activity_label": activity_class_to_label(row.get("activity_class", "")),
        "best_pchembl_value": row.get("best_pchembl_value", ""),
    }


def build_feature_tables(training_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    rdkit = import_rdkit()
    chem = rdkit["Chem"]

    descriptor_rows: list[dict[str, str]] = []
    maccs_rows: list[dict[str, str]] = []
    morgan_rows: list[dict[str, str]] = []
    model_rows: list[dict[str, str]] = []
    invalid_smiles = 0

    for row in training_rows:
        smiles = row.get("canonical_smiles", "")
        mol = chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_smiles += 1
            continue

        metadata = metadata_row(row)
        descriptors = descriptor_row(mol, rdkit)
        maccs = maccs_row(mol, rdkit)
        morgan = morgan_row(mol, rdkit)

        descriptor_rows.append({**metadata, **descriptors})
        maccs_rows.append({**metadata, **maccs})
        morgan_rows.append({**metadata, **morgan})
        model_rows.append({**metadata, **descriptors, **maccs, **morgan})

    summary = {
        "input_training_rows": len(training_rows),
        "feature_rows": len(model_rows),
        "invalid_smiles": invalid_smiles,
        "descriptor_features": len(DESCRIPTOR_FIELDS),
        "maccs_features": len(MACCS_FIELDS),
        "morgan_features": len(MORGAN_FIELDS),
        "model_features": len(DESCRIPTOR_FIELDS) + len(MACCS_FIELDS) + len(MORGAN_FIELDS),
    }
    return descriptor_rows, maccs_rows, morgan_rows, model_rows, summary


def run_rdkit_feature_pipeline(training_path: Path, output_dir: Path) -> dict[str, int]:
    if not training_path.exists():
        raise FileNotFoundError(
            f"Training set not found: {training_path}. Run `python -m kras_discovery.data_curation.chembl_pipeline` first."
        )
    training_rows = read_training_rows(training_path)
    descriptor_rows, maccs_rows, morgan_rows, model_rows, summary = build_feature_tables(training_rows)

    write_csv(output_dir / "kras_features_descriptors.csv", descriptor_rows, METADATA_FIELDS + DESCRIPTOR_FIELDS)
    write_csv(output_dir / "kras_features_maccs.csv", maccs_rows, METADATA_FIELDS + MACCS_FIELDS)
    write_csv(output_dir / "kras_features_morgan.csv", morgan_rows, METADATA_FIELDS + MORGAN_FIELDS)
    write_csv(output_dir / "kras_model_matrix.csv", model_rows, METADATA_FIELDS + DESCRIPTOR_FIELDS + MACCS_FIELDS + MORGAN_FIELDS)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kras_feature_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
