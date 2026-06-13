# ZINC KRAS Hit Triage Report

Generated: 2026-06-09

## Objective

Prioritize computational KRAS hit candidates from a sampled ZINC lead-like screening library using the trained KRAS bioactivity model and the agentic triage workflow.

## Hit Selection Criteria

- Trained-model inference required: `True`
- Minimum KRAS activity probability: `0.7`
- Minimum ADMET score: `0.6`
- Required toxicity label: `Low risk`
- Allowed recommendations: `Advance`, `Advance with review`

## Screening Summary

- Total screened compounds: `5000`
- Computational hit candidates passing filters: `4`
- Reported candidates: `4`

## Top Hit Candidates

| Rank | Compound | KRAS Probability | Overall | ADMET | Toxicity | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 72411788 | 0.816 | 0.836 | 0.826 | Low risk | Advance |
| 2 | 72408688 | 0.774 | 0.826 | 0.826 | Low risk | Advance |
| 3 | 72453647 | 0.709 | 0.812 | 0.837 | Low risk | Advance with review |
| 4 | 72422287 | 0.704 | 0.808 | 0.826 | Low risk | Advance with review |

## Candidate Interpretations

### 1. 72411788

72411788 is prioritized because it shows a moderate trained-model KRAS activity signal (probability 0.816), acceptable ADMET profile (score 0.826), toxicity label `Low risk`, and agent recommendation `Advance`.

- Target-fit label: `Predicted KRAS-active`
- Inference mode: `trained_model`
- Mutant-selectivity hypothesis: `Best hypothesis: SOS1`
- Manufacturability: `Complex synthesis` with score `0.601`
- SMILES: `CCc1nc2c(c(N3CC[C@H](COC)C3)n1)CCN(CC(=O)O)CC2`

### 2. 72408688

72408688 is prioritized because it shows a moderate trained-model KRAS activity signal (probability 0.774), acceptable ADMET profile (score 0.826), toxicity label `Low risk`, and agent recommendation `Advance`.

- Target-fit label: `Predicted KRAS-active`
- Inference mode: `trained_model`
- Mutant-selectivity hypothesis: `Best hypothesis: SOS1`
- Manufacturability: `Complex synthesis` with score `0.601`
- SMILES: `CCOCc1nc2c(c(N3CCC(O)CC3)n1)CCN(C(C)=O)CC2`

### 3. 72453647

72453647 is prioritized because it shows a moderate trained-model KRAS activity signal (probability 0.709), acceptable ADMET profile (score 0.837), toxicity label `Low risk`, and agent recommendation `Advance with review`.

- Target-fit label: `Predicted KRAS-active`
- Inference mode: `trained_model`
- Mutant-selectivity hypothesis: `Best hypothesis: SOS1`
- Manufacturability: `Complex synthesis` with score `0.613`
- SMILES: `COCCNc1nc2c(c(N3CCC[C@@H](CO)C3)n1)CCNCC2`

### 4. 72422287

72422287 is prioritized because it shows a moderate trained-model KRAS activity signal (probability 0.704), acceptable ADMET profile (score 0.826), toxicity label `Low risk`, and agent recommendation `Advance with review`.

- Target-fit label: `Predicted KRAS-active`
- Inference mode: `trained_model`
- Mutant-selectivity hypothesis: `Best hypothesis: SOS1`
- Manufacturability: `Complex synthesis` with score `0.601`
- SMILES: `CCNC(=O)[C@H]1CCN(c2nc(COCC)nc3c2CCNCC3)C1`

## Interpretation

These molecules should be treated as computational hit candidates, not experimentally confirmed KRAS inhibitors. The next scientific step is structure-based validation, such as docking against a relevant KRAS mutant structure, followed by deeper medicinal chemistry review and experimental assay planning.
