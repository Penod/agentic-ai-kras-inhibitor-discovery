# Agentic AI KRAS Inhibitor Discovery

This repository is an end-to-end computational drug discovery workflow for prioritizing KRAS-pathway inhibitor candidates from public bioactivity and chemical-library data.

I built it to answer a practical engineering question:

> Can a reproducible Python pipeline combine ChEMBL curation, RDKit molecular features, supervised learning, agentic screening, and ZINC22 hit triage into a workflow that is understandable enough for scientific review?

The current system is not a clinical tool and does not claim to discover confirmed KRAS drugs. It produces computational hit candidates that require docking, molecular dynamics, medicinal chemistry review, and experimental validation.

## Problem

KRAS is a major cancer driver, especially in pancreatic cancer, lung adenocarcinoma, and colorectal cancer. Direct KRAS inhibition was historically difficult, and although KRAS G12C inhibitors changed the field, many KRAS-driven cancers still lack broadly effective targeted options.

For this project, I focused on the early computational screening problem: assembling public bioactivity data, training a KRAS bioactivity classifier, and using that model inside a transparent screening workflow.

## Target Scope

The project is organized around the KRAS pathway:

| Target or node | Role in this project |
| --- | --- |
| KRAS G12C | Clinically validated direct-inhibition starting point |
| KRAS G12D | High-priority pancreatic cancer mutation |
| KRAS G12V | Common KRAS mutation with limited direct-inhibitor options |
| SOS1 | Pathway-relevant exchange factor for future expansion |

Important limitation: the current trained model should be described as a KRAS bioactivity classifier. SOS1 is included in the curation and pathway framing, but the current labeled training set is dominated by KRAS records and does not support a standalone SOS1 predictor yet.

## Design Goals

I made a few deliberate design choices:

- Use public data sources so the workflow can be inspected and rerun.
- Keep each pipeline stage callable from the command line.
- Prefer standard cheminformatics features before adding deep learning.
- Compare several baseline models instead of reporting one model in isolation.
- Preserve model outputs, reports, and release snapshots for reproducibility.
- Keep agent outputs explainable enough for human scientific review.

I avoided building a web app first because the core risk was not UI. The core risk was whether the data, labels, features, models, and screening outputs were scientifically coherent.

## Architecture

The repository is organized as a Python package:

```text
src/kras_discovery/
  data_curation/       ChEMBL retrieval, cleaning, activity labeling
  feature_engineering/ RDKit descriptors, MACCS keys, Morgan fingerprints
  quality/             Drug-likeness and assay-quality reports
  modeling/            Model training, cross-validation, performance reports
  inference/           Saved-model loading and SMILES-level prediction
  agents/              Multi-agent candidate evaluation workflow
  screening/           Batch screening, ZINC22 preparation, hit triage
  interpretation/      Feature importance, optional SHAP, interpretation report
  validation/          Known KRAS inhibitor positive-control screening
  reports/             Markdown-to-PDF report utility
```

The main workflow is:

```text
ChEMBL activities
  -> curated training set
  -> RDKit feature matrix
  -> model training and cross-validation
  -> saved model artifact
  -> agentic screening pipeline
  -> ZINC22 batch screen
  -> hit triage report
  -> release snapshot
```

## Data Sources

Training data is retrieved from ChEMBL:

| Source | Identifier |
| --- | --- |
| KRAS | `CHEMBL2189121` |
| SOS1 | `CHEMBL4523334` |

The curation step calls the live ChEMBL API. This keeps the pipeline current, but it also means exact row counts can change as ChEMBL updates records. For archival reproducibility, the repository includes release snapshots that preserve the generated metrics, reports, and selected artifacts from a specific run.

Candidate screening used sampled lead-like compounds from ZINC22, accessed through the CartBlanche/ZINC22 tranche interface.

## Labeling Strategy

I used pChEMBL thresholds to create a first binary classification task:

| Class | Rule |
| --- | --- |
| Active | `pchembl_value >= 7.0` |
| Inactive | `pchembl_value <= 5.0` |
| Ambiguous | `5.0 < pchembl_value < 7.0` |
| Unlabeled | missing pChEMBL |

Only clear active/inactive records are used for the first training set. Ambiguous records remain in curated audit files but are excluded from model training.

This is a pragmatic choice. It reduces label noise but also narrows the training set. A future version should explore regression on continuous pChEMBL values, assay-aware modeling, and uncertainty estimates.

## Molecular Representation

SMILES strings are converted into numerical features using RDKit:

- Physicochemical descriptors: molecular weight, LogP, TPSA, hydrogen-bond counts, ring counts, fraction CSP3, and related descriptors.
- MACCS keys: 166 structural keys.
- Morgan fingerprints: 2048-bit circular fingerprints.

The current model matrix contains:

```text
1,398 compounds
2,226 numeric molecular features
```

I chose these features because they are standard, reproducible, and easy to inspect. A graph neural network may be useful later, but descriptor/fingerprint baselines are a better first step for a limited labeled dataset.

## Model Development

The training pipeline compares:

- Dummy baseline
- Logistic Regression
- Random Forest
- Decision Tree
- Naive Bayes
- SVM with RBF kernel
- XGBoost

I selected XGBoost as the deployed model because it performed best on the holdout ROC-AUC metric and is well suited to heterogeneous descriptor/fingerprint feature spaces. Random Forest performed slightly better in cross-validated ROC-AUC, so both models remain important references in the performance report.

The training pipeline writes:

```text
data/processed/model_metrics.csv
data/processed/cross_validation_metrics.csv
data/processed/model_comparison.json
data/processed/confusion_matrices/
artifacts/models/kras_best_model.pkl
artifacts/models/feature_columns.json
```

## Performance Summary

