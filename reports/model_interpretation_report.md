# KRAS Model Interpretation Report

## Summary

This report summarizes model performance and interpretation outputs for the KRAS mutant-selective inhibitor discovery project. The full curated model selected **xgboost** as the best model, while the drug-like subset selected **xgboost**. The comparison supports the current modeling conclusion that ensemble methods, especially XGBoost when installed, provide the strongest predictive performance across both broad and drug-like KRAS chemical spaces.

## Dataset Context

- Full model rows: 1398
- Full model features: 2226
- Full model class counts: {'inactive': 306, 'active': 1092}
- Drug-like model rows: 817
- Drug-like model features: 2226
- Drug-like model class counts: {'inactive': 232, 'active': 585}

## Model Performance

| Dataset | Best Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full curated dataset | xgboost | 0.943 | 0.951 | 0.977 | 0.964 | 0.984 | 0.996 |
| Drug-like subset | xgboost | 0.896 | 0.891 | 0.974 | 0.931 | 0.939 | 0.973 |

## Built-In Feature Importance

### Full Curated Model

Top features: morgan_140, morgan_130, morgan_1456, maccs_62, morgan_775, morgan_1471, mol_logp, maccs_79, maccs_113, morgan_1011

Feature-group importance: Morgan: 0.744, MACCS: 0.210, Descriptor: 0.046

### Drug-Like Model

Top features: morgan_41, maccs_135, morgan_1824, heavy_atom_count, morgan_387, maccs_81, morgan_1504, morgan_847, morgan_1471, morgan_1385

Feature-group importance: Morgan: 0.722, MACCS: 0.214, Descriptor: 0.065

## SHAP Interpretation

### Full Curated Model

SHAP was computed on 250 rows. Top SHAP features: mol_logp, morgan_1569, mol_wt, fraction_csp3, morgan_423, morgan_1634, tpsa, morgan_1747, morgan_1199, morgan_199.

### Drug-Like Model

SHAP was computed on 250 rows. Top SHAP features: mol_logp, mol_wt, heavy_atom_count, morgan_1168, maccs_129, morgan_1569, tpsa, morgan_1824, morgan_45, fraction_csp3.

## Scientific Interpretation

The current interpretation outputs indicate whether predictive signal is concentrated in physicochemical descriptors, MACCS structural keys, or Morgan fingerprint bits. Morgan and MACCS features are useful for predictive performance but require additional chemistry mapping before they can be described as specific molecular substructures. Descriptor-level signals such as molecular weight, LogP, TPSA, heavy atom count, and ring-related features are easier to interpret directly and should be discussed alongside fingerprint features.

## Limitations

- ChEMBL activity records come from heterogeneous assays and publications.
- G12C data dominates the current KRAS training set, while G12D, G12V, and SOS1 remain thinner.
- Built-in feature importance can be biased toward high-cardinality or frequently split features.
- SHAP values improve interpretability but should still be treated as model explanations, not mechanistic proof.
- This project is for computational research and early-stage prioritization, not clinical decision-making.

## Next Steps

1. Map high-ranking MACCS and Morgan bits to representative molecular substructures.
2. Generate per-compound explanations for top predicted active compounds.
3. Add RFECV or another feature-selection workflow for thesis-style dimensionality reduction.
4. Add external validation data from BindingDB, PubChem BioAssay, or newly curated KRAS publications.
5. Promote the best model into the KRAS target-fit agent for agentic inference.
