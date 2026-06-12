# Agentic AI KRAS Inhibitor Discovery

## Overview
An agentic AI and computational drug discovery platform for **KRAS mutant-selective inhibitor discovery**, focused on **KRAS G12C**, **KRAS G12D**, **KRAS G12V**, and **SOS1** in pancreatic cancer, lung adenocarcinoma, and colorectal cancer.

This project is designed as a research-grade, reproducible portfolio system: it combines ChEMBL data curation, target-aware screening agents, active/inactive compound labeling, and a roadmap for machine learning, biomedical RAG, docking, molecular dynamics validation, and cloud deployment.

## Proposed Endeavor

Develop agentic AI systems for KRAS mutant-selective anti-cancer drug discovery, focusing on computational screening, evidence synthesis, and molecular validation for pancreatic cancer, lung adenocarcinoma, and colorectal cancer.

## Why This Matters

KRAS is one of the most important oncogenic drivers in human cancer and has historically been considered difficult to drug. The 2021 FDA accelerated approval of sotorasib for KRAS G12C-mutated non-small cell lung cancer marked a major milestone: KRAS inhibition moved from a long-standing challenge to an active therapeutic frontier.

This project builds on that frontier by creating an AI-assisted screening framework for mutant-selective KRAS discovery. The scientific and public-interest rationale is strong because KRAS-driven cancers include high-burden malignancies such as pancreatic cancer, lung adenocarcinoma, and colorectal cancer, where improved therapeutic options remain urgently needed.

## National-Importance Framing

This repository supports a broader proposed endeavor in:

- AI-enabled cancer drug discovery
- precision oncology
- computational screening of difficult therapeutic targets
- KRAS mutant-selective inhibitor prioritization
- reproducible biomedical machine learning infrastructure
- future cloud-native drug discovery workflows

The project is not presented as a clinical system or treatment recommendation. It is a computational research platform for early-stage candidate prioritization and scientific review.

## Target Scope

| Target | Gene/Node | Discovery Role |
| --- | --- | --- |
| KRAS G12C | KRAS | Clinically validated covalent inhibitor target |
| KRAS G12D | KRAS | High-priority pancreatic cancer mutation |
| KRAS G12V | KRAS | Common solid-tumor mutation with limited direct inhibitor options |
| SOS1 | SOS1 | Upstream KRAS pathway exchange-factor target |

## Current Capabilities

The current prototype accepts candidate SMILES strings and routes them through a multi-agent screening workflow:

1. Molecule validation
2. Molecular feature extraction
3. KRAS pathway target-fit estimation
4. Mutant selectivity hypothesis
5. ADMET suitability
6. Toxicity risk
7. KRAS literature evidence readiness
8. Manufacturability assessment
9. Clinical relevance for pancreatic/lung cancer
10. Candidate ranking

The KRAS target-fit agent now attempts to use the trained model artifacts in `artifacts/models/` for model-powered inference. If RDKit, joblib, or model artifacts are unavailable, the agent falls back to the explainable offline proxy so the CLI remains runnable.

## ChEMBL Data Curation

This project pipeline mirrors a computational drug discovery workflow: retrieve target activity data, clean it, label active/inactive compounds, and prepare a training set for downstream RDKit feature generation and model comparison.

Target sources:

- KRAS ChEMBL target: `CHEMBL2189121`
- SOS1 ChEMBL target: `CHEMBL4523334`

Run the KRAS/SOS1 curation pipeline:

```powershell
python -m kras_discovery.data_curation.chembl_pipeline
```

For a quick smoke test with fewer records:

```powershell
python -m kras_discovery.data_curation.chembl_pipeline --max-records-per-target 100
```

Outputs:

```text
data/processed/kras_chembl_raw_activities.csv
data/processed/kras_chembl_curated_activities.csv
data/processed/kras_training_set.csv
data/processed/kras_curation_summary.json
```

Default labeling rule:

- Active: `pchembl_value >= 7.0`
- Inactive: `pchembl_value <= 5.0`
- Ambiguous: `5.0 < pchembl_value < 7.0`
- Unlabeled: missing pChEMBL value

The middle activity range is retained in the curated audit file but excluded from the first training set to keep labels cleaner.

## RDKit Feature Engineering

After creating `data/processed/kras_training_set.csv`, generate model-ready molecular features with RDKit.

Install the optional feature-engineering dependency:

```powershell
pip install rdkit
```

Run the RDKit feature pipeline:

```powershell
python -m kras_discovery.feature_engineering.rdkit_pipeline
```

Outputs:

```text
data/processed/kras_features_descriptors.csv
data/processed/kras_features_maccs.csv
data/processed/kras_features_morgan.csv
data/processed/kras_model_matrix.csv
data/processed/kras_feature_summary.json
```

Feature groups:

- RDKit descriptors: molecular weight, LogP, TPSA, H-bond donors/acceptors, rotatable bonds, ring count, aromatic ring count, fraction CSP3, heavy atom count, NHOH count, NO count
- MACCS keys: `maccs_1` through `maccs_166`
- Morgan fingerprints: `morgan_0` through `morgan_2047`

The resulting `kras_model_matrix.csv` is the input for the next phase: XGBoost, Random Forest, SVM, Decision Tree, and Naive Bayes model training.

## Drug-Likeness and Assay-Quality Reports

Generate quality-control reports before interpreting model performance:

```powershell
python -m kras_discovery.quality.quality_pipeline
```

Outputs:

```text
data/processed/kras_model_matrix_druglikeness_report.csv
data/processed/kras_model_matrix_druglike_subset.csv
data/processed/kras_druglikeness_summary.json
data/processed/kras_assay_quality_report.csv
data/processed/kras_assay_quality_subset.csv
data/processed/kras_assay_quality_summary.json
```

Drug-likeness checks include Lipinski-style violations, Veber-style TPSA/rotatable-bond filters, and a project-specific drug-like window. These filters are used for reporting and subset analysis, not as irreversible deletion rules, because KRAS covalent inhibitor chemistry may intentionally stretch some classic small-molecule filters.

## Model Training

After `data/processed/kras_model_matrix.csv` exists, train and compare baseline models:

```powershell
pip install scikit-learn joblib numpy
python -m kras_discovery.modeling.train_models
```

XGBoost installation:

```powershell
pip install xgboost
python -m kras_discovery.modeling.train_models
```

Outputs:

```text
data/processed/model_metrics.csv
data/processed/cross_validation_metrics.csv
data/processed/model_comparison.json
data/processed/confusion_matrices/
artifacts/models/kras_best_model.pkl
artifacts/models/feature_columns.json
```

Models currently compared:

- Dummy baseline
- Logistic Regression
- Random Forest
- Decision Tree
- Naive Bayes
- SVM with RBF kernel
- XGBoost

Default model-selection metric: `roc_auc`.

The training pipeline also reports stratified cross-validation metrics by default:

```powershell
python -m kras_discovery.modeling.train_models --cv-folds 5
```

Cross-validation outputs include mean and standard deviation for accuracy, precision, recall, F1, ROC-AUC, and PR-AUC. These results are intended for model documentation and petition/reporting artifacts; the saved best model is still selected from the holdout test-set comparison unless `--selection-metric` is changed.

## Model Interpretation

After training, generate feature-importance outputs for the selected best model:

```powershell
python -m kras_discovery.interpretation.interpret_model
```

For the drug-like subset model:

```powershell
python -m kras_discovery.interpretation.interpret_model --model-path artifacts/models/druglike/kras_best_model.pkl --feature-columns artifacts/models/druglike/feature_columns.json --output-dir data/processed/druglike_modeling/interpretation
```

Outputs:

```text
data/processed/interpretation/feature_importance.csv
data/processed/interpretation/feature_importance_summary.json
```

The current interpretation phase supports models with built-in `feature_importances_` or `coef_`, including XGBoost, Random Forest, Decision Tree, and Logistic Regression. Feature importance is grouped into RDKit descriptors, MACCS keys, and Morgan fingerprint bits.

SHAP analysis:

```powershell
pip install shap
python -m kras_discovery.interpretation.run_shap
python -m kras_discovery.interpretation.run_shap --model-path artifacts/models/druglike/kras_best_model.pkl --model-matrix data/processed/kras_model_matrix_druglike_subset.csv --output-dir data/processed/druglike_modeling/interpretation/shap
```

Generate the written interpretation report:

```powershell
python -m kras_discovery.interpretation.generate_report
```

Report output:

```text
reports/model_interpretation_report.md
```

Generate the model-performance summary:

```powershell
python -m kras_discovery.modeling.performance_report
```

Output:

```text
reports/model_performance_summary.md
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m kras_discovery.cli "O=C(NC1=CC=CC=C1)C1=CC=CC=C1"
```

After model training, the same CLI command uses the saved best model:

```powershell
python -m kras_discovery.cli "SMILES_HERE"
```

The `kras_target_fit` finding will include `inference_mode`, `probability_active`, `predicted_label`, `model_path`, and `feature_count` when trained-model inference is available.

## Known KRAS Inhibitor Validation

Before screening unknown compounds, run the trained agent workflow on known KRAS inhibitor positive controls:

```powershell
python -m kras_discovery.validation.known_inhibitors
```

Input:

```text
data/external/known_kras_inhibitors.csv
```

Outputs:

```text
data/processed/known_inhibitor_validation/known_kras_inhibitor_validation_summary.csv
data/processed/known_inhibitor_validation/known_kras_inhibitor_agent_reports.json
```

