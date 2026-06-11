from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from kras_discovery.modeling.dataset import read_model_matrix
from kras_discovery.modeling.train_models import numeric_matrix


class SHAPDependencyError(RuntimeError):
    """Raised when SHAP dependencies are missing."""


def import_shap_dependencies() -> dict[str, Any]:
    try:
        import joblib
        import numpy as np
        import shap
    except ImportError as exc:
        raise SHAPDependencyError(
            "SHAP analysis requires shap, numpy, and joblib. Install them with `pip install shap numpy joblib`."
        ) from exc
    return {"joblib": joblib, "np": np, "shap": shap}


def unwrap_model(model: Any) -> Any:
    if hasattr(model, "named_steps") and "model" in model.named_steps:
        return model.named_steps["model"]
    return model


def shap_values_for_model(model: Any, x_sample: Any, shap_module: Any) -> Any:
    estimator = unwrap_model(model)
    explainer = shap_module.Explainer(estimator, x_sample)
    values = explainer(x_sample)
    raw_values = values.values
    if getattr(raw_values, "ndim", 0) == 3:
        return raw_values[:, :, -1]
    return raw_values


def build_shap_rows(feature_columns: list[str], mean_abs_values: Any) -> list[dict[str, str]]:
    rows = []
    total = float(sum(mean_abs_values))
    for feature, value in zip(feature_columns, mean_abs_values):
        numeric = float(value)
        rows.append(
            {
                "feature": feature,
                "mean_abs_shap": f"{numeric:.12f}",
                "normalized_mean_abs_shap": f"{(numeric / total if total else 0.0):.12f}",
            }
        )
    rows.sort(key=lambda row: float(row["mean_abs_shap"]), reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = str(rank)
    return rows


def write_shap_outputs(output_dir: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "shap_global_importance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rank", "feature", "mean_abs_shap", "normalized_mean_abs_shap"],
        )
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "shap_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run_shap_analysis(
    *,
    model_path: Path,
    model_matrix_path: Path,
    output_dir: Path,
    sample_size: int = 250,
    top_n: int = 25,
) -> dict[str, Any]:
    deps = import_shap_dependencies()
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    matrix = read_model_matrix(model_matrix_path)
    np = deps["np"]
    x = numeric_matrix(matrix.rows, matrix.feature_columns, np)
    x_sample = x[: min(sample_size, len(matrix.rows))]
    model = deps["joblib"].load(model_path)
    shap_values = shap_values_for_model(model, x_sample, deps["shap"])
    mean_abs_values = np.abs(shap_values).mean(axis=0)
    rows = build_shap_rows(matrix.feature_columns, mean_abs_values)
    summary = {
        "model_path": str(model_path),
        "model_matrix_path": str(model_matrix_path),
        "sample_size": int(len(x_sample)),
        "feature_count": len(matrix.feature_columns),
        "top_n": top_n,
        "top_features": rows[:top_n],
    }
    write_shap_outputs(output_dir, rows, summary)
    return summary
