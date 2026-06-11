from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from kras_discovery.models.schemas import AgentFinding, CandidateReport, MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "external" / "example_screening_library.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "batch_screening"


def read_screening_library(input_path: Path, name_column: str, smiles_column: str) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Input CSV has no header: {input_path}")
        missing = [column for column in [name_column, smiles_column] if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"Input CSV is missing required column(s): {', '.join(missing)}")
        rows = [row for row in reader if (row.get(smiles_column) or "").strip()]
    if not rows:
        raise ValueError(f"Input CSV has no rows with a non-empty {smiles_column!r} value: {input_path}")
    return rows


def candidate_name(row: dict[str, str], name_column: str, fallback_index: int) -> str:
    name = (row.get(name_column) or "").strip()
    return name or f"Candidate-{fallback_index}"


def finding_by_agent(report: CandidateReport, agent_name: str) -> AgentFinding | None:
    for finding in report.findings:
        if finding.agent == agent_name:
            return finding
    return None


def metric(finding: AgentFinding | None, key: str, default: Any = "") -> Any:
    if finding is None:
        return default
    return finding.metrics.get(key, default)


def round_float(value: Any, digits: int = 6) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    return value


def summarize_batch_report(metadata: dict[str, str], report: CandidateReport) -> dict[str, Any]:
    validation = finding_by_agent(report, "validation")
    target_fit = finding_by_agent(report, "kras_target_fit")
    selectivity = finding_by_agent(report, "mutant_selectivity")
    admet = finding_by_agent(report, "admet")
    toxicity = finding_by_agent(report, "toxicity")
    manufacturability = finding_by_agent(report, "manufacturability")
    clinical = finding_by_agent(report, "clinical_relevance")

    return {
        "overall_rank": report.overall_rank,
        "compound": report.compound,
        "overall_score": round_float(report.overall_score),
        "recommendation": report.recommendation,
        "validation_label": validation.label if validation else "",
        "target_fit_label": target_fit.label if target_fit else "",
        "kras_probability_active": round_float(metric(target_fit, "probability_active")),
        "kras_predicted_label": metric(target_fit, "predicted_label"),
        "inference_mode": metric(target_fit, "inference_mode"),
        "mutant_selectivity_label": selectivity.label if selectivity else "",
        "mutant_selectivity_score": round_float(selectivity.score if selectivity else ""),
        "admet_label": admet.label if admet else "",
        "admet_score": round_float(admet.score if admet else ""),
        "toxicity_label": toxicity.label if toxicity else "",
        "toxicity_score": round_float(toxicity.score if toxicity else ""),
        "manufacturability_label": manufacturability.label if manufacturability else "",
        "manufacturability_score": round_float(manufacturability.score if manufacturability else ""),
        "clinical_relevance_label": clinical.label if clinical else "",
        "clinical_relevance_score": round_float(clinical.score if clinical else ""),
        "source_library": metadata.get("library", ""),
        "source_notes": metadata.get("notes", ""),
        "smiles": report.smiles,
    }


def run_batch_screening(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    name_column: str = "compound",
    smiles_column: str = "smiles",
    top_n: int | None = None,
) -> tuple[list[dict[str, Any]], list[CandidateReport]]:
    rows = read_screening_library(input_path, name_column=name_column, smiles_column=smiles_column)
    candidates = [
        MoleculeCandidate(
            name=candidate_name(row, name_column=name_column, fallback_index=index),
            smiles=(row.get(smiles_column) or "").strip(),
        )
        for index, row in enumerate(rows, start=1)
    ]
    reports = evaluate_candidates(candidates)
    if top_n is not None:
        reports = reports[:top_n]

    metadata_by_name = {
        candidate_name(row, name_column=name_column, fallback_index=index): row
        for index, row in enumerate(rows, start=1)
    }
    summary_rows = [
        summarize_batch_report(metadata_by_name.get(report.compound, {}), report)
        for report in reports
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "ranked_screening_results.csv"
    json_path = output_dir / "agent_screening_reports.json"

    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump([report.model_dump() for report in reports], handle, indent=2)

    return summary_rows, reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch screen a CSV library of KRAS pathway candidate SMILES.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Candidate library CSV.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for screening outputs.")
    parser.add_argument("--name-column", default="compound", help="Column containing compound names.")
    parser.add_argument("--smiles-column", default="smiles", help="Column containing SMILES strings.")
    parser.add_argument("--top-n", type=int, default=None, help="Only write the top N ranked candidates.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_rows, _ = run_batch_screening(
        input_path=args.input,
        output_dir=args.output_dir,
        name_column=args.name_column,
        smiles_column=args.smiles_column,
        top_n=args.top_n,
    )
    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
