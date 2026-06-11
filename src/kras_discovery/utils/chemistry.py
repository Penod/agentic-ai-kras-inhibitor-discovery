from __future__ import annotations

import re


ATOM_WEIGHTS = {
    "C": 12.01,
    "N": 14.01,
    "O": 16.00,
    "S": 32.07,
    "P": 30.97,
    "F": 19.00,
    "Cl": 35.45,
    "Br": 79.90,
    "I": 126.90,
}

ALLOWED_SMILES_PATTERN = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)=#$\\/%.]+$")
ATOM_PATTERN = re.compile(r"Cl|Br|[CNOSPFIcnosp]")


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def count_atoms(smiles: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in ATOM_PATTERN.findall(smiles):
        atom = token.capitalize()
        counts[atom] = counts.get(atom, 0) + 1
    return counts


def approximate_molecular_weight(smiles: str) -> float:
    counts = count_atoms(smiles)
    return round(sum(ATOM_WEIGHTS.get(atom, 0.0) * count for atom, count in counts.items()), 2)


def approximate_logp(smiles: str) -> float:
    counts = count_atoms(smiles)
    carbons = counts.get("C", 0)
    hetero = sum(counts.get(atom, 0) for atom in ["N", "O", "S", "P"])
    halogens = sum(counts.get(atom, 0) for atom in ["F", "Cl", "Br", "I"])
    return round((0.35 * carbons) + (0.28 * halogens) - (0.45 * hetero), 2)


def extract_basic_features(smiles: str) -> dict[str, float | int | str]:
    counts = count_atoms(smiles)
    hetero_atoms = sum(counts.get(atom, 0) for atom in ["N", "O", "S", "P"])
    rings = sum(char.isdigit() for char in smiles) // 2
    donors = counts.get("N", 0) + counts.get("O", 0)
    acceptors = counts.get("N", 0) + counts.get("O", 0) + counts.get("S", 0)
    rotatable_bonds = smiles.count("-") + max(0, counts.get("C", 0) - rings - 3)
    aromatic_atoms = sum(1 for char in smiles if char in "cnosp")
    halogens = sum(counts.get(atom, 0) for atom in ["F", "Cl", "Br", "I"])

    return {
        "atom_count": sum(counts.values()),
        "hetero_atom_count": hetero_atoms,
        "ring_count": rings,
        "hydrogen_bond_donors": donors,
        "hydrogen_bond_acceptors": acceptors,
        "rotatable_bonds": rotatable_bonds,
        "aromatic_atom_count": aromatic_atoms,
        "halogen_count": halogens,
        "molecular_weight": approximate_molecular_weight(smiles),
        "logp": approximate_logp(smiles),
    }


def is_plausible_smiles(smiles: str) -> bool:
    if not smiles or len(smiles) < 3:
        return False
    if not ALLOWED_SMILES_PATTERN.match(smiles):
        return False
    return bool(ATOM_PATTERN.search(smiles))
