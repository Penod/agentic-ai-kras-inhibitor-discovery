# Agentic AI KRAS Inhibitor Discovery

An end-to-end computational drug discovery workflow for prioritizing KRAS-pathway inhibitor candidates from public bioactivity and chemical-library data — built to answer a practical engineering question:

> Can a reproducible Python pipeline combine ChEMBL curation, RDKit molecular features, supervised learning, agentic screening, and ZINC22 hit triage into a workflow that is understandable enough for scientific review?

This is not a clinical tool and does not claim to discover confirmed KRAS drugs. It produces computational hit candidates that require docking, molecular dynamics, medicinal chemistry review, and experimental validation before they mean anything therapeutically.

## Problem

KRAS is one of the most frequently mutated oncogenes in human cancer, implicated in a majority of pancreatic ductal adenocarcinoma cases, roughly a third of lung adenocarcinomas, and a large share of colorectal cancers. Direct KRAS inhibition was considered undruggable for decades; KRAS G12C inhibitors changed that, but most KRAS-driven cancers still lack effective targeted options.

This project focuses on the early computational screening problem: assembling public bioactivity data, training a KRAS bioactivity classifier, and using that model inside a transparent, inspectable screening workflow.

## Target Scope

| Target or node | Role in this project |
| --- | --- |
| KRAS G12C | Clinically validated direct-inhibition starting point |
| KRAS G12D | High-priority pancreatic cancer mutation |
| KRAS G12V | Common KRAS mutation with limited direct-inhibitor options |
| SOS1 | Pathway-relevant exchange factor for future expansion |

## Design Goals

- Use public data sources so the workflow can be inspected and rerun by anyone.
- Keep every pipeline stage callable from the command line.
- Prefer standard cheminformatics features before reaching for deep learning.
- Compare several baseline models rather than reporting one in isolation.
- Preserve model outputs, reports, and release snapshots for reproducibility.
- Keep agent outputs explainable enough for human scientific review.

A web app was deliberately not the first thing built. The core risk here was never UI — it was whether the data, labels, features, models, and screening outputs were scientifically coherent.

## Architecture

```text
src/kras_discovery/
  data_curation/       ChEMBL retrieval, cleaning, activity labeling
  feature_engineering/ RDKit descriptors, MACCS keys, Morgan fingerprints
  quality/             Drug-likeness and assay-quality reports
  modeling/            Model training, cross-validation, performance reports
  inference/           Saved-model loading and SMILES-level prediction
  agents/              Rule-based multi-agent candidate evaluation (9 agents, fixed sequence)
  orchestration/       LLM-driven orchestration layer (Strands SDK / AWS Bedrock)
  screening/           Batch screening, ZINC22 preparation, hit triage
  interpretation/      Feature importance, optional SHAP, interpretation report
  validation/          Known KRAS inhibitor positive-control screening
  reports/             Markdown-to-PDF report utility
```

The main workflow:

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

Training data comes from ChEMBL:

| Source | Identifier |
| --- | --- |
| KRAS | `CHEMBL2189121` |
| SOS1 | `CHEMBL4523334` |

Curation calls the live ChEMBL API, which keeps the pipeline current but means exact row counts can shift as ChEMBL updates records. Release snapshots preserve the generated metrics, reports, and artifacts from a specific run for archival reproducibility.

Candidate screening uses sampled lead-like compounds from ZINC22, accessed through the CartBlanche/ZINC22 tranche interface.

## Labeling Strategy

pChEMBL thresholds define a first binary classification task:

| Class | Rule |
| --- | --- |
| Active | `pchembl_value >= 7.0` |
| Inactive | `pchembl_value <= 5.0` |
| Ambiguous | `5.0 < pchembl_value < 7.0` |
| Unlabeled | missing pChEMBL |

Only clear active/inactive records train the model. Ambiguous records stay in curated audit files but are excluded from training — a pragmatic choice that reduces label noise at the cost of a narrower training set. A future version should explore regression on continuous pChEMBL values, assay-aware modeling, and uncertainty estimates.

