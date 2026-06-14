# KRAS Bioactivity Model Performance Summary

Generated: 2026-06-14

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
- Primary holdout split strategy: `molecule`
- Cross-validation strategy: `molecule`

Feature inputs include RDKit physicochemical descriptors, MACCS keys, and Morgan fingerprints generated from curated ChEMBL KRAS/SOS1 bioactivity records.

## Leakage-Control Audit

| Check | Value |
| --- | --- |
| Split strategy | `molecule` |
| Training rows | `1124` |
| Holdout rows | `274` |
| Training active/inactive | `873/251` |
| Holdout active/inactive | `219/55` |
| Train-test molecule overlap | `0` |
| Train-test scaffold overlap | `82` |

## Holdout Test-Set Performance

The deployed model selected by `roc_auc` was **Random Forest**.

| Model | ACCURACY | BALANCED ACCURACY | PRECISION | RECALL | SPECIFICITY | F1 | MCC | ROC AUC | PR AUC | EF 1 PERCENT | EF 5 PERCENT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Random Forest | 0.916 | 0.907 | 0.971 | 0.922 | 0.891 | 0.946 | 0.762 | 0.980 | 0.995 | 1.251 | 1.251 |
| Xgboost | 0.945 | 0.898 | 0.955 | 0.977 | 0.818 | 0.966 | 0.825 | 0.978 | 0.994 | 1.251 | 1.251 |
| Svm RBF | 0.942 | 0.868 | 0.939 | 0.991 | 0.745 | 0.964 | 0.811 | 0.958 | 0.987 | 1.251 | 1.251 |
| Logistic Regression | 0.938 | 0.900 | 0.959 | 0.963 | 0.836 | 0.961 | 0.805 | 0.953 | 0.986 | 1.251 | 1.251 |
| Decision Tree | 0.927 | 0.886 | 0.954 | 0.954 | 0.818 | 0.954 | 0.773 | 0.871 | 0.947 | 1.251 | 1.251 |
| Naive Bayes | 0.814 | 0.747 | 0.904 | 0.858 | 0.636 | 0.881 | 0.463 | 0.775 | 0.899 | 1.251 | 1.251 |
| Dummy Most Frequent | 0.799 | 0.500 | 0.799 | 1.000 | 0.000 | 0.888 | 0.000 | 0.500 | 0.799 | 1.251 | 1.072 |

## Cross-Validation Performance

Cross-validation was run with `5` folds using `molecule` grouping to assess whether performance was stable across multiple train/test partitions.

| Model | Folds | ROC-AUC | PR-AUC | Accuracy | F1 |
| --- | --- | --- | --- | --- | --- |
| Random Forest | 5 | 0.971 +/- 0.011 | 0.991 +/- 0.004 | 0.928 +/- 0.014 | 0.954 +/- 0.009 |
| Xgboost | 5 | 0.968 +/- 0.009 | 0.990 +/- 0.003 | 0.935 +/- 0.011 | 0.959 +/- 0.007 |
| Svm RBF | 5 | 0.956 +/- 0.016 | 0.986 +/- 0.006 | 0.923 +/- 0.019 | 0.952 +/- 0.011 |
| Logistic Regression | 5 | 0.941 +/- 0.017 | 0.978 +/- 0.005 | 0.925 +/- 0.020 | 0.953 +/- 0.012 |
| Decision Tree | 5 | 0.857 +/- 0.023 | 0.931 +/- 0.009 | 0.898 +/- 0.011 | 0.934 +/- 0.007 |
| Naive Bayes | 5 | 0.798 +/- 0.031 | 0.900 +/- 0.014 | 0.837 +/- 0.021 | 0.894 +/- 0.013 |
| Dummy Most Frequent | 5 | 0.500 +/- 0.000 | 0.781 +/- 0.001 | 0.781 +/- 0.001 | 0.877 +/- 0.001 |

## Scaffold-Split Stress Test

The scaffold split is a stricter analog-series generalization test. Lower performance here is expected and should be interpreted as a more realistic estimate for novel chemotypes.

| Check | Value |
| --- | --- |
| Split strategy | `scaffold` |
| Training rows | `1127` |
| Holdout rows | `271` |
| Training active/inactive | `867/260` |
| Holdout active/inactive | `225/46` |
| Train-test molecule overlap | `0` |
| Train-test scaffold overlap | `0` |

| Model | ACCURACY | BALANCED ACCURACY | PRECISION | RECALL | SPECIFICITY | F1 | MCC | ROC AUC | PR AUC | EF 1 PERCENT | EF 5 PERCENT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Svm RBF | 0.900 | 0.810 | 0.934 | 0.947 | 0.674 | 0.940 | 0.638 | 0.951 | 0.990 | 1.204 | 1.204 |
| Random Forest | 0.875 | 0.855 | 0.961 | 0.884 | 0.826 | 0.921 | 0.628 | 0.938 | 0.986 | 1.204 | 1.204 |
| Xgboost | 0.908 | 0.849 | 0.950 | 0.938 | 0.761 | 0.944 | 0.681 | 0.933 | 0.984 | 1.204 | 1.204 |
| Logistic Regression | 0.908 | 0.858 | 0.955 | 0.933 | 0.783 | 0.944 | 0.688 | 0.929 | 0.981 | 1.204 | 1.204 |
| Decision Tree | 0.893 | 0.840 | 0.950 | 0.920 | 0.761 | 0.935 | 0.644 | 0.858 | 0.946 | 0.803 | 1.032 |
| Naive Bayes | 0.871 | 0.767 | 0.920 | 0.924 | 0.609 | 0.922 | 0.538 | 0.775 | 0.916 | 1.204 | 1.118 |
| Dummy Most Frequent | 0.830 | 0.500 | 0.830 | 1.000 | 0.000 | 0.907 | 0.000 | 0.500 | 0.830 | 0.803 | 0.774 |

## Key Findings

- The deployed **Random Forest** model achieved holdout ROC-AUC `0.980` and PR-AUC `0.995`.
- The strongest cross-validated ROC-AUC was achieved by **Random Forest** with `0.971 +/- 0.011`.
- The deployed **Random Forest** model achieved cross-validated ROC-AUC `0.971 +/- 0.011` and F1-score `0.954 +/- 0.009`.
- The dummy baseline ROC-AUC remained at chance level, supporting that the trained classifiers learned structure-activity signal beyond class imbalance.

## Scientific Interpretation

These metrics support use of the trained KRAS classifier as a computational prioritization model within the agentic screening pipeline. Molecule-grouped and scaffold-split results should be interpreted separately: molecule grouping controls exact duplicate leakage, while scaffold splitting better tests performance on less familiar chemotypes. Neither result proves experimental KRAS inhibition or clinical efficacy.

## Limitations

- ChEMBL assay records can contain heterogeneous assay conditions and target annotations.
- The current model predicts broad KRAS bioactivity rather than definitive mutant-selective binding.
- Scaffold-split performance is the more conservative estimate for novel chemical series and should guide claims about prospective generalization.
- ZINC hits remain computational candidates requiring docking, molecular dynamics, medicinal chemistry review, and experimental validation.
- Future iterations should add external validation sets, calibration analysis, applicability-domain checks, and mutation-specific models where sufficient labels exist.
