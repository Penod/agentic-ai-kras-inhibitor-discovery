from __future__ import annotations

from kras_discovery.models.schemas import CandidateContext


RANKING_WEIGHTS = {
    "validation": 0.10,
    "features": 0.07,
    "kras_target_fit": 0.24,
    "mutant_selectivity": 0.18,
    "admet": 0.15,
    "toxicity": 0.12,
    "literature": 0.06,
    "manufacturability": 0.04,
    "clinical_relevance": 0.04,
}


def score_context(context: CandidateContext) -> float:
    finding_by_agent = {finding.agent: finding for finding in context.findings}
    weighted_sum = 0.0
    total_weight = 0.0
    for agent, weight in RANKING_WEIGHTS.items():
        if agent in finding_by_agent:
            weighted_sum += finding_by_agent[agent].score * weight
            total_weight += weight
    return round(weighted_sum / max(total_weight, 1e-9), 3)


def recommendation_for(score: float) -> str:
    if score >= 0.82:
        return "Advance"
    if score >= 0.65:
        return "Advance with review"
    return "Do not advance"
