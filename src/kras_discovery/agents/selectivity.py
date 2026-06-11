from __future__ import annotations

from kras_discovery.agents.base import Agent
from kras_discovery.models.schemas import AgentFinding, CandidateContext
from kras_discovery.utils.chemistry import clamp


class MutantSelectivityAgent(Agent):
    name = "mutant_selectivity"

    def run(self, context: CandidateContext) -> CandidateContext:
        features = context.features
        halogens = float(features.get("halogen_count", 0.0))
        rings = float(features.get("ring_count", 0.0))
        hetero = float(features.get("hetero_atom_count", 0.0))
        smiles = context.candidate.smiles

        g12c = clamp(0.35 + 0.08 * halogens + (0.2 if "C=O" in smiles or "C#N" in smiles else 0.0))
        g12d = clamp(0.28 + 0.06 * hetero + 0.04 * rings)
        g12v = clamp(0.25 + 0.07 * rings + 0.03 * halogens)
        sos1 = clamp(0.32 + 0.05 * hetero + 0.05 * rings)
        score = round(max(g12c, g12d, g12v, sos1), 3)
        best = max({"G12C": g12c, "G12D": g12d, "G12V": g12v, "SOS1": sos1}, key=lambda item: {"G12C": g12c, "G12D": g12d, "G12V": g12v, "SOS1": sos1}[item])

        context.add_finding(
            AgentFinding(
                agent=self.name,
                score=score,
                label=f"Best hypothesis: {best}",
                evidence=["Generated a mutant-selectivity hypothesis for human review"],
                metrics={
                    "kras_g12c_hypothesis": round(g12c, 3),
                    "kras_g12d_hypothesis": round(g12d, 3),
                    "kras_g12v_hypothesis": round(g12v, 3),
                    "sos1_hypothesis": round(sos1, 3),
                },
            )
        )
        return context
