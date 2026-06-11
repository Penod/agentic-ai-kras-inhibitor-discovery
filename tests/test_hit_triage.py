import csv
import tempfile
import unittest
from pathlib import Path

from kras_discovery.screening.hit_triage import passes_hit_filter, triage_hits


class HitTriageTest(unittest.TestCase):
    def test_passes_hit_filter(self) -> None:
        row = {
            "inference_mode": "trained_model",
            "kras_probability_active": "0.81",
            "admet_score": "0.71",
            "recommendation": "Advance with review",
            "toxicity_label": "Low risk",
        }

        self.assertTrue(
            passes_hit_filter(
                row,
                min_kras_probability=0.70,
                min_admet_score=0.60,
                allowed_recommendations={"Advance", "Advance with review"},
                require_low_toxicity=True,
                require_trained_model=True,
            )
        )

    def test_triage_hits_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "ranked.csv"
            output_dir = tmp_path / "triage"
            fieldnames = [
                "overall_rank",
                "compound",
                "overall_score",
                "recommendation",
                "kras_probability_active",
                "inference_mode",
                "admet_score",
                "toxicity_label",
                "smiles",
            ]
            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "overall_rank": "1",
                        "compound": "Hit",
                        "overall_score": "0.90",
                        "recommendation": "Advance",
                        "kras_probability_active": "0.92",
                        "inference_mode": "trained_model",
                        "admet_score": "0.76",
                        "toxicity_label": "Low risk",
                        "smiles": "CCO",
                    }
                )
                writer.writerow(
                    {
                        "overall_rank": "2",
                        "compound": "Miss",
                        "overall_score": "0.85",
                        "recommendation": "Advance",
                        "kras_probability_active": "0.30",
                        "inference_mode": "trained_model",
                        "admet_score": "0.90",
                        "toxicity_label": "Low risk",
                        "smiles": "CCC",
                    }
                )

            hits, summary = triage_hits(input_path=input_path, output_dir=output_dir)

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["compound"], "Hit")
            self.assertEqual(summary["total_screened"], 2)
            self.assertEqual(summary["total_hit_candidates"], 1)
            self.assertTrue((output_dir / "top_hit_candidates.csv").exists())
            self.assertTrue((output_dir / "hit_triage_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
