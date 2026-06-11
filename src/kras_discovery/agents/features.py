from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp, extract_basic_features


class FeatureAgent(Agent):
    name = "features"

    def run(self, context: CandidateContext) -> CandidateContext:
        context.features.update(extract_basic_features(context.candidate.smiles))
        atom_count = float(context.features["atom_count"])
        hetero_ratio = float(context.features["hetero_atom_count"]) / max(atom_count, 1.0)
        ring_count = float(context.features["ring_count"])
        score = clamp(0.55 + hetero_ratio + min(ring_count, 4.0) * 0.06)
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="Descriptor profile generated",
                evidence=["Computed approximate descriptors for KRAS pathway screening"],
                metrics=context.features,
            )
        )
        return context
