# Engineering Review and Ownership Notes

This document records an engineering review of the repository. The goal is to make the project read like a maintained research codebase rather than a generated showcase.

## Review Summary

The project has a coherent technical foundation:

- data curation is scripted and parameterized;
- molecular feature generation uses standard RDKit representations;
- model training compares several baselines and writes metrics;
- cross-validation is included;
- the trained model is integrated into an agent workflow;
- ZINC22 screening and hit triage are reproducible CLI steps;
- generated reports and a release snapshot preserve evidence.

The main engineering risks are not architectural. They are mostly around scope clarity and duplicated helper code:

- several modules repeat simple helpers such as `project_root`, CSV readers/writers, `finding_by_agent`, and rounding utilities;
- some agents use heuristic proxies that should be clearly labeled as proxies;
- generated data and release artifacts need disciplined Git handling;
- the literature agent is currently a placeholder, not a real retrieval system;
- SOS1 is pathway-relevant, but the current model should be described as a KRAS bioactivity classifier.

## File-Level Review

### Repository Configuration

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `README.md` | Main project explanation and run guide | Gives technical readers the problem, workflow, commands, metrics, tradeoffs, and limitations | Rewritten to avoid marketing language and explain design decisions |
| `pyproject.toml` | Package metadata, optional dependencies, console scripts | Makes each pipeline stage runnable as a Python module or installed script | Good structure; dependencies are intentionally grouped by function |
| `requirements.txt` | Practical install path for reproducing the project | Simplifies setup for users not installing optional extras manually | Now includes the scientific stack; future improvement is a locked environment file |
| `.gitignore` | Keeps large generated artifacts out of Git history | Prevents raw ChEMBL/ZINC data and model binaries from cluttering normal commits | Should continue tracking small summary/report artifacts while excluding large data |
| `.env.example` | Placeholder for future environment variables | Documents configuration shape without leaking secrets | Currently minimal; expand only when real secrets/configuration exist |
| `LICENSE` | Repository license | Defines reuse terms | No action needed |

### Documentation

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `docs/technical_design.md` | System architecture and pipeline outputs | Captures design intent beyond README commands | Good high-level companion; updated to reflect the live AWS deployment (see README Deployment section); should be updated again when docking modules are added |
| `docs/reproducibility_protocol.md` | Exact rebuild order and reproducibility caveats | Makes the workflow reviewable and rerunnable | Important because ChEMBL is live and can change |
| `docs/niw_positioning.md` | Petition/portfolio framing | Separates immigration narrative from engineering README | Keep this separate so README stays technical |
| `docs/engineering_review.md` | Maintenance and ownership review | Records tradeoffs, file purpose, and cleanup opportunities | This document should evolve as the repo matures |

### Data Curation

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/data_curation/targets.py` | Defines ChEMBL target configuration | Keeps KRAS/SOS1 target IDs out of pipeline logic | Good simple config module |
| `src/kras_discovery/data_curation/chembl_client.py` | Minimal ChEMBL API client | Avoids adding a heavy client dependency and keeps API calls explicit | Add retry/backoff later for large reproducible runs |
| `src/kras_discovery/data_curation/curation.py` | Raw record extraction, labeling, variant inference, training-set construction | Encapsulates curation rules in testable functions | Strong core module; variant inference is heuristic and should stay documented |
| `src/kras_discovery/data_curation/chembl_pipeline.py` | CLI entrypoint for ChEMBL curation | Connects client and curation logic into runnable pipeline | Good; repeated `project_root` helper could eventually move to `utils.paths` |
| `tests/test_data_curation.py` | Unit tests for labeling and curation behavior | Protects the most scientifically important assumptions | Good coverage for current scope |

### Feature Engineering

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/feature_engineering/rdkit_features.py` | RDKit descriptors, MACCS keys, Morgan fingerprints, model matrix writer | Converts curated SMILES into numeric ML features | Clear and reproducible; keep fingerprint parameters explicit |
| `src/kras_discovery/feature_engineering/rdkit_pipeline.py` | CLI entrypoint for feature generation | Separates command parsing from feature logic | Good pattern |
| `tests/test_feature_engineering.py` | Tests descriptor and matrix behavior | Prevents accidental feature-layout breakage | Important because inference depends on feature order |

### Quality Filters

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/quality/druglikeness.py` | Lipinski/Veber/project-specific drug-likeness flags | Adds medicinal-chemistry context without deleting data | Good; keep language as "flags" rather than hard truth |
| `src/kras_discovery/quality/assay_quality.py` | Assay-quality flags from curated ChEMBL records | Makes assay caveats visible for reports | Good; future improvement is more assay-type stratification |
| `src/kras_discovery/quality/quality_pipeline.py` | CLI entrypoint for quality reports | Runs drug-likeness and assay-quality reports together | Simple and appropriate |
| `tests/test_quality.py` | Tests quality rules | Protects filter assumptions | Good |

### Modeling

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/modeling/dataset.py` | Reads model matrix and identifies numeric feature columns | Keeps metadata/quality fields out of the feature matrix | Important fix because boolean quality columns should not become features |
| `src/kras_discovery/modeling/train_models.py` | Trains baseline classifiers, writes metrics, CV, confusion matrices, and best model | Central modeling pipeline | Functionally solid; future cleanup could split CV/report-writing helpers into a smaller metrics module |
| `src/kras_discovery/modeling/performance_report.py` | Generates a Markdown model-performance summary | Converts metrics into a reviewable artifact | Useful for project evidence and reproducibility |
| `tests/test_modeling.py` | Tests matrix parsing, dependencies, and CV fold logic | Protects modeling assumptions | Good |
| `tests/test_performance_report.py` | Tests performance report generation | Ensures report generator remains stable | Good |

