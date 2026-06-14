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
            balanced_accuracy_score,
            confusion_matrix,
            f1_score,
            matthews_corrcoef,
            precision_score,
            recall_score,
            roc_auc_score,
        )
        from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, StratifiedKFold, cross_validate, train_test_split
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
        "balanced_accuracy_score": balanced_accuracy_score,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "matthews_corrcoef": matthews_corrcoef,
        "precision_score": precision_score,
        "recall_score": recall_score,
        "roc_auc_score": roc_auc_score,
        "GroupShuffleSplit": GroupShuffleSplit,
        "StratifiedGroupKFold": StratifiedGroupKFold,
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


def import_scaffold_tools() -> Any:
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
    except ImportError as exc:
        raise ModelingDependencyError(
            "Scaffold-aware validation requires RDKit. Install it with `pip install rdkit`."
        ) from exc
    return Chem, MurckoScaffold


def molecule_group_keys(rows: list[dict[str, str]]) -> list[str]:
    return [
        row.get("canonical_smiles") or row.get("molecule_chembl_id") or f"row_{index}"
        for index, row in enumerate(rows)
    ]


def scaffold_group_keys(rows: list[dict[str, str]]) -> list[str]:
    chem, murcko = import_scaffold_tools()
    groups: list[str] = []
    for index, row in enumerate(rows):
        smiles = row.get("canonical_smiles", "")
        mol = chem.MolFromSmiles(smiles)
        if mol is None:
            groups.append(row.get("molecule_chembl_id") or f"invalid_smiles_{index}")
            continue
        scaffold = murcko.MurckoScaffoldSmiles(mol=mol)
        groups.append(scaffold or row.get("molecule_chembl_id") or f"no_scaffold_{index}")
    return groups


def group_keys_for_strategy(rows: list[dict[str, str]], split_strategy: str) -> list[str] | None:
    if split_strategy == "random":
        return None
    if split_strategy == "molecule":
        return molecule_group_keys(rows)
    if split_strategy == "scaffold":
        return scaffold_group_keys(rows)
    raise ValueError(f"Unsupported split strategy: {split_strategy}")


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


def enrichment_factor(y_test: Any, y_score: Any, top_fraction: float, np: Any) -> float:
    labels = np.asarray(y_test, dtype=int)
    scores = np.asarray(y_score, dtype=float)
    if len(labels) == 0:
        return 0.0
    base_rate = float(np.mean(labels))
    if base_rate == 0.0:
        return 0.0
    top_n = max(1, int(np.ceil(len(labels) * top_fraction)))
    ranked_indices = np.argsort(scores)[::-1][:top_n]
    top_hit_rate = float(np.mean(labels[ranked_indices]))
    return top_hit_rate / base_rate


def evaluate_model(name: str, model: Any, x_test: Any, y_test: Any, deps: dict[str, Any]) -> tuple[dict[str, str], list[list[int]], Any, Any]:
    y_pred = model.predict(x_test)
    y_score = positive_scores(model, x_test)
    np = deps["np"]
    matrix = deps["confusion_matrix"](y_test, y_pred, labels=[0, 1]).tolist()
    tn, fp = matrix[0]
    fn, tp = matrix[1]
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0

    metrics = {
        "model": name,
        "accuracy": deps["accuracy_score"](y_test, y_pred),
        "balanced_accuracy": deps["balanced_accuracy_score"](y_test, y_pred),
        "precision": deps["precision_score"](y_test, y_pred, zero_division=0),
        "recall": deps["recall_score"](y_test, y_pred, zero_division=0),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "f1": deps["f1_score"](y_test, y_pred, zero_division=0),
        "mcc": deps["matthews_corrcoef"](y_test, y_pred),
        "roc_auc": deps["roc_auc_score"](y_test, y_score),
        "pr_auc": deps["average_precision_score"](y_test, y_score),
        "ef_1_percent": enrichment_factor(y_test, y_score, 0.01, np),
        "ef_5_percent": enrichment_factor(y_test, y_score, 0.05, np),
    }
    return ({key: f"{value:.6f}" if isinstance(value, float) else value for key, value in metrics.items()}, matrix, y_pred, y_score)


def write_metrics_csv(path: Path, metrics_rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "sensitivity",
        "specificity",
        "f1",
        "mcc",
        "roc_auc",
        "pr_auc",
        "ef_1_percent",
        "ef_5_percent",
    ]
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
        "balanced_accuracy_mean",
        "balanced_accuracy_std",
        "precision_mean",
        "precision_std",
        "recall_mean",
        "recall_std",
        "f1_mean",
        "f1_std",
        "mcc_mean",
        "mcc_std",
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


