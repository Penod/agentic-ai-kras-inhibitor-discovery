from __future__ import annotations

from kras_discovery.agents.orchestrator import AgentOrchestrator
from kras_discovery.models.schemas import CandidateReport, MoleculeCandidate


def evaluate_candidates(candidates: list[MoleculeCandidate]) -> list[CandidateReport]:
    orchestrator = AgentOrchestrator()
    reports = [orchestrator.evaluate(candidate) for candidate in candidates]
    reports.sort(key=lambda report: report.overall_score, reverse=True)
    return [
        report.model_copy(update={"overall_rank": rank})
        for rank, report in enumerate(reports, start=1)
    ]
