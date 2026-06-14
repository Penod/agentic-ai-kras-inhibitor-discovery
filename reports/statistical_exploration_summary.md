# Statistical Exploration and Model Evidence Summary

This report collects reproducible figures generated from saved project outputs. It is intended to support scientific review by showing how compounds moved through curation, feature engineering, model evaluation, and ZINC22 hit triage.

## Source Files

- `data/processed/kras_curation_summary.json`
- `data/processed/kras_model_matrix.csv`
- `data/processed/kras_druglikeness_summary.json`
- `data/processed/model_metrics.csv`
- `data/processed/holdout_predictions.csv`
- `data/processed/cross_validation_metrics.csv`
- `data/processed/confusion_matrices/*.csv`
- `data/processed/interpretation/feature_importance.csv`
- `data/processed/batch_screening/ranked_screening_results.csv`
- `data/processed/batch_screening/hit_triage/hit_triage_summary.json`

## Key Counts

- ChEMBL raw records curated: `17,063`
- Labeled active/inactive training records: `1,398`
- Active training records: `1,092`
- Inactive training records: `306`
- Project drug-like records: `817`
- ZINC22 compounds screened: `5,000`
- ZINC22 candidates passing hit-triage criteria: `4`

## Model Evidence

The best holdout model in the saved comparison is `xgboost` with ROC-AUC `0.984`, PR-AUC `0.996`, F1 `0.964`, and recall `0.977`.
Five-fold cross-validation for XGBoost produced mean ROC-AUC `0.968` with standard deviation `0.008`.

## Generated Figures

### Activity-class balance

![Activity-class balance](figures/activity_class_balance.svg)

### ChEMBL curation funnel

![ChEMBL curation funnel](figures/curation_funnel.svg)

### Target and mutation distribution

![Target and mutation distribution](figures/variant_distribution.svg)

### Drug-likeness filter summary

![Drug-likeness filter summary](figures/druglikeness_filter_summary.svg)

### Molecular property distributions

![Molecular property distributions](figures/molecular_property_distributions.svg)

### Lipinski violation counts

![Lipinski violation counts](figures/lipinski_violation_counts.svg)

### Holdout model metric comparison

![Holdout model metric comparison](figures/model_metric_comparison.svg)

### Cross-validation ROC-AUC comparison

![Cross-validation ROC-AUC comparison](figures/cross_validation_roc_auc.svg)

### Holdout ROC curves

![Holdout ROC curves](figures/holdout_roc_curves.svg)

### Holdout precision-recall curves

![Holdout precision-recall curves](figures/holdout_precision_recall_curves.svg)

### Holdout confusion matrices

![Holdout confusion matrices](figures/confusion_matrices.svg)

### Top model feature importance

![Top model feature importance](figures/top_feature_importance.svg)

### ZINC22 hit triage funnel

![ZINC22 hit triage funnel](figures/zinc22_hit_triage_funnel.svg)

### ZINC22 probability versus ADMET

![ZINC22 probability versus ADMET](figures/zinc22_probability_vs_admet.svg)

### ZINC22 recommendation distribution

![ZINC22 recommendation distribution](figures/zinc22_recommendation_distribution.svg)

## Notes and Limitations

- These figures are generated from saved project artifacts, not from a fresh ChEMBL or ZINC22 download.
- ROC and precision-recall curves are generated when `data/processed/holdout_predictions.csv` is available. Rerun model training first if that file is missing.
- The ZINC22 hit triage results are computational predictions and should be treated as prioritization evidence for docking, molecular dynamics, medicinal chemistry review, and experimental validation.

## Reproduce

```bash
python -m kras_discovery.visualization.static_plots
```
