import unittest

from kras_discovery.inference.model_inference import feature_vector_from_row, probability_active
from kras_discovery.models.schemas import MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates


class FakeProbModel:
    def predict_proba(self, vector):
        return [[0.2, 0.8]]


class InferenceTest(unittest.TestCase):
    def test_feature_vector_follows_feature_columns_order(self) -> None:
        row = {"b": "2.5", "a": "1.0"}
        vector = feature_vector_from_row(row, ["a", "b", "missing"])

        self.assertEqual(vector, [[1.0, 2.5, 0.0]])

    def test_probability_active_uses_predict_proba(self) -> None:
        self.assertEqual(probability_active(FakeProbModel(), [[1.0]]), 0.8)

    def test_pipeline_still_runs_with_model_fallback(self) -> None:
        [report] = evaluate_candidates([MoleculeCandidate(name="Small control", smiles="CCO")])
        target_fit = next(finding for finding in report.findings if finding.agent == "kras_target_fit")

        self.assertIn(target_fit.metrics["inference_mode"], {"trained_model", "heuristic_fallback"})


if __name__ == "__main__":
    unittest.main()
