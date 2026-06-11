# Technical Design

## Objective

Build an agentic AI platform for KRAS mutant-selective inhibitor discovery, with a first emphasis on KRAS G12C, KRAS G12D, KRAS G12V, and SOS1 pathway modulation.

## Current Prototype

The current version provides a runnable scaffold for candidate evaluation while preserving clean extension points for real KRAS bioactivity models, PubMed retrieval, docking, molecular dynamics, and AWS deployment.

After model training, `KRASTargetFitAgent` attempts to load `artifacts/models/kras_best_model.pkl` and `artifacts/models/feature_columns.json`. If model artifacts and RDKit dependencies are available, it generates a single-row RDKit feature vector for the submitted SMILES string and returns a trained-model probability. If dependencies or artifacts are missing, it falls back to the transparent heuristic target-fit score.

## Agent Responsibilities

- Validation Agent: checks SMILES plausibility and drug-likeness constraints.
- Feature Agent: extracts approximate descriptors from SMILES strings.
- KRAS Target-Fit Agent: estimates KRAS pathway activity using the trained model when available, with heuristic fallback.
- Mutant Selectivity Agent: produces a hypothesis across G12C, G12D, G12V, and SOS1.
- ADMET Agent: estimates absorption, distribution, metabolism, and excretion suitability.
- Toxicity Agent: flags simple structural alerts.
- Literature Agent: records target-specific evidence readiness for KRAS research.
- Manufacturability Agent: estimates synthesis feasibility.
- Clinical Relevance Agent: maps candidate relevance to pancreatic cancer and lung adenocarcinoma.
- Ranking Agent: combines all evidence into a final prioritization score.

## Future Model Workflow

1. Curate assay records for KRAS G12C, G12D, G12V, and SOS1.
2. Standardize activities and label active/inactive compounds.
3. Generate RDKit fingerprints and descriptors.
4. Train target-specific classifiers and regressors.
5. Evaluate ROC-AUC, PR-AUC, precision, recall, F1, calibration, and uncertainty.
6. Add explainability outputs for human scientific review.
7. Promote saved models into agent runtime.

## ChEMBL Curation Outputs

The ChEMBL curation pipeline writes four artifacts:

- `data/processed/kras_chembl_raw_activities.csv`: selected raw ChEMBL fields for auditability.
- `data/processed/kras_chembl_curated_activities.csv`: target labels, mutation/node inference, activity labels, and curation notes.
- `data/processed/kras_training_set.csv`: deduplicated active/inactive rows for model training.
- `data/processed/kras_curation_summary.json`: record counts and class balance.

Current target IDs:

- KRAS: `CHEMBL2189121`
- SOS1: `CHEMBL4523334`

Default class rules:

- Active: `pchembl_value >= 7.0`
- Inactive: `pchembl_value <= 5.0`
- Ambiguous records are retained in the curated audit file but excluded from the training set.

## RDKit Feature Engineering Outputs

The RDKit feature pipeline reads `data/processed/kras_training_set.csv` and writes:

- `data/processed/kras_features_descriptors.csv`: compact physicochemical descriptor matrix.
- `data/processed/kras_features_maccs.csv`: 166-bit MACCS key matrix aligned with the thesis-style workflow.
- `data/processed/kras_features_morgan.csv`: 2048-bit Morgan fingerprint matrix.
- `data/processed/kras_model_matrix.csv`: combined descriptors, MACCS keys, Morgan fingerprints, metadata, and binary labels.
- `data/processed/kras_feature_summary.json`: feature counts and invalid-SMILES counts.

The model matrix contains `activity_label`, where active compounds are encoded as `1` and inactive compounds are encoded as `0`.

## Drug-Likeness and Assay-Quality Controls

The quality pipeline writes:

- `data/processed/kras_model_matrix_druglikeness_report.csv`
- `data/processed/kras_model_matrix_druglike_subset.csv`
- `data/processed/kras_druglikeness_summary.json`
- `data/processed/kras_assay_quality_report.csv`
- `data/processed/kras_assay_quality_subset.csv`
- `data/processed/kras_assay_quality_summary.json`

Drug-likeness checks are intentionally used as flags and subset definitions rather than hard deletion rules. This is important for KRAS G12C because covalent inhibitor design can include electrophilic or higher-complexity chemistry that should be reviewed rather than automatically discarded.

Assay-quality checks flag non-human targets, non-binding assay types, non-priority activity measurements, ChEMBL validity comments, missing SMILES, and records that do not have clean active/inactive labels.

## Model Training Outputs

The model training pipeline reads `data/processed/kras_model_matrix.csv` and writes:

- `data/processed/model_metrics.csv`: accuracy, precision, recall, F1, ROC-AUC, and PR-AUC for each model.
- `data/processed/model_comparison.json`: dataset summary, class counts, model metrics, and selected best model.
- `data/processed/confusion_matrices/`: one CSV confusion matrix per trained model.
- `artifacts/models/kras_best_model.pkl`: serialized best model selected by ROC-AUC by default.
- `artifacts/models/feature_columns.json`: ordered feature list required for future inference.

The first model suite compares a dummy baseline, Logistic Regression, Random Forest, Decision Tree, Naive Bayes, SVM, and XGBoost when the optional dependency is installed.

## Model Interpretation Outputs

The interpretation pipeline reads a saved model and `feature_columns.json`, then writes:

- `feature_importance.csv`: ranked feature importances with feature group labels.
- `feature_importance_summary.json`: top features and aggregate importance by feature group.

Supported model families include estimators exposing `feature_importances_` or `coef_`. This covers XGBoost, Random Forest, Decision Tree, and Logistic Regression. For future scientific reporting, MACCS and Morgan bit importances should be mapped back to structural motifs where possible.

## SHAP and Report Outputs

Optional SHAP interpretation writes:

- `data/processed/interpretation/shap/shap_global_importance.csv`
- `data/processed/interpretation/shap/shap_summary.json`
- `data/processed/druglike_modeling/interpretation/shap/shap_global_importance.csv`
- `data/processed/druglike_modeling/interpretation/shap/shap_summary.json`

The written interpretation report is generated at `reports/model_interpretation_report.md`. It summarizes dataset context, full-vs-drug-like model performance, built-in feature importance, optional SHAP outputs, scientific interpretation, limitations, and next steps.

## Future Validation Workflow

- Dock top candidates against relevant KRAS mutant structures.
- Run short molecular dynamics simulations for binding stability.
- Compare binding hypotheses across mutant-selective pockets.
- Store results in auditable candidate evidence records.