### Model Inference

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/inference/model_inference.py` | Loads saved model, builds single-SMILES feature vector, returns activity probability | Bridges offline training and runtime agent scoring | Important module; assumptions around feature order are explicit through `feature_columns.json` |
| `tests/test_inference.py` | Tests inference helpers and fallback-safe pipeline behavior | Ensures the CLI runs even without optional model dependencies | Good |

### Agent Workflow

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/agents/base.py` | Abstract agent interface | Gives all agents a consistent `run(context)` contract | Simple and appropriate |
| `src/kras_discovery/agents/orchestrator.py` | Runs agents in sequence and returns candidate report | Centralizes workflow order | Good; future version could make agent list configurable |
| `src/kras_discovery/agents/validation.py` | Basic candidate validation | Catches weak/invalid molecule inputs early | Proxy only; not a full chemistry validator |
| `src/kras_discovery/agents/features.py` | Approximate descriptor extraction for agent context | Gives heuristic agents lightweight molecular properties | Uses approximate helpers; trained model uses RDKit separately |
| `src/kras_discovery/agents/target_fit.py` | KRAS model inference with heuristic fallback | Main connection between ML model and agent workflow | Good; fallback evidence should remain visible |
| `src/kras_discovery/agents/selectivity.py` | Heuristic mutant/SOS1 hypothesis | Provides a review prompt, not a trained selectivity model | Rename in future to make heuristic status clearer if needed |
| `src/kras_discovery/agents/admet.py` | Rule-based ADMET proxy | Adds prioritization context | Not a replacement for ADMET ML models |
| `src/kras_discovery/agents/toxicity.py` | Simple toxicity motif flags | Screens obvious simple alerts | Limited; future work should add real toxicophore/PAINS logic |
| `src/kras_discovery/agents/literature.py` | Offline literature-readiness placeholder | Reserves the interface for PubMed/RAG evidence | Should not be described as real RAG until implemented |
| `src/kras_discovery/agents/manufacturability.py` | Synthetic-feasibility proxy | Adds practical development context | Heuristic only |
| `src/kras_discovery/agents/clinical.py` | Aggregates clinical relevance proxies | Connects model/ADMET/toxicity signals to indication context | Good as a prioritization layer, not clinical evidence |
| `src/kras_discovery/agents/ranking.py` | Combines agent scores into recommendation | Keeps ranking policy out of orchestrator | Good; thresholds should remain documented |
| `tests/test_pipeline.py` | Tests end-to-end agent report behavior | Guards CLI-level behavior | Good |

### Screening and Validation

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/cli.py` | Single/multiple SMILES CLI | Quick manual candidate evaluation | Simple and useful |
| `src/kras_discovery/pipelines/screening.py` | Candidate evaluation and ranking wrapper | Separates reusable screening logic from CLI | Good |
| `src/kras_discovery/validation/known_inhibitors.py` | Runs known KRAS inhibitors through the workflow | Provides positive-control sanity check | Should report actual probabilities and failures honestly |
| `src/kras_discovery/screening/zinc_prepare.py` | Converts ZINC `.smi` files to project CSV format | Makes ZINC22 tranche downloads usable by the screener | Good pragmatic bridge |
| `src/kras_discovery/screening/batch_screen.py` | Screens CSV libraries and writes ranked summaries/full reports | Core batch virtual screening module | Good; duplicated report helper functions could be shared later |
| `src/kras_discovery/screening/hit_triage.py` | Filters batch results into computational hit candidates | Makes hit selection reproducible instead of manual | Strong engineering decision |
| `src/kras_discovery/screening/hit_report.py` | Generates Markdown hit-triage report | Turns CSV evidence into a readable scientific artifact | Good; formatting helpers are local and acceptable for now |
| `tests/test_known_inhibitor_validation.py` | Tests validation workflow output | Good |
| `tests/test_zinc_prepare.py` | Tests ZINC conversion | Good |
| `tests/test_batch_screening.py` | Tests batch output behavior | Good |
| `tests/test_hit_triage.py` | Tests hit filtering | Good |
| `tests/test_hit_report.py` | Tests report generation | Good |

### Interpretation and Reports

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/interpretation/feature_importance.py` | Extracts built-in feature importances/coefs | Provides first-pass model interpretation | Good baseline; Morgan/MACCS bit mapping remains future work |
| `src/kras_discovery/interpretation/interpret_model.py` | CLI for built-in importance extraction | Keeps interpretation runnable | Good |
| `src/kras_discovery/interpretation/shap_analysis.py` | Optional SHAP analysis | Adds model-agnostic explanation support where dependencies exist | Optional dependency is appropriate |
| `src/kras_discovery/interpretation/run_shap.py` | CLI for SHAP outputs | Separates heavy optional path from standard run | Good |
| `src/kras_discovery/interpretation/report.py` | Builds interpretation Markdown content | Turns outputs into readable evidence | Good |
| `src/kras_discovery/interpretation/generate_report.py` | CLI for interpretation report | Good |
| `src/kras_discovery/reports/markdown_pdf.py` | Converts simple Markdown reports to PDF using ReportLab | Creates petition/review-friendly PDF artifact | Useful, but intentionally minimal Markdown support |
| `tests/test_interpretation.py` | Tests feature importance behavior | Good |
| `tests/test_shap_and_report.py` | Tests SHAP/report utilities | Good |

