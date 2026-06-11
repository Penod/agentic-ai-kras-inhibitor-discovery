# Reproducibility Protocol

This protocol documents the expected run order for rebuilding the KRAS inhibitor discovery workflow from source.

## Environment

Create and activate a Python environment, then install the repository and scientific dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Pipeline Order

Run the pipeline in this order:

```bash
python -m kras_discovery.data_curation.chembl_pipeline
python -m kras_discovery.feature_engineering.rdkit_pipeline
python -m kras_discovery.quality.quality_pipeline
python -m kras_discovery.modeling.train_models --cv-folds 5
python -m kras_discovery.interpretation.interpret_model
python -m kras_discovery.modeling.performance_report
python -m kras_discovery.validation.known_inhibitors
python -m kras_discovery.screening.batch_screen --input data/external/example_screening_library.csv
python -m kras_discovery.screening.hit_triage --input data/processed/batch_screening/ranked_screening_results.csv --min-kras-probability 0.70 --min-admet-score 0.60 --top-n 25
python -m kras_discovery.screening.hit_report
python -m kras_discovery.reports.markdown_pdf --input reports/zinc_hit_triage_report.md --output reports/zinc_hit_triage_report.pdf
```

For ZINC screening, first convert a downloaded `.smi` tranche into a sampled CSV:

```bash
python -m kras_discovery.screening.zinc_prepare --input data/external/zinc_raw/EC/ECAA.smi --output data/external/zinc_screening_library.csv --limit 5000
python -m kras_discovery.screening.batch_screen --input data/external/zinc_screening_library.csv
```

## Expected Checkpoints

The full ChEMBL/RDKit/modeling workflow should produce:

```text
data/processed/kras_curation_summary.json
data/processed/kras_feature_summary.json
data/processed/kras_druglikeness_summary.json
data/processed/kras_assay_quality_summary.json
data/processed/model_metrics.csv
data/processed/cross_validation_metrics.csv
data/processed/model_comparison.json
artifacts/models/kras_best_model.pkl
artifacts/models/feature_columns.json
reports/model_performance_summary.md
reports/model_interpretation_report.md
reports/zinc_hit_triage_report.md
reports/zinc_hit_triage_report.pdf
```

## Determinism Notes

- Model training uses a fixed `random_state` of `42` by default.
- Train/test splitting uses stratification to preserve active/inactive class balance.
- Cross-validation uses stratified folds and the same random seed.
- Training rows are sorted by target, variant/node, and ChEMBL molecule identifier.
- RDKit feature generation uses deterministic descriptor and fingerprint settings.

## External Data Notes

The ChEMBL curation step calls the live ChEMBL API. Results may change if ChEMBL updates records after a previous run. For exact archival reproducibility, preserve the generated raw and curated ChEMBL CSV files, model matrix, and model artifacts in a release archive or external data repository.

The repository intentionally ignores large raw/processed data files by default. Small control inputs, metric summaries, and report artifacts should be committed because they document the methodology and allow reviewers to inspect the evidence without rerunning the full workflow.

## Validation Boundary

The workflow produces computational hit candidates for downstream validation. It does not claim experimental KRAS inhibition, clinical activity, or therapeutic efficacy. Top-ranked candidates require docking, molecular dynamics, medicinal chemistry review, and experimental biochemical or cell-based validation.
