import unittest

from kras_discovery.models.schemas import MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates


class KRASPipelineTest(unittest.TestCase):
    def test_pipeline_returns_ranked_kras_report(self) -> None:
        reports = evaluate_candidates(
            [
                MoleculeCandidate(name="Aromatic candidate", smiles="O=C(NC1=CC=CC=C1)C1=CC=CC=C1"),
                MoleculeCandidate(name="Small control", smiles="CCO"),
            ]
        )

        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0].overall_rank, 1)
        self.assertTrue(0 <= reports[0].overall_score <= 1)
        self.assertEqual(reports[0].target_panel.family, "KRAS pathway")
        self.assertGreaterEqual(
            {finding.agent for finding in reports[0].findings},
            {
                "validation",
                "features",
                "kras_target_fit",
                "mutant_selectivity",
                "admet",
                "toxicity",
                "literature",
                "manufacturability",
                "clinical_relevance",
            },
        )

    def test_invalid_smiles_is_flagged_for_review(self) -> None:
        [report] = evaluate_candidates([MoleculeCandidate(name="Invalid", smiles="???")])
        validation = next(finding for finding in report.findings if finding.agent == "validation")

        self.assertEqual(validation.label, "Review")
        self.assertIn(report.recommendation, {"Advance with review", "Do not advance"})


if __name__ == "__main__":
    unittest.main()
