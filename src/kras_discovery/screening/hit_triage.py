from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "batch_screening" / "ranked_screening_results.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "batch_screening" / "hit_triage"


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def read_screening_results(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def passes_hit_filter(
    row: dict[str, str],
    min_kras_probability: float,
    min_admet_score: float,
    allowed_recommendations: set[str],
    require_low_toxicity: bool,
    require_trained_model: bool,
) -> bool:
    if require_trained_model and row.get("inference_mode") != "trained_model":
        return False
    if parse_float(row.get("kras_probability_active")) < min_kras_probability:
        return False
    if parse_float(row.get("admet_score")) < min_admet_score:
        return False
    if row.get("recommendation") not in allowed_recommendations:
        return False
    if require_low_toxicity and row.get("toxicity_label") != "Low risk":
        return False
    return True


def sort_hits(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (
            parse_float(row.get("kras_probability_active")),
            parse_float(row.get("overall_score")),
            parse_float(row.get("admet_score")),
        ),
        reverse=True,
    )


def triage_hits(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    min_kras_probability: float = 0.70,
    min_admet_score: float = 0.60,
    top_n: int = 25,
    require_low_toxicity: bool = True,
    require_trained_model: bool = True,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = read_screening_results(input_path)
    allowed_recommendations = {"Advance", "Advance with review"}
    filtered = [
        row
        for row in rows
        if passes_hit_filter(
            row=row,
            min_kras_probability=min_kras_probability,
            min_admet_score=min_admet_score,
            allowed_recommendations=allowed_recommendations,
            require_low_toxicity=require_low_toxicity,
            require_trained_model=require_trained_model,
        )
    ]
    hits = sort_hits(filtered)[:top_n]

    output_dir.mkdir(parents=True, exist_ok=True)
    hit_csv_path = output_dir / "top_hit_candidates.csv"
    summary_path = output_dir / "hit_triage_summary.json"

    fieldnames = list(rows[0].keys()) if rows else []
    with hit_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hits)

    summary = {
        "input_path": str(input_path),
        "total_screened": len(rows),
        "total_hit_candidates": len(filtered),
        "reported_top_n": len(hits),
        "min_kras_probability": min_kras_probability,
        "min_admet_score": min_admet_score,
        "require_low_toxicity": require_low_toxicity,
        "require_trained_model": require_trained_model,
        "allowed_recommendations": sorted(allowed_recommendations),
        "output_csv": str(hit_csv_path),
    }
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    return hits, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter batch-screening results into top KRAS hit candidates.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Ranked batch-screening CSV.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for hit triage outputs.")
    parser.add_argument("--min-kras-probability", type=float, default=0.70, help="Minimum trained-model KRAS probability.")
    parser.add_argument("--min-admet-score", type=float, default=0.60, help="Minimum ADMET score.")
    parser.add_argument("--top-n", type=int, default=25, help="Maximum number of top hit candidates to write.")
    parser.add_argument("--allow-non-low-toxicity", action="store_true", help="Do not require toxicity_label to be Low risk.")
    parser.add_argument("--allow-fallback", action="store_true", help="Do not require inference_mode to be trained_model.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hits, summary = triage_hits(
        input_path=args.input,
        output_dir=args.output_dir,
        min_kras_probability=args.min_kras_probability,
        min_admet_score=args.min_admet_score,
        top_n=args.top_n,
        require_low_toxicity=not args.allow_non_low_toxicity,
        require_trained_model=not args.allow_fallback,
    )
    print(json.dumps({"summary": summary, "hits": hits}, indent=2))


if __name__ == "__main__":
    main()
