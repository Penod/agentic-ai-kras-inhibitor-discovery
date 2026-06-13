from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MoleculeCandidate:
    """A molecule submitted to the screening workflow.

    The project keeps this object intentionally small: candidate identity and
    SMILES are enough for the current CLI and batch-screening workflows.
    Additional metadata from CSV libraries is preserved in downstream summary
    outputs instead of expanding the core runtime schema.
    """

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
    """A single agent's contribution to a candidate report.

    `score` is always normalized to the 0-1 range by convention, but the
    interpretation depends on the agent. `evidence` stores human-readable
    rationale, while `metrics` keeps structured values for reports and filters.
    """

    agent: str
    score: float
    label: str
    evidence: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateReport:
    """Final report returned by the agent orchestrator for one molecule.

    The `model_copy` and `model_dump` methods mimic the small subset of a
    Pydantic-style API used by the rest of the project without introducing a
    heavier runtime dependency.
    """

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
    """Mutable state passed between agents during one screening run."""

    candidate: MoleculeCandidate
    target_panel: TargetPanel
    features: dict[str, float | int | str] = field(default_factory=dict)
    findings: list[AgentFinding] = field(default_factory=list)

    def add_finding(self, finding: AgentFinding) -> None:
        self.findings.append(finding)