Holdout test-set results for the deployed XGBoost model:

| Metric | Value |
| --- | --- |
| Accuracy | 0.9429 |
| Precision | 0.9511 |
| Recall | 0.9772 |
| F1 | 0.9640 |
| ROC-AUC | 0.9845 |
| PR-AUC | 0.9957 |

Five-fold stratified cross-validation:

| Model | ROC-AUC | PR-AUC | Accuracy | F1 |
| --- | --- | --- | --- | --- |
| Random Forest | 0.970 +/- 0.011 | 0.991 +/- 0.003 | 0.925 +/- 0.016 | 0.952 +/- 0.010 |
| XGBoost | 0.968 +/- 0.008 | 0.990 +/- 0.002 | 0.933 +/- 0.017 | 0.958 +/- 0.011 |
| Dummy baseline | 0.500 +/- 0.000 | 0.781 +/- 0.001 | 0.781 +/- 0.001 | 0.877 +/- 0.001 |

These metrics support using the classifier for computational prioritization. They do not prove experimental KRAS inhibition.

## Agentic Screening Workflow

The agentic layer evaluates each candidate through small, focused components:

| Agent | Purpose |
| --- | --- |
| Validation | Basic SMILES and property checks |
| Feature | Lightweight approximate descriptors for agent context |
| KRAS target fit | Trained-model inference when model artifacts are available |
| Mutant selectivity | Heuristic hypothesis across KRAS mutations and SOS1 |
| ADMET | Rule-based suitability proxy |
| Toxicity | Simple structural-alert proxy |
| Literature | Offline evidence-readiness placeholder |
| Manufacturability | Synthetic-feasibility proxy |
| Clinical relevance | Aggregates target fit, selectivity, ADMET, and toxicity |

The trained model is loaded by `KRASTargetFitAgent`. If RDKit, joblib, or model artifacts are missing, the agent falls back to a transparent heuristic instead of failing the entire CLI. This makes the demo runnable in limited environments, but trained-model results should always be preferred for real screening.

## ZINC22 Screening and Hit Triage

I used a sampled ZINC22 lead-like tranche for a pilot virtual screen.

The ZINC `.smi` file is converted into CSV format:

```bash
python -m kras_discovery.screening.zinc_prepare \
  --input data/external/zinc_raw/EC/ECAA.smi \
  --output data/external/zinc_screening_library.csv \
  --limit 5000
```

Then the batch screener runs:

```bash
python -m kras_discovery.screening.batch_screen \
  --input data/external/zinc_screening_library.csv
```

Hit selection is reproducible:

```text
inference_mode = trained_model
kras_probability_active >= 0.70
admet_score >= 0.60
toxicity_label = Low risk
recommendation = Advance or Advance with review
```

The resulting candidates are documented in:

```text
reports/zinc_hit_triage_report.md
reports/zinc_hit_triage_report.pdf
```

## Known Inhibitor Benchmark

The repository includes a small positive-control set:

- Sotorasib
- Adagrasib
- Divarasib
- MRTX1133

This is a sanity check, not a substitute for external validation. If a known inhibitor is scored poorly, that result should be documented as a model limitation and investigated through SMILES verification, training data coverage, and applicability-domain analysis.

## Reproducibility

Install:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Run tests:

```bash
python -m unittest discover -s tests
```

Rebuild order:

```bash
python -m kras_discovery.data_curation.chembl_pipeline
python -m kras_discovery.feature_engineering.rdkit_pipeline
python -m kras_discovery.quality.quality_pipeline
python -m kras_discovery.modeling.train_models --cv-folds 5
python -m kras_discovery.interpretation.interpret_model
python -m kras_discovery.modeling.performance_report
python -m kras_discovery.validation.known_inhibitors
python -m kras_discovery.screening.batch_screen --input data/external/example_screening_library.csv
python -m kras_discovery.screening.hit_triage --input data/processed/batch_screening/ranked_screening_results.csv
python -m kras_discovery.screening.hit_report
```

See [docs/reproducibility_protocol.md](docs/reproducibility_protocol.md) for full details.

## Reports and Release Snapshot

Key artifacts:

```text
reports/model_performance_summary.md
reports/model_interpretation_report.md
reports/zinc_hit_triage_report.md
reports/zinc_hit_triage_report.pdf
releases/v0.1-kras-zinc-screening.zip
```

The release snapshot preserves the generated evidence for review because live ChEMBL results may change over time.

## Engineering Tradeoffs

Several choices were made deliberately:

- I used descriptor and fingerprint models before deep learning because the labeled dataset is limited.
- I kept heuristic agents separate from trained-model inference so their assumptions remain visible.
- I committed small reports and summaries, but kept large raw data and model files out of normal Git history unless packaged in a release snapshot.
- I used CLI-first workflows because they are easier to test, rerun, and automate than notebooks.
- I treated drug-likeness filters as flags rather than hard deletion rules because oncology chemistry can violate simple rules.

## Limitations

- The model predicts KRAS bioactivity from curated public assay data; it does not prove direct binding or mutant selectivity.
- SOS1 is included as a pathway node but is not yet a separately trained predictive model.
- ChEMBL activity records are heterogeneous across assay conditions.
- ZINC22 hit candidates are computational predictions only.
- Docking, molecular dynamics, and experimental validation are not yet implemented in this repository.

## Version 2 Improvements

The next version should add:

- KRAS G12C docking for top ZINC22 hits.
- Comparison against known inhibitors in the same docking protocol.
- Applicability-domain analysis for model predictions.
- Probability calibration.
- More explicit assay-type stratification.
- PubMed/RAG evidence retrieval with citations.
- Better mapping of important MACCS/Morgan features back to chemical motifs.
- AWS Batch or ECS deployment for larger screening runs.

