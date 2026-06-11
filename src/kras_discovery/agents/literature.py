from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext


class LiteratureAgent(Agent):
    name = "literature"

    def run(self, context: CandidateContext) -> CandidateContext:
        target_names = ", ".join(node.name for node in context.target_panel.nodes)
        score = 0.74 if float(context.features.get("ring_count", 0.0)) >= 1 else 0.58
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=score,
                label="KRAS evidence-ready" if score >= 0.7 else "Limited KRAS evidence",
                evidence=[
                    f"Offline literature stub prepared for targets: {target_names}",
                    "Future version should retrieve PubMed evidence for KRAS mutant selectivity, resistance, and cancer indication context",
                ],
                metrics={"retrieval_mode": "offline_stub"},
            )
        )
        return context
