import csv
import json
import tempfile
import unittest
from pathlib import Path

from kras_discovery.screening.hit_report import build_hit_report, write_hit_report


class HitReportTest(unittest.TestCase):
    def test_build_hit_report_includes_key_sections(self) -> None:
        hits = [
            {
                "compound": "ZINC001",
                "kras_probability_active": "0.91",
                "overall_score": "0.88",
                "admet_score": "0.72",
                "toxicity_label": "Low risk",
                "recommendation": "Advance",
                "target_fit_label": "Predicted KRAS-active",
                "inference_mode": "trained_model",
                "mutant_selectivity_label": "Best hypothesis: G12D",
                "manufacturability_label": "Manufacturable",
                "manufacturability_score": "0.66",
                "smiles": "CCO",
            }
        ]
        summary = {"total_screened": 5000, "total_hit_candidates": 1, "min_kras_probability": 0.7, "min_admet_score": 0.6}

        report = build_hit_report(hits, summary)

        self.assertIn("# ZINC KRAS Hit Triage Report", report)
        self.assertIn("ZINC001", report)
        self.assertIn("computational hit candidates", report)

    def test_write_hit_report_creates_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hits_path = tmp_path / "hits.csv"
            summary_path = tmp_path / "summary.json"
            output_path = tmp_path / "report.md"
            fieldnames = [
                "compound",
                "kras_probability_active",
                "overall_score",
                "admet_score",
                "toxicity_label",
                "recommendation",
                "target_fit_label",
                "inference_mode",
                "mutant_selectivity_label",
                "manufacturability_label",
                "manufacturability_score",
                "smiles",
            ]
            with hits_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "compound": "ZINC001",
                        "kras_probability_active": "0.91",
                        "overall_score": "0.88",
                        "admet_score": "0.72",
                        "toxicity_label": "Low risk",
                        "recommendation": "Advance",
                        "target_fit_label": "Predicted KRAS-active",
                        "inference_mode": "trained_model",
                        "mutant_selectivity_label": "Best hypothesis: G12D",
                        "manufacturability_label": "Manufacturable",
                        "manufacturability_score": "0.66",
                        "smiles": "CCO",
                    }
                )
            summary_path.write_text(json.dumps({"total_screened": 5000, "total_hit_candidates": 1}), encoding="utf-8")

            write_hit_report(hits_path=hits_path, summary_path=summary_path, output_path=output_path)

            self.assertTrue(output_path.exists())
            self.assertIn("ZINC001", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