This validation set includes verified reference compounds such as sotorasib, adagrasib, divarasib, and MRTX1133. It is used as an external positive-control sanity check: known inhibitors should receive higher KRAS activity probabilities than weak or unrelated screening candidates. If the trained model scores known inhibitors, that result should be documented as a model limitation and used to guide additional curation, target-specific labeling, or model improvement.

## Batch Virtual Screening

Screen a CSV library of candidate SMILES through the full agent workflow:

```powershell
python -m kras_discovery.screening.batch_screen --input data/external/example_screening_library.csv
```

Expected input columns:

```text
compound,smiles
```

Additional metadata columns such as `library` and `notes` are preserved in the ranked summary when present.

Outputs:

```text
data/processed/batch_screening/ranked_screening_results.csv
data/processed/batch_screening/agent_screening_reports.json
```

The ranked CSV includes overall score, recommendation, validation label, KRAS target-fit label, trained-model probability when available, inference mode, mutant-selectivity hypothesis, ADMET score, toxicity score, manufacturability score, clinical-relevance score, and SMILES. The JSON output preserves the full multi-agent report for each screened compound.

For custom column names:

```powershell
python -m kras_discovery.screening.batch_screen --input path/to/library.csv --name-column molecule_name --smiles-column canonical_smiles
```

To export only the top-ranked candidates:

```powershell
python -m kras_discovery.screening.batch_screen --input path/to/library.csv --top-n 25
```

If ZINC22 exports a `.smi` file, convert and sample it before screening:

```powershell
python -m kras_discovery.screening.zinc_prepare --input data/external/zinc_raw/EC/ECAA.smi --output data/external/zinc_screening_library.csv --limit 5000
python -m kras_discovery.screening.batch_screen --input data/external/zinc_screening_library.csv
```

After screening, filter computational hit candidates:

```powershell
python -m kras_discovery.screening.hit_triage --input data/processed/batch_screening/ranked_screening_results.csv --min-kras-probability 0.70 --min-admet-score 0.60 --top-n 25
```

Outputs:

```text
data/processed/batch_screening/hit_triage/top_hit_candidates.csv
data/processed/batch_screening/hit_triage/hit_triage_summary.json
```

Generate a written Markdown triage report:

```powershell
python -m kras_discovery.screening.hit_report
```

Output:

```text
reports/zinc_hit_triage_report.md
```

Export the ZINC22 hit triage report to PDF:

```powershell
pip install reportlab
python -m kras_discovery.reports.markdown_pdf --input reports/zinc_hit_triage_report.md --output reports/zinc_hit_triage_report.pdf
```

Run tests:

```powershell
python -m unittest discover -s tests
```

For a complete rebuild order and reproducibility notes, see:

```text
docs/reproducibility_protocol.md
```

## Example Output

```json
{
  "compound": "Candidate-1",
  "smiles": "O=C(NC1=CC=CC=C1)C1=CC=CC=C1",
  "target_family": "KRAS pathway",
  "overall_score": 0.74,
  "overall_rank": 1,
  "recommendation": "Advance with review"
}
```

## Architecture

```text
Research Scientist
       |
       v
KRAS Agent Orchestrator
       |
       +--> Validation Agent
       +--> Feature Agent
       +--> KRAS Target-Fit Agent
       +--> Mutant Selectivity Agent
       +--> ADMET Agent
       +--> Toxicity Agent
       +--> Literature Agent
       +--> Manufacturability Agent
       +--> Clinical Relevance Agent
       +--> Ranking Agent
       |
       v
Human Scientific Review
       |
       v
Ranked KRAS Pathway Inhibitor Candidates
```

## Research Roadmap

- Curate KRAS G12C, G12D, G12V, and SOS1 bioactivity records from ChEMBL, BindingDB, PubChem, and primary literature.
- Generate RDKit molecular descriptors, MACCS keys, Morgan fingerprints, and substructure flags.
- Train baseline models for KRAS target activity and mutant selectivity.
- Compare XGBoost, Random Forest, SVM, LightGBM, and neural baselines.
- Evaluate ROC-AUC, PR-AUC, precision, recall, F1-score, calibration, and class balance.
- Add explainability outputs and model cards for scientific review.
- Add ADMET/toxicity filters and uncertainty-aware candidate ranking.
- Add PubMed RAG evidence summaries with source citations.
- Add docking and molecular dynamics validation for prioritized candidates.
- Deploy a reproducible API and cloud workflow on AWS.

## Evidence To Build

This repository is intended to support a larger technical portfolio by producing:

- reproducible curation scripts and datasets
- benchmarked machine learning models
- target-aware agentic screening reports
- technical documentation and model cards
- cloud deployment artifacts
- future research report or preprint material

## Sources

- FDA: sotorasib received accelerated approval on May 28, 2021 for KRAS G12C-mutated locally advanced or metastatic NSCLC after at least one prior systemic therapy.
- NCI: the sotorasib approval was described as the first FDA-approved KRAS inhibitor and a milestone for a target long considered difficult to drug.
