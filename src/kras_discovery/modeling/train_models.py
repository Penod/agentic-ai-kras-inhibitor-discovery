from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from kras_discovery.modeling.dataset import class_counts, read_model_matrix


class ModelingDependencyError(RuntimeError):
    """Raised when model training dependencies are missing."""


def import_modeling_dependencies() -> dict[str, Any]:
    try:
        import joblib
        import numpy as np
        from sklearn.compose import ColumnTransformer
        from sklearn.dummy import DummyClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score,
            average_precision_score,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )
        from sklearn.model_selection import train_test_split
        from sklearn.model_selection import StratifiedKFold, cross_validate
        from sklearn.naive_bayes import GaussianNB
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
        from sklearn.tree import DecisionTreeClassifier
    except ImportError as exc:
        raise ModelingDependencyError(
            "Model training requires scikit-learn, numpy, and joblib. Install them with "
            "`pip install scikit-learn joblib numpy`."
        ) from exc

    dependencies: dict[str, Any] = {
        "joblib": joblib,
        "np": np,
        "ColumnTransformer": ColumnTransformer,
        "DummyClassifier": DummyClassifier,
        "RandomForestClassifier": RandomForestClassifier,
        "SimpleImputer": SimpleImputer,
        "LogisticRegression": LogisticRegression,
        "accuracy_score": accuracy_score,
        "average_precision_score": average_precision_score,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "precision_score": precision_score,
        "recall_score": recall_score,
        "roc_auc_score": roc_auc_score,
        "train_test_split": train_test_split,
        "StratifiedKFold": StratifiedKFold,
        "cross_validate": cross_validate,
        "GaussianNB": GaussianNB,
        "Pipeline": Pipeline,
        "StandardScaler": StandardScaler,
        "SVC": SVC,
        "DecisionTreeClassifier": DecisionTreeClassifier,
    }

    try:
        from xgboost import XGBClassifier
    except ImportError:
        dependencies["XGBClassifier"] = None
    else:
        dependencies["XGBClassifier"] = XGBClassifier
    return dependencies


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def numeric_matrix(rows: list[dict[str, str]], feature_columns: list[str], np: Any) -> Any:
    values = []
    for row in rows:
        values.append([float(row.get(column) or 0.0) for column in feature_columns])
    return np.asarray(values, dtype=float)


