import csv
import tempfile
import unittest
from pathlib import Path

from kras_discovery.screening.batch_screen import run_batch_screening


class BatchScreeningTest(unittest.TestCase):
    def test_batch_screening_writes_ranked_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "library.csv"
            output_dir = tmp_path / "outputs"

            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["compound", "smiles", "library", "notes"])
                writer.writeheader()
                writer.writerow(
                    {
                        "compound": "Aromatic candidate",
                        "smiles": "O=C(NC1=CC=CC=C1)C1=CC=CC=C1",
                        "library": "fixture",
                        "notes": "test",
                    }
                )
                writer.writerow(
                    {
                        "compound": "Small control",
                        "smiles": "CCO",
                        "library": "fixture",
                        "notes": "test",
                    }
                )

            summary_rows, reports = run_batch_screening(input_path=input_path, output_dir=output_dir)

            self.assertEqual(len(summary_rows), 2)
            self.assertEqual(len(reports), 2)
            self.assertEqual(summary_rows[0]["overall_rank"], 1)
            self.assertIn("kras_probability_active", summary_rows[0])
            self.assertTrue((output_dir / "ranked_screening_results.csv").exists())
            self.assertTrue((output_dir / "agent_screening_reports.json").exists())

    def test_batch_screening_supports_top_n(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "library.csv"
            output_dir = tmp_path / "outputs"

            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["compound", "smiles"])
                writer.writeheader()
                writer.writerow({"compound": "A", "smiles": "CCO"})
                writer.writerow({"compound": "B", "smiles": "CCC"})

            summary_rows, reports = run_batch_screening(input_path=input_path, output_dir=output_dir, top_n=1)

            self.assertEqual(len(summary_rows), 1)
            self.assertEqual(len(reports), 1)


if __name__ == "__main__":
    unittest.main()
