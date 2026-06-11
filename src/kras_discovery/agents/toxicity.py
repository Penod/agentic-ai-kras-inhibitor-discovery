from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp


RISK_MOTIFS = {
    "nitro": "[N+](=O)[O-]",
    "azide": "N=[N+]=[N-]",
    "acid_chloride": "C(=O)Cl",
    "epoxide": "C1OC1",
}


class ToxicityAgent(Agent):
    name = "toxicity"

    def run(self, context: CandidateContext) -> CandidateContext:
        smiles = context.candidate.smiles
        hits = [name for name, motif in RISK_MOTIFS.items() if motif in smiles]
        halogen_count = float(context.features.get("halogen_count", 0.0))
        score = clamp(0.93 - (0.2 * len(hits)) - (0.035 * max(halogen_count - 4, 0)))
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="Low risk" if score >= 0.75 else "Elevated risk",
                evidence=[f"Detected structural alert: {hit}" for hit in hits] or ["No simple toxicity motifs detected"],
                metrics={"structural_alert_count": len(hits), "halogen_count": halogen_count},
            )
        )
        return context
