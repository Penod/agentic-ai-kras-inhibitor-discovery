from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_metric(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "n/a"


def top_model_metrics(comparison: dict[str, Any]) -> dict[str, Any]:
    metrics = comparison.get("metrics", [])
    return metrics[0] if metrics else {}


def feature_names(summary: dict[str, Any], limit: int = 10) -> str:
    features = summary.get("top_features", [])[:limit]
    if not features:
        return "No feature importance output was available."
    return ", ".join(feature.get("feature", "") for feature in features)


def group_importance_text(summary: dict[str, Any]) -> str:
    groups = summary.get("group_importance", {})
    if not groups:
        return "No feature-group importance summary was available."
    return ", ".join(f"{group}: {value:.3f}" for group, value in groups.items())


def shap_text(summary: dict[str, Any]) -> str:
    if not summary:
        return "SHAP outputs were not found. Run `python -m kras_discovery.interpretation.run_shap` after installing `shap`."
    return f"SHAP was computed on {summary.get('sample_size', 'n/a')} rows. Top SHAP features: {feature_names(summary)}."


def build_report(
    *,
    full_comparison: dict[str, Any],
    druglike_comparison: dict[str, Any],
    full_importance: dict[str, Any],
    druglike_importance: dict[str, Any],
    full_shap: dict[str, Any],
    druglike_shap: dict[str, Any],
) -> str:
    full_top = top_model_metrics(full_comparison)
    druglike_top = top_model_metrics(druglike_comparison)
    full_best = full_comparison.get("best_model", full_top.get("model", "n/a"))
    druglike_best = druglike_comparison.get("best_model", druglike_top.get("model", "n/a"))

    return f"""# KRAS Model Interpretation Report

## Summary

This report summarizes model performance and interpretation outputs for the KRAS mutant-selective inhibitor discovery project. The full curated model selected **{full_best}** as the best model, while the drug-like subset selected **{druglike_best}**. The comparison supports the current modeling conclusion that ensemble methods, especially XGBoost when installed, provide the strongest predictive performance across both broad and drug-like KRAS chemical spaces.

## Dataset Context

- Full model rows: {full_comparison.get("row_count", "n/a")}
- Full model features: {full_comparison.get("feature_count", "n/a")}
- Full model class counts: {full_comparison.get("class_counts", "n/a")}
- Drug-like model rows: {druglike_comparison.get("row_count", "n/a")}
- Drug-like model features: {druglike_comparison.get("feature_count", "n/a")}
- Drug-like model class counts: {druglike_comparison.get("class_counts", "n/a")}

## Model Performance

| Dataset | Best Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full curated dataset | {full_best} | {format_metric(full_top.get("accuracy"))} | {format_metric(full_top.get("precision"))} | {format_metric(full_top.get("recall"))} | {format_metric(full_top.get("f1"))} | {format_metric(full_top.get("roc_auc"))} | {format_metric(full_top.get("pr_auc"))} |
| Drug-like subset | {druglike_best} | {format_metric(druglike_top.get("accuracy"))} | {format_metric(druglike_top.get("precision"))} | {format_metric(druglike_top.get("recall"))} | {format_metric(druglike_top.get("f1"))} | {format_metric(druglike_top.get("roc_auc"))} | {format_metric(druglike_top.get("pr_auc"))} |

## Built-In Feature Importance

### Full Curated Model

Top features: {feature_names(full_importance)}

Feature-group importance: {group_importance_text(full_importance)}

### Drug-Like Model

Top features: {feature_names(druglike_importance)}

Feature-group importance: {group_importance_text(druglike_importance)}

## SHAP Interpretation

### Full Curated Model

{shap_text(full_shap)}

### Drug-Like Model

{shap_text(druglike_shap)}

## Scientific Interpretation

The current interpretation outputs indicate whether predictive signal is concentrated in physicochemical descriptors, MACCS structural keys, or Morgan fingerprint bits. Morgan and MACCS features are useful for predictive performance but require additional chemistry mapping before they can be described as specific molecular substructures. Descriptor-level signals such as molecular weight, LogP, TPSA, heavy atom count, and ring-related features are easier to interpret directly and should be discussed alongside fingerprint features.

## Limitations

- ChEMBL activity records come from heterogeneous assays and publications.
- G12C data dominates the current KRAS training set, while G12D, G12V, and SOS1 remain thinner.
- Built-in feature importance can be biased toward high-cardinality or frequently split features.
- SHAP values improve interpretability but should still be treated as model explanations, not mechanistic proof.
- This project is for computational research and early-stage prioritization, not clinical decision-making.

## Next Steps

1. Map high-ranking MACCS and Morgan bits to representative molecular substructures.
2. Generate per-compound explanations for top predicted active compounds.
3. Add RFECV or another feature-selection workflow for thesis-style dimensionality reduction.
4. Add external validation data from BindingDB, PubChem BioAssay, or newly curated KRAS publications.
5. Promote the best model into the KRAS target-fit agent for agentic inference.
"""


def write_report(report_path: Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
