from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MoleculeCandidate:
    smiles: str
    name: str = "Candidate"


@dataclass(frozen=True)
class TargetNode:
    name: str
    gene: str
    mutation: str
    role: str
    disease_context: str


@dataclass(frozen=True)
class TargetPanel:
    family: str
    indication_focus: str
    nodes: tuple[TargetNode, ...]


@dataclass
class AgentFinding:
    agent: str
    score: float
    label: str
    evidence: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateReport:
    compound: str
    smiles: str
    target_panel: TargetPanel
    findings: list[AgentFinding]
    overall_score: float
    overall_rank: int
    recommendation: str

    def model_copy(self, update: dict[str, Any] | None = None) -> "CandidateReport":
        values = {
            "compound": self.compound,
            "smiles": self.smiles,
            "target_panel": self.target_panel,
            "findings": self.findings,
            "overall_score": self.overall_score,
            "overall_rank": self.overall_rank,
            "recommendation": self.recommendation,
        }
        values.update(update or {})
        return CandidateReport(**values)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateContext:
    candidate: MoleculeCandidate
    target_panel: TargetPanel
    features: dict[str, float | int | str] = field(default_factory=dict)
    findings: list[AgentFinding] = field(default_factory=list)

    def add_finding(self, finding: AgentFinding) -> None:
        self.findings.append(finding)