## Molecular Representation

SMILES strings become numerical features via RDKit:

- **Physicochemical descriptors** — molecular weight, LogP, TPSA, hydrogen-bond counts, ring counts, fraction CSP3, and related properties.
- **MACCS keys** — 166 structural keys.
- **Morgan fingerprints** — 2048-bit circular fingerprints.

The current model matrix: **1,398 compounds × 2,226 numeric molecular features.**

Descriptor and fingerprint baselines were chosen over a graph neural network because they're standard, reproducible, easy to inspect, and a better first step for a limited labeled dataset. A GNN remains a reasonable future direction once more labeled data is available.

## Model Development

The training pipeline compares seven models: a dummy baseline, Logistic Regression, Random Forest, Decision Tree, Naive Bayes, SVM (RBF kernel), and XGBoost.

Model selection uses a **molecule-grouped train/test split** (zero shared molecules between train and holdout), scored on holdout ROC-AUC:

| Model | ROC-AUC | Accuracy | F1 |
| --- | --- | --- | --- |
| **Random Forest (deployed)** | **0.9802** | 0.916 | 0.946 |
| XGBoost | 0.9784 | 0.945 | 0.966 |
| SVM (RBF) | 0.9579 | 0.942 | 0.964 |
| Logistic Regression | 0.9532 | 0.938 | 0.961 |

**Random Forest is the deployed model** — it holds the best holdout ROC-AUC under the molecule-grouped split. XGBoost is a close second and remains an important reference in the full performance report; both are kept visible rather than reporting a single model in isolation.

To test generalization to unfamiliar chemistry, the same models are also evaluated on a **scaffold split**, where the holdout set shares zero Bemis-Murcko scaffolds with the training set — a stricter, more realistic test for structurally novel candidates.

The training pipeline writes:

```text
data/processed/model_metrics.csv
data/processed/cross_validation_metrics.csv
data/processed/model_comparison.json
data/processed/holdout_predictions.csv
data/processed/confusion_matrices/
artifacts/models/kras_best_model.pkl
artifacts/models/feature_columns.json
```

## Performance Summary

### Molecule-grouped holdout

| Metric | Value |
| --- | --- |
| Accuracy | 0.916 |
| Precision | 0.971 |
| Recall | 0.922 |
| F1 | 0.946 |
| ROC-AUC | 0.980 |
| PR-AUC | 0.995 |

Train/holdout molecule overlap: 0. Scaffold overlap: 82 — some analog series appear on both sides, which is why the scaffold split below is the more conservative estimate.

### Scaffold split

| Metric | Value |
| --- | --- |
| Accuracy | 0.875 |
| Precision | 0.961 |
| Recall | 0.884 |
| F1 | 0.921 |
| ROC-AUC | 0.938 |
| PR-AUC | 0.986 |

Performance drops modestly under the stricter split, as expected, and still clears the dummy baseline (ROC-AUC 0.500) by a wide margin.

### Five-fold molecule-grouped cross-validation

| Model | ROC-AUC | PR-AUC | Accuracy | F1 |
| --- | --- | --- | --- | --- |
| Random Forest | 0.971 ± 0.011 | 0.991 ± 0.004 | 0.928 ± 0.014 | 0.954 ± 0.009 |
| XGBoost | 0.968 ± 0.009 | 0.990 ± 0.003 | 0.935 ± 0.011 | 0.959 ± 0.007 |
| Dummy baseline | 0.500 ± 0.000 | 0.781 ± 0.001 | 0.781 ± 0.001 | 0.877 ± 0.001 |

These metrics support using the classifier for computational prioritization within the screening pipeline. They do not prove experimental KRAS inhibition, binding, or mutant selectivity.

## Agentic Screening Workflow