### Models and Utilities

| File | Purpose | Why it exists | Review notes |
| --- | --- | --- | --- |
| `src/kras_discovery/models/schemas.py` | Dataclasses for candidates, findings, reports, and target panels | Provides lightweight internal data contracts | Good choice; avoids heavier Pydantic dependency |
| `src/kras_discovery/models/targets.py` | KRAS target panel constants | Keeps target metadata centralized | Good |
| `src/kras_discovery/utils/chemistry.py` | Approximate chemistry helpers for lightweight agents | Allows CLI fallback without RDKit | Should remain clearly labeled as approximate |

### Generated Evidence and Release Artifacts

| Path | Purpose | Review notes |
| --- | --- | --- |
| `data/external/example_screening_library.csv` | Small screening fixture | Good to track |
| `data/external/known_kras_inhibitors.csv` | Positive-control input set | Good to track |
| `data/processed/*.json` and selected metrics CSVs | Small reproducibility summaries | Good to track |
| `reports/*.md` and `reports/*.pdf` | Human-readable evidence artifacts | Good to track |
| `releases/v0.1-kras-zinc-screening.zip` | Archival snapshot | Good as a GitHub release attachment; avoid many large versions in Git |
| `releases/v0.1-kras-zinc-screening/` | Expanded snapshot directory | Useful locally; consider whether the zip alone is enough in Git |
| `artifacts/models/` | Trained model binaries | Usually keep out of normal Git; include in release snapshots |
| `data/processed/batch_screening/ranked_screening_results.csv` | Full screening output | Can be large; track only if intentionally small |
| `data/processed/batch_screening/agent_screening_reports.json` | Full agent output | Can grow quickly; better suited for release artifacts |

## Unnecessary Complexity and Simplification Opportunities

1. Repeated root/path helpers
   - Several modules define `project_root`.
   - This is acceptable now, but a `utils.paths.project_root()` helper would reduce repetition.

2. Repeated report helper functions
   - `finding_by_agent`, `metric`, and `round_float` appear in more than one screening/validation module.
   - If another report module is added, move these to `utils.reporting`.

3. Heuristic agents should stay visibly heuristic
   - Selectivity, ADMET, toxicity, manufacturability, and clinical relevance are proxies.
   - The code already exposes evidence and metrics, but documentation should avoid making them sound like validated predictive models.

4. Report generation is intentionally simple
   - The Markdown-to-PDF exporter supports only the Markdown subset used by current reports.
   - This is fine for now; avoid turning it into a full document engine unless needed.

5. Generated files need discipline
   - The repo should track small evidence files, not every raw or full screening artifact.
   - Release snapshots are the right place for model binaries and larger outputs.

## Naming Improvements to Consider

- `MutantSelectivityAgent` could become `MutantSelectivityHypothesisAgent` to make its heuristic nature clearer.
- `FeatureAgent` could become `LightweightFeatureAgent` because trained-model features are generated separately with RDKit.
- `ClinicalRelevanceAgent` could become `ClinicalPrioritizationAgent` to avoid implying clinical validation.
- `zinc_hit_triage_report` should consistently be described as `ZINC22` in documentation.

These are not urgent changes because they would touch tests and documentation. The current names are understandable, but future renaming would make scientific boundaries clearer.

## Version 2 Engineering Plan

1. Add `utils.paths` and `utils.reporting` only if duplication grows.
2. Add model calibration and applicability-domain checks.
3. Add PubMed retrieval with citations before calling the literature agent real RAG.
4. Add docking preparation for top ZINC22 hits against KRAS G12C.
5. Add structured candidate evidence records that combine model score, hit triage, docking, literature, and limitations.
6. Add a locked environment file for exact dependency versions.
7. Add CI that runs unit tests and verifies report generation.

## Ownership Statement

The strongest part of this project is not a single model score. It is the connected workflow:

```text
target rationale -> public data -> transparent labels -> molecular features -> model comparison -> cross-validation -> agentic inference -> ZINC22 screening -> reproducible hit triage -> release snapshot
```

That structure makes the project explainable to software engineers, machine learning engineers, and computational biology reviewers.
