from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class InterpretationDependencyError(RuntimeError):
    """Raised when model interpretation dependencies are missing."""


class FeatureImportanceUnavailableError(RuntimeError):
    """Raised when a saved model does not expose feature importances."""


def import_interpretation_dependencies() -> dict[str, Any]:
    try:
        import joblib
    except ImportError as exc:
        raise InterpretationDependencyError("Model interpretation requires joblib. Install it with `pip install joblib`.") from exc
    return {"joblib": joblib}


def load_feature_columns(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Feature column file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unwrap_model(model: Any) -> Any:
    if hasattr(model, "named_steps") and "model" in model.named_steps:
        return model.named_steps["model"]
    return model


def get_feature_importance_values(model: Any) -> list[float]:
    estimator = unwrap_model(model)
    if hasattr(estimator, "feature_importances_"):
        return [float(value) for value in estimator.feature_importances_]
    if hasattr(estimator, "coef_"):
        coefficients = estimator.coef_[0] if len(estimator.coef_) else []
        return [abs(float(value)) for value in coefficients]
    raise FeatureImportanceUnavailableError(
        f"Model type {type(estimator).__name__} does not expose feature_importances_ or coef_."
    )


def feature_group(feature_name: str) -> str:
    if feature_name.startswith("maccs_"):
        return "MACCS"
    if feature_name.startswith("morgan_"):
        return "Morgan"
    return "Descriptor"


def build_importance_rows(feature_columns: list[str], importance_values: list[float]) -> list[dict[str, str]]:
    if len(feature_columns) != len(importance_values):
        raise ValueError(
            f"Feature count mismatch: {len(feature_columns)} columns vs {len(importance_values)} importances."
        )

    total = sum(max(value, 0.0) for value in importance_values)
    rows = []
    for feature, importance in zip(feature_columns, importance_values):
        normalized = importance / total if total else 0.0
        rows.append(
            {
                "feature": feature,
                "feature_group": feature_group(feature),
                "importance": f"{importance:.12f}",
                "normalized_importance": f"{normalized:.12f}",
            }
        )
    rows.sort(key=lambda row: float(row["importance"]), reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = str(rank)
    return rows


def summarize_importances(rows: list[dict[str, str]], *, top_n: int = 25) -> dict[str, Any]:
    group_totals: dict[str, float] = {}
    for row in rows:
        group = row["feature_group"]
        group_totals[group] = group_totals.get(group, 0.0) + float(row["normalized_importance"])

    return {
        "feature_count": len(rows),
        "top_n": top_n,
        "top_features": rows[:top_n],
        "group_importance": {
            group: round(value, 6)
            for group, value in sorted(group_totals.items(), key=lambda item: item[1], reverse=True)
        },
    }


def write_importance_outputs(output_dir: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "feature_importance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rank", "feature", "feature_group", "importance", "normalized_importance"],
        )
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "feature_importance_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run_feature_importance(
    *,
    model_path: Path,
    feature_columns_path: Path,
    output_dir: Path,
    top_n: int = 25,
) -> dict[str, Any]:
    deps = import_interpretation_dependencies()
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    model = deps["joblib"].load(model_path)
    feature_columns = load_feature_columns(feature_columns_path)
    importance_values = get_feature_importance_values(model)
    rows = build_importance_rows(feature_columns, importance_values)
    summary = summarize_importances(rows, top_n=top_n)
    write_importance_outputs(output_dir, rows, summary)
    return summary
