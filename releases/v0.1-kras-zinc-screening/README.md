# v0.1 KRAS ZINC Screening Reproducibility Snapshot

This snapshot preserves the core generated artifacts for the KRAS mutant-selective inhibitor discovery workflow.

## Purpose

The snapshot is intended to support reproducible review of the project evidence without requiring a reviewer to rerun live ChEMBL curation, RDKit feature engineering, model training, or ZINC screening.

## Contents

```text
data/
  kras_curation_summary.json
  kras_feature_summary.json
  kras_druglikeness_summary.json
  kras_assay_quality_summary.json
  model_metrics.csv
  cross_validation_metrics.csv
  model_comparison.json
  top_hit_candidates.csv
  hit_triage_summary.json

artifacts/models/
  kras_best_model.pkl
  feature_columns.json

reports/
  model_performance_summary.md
  model_interpretation_report.md
  zinc_hit_triage_report.md
  zinc_hit_triage_report.pdf

manifest.json
```

## Key Methodology

- KRAS/SOS1 bioactivity records were curated from ChEMBL.
- RDKit descriptors, MACCS keys, and Morgan fingerprints were generated.
- Multiple classifiers were compared, including XGBoost, Random Forest, SVM, Logistic Regression, Decision Tree, Naive Bayes, and a dummy baseline.
- Model performance was evaluated using holdout testing and 5-fold stratified cross-validation.
- A sampled ZINC lead-like screening library was scored through the trained model and agentic triage workflow.
- Computational hit candidates were filtered using trained-model KRAS probability, ADMET score, toxicity label, and agent recommendation.

## Validation Boundary

The compounds in `top_hit_candidates.csv` are computational hit candidates only. They are not experimentally confirmed KRAS inhibitors, clinical candidates, or therapeutic recommendations. Further validation is required through docking, molecular dynamics, medicinal chemistry review, and biochemical or cell-based assays.

## Reproducibility Note

The live ChEMBL API may change over time as new records are added or corrected. This snapshot preserves the exact generated evidence from this project run so that model metrics, screening results, reports, and model artifacts remain inspectable even if the live source database later changes.