def split_indices(
    *,
    y: Any,
    deps: dict[str, Any],
    rows: list[dict[str, str]],
    test_size: float,
    random_state: int,
    split_strategy: str,
) -> tuple[Any, Any, list[str] | None]:
    np = deps["np"]
    row_indices = np.arange(len(rows))
    groups = group_keys_for_strategy(rows, split_strategy)
    if groups is None:
        train_indices, test_indices = deps["train_test_split"](
            row_indices,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
        return train_indices, test_indices, None

    splitter = deps["GroupShuffleSplit"](n_splits=50, test_size=test_size, random_state=random_state)
    last_split: tuple[Any, Any] | None = None
    for train_indices, test_indices in splitter.split(row_indices, y, groups):
        last_split = (train_indices, test_indices)
        train_labels = set(int(value) for value in y[train_indices])
        test_labels = set(int(value) for value in y[test_indices])
        if train_labels == {0, 1} and test_labels == {0, 1}:
            return train_indices, test_indices, groups
    if last_split is None:
        raise ValueError(f"Could not create a grouped split for strategy: {split_strategy}")
    return last_split[0], last_split[1], groups


def overlap_count(values: list[str], train_indices: Any, test_indices: Any) -> int:
    train_values = {values[int(index)] for index in train_indices}
    test_values = {values[int(index)] for index in test_indices}
    return len(train_values & test_values)


def split_summary(
    *,
    rows: list[dict[str, str]],
    y: Any,
    train_indices: Any,
    test_indices: Any,
    split_strategy: str,
) -> dict[str, Any]:
    train_labels = [int(y[int(index)]) for index in train_indices]
    test_labels = [int(y[int(index)]) for index in test_indices]
    molecule_groups = molecule_group_keys(rows)
    try:
        scaffold_groups = scaffold_group_keys(rows)
    except ModelingDependencyError:
        scaffold_groups = []
    summary = {
        "split_strategy": split_strategy,
        "train_rows": len(train_indices),
        "test_rows": len(test_indices),
        "train_class_counts": class_counts(train_labels),
        "test_class_counts": class_counts(test_labels),
        "train_test_molecule_overlap": overlap_count(molecule_groups, train_indices, test_indices),
    }
    if scaffold_groups:
        summary["train_test_scaffold_overlap"] = overlap_count(scaffold_groups, train_indices, test_indices)
    return summary


def metric_value(row: dict[str, str], metric: str) -> float:
    return float(row[metric])


def effective_cv_folds(labels: list[int], requested_folds: int) -> int:
    counts = class_counts(labels)
    smallest_class = min(counts.values())
    return min(requested_folds, smallest_class) if smallest_class >= 2 and requested_folds >= 2 else 0


def summarize_cv_scores(name: str, scores: dict[str, Any], folds: int, np: Any) -> dict[str, str]:
    metric_map = {
        "accuracy": "test_accuracy",
        "balanced_accuracy": "test_balanced_accuracy",
        "precision": "test_precision",
        "recall": "test_recall",
        "f1": "test_f1",
        "mcc": "test_mcc",
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
    groups: list[str] | None = None,
) -> list[dict[str, str]]:
    effective_folds = effective_cv_folds([int(value) for value in y], cv_folds)
    if effective_folds == 0:
        return []

    cv = (
        deps["StratifiedGroupKFold"](n_splits=effective_folds, shuffle=True, random_state=random_state)
        if groups is not None
        else deps["StratifiedKFold"](n_splits=effective_folds, shuffle=True, random_state=random_state)
    )
    scoring = {
        "accuracy": "accuracy",
        "balanced_accuracy": "balanced_accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "mcc": "matthews_corrcoef",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    rows: list[dict[str, str]] = []
    for name, model in build_models(deps, random_state).items():
        scores = deps["cross_validate"](
            model,
            x,
            y,
            groups=groups,
            cv=cv,
            scoring=scoring,
            error_score="raise",
        )
        rows.append(summarize_cv_scores(name, scores, effective_folds, deps["np"]))
    rows.sort(key=lambda row: float(row["roc_auc_mean"]), reverse=True)
    return rows


def fit_and_evaluate_models(
    *,
    x: Any,
    y: Any,
    rows: list[dict[str, str]],
    train_indices: Any,
    test_indices: Any,
    deps: dict[str, Any],
    random_state: int,
    selection_metric: str,
) -> tuple[list[dict[str, str]], dict[str, list[list[int]]], dict[str, Any], list[dict[str, str]]]:
    metrics_rows: list[dict[str, str]] = []
    confusion_matrices: dict[str, list[list[int]]] = {}
    fitted_models: dict[str, Any] = {}
    holdout_prediction_rows: list[dict[str, str]] = []
    x_train = x[train_indices]
    x_test = x[test_indices]
    y_train = y[train_indices]
    y_test = y[test_indices]

    for name, model in build_models(deps, random_state).items():
        model.fit(x_train, y_train)
        metrics, matrix_values, y_pred, y_score = evaluate_model(name, model, x_test, y_test, deps)
        metrics_rows.append(metrics)
        confusion_matrices[name] = matrix_values
        fitted_models[name] = model
        holdout_prediction_rows.extend(
            build_holdout_prediction_rows(
                model_name=name,
                source_rows=rows,
                holdout_indices=test_indices,
                y_test=y_test,
                y_pred=y_pred,
                y_score=y_score,
            )
        )

    metrics_rows.sort(key=lambda row: metric_value(row, selection_metric), reverse=True)
    return metrics_rows, confusion_matrices, fitted_models, holdout_prediction_rows


def train_and_evaluate(
    *,
    model_matrix_path: Path,
    output_dir: Path,
    model_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
    selection_metric: str = "roc_auc",
    cv_folds: int = 5,
    split_strategy: str = "molecule",
    cv_strategy: str = "molecule",
    run_scaffold_evaluation: bool = True,
) -> dict[str, Any]:
    deps = import_modeling_dependencies()
    matrix = read_model_matrix(model_matrix_path)
    np = deps["np"]
    x = numeric_matrix(matrix.rows, matrix.feature_columns, np)
    y = np.asarray(matrix.labels, dtype=int)
    cv_groups = group_keys_for_strategy(matrix.rows, cv_strategy)
    cv_rows = cross_validate_models(
        x=x,
        y=y,
        deps=deps,
        cv_folds=cv_folds,
        random_state=random_state,
        groups=cv_groups,
    )

    train_indices, test_indices, _ = split_indices(
        y=y,
        deps=deps,
        rows=matrix.rows,
        test_size=test_size,
        random_state=random_state,
        split_strategy=split_strategy,
    )
    split_audit = split_summary(
        rows=matrix.rows,
        y=y,
        train_indices=train_indices,
        test_indices=test_indices,
        split_strategy=split_strategy,
    )
    metrics_rows, confusion_matrices, fitted_models, holdout_prediction_rows = fit_and_evaluate_models(
        x=x,
        y=y,
        rows=matrix.rows,
        train_indices=train_indices,
        test_indices=test_indices,
        deps=deps,
        random_state=random_state,
        selection_metric=selection_metric,
    )
    best_model_name = metrics_rows[0]["model"]
    best_model = fitted_models[best_model_name]

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    write_metrics_csv(output_dir / "model_metrics.csv", metrics_rows)
    write_cross_validation_csv(output_dir / "cross_validation_metrics.csv", cv_rows)
    write_holdout_predictions(output_dir / "holdout_predictions.csv", holdout_prediction_rows)
    for name, matrix_values in confusion_matrices.items():
        write_confusion_matrix(output_dir / "confusion_matrices" / f"{name}.csv", matrix_values)

    scaffold_evaluation: dict[str, Any] | None = None
    if run_scaffold_evaluation and split_strategy != "scaffold":
        scaffold_train_indices, scaffold_test_indices, _ = split_indices(
            y=y,
            deps=deps,
            rows=matrix.rows,
            test_size=test_size,
            random_state=random_state,
            split_strategy="scaffold",
        )
        scaffold_metrics, scaffold_matrices, _, scaffold_predictions = fit_and_evaluate_models(
            x=x,
            y=y,
            rows=matrix.rows,
            train_indices=scaffold_train_indices,
            test_indices=scaffold_test_indices,
            deps=deps,
            random_state=random_state,
            selection_metric=selection_metric,
        )
        write_metrics_csv(output_dir / "scaffold_split_metrics.csv", scaffold_metrics)
        write_holdout_predictions(output_dir / "scaffold_split_holdout_predictions.csv", scaffold_predictions)
        for name, matrix_values in scaffold_matrices.items():
            write_confusion_matrix(output_dir / "scaffold_split_confusion_matrices" / f"{name}.csv", matrix_values)
        scaffold_evaluation = {
            "split": split_summary(
                rows=matrix.rows,
                y=y,
                train_indices=scaffold_train_indices,
                test_indices=scaffold_test_indices,
                split_strategy="scaffold",
            ),
            "metrics": scaffold_metrics,
            "best_model": scaffold_metrics[0]["model"] if scaffold_metrics else "",
        }

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
        "split_strategy": split_strategy,
        "split_audit": split_audit,
        "selection_metric": selection_metric,
        "cv_strategy": cv_strategy,
        "cv_folds_requested": cv_folds,
        "cv_folds_used": int(cv_rows[0]["folds"]) if cv_rows else 0,
        "best_model": best_model_name,
        "metrics": metrics_rows,
        "cross_validation": cv_rows,
        "scaffold_evaluation": scaffold_evaluation,
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
    parser.add_argument(
        "--selection-metric",
        default="roc_auc",
        choices=["roc_auc", "pr_auc", "f1", "recall", "precision", "accuracy", "balanced_accuracy", "mcc"],
    )
    parser.add_argument("--cv-folds", type=int, default=5, help="Number of stratified cross-validation folds to report.")
    parser.add_argument(
        "--split-strategy",
        default="molecule",
        choices=["random", "molecule", "scaffold"],
        help="Holdout split strategy. Use molecule or scaffold to prevent grouped leakage.",
    )
    parser.add_argument(
        "--cv-strategy",
        default="molecule",
        choices=["random", "molecule", "scaffold"],
        help="Cross-validation grouping strategy.",
    )
    parser.add_argument(
        "--skip-scaffold-evaluation",
        action="store_true",
        help="Skip the additional scaffold-split stress-test outputs.",
    )
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
            split_strategy=args.split_strategy,
            cv_strategy=args.cv_strategy,
            run_scaffold_evaluation=not args.skip_scaffold_evaluation,
        )
    except ModelingDependencyError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps({"best_model": comparison["best_model"], "metrics": comparison["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
