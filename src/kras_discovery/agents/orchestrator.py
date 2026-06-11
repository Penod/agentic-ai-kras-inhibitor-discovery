from __future__ import annotations

from kras_discovery.agents.admet import ADMETAgent
from kras_discovery.agents.base import Agent
from kras_discovery.agents.clinical import ClinicalRelevanceAgent
from kras_discovery.agents.features import FeatureAgent
from kras_discovery.agents.literature import LiteratureAgent
from kras_discovery.agents.manufacturability import ManufacturabilityAgent
from kras_discovery.agents.ranking import recommendation_for, score_context
from kras_discovery.agents.selectivity import MutantSelectivityAgent
from kras_discovery.agents.target_fit import KRASTargetFitAgent
from kras_discovery.agents.toxicity import ToxicityAgent
from kras_discovery.agents.validation import ValidationAgent
from kras_discovery.models.schemas import CandidateContext, CandidateReport, MoleculeCandidate, TargetPanel
from kras_discovery.models.targets import KRAS_TARGET_PANEL


class AgentOrchestrator:
    def __init__(self, agents: list[Agent] | None = None, target_panel: TargetPanel = KRAS_TARGET_PANEL) -> None:
        self.target_panel = target_panel
        self.agents = agents or [
            ValidationAgent(),
            FeatureAgent(),
            KRASTargetFitAgent(),
            MutantSelectivityAgent(),
            ADMETAgent(),
            ToxicityAgent(),
            LiteratureAgent(),
            ManufacturabilityAgent(),
            ClinicalRelevanceAgent(),
        ]

    def evaluate(self, candidate: MoleculeCandidate, rank: int = 1) -> CandidateReport:
        context = CandidateContext(candidate=candidate, target_panel=self.target_panel)
        for agent in self.agents:
            context = agent.run(context)

        overall_score = score_context(context)
        return CandidateReport(
            compound=candidate.name,
            smiles=candidate.smiles,
            target_panel=self.target_panel,
            findings=context.findings,
            overall_score=overall_score,
            overall_rank=rank,
            recommendation=recommendation_for(overall_score),
        )
