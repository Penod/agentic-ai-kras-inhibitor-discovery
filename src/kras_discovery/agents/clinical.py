from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext


class ClinicalRelevanceAgent(Agent):
    name = "clinical_relevance"

    def run(self, context: CandidateContext) -> CandidateContext:
        scores = {
            finding.agent: finding.score
            for finding in context.findings
            if finding.agent in {"kras_target_fit", "mutant_selectivity", "admet", "toxicity"}
        }
        score = round(sum(scores.values()) / max(len(scores), 1), 3)
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=score,
                label="Relevant for KRAS-driven oncology" if score >= 0.68 else "Needs stronger evidence",
                evidence=[
                    f"Indication focus: {context.target_panel.indication_focus}",
                    "Clinical relevance aggregates target fit, mutant-selectivity hypothesis, ADMET, and toxicity signals",
                ],
                metrics=scores,
            )
        )
        return context
