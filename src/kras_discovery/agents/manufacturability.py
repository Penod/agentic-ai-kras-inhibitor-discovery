from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp


class ManufacturabilityAgent(Agent):
    name = "manufacturability"

    def run(self, context: CandidateContext) -> CandidateContext:
        rings = float(context.features.get("ring_count", 0.0))
        rotatable = float(context.features.get("rotatable_bonds", 0.0))
        hetero = float(context.features.get("hetero_atom_count", 0.0))
        score = clamp(0.88 - rings * 0.045 - rotatable * 0.012 - max(hetero - 9, 0) * 0.025)
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="Manufacturable" if score >= 0.68 else "Complex synthesis",
                evidence=["Estimated synthesis feasibility from ring count, flexibility, and hetero atom burden"],
                metrics={"synthetic_accessibility_proxy": round(score, 3)},
            )
        )
        return context
