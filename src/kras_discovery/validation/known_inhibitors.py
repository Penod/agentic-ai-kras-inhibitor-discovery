from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from kras_discovery.models.schemas import AgentFinding, CandidateReport, MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "external" / "known_kras_inhibitors.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "known_inhibitor_validation"


def read_known_inhibitors(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def summarize_report(metadata: dict[str, str], report: CandidateReport) -> dict[str, Any]:
    target_fit = finding_by_agent(report, "kras_target_fit")
    selectivity = finding_by_agent(report, "mutant_selectivity")
    admet = finding_by_agent(report, "admet")
    toxicity = finding_by_agent(report, "toxicity")
    manufacturability = finding_by_agent(report, "manufacturability")

    return {
        "compound": report.compound,
        "expected_target": metadata.get("expected_target", ""),
        "expected_activity": metadata.get("expected_activity", ""),
        "clinical_status": metadata.get("clinical_status", ""),
        "pubchem_cid": metadata.get("pubchem_cid", ""),
        "source_url": metadata.get("source_url", ""),
        "overall_score": round_float(report.overall_score),
        "overall_rank": report.overall_rank,
        "recommendation": report.recommendation,
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
        "smiles": report.smiles,
    }


def run_known_inhibitor_validation(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[list[dict[str, Any]], list[CandidateReport]]:
    records = read_known_inhibitors(input_path)
    candidates = [
        MoleculeCandidate(name=record["compound"], smiles=record["smiles"])
        for record in records
    ]
    reports = evaluate_candidates(candidates)
    metadata_by_name = {record["compound"]: record for record in records}
    summary_rows = [
        summarize_report(metadata_by_name.get(report.compound, {}), report)
        for report in reports
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "known_kras_inhibitor_validation_summary.csv"
    json_path = output_dir / "known_kras_inhibitor_agent_reports.json"

    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump([report.model_dump() for report in reports], handle, indent=2)

    return summary_rows, reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the KRAS agent pipeline on known KRAS inhibitors.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Known inhibitor CSV input.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for validation outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_rows, _ = run_known_inhibitor_validation(input_path=args.input, output_dir=args.output_dir)
    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
