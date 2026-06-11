from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kras_discovery.feature_engineering.rdkit_features import (
    RDKitUnavailableError,
    descriptor_row,
    import_rdkit,
    maccs_row,
    morgan_row,
)


class ModelInferenceUnavailableError(RuntimeError):
    """Raised when trained-model inference cannot run."""


@dataclass(frozen=True)
class ModelPrediction:
    probability_active: float
    predicted_label: int
    model_path: str
    feature_count: int
    inference_mode: str = "trained_model"


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def import_joblib() -> Any:
    try:
        import joblib
    except ImportError as exc:
        raise ModelInferenceUnavailableError("joblib is required for trained-model inference. Install it with `pip install joblib`.") from exc
    return joblib


def default_model_paths() -> tuple[Path, Path]:
    root = project_root()
    return (
        root / "artifacts" / "models" / "kras_best_model.pkl",
        root / "artifacts" / "models" / "feature_columns.json",
    )


def load_feature_columns(path: Path) -> list[str]:
    if not path.exists():
        raise ModelInferenceUnavailableError(f"Feature columns file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_smiles_feature_row(smiles: str) -> dict[str, str]:
    rdkit = import_rdkit()
    mol = rdkit["Chem"].MolFromSmiles(smiles)
    if mol is None:
        raise ModelInferenceUnavailableError(f"RDKit could not parse SMILES: {smiles}")
    return {
        **descriptor_row(mol, rdkit),
        **maccs_row(mol, rdkit),
        **morgan_row(mol, rdkit),
    }


def feature_vector_from_row(row: dict[str, str], feature_columns: list[str]) -> list[list[float]]:
    return [[float(row.get(column) or 0.0) for column in feature_columns]]


def probability_active(model: Any, vector: list[list[float]]) -> float:
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(vector)[0][1])
    if hasattr(model, "decision_function"):
        score = float(model.decision_function(vector)[0])
        return 1.0 / (1.0 + pow(2.718281828459045, -score))
    prediction = int(model.predict(vector)[0])
    return float(prediction)


def predict_smiles_activity(
    smiles: str,
    *,
    model_path: Path | None = None,
    feature_columns_path: Path | None = None,
) -> ModelPrediction:
    default_model, default_features = default_model_paths()
    selected_model_path = model_path or default_model
    selected_feature_columns_path = feature_columns_path or default_features

    if not selected_model_path.exists():
        raise ModelInferenceUnavailableError(f"Model file not found: {selected_model_path}")

    try:
        feature_row = build_smiles_feature_row(smiles)
    except RDKitUnavailableError as exc:
        raise ModelInferenceUnavailableError(str(exc)) from exc

    feature_columns = load_feature_columns(selected_feature_columns_path)
    vector = feature_vector_from_row(feature_row, feature_columns)
    model = import_joblib().load(selected_model_path)
    probability = probability_active(model, vector)
    return ModelPrediction(
        probability_active=probability,
        predicted_label=int(probability >= 0.5),
        model_path=str(selected_model_path),
        feature_count=len(feature_columns),
    )
