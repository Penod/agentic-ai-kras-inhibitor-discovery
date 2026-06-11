from __future__ import annotations

import argparse
import json

from kras_discovery.models.schemas import MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate candidate KRAS pathway inhibitors from SMILES strings.")
    parser.add_argument("smiles", nargs="+", help="One or more SMILES strings to evaluate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = [
        MoleculeCandidate(name=f"Candidate-{index}", smiles=smiles)
        for index, smiles in enumerate(args.smiles, start=1)
    ]
    reports = evaluate_candidates(candidates)
    print(json.dumps([report.model_dump() for report in reports], indent=2))


if __name__ == "__main__":
    main()
