from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.inference.model_inference import ModelInferenceUnavailableError, predict_smiles_activity
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp


class KRASTargetFitAgent(Agent):
    name = "kras_target_fit"

    def run(self, context: CandidateContext) -> CandidateContext:
        try:
            prediction = predict_smiles_activity(context.candidate.smiles)
        except ModelInferenceUnavailableError as exc:
            return self._run_heuristic(context, str(exc))

        score = clamp(prediction.probability_active)
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="Predicted KRAS-active" if prediction.predicted_label == 1 else "Predicted KRAS-inactive",
                evidence=[
                    "Trained model inference estimated KRAS pathway activity probability from RDKit descriptors, MACCS keys, and Morgan fingerprints",
                    "Model-powered score replaces the offline target-fit proxy when model artifacts and RDKit are available",
                ],
                metrics={
                    "target_family": context.target_panel.family,
                    "inference_mode": prediction.inference_mode,
                    "probability_active": round(prediction.probability_active, 6),
                    "predicted_label": prediction.predicted_label,
                    "model_path": prediction.model_path,
                    "feature_count": prediction.feature_count,
                },
            )
        )
        return context

    def _run_heuristic(self, context: CandidateContext, fallback_reason: str) -> CandidateContext:
        features = context.features
        weight = float(features.get("molecular_weight", 0.0))
        logp = float(features.get("logp", 0.0))
        rings = float(features.get("ring_count", 0.0))
        hetero_atoms = float(features.get("hetero_atom_count", 0.0))
        halogens = float(features.get("halogen_count", 0.0))

        size_fit = 1.0 - abs(weight - 480.0) / 650.0
        lipophilicity_fit = 1.0 - abs(logp - 3.8) / 6.0
        pocket_feature_fit = min((rings + hetero_atoms + halogens) / 10.0, 1.0)
        covalent_like_signal = 0.35 if any(fragment in context.candidate.smiles for fragment in ["C=O", "N=C", "C#N"]) else 0.0
        score = clamp(0.35 * size_fit + 0.25 * lipophilicity_fit + 0.25 * pocket_feature_fit + covalent_like_signal)

        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="KRAS pathway-like" if score >= 0.68 else "Weak KRAS fit",
                evidence=[
                    "Offline proxy estimates KRAS-pathway inhibitor fit from size, lipophilicity, ring/hetero features, and electrophile-like motifs",
                    f"Trained model fallback reason: {fallback_reason}",
                ],
                metrics={
                    "target_family": context.target_panel.family,
                    "inference_mode": "heuristic_fallback",
                    "size_fit": round(clamp(size_fit), 3),
                    "lipophilicity_fit": round(clamp(lipophilicity_fit), 3),
                    "pocket_feature_fit": round(clamp(pocket_feature_fit), 3),
                    "covalent_like_signal": covalent_like_signal,
                },
            )
        )
        return context
