from __future__ import annotations

from abc import ABC, abstractmethod

from kras_discovery.models.schemas import CandidateContext


class Agent(ABC):
    name: str

    @abstractmethod
    def run(self, context: CandidateContext) -> CandidateContext:
        """Analyze a candidate and return the updated context."""