A fixed sequence of 9 rule-based agents evaluates each candidate, passing a shared context object from one to the next:

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

`KRASTargetFitAgent` loads the trained model. If RDKit, joblib, or model artifacts are missing, it falls back to a transparent heuristic instead of failing the whole pipeline — this keeps the workflow runnable in minimal environments, but trained-model results should always be preferred for real screening, and every finding reports which mode (`trained_model` vs. `heuristic_fallback`) produced it.

### LLM orchestration layer

`src/kras_discovery/orchestration/` adds a Bedrock/Strands-based LLM agent on top of this pipeline — it does not replace or re-implement the 9-agent sequence above, which stays deterministic and unchanged. The LLM's job is workflow-level: deciding whether a request calls for single-molecule evaluation, ZINC library preparation, batch screening, or hit triage, chaining those correctly, and explaining the results in natural language rather than requiring the user to run each CLI step by hand or interpret raw CSV output themselves.

This is a genuine capability gap the rule-based pipeline doesn't close on its own: the original CLI (`kras-screen <smiles>`) takes one predetermined input shape and prints structured JSON. The orchestration layer instead accepts a request in plain language, decides which underlying tool(s) to call, and reports back — while every prediction underneath is still produced by the same trained Random Forest classifier and the same 9 rule-based agents.

This has been demonstrated end-to-end on AWS Bedrock (Amazon Nova) for both supported workflows: a single-molecule evaluation request that correctly invoked `evaluate_candidate` and explained all 9 agent findings in natural language, and a full-library request that correctly chained `run_batch_screen` followed by `triage_screening_hits` against the 5,000-compound ZINC22 run documented above, reasoning explicitly about why zero-then-four hits passed the triage criteria.

## ZINC22 Screening and Hit Triage

A sampled ZINC22 lead-like tranche was used for a pilot virtual screen.

Convert the raw ZINC `.smi` file to CSV:

```bash
python -m kras_discovery.screening.zinc_prepare \
  --input data/external/zinc_raw/EC/ECAA.smi \
  --output data/external/zinc_screening_library.csv \
  --limit 5000
```

Run the batch screener:

```bash
python -m kras_discovery.screening.batch_screen \
  --input data/external/zinc_screening_library.csv
```

Hit selection is reproducible against fixed criteria:

```text
inference_mode = trained_model
kras_probability_active >= 0.70
admet_score >= 0.60
toxicity_label = Low risk
recommendation = Advance or Advance with review
```

Results are documented in `reports/zinc_hit_triage_report.md` and `reports/zinc_hit_triage_report.pdf`.

### Reproduced run (ZINC22 EC/ECAA tranche, 5,000 compounds)

A full run against a live-downloaded ZINC22 tranche (`files.docking.org/2D/EC/ECAA.smi`, 31,454 compounds, capped at 5,000 per the standard `--limit`) through the trained Random Forest classifier (`inference_mode = trained_model` for all 5,000 evaluations) produced:

| Metric | Value |
| --- | --- |
| Total screened | 5,000 |
| Total hit candidates | 4 |
| Recommendation: Advance | 2 |
| Recommendation: Advance with review | 2 |

| Rank | Compound (ZINC ID) | KRAS-active probability | ADMET score | Toxicity | Recommendation |
| --- | --- | --- | --- | --- | --- |
| 1 | 72411788 | 0.816 | 0.826 | Low risk | Advance |
| 2 | 72408688 | 0.774 | 0.826 | Low risk | Advance |
| 4 | 72453647 | 0.709 | 0.837 | Low risk | Advance with review |
| 5 | 72422287 | 0.704 | 0.826 | Low risk | Advance with review |

Two caveats specific to this run:

- All four hits share a visually similar fused bicyclic scaffold. This may reflect a genuine structure-activity signal, or the model's sensitivity to one scaffold family rather than diverse chemotypes — worth checking against Bemis-Murcko scaffold overlap before treating these as four independent leads.
- All four hits' mutant-selectivity hypothesis is "SOS1," not a specific KRAS mutant (G12C/G12D/G12V). Per the Known Inhibitor Benchmark below, the selectivity agent is not yet reliable at distinguishing mutants, so these should be read as KRAS-pathway hits by the trained classifier, not as mutant-selective candidates.

## Known Inhibitor Benchmark

| Compound | Status | Predicted KRAS-active probability | Recommendation |
| --- | --- | --- | --- |
| Sotorasib | FDA-approved (KRAS G12C) | 0.992 | Advance |
| Divarasib | Investigational (KRAS G12C) | 0.998 | Advance |
| Adagrasib | FDA-approved (KRAS G12C) | 0.998 | Advance |
| MRTX1133 | Investigational (KRAS G12D) | 1.000 | Advance with review |

All four known inhibitors are correctly flagged as KRAS-active with high confidence — a useful sanity check on the bioactivity classifier.

The mutant-selectivity hypothesis agent is **not yet reliable** at distinguishing which KRAS mutant a compound targets: it labels all four compounds above as "Best hypothesis: G12D," even though three are G12C-selective drugs. This is expected given its current heuristic (non-trained) design and should not be read as a validated mutant-selectivity prediction.

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
python -m kras_discovery.visualization.static_plots
```

See [docs/reproducibility_protocol.md](docs/reproducibility_protocol.md) for full details.

## Reports and Release Snapshot

```text
reports/model_performance_summary.md
reports/model_interpretation_report.md
reports/statistical_exploration_summary.md
reports/zinc_hit_triage_report.md
reports/zinc_hit_triage_report.pdf
reports/figures/
releases/v0.1-kras-zinc-screening.zip
```

The release snapshot preserves generated evidence for review, since live ChEMBL results can change over time.

The statistical exploration report is generated from saved CSV and JSON outputs, and includes the ChEMBL curation funnel, activity-class balance, KRAS mutation distribution, molecular property distributions, drug-likeness summaries, holdout confusion matrices, cross-validation ROC-AUC, ROC/precision-recall curves, feature importance, and ZINC22 screening triage figures.

## Engineering Tradeoffs

- Descriptor and fingerprint models came before deep learning, because the labeled dataset is limited.
- Heuristic agents are kept separate from trained-model inference so their assumptions stay visible rather than blended together.
- Small reports and summaries are committed to Git; large raw data and model files stay out of normal history unless packaged into a release snapshot.
- CLI-first workflows were chosen over notebooks because they're easier to test, rerun, and automate.
- Drug-likeness filters are flags, not hard deletion rules, because oncology chemistry can legitimately violate simple rules.

## Limitations

- The deployed classifier predicts general KRAS-pathway bioactivity from curated public assay data. It does not prove direct binding, functional inhibition, or mutant selectivity.
- SOS1 is included as a pathway node but is not yet a separately trained predictive model.
- Scaffold-split performance (ROC-AUC 0.938) is meaningfully lower than molecule-grouped holdout performance (ROC-AUC 0.980) and is the more realistic estimate for structurally novel candidates.
- ChEMBL activity records are heterogeneous across assay conditions and are not yet stratified by assay type.
- ZINC22 hit candidates are computational predictions only; confirm the hit triage report was generated against the current molecule-grouped/scaffold-validated model before citing it as final evidence.
- Docking, molecular dynamics, and experimental validation are not yet implemented.
- The system evaluates and ranks existing compounds; it does not design, generate, or optimize novel molecular structures.

## Future Improvements

- KRAS G12C docking for top ZINC22 hits, benchmarked against known inhibitors in the same docking protocol.
- Applicability-domain analysis and probability calibration for model predictions.
- More explicit assay-type stratification.
- PubMed/RAG evidence retrieval with citations, replacing the current literature-agent placeholder.
- AWS deployment (Lambda/AgentCore or ECS/Batch) for the orchestration layer and larger screening runs.
