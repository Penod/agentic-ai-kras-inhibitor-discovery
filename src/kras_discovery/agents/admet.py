from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp


class ADMETAgent(Agent):
    name = "admet"

    def run(self, context: CandidateContext) -> CandidateContext:
        weight = float(context.features.get("molecular_weight", 0.0))
        logp = float(context.features.get("logp", 0.0))
        rotatable_bonds = float(context.features.get("rotatable_bonds", 0.0))

        oral_exposure = clamp(1.0 - abs(logp - 3.0) / 6.5)
        distribution = clamp(1.0 - max(weight - 550.0, 0.0) / 350.0)
        metabolic_risk = clamp(1.0 - rotatable_bonds / 24.0)
        score = round((oral_exposure + distribution + metabolic_risk) / 3.0, 3)
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=score,
                label="ADMET suitable" if score >= 0.72 else "ADMET review",
                evidence=["Estimated ADMET suitability from size, lipophilicity, and flexibility"],
                metrics={
                    "oral_exposure_proxy": round(oral_exposure, 3),
                    "distribution_proxy": round(distribution, 3),
                    "metabolic_risk_proxy": round(metabolic_risk, 3),
                },
            )
        )
        return context
