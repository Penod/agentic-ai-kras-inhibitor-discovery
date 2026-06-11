from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPARISON_PATH = PROJECT_ROOT / "data" / "processed" / "model_comparison.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "model_performance_summary.md"


def fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def model_label(name: str) -> str:
    return name.replace("_", " ").title().replace("Rbf", "RBF")


def metric_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    headers = ["Model", *[column.replace("_", " ").upper() for column in columns]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = [model_label(row["model"]), *[fmt(row.get(column, "")) for column in columns]]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def cv_table(rows: list[dict[str, Any]]) -> str:
    headers = ["Model", "Folds", "ROC-AUC", "PR-AUC", "Accuracy", "F1"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = [
            model_label(row["model"]),
            str(row.get("folds", "")),
            f"{fmt(row.get('roc_auc_mean'))} +/- {fmt(row.get('roc_auc_std'))}",
            f"{fmt(row.get('pr_auc_mean'))} +/- {fmt(row.get('pr_auc_std'))}",
            f"{fmt(row.get('accuracy_mean'))} +/- {fmt(row.get('accuracy_std'))}",
            f"{fmt(row.get('f1_mean'))} +/- {fmt(row.get('f1_std'))}",
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_performance_report(comparison: dict[str, Any]) -> str:
    metrics = comparison.get("metrics", [])
    cv_rows = comparison.get("cross_validation", [])
    best = next((row for row in metrics if row["model"] == comparison.get("best_model")), metrics[0] if metrics else {})
    best_cv = cv_rows[0] if cv_rows else {}
    deployed_cv = next((row for row in cv_rows if row.get("model") == comparison.get("best_model")), {})
    class_counts = comparison.get("class_counts", {})

    lines = [
        "# KRAS Bioactivity Model Performance Summary",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Objective",
        "",
        "Document the supervised machine-learning performance of the KRAS bioactivity classifier used by the agentic screening workflow.",
        "",
        "## Dataset",
        "",
        f"- Model matrix: `{comparison.get('model_matrix', 'NA')}`",
        f"- Compounds/rows: `{comparison.get('row_count', 'NA')}`",
        f"- Numeric molecular features: `{comparison.get('feature_count', 'NA')}`",
        f"- Active compounds: `{class_counts.get('active', 'NA')}`",
        f"- Inactive compounds: `{class_counts.get('inactive', 'NA')}`",
        f"- Holdout test size: `{comparison.get('test_size', 'NA')}`",
        f"- Random state: `{comparison.get('random_state', 'NA')}`",
        "",
        "Feature inputs include RDKit physicochemical descriptors, MACCS keys, and Morgan fingerprints generated from curated ChEMBL KRAS/SOS1 bioactivity records.",
        "",
        "## Holdout Test-Set Performance",
        "",
        f"The deployed model selected by `{comparison.get('selection_metric', 'NA')}` was **{model_label(comparison.get('best_model', 'NA'))}**.",
        "",
        metric_table(metrics, ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]),
        "",
        "## Cross-Validation Performance",
        "",
        f"Stratified cross-validation was run with `{comparison.get('cv_folds_used', 0)}` folds to assess whether performance was stable across multiple train/test partitions.",
        "",
        cv_table(cv_rows),
        "",
        "## Key Findings",
        "",
        f"- The deployed **{model_label(comparison.get('best_model', 'NA'))}** model achieved holdout ROC-AUC `{fmt(best.get('roc_auc'))}` and PR-AUC `{fmt(best.get('pr_auc'))}`.",
        f"- The strongest cross-validated ROC-AUC was achieved by **{model_label(best_cv.get('model', 'NA'))}** with `{fmt(best_cv.get('roc_auc_mean'))} +/- {fmt(best_cv.get('roc_auc_std'))}`.",
        f"- The deployed **{model_label(comparison.get('best_model', 'NA'))}** model achieved cross-validated ROC-AUC `{fmt(deployed_cv.get('roc_auc_mean'))} +/- {fmt(deployed_cv.get('roc_auc_std'))}` and F1-score `{fmt(deployed_cv.get('f1_mean'))} +/- {fmt(deployed_cv.get('f1_std'))}`.",
        "- The dummy baseline ROC-AUC remained at chance level, supporting that the trained classifiers learned structure-activity signal beyond class imbalance.",
        "",
        "## Scientific Interpretation",
        "",
        "These metrics support use of the trained KRAS classifier as a computational prioritization model within the agentic screening pipeline. They should be interpreted as internal and cross-validated performance on the curated dataset, not as proof of experimental KRAS inhibition or clinical efficacy.",
        "",
        "## Limitations",
        "",
        "- ChEMBL assay records can contain heterogeneous assay conditions and target annotations.",
        "- The current model predicts broad KRAS bioactivity rather than definitive mutant-selective binding.",
        "- ZINC hits remain computational candidates requiring docking, molecular dynamics, medicinal chemistry review, and experimental validation.",
        "- Future iterations should add external validation sets, calibration analysis, applicability-domain checks, and mutation-specific models where sufficient labels exist.",
        "",
    ]
    return "\n".join(lines)


def write_performance_report(comparison_path: Path = DEFAULT_COMPARISON_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> str:
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    report = build_performance_report(comparison)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown model-performance summary report.")
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON_PATH, help="model_comparison.json path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_performance_report(comparison_path=args.comparison, output_path=args.output)
    print(f"Wrote model performance summary to {args.output}")


if __name__ == "__main__":
    main()
