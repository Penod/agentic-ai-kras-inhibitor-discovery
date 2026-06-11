import csv
import tempfile
import unittest
from pathlib import Path

from kras_discovery.validation.known_inhibitors import run_known_inhibitor_validation


class KnownInhibitorValidationTest(unittest.TestCase):
    def test_known_inhibitor_validation_writes_summary_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "known.csv"
            output_dir = tmp_path / "outputs"

            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "compound",
                        "expected_target",
                        "expected_activity",
                        "clinical_status",
                        "pubchem_cid",
                        "source_name",
                        "source_url",
                        "smiles",
                        "notes",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "compound": "Small control",
                        "expected_target": "KRAS G12C",
                        "expected_activity": "active",
                        "clinical_status": "test fixture",
                        "pubchem_cid": "",
                        "source_name": "test",
                        "source_url": "",
                        "smiles": "CCO",
                        "notes": "",
                    }
                )

            summary_rows, reports = run_known_inhibitor_validation(input_path=input_path, output_dir=output_dir)

            self.assertEqual(len(summary_rows), 1)
            self.assertEqual(len(reports), 1)
            self.assertEqual(summary_rows[0]["compound"], "Small control")
            self.assertIn("kras_probability_active", summary_rows[0])
            self.assertTrue((output_dir / "known_kras_inhibitor_validation_summary.csv").exists())
            self.assertTrue((output_dir / "known_kras_inhibitor_agent_reports.json").exists())


if __name__ == "__main__":
    unittest.main()
