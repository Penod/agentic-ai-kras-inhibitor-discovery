# KRAS Bioactivity Model Performance Summary

Generated: 2026-06-09

## Objective

Document the supervised machine-learning performance of the KRAS bioactivity classifier used by the agentic screening workflow.

## Dataset

- Model matrix: `C:\Users\emman\OneDrive\Desktop\Portfolio_Git\Agentic AI Drug Discovery Platform\kras-mutant-inhibitor-discovery\data\processed\kras_model_matrix.csv`
- Compounds/rows: `1398`
- Numeric molecular features: `2226`
- Active compounds: `1092`
- Inactive compounds: `306`
- Holdout test size: `0.2`
- Random state: `42`

Feature inputs include RDKit physicochemical descriptors, MACCS keys, and Morgan fingerprints generated from curated ChEMBL KRAS/SOS1 bioactivity records.

## Holdout Test-Set Performance

The deployed model selected by `roc_auc` was **Xgboost**.

| Model | ACCURACY | PRECISION | RECALL | F1 | ROC AUC | PR AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Xgboost | 0.943 | 0.951 | 0.977 | 0.964 | 0.984 | 0.996 |
| Random Forest | 0.929 | 0.963 | 0.945 | 0.954 | 0.981 | 0.995 |
| Svm RBF | 0.921 | 0.946 | 0.954 | 0.950 | 0.966 | 0.990 |
| Logistic Regression | 0.943 | 0.963 | 0.963 | 0.963 | 0.962 | 0.987 |
| Decision Tree | 0.932 | 0.963 | 0.950 | 0.956 | 0.911 | 0.955 |
| Naive Bayes | 0.864 | 0.921 | 0.904 | 0.912 | 0.827 | 0.914 |
| Dummy Most Frequent | 0.782 | 0.782 | 1.000 | 0.878 | 0.500 | 0.782 |

## Cross-Validation Performance

Stratified cross-validation was run with `5` folds to assess whether performance was stable across multiple train/test partitions.

| Model | Folds | ROC-AUC | PR-AUC | Accuracy | F1 |
| --- | --- | --- | --- | --- | --- |
| Random Forest | 5 | 0.970 +/- 0.011 | 0.991 +/- 0.003 | 0.925 +/- 0.016 | 0.952 +/- 0.010 |
| Xgboost | 5 | 0.968 +/- 0.008 | 0.990 +/- 0.002 | 0.933 +/- 0.017 | 0.958 +/- 0.011 |
| Svm RBF | 5 | 0.952 +/- 0.014 | 0.985 +/- 0.005 | 0.928 +/- 0.021 | 0.955 +/- 0.012 |
| Logistic Regression | 5 | 0.942 +/- 0.026 | 0.976 +/- 0.015 | 0.926 +/- 0.015 | 0.953 +/- 0.009 |
| Decision Tree | 5 | 0.873 +/- 0.022 | 0.937 +/- 0.013 | 0.910 +/- 0.015 | 0.942 +/- 0.010 |
| Naive Bayes | 5 | 0.796 +/- 0.025 | 0.899 +/- 0.011 | 0.834 +/- 0.021 | 0.892 +/- 0.015 |
| Dummy Most Frequent | 5 | 0.500 +/- 0.000 | 0.781 +/- 0.001 | 0.781 +/- 0.001 | 0.877 +/- 0.001 |

## Key Findings

- The deployed **Xgboost** model achieved holdout ROC-AUC `0.984` and PR-AUC `0.996`.
- The strongest cross-validated ROC-AUC was achieved by **Random Forest** with `0.970 +/- 0.011`.
- The deployed **Xgboost** model achieved cross-validated ROC-AUC `0.968 +/- 0.008` and F1-score `0.958 +/- 0.011`.
- The dummy baseline ROC-AUC remained at chance level, supporting that the trained classifiers learned structure-activity signal beyond class imbalance.

## Scientific Interpretation

These metrics support use of the trained KRAS classifier as a computational prioritization model within the agentic screening pipeline. They should be interpreted as internal and cross-validated performance on the curated dataset, not as proof of experimental KRAS inhibition or clinical efficacy.

## Limitations

- ChEMBL assay records can contain heterogeneous assay conditions and target annotations.
- The current model predicts broad KRAS bioactivity rather than definitive mutant-selective binding.
- ZINC hits remain computational candidates requiring docking, molecular dynamics, medicinal chemistry review, and experimental validation.
- Future iterations should add external validation sets, calibration analysis, applicability-domain checks, and mutation-specific models where sufficient labels exist.
