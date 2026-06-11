from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HITS_PATH = PROJECT_ROOT / "data" / "processed" / "batch_screening" / "hit_triage" / "top_hit_candidates.csv"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "batch_screening" / "hit_triage" / "hit_triage_summary.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "zinc_hit_triage_report.md"


def read_csv_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        return {}
    with summary_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: Any, digits: int = 3) -> str:
    if value in (None, ""):
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def truncate_smiles(smiles: str, max_length: int = 72) -> str:
    if len(smiles) <= max_length:
        return smiles
    return f"{smiles[: max_length - 3]}..."


def hit_interpretation(row: dict[str, str]) -> str:
    probability = as_float(row.get("kras_probability_active"))
    admet = as_float(row.get("admet_score"))
    toxicity = row.get("toxicity_label", "NA")
    recommendation = row.get("recommendation", "NA")

    activity_text = "strong trained-model KRAS activity signal" if probability >= 0.85 else "moderate trained-model KRAS activity signal"
    admet_text = "acceptable ADMET profile" if admet >= 0.75 else "reviewable ADMET profile"
    return (
        f"{row.get('compound', 'Candidate')} is prioritized because it shows a {activity_text} "
        f"(probability {fmt(probability)}), {admet_text} (score {fmt(admet)}), "
        f"toxicity label `{toxicity}`, and agent recommendation `{recommendation}`."
    )


def markdown_table(rows: list[dict[str, str]]) -> str:
    headers = [
        "Rank",
        "Compound",
        "KRAS Probability",
        "Overall",
        "ADMET",
        "Toxicity",
        "Recommendation",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for index, row in enumerate(rows, start=1):
        values = [
            str(index),
            row.get("compound", ""),
            fmt(row.get("kras_probability_active")),
            fmt(row.get("overall_score")),
            fmt(row.get("admet_score")),
            row.get("toxicity_label", ""),
            row.get("recommendation", ""),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_hit_report(hits: list[dict[str, str]], summary: dict[str, Any]) -> str:
    total_screened = summary.get("total_screened", "NA")
    min_kras = summary.get("min_kras_probability", "NA")
    min_admet = summary.get("min_admet_score", "NA")
    total_hits = summary.get("total_hit_candidates", len(hits))

    lines = [
        "# ZINC KRAS Hit Triage Report",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Objective",
        "",
        "Prioritize computational KRAS hit candidates from a sampled ZINC lead-like screening library using the trained KRAS bioactivity model and the agentic triage workflow.",
        "",
        "## Hit Selection Criteria",
        "",
        f"- Trained-model inference required: `{summary.get('require_trained_model', True)}`",
        f"- Minimum KRAS activity probability: `{min_kras}`",
        f"- Minimum ADMET score: `{min_admet}`",
        f"- Required toxicity label: `Low risk`",
        "- Allowed recommendations: `Advance`, `Advance with review`",
        "",
        "## Screening Summary",
        "",
        f"- Total screened compounds: `{total_screened}`",
        f"- Computational hit candidates passing filters: `{total_hits}`",
        f"- Reported candidates: `{len(hits)}`",
        "",
        "## Top Hit Candidates",
        "",
    ]

    if hits:
        lines.append(markdown_table(hits))
    else:
        lines.append("No hit candidates passed the current filters.")

    lines.extend(
        [
            "",
            "## Candidate Interpretations",
            "",
        ]
    )
    for index, row in enumerate(hits, start=1):
        lines.extend(
            [
                f"### {index}. {row.get('compound', 'Candidate')}",
                "",
                hit_interpretation(row),
                "",
                f"- Target-fit label: `{row.get('target_fit_label', 'NA')}`",
                f"- Inference mode: `{row.get('inference_mode', 'NA')}`",
                f"- Mutant-selectivity hypothesis: `{row.get('mutant_selectivity_label', 'NA')}`",
                f"- Manufacturability: `{row.get('manufacturability_label', 'NA')}` with score `{fmt(row.get('manufacturability_score'))}`",
                f"- SMILES: `{truncate_smiles(row.get('smiles', ''))}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "These molecules should be treated as computational hit candidates, not experimentally confirmed KRAS inhibitors. The next scientific step is structure-based validation, such as docking against a relevant KRAS mutant structure, followed by deeper medicinal chemistry review and experimental assay planning.",
            "",
        ]
    )
    return "\n".join(lines)


def write_hit_report(
    hits_path: Path = DEFAULT_HITS_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> str:
    hits = read_csv_rows(hits_path)
    summary = read_summary(summary_path)
    report = build_hit_report(hits, summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown report for KRAS hit triage results.")
    parser.add_argument("--hits", type=Path, default=DEFAULT_HITS_PATH, help="Top hit candidate CSV.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH, help="Hit triage summary JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_hit_report(hits_path=args.hits, summary_path=args.summary, output_path=args.output)
    print(f"Wrote hit triage report to {args.output}")


if __name__ == "__main__":
    main()
