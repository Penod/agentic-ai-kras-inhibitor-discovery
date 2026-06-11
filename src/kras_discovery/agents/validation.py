from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp, extract_basic_features, is_plausible_smiles


class ValidationAgent(Agent):
    name = "validation"

    def run(self, context: CandidateContext) -> CandidateContext:
        smiles = context.candidate.smiles
        features = extract_basic_features(smiles)
        context.features.update(features)

        violations = []
        if not is_plausible_smiles(smiles):
            violations.append("SMILES failed basic syntax screening")
        if features["molecular_weight"] > 650:
            violations.append("Molecular weight exceeds discovery-stage threshold")
        if features["logp"] > 6:
            violations.append("LogP may create solubility or exposure risk")
        if features["hydrogen_bond_donors"] > 5:
            violations.append("Hydrogen bond donor count exceeds threshold")
        if features["hydrogen_bond_acceptors"] > 12:
            violations.append("Hydrogen bond acceptor count exceeds threshold")

        syntax_penalty = 0.45 if violations and violations[0].startswith("SMILES failed") else 0.0
        score = clamp(1.0 - syntax_penalty - (0.15 * (len(violations) - int(bool(syntax_penalty)))))
        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=round(score, 3),
                label="Pass" if score >= 0.75 else "Review",
                evidence=violations or ["Candidate satisfies baseline discovery constraints"],
                metrics=features,
            )
        )
        return context