def build_models(deps: dict[str, Any], random_state: int) -> dict[str, Any]:
    models = {
        "dummy_most_frequent": deps["DummyClassifier"](strategy="most_frequent"),
        "logistic_regression": deps["Pipeline"](
            [
                ("imputer", deps["SimpleImputer"](strategy="median")),
                ("scaler", deps["StandardScaler"]()),
                (
                    "model",
                    deps["LogisticRegression"](
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "random_forest": deps["RandomForestClassifier"](
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        ),
        "decision_tree": deps["DecisionTreeClassifier"](
            class_weight="balanced",
            random_state=random_state,
            max_depth=12,
        ),
        "naive_bayes": deps["Pipeline"](
            [
                ("imputer", deps["SimpleImputer"](strategy="median")),
                ("model", deps["GaussianNB"]()),
            ]
        ),
        "svm_rbf": deps["Pipeline"](
            [
                ("imputer", deps["SimpleImputer"](strategy="median")),
                ("scaler", deps["StandardScaler"]()),
                (
                    "model",
                    deps["SVC"](
                        kernel="rbf",
                        class_weight="balanced",
                        probability=True,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }

    xgb = deps.get("XGBClassifier")
    if xgb is not None:
        models["xgboost"] = xgb(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=random_state,
        )
    return models


def positive_scores(model: Any, x_test: Any) -> Any:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x_test)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(x_test)
    return model.predict(x_test)


def evaluate_model(name: str, model: Any, x_test: Any, y_test: Any, deps: dict[str, Any]) -> tuple[dict[str, str], list[list[int]], Any, Any]:
    y_pred = model.predict(x_test)
    y_score = positive_scores(model, x_test)

    metrics = {
        "model": name,
        "accuracy": deps["accuracy_score"](y_test, y_pred),
        "precision": deps["precision_score"](y_test, y_pred, zero_division=0),
        "recall": deps["recall_score"](y_test, y_pred, zero_division=0),
        "f1": deps["f1_score"](y_test, y_pred, zero_division=0),
        "roc_auc": deps["roc_auc_score"](y_test, y_score),
        "pr_auc": deps["average_precision_score"](y_test, y_score),
    }
    matrix = deps["confusion_matrix"](y_test, y_pred, labels=[0, 1]).tolist()
    return ({key: f"{value:.6f}" if isinstance(value, float) else value for key, value in metrics.items()}, matrix, y_pred, y_score)


def write_metrics_csv(path: Path, metrics_rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics_rows)


def write_cross_validation_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "folds",
        "accuracy_mean",
        "accuracy_std",
        "precision_mean",
        "precision_std",
        "recall_mean",
        "recall_std",
        "f1_mean",
        "f1_std",
        "roc_auc_mean",
        "roc_auc_std",
        "pr_auc_mean",
        "pr_auc_std",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_confusion_matrix(path: Path, matrix: list[list[int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["actual/predicted", "predicted_inactive_0", "predicted_active_1"])
        writer.writerow(["actual_inactive_0", matrix[0][0], matrix[0][1]])
        writer.writerow(["actual_active_1", matrix[1][0], matrix[1][1]])


def write_holdout_predictions(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "holdout_index",
        "molecule_chembl_id",
        "canonical_smiles",
        "target_label",
        "variant_or_node",
        "actual_label",
        "predicted_label",
        "positive_score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_holdout_prediction_rows(
    *,
    model_name: str,
    source_rows: list[dict[str, str]],
    holdout_indices: Any,
    y_test: Any,
    y_pred: Any,
    y_score: Any,
) -> list[dict[str, str]]:
    prediction_rows: list[dict[str, str]] = []
    for position, source_index in enumerate(holdout_indices):
        source = source_rows[int(source_index)]
        prediction_rows.append(
            {
                "model": model_name,
                "holdout_index": str(int(source_index)),
                "molecule_chembl_id": source.get("molecule_chembl_id", ""),
                "canonical_smiles": source.get("canonical_smiles", ""),
                "target_label": source.get("target_label", ""),
                "variant_or_node": source.get("variant_or_node", ""),
                "actual_label": str(int(y_test[position])),
                "predicted_label": str(int(y_pred[position])),
                "positive_score": f"{float(y_score[position]):.12f}",
            }
        )
    return prediction_rows


def metric_value(row: dict[str, str], metric: str) -> float:
    return float(row[metric])


def effective_cv_folds(labels: list[int], requested_folds: int) -> int:
    counts = class_counts(labels)
    smallest_class = min(counts.values())
    return min(requested_folds, smallest_class) if smallest_class >= 2 and requested_folds >= 2 else 0


def summarize_cv_scores(name: str, scores: dict[str, Any], folds: int, np: Any) -> dict[str, str]:
    metric_map = {
        "accuracy": "test_accuracy",
        "precision": "test_precision",
        "recall": "test_recall",
        "f1": "test_f1",
        "roc_auc": "test_roc_auc",
        "pr_auc": "test_pr_auc",
    }
    row: dict[str, str] = {"model": name, "folds": str(folds)}
    for metric_name, score_key in metric_map.items():
        values = scores[score_key]
        row[f"{metric_name}_mean"] = f"{float(np.mean(values)):.6f}"
        row[f"{metric_name}_std"] = f"{float(np.std(values)):.6f}"
    return row


def cross_validate_models(
    *,
    x: Any,
    y: Any,
    deps: dict[str, Any],
    cv_folds: int,
    random_state: int,
) -> list[dict[str, str]]:
    effective_folds = effective_cv_folds([int(value) for value in y], cv_folds)
    if effective_folds == 0:
        return []

    cv = deps["StratifiedKFold"](n_splits=effective_folds, shuffle=True, random_state=random_state)
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    rows: list[dict[str, str]] = []
    for name, model in build_models(deps, random_state).items():
        scores = deps["cross_validate"](
            model,
            x,
            y,
            cv=cv,
            scoring=scoring,
            error_score="raise",
        )
        rows.append(summarize_cv_scores(name, scores, effective_folds, deps["np"]))
    rows.sort(key=lambda row: float(row["roc_auc_mean"]), reverse=True)
    return rows


def train_and_evaluate(
    *,
    model_matrix_path: Path,
    output_dir: Path,
    model_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
    selection_metric: str = "roc_auc",
    cv_folds: int = 5,
) -> dict[str, Any]:
    deps = import_modeling_dependencies()
    matrix = read_model_matrix(model_matrix_path)
    np = deps["np"]
    x = numeric_matrix(matrix.rows, matrix.feature_columns, np)
    y = np.asarray(matrix.labels, dtype=int)
    cv_rows = cross_validate_models(
        x=x,
        y=y,
        deps=deps,
        cv_folds=cv_folds,
        random_state=random_state,
    )

    row_indices = np.arange(len(matrix.rows))
    x_train, x_test, y_train, y_test, _, holdout_indices = deps["train_test_split"](
        x,
        y,
        row_indices,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    metrics_rows: list[dict[str, str]] = []
    confusion_matrices: dict[str, list[list[int]]] = {}
    fitted_models: dict[str, Any] = {}
    holdout_prediction_rows: list[dict[str, str]] = []
    for name, model in build_models(deps, random_state).items():
        model.fit(x_train, y_train)
        metrics, matrix_values, y_pred, y_score = evaluate_model(name, model, x_test, y_test, deps)
        metrics_rows.append(metrics)
        confusion_matrices[name] = matrix_values
        fitted_models[name] = model
        holdout_prediction_rows.extend(
            build_holdout_prediction_rows(
                model_name=name,
                source_rows=matrix.rows,
                holdout_indices=holdout_indices,
                y_test=y_test,
                y_pred=y_pred,
                y_score=y_score,
            )
        )

    metrics_rows.sort(key=lambda row: metric_value(row, selection_metric), reverse=True)
    best_model_name = metrics_rows[0]["model"]
    best_model = fitted_models[best_model_name]

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    write_metrics_csv(output_dir / "model_metrics.csv", metrics_rows)
    write_cross_validation_csv(output_dir / "cross_validation_metrics.csv", cv_rows)
    write_holdout_predictions(output_dir / "holdout_predictions.csv", holdout_prediction_rows)
    for name, matrix_values in confusion_matrices.items():
        write_confusion_matrix(output_dir / "confusion_matrices" / f"{name}.csv", matrix_values)

    deps["joblib"].dump(best_model, model_dir / "kras_best_model.pkl")
    (model_dir / "feature_columns.json").write_text(
        json.dumps(matrix.feature_columns, indent=2),
        encoding="utf-8",
    )
    comparison = {
        "model_matrix": str(model_matrix_path),
        "row_count": len(matrix.rows),
        "feature_count": len(matrix.feature_columns),
        "class_counts": class_counts(matrix.labels),
        "test_size": test_size,
        "random_state": random_state,
        "selection_metric": selection_metric,
        "cv_folds_requested": cv_folds,
        "cv_folds_used": int(cv_rows[0]["folds"]) if cv_rows else 0,
        "best_model": best_model_name,
        "metrics": metrics_rows,
        "cross_validation": cv_rows,
    }
    (output_dir / "model_comparison.json").write_text(
        json.dumps(comparison, indent=2),
        encoding="utf-8",
    )
    return comparison


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description="Train and evaluate KRAS inhibitor activity models.")
    parser.add_argument("--model-matrix", type=Path, default=root / "data" / "processed" / "kras_model_matrix.csv")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "processed")
    parser.add_argument("--model-dir", type=Path, default=root / "artifacts" / "models")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--selection-metric", default="roc_auc", choices=["roc_auc", "pr_auc", "f1", "recall", "precision", "accuracy"])
    parser.add_argument("--cv-folds", type=int, default=5, help="Number of stratified cross-validation folds to report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        comparison = train_and_evaluate(
            model_matrix_path=args.model_matrix,
            output_dir=args.output_dir,
            model_dir=args.model_dir,
            test_size=args.test_size,
            random_state=args.random_state,
            selection_metric=args.selection_metric,
            cv_folds=args.cv_folds,
        )
    except ModelingDependencyError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps({"best_model": comparison["best_model"], "metrics": comparison["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
